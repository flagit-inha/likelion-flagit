from django.urls import path
from .views import CertificationView, CertificationStatusView

urlpatterns = [
    path('<int:store_id>/', CertificationView.as_view()),
    path('status/<int:certification_id>/', CertificationStatusView.as_view()),
]   