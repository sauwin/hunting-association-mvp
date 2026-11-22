from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import (
    FAQ,
    Article,
    Category,
    MembershipEnquiry,
    Representative,
    VolunteerEnquiry,
)

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
            "public_site:representatives",
            "public_site:volunteer",
            "public_site:membership_interest",
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


class RepresentativesAndVolunteerModuleTest(TestCase):
    def setUp(self):
        self.active_rep_nitra = Representative.objects.create(
            region="Nitriansky kraj",
            display_name="Ing. Marek Kováč",
            role="Krajský koordinátor",
            public_contact="marek.kovac.demo@example.sk",
            bio="Koordinácia dobrovoľníkov v Nitrianskom kraji.",
            areas_of_interest="Ochrana zveri, osveta",
            is_active=True,
            display_order=1,
        )
        self.active_rep_zilina = Representative.objects.create(
            region="Žilinský kraj",
            display_name="Mgr. Katarína Horváthová",
            role="Regionálna zástupkyňa",
            public_contact="katarina.horvathova.demo@example.sk",
            bio="Práca s mládežou v Žilinskom kraji.",
            areas_of_interest="Práca s mládežou",
            is_active=True,
            display_order=2,
        )
        self.inactive_rep = Representative.objects.create(
            region="Trnavský kraj",
            display_name="Peter Neaktívny",
            role="Bývalý kontakt",
            public_contact="peter.neaktivny.demo@example.sk",
            bio="Tento záznam je neaktívny.",
            areas_of_interest="Administratíva",
            is_active=False,
            display_order=3,
        )

    def test_directory_shows_only_active_representatives(self):
        """Public directory displays active representatives and hides inactive ones."""
        response = self.client.get(reverse("public_site:representatives"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.active_rep_nitra.display_name)
        self.assertContains(response, self.active_rep_zilina.display_name)
        self.assertNotContains(response, self.inactive_rep.display_name)
        self.assertNotContains(response, self.inactive_rep.public_contact)

    def test_directory_region_filter_works(self):
        """Filtering by region returns only matching active representatives."""
        url = reverse("public_site:representatives")
        response = self.client.get(url, {"region": "Nitriansky kraj"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.active_rep_nitra.display_name)
        self.assertNotContains(response, self.active_rep_zilina.display_name)

    def test_volunteer_form_valid_submission_creates_private_enquiry(self):
        """Valid volunteer submission saves with NEW status and is not exposed publicly."""
        url = reverse("public_site:volunteer")
        payload = {
            "full_name": "Lucia Kráľová",
            "region": "Nitriansky kraj",
            "email": "lucia.test@example.sk",
            "phone": "+421 900 123 456",
            "interests": "Ochrana prírody",
            "message": "Rada by som sa zapojila ako dobrovoľníčka.",
            "consent_given": "on",
            "website": "",
        }
        response = self.client.post(url, data=payload, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(VolunteerEnquiry.objects.count(), 1)

        enquiry = VolunteerEnquiry.objects.first()
        self.assertEqual(enquiry.full_name, "Lucia Kráľová")
        self.assertEqual(enquiry.status, VolunteerEnquiry.Status.NEW)
        self.assertTrue(enquiry.consent_given)

        dir_response = self.client.get(reverse("public_site:representatives"))
        self.assertNotContains(dir_response, "lucia.test@example.sk")

    def test_volunteer_form_requires_consent(self):
        """Submitting without consent checkbox must fail validation and save nothing."""
        url = reverse("public_site:volunteer")
        payload = {
            "full_name": "Bez Súhlasu",
            "region": "Bratislavský kraj",
            "email": "bez.suhlasu@example.sk",
            "interests": "Podujatia",
            "message": "Test bez súhlasu.",
            "website": "",
        }
        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(VolunteerEnquiry.objects.count(), 0)

    def test_volunteer_form_honeypot_blocks_spam(self):
        """Filling the hidden honeypot field rejects spam submissions."""
        url = reverse("public_site:volunteer")
        payload = {
            "full_name": "Spam Bot",
            "region": "Unknown",
            "email": "bot@spam.example.com",
            "interests": "SEO links",
            "message": "Buy cheap products",
            "consent_given": "on",
            "website": "https://spam.example.com",
        }
        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(VolunteerEnquiry.objects.count(), 0)


class MembershipInterestAndStudentAIntegrationTest(TestCase):
    def test_membership_interest_page_exposes_student_a_handoff_links(self):
        """Membership interest page provides direct links into Student A's registration and apply flow."""
        response = self.client.get(reverse("public_site:membership_interest"))
        self.assertEqual(response.status_code, 200)

        apply_url = response.context["membership_apply_url"]
        register_url = response.context["account_register_url"]
        calculator_url = response.context["membership_calculator_url"]

        self.assertContains(response, f'href="{apply_url}"')
        self.assertContains(response, f'href="{register_url}"')
        self.assertContains(response, f'href="{calculator_url}"')

    def test_student_a_registration_and_apply_endpoints_reachable(self):
        """Verify Student A's real registration and membership application endpoints respond properly."""
        register_response = self.client.get(reverse("accounts:register"))
        self.assertEqual(register_response.status_code, 200)

        # Anonymous user accessing membership:apply is redirected cleanly to login/registration
        apply_response = self.client.get(reverse("membership:apply"))
        self.assertIn(apply_response.status_code, (200, 302))

    def test_membership_enquiry_valid_submission_creates_private_record(self):
        """Valid membership enquiry saves with NEW status and stays private from public pages."""
        url = reverse("public_site:membership_interest")
        payload = {
            "full_name": "Martin Kováčik",
            "email": "martin.enquiry@example.sk",
            "phone": "+421 905 111 222",
            "region": "Trnavský kraj",
            "preferred_membership_type": MembershipEnquiry.MembershipType.CANDIDATE,
            "has_hunting_licence": False,
            "message": "Zaujímam sa o prípravný kurz na prvý poľovný lístok.",
            "consent_given": "on",
            "website": "",
        }
        response = self.client.post(url, data=payload, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(MembershipEnquiry.objects.count(), 1)

        enquiry = MembershipEnquiry.objects.first()
        self.assertEqual(enquiry.full_name, "Martin Kováčik")
        self.assertEqual(
            enquiry.preferred_membership_type,
            MembershipEnquiry.MembershipType.CANDIDATE,
        )
        self.assertEqual(enquiry.status, MembershipEnquiry.Status.NEW)
        self.assertTrue(enquiry.consent_given)

        # Ensure enquiry email is never exposed publicly
        public_page = self.client.get(reverse("public_site:membership_interest"))
        self.assertNotContains(public_page, "martin.enquiry@example.sk")

    def test_membership_enquiry_requires_consent(self):
        """Submitting membership enquiry without consent checkbox must fail validation."""
        url = reverse("public_site:membership_interest")
        payload = {
            "full_name": "Bez Súhlasu",
            "email": "no.consent@example.sk",
            "region": "Nitriansky kraj",
            "preferred_membership_type": MembershipEnquiry.MembershipType.REGULAR,
            "message": "Otázka bez súhlasu.",
            "website": "",
        }
        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(MembershipEnquiry.objects.count(), 0)

    def test_membership_enquiry_honeypot_blocks_spam(self):
        """Filling hidden honeypot field rejects spam submissions."""
        url = reverse("public_site:membership_interest")
        payload = {
            "full_name": "Spam Bot",
            "email": "bot@spam.example.com",
            "region": "Unknown",
            "preferred_membership_type": MembershipEnquiry.MembershipType.REGULAR,
            "message": "Spam text",
            "consent_given": "on",
            "website": "https://spam.example.com",
        }
        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(MembershipEnquiry.objects.count(), 0)

class SeoAccessibilityAndShareTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Legislatíva",
            slug="legislativa",
        )
        self.published_article = Article.objects.create(
            category=self.category,
            title="Novela zákona o poľovníctve 2026",
            slug="novela-zakona-o-polovnictve-2026",
            summary="Prehľad dôležitých zmien pre členov komory.",
            body="Podrobný rozbor legislatívnych zmien.",
            author_byline="JUDr. Peter Varga",
            cover_image="https://example.com/images/cover.jpg",
            status=Article.Status.PUBLISHED,
        )
        self.draft_article = Article.objects.create(
            category=self.category,
            title="Nezverejnený interný návrh",
            slug="nezverejneny-interny-navrh",
            summary="Koncept článku.",
            body="Interný text.",
            author_byline="Redakcia SPK",
            status=Article.Status.DRAFT,
        )

    def test_robots_txt_endpoint(self):
        """Verify /robots.txt returns 200 text/plain with sitemap reference."""
        response = self.client.get(reverse("public_site:robots_txt"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/plain", response["Content-Type"])
        self.assertContains(response, "User-agent: *")
        self.assertContains(response, "Disallow: /admin/")
        self.assertContains(response, "/sitemap.xml")

    def test_sitemap_xml_includes_public_pages_and_published_articles_only(self):
        """Verify /sitemap.xml lists public routes and published articles, excluding drafts."""
        response = self.client.get(reverse("public_site:sitemap_xml"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("application/xml", response["Content-Type"])
        self.assertContains(response, reverse("public_site:home"))
        self.assertContains(response, reverse("public_site:membership_interest"))
        self.assertContains(response, self.published_article.get_absolute_url())
        self.assertNotContains(response, self.draft_article.get_absolute_url())

    def test_article_detail_open_graph_and_share_controls(self):
        """Verify article detail renders Open Graph metadata and social share controls."""
        response = self.client.get(self.published_article.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'property="og:type" content="article"')
        self.assertContains(response, self.published_article.title)
        self.assertContains(response, 'property="og:image" content="https://example.com/images/cover.jpg"')
        self.assertContains(response, "facebook.com/sharer/sharer.php")
        self.assertContains(response, "linkedin.com/sharing/share-offsite/")
        self.assertContains(response, "copy-article-link-btn")

    def test_accessibility_skip_link_and_association_social_links(self):
        """Verify skip-to-content accessibility link and footer social media channels exist."""
        response = self.client.get(reverse("public_site:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="#main-content"')
        self.assertContains(response, 'id="main-content"')
        self.assertContains(response, 'aria-label="Facebook Slovenskej poľovníckej komory"')
        self.assertContains(response, 'aria-label="Instagram Slovenskej poľovníckej komory"')
        self.assertContains(response, 'aria-label="YouTube kanál Slovenskej poľovníckej komory"')