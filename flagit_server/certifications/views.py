from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.utils import timezone
from .serializers import CertificationSerializer
from .models import Certification
from stores.models import Store
from coupons.models import Coupon
from django.db import transaction
from django.contrib.gis.measure import D
from datetime import timedelta
# Create your views here.
class CertificationView(APIView):
    def post(self, request, store_id):
        try:
            store = Store.objects.get(store_id=store_id)
        except Store.DoesNotExist:
            return Response({'status' : 'error', 'code' : 404, 'message' : '가게가 존재하지 않습니다.'}
                            , status=status.HTTP_404_NOT_FOUND)

        serializer = CertificationSerializer(data=request.data, context={'request' : request, 'store' : store})

        if serializer.is_valid():
            certification = serializer.save()
            return Response({'status' : 'success', 'code' : 201, 'message' : '인증 요청을 보냈습니다.', 'certification' : serializer.data}
                            , status=status.HTTP_201_CREATED)
        else:
            return Response({'status' : 'error', 'code' : 400, 'message' : '인증 요청에 실패했습니다.'}
                            , status=status.HTTP_400_BAD_REQUEST)

class CertificationStatusView(APIView):
    def get(self, request, certification_id):
        try:
            certification = Certification.objects.get(
                certification_id=certification_id,
                member=request.user
            )
        except Certification.DoesNotExist:
            return Response({
                'status': 'error',
                'code': 404,
                'message': '인증 요청을 찾을 수 없습니다.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # 이미 완료된 경우
        if certification.status == 'completed':
            try:
                coupon = Coupon.objects.get(store=certification.store)
                return Response({
                    'status': 'completed',
                    'code': 200,
                    'message': '인증이 완료되었습니다!',
                    'coupon': {
                        'coupon_id': coupon.coupon_id,
                        'coupon_name': coupon.coupon_name,
                        'code': str(coupon.code),
                        'qr_code_image': coupon.qr_code_image.url if coupon.qr_code_image else None
                    }
                }, status=status.HTTP_200_OK)
            except Coupon.DoesNotExist:
                return Response({
                    'status': 'error',
                    'code': 404,
                    'message': '해당 가게의 쿠폰을 찾을 수 없습니다.'
                }, status=status.HTTP_404_NOT_FOUND)
        

        with transaction.atomic():
            store = Store.objects.select_for_update().get(pk=certification.store.pk) # store 행에 락을 걸어서 동시성 문제 방지
            required_count = store.required_count
            now = timezone.now()
            window_secs = store.success_window_seconds

            store_location = Point(store.lng, store.lat, srid=4326)

            nearby_certifications = Certification.objects.filter(
                store=store,
                status='pending',
                location__distance_lte=(store_location, D(m=50))  # 50m 이내
            )
        
            current_count = nearby_certifications.count()
        
            # 윈도우가 열려 있는 경우우
            if store.success_window_started_at:
                deadline = store.success_window_started_at + timedelta(seconds=window_secs)

                if now > deadline:
                    # 창 만료되었을 때 모인 pending 인증 일괄 완료
                    nearby_certifications.update(status='completed')
                    store.success_window_started_at = None
                    store.save(update_fields=['success_window_started_at'])

                    certification.refresh_from_db(fields=['status'])

                    try:
                        coupon = Coupon.objects.get(store=store)
                        return Response({
                            'status': 'completed', 'code': 200,
                            'message': '인증이 완료되었습니다!(윈도우 종료 시 일괄 확정)',
                            'required_count': required_count,
                            'coupon': {
                                'coupon_id': coupon.coupon_id,
                                'coupon_name': coupon.coupon_name,
                                'code': str(coupon.code),
                                'qr_code_image': coupon.qr_code_image.url if coupon.qr_code_image else None
                            }
                        }, status=status.HTTP_200_OK)
                    except Coupon.DoesNotExist:
                        return Response({'status': 'error', 'code': 404, 'message': '해당 가게의 쿠폰을 찾을 수 없습니다.'},
                                        status=status.HTTP_404_NOT_FOUND)
                else:
                    remaining = (deadline - now).total_seconds()
                    return Response({
                        'status': 'pending', 'code': 200,
                        'message': '아직 윈도우가 닫히지 않았습니다. 곧 함께 완료됩니다다.',
                        'current_count': current_count,
                        'required_count': required_count,
                        'window': {
                            'open': True,
                            'ends_at': deadline.isoformat(),
                            'remaining_seconds': remaining
                        },
                        'certification_id': certification_id
                    }, status=status.HTTP_200_OK)

            # required_count에 도달한 경우, 창이 닫혀 있는 경우
            if current_count >= required_count:
                store.success_window_started_at = now
                store.save(update_fields=['success_window_started_at'])
                deadline = now + timedelta(seconds=window_secs)
                return Response({
                    'status': 'pending', 'code': 200,
                    'message': '유예 창이 열렸습니다. 창이 닫히면 함께 완료됩니다.',
                    'current_count': current_count,
                    'required_count': required_count,
                    'window': {
                        'open': True,
                        'ends_at': deadline.isoformat(),
                        'remaining_seconds': window_secs
                    },
                    'certification_id': certification_id
                }, status=status.HTTP_200_OK)

            
        # 아직 완료되지 않은 경우
        return Response({
            'status': 'pending',
            'code': 200,
            'message': '인증 진행 중...',
            'current_count': current_count,
            'required_count': required_count,
            'window': {'open': False},
            'certification_id': certification_id
        }, status=status.HTTP_200_OK)
        

class CertificationStatusView2(APIView): # 인증 완료 버튼 있는 버전
    def get(self, request, certification_id):
        try:
            certification = Certification.objects.get(certification_id=certification_id)
        except Certification.DoesNotExist:
            return Response({'status': 'error', 'code': 404, 'message': '인증 요청을 찾을 수 없습니다.'},
                            status=status.HTTP_404_NOT_FOUND)
        
        if certification.status == 'completed':
            try:
                coupon = Coupon.objects.get(store=certification.store)
                return Response({
                    'status': 'completed',
                    'code': 200,
                    'message': '인증이 완료되었습니다!',
                    'coupon': {
                        'coupon_id': coupon.coupon_id,
                        'coupon_name': coupon.coupon_name,
                        'code': str(coupon.code),
                        'qr_code_image': coupon.qr_code_image.url if coupon.qr_code_image else None
                    }
                }, status=status.HTTP_200_OK)
            except Coupon.DoesNotExist:
                return Response({'status': 'error', 'code': 404, 'message': '해당 가게의 쿠폰을 찾을 수 없습니다.'},
                                status=status.HTTP_404_NOT_FOUND)
        
        with transaction.atomic():
            store = Store.objects.select_for_update().get(pk=certification.store.pk)
            required_count = store.required_count

            store_location = Point(store.lng, store.lat, srid=4326)

            nearby_certifications = Certification.objects.filter(
                store=store,
                status='pending',
                location__distance_lte=(store_location, D(m=50))
            )

            current_count = nearby_certifications.count()

            if current_count >= required_count: # 문턱 달성, 하지만 아직 pending 상태 -> 일괄 완료로 업데이트
                nearby_certifications.update(status='completed')
                certification.refresh_from_db(fields=['status'])
                try:
                    coupon = Coupon.objects.get(store=store)
                except Coupon.DoesNotExist:
                    return Response({'status': 'error', 'code': 404, 'message': '해당 가게의 쿠폰을 찾을 수 없습니다.'},
                                    status=status.HTTP_404_NOT_FOUND)
                
                return Response({
                    'status': 'completed',
                    'code': 200,
                    'message': '인증이 완료되었습니다!',
                    'coupon': {
                        'coupon_id': coupon.coupon_id,
                        'coupon_name': coupon.coupon_name,
                        'code': str(coupon.code),
                        'qr_code_image': coupon.qr_code_image.url if coupon.qr_code_image else None
                    }
                }, status=status.HTTP_200_OK)
    
        certification.refresh_from_db(fields=['status'])
        if certification.status == 'completed':
            try:
                coupon = Coupon.objects.get(store=certification.store)
                return Response({
                    'status': 'completed',
                    'code': 200,
                    'message': '인증이 완료되었습니다!',
                    'coupon': {
                        'coupon_id': coupon.coupon_id,
                        'coupon_name': coupon.coupon_name,
                        'code': str(coupon.code),
                        'qr_code_image': coupon.qr_code_image.url if coupon.qr_code_image else None
                    }
                }, status=status.HTTP_200_OK)
            except Coupon.DoesNotExist:
                return Response({'status': 'error', 'code': 404, 'message': '해당 가게의 쿠폰을 찾을 수 없습니다.'},
                                status=status.HTTP_404_NOT_FOUND)
        elif certification.status == 'pending':
            return Response({"status" : "pending", "code" : 200, "message" : "인증 진행 중..", "certification_id" : certification_id})
        else:
            return Response({"status" : "error", "code" : 404, "message" : "인증 상태를 찾을 수 없습니다."},
                            status=status.HTTP_404_NOT_FOUND)
            
