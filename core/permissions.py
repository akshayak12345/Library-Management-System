from rest_framework.permissions import BasePermission

class IsLibrarian(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'librarian'

class IsRegularUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'regular'
