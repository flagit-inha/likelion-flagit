from django.urls import path
from notices.views import NoticeView, NoticeReactionView

urlpatterns = [
    path('', NoticeView.as_view()), # 공지 생성
    path('<int:crew_id>/', NoticeView.as_view()), # 공지 조회
    path('<int:crew_id>/<int:notice_id>/', NoticeView.as_view()), # 공지 상세 조회
    path('<int:crew_id>/<int:notice_id>/reaction/', NoticeReactionView.as_view()), # 공지 반응 저장
]