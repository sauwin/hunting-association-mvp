from functools import wraps
from django.contrib.auth.mixins import AccessMixin
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from .models import User


def user_has_any_role(user, allowed_roles: tuple[str, ...]) -> bool:
    """Return True if the authenticated user holds one of the allowed roles or is a superuser."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser or user.role == User.Role.ADMIN:
        return True
    return user.role in allowed_roles


def role_required(*allowed_roles: str):
    """
    Decorator for function-based views enforcing server-side role checks.
    - Unauthenticated users are redirected to LOGIN_URL.
    - Authenticated users without the required role receive HTTP 403 Forbidden.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if not user_has_any_role(request.user, allowed_roles):
                raise PermissionDenied("You do not have permission to perform this action.")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


class RoleRequiredMixin(AccessMixin):
    """
    Mixin for class-based views enforcing server-side role checks.
    Subclasses specify `allowed_roles = (...)`.
    """
    allowed_roles: tuple[str, ...] = ()

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not user_has_any_role(request.user, self.allowed_roles):
            raise PermissionDenied("You do not have permission to access this resource.")
        return super().dispatch(request, *args, **kwargs)


class MemberRequiredMixin(RoleRequiredMixin):
    """Allows authenticated members (as well as secretariat and admin)."""
    allowed_roles = (User.Role.MEMBER, User.Role.SECRETARIAT, User.Role.ADMIN)


class SecretariatRequiredMixin(RoleRequiredMixin):
    """Allows only secretariat staff and administrators (Student A back-office scope)."""
    allowed_roles = (User.Role.SECRETARIAT, User.Role.ADMIN)


class EditorRequiredMixin(RoleRequiredMixin):
    """Allows only editors and administrators (Student B content management scope)."""
    allowed_roles = (User.Role.EDITOR, User.Role.ADMIN)