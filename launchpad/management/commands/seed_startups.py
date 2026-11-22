from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from launchpad.models import Campaign, Company, wallet_validator


STARTUPS = (
    ("atlas-ai", "AtlasAI", "Intelligence artificielle", "Tanger, Maroc",
     "Financer le pilote de prévision des ventes",
     "AtlasAI aide les PME à anticiper la demande et à réduire les ruptures de stock à partir de leurs données de vente.",
     "50 % pour le développement du moteur de prévision, 30 % pour les connecteurs ERP et 20 % pour l’accompagnement des entreprises pilotes.", "AtlasAI Demo", "ATLS", "0.001"),
    ("greenbox-ventures", "GreenBox", "Économie circulaire", "Casablanca, Maroc",
     "Financer une ligne pilote d’emballages réutilisables",
     "GreenBox conçoit des caisses réutilisables pour les commerces et organise leur collecte entre les points de vente.",
     "60 % pour les moules et la première série, 25 % pour la logistique de retour et 15 % pour les essais terrain.", "GreenBox Demo", "GBX", "0.001"),
    ("aquanorth", "AquaNorth", "AgriTech", "Agadir, Maroc",
     "Déployer des capteurs d’irrigation sur trois fermes pilotes",
     "AquaNorth mesure l’humidité des sols et aide les exploitants à programmer l’irrigation en fonction des besoins de chaque parcelle.",
     "50 % pour les capteurs, 30 % pour les installations sur site et 20 % pour le tableau de bord agronomique.", "AquaNorth Demo", "AQUA", "0.002"),
    ("medroute", "MedRoute", "Logistique de santé", "Rabat, Maroc",
     "Tester le suivi de la chaîne du froid",
     "MedRoute développe un outil de suivi de température et d’alertes pour les livraisons de produits thermosensibles.",
     "45 % pour l’intégration logicielle, 35 % pour les équipements et 20 % pour le suivi des trajets pilotes.", "MedRoute Demo", "MDRT", "0.0015"),
)


class Command(BaseCommand):
    help = "Ajoute quatre startups fictives et masque les deux campagnes du catalogue initial."

    def add_arguments(self, parser):
        parser.add_argument("wallets", nargs="*", help="Deux ou quatre adresses publiques MetaMask.")

    @transaction.atomic
    def handle(self, *args, **options):
        wallets = options["wallets"]
        if not wallets:
            wallets = list(Company.objects.filter(account__username__in=["data-academy", "greenbox"])
                           .order_by("account__username").values_list("wallet", flat=True))
        if len(wallets) not in (2, 4) or len(set(wallet.lower() for wallet in wallets)) != len(wallets):
            raise CommandError("Indiquez deux ou quatre adresses MetaMask distinctes.")
        try:
            for wallet in wallets:
                wallet_validator(wallet)
        except ValidationError as error:
            raise CommandError("Adresse publique MetaMask invalide.") from error

        for index, row in enumerate(STARTUPS):
            username, name, sector, location, title, description, funds, token, symbol, goal = row
            account, _ = get_user_model().objects.get_or_create(username=username)
            company, _ = Company.objects.get_or_create(account=account, defaults={
                "name": name, "wallet": wallets[index % len(wallets)],
            })
            campaign, _ = Campaign.objects.get_or_create(company=company, title=title, defaults={
                "sector": sector, "location": location, "description": description, "use_of_funds": funds,
                "token_name": token, "symbol": symbol, "price": "0.00001", "goal": goal,
                "cap": 500, "duration_minutes": 15, "approved": True,
            })
            self.stdout.write(f"{name} · {username} · /campagnes/{campaign.reference}/")

        Campaign.objects.filter(company__account__username="data-academy", title="Formation Power BI").update(approved=False)
        Campaign.objects.filter(company__account__username="greenbox", title="Kit GreenBox").update(approved=False)
        if len(wallets) == 2:
            self.stdout.write("Démo : deux portefeuilles sont utilisés pour les quatre startups.")
