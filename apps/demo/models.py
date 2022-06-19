from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractBaseUser, UserManager, AbstractUser
from django.db import models
from base.models import ReviewBaseModels
USER_ID_CLAIM = 'user_id'


class User(AbstractUser, ReviewBaseModels):
    objects = UserManager()
    USERNAME_FIELD = 'username'
    email = models.EmailField(blank=True)
    username = models.CharField(max_length=100, help_text='用户名', unique=True)
    nickname = models.CharField(max_length=100, help_text='用户昵称')
    password = models.CharField(max_length=100, help_text='加密后的密码')
    type = models.CharField(max_length=20, default='default', help_text='类型')
    is_supper = models.BooleanField(default=False, help_text='是否管理员')
    is_active = models.BooleanField(default=True, help_text='是否启用')
    last_login = models.CharField(max_length=50, help_text='最后登陆时间', blank=True)
    last_ip = models.CharField(max_length=50, help_text='最后登陆IP地址', blank=True)
    wx_token = models.CharField(max_length=50, null=True, help_text='用于发送微信消息的token')
    # roles = models.ManyToManyField('Role', db_table='user_role_rel')

    @staticmethod
    def make_password(plain_password: str) -> str:
        return make_password(plain_password, hasher='pbkdf2_sha256')
