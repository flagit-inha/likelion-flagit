from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializers import CrewSerializer

from .models import Crew
from .models import CrewMember

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_crew(request):
    if Crew.objects.filter(leader_id=request.user).exists():
        return Response(
            {"detail": "이미 크루를 생성하셨습니다. 한 명의 유저는 하나의 크루만 생성할 수 있습니다."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    serializer = CrewSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        crew = serializer.save()  # leader_id에 현재 로그인한 유저 할당
        return Response({
            "crew_id": crew.crew_id,
            "crewname": crew.crewname,
            "type": crew.type,
            "invitecode": crew.invitecode,
            "member_count": crew.member_count,
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def join_crew(request):
    invitecode = request.data.get('invitecode')
    if not invitecode:
        return Response({"detail": "초대 코드를 입력해주세요."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        crew = Crew.objects.get(invitecode=invitecode)
    except Crew.DoesNotExist:
        return Response({"detail": "유효하지 않은 초대 코드입니다."}, status=status.HTTP_404_NOT_FOUND)

    if CrewMember.objects.filter(crew=crew, user=request.user).exists():
        return Response({"detail": "이미 가입된 크루입니다."}, status=status.HTTP_400_BAD_REQUEST)
    
    if CrewMember.objects.filter(user=request.user).exists():
        return Response({"detail": "이미 다른 크루에 가입되어 있습니다. 한 명의 유저는 하나의 크루에만 가입할 수 있습니다."}, status=status.HTTP_400_BAD_REQUEST)
        
    crew_member = CrewMember.objects.create(crew=crew, user=request.user)
    
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

    # 반복문(List Comprehension)을 사용해 데이터를 구성합니다.
    data = [
        {
            "user_id": member.user.id,
            "nickname": member.user.nickname,
            "profile_image": member.user.profile_image,
        }
        for member in crew_members
    ]
    
    return Response(data, status=status.HTTP_200_OK)
