from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import HTTP_HEADER_ENCODING, authentication

from .exceptions import AuthenticationFailed, InvalidToken, TokenError
from .tokens import AccessToken


# 认证方式 如Bearer
AUTH_HEADER_TYPES = ('Bearer',)
AUTH_HEADER_TYPE_BYTES = {h.encode(HTTP_HEADER_ENCODING) for h in AUTH_HEADER_TYPES}
AUTH_TOKEN_CLASSES = (AccessToken,)
USER_ID_CLAIM = "user_id"
USER_ID_FIELD = "id"


class JWTAuthentication(authentication.BaseAuthentication):
    """
    一个认证插件，通过请求头中提供的JSON web令牌对请求进行认证。
    """

    www_authenticate_realm = "api"
    media_type = "application/json"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_model = get_user_model()

    def authenticate(self, request):
        header = self.get_header(request)
        if header is None:
            return None
        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None
        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token

    def authenticate_header(self, request):
        """
        返回一个字符串作为' 401 Unauthenticated '响应中的' WWW-Authenticate '头的值，
        或者如果认证方案应该返回' 403 Permission Denied '响应，则返回' None '。
        """
        return '{} realm="{}"'.format(
            AUTH_HEADER_TYPES[0],
            self.www_authenticate_realm,
        )

    def get_header(self, request):
        """
        从给定的请求中提取包含JSON web令牌的头。
        """
        header = request.META.get('HTTP_AUTHORIZATION')
        if isinstance(header, str):
            # Work around django test client oddness
            header = header.encode(HTTP_HEADER_ENCODING)
        return header

    def get_raw_token(self, header):
        """
        从给定的“授权”报头值中提取一个未验证的JSON web令牌。
        """
        parts = header.split()

        if len(parts) == 0:
            # Empty AUTHORIZATION header sent
            return None

        if parts[0] not in AUTH_HEADER_TYPE_BYTES:
            # Assume the header does not contain a JSON web token
            return None

        if len(parts) != 2:
            raise AuthenticationFailed(
                _("Authorization header must contain two space-delimited values"),
                code="bad_authorization_header",
            )

        return parts[1]

    def get_validated_token(self, raw_token):
        """
        验证一个编码的JSON web令牌，并返回一个验证的令牌包装器对象。
        """
        messages = []
        for AuthToken in AUTH_TOKEN_CLASSES:
            try:
                return AuthToken(raw_token)
            except TokenError as e:
                messages.append(
                    {
                        "token_class": AuthToken.__name__,
                        "token_type": AuthToken.token_type,
                        "message": e.args[0],
                    }
                )

        raise InvalidToken(
            {
                "detail": _("Given token not valid for any token type"),
                "messages": messages,
            }
        )

    def get_user(self, validated_token):
        """
        Attempts to find and return a user using the given validated token.
        尝试使用给定的验证过的令牌查找并返回用户。
        """
        try:
            user_id = validated_token[USER_ID_CLAIM]
        except KeyError:
            raise InvalidToken(_("Token contained no recognizable user identification"))

        try:
            user = self.user_model.objects.get(**{USER_ID_FIELD: user_id})
        except self.user_model.DoesNotExist:
            raise AuthenticationFailed(_("User not found"), code="user_not_found")

        if not user.is_active:
            raise AuthenticationFailed(_("User is inactive"), code="user_inactive")

        return user
