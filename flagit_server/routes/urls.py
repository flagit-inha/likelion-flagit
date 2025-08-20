from django.urls import path
from . import views

app_name = 'routes'

urlpatterns = [
	# 경로 추천 및 저장
	path('', views.RouteRecommendationView.as_view()),
	# 경로 조회회
	path('<int:route_id>/', views.RouteRetrieveView.as_view()),
]
