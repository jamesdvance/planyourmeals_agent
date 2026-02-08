"""
Amount adjuster: takes a day's plan and adjusts serving amounts
to better fit nutritional requirements using Pyomo optimization.
"""

from __future__ import annotations

import datetime
import logging
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
from django.db import connection as django_connection
from pyomo.environ import (
    ConcreteModel,
    Constraint,
    NonNegativeIntegers,
    Objective,
    Param,
    Set,
    SolverFactory,
    Var,
    summation,
)

from .autoplan_week import DEFAULT_LAST_VIEW, SOLVER_NAME

logger = logging.getLogger(__name__)

# Nutrient abbreviation to column name mapping
ABREV_TO_NUT = {
    "cal": "calories",
    "pro": "protein_g",
    "fat": "fat_g",
    "car": "carb_g",
    "fib": "fiber_g",
    "clc": "calcium_mg",
    "irn": "iron_mg",
    "vta": "vit_a_mcg",
    "vtc": "vit_c_mg",
    "sug": "sugar_g",
    "stf": "saturated_fat_g",
    "sod": "sodium_mg",
    "cho": "cholesterol_mg",
}


@dataclass
class AdjustResult:
    """Result of an amount adjustment solve."""

    results_df: pd.DataFrame
    status: str
    model: Any = field(default=None, repr=False)


class AmountAdjuster:
    """
    Adjusts food serving amounts for a single day to fit nutrient requirements.

    Parameters
    ----------
    req_cols : list[str]
        Nutrient column names to constrain.
    meal_incl_list : list[str]
        Meal types to adjust (others are fixed).
    adjust_mult : float
        Minimum adjustment granularity (0.25 or 0.5 typical).
    user_id : int
    plan_date : date
    max_amt : int
        Maximum servings per food.
    """

    def __init__(
        self,
        req_cols: list[str],
        meal_incl_list: list[str],
        adjust_mult: float,
        user_id: int,
        plan_date: datetime.date,
        max_amt: int = 4,
    ):
        self.req_cols = req_cols
        self.meal_incl_list = meal_incl_list
        self.adjust_mult = adjust_mult
        self.user_id = user_id
        self.plan_date = plan_date
        self.max_amt = max_amt

    def solve(self) -> AdjustResult:
        """Build dataset, create model, solve, return adjusted amounts."""
        food_df_adj, reqs_df_adj = self._build_food_df()

        if food_df_adj.empty:
            return AdjustResult(results_df=pd.DataFrame(), status="no_data")

        model = self._build_model(
            food_df_adj,
            reqs_df_adj,
            self.req_cols,
            round(self.max_amt / self.adjust_mult),
        )
        model, status = self._solve_model(model)
        results_df = self._parse_results(model, food_df_adj)

        return AdjustResult(results_df=results_df, status=status, model=model)

    def _build_food_df(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Query and prepare the food/requirements DataFrames."""
        reqs_df = pd.read_sql(
            sql=self._query_reqs(),
            params={"user_id": self.user_id},
            con=django_connection,
        )
        reqs_df = reqs_df.fillna(0)

        food_df = pd.read_sql(
            sql=self._query_foods(),
            params={"user_id": self.user_id, "plan_date": self.plan_date},
            con=django_connection,
        )
        food_df["last_view"] = pd.to_datetime(
            food_df["last_view"].fillna(DEFAULT_LAST_VIEW)
        )
        food_df["last_use"] = pd.to_datetime(
            food_df["last_use"].fillna(DEFAULT_LAST_VIEW)
        )
        food_df = food_df.fillna(0)

        # Separate included (adjust) from excluded (fixed)
        excl_df = food_df[~food_df["meal_type"].isin(self.meal_incl_list)].copy()
        food_df_adj = food_df[food_df["meal_type"].isin(self.meal_incl_list)].copy()
        food_df_adj = food_df_adj.reset_index(drop=True)

        for req in self.req_cols:
            excl_df[req] = excl_df[req] * excl_df["amt"] / excl_df["amount_divisor"]

        # Subtract fixed-meal nutrients from requirements
        reqs_df_adj = reqs_df.copy()
        if len(excl_df) > 0:
            excl_sum = excl_df[self.req_cols].sum()
            excl_stacked = pd.concat(
                [excl_sum.to_frame().T, excl_sum.to_frame().T], ignore_index=True
            )
            reqs_df_adj[self.req_cols] -= excl_stacked[self.req_cols].values

        # Set bounds per food
        food_df_adj["lb_col"] = 1
        food_df_adj["ub_col"] = np.round(
            food_df_adj["max_servings"] / self.adjust_mult
        )

        # Normalize nutrients by adjust_mult
        for req in self.req_cols:
            food_df_adj[req] = np.round(
                food_df_adj[req].astype("float") * self.adjust_mult, 2
            ).astype("float")

        # Calculate prob_r
        n = len(food_df_adj)
        today = datetime.date.today()
        prob_r = (
            (1 - (food_df_adj["user_total_uses"] + 0.001) / (food_df_adj["viewed"] + 0.002)) * 0.3
            + (5 - food_df_adj["user_star_rating"]) * 0.3
            + np.random.rand(n) * 0.05
            + 1 / np.maximum([0.5] * n, food_df_adj["user_total_uses"]) * 0.3
            + (1 / (((today - food_df_adj["last_view"].dt.date).dt.days) + 0.5)) * 0.1
            + (1 / (((today - food_df_adj["last_use"].dt.date).dt.days) + 0.5)) * 0.25
        )
        food_df_adj["prob_r"] = prob_r

        return food_df_adj, reqs_df_adj

    def _build_model(
        self,
        food_df: pd.DataFrame,
        reqs_df: pd.DataFrame,
        req_cols: list[str],
        fd_mx: int,
    ) -> ConcreteModel:
        """Build the Pyomo adjustment model."""
        model = ConcreteModel()
        model.N = Set(initialize=req_cols)
        model.full_I = Set(initialize=food_df.index)

        food_df_dict = food_df[["prob_r"] + req_cols].to_dict("list")
        model.bounds = Param(model.N, initialize=reqs_df[req_cols].to_dict("list"))
        model.amt = Var(model.full_I, bounds=(1, fd_mx), within=NonNegativeIntegers)
        model.amt_lb = Param(
            model.full_I, initialize=food_df["lb_col"].to_dict()
        )
        model.amt_ub = Param(
            model.full_I, initialize=food_df["ub_col"].to_dict()
        )

        def ml_bounds(model, n):
            return (
                model.bounds[n][0],
                summation(food_df_dict[n], model.amt),
                model.bounds[n][1],
            )

        model.nutr_constr = Constraint(model.N, rule=ml_bounds)

        def amt_bounds(model, i):
            return (model.amt_lb[i], model.amt[i], model.amt_ub[i])

        model.amt_constr = Constraint(model.full_I, rule=amt_bounds)

        def tgt_obj(model):
            return summation(food_df_dict["prob_r"], model.amt)

        model.obj = Objective(rule=tgt_obj)

        return model

    def _solve_model(self, model: ConcreteModel) -> tuple[ConcreteModel, str]:
        opt = SolverFactory(SOLVER_NAME)
        result = opt.solve(model, tee=False)
        status = str(result.solver.termination_condition)
        return model, status

    def _parse_results(
        self, model: ConcreteModel, food_df: pd.DataFrame
    ) -> pd.DataFrame:
        sol_li = [model.amt[i].value for i in range(len(food_df))]
        sol_li = [0 if s is None else s for s in sol_li]
        return_df = food_df.assign(amt=sol_li)
        for req in self.req_cols:
            return_df[req] = np.round(return_df[req] * return_df["amt"], 2)
        return return_df

    def _query_reqs(self) -> str:
        return """
            SELECT
                cal_lb as calories, pro_lb as protein_g, fat_lb as fat_g,
                car_lb as carb_g, fib_lb as fiber_g, clc_lb as calcium_mg,
                irn_lb as iron_mg, vta_lb as vit_a_mcg, vtc_lb as vit_c_mg,
                sug_lb as sugar_g, stf_lb as saturated_fat_g, sod_lb as sodium_mg,
                cho_lb as cholesterol_mg
            FROM core_profile WHERE user_id = %(user_id)s
            UNION
            SELECT
                cal_ub as calories, pro_ub as protein_g, fat_ub as fat_g,
                car_ub as carb_g, fib_ub as fiber_g, clc_ub as calcium_mg,
                irn_ub as iron_mg, vta_ub as vit_a_mcg, vtc_ub as vit_c_mg,
                sug_ub as sugar_g, stf_ub as saturated_fat_g, sod_ub as sodium_mg,
                cho_ub as cholesterol_mg
            FROM core_profile WHERE user_id = %(user_id)s
        """

    def _query_foods(self) -> str:
        return """
        SELECT
          am.meal_id,
          am.amt,
          am.amount_divisor,
          am.serving_size_idx,
          p.meal_type,
          COALESCE(pr.default_dish_num, f.default_dish_num) as dish_num,
          pr.viewed,
          pr.user_total_uses,
          COALESCE(pr.user_star_rating, f.star_rating) as user_star_rating,
          pr.last_use,
          pr.removed,
          pr.dislike_ind,
          pr.last_view,
          COALESCE(pr.max_servings, f.max_servings) as max_servings,
          f.id as food_key,
          f.food_description,
          f.brand,
          f.serving_size_val,
          f.food_type_grp,
          f.calories,
          f.protein_g,
          f.fat_g,
          f.carb_g,
          f.fiber_g,
          f.calcium_mg,
          f.iron_mg,
          f.vit_a_mcg,
          f.vit_c_mg,
          f.sugar_g,
          f.saturated_fat_g,
          f.sodium_mg,
          f.cholesterol_mg,
          f.image_url
        FROM plan_planmeal p
        JOIN plan_meal m ON p.meal_id = m.id
        JOIN plan_food_amount am ON m.id = am.meal_id
        JOIN food_foods f ON f.id = am.food_id
        LEFT JOIN core_userprobrejectfood pr
          ON f.id = pr.food_id AND pr.user_id = %(user_id)s
        WHERE plan_date = %(plan_date)s AND p.user_id = %(user_id)s;
        """
