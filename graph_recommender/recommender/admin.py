from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Item, UserPreference, Recommendation


admin.site.unregister(User)  # Отменяет стандартную регистрацию
admin.site.register(User, UserAdmin)  # Регистрируем с кастомным админом

# Регистрируем остальные модели
admin.site.register(Item)
admin.site.register(UserPreference)
admin.site.register(Recommendation)
