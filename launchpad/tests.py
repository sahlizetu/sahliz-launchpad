from unittest.mock import patch

from eth_account import Account
from eth_account.messages import encode_defunct
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import Campaign, Company


class LaunchpadTests(TestCase):
    def setUp(self):
        call_command("seed_demo", "0x" + "a" * 40, "0x" + "b" * 40)

    def test_catalogue_displays_two_distinct_companies(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Data Academy")
        self.assertContains(response, "GreenBox")
        for campaign in Campaign.objects.all():
            detail = self.client.get(reverse("detail", args=[campaign.reference]))
            self.assertContains(detail, campaign.company.wallet)
            self.assertNotContains(detail, 'id="launch"')

    def test_submission_requires_review_and_correct_owner_for_launch(self):
        company = Company.objects.get(name="Data Academy")
        self.client.force_login(company.account)
        response = self.client.post(reverse("studio"), {
            "title":"Atelier Python", "description":"Atelier", "token_name":"Python Pass",
            "symbol":"PYP", "price":"0.00001", "goal":"0.001", "cap":500, "duration_minutes":5,
        })
        self.assertRedirects(response, reverse("studio"))
        campaign = Campaign.objects.get(title="Atelier Python")
        url = reverse("detail", args=[campaign.reference])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertTrue(campaign.requires_fee)
        campaign.approved = True
        campaign.commission = 20
        campaign.save(update_fields=["approved", "commission"])
        self.assertContains(self.client.get(url), 'id="launch"')
        publish = reverse("publish-campaign", args=[campaign.reference])
        self.assertNotContains(self.client.get(reverse("home")), campaign.title)
        with patch("launchpad.views.campaign_is_deployed", return_value=False):
            self.client.post(publish)
            campaign.refresh_from_db()
            self.assertFalse(campaign.published)
        with patch("launchpad.views.campaign_is_deployed", return_value=True):
            self.client.post(publish)
        self.assertContains(self.client.get(reverse("home")), campaign.title)
        self.client.force_login(Company.objects.get(name="GreenBox").account)
        self.assertNotContains(self.client.get(url), 'id="launch"')
        self.assertEqual(self.client.post(publish).status_code, 404)

    def test_language_preference_defaults_to_english_and_supports_rtl(self):
        home = reverse("home")
        response = self.client.get(home, HTTP_ACCEPT_LANGUAGE="fr")
        self.assertContains(response, 'lang="en" dir="ltr"')
        self.assertContains(response, "Explore startup campaigns.")

        for language, direction, heading in (
            ("fr", "ltr", "Découvrez les levées de startups."),
            ("ar", "rtl", "اكتشف حملات تمويل الشركات الناشئة."),
        ):
            with self.subTest(language=language):
                response = self.client.post(
                    reverse("set_language"), {"language": language, "next": home}
                )
                self.assertRedirects(response, home)
                response = self.client.get(home)
                self.assertContains(response, f'lang="{language}" dir="{direction}"')
                self.assertContains(response, heading)
                self.assertContains(self.client.get(reverse("javascript-catalog")), "Campaign open")


    def test_signup_requires_wallet_ownership_before_campaign_submission(self):
        wallet_page = reverse("connect-wallet")
        self.assertRedirects(self.client.post(reverse("signup"), {
            "company_name": "New Startup", "email": "founder@example.com",
            "username": "new-startup", "password1": "demo-password9!",
            "password2": "demo-password9!",
        }), wallet_page)
        company = Company.objects.get(name="New Startup")
        self.assertEqual(company.account.email, "founder@example.com")
        self.assertFalse(company.account.is_staff)
        self.assertRedirects(self.client.get(reverse("studio")), wallet_page)
        message = self.client.get(wallet_page).context["wallet_message"]
        wallet = Account.create()
        encoded = encode_defunct(text=message)
        wrong_signature = Account.create().sign_message(encoded).signature.hex()
        self.client.post(wallet_page, {"wallet": wallet.address, "signature": wrong_signature})
        company.refresh_from_db()
        self.assertFalse(company.wallet)
        signature = wallet.sign_message(encoded).signature.hex()
        self.assertRedirects(self.client.post(wallet_page, {
            "wallet": wallet.address, "signature": signature,
        }), reverse("studio"))
        company.refresh_from_db()
        self.assertEqual(company.wallet, wallet.address)
