import datetime

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .alternatives_engine import AlternativesEngine
from .autoplan_week import WeekAutoPlanner


class AutoplanWeekView(APIView):
    """Generate a weekly meal plan using the Pyomo optimizer."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        user_id = request.user.id

        requirements_dict = data.get("requirements_dict", {})
        menus_dict_list = data.get("menus_dict_list", [])
        week_start_dt = datetime.date.fromisoformat(data["week_start_dt"])
        week_end_dt = datetime.date.fromisoformat(data["week_end_dt"])
        n_snack = data.get("n_snack", 2)

        planner = WeekAutoPlanner(
            user_id=user_id,
            requirements_dict=requirements_dict,
            menus_dict_list=menus_dict_list,
            week_start_dt=week_start_dt,
            week_end_dt=week_end_dt,
            n_snack=n_snack,
        )

        result = planner.solve()

        if result.results_df.empty:
            return Response(
                {"status": result.status, "plan": []},
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "status": result.status,
                "solve_time_seconds": round(result.solve_time_seconds, 2),
                "plan": result.results_df.to_dict("records"),
            },
            status=status.HTTP_200_OK,
        )


class GetFoodAlternativeView(APIView):
    """Find alternative foods for a given food in a meal slot."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        user_id = request.user.id

        reqs_dict = data.get("reqs_dict", {})
        food_id = data["food_id"]

        # For now, pass an empty food_df — full implementation needs
        # the food query from the user's menu context
        import pandas as pd

        food_df = pd.DataFrame()

        engine = AlternativesEngine(
            reqs_dict=reqs_dict,
            food_df=food_df,
            food_id=food_id,
            user_id=user_id,
        )

        result = engine.find_alternatives_and_similar()

        return Response(
            {
                "alternatives": (
                    result.alternatives_df.to_dict("records")
                    if not result.alternatives_df.empty
                    else []
                ),
                "similar": (
                    result.similar_df.to_dict("records") if not result.similar_df.empty else []
                ),
            },
            status=status.HTTP_200_OK,
        )
