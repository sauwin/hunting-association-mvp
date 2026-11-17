from django.db import models
from django.urls import reverse
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self) -> str:
        return self.name


class Article(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PUBLISHED = "PUBLISHED", "Published"

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="articles",
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    summary = models.TextField(max_length=500)
    body = models.TextField()
    author_byline = models.CharField(max_length=120)
    cover_image = models.URLField(
        max_length=500,
        blank=True,
        help_text="Optional URL to cover image.",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]
        verbose_name = "Article"
        verbose_name_plural = "Articles"

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if self.status == self.Status.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("public_site:article_detail", kwargs={"slug": self.slug})


class FAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    display_order = models.PositiveIntegerField(
        default=0,
        help_text="Lower numbers appear first on the FAQ page.",
    )
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "id"]
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self) -> str:
        return self.question


class Representative(models.Model):
    region = models.CharField(max_length=120, verbose_name="Kraj / Okres")
    display_name = models.CharField(max_length=150, verbose_name="Meno a priezvisko")
    role = models.CharField(max_length=150, verbose_name="Pozícia / Rola")
    public_contact = models.CharField(
        max_length=200,
        verbose_name="Verejný kontakt (e-mail / telefón)",
        help_text="Zobrazí sa verejne len so súhlasom zástupcu.",
    )
    bio = models.TextField(verbose_name="Krátke predstavenie")
    areas_of_interest = models.CharField(
        max_length=255,
        verbose_name="Oblasti pôsobenia",
        help_text="Napr. Ochrana zveri, kynológia, práca s mládežou",
    )
    is_active = models.BooleanField(default=True, verbose_name="Aktívny")
    display_order = models.PositiveIntegerField(
        default=0,
        verbose_name="Poradie zobrazenia",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "region", "display_name"]
        verbose_name = "Regional Representative"
        verbose_name_plural = "Regional Representatives"

    def __str__(self) -> str:
        return f"{self.display_name} ({self.region})"


class VolunteerEnquiry(models.Model):
    class Status(models.TextChoices):
        NEW = "NEW", "New"
        CONTACTED = "CONTACTED", "Contacted"
        ACCEPTED = "ACCEPTED", "Accepted"
        DECLINED = "DECLINED", "Declined"

    full_name = models.CharField(max_length=150, verbose_name="Meno a priezvisko")
    region = models.CharField(max_length=120, verbose_name="Kraj / Okres")
    email = models.EmailField(verbose_name="E-mailová adresa")
    phone = models.CharField(max_length=40, blank=True, verbose_name="Telefónne číslo")
    interests = models.CharField(max_length=255, verbose_name="Oblasti záujmu")
    message = models.TextField(verbose_name="Krátka správa")
    consent_given = models.BooleanField(
        default=False,
        verbose_name="Súhlas so spracovaním údajov",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
        verbose_name="Stav žiadosti",
    )
    staff_notes = models.TextField(blank=True, verbose_name="Interná poznámka")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Volunteer Enquiry"
        verbose_name_plural = "Volunteer Enquiries"

    def __str__(self) -> str:
        return f"{self.full_name} – {self.region} ({self.get_status_display()})"