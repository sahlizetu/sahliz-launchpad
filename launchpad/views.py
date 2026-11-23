from secrets import token_urlsafe

from django.contrib import messages
from django.contrib.auth import login
from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.views.decorators.http import require_POST
from django.utils.translation import gettext_lazy as _
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.forms import modelform_factory, Textarea
from django.shortcuts import get_object_or_404, redirect, render

from .chain import campaign_is_deployed
from .forms import StartupSignupForm, WalletForm
from .models import Campaign, Company

CampaignForm = modelform_factory(
    Campaign, fields=("title", "sector", "location", "description", "use_of_funds", "token_name", "symbol", "price", "goal", "cap", "duration_minutes"),
    widgets={"description": Textarea(attrs={"rows": 4})},
    labels={"title": _("Title"), "description": _("Startup overview"), "use_of_funds": _("Use of funds"), "sector": _("Sector"), "location": _("Market / city"), "token_name": _("Token name"),
            "symbol": _("Symbol"), "price": _("Price per token (ETH)"), "goal": _("Funding goal (ETH)"),
            "cap": _("Tokens for sale"), "duration_minutes": _("Duration (minutes)")},
)


def home(request):
    return render(request, "home.html", {"campaigns": Campaign.objects.filter(approved=True).filter(Q(requires_fee=False) | Q(published=True)).select_related("company")})


def detail(request, reference):
    c = get_object_or_404(Campaign.objects.select_related("company"), reference=reference, approved=True)
    is_owner = c.company.account_id == request.user.pk
    if c.requires_fee and not c.published and not (is_owner or request.user.is_superuser):
        raise Http404
    return render(request, "detail.html", {
        "campaign": c, "can_launch": is_owner, "can_approve": request.user.is_superuser and c.requires_fee and not c.published,
        "chain_data": {"factory": settings.FEE_FACTORY_ADDRESS if c.requires_fee else settings.FACTORY_ADDRESS,
                       "requiresFee": c.requires_fee, "commission": c.commission, "reference": "0x" + c.reference.hex.rjust(64, "0"),
                       "issuer": c.company.wallet, "name": c.token_name, "symbol": c.symbol,
                       "price": format(c.price, "f"), "goal": format(c.goal, "f"),
                       "cap": c.cap, "duration": c.duration_minutes},
    })


@login_required
def studio(request):
    company = get_object_or_404(Company, account=request.user)
    if not company.wallet:
        return redirect("connect-wallet")
    form = CampaignForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        campaign = form.save(commit=False)
        campaign.company = company
        campaign.requires_fee = True
        campaign.save()
        return redirect("studio")
    return render(request, "studio.html", {"company": company, "form": form, "campaigns": company.campaign_set.all()})




@staff_member_required
def setup(request):
    return render(request, "setup.html", {"factory": settings.FACTORY_ADDRESS, "fee_factory": settings.FEE_FACTORY_ADDRESS, "treasury": settings.SAHLIZ_TREASURY, "can_deploy_fee_factory": request.user.is_superuser})


@transaction.atomic
def signup(request):
    if request.user.is_authenticated:
        return redirect("home")
    form = StartupSignupForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        account = form.save()
        Company.objects.create(account=account, name=form.cleaned_data["company_name"])
        login(request, account)
        return redirect("connect-wallet")
    return render(request, "signup.html", {"form": form})


@login_required
def connect_wallet(request):
    company = get_object_or_404(Company, account=request.user)
    if company.wallet:
        return redirect("studio")
    nonce = request.session.setdefault("wallet_nonce", token_urlsafe(32))
    message = f"Sahliz Launchpad wallet verification\nSite: {request.get_host()}\nAccount: {request.user.pk}\nNonce: {nonce}"
    if request.method == "POST":
        form = WalletForm(request.POST)
        wallet = form.verified_wallet(message) if form.is_valid() else None
        if wallet:
            Company.objects.filter(pk=company.pk, wallet="").update(wallet=wallet)
            request.session.pop("wallet_nonce", None)
            return redirect("studio")
        messages.error(request, _("Wallet signature could not be verified."))
    return render(request, "wallet.html", {"wallet_message": message})


@login_required
@require_POST
def publish_campaign(request, reference):
    campaign = get_object_or_404(
        Campaign.objects.select_related("company"),
        reference=reference, approved=True, requires_fee=True, company__account=request.user,
    )
    if not campaign.published:
        try:
            deployed = campaign_is_deployed(campaign)
        except (OSError, ValueError, TypeError, KeyError):
            deployed = False
        if deployed:
            Campaign.objects.filter(pk=campaign.pk, approved=True, commission=campaign.commission).update(published=True)
        else:
            messages.error(request, _("Deployment could not be verified on Sepolia. Try publishing again once confirmed."))
    return redirect("detail", reference=reference)
