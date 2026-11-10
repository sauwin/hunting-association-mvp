from django.test import TestCase
from django.urls import reverse
from .models import FAQ


class PublicSiteViewsTest(TestCase):
    def setUp(self):
        self.published_faq = FAQ.objects.create(
            question="Ako dlho trvá schválenie členstva?",
            answer="Schválenie žiadosti trvá spravidla 5 až 10 pracovných dní.",
            is_published=True,
            display_order=1,
        )
        self.unpublished_faq = FAQ.objects.create(
            question="Interná poznámka (koncept)",
            answer="Táto odpoveď by nemala byť verejne viditeľná.",
            is_published=False,
            display_order=2,
        )

    def test_public_pages_status_code_200(self):
        """Verify all public pages load properly without login."""
        routes = ["public_site:home", "public_site:about", "public_site:how_to_join", "public_site:faq"]
        for route in routes:
            response = self.client.get(reverse(route))
            self.assertEqual(response.status_code, 200, f"Route {route} failed to return 200 OK")

    def test_faq_page_shows_only_published_items(self):
        """Ensure published FAQs are visible and drafts remain hidden."""
        response = self.client.get(reverse("public_site:faq"))
        self.assertContains(response, self.published_faq.question)
        self.assertNotContains(response, self.unpublished_faq.question)

    def test_registration_handoff_link_present(self):
        """Verify direct registration CTA link is rendered on Home and How to Join pages."""
        home_response = self.client.get(reverse("public_site:home"))
        join_response = self.client.get(reverse("public_site:how_to_join"))
        
        expected_url = home_response.context["membership_register_url"]
        self.assertContains(home_response, f'href="{expected_url}"')
        self.assertContains(join_response, f'href="{expected_url}"')