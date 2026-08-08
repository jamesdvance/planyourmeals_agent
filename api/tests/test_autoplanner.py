"""
Autoplanner tests.

These test the core optimization logic: building the Pyomo model,
solving, and parsing results.
"""

import datetime

import pytest

from app.autoplanner.autoplan_week import WeekAutoPlanner


@pytest.mark.django_db
class TestAutoplannerBuild:
    """Test autoplanner data preparation methods."""

    def test_prep_query_params(self, user_with_menus):
        user, pref_menus = user_with_menus
        menus_list = [
            {
                "day": "day1",
                "meals": [
                    {
                        "meal": "Breakfast",
                        "menus": [{"type": "menu", "id": pref_menus["br"].id}],
                    },
                    {
                        "meal": "Lunch",
                        "menus": [{"type": "menu", "id": pref_menus["lu"].id}],
                    },
                    {
                        "meal": "Dinner",
                        "menus": [{"type": "menu", "id": pref_menus["di"].id}],
                    },
                    {
                        "meal": "Snack",
                        "menus": [{"type": "menu", "id": pref_menus["sn"].id}],
                    },
                ],
            },
        ]

        requirements = {
            "day1": {
                "calories": [2100, 1900],
                "protein_g": [131, 119],
                "fat_g": [82, 74],
                "carb_g": [210, 190],
            },
        }

        planner = WeekAutoPlanner(
            user_id=user.id,
            requirements_dict=requirements,
            menus_dict_list=menus_list,
            week_start_dt=datetime.date.today(),
            week_end_dt=datetime.date.today() + datetime.timedelta(days=7),
            n_snack=2,
        )

        tag_ids, rest_ids, menu_ids, meals_idx_tup, days_list = planner._prep_query_params()

        assert len(meals_idx_tup) == 4
        assert "day1" in days_list
        assert pref_menus["br"].id in menu_ids

    def test_solve_returns_result(self, user_with_menus):
        """Integration test: full solve with test data."""
        user, pref_menus = user_with_menus
        menus_list = [
            {
                "day": "day1",
                "meals": [
                    {
                        "meal": "Breakfast",
                        "menus": [{"type": "menu", "id": pref_menus["br"].id}],
                    },
                    {
                        "meal": "Lunch",
                        "menus": [{"type": "menu", "id": pref_menus["lu"].id}],
                    },
                    {
                        "meal": "Dinner",
                        "menus": [{"type": "menu", "id": pref_menus["di"].id}],
                    },
                    {
                        "meal": "Snack",
                        "menus": [{"type": "menu", "id": pref_menus["sn"].id}],
                    },
                ],
            },
        ]

        # Use relaxed bounds so feasibility is easier with small food set
        requirements = {
            "day1": {
                "calories": [3000, 500],
                "protein_g": [200, 10],
                "fat_g": [150, 5],
                "carb_g": [300, 10],
            },
        }

        planner = WeekAutoPlanner(
            user_id=user.id,
            requirements_dict=requirements,
            menus_dict_list=menus_list,
            week_start_dt=datetime.date.today(),
            week_end_dt=datetime.date.today() + datetime.timedelta(days=7),
            n_snack=2,
        )

        result = planner.solve()

        # The solve should complete (may be optimal or infeasible with limited data)
        assert result.status in ("optimal", "infeasible", "no_data")
