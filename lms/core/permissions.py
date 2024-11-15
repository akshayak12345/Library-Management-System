from rest_framework.permissions import BasePermission

class isLibrarianUser(BasePermission):
    def has_permission(self, request, view):
        print("REQ",request.data,request.user,request.user.is_authenticated)
        if not request.user or  not request.user.is_authenticated:
            return False
        return request.user.user_type=="librarian"
    
class isRegularUser(BasePermission):
    def has_permission(self, request, view):
        if not request.user or  not request.user.is_authenticated:
            return False
        return request.user.user_type=="regular"