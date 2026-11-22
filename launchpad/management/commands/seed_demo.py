from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from launchpad.models import Campaign, Company, wallet_validator


class Command(BaseCommand):
    help = "Crée deux sociétés et campagnes de démonstration."

    def add_arguments(self, parser):
        parser.add_argument("academy_wallet")
        parser.add_argument("greenbox_wallet")
        parser.add_argument("--duration", type=int, default=5)

    @transaction.atomic
    def handle(self, *args, **options):
        rows = [
            ("data-academy", "Data Academy", options["academy_wallet"], "Formation Power BI",
             "Finance un atelier pratique. Les tokens représentent des crédits d’accès dans le scénario de démonstration.", "Academy Pass", "DAP"),
            ("greenbox", "GreenBox", options["greenbox_wallet"], "Kit GreenBox",
             "Finance le prototype d’un kit réutilisable. Les tokens représentent des crédits de précommande dans le scénario.", "GreenBox Credit", "GBC"),
        ]
        for username, name, wallet, title, description, token, symbol in rows:
            wallet_validator(wallet)
            user, _ = get_user_model().objects.get_or_create(username=username)
            company, _ = Company.objects.get_or_create(account=user, defaults={"name": name, "wallet": wallet})
            if company.wallet.lower() != wallet.lower():
                raise CommandError(f"Le portefeuille de {name} est déjà différent. Vérifiez-le dans Administration.")
            campaign, created = Campaign.objects.get_or_create(company=company, title=title, defaults={
                "description": description, "token_name": token, "symbol": symbol,
                "price": "0.00001", "goal": "0.001", "cap": 500,
                "duration_minutes": options["duration"], "approved": True,
            })
            if created:
                campaign.full_clean()
            self.stdout.write(f"{username} • /campagnes/{campaign.reference}/")
