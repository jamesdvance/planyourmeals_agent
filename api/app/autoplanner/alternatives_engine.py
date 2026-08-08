"""
Alternatives engine: finds food alternatives and similar foods
that fit within nutritional constraints.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd
from django.db import connection as django_connection

logger = logging.getLogger(__name__)

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

TOP_N_SIMILAR = 3


@dataclass
class AlternativesResult:
    """Result of an alternatives search."""

    alternatives_df: pd.DataFrame
    similar_df: pd.DataFrame


class AlternativesEngine:
    """
    Finds food alternatives that meet nutritional constraints
    and similar foods based on nutrient index distance.

    Parameters
    ----------
    reqs_dict : dict
        Nutrient bounds, e.g. {"cal_lb": 50, "cal_ub": 100, ...}
    food_df : DataFrame
        Available foods with nutrient columns.
    food_id : int
        ID of the food to find alternatives for.
    user_id : int
    """

    def __init__(
        self,
        reqs_dict: dict,
        food_df: pd.DataFrame,
        food_id: int,
        user_id: int,
    ):
        self.reqs_dict = reqs_dict
        self.food_df = food_df
        self.food_id = food_id
        self.user_id = user_id

    def find_alternatives_and_similar(self) -> AlternativesResult:
        """Find both constraint-satisfying alternatives and similar foods."""
        alt_df = self._find_alternates()
        sim_df = self._find_similar(alt_df)
        return AlternativesResult(alternatives_df=alt_df, similar_df=sim_df)

    def _find_alternates(self) -> pd.DataFrame:
        """Find foods that fit within the nutritional constraints using brute-force check."""
        return self._no_opt_solve(self.reqs_dict, self.food_df)

    def _find_similar(self, alt_df: pd.DataFrame) -> pd.DataFrame:
        """Find foods most similar to target based on nutrient index distance."""
        excluded_ids = set(alt_df["food_key"].values) if not alt_df.empty else set()
        sim_food_df = self.food_df[~self.food_df["food_key"].isin(excluded_ids)].copy()

        req_cols = list({ABREV_TO_NUT[req[:3]] for req in self.reqs_dict if "cal" not in req})

        tgt_food_df = self._query_single_food(self.food_id)
        if tgt_food_df.empty or sim_food_df.empty:
            return pd.DataFrame()

        return self._get_closest_greedy(req_cols, sim_food_df, tgt_food_df)

    def _compare_reqs_and_cols(
        self, reqs_dict: dict, loop_df: pd.DataFrame, j: int
    ) -> pd.DataFrame:
        """Filter foods where j servings satisfy all nutrient constraints."""
        req_abrevs = list({req[:3] for req in reqs_dict})
        for nut_abrev in req_abrevs:
            nutrient = ABREV_TO_NUT[nut_abrev]
            lb = reqs_dict.get(f"{nut_abrev}_lb", 0)
            ub = reqs_dict.get(f"{nut_abrev}_ub", float("inf"))
            loop_df = loop_df[(loop_df[nutrient] * j >= lb) & (loop_df[nutrient] * j <= ub)]
        return loop_df.assign(amt=j)

    def _no_opt_solve(self, reqs_dict: dict, food_df: pd.DataFrame) -> pd.DataFrame:
        """Brute-force solve: try 1..max_servings and keep foods that fit constraints."""
        final_df = self._compare_reqs_and_cols(reqs_dict, food_df.copy(), 1)
        max_amt = int(max(food_df["max_servings"])) if not food_df.empty else 1

        for j in range(2, max_amt + 1):
            loop_df = food_df[food_df["max_servings"] >= j].copy()
            if len(loop_df) > 0:
                res_df = self._compare_reqs_and_cols(reqs_dict, loop_df, j)
                final_df = pd.concat([final_df, res_df], ignore_index=True)

        return final_df

    def _get_closest_greedy(
        self,
        req_cols: list[str],
        food_df: pd.DataFrame,
        tgt_food_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Find most similar foods by Euclidean distance on nutrient index."""
        fd_idx_cols = [f"{req}_index" for req in req_cols]

        # Check that index columns exist
        available_cols = [
            c for c in fd_idx_cols if c in tgt_food_df.columns and c in food_df.columns
        ]
        if not available_cols:
            return pd.DataFrame()

        tgt_vals = tgt_food_df[available_cols].values[0]

        distances = []
        for i in food_df.index:
            oth_vals = food_df.loc[i, available_cols].values
            dist = np.sqrt(np.sum(np.square(tgt_vals - oth_vals)))
            distances.append(dist)

        food_df = food_df.copy()
        food_df["tgt_dist"] = distances
        return food_df.sort_values("tgt_dist", ascending=True).head(TOP_N_SIMILAR)

    def _query_single_food(self, food_id: int) -> pd.DataFrame:
        """Query a single food with its nutrient index values."""
        qry = """
        SELECT
            f.id as food_key,
            fi.*
        FROM food_foods f
        JOIN food_foodindex fi ON f.id = fi.food_id
        WHERE f.id = %(food_id)s
        """
        df = pd.read_sql(sql=qry, params={"food_id": food_id}, con=django_connection)
        return df.fillna(0)
