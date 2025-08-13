from django.urls import path
from .views import StoreView

urlpatterns = [
    path('admin/', StoreView.as_view()), 
    path('nearby/', StoreView.as_view()),
]