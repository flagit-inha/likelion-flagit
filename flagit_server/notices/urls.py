from django.urls import path
from notices.views import NoticeView

urlpatterns = [
    path('', NoticeView.as_view()), # 공지 생성
    path('<int:crew_id>/', NoticeView.as_view()), # 공지 조회
    path('<int:crew_id>/<int:notice_id>/', NoticeView.as_view()), # 공지 상세 조회
]