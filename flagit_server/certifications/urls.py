from django.urls import path
from .views import CertificationView, CertificationStatusView2

urlpatterns = [
    path('<int:store_id>/', CertificationView.as_view()), # 인증 요청
    path('<int:certification_id>/', CertificationStatusView2.as_view()), # 인증 상태 조회
]   