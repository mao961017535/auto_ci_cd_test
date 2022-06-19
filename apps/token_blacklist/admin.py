from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import OutstandingToken


class OutstandingTokenAdmin(admin.ModelAdmin):
    list_display = (
        "jti",
        "user",
        "created_at",
        "expires_at",
    )
    search_fields = (
        "user__id",
        "jti",
    )
    ordering = ("user",)

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)

        return qs.select_related("user")

    # Read-only behavior defined below
    actions = None

    def get_readonly_fields(self, *args, **kwargs):
        return [f.name for f in self.model._meta.fields]

    def has_add_permission(self, *args, **kwargs):
        return False

    def has_delete_permission(self, *args, **kwargs):
        return False

    def has_change_permission(self, request, obj=None):
        return request.method in ["GET", "HEAD"] and super().has_change_permission(
            request, obj
        )


# admin.site.register(OutstandingToken, OutstandingTokenAdmin)
