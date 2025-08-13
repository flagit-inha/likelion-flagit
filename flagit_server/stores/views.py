from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import StoreSerializer
from .models import Store
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance

# Create your views here.
class StoreView(APIView):
    def post(self, request): # 가게 생성은 관리자만 가능
        serializer = StoreSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=s
                            tatus.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request): # 가게 목록 조회
        user_lat = request.query_params.get('lat')
        user_lng = request.query_params.get('lng')

        if user_lat and user_lng:
            user_location = Point(x=user_lng, y=user_lat, srid=4326)
            nearby_stores = Store.objects.annotate(distance=Distance('location', user_location)).order_by('distance')
            stores_data=[]
            for store in nearby_stores:
                stores_data.append({
                    'store_id': store.store_id,
                    'name': store.name,
                    'lat': store.lat,
                    'lng': store.lng,
                    'distance': round(store.distance.m, 1) # 미터 단위
                })

            return Response({
                'status': 'success',
                'code': 200,
                'message': '가게 목록 조회가 완료되었습니다.',
                'stores': stores_data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'status': 'error',
                'code': 400,
                'message': '위치 정보가 필요합니다.'
            }, status=status.HTTP_400_BAD_REQUEST)


