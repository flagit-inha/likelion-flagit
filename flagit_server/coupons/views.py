from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import CouponSerializer
from .models import Coupon
from rest_framework.permissions import AllowAny, IsAuthenticated

# Create your views here.
class CouponView(APIView):
    def get_authenticators(self):
        if self.request.method in ("POST", "OPTIONS"):
            return []  # 인증 스킵
        return super().get_authenticators()
    
    def get_permissions(self):
        if self.request.method in ('POST', 'OPTIONS'):
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def post(self, request): # 관리자만 쿠폰 생성 가능
        serializer = CouponSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response({'status': 'success','code' : 201, 'message' :'쿠폰이 생성되었습니다.',
                             'coupon' : serializer.data}, status=status.HTTP_201_CREATED)
        return Response({'status' : 'error', 'code' : 400, 'message' : '쿠폰 생성에 실패했습니다.'}
                        , status=status.HTTP_400_BAD_REQUEST)
    