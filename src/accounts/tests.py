from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.views import View

from .permissions import (
    EditorRequiredMixin,
    MemberRequiredMixin,
    SecretariatRequiredMixin,
    role_required,
)

User = get_user_model()


@role_required(User.Role.SECRETARIAT, User.Role.ADMIN)
def dummy_secretariat_view(request):
    return HttpResponse("Secretariat OK")


class DummySecretariatCBV(SecretariatRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return HttpResponse("Secretariat CBV OK")


class DummyMemberCBV(MemberRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return HttpResponse("Member CBV OK")


class DummyEditorCBV(EditorRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return HttpResponse("Editor CBV OK")


class RoleAndPermissionTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.member_user = User.objects.create_user(
            username="member1",
            email="member1@example.test",
            password="StrongPassword123!",
            role=User.Role.MEMBER,
        )
        self.secretariat_user = User.objects.create_user(
            username="staff1",
            email="staff1@example.test",
            password="StrongPassword123!",
            role=User.Role.SECRETARIAT,
        )
        self.editor_user = User.objects.create_user(
            username="editor1",
            email="editor1@example.test",
            password="StrongPassword123!",
            role=User.Role.EDITOR,
        )
        self.admin_user = User.objects.create_user(
            username="admin1",
            email="admin1@example.test",
            password="StrongPassword123!",
            role=User.Role.ADMIN,
        )

    def test_user_role_helper_properties(self):
        self.assertTrue(self.member_user.is_member_role)
        self.assertFalse(self.member_user.can_manage_members)
        self.assertFalse(self.member_user.can_edit_public_content)

        self.assertTrue(self.secretariat_user.is_secretariat_role)
        self.assertTrue(self.secretariat_user.can_manage_members)
        self.assertFalse(self.secretariat_user.can_edit_public_content)

        self.assertTrue(self.editor_user.is_editor_role)
        self.assertFalse(self.editor_user.can_manage_members)
        self.assertTrue(self.editor_user.can_edit_public_content)

        self.assertTrue(self.admin_user.is_admin_role)
        self.assertTrue(self.admin_user.can_manage_members)
        self.assertTrue(self.admin_user.can_edit_public_content)

    def test_anonymous_user_redirected_to_login(self):
        request = self.factory.get("/secretariat-action/")
        request.user = AnonymousUser()
        response = dummy_secretariat_view(request)
        self.assertEqual(response.status_code, 302)

    def test_member_blocked_from_secretariat_decorator_and_mixin(self):
        request = self.factory.get("/secretariat-action/")
        request.user = self.member_user

        with self.assertRaises(PermissionDenied):
            dummy_secretariat_view(request)

        with self.assertRaises(PermissionDenied):
            DummySecretariatCBV.as_view()(request)

    def test_secretariat_and_admin_allowed_on_secretariat_views(self):
        for allowed_user in (self.secretariat_user, self.admin_user):
            request = self.factory.get("/secretariat-action/")
            request.user = allowed_user

            response_fbv = dummy_secretariat_view(request)
            self.assertEqual(response_fbv.status_code, 200)

            response_cbv = DummySecretariatCBV.as_view()(request)
            self.assertEqual(response_cbv.status_code, 200)

    def test_editor_permissions_isolated_from_secretariat_and_member(self):
        request = self.factory.get("/editor-action/")
        request.user = self.member_user
        with self.assertRaises(PermissionDenied):
            DummyEditorCBV.as_view()(request)

        request.user = self.editor_user
        response = DummyEditorCBV.as_view()(request)
        self.assertEqual(response.status_code, 200)

        request_member_area = self.factory.get("/member-portal/")
        request_member_area.user = self.member_user
        response_member = DummyMemberCBV.as_view()(request_member_area)
        self.assertEqual(response_member.status_code, 200)


class AuthenticationFlowTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            username="hunter_login",
            email="hunter_login@example.test",
            password="ValidPassword123!",
            first_name="Jan",
            last_name="Novak",
        )

    def test_registration_creates_member_role_and_logs_in(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "new_applicant",
                "email": "applicant@example.test",
                "first_name": "Peter",
                "last_name": "Kovac",
                "password1": "ComplexPass123!",
                "password2": "ComplexPass123!",
            },
        )
        self.assertRedirects(response, reverse("accounts:dashboard"))
        created_user = User.objects.get(username="new_applicant")
        self.assertEqual(created_user.role, User.Role.MEMBER)
        self.assertEqual(created_user.email, "applicant@example.test")

    def test_login_with_email_and_username(self):
        response_email = self.client.post(
            reverse("accounts:login"),
            {"identifier": "HUNTER_LOGIN@example.test", "password": "ValidPassword123!"},
        )
        self.assertRedirects(response_email, reverse("accounts:dashboard"))
        self.client.post(reverse("accounts:logout"))

        response_username = self.client.post(
            reverse("accounts:login"),
            {"identifier": "hunter_login", "password": "ValidPassword123!"},
        )
        self.assertRedirects(response_username, reverse("accounts:dashboard"))

    @override_settings(LOGIN_RATE_LIMIT_ATTEMPTS=3, LOGIN_RATE_LIMIT_TIMEOUT=300)
    def test_login_rate_limiting_blocks_brute_force(self):
        login_url = reverse("accounts:login")
        bad_payload = {"identifier": "hunter_login", "password": "WrongPassword!"}

        for _ in range(3):
            res = self.client.post(login_url, bad_payload)
            self.assertEqual(res.status_code, 200)

        blocked_res = self.client.post(login_url, bad_payload)
        self.assertEqual(blocked_res.status_code, 429)
        self.assertContains(blocked_res, "Too many failed login attempts", status_code=429)

    def test_dashboard_requires_authentication(self):
        response = self.client.get(reverse("accounts:dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_password_reset_request_succeeds(self):
        response = self.client.post(
            reverse("accounts:password_reset"),
            {"email": "hunter_login@example.test"},
        )
        self.assertRedirects(response, reverse("accounts:password_reset_done"))