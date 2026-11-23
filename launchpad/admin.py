from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Campaign, Company


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "symbol", "approved", "published", "commission")
    list_filter = ("approved", "published", "company")
    readonly_fields = ("requires_fee", "published", "campaign_page")

    @admin.display(description="Campaign page")
    def campaign_page(self, obj):
        if obj and obj.approved:
            return format_html('<a href="{}">Open campaign</a>', reverse("detail", args=[obj.reference]))
        return "Available after approval"

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.requires_fee and obj.approved:
            return (*self.readonly_fields, "company", "commission", "token_name",
                    "symbol", "price", "goal", "cap", "duration_minutes", "approved")
        return self.readonly_fields


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "account", "wallet")
