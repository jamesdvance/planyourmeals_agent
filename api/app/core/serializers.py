from rest_framework import serializers

from app.core.models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Profile
        exclude = ["id", "user"]


class NutrientUpdateSerializer(serializers.Serializer):
    """Serializer for updating nutrient bounds on a profile."""

    # Each nutrient can have: track flag, upper bound, lower bound
    cal = serializers.BooleanField(required=False)
    cal_ub = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
    cal_lb = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
    pro = serializers.BooleanField(required=False)
    pro_ub = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
    pro_lb = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
    car = serializers.BooleanField(required=False)
    car_ub = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
    car_lb = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
    fat = serializers.BooleanField(required=False)
    fat_ub = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
    fat_lb = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
    stf = serializers.BooleanField(required=False)
    stf_ub = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
    stf_lb = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
    fib = serializers.BooleanField(required=False)
    fib_ub = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
    fib_lb = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
    sug = serializers.BooleanField(required=False)
    sug_ub = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
    sug_lb = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
    sod = serializers.BooleanField(required=False)
    sod_ub = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
    sod_lb = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
    cho = serializers.BooleanField(required=False)
    cho_ub = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
    cho_lb = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
    clc = serializers.BooleanField(required=False)
    clc_ub = serializers.DecimalField(max_digits=7, decimal_places=2, required=False)
    clc_lb = serializers.DecimalField(max_digits=7, decimal_places=2, required=False)
    irn = serializers.BooleanField(required=False)
    irn_ub = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
    irn_lb = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
    vta = serializers.BooleanField(required=False)
    vta_ub = serializers.DecimalField(max_digits=7, decimal_places=2, required=False)
    vta_lb = serializers.DecimalField(max_digits=7, decimal_places=2, required=False)
    vtc = serializers.BooleanField(required=False)
    vtc_ub = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
    vtc_lb = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
