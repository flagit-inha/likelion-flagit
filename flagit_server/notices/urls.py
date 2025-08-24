from django.urls import path
from notices.views import NoticeView, NoticeReactionView

urlpatterns = [
    path('<int:crew_id>/', NoticeView.as_view()), # 공지 조회, 생성성
    path('<int:crew_id>/<int:notice_id>/', NoticeView.as_view()), # 공지 상세 조회
    path('<int:notice_id>/reactions/', NoticeReactionView.as_view()), # 공지 반응 저장
]