from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        MEMBER = "member", "Member"
        SECRETARIAT = "secretariat", "Secretariat"
        EDITOR = "editor", "Editor"
        ADMIN = "admin", "Admin"

    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER,
    )

    def __str__(self):
        return f"{self.username} ({self.role})"
