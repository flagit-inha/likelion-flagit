from django.contrib import admin
from .models import Crew, CrewMember

# CrewMember 인라인 (Crew 페이지 안에서 함께 보기)
class CrewMemberInline(admin.TabularInline):
    model = CrewMember
    extra = 0
    readonly_fields = ('user',)
    can_delete = True


# Crew Admin
@admin.register(Crew)
class CrewAdmin(admin.ModelAdmin):
    model = Crew
    list_display = ('crew_id', 'crewname', 'crew_type', 'leader', 'invitecode', 'member_count')
    list_filter = ('crew_type',)
    search_fields = ('crewname', 'leader__email', 'invitecode')
    ordering = ('crew_id',)
    inlines = [CrewMemberInline]

    fieldsets = (
        (None, {
            'fields': ('crewname', 'crew_type', 'leader', 'invitecode')
        }),
        ('추가 정보', {
            'fields': ('member_count',),
        }),
    )
    readonly_fields = ('member_count',)  # member_count는 계산값이니까 읽기 전용


# CrewMember Admin
@admin.register(CrewMember)
class CrewMemberAdmin(admin.ModelAdmin):
    model = CrewMember
    list_display = ('id', 'user', 'crew')
    list_filter = ('crew',)
    search_fields = ('user__email', 'crew__crewname')
    ordering = ('id',)