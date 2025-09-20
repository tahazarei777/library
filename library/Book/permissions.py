from rest_framework import permissions

class HasUserType(permissions.BasePermission):
    allowed_types = []
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            hasattr(request.user, 'user_type') and 
            request.user.user_type in self.allowed_types
        )

class IsAdmin(HasUserType):
    allowed_types = ['admin']

class IsLibrarian(HasUserType):
    allowed_types = ['librarian']

class IsStorekeeper(HasUserType):
    allowed_types = ['storekeeper']

class IsAdminOrLibrarian(HasUserType):
    allowed_types = ['admin', 'librarian']

class IsAdminOrStorekeeper(HasUserType):
    allowed_types = ['admin', 'storekeeper']

class IsLibrarianOrStorekeeper(HasUserType):
    allowed_types = ['librarian', 'storekeeper']

class IsAdminOrLibrarianOrStorekeeper(HasUserType):
    allowed_types = ['admin', 'librarian', 'storekeeper']