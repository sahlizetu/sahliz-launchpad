from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _
from eth_account import Account
from eth_account.messages import encode_defunct
from eth_keys.exceptions import BadSignature
from eth_utils import is_checksum_address

from .models import wallet_validator


class StartupSignupForm(UserCreationForm):
    company_name = forms.CharField(max_length=100, label=_("Startup name"))
    email = forms.EmailField(label=_("Contact email"))

    def save(self, commit=True):
        account = super().save(commit=False)
        account.email = self.cleaned_data["email"]
        if commit:
            account.save()
        return account


class WalletForm(forms.Form):
    wallet = forms.CharField(max_length=42, validators=[wallet_validator])
    signature = forms.CharField(max_length=132)

    def verified_wallet(self, message):
        wallet = self.cleaned_data["wallet"]
        if not is_checksum_address(wallet):
            return None
        try:
            recovered = Account.recover_message(
                encode_defunct(text=message), signature=self.cleaned_data["signature"]
            )
        except (ValueError, TypeError, BadSignature):
            return None
        return recovered if recovered == wallet else None
