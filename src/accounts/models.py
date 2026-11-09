from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        MEMBER = "member", "Member"
        SECRETARIAT = "secretariat", "Secretariat"
        EDITOR = "editor", "Editor"
        ADMIN = "admin", "Administrator"

    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER,
        help_text="Designates the user's role and permissions in the system.",
    )

    @property
    def is_member_role(self) -> bool:
        return self.role == self.Role.MEMBER

    @property
    def is_secretariat_role(self) -> bool:
        return self.role == self.Role.SECRETARIAT

    @property
    def is_editor_role(self) -> bool:
        return self.role == self.Role.EDITOR

    @property
    def is_admin_role(self) -> bool:
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def can_manage_members(self) -> bool:
        """True for Secretariat and Admin users (Student A back-office scope)."""
        return self.is_authenticated and (
            self.role in {self.Role.SECRETARIAT, self.Role.ADMIN} or self.is_superuser
        )

    @property
    def can_edit_public_content(self) -> bool:
        """True for Editor and Admin users (Student B content scope)."""
        return self.is_authenticated and (
            self.role in {self.Role.EDITOR, self.Role.ADMIN} or self.is_superuser
        )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"