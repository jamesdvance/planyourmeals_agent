from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from app.core.models import Profile
from app.core.serializers import NutrientUpdateSerializer, ProfileSerializer


class ProfileView(APIView):
    """GET user profile + nutrient requirements."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            return Response(
                {"detail": "Profile not found."}, status=status.HTTP_404_NOT_FOUND
            )
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)


class NutrientUpdateView(APIView):
    """PUT to update nutrient tracking flags and bounds."""

    permission_classes = [IsAuthenticated]

    def put(self, request):
        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            return Response(
                {"detail": "Profile not found."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = NutrientUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        for field_name, value in serializer.validated_data.items():
            setattr(profile, field_name, value)
        profile.save()

        return Response(ProfileSerializer(profile).data)
