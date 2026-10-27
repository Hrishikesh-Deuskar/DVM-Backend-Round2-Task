from django.contrib import admin

from .models import Organization, OrganizationMembership

class OrganizationMembershipInline(admin.TabularInline):
    model = OrganizationMembership 
    extra = 1

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)
    inlines = [OrganizationMembershipInline]

@admin.register(OrganizationMembership)
class OrganizationMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "organization", "role", "joined_at")
    list_filter = ("role", "organization")
    search_fields = ("user_username", "organization_name")