from django.shortcuts import render
from .serializers import NoticeSerializer, NoticeReactionSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from crew.models import Crew

# Create your views here.
class NoticeView(APIView):
    def post(self, request):
        serializer = NoticeSerializer(data=request.data)

        if serializer.is_valid():

            crew_id=serializer.validated_data.get('crew').crew_id

            try:
                crew=Crew.objects.get(crew_id=crew_id)
                current_user_id=request.user.id
                if current_user_id ==crew.leader_id:
                    notice=serializer.save()
                    return Response({'status': 'success', 'code': 201, 'message' : '공지가 생성되었습니다.',
                                      'notice': NoticeSerializer(notice).data}, 
                                    status=status.HTTP_201_CREATED)
                else:
                    return Response({'status' : 'error', 'code' : 403,
                                      'message' : '크루 리더만 공지 작성이 가능합니다.'}, status=status.HTTP_403_FORBIDDEN)
            except Crew.DoesNotExist:
                    return Response({'status' : 'error', 'code' : 404, 'message' : '존재하지 않는 크루입니다.'},
                                     status=status.HTTP_404_NOT_FOUND)

        return Response({'status' : 'error', 'code' : 400, 'message' : '잘못된 요청입니다.'}, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request):
        