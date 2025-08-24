from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance

from .models import Route
from stores.models import Store
from routes.models import Route
from location.models import Location
from member.models import ActivityLocation
from member.models import User
from member.views import assign_badges, assign_mvp_badge

from .serializers import (
	RouteSerializer, 
	RouteRecommendationRequestSerializer,
	RouteRecommendationResponseSerializer,
)
from .services import RouteRecommendationService
from crew.models import CrewMember
from rest_framework.views import APIView

class RouteRecommendationView(APIView):
	"""
	경로 추천 및 저장
	"""
	
	def post(self, request):
		serializer = RouteRecommendationRequestSerializer(data=request.data)
		if serializer.is_valid():
			try:
				# 사용자 소속 크루 및 타입
				crew_member = CrewMember.objects.filter(user=request.user).first()
				if not crew_member:
					return Response({'error': '사용자가 속한 크루가 없습니다.'}, status=status.HTTP_400_BAD_REQUEST)
				crew_type = crew_member.crew.crew_type

				start_location = serializer.validated_data['start_location']
				target_distance = serializer.validated_data['target_distance']

				# 추천 서비스 생성
				recommendation_service = RouteRecommendationService()
				
				# 시작 위치를 위도/경도로 변환
				start_lat, start_lng = recommendation_service.convert_location_to_coordinates(start_location)

				# PostGIS로 시작점 반경 내 제휴 가게 1곳 찾기 
				user_point = Point(start_lng, start_lat, srid=4326)
				candidate = (
					Store.objects.filter(
						location__distance_lte=(user_point, D(km=target_distance))
					)
					.first()
				)

				waypoint = None
				if candidate:
					waypoint = {
						'lat': candidate.lat,
						'lng': candidate.lng,
						'name': candidate.name,
						'is_partner': True,
					}

				# 추천 생성
				route_path = recommendation_service.recommend_route(
					start_location=start_location,
					target_distance=target_distance,
					crew_type=crew_type,
					waypoint=waypoint,
				)

				# 저장
				created_route = Route.objects.create(
					crew_member=crew_member,
					crew_type=crew_type,
					start_location=start_location,
					target_distance=target_distance,
					route_path=route_path,
				)

				response_data = {
					'route_id': created_route.route_id,
					'route_path': route_path,
				}
				return Response({"status" : "success", "code" : 200, "message" : "경로 추천 성공", "data" : RouteRecommendationResponseSerializer(response_data).data}
					, status=status.HTTP_200_OK)

			except ValueError as e:
				return Response({"status" : "error", "code" : 400, "message" : str(e)}, status=status.HTTP_400_BAD_REQUEST)
			except Exception as e:
				return Response({"status" : "error", "code" : 500, "message" : f'경로 추천 중 오류 발생: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

		return Response({"status" : "error", "code" : 400, "message" : serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class RouteRetrieveView(APIView):
	"""
	저장된 경로 단건 조회 API (route_id로 조회)
	"""
	
	def get(self, request, route_id: int):
		route = get_object_or_404(Route, route_id=route_id)
		response_data = {
			'route_id': route.route_id,
			'route_path': route.route_path,
		}
		return Response({"status" : "success", "code" : 200, "message" : "경로 조회 성공", "data" : RouteRecommendationResponseSerializer(response_data).data}
				  , status=status.HTTP_200_OK)
	def post(self, request, route_id: int):
		try:
			route = get_object_or_404(Route, route_id = route_id)
		except Route.DoesNotExist:
			return Response({
                "status": "error",
                "code": 404,
                "message": "해당 경로를 찾을 수 없습니다."
            }, status=status.HTTP_404_NOT_FOUND)
		
		try:
			Location.objects.create(
				location_distance=route.target_distance,
				name=route.start_location,
			)
		except Exception as e:
			return Response({
                "status": "error",
                "code": 500,
                "message": f"Location 저장 중 오류 발생: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

		try:
			ActivityLocation.objects.create(
                user=request.user,
                location_name=route.start_location,  # 가장 가까운 장소의 이름을 사용
				location_distance = route.target_distance,
            )
			return Response(
                {"message": f"방문 기록이 성공적으로 저장되었습니다."},
                status=status.HTTP_201_CREATED
            )
		except Exception as e:
			return Response(
                {"detail": f"방문 기록 저장 중 오류가 발생했습니다: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


		if not request.user.is_authenticated:
			return Response({
                "status": "error",
                "code": 401,
                "message": "사용자 인증이 필요합니다."
            }, status=status.HTTP_401_UNAUTHORIZED)
		
		try:
			member = request.user
			member.total_distance += route.target_distance
			member.activities_count += 1
			assign_badges(member)
			member.save()
		except User.DoesNotExist:
			return Response({
                "status": "error",
                "code": 404,
                "message": "사용자 정보를 찾을 수 없습니다."
            }, status=status.HTTP_404_NOT_FOUND)
		except Exception as e:
			return Response({
                "status": "error",
                "code": 500,
                "message": f"총 거리 업데이트 중 오류 발생: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
		
		return Response({
            "message": "경로 기록 및 총 거리 업데이트 성공",
            "data": {
                "route_id": route.route_id,
                "recorded_target_distance": route.target_distance,
                "updated_total_distance": member.total_distance
            }
        }, status=status.HTTP_201_CREATED)