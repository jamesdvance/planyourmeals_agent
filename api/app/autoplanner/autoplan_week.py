"""
Weekly meal plan auto-planner using Pyomo mixed-integer optimization.

Ported from legacy autoplanner. Preserves the Pyomo ConcreteModel structure
(decision variables, constraints, objective) and raw SQL queries. Uses
django.db.connection instead of raw psycopg2/ODBC connections.
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
    Binary,
    ConcreteModel,
    Constraint,
    NonNegativeIntegers,
    Objective,
    Param,
    Set,
    SolverFactory,
    Var,
    inequality,
    sum_product,
)
from pyomo.gdp import Disjunct, Disjunction, TransformationFactory

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Named constants (extracted from magic numbers in legacy code)
# ---------------------------------------------------------------------------
DEFAULT_LAST_VIEW = datetime.date(2018, 1, 1)
DEFAULT_MAX_SERVINGS = 2
PROB_R_USES_WEIGHT = 0.3
PROB_R_RATING_WEIGHT = 0.3
PROB_R_RANDOM_WEIGHT = 0.75
PROB_R_INV_USES_WEIGHT = 0.3
PROB_R_VIEW_RECENCY_WEIGHT = 0.1
PROB_R_USE_RECENCY_WEIGHT = 0.25
MAX_REPEAT_PER_MEAL = 2
SOLVER_NAME = "cbc"
SIDES_DICT = {
    "Breakfast": {"min": 1, "max": 2},
    "Lunch": {"min": 1, "max": 2},
    "Dinner": {"min": 1, "max": 2},
}


@dataclass
class PlanResult:
    """Result of an autoplan solve."""

    results_df: pd.DataFrame
    status: str  # "optimal", "infeasible", etc.
    solve_time_seconds: float = 0.0
    model: Any = field(default=None, repr=False)


class WeekAutoPlanner:
    """
    Builds and solves a weekly meal plan optimization model.

    Parameters
    ----------
    user_id : int
    requirements_dict : dict
        {day_key: {nutrient: [upper_bound, lower_bound], ...}}
    menus_dict_list : list[dict]
        Menu structure from the frontend.
    week_start_dt : date
    week_end_dt : date
    n_snack : int
        Max snacks per day.
    solver_params : dict
        CBC solver parameters (e.g. {"seconds": 30}).
    """

    def __init__(
        self,
        user_id: int,
        requirements_dict: dict,
        menus_dict_list: list[dict],
        week_start_dt: datetime.date,
        week_end_dt: datetime.date,
        n_snack: int = 2,
        solver_params: dict | None = None,
    ):
        self.user_id = user_id
        self.requirements_dict = requirements_dict
        self.menus_list = menus_dict_list
        self.week_start_dt = week_start_dt
        self.week_end_dt = week_end_dt
        self.n_snack = n_snack
        self.solver_params = solver_params or {"seconds": 30}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def solve(self) -> PlanResult:
        """Query data, build model, solve, return results."""
        from timeit import default_timer as timer

        start = timer()

        qry = self._all_menu_opts_qry()
        tag_ids, rest_ids, menu_ids, meals_idx_tup, days_list = self._prep_query_params()
        params = {
            "user_id": self.user_id,
            "week_start_dt": self.week_start_dt,
            "week_end_dt": self.week_end_dt,
            "menu_id_list": tuple(menu_ids),
            "tag_id_list": tuple(tag_ids),
            "rest_id_list": tuple(rest_ids),
        }

        food_df = self._query_food_df(params, qry)
        if food_df.empty:
            return PlanResult(
                results_df=pd.DataFrame(), status="no_data", model=None
            )

        opt_input_df, leftover_dict = self._build_opt_dataset(food_df)

        food_max, global_m, meal_food_tup, src_constr_dict, incl_dict = (
            self._set_opt_variables(opt_input_df, days_list, meals_idx_tup)
        )

        model = self._build_model(
            opt_input_df,
            self.requirements_dict,
            food_max,
            self.n_snack,
            global_m,
            src_constr_dict,
            incl_dict,
            SIDES_DICT,
            meal_food_tup,
            meals_idx_tup,
            days_list,
            leftover_dict,
        )

        model, status = self._solve_model(model)

        results_df = self._parse_results(model, opt_input_df, leftover_dict)

        elapsed = timer() - start
        logger.info("Autoplan solved in %.2fs with status=%s", elapsed, status)

        return PlanResult(
            results_df=results_df,
            status=status,
            solve_time_seconds=elapsed,
            model=model,
        )

    # ------------------------------------------------------------------
    # Query methods (raw SQL preserved from legacy)
    # ------------------------------------------------------------------

    def _query_food_df(self, params: dict, qry: str) -> pd.DataFrame:
        """Execute the all-menus query and return a DataFrame."""
        return pd.read_sql(sql=qry, params=params, con=django_connection)

    def _all_menu_opts_qry(self) -> str:
        """
        Combined query for foods from menus, food preferences, tags.

        Table names match db_table values set on the new Django models:
        - food_foods, core_foodpreferences, core_userprobrejectfood,
        - food_taggedfoods, core_prefmenu, plan_meal, plan_food_amount
        """
        return """
        /* Foods from food preferences in menus */
        SELECT
            f.id as unique_id,
            'food' as fd_type,
            m.meal_type as meal,
            m.dish_num,
            'menu' as menu_type,
            m.prefmenu_id as menu_id,
            pr.viewed,
            pr.user_total_uses,
            pr.user_star_rating,
            COALESCE(pr.last_use, '2018-01-01'::date) as last_use,
            pr.removed,
            pr.dislike_ind,
            COALESCE(pr.last_view, '2018-01-01'::date) as last_view,
            COALESCE(pr.max_servings, f.max_servings) as max_servings,
            COALESCE(pr.max_num_per_week, f.max_num_per_week) as max_num_per_week,
            f.serving_size_val,
            f.calories,
            f.protein_g,
            f.fat_g,
            f.carb_g,
            f.saturated_fat_g,
            f.fiber_g,
            f.sugar_g,
            f.sodium_mg,
            f.cholesterol_mg,
            f.calcium_mg,
            f.iron_mg,
            f.vit_a_mcg,
            f.vit_c_mg
        FROM core_foodpreferences m
        JOIN food_foods f
            ON m.food_id = f.id
        LEFT JOIN core_userprobrejectfood pr
            ON f.id = pr.food_id
            AND pr.user_id = %(user_id)s
        WHERE m.prefmenu_id IN %(menu_id_list)s

        UNION

        /* Foods from tags (standalone) */
        SELECT
            f.id as unique_id,
            'food' as fd_type,
            'placeholder' as meal,
            COALESCE(pr.default_dish_num, f.default_dish_num) as dish_num,
            'tag' as menu_type,
            t.id as menu_id,
            pr.viewed,
            pr.user_total_uses,
            COALESCE(pr.user_star_rating, f.star_rating) as user_star_rating,
            COALESCE(pr.last_use, '2018-01-01'::date) as last_use,
            pr.removed,
            pr.dislike_ind,
            COALESCE(pr.last_view, '2018-01-01'::date) as last_view,
            COALESCE(pr.max_servings, f.max_servings) as max_servings,
            COALESCE(pr.max_num_per_week, f.max_num_per_week) as max_num_per_week,
            f.serving_size_val,
            f.calories,
            f.protein_g,
            f.fat_g,
            f.carb_g,
            f.saturated_fat_g,
            f.fiber_g,
            f.sugar_g,
            f.sodium_mg,
            f.cholesterol_mg,
            f.calcium_mg,
            f.iron_mg,
            f.vit_a_mcg,
            f.vit_c_mg
        FROM food_taggedfoods t
        JOIN food_foods f
            ON t.food_id = f.id
        LEFT JOIN core_userprobrejectfood pr
            ON f.id = pr.food_id
            AND pr.user_id = %(user_id)s
        WHERE t.foodtag_id IN %(tag_id_list)s
        """

    def _user_reqs_qry(self) -> str:
        """Query user nutrient upper/lower bounds from profile."""
        return """
            SELECT
                cal_lb as calories,
                pro_lb as protein_g,
                fat_lb as fat_g,
                car_lb as carb_g,
                fib_lb as fiber_g,
                clc_lb as calcium_mg,
                irn_lb as iron_mg,
                vta_lb as vit_a_mcg,
                vtc_lb as vit_c_mg,
                sug_lb as sugar_g,
                stf_lb as saturated_fat_g,
                sod_lb as sodium_mg,
                cho_lb as cholesterol_mg
            FROM core_profile
            WHERE user_id = %(user_id)s
            UNION
            SELECT
                cal_ub as calories,
                pro_ub as protein_g,
                fat_ub as fat_g,
                car_ub as carb_g,
                fib_ub as fiber_g,
                clc_ub as calcium_mg,
                irn_ub as iron_mg,
                vta_ub as vit_a_mcg,
                vtc_ub as vit_c_mg,
                sug_ub as sugar_g,
                stf_ub as saturated_fat_g,
                sod_ub as sodium_mg,
                cho_ub as cholesterol_mg
            FROM core_profile
            WHERE user_id = %(user_id)s
        """

    # ------------------------------------------------------------------
    # Data preparation
    # ------------------------------------------------------------------

    def _prep_query_params(
        self,
    ) -> tuple[list, list, list, list[tuple], list[str]]:
        """Extract query parameter lists from menus structure."""
        tag_ids: list[int] = [0]
        rest_ids: list[int] = [0]
        menu_ids: list[int] = [0]
        meals_idx_tup: list[tuple[str, str]] = []
        days_list: list[str] = []

        for menu_dict in self.menus_list:
            for meal in menu_dict["meals"]:
                days_list.append(menu_dict["day"])
                meals_idx_tup.append((menu_dict["day"], meal["meal"]))
                for menu in meal["menus"]:
                    if menu["type"] == "menu":
                        menu_ids.append(menu["id"])
                    elif menu["type"] == "tag":
                        tag_ids.append(menu["id"])
                    elif menu["type"] == "restaurant":
                        rest_ids.append(menu["id"])

        return (
            list(set(tag_ids)),
            list(set(rest_ids)),
            list(set(menu_ids)),
            meals_idx_tup,
            list(set(days_list)),
        )

    def _build_opt_dataset(
        self, food_df: pd.DataFrame
    ) -> tuple[pd.DataFrame, dict]:
        """
        Build the optimization input DataFrame from queried food data.

        Calculates prob_r (probability-to-reject) as the objective coefficient.
        """
        leftover_dict: dict = {}
        opt_input_df = pd.DataFrame()

        for menu_dict in self.menus_list:
            for meal in menu_dict["meals"]:
                for menu in meal["menus"]:
                    if menu["type"] == "leftovers":
                        leftover_dict[menu_dict["day"]] = {
                            "meal": meal["meal"],
                            "orig_meal": menu["meal"],
                            "orig_day": menu["day"],
                        }
                    else:
                        loop_df = food_df[
                            (food_df["menu_type"] == menu["type"])
                            & (food_df["menu_id"] == menu["id"])
                        ].copy()
                        loop_df["meal"] = meal["meal"]
                        loop_df["day"] = menu_dict["day"]
                        opt_input_df = pd.concat(
                            [opt_input_df, loop_df], ignore_index=True
                        )

        if opt_input_df.empty:
            return opt_input_df, leftover_dict

        opt_input_df = opt_input_df.reset_index(drop=True)

        # Fill NAs
        opt_input_df["last_view"] = pd.to_datetime(
            opt_input_df["last_view"].fillna(DEFAULT_LAST_VIEW)
        )
        opt_input_df["last_use"] = pd.to_datetime(
            opt_input_df["last_use"].fillna(DEFAULT_LAST_VIEW)
        )
        opt_input_df["max_servings"] = opt_input_df["max_servings"].fillna(
            DEFAULT_MAX_SERVINGS
        )
        opt_input_df = opt_input_df.fillna(0)

        # Build access index (unique key per food-day-meal-dish)
        opt_input_df["access_idx"] = (
            opt_input_df["unique_id"].astype(str)
            + "_"
            + opt_input_df["fd_type"]
            + "_"
            + opt_input_df["day"]
            + "_"
            + opt_input_df["meal"]
            + "_"
            + opt_input_df["dish_num"]
            + "_"
            + opt_input_df["serving_size_val"].astype(str)
        )

        # Calculate prob_r objective
        n = len(opt_input_df)
        today = datetime.date.today()
        prob_r = (
            (1 - (opt_input_df["user_total_uses"] + 0.001) / (opt_input_df["viewed"] + 0.002))
            * PROB_R_USES_WEIGHT
            + (5 - opt_input_df["user_star_rating"]) * PROB_R_RATING_WEIGHT
            + np.random.rand(n) * PROB_R_RANDOM_WEIGHT
            + 1 / np.maximum([0.5] * n, opt_input_df["user_total_uses"]) * PROB_R_INV_USES_WEIGHT
            + (1 / (((today - opt_input_df["last_view"].dt.date).dt.days) + 0.5))
            * PROB_R_VIEW_RECENCY_WEIGHT
            + (1 / (((today - opt_input_df["last_use"].dt.date).dt.days) + 0.5))
            * PROB_R_USE_RECENCY_WEIGHT
        )
        opt_input_df["prob_r"] = prob_r

        return opt_input_df, leftover_dict

    def _set_opt_variables(
        self,
        opt_input_df: pd.DataFrame,
        days_list: list[str],
        meals_idx_tup: list[tuple[str, str]],
    ) -> tuple[float, float, list[tuple], dict, dict]:
        """Compute optimization parameters from the input dataset."""
        food_max = max(opt_input_df["max_servings"])
        global_m = food_max + 3

        meal_food_tup = [
            tuple(x)
            for x in opt_input_df[~opt_input_df["meal"].isin(["Snack", "Breakfast"])][
                ["meal", "fd_type", "unique_id"]
            ]
            .drop_duplicates()
            .values
        ]

        src_constr_dict: dict = {}
        incl_dict: dict = {}

        for tup in meals_idx_tup:
            incl_dict[tup] = True
            if tup[1] != "Snack":
                loop_df = opt_input_df[
                    (opt_input_df["day"] == tup[0]) & (opt_input_df["meal"] == tup[1])
                ]
                wh = "Whole Meals" in loop_df["dish_num"].values
                si = "Sides" in loop_df["dish_num"].values
                mc = "Main Courses" in loop_df["dish_num"].values

                if wh and (not si or not mc):
                    src_constr_dict[tup] = "sa"
                elif not wh and (si and mc):
                    src_constr_dict[tup] = "bd"
                elif wh and si and mc:
                    src_constr_dict[tup] = "dj"
                else:
                    incl_dict[tup] = False
                    src_constr_dict[tup] = "sa"

        return food_max, global_m, meal_food_tup, src_constr_dict, incl_dict

    # ------------------------------------------------------------------
    # Model building (Pyomo)
    # ------------------------------------------------------------------

    def _build_model(
        self,
        food_df: pd.DataFrame,
        requirements_dict: dict,
        food_max: float,
        n_snack: int,
        global_m: float,
        src_constr_dict: dict,
        incl_dict: dict,
        sides_dict: dict,
        meal_food_tup: list[tuple],
        meals_idx_tup: list[tuple],
        days: list[str],
        leftover_dict: dict,
    ) -> ConcreteModel:
        """Build the Pyomo ConcreteModel with all constraints."""
        has_dj = False

        model = ConcreteModel()

        # -- Indices --
        access_df = food_df[["access_idx"]].copy()
        full_I_dict = access_df["access_idx"].to_dict()
        access_df.index = access_df["access_idx"]
        access_df["full_I"] = range(len(access_df))
        access_dict = access_df["full_I"].to_dict()

        model.access_idx = Set(initialize=access_df.index)
        model.full_I = Set(initialize=food_df.index)

        # -- Params --
        model.access_idx_lkup = Param(model.access_idx, initialize=access_dict)
        model.full_I_lkup = Param(model.full_I, initialize=full_I_dict)

        # -- Sub-indices per meal --
        for tup in meals_idx_tup:
            if incl_dict[tup] and tup[1] != "Snack":
                day, meal = tup
                setattr(
                    model,
                    f"{day}_{meal}",
                    Set(
                        initialize=food_df[
                            (food_df["day"] == day) & (food_df["meal"] == meal)
                        ].index
                    ),
                )

                if src_constr_dict[tup] == "sa":
                    setattr(
                        model,
                        f"{day}_{meal}_wm",
                        Set(
                            initialize=food_df[
                                (food_df["day"] == day)
                                & (food_df["meal"] == meal)
                                & (food_df["dish_num"] == "Whole Meals")
                            ].index
                        ),
                    )
                elif src_constr_dict[tup] == "bd":
                    setattr(
                        model,
                        f"{day}_{meal}_mc",
                        Set(
                            initialize=food_df[
                                (food_df["day"] == day)
                                & (food_df["meal"] == meal)
                                & (food_df["dish_num"] == "Main Courses")
                            ].index
                        ),
                    )
                    setattr(
                        model,
                        f"{day}_{meal}_si",
                        Set(
                            initialize=food_df[
                                (food_df["day"] == day)
                                & (food_df["meal"] == meal)
                                & (food_df["dish_num"] == "Sides")
                            ].index
                        ),
                    )
                else:  # "dj"
                    for suffix, dish in [("_wm", "Whole Meals"), ("_mc", "Main Courses"), ("_si", "Sides")]:
                        setattr(
                            model,
                            f"{day}_{meal}{suffix}",
                            Set(
                                initialize=food_df[
                                    (food_df["day"] == day)
                                    & (food_df["meal"] == meal)
                                    & (food_df["dish_num"] == dish)
                                ].index
                            ),
                        )

            elif incl_dict[tup] and tup[1] == "Snack":
                setattr(
                    model,
                    f"{tup[0]}_{tup[1]}",
                    Set(
                        initialize=food_df[
                            (food_df["day"] == tup[0]) & (food_df["meal"] == tup[1])
                        ].index
                    ),
                )

        # -- Variables --
        model.amt_ub = Param(
            model.full_I,
            initialize=food_df[["max_servings"]].to_dict("dict")["max_servings"],
        )
        model.ind = Var(model.full_I, within=Binary)
        model.amt = Var(model.full_I, within=NonNegativeIntegers, bounds=(0, food_max))

        # Big-M linking ind and amt
        def m_rule(model, i):
            return model.amt[i] <= model.ind[i] * global_m

        def use_ind_rule(model, i):
            return model.ind[i] <= model.amt[i]

        model.m_items = Constraint(model.full_I, rule=m_rule)
        model.use_m = Constraint(model.full_I, rule=use_ind_rule)

        # -- Don't repeat across days --
        for tup in meal_food_tup:
            idx = food_df[
                (food_df["meal"] == tup[0])
                & (food_df["fd_type"] == tup[1])
                & (food_df["unique_id"] == tup[2])
            ].index
            setattr(
                model,
                f"{tup[0]}{tup[1]}{tup[2]}_non_rep",
                Constraint(
                    expr=sum(model.ind[m] for m in idx) <= MAX_REPEAT_PER_MEAL
                ),
            )

        # -- Disjunction / selection constraints --
        for tup in meals_idx_tup:
            day, meal = tup
            if incl_dict[tup] and meal != "Snack":
                if src_constr_dict[tup] == "sa":
                    setattr(
                        model,
                        f"{day}_{meal}_sel_wm",
                        Constraint(
                            expr=sum(
                                model.ind[m]
                                for m in getattr(model, f"{day}_{meal}_wm")
                            )
                            == 1
                        ),
                    )
                elif src_constr_dict[tup] == "bd":
                    setattr(
                        model,
                        f"{day}_{meal}_sel_mc",
                        Constraint(
                            expr=sum(
                                model.ind[m]
                                for m in getattr(model, f"{day}_{meal}_mc")
                            )
                            == 1
                        ),
                    )
                    setattr(
                        model,
                        f"{day}_{meal}_sel_si",
                        Constraint(
                            expr=inequality(
                                sides_dict[meal]["min"],
                                sum(
                                    model.ind[m]
                                    for m in getattr(model, f"{day}_{meal}_si")
                                ),
                            )
                        ),
                    )
                else:  # "dj"
                    # Standalone disjunct
                    sa_dj = Disjunct()
                    setattr(model, f"{day}_{meal}_sel_sa", sa_dj)
                    sa_dj.c1 = Constraint(
                        expr=sum(
                            model.ind[m] for m in getattr(model, f"{day}_{meal}_wm")
                        )
                        == 1
                    )
                    sa_dj.c2 = Constraint(
                        expr=sum(
                            model.ind[m] for m in getattr(model, f"{day}_{meal}_mc")
                        )
                        == 0
                    )
                    sa_dj.c3 = Constraint(
                        expr=sum(
                            model.ind[m] for m in getattr(model, f"{day}_{meal}_si")
                        )
                        == 0
                    )

                    # By-dish disjunct
                    bd_dj = Disjunct()
                    setattr(model, f"{day}_{meal}_sel_bd", bd_dj)
                    bd_dj.c1 = Constraint(
                        expr=sum(
                            model.ind[m] for m in getattr(model, f"{day}_{meal}_wm")
                        )
                        == 0
                    )
                    bd_dj.c2 = Constraint(
                        expr=sum(
                            model.ind[m] for m in getattr(model, f"{day}_{meal}_mc")
                        )
                        == 1
                    )
                    bd_dj.c3 = Constraint(
                        expr=inequality(
                            sides_dict[meal]["min"],
                            sum(
                                model.ind[m]
                                for m in getattr(model, f"{day}_{meal}_si")
                            ),
                            sides_dict[meal]["max"],
                        )
                    )

                    setattr(
                        model,
                        f"{day}_{meal}c",
                        Disjunction(expr=[sa_dj, bd_dj]),
                    )
                    has_dj = True

            elif incl_dict[tup] and meal == "Snack":
                setattr(
                    model,
                    f"{day}_{meal}_ind_n",
                    Constraint(
                        expr=sum(
                            model.ind[m] for m in getattr(model, f"{day}_{meal}")
                        )
                        <= n_snack
                    ),
                )

        # Disjunctive transformation
        if has_dj:
            trnsfrm = TransformationFactory("gdp.bigm")
            trnsfrm.apply_to(model)

        # -- Amount upper bounds --
        def amt_bounds_rule(model, i):
            return model.amt[i] <= model.amt_ub[i]

        model.amt_bounds = Constraint(model.full_I, rule=amt_bounds_rule)

        # -- Nutritional bounds per day --
        food_df_dict = food_df[
            [
                "prob_r",
                "calories",
                "protein_g",
                "fat_g",
                "carb_g",
                "saturated_fat_g",
                "fiber_g",
                "sugar_g",
                "sodium_mg",
                "cholesterol_mg",
                "calcium_mg",
                "iron_mg",
                "vit_a_mcg",
                "vit_c_mg",
            ]
        ].to_dict("list")

        for day in days:
            if day in leftover_dict:
                day_idx = food_df[
                    (food_df["day"] == day)
                    | (
                        (food_df["day"] == leftover_dict[day]["orig_day"])
                        & (food_df["meal"] == leftover_dict[day]["orig_meal"])
                    )
                ].index
            else:
                day_idx = food_df[food_df["day"] == day].index

            setattr(model, f"{day}_index", Set(initialize=day_idx))

            nutrient_df = pd.DataFrame(self.requirements_dict[day])
            nut_cols = list(nutrient_df.columns.values)

            setattr(model, f"{day}_N", Set(initialize=nut_cols))
            setattr(
                model,
                f"{day}_bounds",
                Param(
                    getattr(model, f"{day}_N"),
                    initialize=nutrient_df[nut_cols].to_dict("list"),
                ),
            )

            def ml_bounds(model, n, _day=day):
                bounds_param = getattr(model, f"{_day}_bounds")
                day_index = getattr(model, f"{_day}_index")
                return (
                    bounds_param[n][0],
                    sum(food_df_dict[n][i] * model.amt[i] for i in day_index),
                    bounds_param[n][1],
                )

            setattr(
                model,
                f"{day}_nutr_bounds",
                Constraint(getattr(model, f"{day}_N"), rule=ml_bounds),
            )

        # -- Objective: minimize prob_r --
        def tgt_obj(model):
            return sum_product(food_df_dict["prob_r"], model.amt, index=model.full_I)

        model.obj = Objective(rule=tgt_obj)

        return model

    # ------------------------------------------------------------------
    # Solver
    # ------------------------------------------------------------------

    def _solve_model(self, model: ConcreteModel) -> tuple[ConcreteModel, str]:
        """Solve with CBC and return (model, status_string)."""
        opt = SolverFactory(SOLVER_NAME)
        for key, val in self.solver_params.items():
            opt.options[key] = val

        result = opt.solve(model, tee=False)
        status = str(result.solver.termination_condition)
        return model, status

    # ------------------------------------------------------------------
    # Results parsing
    # ------------------------------------------------------------------

    def _parse_results(
        self,
        model: ConcreteModel,
        opt_input_df: pd.DataFrame,
        leftover_dict: dict,
    ) -> pd.DataFrame:
        """Extract solution from solved model into a DataFrame."""
        amt_vec = [model.amt[i].value for i in model.full_I]
        amt_vec = [0 if s is None else s for s in amt_vec]

        fd_df = opt_input_df.assign(amt=amt_vec)
        fd_df = fd_df[fd_df["amt"] > 0]
        fd_df = fd_df[
            ["unique_id", "day", "meal", "dish_num", "fd_type", "amt", "serving_size_val"]
        ]

        # Append leftover copies
        for day in opt_input_df["day"].unique():
            if day in leftover_dict:
                meal_df = fd_df[
                    (fd_df["meal"] == leftover_dict[day]["orig_meal"])
                    & (fd_df["day"] == leftover_dict[day]["orig_day"])
                ].copy()
                meal_df["day"] = day
                meal_df["meal"] = leftover_dict[day]["meal"]
                fd_df = pd.concat([fd_df, meal_df], ignore_index=True)

        return fd_df
