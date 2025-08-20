from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from .models import Badge

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('email', 'nickname', 'is_staff', 'is_active',)
    list_filter = ('is_staff', 'is_active',)
    search_fields = ('email', 'nickname',)
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password', 'nickname')}),
        ('Permissions', {'fields': ('is_staff', 'is_active')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nickname', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )

@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('badge_name', 'description',)


admin.site.register(User, CustomUserAdmin)