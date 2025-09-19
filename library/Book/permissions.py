from rest_framework import permissions

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'admin'

class IsLibrarian(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'librarian'
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'storekeeper'

class IsAdminOrLibrarian(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.user_type == 'admin' or 
            request.user.user_type == 'librarian'
        )

class IsAdminOrStorekeeper(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.user_type == 'admin' or 
            request.user.user_type == 'storekeeper'
        )
    
class IsStorekeeper(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'storekeeper'
