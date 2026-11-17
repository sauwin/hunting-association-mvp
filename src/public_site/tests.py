from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import FAQ, Article, Category

User = get_user_model()


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
        routes = [
            "public_site:home",
            "public_site:about",
            "public_site:how_to_join",
            "public_site:faq",
            "public_site:article_list",
        ]
        for route in routes:
            response = self.client.get(reverse(route))
            self.assertEqual(
                response.status_code,
                200,
                f"Route {route} failed to return 200 OK",
            )

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


class ArticleModuleTest(TestCase):
    def setUp(self):
        self.cat_nature = Category.objects.create(
            name="Ochrana prírody",
            slug="ochrana-prirody",
            description="Starostlivosť o biotopy a zver.",
        )
        self.cat_events = Category.objects.create(
            name="Podujatia",
            slug="podujatia",
            description="Regionálne akcie a kynológia.",
        )

        self.published_article = Article.objects.create(
            category=self.cat_nature,
            title="Zimné prikrmovanie zveri",
            slug="zimne-prikrmovanie-zveri",
            summary="Zásady správneho prikrmovania počas zimy.",
            body="Podrobný text publikovaného článku.",
            author_byline="Ing. Marek Kováč",
            status=Article.Status.PUBLISHED,
        )

        self.draft_article = Article.objects.create(
            category=self.cat_events,
            title="Rozpracovaný koncept článku",
            slug="rozpracovany-koncept-clanku",
            summary="Tento koncept nesmie byť verejne prístupný.",
            body="Interný text rozpracovaného článku.",
            author_byline="Redakcia SPK",
            status=Article.Status.DRAFT,
        )

    def test_article_list_shows_only_published_articles(self):
        """Public article list displays published articles and hides drafts."""
        response = self.client.get(reverse("public_site:article_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.published_article.title)
        self.assertNotContains(response, self.draft_article.title)

    def test_category_filtering_works(self):
        """Category filter route shows only articles belonging to that category."""
        other_article = Article.objects.create(
            category=self.cat_events,
            title="Celoslovenské skúšky psov",
            slug="celoslovenske-skusky-psov",
            summary="Kynologické podujatie.",
            body="Obsah článku o kynológii.",
            author_byline="Mgr. Lukáš Kráľ",
            status=Article.Status.PUBLISHED,
        )
        url = reverse(
            "public_site:article_list_by_category",
            kwargs={"category_slug": self.cat_nature.slug},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.published_article.title)
        self.assertNotContains(response, other_article.title)

    def test_published_article_detail_accessible_to_visitor(self):
        """Anonymous visitors can open a published article detail page."""
        url = reverse(
            "public_site:article_detail",
            kwargs={"slug": self.published_article.slug},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.published_article.title)
        self.assertContains(response, self.published_article.body)

    def test_draft_article_returns_404_for_anonymous_visitor(self):
        """Unpublished draft articles must return 404 to anonymous visitors."""
        url = reverse(
            "public_site:article_detail",
            kwargs={"slug": self.draft_article.slug},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_draft_article_preview_accessible_to_staff_editor(self):
        """Authorised staff/editors can preview unpublished draft articles."""
        editor_user = User.objects.create_user(
            username="editor_test",
            email="editor@spk.sk",
            password="testpassword123",
            is_staff=True,
        )
        self.client.force_login(editor_user)
        url = reverse(
            "public_site:article_detail",
            kwargs={"slug": self.draft_article.slug},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.draft_article.title)
        self.assertContains(response, "NÁHĽAD ROZPRACOVANÉHO ČLÁNKU")