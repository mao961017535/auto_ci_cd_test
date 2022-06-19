from rest_framework.permissions import BasePermission, IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response
from rest_framework.views import APIView


class AllowPostPermission(BasePermission):
    def has_permission(self, request, view):
        print("查看一下method")
        print(request.method)
        return request.method == "POST"

