from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import api_view, permission_classes

from .serializers import UserSignupSerializer, UserLoginSerializer, UserDetailSerializer, ActivityLocationSerializer, FlagSerializer, BadgeSerializer

from .models import ActivityLocation, Flag, User, Badge, UserBadge
from location.models import Location
from crew.models import CrewMember, Crew

from django.core.files.base import ContentFile
from django.conf import settings

import math
from storages.backends.s3boto3 import S3Boto3Storage

def assign_mvp_badge(user):
    try:
        crew_member = CrewMember.objects.get(user=user)
        crew = crew_member.crew
    except CrewMember.DoesNotExist:
        return

    mvp_badge, created= Badge.objects.get_or_create(badge_name='MVP 활동러')

    crew_member_ids = CrewMember.objects.filter(crew=crew).values_list('user_id', flat=True)

    member_activities_count = User.objects.filter(id__in=crew_member_ids).order_by('-activities_count')
    
    if not member_activities_count.exists():
        return
        
    top_user_activities = member_activities_count[0].activities_count
    
    UserBadge.objects.filter(badge=mvp_badge, user__in=crew_member_ids).delete()

    if top_user_activities > 0:
        mvp_users = User.objects.filter(
            id__in=crew_member_ids,
            activities_count=top_user_activities
        )
        for mvp_user in mvp_users:
            UserBadge.objects.get_or_create(user=mvp_user, badge=mvp_badge)

def assign_badges(user):
    # '입문자' 뱃지
    beginner_badge, created = Badge.objects.get_or_create(badge_name='입문자')
    # '초보 탐험가' 뱃지
    novice_badge, created = Badge.objects.get_or_create(badge_name='초보 탐험가')
    # '신의 경지' 뱃지
    expert_badge, created = Badge.objects.get_or_create(badge_name='신의 경지')
    
    # 등업
    if user.activities_count >= 30:
        UserBadge.objects.get_or_create(user=user, badge=expert_badge)
        UserBadge.objects.filter(user=user, badge__in=[novice_badge, beginner_badge]).delete()
        print("aaaaaaaaaaa")
    elif user.activities_count >= 2:
        UserBadge.objects.get_or_create(user=user, badge=novice_badge)
        UserBadge.objects.filter(user=user, badge=beginner_badge).delete()
        print("bbbbbbbbbbb")
    else:
        UserBadge.objects.get_or_create(user=user, badge=beginner_badge)
        print("ccccccccc")
    
    # 누적 거리 기반 뱃지
    total_distance_km = user.total_distance
    
    # '거리 정복자' 뱃지
    distance_conqueror, created = Badge.objects.get_or_create(badge_name='거리 정복자')
    # '로드위의 전사' 뱃지
    road_warrior, created = Badge.objects.get_or_create(badge_name='로드 위의 전사')
    # '끝없는 트랙터' 뱃지
    endless_tractor, created = Badge.objects.get_or_create(badge_name='끝없는 트랙터')

    # 등업
    if total_distance_km >= 300:
        UserBadge.objects.get_or_create(user=user, badge=endless_tractor)
        UserBadge.objects.filter(user=user, badge__in=[road_warrior, distance_conqueror]).delete()
    elif total_distance_km >= 100:
        UserBadge.objects.get_or_create(user=user, badge=road_warrior)
        UserBadge.objects.filter(user=user, badge=distance_conqueror).delete()
    elif total_distance_km >= 50:
        UserBadge.objects.get_or_create(user=user, badge=distance_conqueror)
    else:
        UserBadge.objects.filter(user=user, badge__in=[distance_conqueror, road_warrior, endless_tractor]).delete()

    guide_badge, created = Badge.objects.get_or_create(badge_name='길잡이')
    if Crew.objects.filter(leader=user).exists():
        UserBadge.objects.get_or_create(user=user, badge=guide_badge)
    else:
        UserBadge.objects.filter(user=user, badge=guide_badge).delete()

    assign_mvp_badge(user)


class UserSignupView(APIView):
    permission_classes = [AllowAny]
    serializer_class = UserSignupSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            user = serializer.save()

            refresh = RefreshToken.for_user(user)
            access = refresh.access_token

            data = {
                "status": "success",
                "message": "회원가입이 완료되었습니다.",
                "user": {
                    "id": user.id,
                    "nickname": user.nickname,
                    "email": user.email,
                },
                "refresh_token": str(refresh),
                "access_token": str(access),
            }
            return Response(data, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            # serializer.errors에 있는 내용을 알맞게 변환해서 메시지 처리
            errors = e.detail
            # 간단히 첫 번째 에러 메시지 가져오기 (복잡하면 별도 처리 필요)
            first_error_message = ""
            if isinstance(errors, dict):
                first_key = next(iter(errors))
                first_error_message = errors[first_key][0] if errors[first_key] else ""
            else:
                first_error_message = str(errors)

            return Response({
                "status": "error",
                "message": first_error_message or "입력값이 올바르지 않습니다."
            }, status=status.HTTP_400_BAD_REQUEST)
        
class UserLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        data = {
            "user": {
                "id": user.id,
                "email": user.email,
                "nickname": user.nickname,
            },
            "refresh_token": str(refresh),
            "access_token": str(access),
        }

        return Response(data, status=status.HTTP_200_OK)
    
@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def user_info(request):    
    if request.method == 'GET':
        serializer = UserDetailSerializer(request.user)

        try:
            crew_member = CrewMember.objects.get(user=request.user)
            crew_info = {
                "crewname": crew_member.crew.crewname,
                "invitecode": crew_member.crew.invitecode,
            }
        except CrewMember.DoesNotExist:
            crew_info = None

        return Response({
            "status": "success",
            "user": serializer.data,
            "crew_info": crew_info
        })

    elif request.method == 'PATCH':

        user = request.user

        nickname = request.data.get("nickname")
        password = request.data.get("password")
        password_check = request.data.get("password_check")

        if nickname:
            user.nickname = nickname

        if password or password_check:
            if not password or not password_check:
                return Response({
                    "status": "error",
                    "message": "비밀번호와 비밀번호 확인을 모두 입력해주세요."
                }, status=status.HTTP_400_BAD_REQUEST)
            if password != password_check:
                return Response({
                    "status": "error",
                    "message": "비밀번호가 일치하지 않습니다."
                }, status=status.HTTP_400_BAD_REQUEST)
            user.set_password(password)  # 해시 저장

        user.save()

        serializer = UserDetailSerializer(request.user)

        return Response({
            "status": "success",
            "message": "회원정보가 수정되었습니다.",
            "user": serializer.data
        }, status=status.HTTP_200_OK)
    
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_user_distance(request):
    user = request.user
    distance = request.data.get('distance')

    if distance is None:
        return Response({"status": "error", "message": "distance 필드가 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        distance = float(distance)
        if distance <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        return Response({"status": "error", "message": "distance는 0보다 큰 숫자여야 합니다."}, status=status.HTTP_400_BAD_REQUEST)

    # 누적 거리 갱신
    user.total_distance += distance
    user.activities_count += 1
    assign_badges(user)
    user.save()


    return Response({
        "status": "success",
        "message": "누적 거리가 갱신되었습니다.",
        "total_distance": user.total_distance,
    })

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371  # 지구 반경 (단위: 킬로미터)
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance

@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticated])
def record_user_location(request):

    if request.method == 'POST':
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        description = request.data.get('description', '')
        
        if not latitude or not longitude:
            return Response(
                {"detail": "위도와 경도 정보가 필요합니다."},
                status=status.HTTP_400_BAD_REQUEST
            )

        locations = Location.objects.all()
        
        closest_location_name = "알 수 없는 장소"
        min_distance = float('inf')  # 초기 최소 거리를 무한대로 설정

        # 모든 장소와 사용자의 현재 위치 간의 거리를 계산하여 가장 가까운 장소를 찾습니다.
        for loc in locations:
            distance = haversine_distance(
                latitude, 
                longitude, 
                loc.location_lat, 
                loc.location_lng
            )
            if distance < min_distance:
                min_distance = distance
                closest_location_name = loc.name

        try:
            # ActivityLocation 모델에 방문 기록을 생성합니다.
            ActivityLocation.objects.create(
                user=request.user,
                name=closest_location_name,  # 가장 가까운 장소의 이름을 사용
                description=description,
                location_lat=latitude,
                location_lng=longitude
            )
            return Response(
                {"message": f"가장 가까운 장소 '{closest_location_name}' 방문 기록이 성공적으로 저장되었습니다."},
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {"detail": f"방문 기록 저장 중 오류가 발생했습니다: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    elif request.method == 'GET':
        # 현재 로그인한 유저의 모든 ActivityLocation 기록을 최신순으로 정렬해서 가져옵니다.
        locations = ActivityLocation.objects.filter(user=request.user).order_by('-visited_at')
        
        # Serializer를 사용해 모델 객체를 JSON 데이터로 변환합니다.
        serializer = ActivityLocationSerializer(locations, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
    
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def flags_detail_view(request):
    if request.method == 'GET':
        flags = Flag.objects.filter(user=request.user).order_by('-date', '-time_record')
        serializer = FlagSerializer(flags, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        group_photo_file = request.FILES.get('group_photo')
        group_photo_url = None
        if group_photo_file:
            s3_storage = S3Boto3Storage()
            path = s3_storage.save(f"flag_photos/{group_photo_file.name}", ContentFile(group_photo_file.read()))
            group_photo_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{path}"

        data = request.data.copy()
        if group_photo_url:
            data['group_photo'] = group_photo_url

        try:
            location_id = data.get('location')
            location_instance = Location.objects.get(id=location_id)
            data['location'] = location_instance.id
        except Location.DoesNotExist:
            return Response({"location": ["유효하지 않은 장소 ID입니다."]}, status=status.HTTP_400_BAD_REQUEST)

        crew_members_ids = data.pop('crew_members', [])
        if not isinstance(crew_members_ids, list):
            crew_members_ids = []
        
        crew_members_ids = [int(cid) for cid in crew_members_ids if str(cid).isdigit()]

        serializer = FlagSerializer(data=data)
        if serializer.is_valid():
            flag = serializer.save(user=request.user, location=location_instance)

            if crew_members_ids:
                members = CrewMember.objects.filter(id__in=crew_members_ids)
                flag.crew_members.set(members)
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_badges_view(request):
    user = request.user
    assign_badges(user=user)

    badges = request.user.badges.all()

    serializer = BadgeSerializer(badges, many=True)
    
    return Response(serializer.data, status=status.HTTP_200_OK)