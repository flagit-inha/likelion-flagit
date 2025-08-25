from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.files.base import ContentFile
from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings

from .models import ActivityLocation, Flag, User, Badge
from location.models import Location

User = get_user_model()

class UserSignupSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        error_messages={
            "required": "이메일은 필수 입력 항목입니다.",
            "invalid": "유효한 이메일 주소를 입력해주세요.",
        }
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        error_messages={
            "required": "비밀번호는 필수 입력 항목입니다."
        }
    )
    password_check = serializers.CharField(
        write_only=True,
        required=True,
        error_messages={
            "required": "비밀번호 확인은 필수 입력 항목입니다."
        }
    )
    nickname = serializers.CharField(
        required=True,
        error_messages={
            "required": "닉네임은 필수 입력 항목입니다."
        }
    )
    profile_image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ('nickname', 'email', 'password', 'password_check', 'profile_image')

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("이미 사용 중인 이메일입니다.")
        return value

    def validate_nickname(self, value):
        if User.objects.filter(nickname=value).exists():
            raise serializers.ValidationError("이미 사용 중인 닉네임입니다.")
        return value
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_check']:
            raise serializers.ValidationError({"password": "비밀번호가 일치하지 않습니다."})
        return attrs

    def create(self, validated_data):
        profile_image = validated_data.pop('profile_image', None)
        validated_data.pop('password_check')
        img_url = None
        if profile_image:
            s3_storage = S3Boto3Storage()
            path = s3_storage.save(f"profile_image/{profile_image.name}", ContentFile(profile_image.read()))
            img_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{path}"
        
        user = User.objects.create_user(
            email=validated_data['email'],
            nickname=validated_data['nickname'],
            password=validated_data['password']
        )
        if img_url:
            user.profile_image = img_url  # User 모델에 profile_image 필드가 url 저장 가능하도록 CharField 혹은 URLField여야 함
            user.save()
        return user
    
class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError("이메일 또는 비밀번호가 올바르지 않습니다.")
        else:
            raise serializers.ValidationError("이메일과 비밀번호를 모두 입력해주세요.")

        data['user'] = user
        return data
    
class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'nickname', 'email', 'flag_count', 'total_distance', 'profile_image', 'activities_count', 'discounts_count')

class UserSerializer(serializers.ModelSerializer): #ActivityLocation Serializer 내
    class Meta:
        model = User
        fields = ('id',)

class ActivityLocationSerializer(serializers.ModelSerializer):
    """
    ActivityLocation 모델을 위한 시리얼라이저
    """
    # 유저 정보를 중첩해서 보여주기 위해 UserSerializer를 사용합니다.
    user = UserSerializer(read_only=True)

    class Meta:
        model = ActivityLocation
        fields = ('id', 'user', 'location_name', 'description', 'visited_at', 'location_distance')

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ('id', 'name', 'location_distance')


class FlagSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    location = LocationSerializer(read_only=True)
    crew_members = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Flag
        fields = (
            'id', 'user', 'activity_type', 'location', 'date',
            'distance_km', 'time_record', 'crew_members', 'group_photo', 'description'
        )

class UserFlagSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    location = ActivityLocationSerializer(read_only=True)
    crew_members = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Flag
        fields = (
            'id', 'user', 'activity_type', 'location', 'date',
            'distance_km', 'time_record', 'crew_members', 'group_photo', 'description'
        )

class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = ('id', 'badge_name', 'description')