from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializers import CrewSerializer, CrewDetailSerializer
from member.serializers import BadgeSerializer

from django.core.files.base import ContentFile
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage

from member.views import assign_badges

from .models import Crew
from .models import CrewMember
import uuid
import secrets

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_crew(request):
    if Crew.objects.filter(leader=request.user).exists():
        return Response(
            {"detail": "이미 크루를 생성하셨습니다. 한 명의 유저는 하나의 크루만 생성할 수 있습니다."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not request.data.get('invitecode'):
        return Response({"detail": "초대코드를 입력해주세요."}, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = CrewSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        crew = serializer.save()
        user = request.user
        assign_badges(user)
        detail_serializer = CrewDetailSerializer(crew)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def join_crew(request):
    invitecode = request.data.get('invitecode')
    crewname = request.data.get('crewname')

    if not invitecode or not crewname:
        return Response({"detail": "초대 코드와 크루명을 모두 입력해주세요."},
                        status=status.HTTP_400_BAD_REQUEST)

    try:
        crew = Crew.objects.get(invitecode=invitecode, crewname=crewname)
    except Crew.DoesNotExist:
        return Response({"detail": "유효하지 않은 초대 코드 또는 크루명입니다."},
                        status=status.HTTP_404_NOT_FOUND)

    if CrewMember.objects.filter(crew=crew, user=request.user).exists():
        return Response({"detail": "이미 가입된 크루입니다."}, status=status.HTTP_400_BAD_REQUEST)
    
    if CrewMember.objects.filter(user=request.user).exists():
        return Response({
            "detail": "이미 다른 크루에 가입되어 있습니다. 한 명의 유저는 하나의 크루에만 가입할 수 있습니다.",
            "user_id": request.user.id,
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user = request.user
    assign_badges(user)
    crew_member = CrewMember.objects.create(crew=crew, user=user)
    
    crew.member_count = CrewMember.objects.filter(crew=crew).count()
    crew.save()

    # 수정된 부분: CrewMemberSerializer가 아닌 직접 데이터를 반환
    data = {
        "user_id": crew_member.user.id,
        "nickname": crew_member.user.nickname,
        "crew_id": crew_member.crew.crew_id,
    }
    return Response(data, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_crew_details(request, crew_id):
    """
    특정 크루의 초대 코드를 조회하는 API 뷰입니다.
    크루의 리더만 접근할 수 있습니다.
    """
    try:
        crew = Crew.objects.get(crew_id=crew_id)
    except Crew.DoesNotExist:
        return Response({"detail": "해당 크루를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

    data = {
        "crew_id": crew.crew_id,
        "crewname": crew.crewname,
        "invitecode": crew.invitecode,
    }
    return Response(data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_crew_members(request, crew_id):
    try:
        crew = Crew.objects.get(crew_id=crew_id)
    except Crew.DoesNotExist:
        return Response({"detail": "해당 크루를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

    # CrewMember 객체들을 쿼리합니다.
    # select_related('user')를 사용하여 User 객체에 대한 추가 쿼리를 방지합니다.
    crew_members = CrewMember.objects.filter(crew=crew).select_related('user')

    data = {
        "crew_logo": crew.crew_logo,
        "crew_image":crew.crew_image,
        "crew_count":crew.member_count,
        "crewname":crew.crewname,
        "members": []
    }

    for member in crew_members:
        # 멤버별 뱃지 로직 적용
        if crew.leader == member.user:
            badge = member.user.badges.order_by('id').first()
        else:
            badge = member.user.badges.order_by('-id').first()

        badge_data = None
        if badge:
            badge_data = BadgeSerializer(badge).data

        data["members"].append({
            "user_id": member.user.id,
            "nickname": member.user.nickname,
            "profile_image": member.user.profile_image,
            "joined_at": member.joined_at,
            "badge": badge_data,
        })
    
    return Response(data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_crew_image(request):
    """
    로그인한 유저가 소속된 크루의 로고 이미지를 업로드합니다.
    """
    user = request.user
    try:
        crew = Crew.objects.filter(leader=user).first()
        if not crew:
            return Response({
                "status": "error",
                "code": 404,
                "message": "사용자가 리더인 크루를 찾을 수 없습니다."
            }, status=404)

        # 업로드된 이미지 가져오기
        crew_logo = request.FILES.get('crew_logo')
        crew_image = request.FILES.get('crew_image')
        if not crew_logo and not crew_image:
            return Response({
                "status": "error",
                "code": 400,
                "message": "업로드할 이미지가 없습니다. crew_logo 또는 crew_image 중 하나 이상 필요합니다."
            }, status=400)

        s3_storage = S3Boto3Storage()
        uploaded_data = {}

        if crew_logo:
            ext = crew_logo.name.split('.')[-1]
            random_filename = f"logo_{secrets.token_hex(4)}.{ext}"
            path = s3_storage.save(f"crew_logo/{random_filename}", ContentFile(crew_logo.read()))
            crew.crew_logo = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{path}"
            uploaded_data['crew_logo'] = crew.crew_logo

        if crew_image:
            ext = crew_image.name.split('.')[-1]
            random_filename = f"image_{secrets.token_hex(4)}.{ext}"
            path = s3_storage.save(f"crew_image/{random_filename}", ContentFile(crew_image.read()))
            crew.crew_image = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{path}"
            uploaded_data['crew_image'] = crew.crew_image

        crew.save()

        return Response({
            "status": "success",
            "code": 200,
            "message": "크루 로고 이미지 업로드 성공",
            "data": {
                "crew_id": crew.crew_id,
                "crew_logo": crew.crew_logo,
                "crew_image": crew.crew_image
            }
        })

    except Exception as e:
        return Response({
            "status": "error",
            "code": 500,
            "message": f"이미지 업로드 중 오류 발생: {str(e)}"
        }, status=500)