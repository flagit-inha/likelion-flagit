import google.generativeai as genai
from django.conf import settings
import json
from typing import List, Dict, Any, Optional, Tuple

class RouteRecommendationService:
	def __init__(self):
		# Django settings에서 Gemini API 키와 모델명 가져오기
		api_key = getattr(settings, 'GEMINI_API_KEY', None)
		model_name = getattr(settings, 'GEMINI_MODEL_NAME', 'gemini-1.5-flash')
		
		if not api_key:
			raise ValueError("GEMINI_API_KEY가 Django settings에 설정되지 않았습니다.")
		
		genai.configure(api_key=api_key)
		
		# 경로 추천용 설정
		route_generation_config = {
			"response_mime_type" : "application/json",
			"response_schema" : {
				"type" : "array",
				"items" : {
					"type" : "object",
					"properties" : {
						"lat" : {"type" : "number"},
						"lng" : {"type" : "number"},
						"name" : {"type" : "string"},
						"description" : {"type" : "string"},
						"is_partner" : {"type" : "boolean"},
					},
					"required" : ["lat", "lng", "is_partner"],
				},
			},
		}
		
		# 위치 변환용 설정
		location_generation_config = {
			"response_mime_type" : "application/json",
			"response_schema" : {
				"type" : "object",
				"properties" : {
					"lat" : {"type" : "number"},
					"lng" : {"type" : "number"},
				},
				"required" : ["lat", "lng"],
			},
		}
		
		self.route_model = genai.GenerativeModel(model_name, generation_config=route_generation_config)
		self.location_model = genai.GenerativeModel(model_name, generation_config=location_generation_config)
	
	def convert_location_to_coordinates(self, location_name: str) -> Tuple[float, float]:
		"""
		위치 이름을 위도/경도로 변환합니다.
		"""
		prompt = f"""
당신은 위치 정보를 위도와 경도로 변환하는 전문가입니다.
다음 위치의 정확한 위도와 경도를 찾아주세요:

위치: {location_name}

다음 형식으로 JSON을 반환하세요 (설명 없이 JSON만):
{{"lat": 위도, "lng": 경도}}

주의사항:
1. 한국의 실제 위치를 기준으로 정확한 좌표를 제공하세요
2. 위도는 -90에서 90 사이의 값이어야 합니다
3. 경도는 -180에서 180 사이의 값이어야 합니다
4. 무조건 주어진 JSON 형식만 반환하세요
"""

		try:
			response = self.location_model.generate_content(prompt)
			content = response.text.strip()
			location_data = json.loads(content)

			if not isinstance(location_data, dict) or 'lat' not in location_data or 'lng' not in location_data:
				raise ValueError("응답이 올바른 형식이 아닙니다.")

			lat = float(location_data['lat'])
			lng = float(location_data['lng'])

			# 좌표 유효성 검사
			if not (-90 <= lat <= 90):
				raise ValueError("위도는 -90에서 90 사이의 값이어야 합니다.")
			if not (-180 <= lng <= 180):
				raise ValueError("경도는 -180에서 180 사이의 값이어야 합니다.")

			return lat, lng

		except json.JSONDecodeError as e:
			raise ValueError(f"JSON 파싱 오류: {e}")
		except Exception as e:
			raise ValueError(f"위치 변환 중 오류 발생: {e}")
	
	def recommend_route(
		self,
		start_location: str,
		target_distance: float,
		crew_type: str = 'running',
		waypoint: Optional[Dict[str, Any]] = None,
	) -> List[Dict[str, Any]]:
		"""
		시작 위치 문자열과 목표 거리를 기반으로 경로를 추천합니다.
		"""
		# 시작 위치를 위도/경도로 변환
		start_lat, start_lng = self.convert_location_to_coordinates(start_location)
		
		# 크루 타입에 따른 프롬프트 조정
		activity_map = {
			'running': '러닝',
			'hiking': '등산',
			'riding': '라이딩'
		}
		activity = activity_map.get(crew_type, '러닝')

		waypoint_block = ""
		if waypoint:
			w_name = waypoint.get('name', '제휴 가게')
			w_lat = waypoint.get('lat')
			w_lng = waypoint.get('lng')
			waypoint_block = f"""
반드시 아래 제휴 가게를 경유하세요 (정확히 이 좌표를 포함):
- name: {w_name}
- lat: {w_lat}
- lng: {w_lng}
이 지점은 JSON에 is_partner: true로 표기하세요. 그 외 지점은 is_partner: false로 표기하세요.
"""

		prompt = f"""
당신은 {activity} 경로 추천 전문가입니다.
다음 조건에 맞는 경로를 추천해주세요:

시작 위치: {start_location} (위도 {start_lat}, 경도 {start_lng})
목표 거리: {target_distance}km
활동 유형: {activity}
{waypoint_block}

다음 형식으로 JSON 배열을 반환하세요(설명 없이 JSON만):
[
	{{"lat": 위도, "lng": 경도, "name": "장소명", "description": "간단한 설명", "is_partner": false}},
	...
]

주의사항:
1. 시작 위치에서 시작해서 다시 시작 위치로 돌아오는 원형 경로를 만들어주세요
2. 총 거리를 목표 거리와 비슷하게 맞춰주세요
3. 지점 간 간격을 적절히 유지하세요
4. {activity}에 적합한 실제 장소를 포함하세요
5. 무조건 주어진 JSON 형식만 반환하세요
"""

		try:
			response = self.route_model.generate_content(prompt)
			content = response.text.strip()
			route_data = json.loads(content)

			if not isinstance(route_data, list):
				raise ValueError("응답이 리스트 형태가 아닙니다.")

			validated_route: List[Dict[str, Any]] = []
			for point in route_data:
				if isinstance(point, dict) and 'lat' in point and 'lng' in point:
					validated_point = {
						'lat': float(point['lat']),
						'lng': float(point['lng']),
						'name': point.get('name', ''),
						'description': point.get('description', ''),
						'is_partner': bool(point.get('is_partner', False)),
					}
					validated_route.append(validated_point)

			# 나머지 포인트에 is_partner 키가 없으면 False로 표준화
			for p in validated_route:
				if 'is_partner' not in p:
					p['is_partner'] = False

			return validated_route

		except json.JSONDecodeError as e:
			raise ValueError(f"JSON 파싱 오류: {e}")
		except Exception as e:
			raise ValueError(f"경로 추천 중 오류 발생: {e}")

# 기존 함수는 호환성을 위해 유지
def get_start_location(start_location: str) -> Tuple[float, float]:
	"""
	출발 위치를 경도, 위도 형식으로 변환 (기존 호환성용)
	"""
	lat, lng = start_location.split(',')
	return float(lat), float(lng)