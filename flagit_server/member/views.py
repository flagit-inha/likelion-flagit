from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import ValidationError

from .serializers import UserSignupSerializer
from .serializers import UserLoginSerializer

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