import datetime

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from app.plan.models import PlanMeal
from app.plan.serializers import PlanMealSerializer


class DayPlanView(APIView):
    """GET a user's plan for a given date."""

    permission_classes = [IsAuthenticated]

    def get(self, request, date):
        try:
            plan_date = datetime.date.fromisoformat(date)
        except ValueError:
            return Response(
                {"detail": "Invalid date format. Use YYYY-MM-DD."}, status=400
            )

        plan_meals = PlanMeal.objects.filter(
            user=request.user, plan_date=plan_date
        ).select_related("meal").prefetch_related("meal__food_amounts__food")

        serializer = PlanMealSerializer(plan_meals, many=True)
        return Response(serializer.data)
