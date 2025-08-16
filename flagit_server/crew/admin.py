from django.contrib import admin
from .models import Crew, CrewMember

# CrewMember를 Crew 페이지에서 인라인으로 보기
class CrewMemberInline(admin.TabularInline):
    model = CrewMember
    extra = 0  # 빈 폼 개수
    readonly_fields = ('user',)  # 필요하면 읽기 전용
    can_delete = True

# Crew Admin
@admin.register(Crew)
class CrewAdmin(admin.ModelAdmin):
    list_display = ('crew_id', 'crewname', 'type', 'leader', 'invitecode', 'member_count')
    list_filter = ('type',)
    search_fields = ('crewname', 'leader__username', 'invitecode')
    inlines = [CrewMemberInline]  # CrewMember 인라인 표시

# CrewMember Admin
@admin.register(CrewMember)
class CrewMemberAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'crew')
    search_fields = ('user__username', 'crew__crewname')
    list_filter = ('crew',)