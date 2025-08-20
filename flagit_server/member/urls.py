from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import UserSignupView, UserLoginView, user_info, update_user_distance, record_user_location, flags_detail_view, user_badges_view


urlpatterns = [
    path('signup/', UserSignupView.as_view()),
    path('login/', UserLoginView.as_view()),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('records/', update_user_distance),
    path('location/', record_user_location),
    path('flag/', flags_detail_view),
    path('badge/', user_badges_view),
    path('',user_info),
]