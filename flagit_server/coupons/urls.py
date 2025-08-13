from django.urls import path
from .views import CouponView

urlpatterns=[
    path('admin/', CouponView.as_view()),

]