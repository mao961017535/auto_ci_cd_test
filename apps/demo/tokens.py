from datetime import timedelta
from uuid import uuid4

from django.conf import settings
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _

from .exceptions import TokenBackendError, TokenError
from .utils import aware_utcnow, datetime_from_epoch, datetime_to_epoch, format_lazy
from token_blacklist.models import OutstandingToken

TOKEN_TYPE_CLAIM = "token_type"
JTI_CLAIM = "jti"
USER_ID_FIELD = "id"
USER_ID_CLAIM = "user_id"
ACCESS_TOKEN_LIFETIME = timedelta(minutes=5)
REFRESH_TOKEN_LIFETIME = timedelta(days=1)
SLIDING_TOKEN_LIFETIME = timedelta(minutes=5)
SLIDING_TOKEN_REFRESH_LIFETIME = timedelta(days=1)
SLIDING_TOKEN_REFRESH_EXP_CLAIM = "refresh_exp"


class Token:
    """
    A class which validates and wraps an existing JWT or can be used to build a new JWT.
    一个类，用于验证和包装现有的JWT或用于构建新的JWT。
    """

    token_type = None
    lifetime = None

    def __init__(self, token=None, verify=True):
        """
        如果给定的令牌无效、过期或不安，必须引发带有面向用户错误的 TokenError 消息。
        """
        if self.token_type is None or self.lifetime is None:
            raise TokenError(_("Cannot create token with no type or lifetime"))

        self.token = token
        self.current_time = aware_utcnow()

        # 设置令牌
        if token is not None:
            # An encoded token was provided
            token_backend = self.get_token_backend()

            # Decode token
            try:
                self.payload = token_backend.decode(token, verify=verify)
            except TokenBackendError:
                raise TokenError(_("Token is invalid or expired"))

            if verify:
                self.verify()
        else:
            # 新令牌 跳过所有验证步骤。
            self.payload = {TOKEN_TYPE_CLAIM: self.token_type}

            # Set "exp" and "iat" claims with default value
            self.set_exp(from_time=self.current_time, lifetime=self.lifetime)
            self.set_iat(at_time=self.current_time)

            # Set "jti" claim
            self.set_jti()

    def __repr__(self):
        return repr(self.payload)

    def __getitem__(self, key):
        return self.payload[key]

    def __setitem__(self, key, value):
        self.payload[key] = value

    def __delitem__(self, key):
        del self.payload[key]

    def __contains__(self, key):
        return key in self.payload

    def get(self, key, default=None):
        return self.payload.get(key, default)

    def __str__(self):
        """
        标记并返回一个标记为base64编码的字符串。
        """
        return self.get_token_backend().encode(self.payload)

    def verify(self):
        """
            解码此令牌时未执行的附加验证步骤。此方法是公共 API 的一部分，以表明它可能在子类中被重写的意图。
        """
        # (https://tools.ietf.org/html/rfc7519#section-4.1.4).
        # 根据RFC 7519， exp 声明是可选的作为授权令牌更正确的行为，我们需要一个 exp 声明。我们不希望有僵尸 Token 到处乱走。
        self.check_exp()

        # 如果默认值不是None，那么我们应该强制这些设置的要求。如上所述，规范将这些标记为可选的。
        if "jti" not in self.payload:
            raise TokenError(_("Token has no id"))

        if TOKEN_TYPE_CLAIM is not None:

            self.verify_token_type()

    def verify_token_type(self):
        """
        Ensures that the token type claim is present and has the correct value.
        """
        try:
            token_type = self.payload[TOKEN_TYPE_CLAIM]
        except KeyError:
            raise TokenError(_("Token has no type"))

        if self.token_type != token_type:
            raise TokenError(_("Token has wrong type"))

    def set_jti(self):
        """
        Populates the configured jti claim of a token with a string where there
        is a negligible probability that the same string will be chosen at a
        later time.

        See here:
        https://tools.ietf.org/html/rfc7519#section-4.1.7
        """
        self.payload[JTI_CLAIM] = uuid4().hex

    def set_exp(self, claim="exp", from_time=None, lifetime=None):
        """
        Updates the expiration time of a token.

        See here:
        https://tools.ietf.org/html/rfc7519#section-4.1.4
        """
        if from_time is None:
            from_time = self.current_time

        if lifetime is None:
            lifetime = self.lifetime

        self.payload[claim] = datetime_to_epoch(from_time + lifetime)

    def set_iat(self, claim="iat", at_time=None):
        """
        Updates the time at which the token was issued.

        See here:
        https://tools.ietf.org/html/rfc7519#section-4.1.6
        """
        if at_time is None:
            at_time = self.current_time

        self.payload[claim] = datetime_to_epoch(at_time)

    def check_exp(self, claim="exp", current_time=None):
        """
        Checks whether a timestamp value in the given claim has passed (since
        the given datetime value in `current_time`).  Raises a TokenError with
        a user-facing error message if so.
        """
        if current_time is None:
            current_time = self.current_time

        try:
            claim_value = self.payload[claim]
        except KeyError:
            raise TokenError(format_lazy(_("Token has no '{}' claim"), claim))

        claim_time = datetime_from_epoch(claim_value)
        leeway = self.get_token_backend().get_leeway()
        if claim_time <= current_time - leeway:
            raise TokenError(format_lazy(_("Token '{}' claim has expired"), claim))

    @classmethod
    def for_user(cls, user):
        """
        Returns an authorization token for the given user that will be provided
        after authenticating the user's credentials.
        """
        user_id = getattr(user, USER_ID_FIELD)
        if not isinstance(user_id, int):
            user_id = str(user_id)

        token = cls()
        token[USER_ID_CLAIM] = user_id

        return token

    _token_backend = None

    @property
    def token_backend(self):
        if self._token_backend is None:
            self._token_backend = import_string(
                "demo.state.token_backend"
            )
        return self._token_backend

    def get_token_backend(self):
        # Backward compatibility.
        return self.token_backend


class SlidingToken(Token):
    token_type = "sliding"
    lifetime = SLIDING_TOKEN_LIFETIME

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.token is None:
            # Set sliding refresh expiration claim if new token
            self.set_exp(
                SLIDING_TOKEN_REFRESH_EXP_CLAIM,
                from_time=self.current_time,
                lifetime=SLIDING_TOKEN_REFRESH_LIFETIME,
            )


class AccessToken(Token):
    token_type = "access"
    lifetime = ACCESS_TOKEN_LIFETIME


class RefreshToken(Token):
    token_type = "refresh"
    lifetime = REFRESH_TOKEN_LIFETIME
    no_copy_claims = (
        TOKEN_TYPE_CLAIM,
        "exp",
        # Both of these claims are included even though they may be the same.
        # It seems possible that a third party token might have a custom or
        # namespaced JTI claim as well as a default "jti" claim.  In that case,
        # we wouldn't want to copy either one.
        JTI_CLAIM,
        "jti",
    )
    access_token_class = AccessToken

    @property
    def access_token(self):
        """
        Returns an access token created from this refresh token.  Copies all claims present in this refresh token to the new access token except those claims listed in the `no_copy_claims` attribute.
        返回从此刷新令牌创建的访问令牌。将出现在此刷新令牌中的所有声明复制到新的访问令牌，但 no_copy_claims 属性中列出的声明除外
        """
        access = self.access_token_class()

        # Use instantiation time of refresh token as relative timestamp for
        # access token "exp" claim.  This ensures that both a refresh and
        # access token expire relative to the same time if they are created as
        # a pair.
        access.set_exp(from_time=self.current_time)

        no_copy = self.no_copy_claims
        for claim, value in self.payload.items():
            if claim in no_copy:
                continue
            access[claim] = value

        return access


class UntypedToken(Token):
    token_type = "untyped"
    lifetime = timedelta(seconds=0)

    def verify_token_type(self):
        """
        Untyped tokens do not verify the "token_type" claim.  This is useful when performing general validation of a token's signature and other properties which do not relate to the token's intended use.
        非类型化标记不验证“token_type”声明。当对令牌的签名和其他与令牌的预期用途无关的属性执行通用验证时，这是有用的
        """
        pass
