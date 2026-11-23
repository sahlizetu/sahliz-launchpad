from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models

wallet_validator = RegexValidator(r"^0x[0-9a-fA-F]{40}\Z", "Adresse Ethereum invalide.")


class Company(models.Model):
    account = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    name = models.CharField(max_length=100)
    wallet = models.CharField(max_length=42, blank=True, validators=[wallet_validator])

    def __str__(self):
        return self.name


class Campaign(models.Model):
    reference = models.UUIDField(default=uuid4, unique=True, editable=False)
    company = models.ForeignKey(Company, on_delete=models.PROTECT)
    title = models.CharField(max_length=100)
    description = models.TextField(max_length=2000)
    sector = models.CharField(max_length=60, blank=True)
    location = models.CharField(max_length=80, blank=True)
    use_of_funds = models.TextField(max_length=1000, blank=True)
    token_name = models.CharField(max_length=40)
    symbol = models.CharField(max_length=10, validators=[RegexValidator(r"^[A-Z0-9]{2,10}\Z")])
    price = models.DecimalField(max_digits=22, decimal_places=18, validators=[MinValueValidator(Decimal("0.000000000000000001"))])
    goal = models.DecimalField(max_digits=22, decimal_places=18, validators=[MinValueValidator(Decimal("0.000000000000000001"))])
    cap = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    duration_minutes = models.PositiveIntegerField(validators=[MinValueValidator(2)])
    approved = models.BooleanField(default=False)
    requires_fee = models.BooleanField(default=False, editable=False)
    commission = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(5), MaxValueValidator(50)]
    )
    published = models.BooleanField(default=False, editable=False)

    def clean(self):
        if self.requires_fee and self.approved and self.commission is None:
            raise ValidationError({"commission": _("Set a commission between 5% and 50% before approval.")})
        if self.goal and self.price and self.cap and self.goal > self.price * self.cap:
            raise ValidationError({"goal": _("The goal exceeds the maximum sale proceeds.")})

    def __str__(self):
        return self.title
