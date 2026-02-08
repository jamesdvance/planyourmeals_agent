from django.contrib import admin

from app.core.models import (
    FoodPreferences,
    PrefMenu,
    Profile,
    PublicMenu,
    UserMenu,
    UserProbRejectFood,
)

admin.site.register(Profile)
admin.site.register(PublicMenu)
admin.site.register(UserMenu)
admin.site.register(PrefMenu)
admin.site.register(FoodPreferences)
admin.site.register(UserProbRejectFood)
