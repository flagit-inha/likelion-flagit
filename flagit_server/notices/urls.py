from django.urls import path
from notices.views import NoticeView

urlpatterns = [
    path('', NoticeView.as_view()),
    path('<int:crew_id>/')
]