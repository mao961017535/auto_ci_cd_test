
from django.contrib.auth.hashers import make_password
from django.shortcuts import render

# Create your views here.
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from django.utils.module_loading import import_string
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from .authentication import AUTH_HEADER_TYPES
from .serializers import UserSerializer
from .models import User
from .exceptions import InvalidToken, TokenError
from .permissions import AllowPostPermission
from demo.serializers import TokenObtainPairSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    用户管理视图集
    """
    permission_classes = [AllowPostPermission | IsAuthenticated]
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @extend_schema(
        request=UserSerializer,
        responses={201: UserSerializer},
    )
    def create(self, request):
        # request.data['password'] = make_password(request.data['password'], hasher='pbkdf2_sha256')
        return super().create(request)

    @action(detail=False, methods=['get'])
    def callback(self, request):
        print(request)
        return Response("你好")


class TokenViewBase(generics.GenericAPIView):
    permission_classes = [AllowAny]
    authentication_classes = ()

    serializer_class = None
    _serializer_class = ""

    www_authenticate_realm = "api"

    def get_serializer_class(self):
        """
        If serializer_class is set, use it directly. Otherwise get the class from settings.
        如果设置了serializer_class，则直接使用它。否则从设置中获取类。
        """

        if self.serializer_class:
            return self.serializer_class
        try:
            return import_string(self._serializer_class)
        except ImportError:
            msg = "Could not import serializer '%s'" % self._serializer_class
            raise ImportError(msg)

    def get_authenticate_header(self, request):
        return '{} realm="{}"'.format(
            AUTH_HEADER_TYPES[0],
            self.www_authenticate_realm,
        )

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class TokenObtainPairView(generics.GenericAPIView):
    """
    获取一组用户凭证，并返回一个访问和刷新JSON web令牌对，以证明这些凭证的身份验证。
    """
    serializer_class = TokenObtainPairSerializer
    permission_classes = [AllowAny]
    authentication_classes = ()
    www_authenticate_realm = "api"

    def get_authenticate_header(self, request):
        return '{} realm="{}"'.format(
            AUTH_HEADER_TYPES[0],
            self.www_authenticate_realm,
        )

    @extend_schema(
        request=TokenObtainPairSerializer,
        responses={201: TokenObtainPairSerializer},
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        return Response(serializer.validated_data, status=status.HTTP_200_OK)


token_obtain_pair = TokenObtainPairView.as_view()
