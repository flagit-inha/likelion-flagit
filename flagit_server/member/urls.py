from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import UserSignupView, UserLoginView, user_info, update_user_distance


urlpatterns = [
    path('signup/', UserSignupView.as_view()),
    path('login/', UserLoginView.as_view()),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('records/', update_user_distance),
    path('',user_info)  
]