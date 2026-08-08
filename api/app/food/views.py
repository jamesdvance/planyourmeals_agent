from django.db import connection
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from app.food.models import Food
from app.food.serializers import FoodSerializer


class FoodSearchView(APIView):
    """Search foods by name using ILIKE (raw SQL for performance)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        if len(query) < 2:
            return Response(
                {"detail": "Query must be at least 2 characters."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        sql = """
            SELECT id, food_description, brand, calories, protein_g, fat_g, carb_g,
                   serving_size_val, serving_size_unit, image_url
            FROM food_foods
            WHERE food_description ILIKE %(query)s
            ORDER BY food_description
            LIMIT 25
        """
        with connection.cursor() as cursor:
            cursor.execute(sql, {"query": f"%{query}%"})
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return Response(results)


class FoodDetailView(APIView):
    """Get full food detail by ID."""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            food = Food.objects.get(pk=pk)
        except Food.DoesNotExist:
            return Response({"detail": "Food not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = FoodSerializer(food)
        return Response(serializer.data)
