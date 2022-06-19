from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.hashers import make_password

from .models import User
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions, serializers
from .tokens import RefreshToken
from django.contrib.auth.models import update_last_login


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

    def validate_password(self, value):
        value = make_password(value, hasher='pbkdf2_sha256')
        return value


class PasswordField(serializers.CharField):
    def __init__(self, **kwargs):
        kwargs.setdefault("style", {})
        kwargs["style"]["input_type"] = "password"
        kwargs["write_only"] = True
        super().__init__(**kwargs)


class TokenObtainPairSerializer(serializers.Serializer):
    token_class = RefreshToken
    user = None
    password = PasswordField()
    username_field = get_user_model().USERNAME_FIELD
    refresh = serializers.CharField(read_only=True)
    access = serializers.CharField(read_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[self.username_field] = serializers.CharField(write_only=True)

    def validate(self, attrs):
        authenticate_kwargs = {
            self.username_field: attrs[self.username_field],
            "password": attrs["password"],
        }
        try:
            authenticate_kwargs["request"] = self.context["request"]
        except KeyError:
            pass

        self.user = authenticate(**authenticate_kwargs)
        if self.user is None or not self.user.is_active:
            raise exceptions.AuthenticationFailed(
                self.error_messages["no_active_account"],
                "no_active_account",
            )

        refresh = self.get_token(self.user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token)
        }

    @classmethod
    def get_token(cls, user):
        return cls.token_class.for_user(user)
