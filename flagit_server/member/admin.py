from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from .models import Badge, UserBadge

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('email', 'nickname', 'is_staff', 'is_active',)
    list_filter = ('is_staff', 'is_active',)
    search_fields = ('email', 'nickname',)
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password', 'nickname')}),
        ('Permissions', {'fields': ('is_staff', 'is_active')}),
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

@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ('user', 'badge',)
    list_filter = ('user', 'badge',)
    search_fields = ('user__nickname', 'badge__badge_name',)


admin.site.register(User, CustomUserAdmin)