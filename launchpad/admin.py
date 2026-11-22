from django.contrib import admin
from .models import Campaign, Company


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "symbol", "approved")
    list_filter = ("approved", "company")
    list_editable = ("approved",)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "account", "wallet")
