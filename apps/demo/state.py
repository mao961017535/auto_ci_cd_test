from .backends import TokenBackend
from django.conf import settings
token_backend = TokenBackend(
    "HS256",
    settings.SECRET_KEY,
    "",
    None,
    None,
    None,
    0,
    None,
)
