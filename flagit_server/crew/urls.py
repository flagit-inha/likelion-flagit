from django.urls import path
from .views import create_crew, join_crew, get_crew_details, list_crew_members, add_crew_image

urlpatterns = [
    path('join/', join_crew),
    path('<int:crew_id>/', get_crew_details),
    path('<int:crew_id>/members/', list_crew_members),
    path('images/', add_crew_image),
    path('', create_crew),
]