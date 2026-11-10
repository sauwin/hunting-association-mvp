from django.db import models


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