"""
API endpoint smoke tests using DRF test client.
"""

import datetime

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from app.food.models import Food
from app.plan.models import FoodAmount, Meal, PlanMeal


@pytest.fixture
def api_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
class TestProfileAPI:
    def test_get_profile(self, api_client, profile):
        response = api_client.get("/api/v1/core/profile/")
        assert response.status_code == 200
        assert "cal_ub" in response.data
        assert "cal_lb" in response.data

    def test_update_nutrients(self, api_client, profile):
        response = api_client.put(
            "/api/v1/core/profile/nutrients/",
            {"cal_ub": 2200, "cal_lb": 1800, "fib": True},
            format="json",
        )
        assert response.status_code == 200
        assert float(response.data["cal_ub"]) == 2200.0
        assert response.data["fib"] is True


@pytest.mark.django_db
class TestFoodAPI:
    def test_search_foods(self, api_client, sample_food):
        response = api_client.get("/api/v1/food/search/?q=Chicken")
        assert response.status_code == 200
        assert len(response.data) >= 1
        assert "Chicken" in response.data[0]["food_description"]

    def test_search_too_short(self, api_client):
        response = api_client.get("/api/v1/food/search/?q=C")
        assert response.status_code == 400

    def test_food_detail(self, api_client, sample_food):
        response = api_client.get(f"/api/v1/food/{sample_food.pk}/")
        assert response.status_code == 200
        assert response.data["food_description"] == "Chicken Breast, grilled"

    def test_food_detail_not_found(self, api_client):
        response = api_client.get("/api/v1/food/99999/")
        assert response.status_code == 404


@pytest.mark.django_db
class TestPlanAPI:
    def test_get_day_plan_empty(self, api_client):
        response = api_client.get("/api/v1/plan/day/2026-02-08/")
        assert response.status_code == 200
        assert response.data == []

    def test_get_day_plan_with_meal(self, api_client, user, sample_food):
        meal = Meal.objects.create(user=user, mealname="Test Dinner")
        FoodAmount.objects.create(food=sample_food, meal=meal, amt=1)
        PlanMeal.objects.create(
            user=user,
            plan_date=datetime.date(2026, 2, 8),
            meal_type="Dinner",
            ml_cd="di",
            meal=meal,
        )

        response = api_client.get("/api/v1/plan/day/2026-02-08/")
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["meal_type"] == "Dinner"

    def test_invalid_date(self, api_client):
        response = api_client.get("/api/v1/plan/day/not-a-date/")
        assert response.status_code == 400
