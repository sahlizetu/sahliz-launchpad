from django.utils.translation import gettext_lazy as _
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.forms import modelform_factory, Textarea
from django.shortcuts import get_object_or_404, redirect, render

from .models import Campaign, Company

CampaignForm = modelform_factory(
    Campaign, fields=("title", "sector", "location", "description", "use_of_funds", "token_name", "symbol", "price", "goal", "cap", "duration_minutes"),
    widgets={"description": Textarea(attrs={"rows": 4})},
    labels={"title": _("Title"), "description": _("Startup overview"), "use_of_funds": _("Use of funds"), "sector": _("Sector"), "location": _("Market / city"), "token_name": _("Token name"),
            "symbol": _("Symbol"), "price": _("Price per token (ETH)"), "goal": _("Funding goal (ETH)"),
            "cap": _("Tokens for sale"), "duration_minutes": _("Duration (minutes)")},
)


def home(request):
    return render(request, "home.html", {"campaigns": Campaign.objects.filter(approved=True).select_related("company")})


def detail(request, reference):
    c = get_object_or_404(Campaign.objects.select_related("company"), reference=reference, approved=True)
    return render(request, "detail.html", {
        "campaign": c, "can_launch": c.company.account_id == request.user.pk,
        "chain_data": {"factory": settings.FACTORY_ADDRESS, "reference": "0x" + c.reference.hex.rjust(64, "0"),
                       "issuer": c.company.wallet, "name": c.token_name, "symbol": c.symbol,
                       "price": format(c.price, "f"), "goal": format(c.goal, "f"),
                       "cap": c.cap, "duration": c.duration_minutes},
    })


@login_required
def studio(request):
    company = get_object_or_404(Company, account=request.user)
    form = CampaignForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        campaign = form.save(commit=False)
        campaign.company = company
        campaign.save()
        return redirect("studio")
    return render(request, "studio.html", {"company": company, "form": form, "campaigns": company.campaign_set.all()})




@staff_member_required
def setup(request):
    return render(request, "setup.html", {"factory": settings.FACTORY_ADDRESS})
