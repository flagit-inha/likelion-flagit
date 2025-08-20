from django.shortcuts import render
from .serializers import NoticeSerializer, NoticeReactionSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from crew.models import Crew
from crew.models import CrewMember
from notices.models import Notice, NoticeReaction

# Create your views here.
class NoticeView(APIView):
    def post(self, request): # 공지 생성하기
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
    
    def get(self, request, crew_id=None, notice_id=None): # 공지 조회하기
        if crew_id:
            try:
                crew = Crew.objects.get(crew_id=crew_id)
                
                # 공지 상세 조회 (notice_id가 있는 경우)
                if notice_id:
                    try:
                        notice = Notice.objects.get(id=notice_id, crew=crew)
                        return Response({
                            'status': 'success', 'code': 200, 
                            'message': '공지 상세 조회가 완료되었습니다.',
                            'notice': NoticeSerializer(notice).data
                        }, status=status.HTTP_200_OK)
                    except Notice.DoesNotExist:
                        return Response({
                            'status': 'error', 
                            'code': 404, 
                            'message': '존재하지 않는 공지입니다.'
                        }, status=status.HTTP_404_NOT_FOUND)
                
                # 크루의 모든 공지 조회 (notice_id가 없는 경우)
                else:
                    notices = Notice.objects.filter(crew=crew).order_by('-created_at')
                    return Response({
                        'status': 'success', 
                        'code': 200, 
                        'message': '공지 조회가 완료되었습니다.',
                        'notices': NoticeSerializer(notices, many=True).data
                    }, status=status.HTTP_200_OK)
                    
            except Crew.DoesNotExist:
                return Response({
                    'status': 'error', 
                    'code': 404, 
                    'message': '존재하지 않는 크루입니다.'
                }, status=status.HTTP_404_NOT_FOUND) 

class NoticeReactionView(APIView):
    def post(self, request, notice_id):
        try:
            notice = Notice.objects.get(id=notice_id) # 공지 가져오기
            notice_reaction = NoticeReaction.objects.filter(notice=notice, crew_member__user=request.user).first()

            if notice_reaction:
                serializer = NoticeReactionSerializer(notice_reaction, data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response({'status': 'success', 'code': 200, 'message': '공지 반응이 수정되었습니다.',
                                    'reaction': serializer.data}, status=status.HTTP_200_OK)
                else:
                    return Response({'status': 'error', 'code': 400, 'message': '잘못된 요청입니다.'}, status=status.HTTP_400_BAD_REQUEST)

            crew_member = CrewMember.objects.get(user=request.user, crew=notice.crew)
            serializer = NoticeReactionSerializer(data=request.data)

            if serializer.is_valid():
                serializer.save(
                    notice=notice,
                    crew_member=crew_member,
                    reaction=serializer.validated_data['reaction']
                    )
                return Response({'status': 'success', 'code': 201, 'message': '공지 반응이 저장되었습니다.',
                                  'reaction': serializer.data}, status=status.HTTP_201_CREATED)
            else:
                return Response({'status': 'error', 'code': 400, 'message': '잘못된 요청입니다.'}, status=status.HTTP_400_BAD_REQUEST)

        except Notice.DoesNotExist:
            return Response({'status': 'error', 'code': 404, 'message': '존재하지 않는 공지입니다.'}, status=status.HTTP_404_NOT_FOUND)
        except CrewMember.DoesNotExist:
            return Response({'status': 'error', 'code': 404, 'message': '존재하지 않는 크루 멤버입니다.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'status': 'error', 'code': 500, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

