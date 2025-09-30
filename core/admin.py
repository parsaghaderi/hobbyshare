from django.contrib import admin
from .models import (
    Profile, Hobby, Category, Tag, Application, Rating,
    Requirement, SupplierItem, SupplierProfile
)

# Unregister models if they are already registered to avoid errors on reload
# This part is for safety, in case of complex setups.
# You can likely remove this block if it causes issues, but it's good practice.
try:
    admin.site.unregister(Profile)
    admin.site.unregister(Hobby)
    admin.site.unregister(Category)
    admin.site.unregister(Tag)
    admin.site.unregister(Application)
    admin.site.unregister(Rating)
    admin.site.unregister(Requirement)
    admin.site.unregister(SupplierItem)
    admin.site.unregister(SupplierProfile)
except admin.sites.NotRegistered:
    pass


@admin.register(Hobby)
class HobbyAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Hobby model.
    This is a safe configuration that only uses fields known to exist.
    """
    list_display = ('title', 'host', 'address', 'start_datetime', 'recurrence')
    list_filter = ('recurrence', 'category', 'host')
    search_fields = ('title', 'description', 'address')
    date_hierarchy = 'start_datetime'


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'goal')
    search_fields = ('user__username',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('hobby', 'applicant', 'status', 'applied_at')
    list_filter = ('status',)


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('hobby', 'user', 'score', 'created_at')
    list_filter = ('score',)


@admin.register(Requirement)
class RequirementAdmin(admin.ModelAdmin):
    list_display = ('hobby', 'description', 'is_claimed', 'claimed_by')
    list_filter = ('is_claimed',)


@admin.register(SupplierItem)
class SupplierItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'supplier', 'price')
    search_fields = ('name', 'description')


@admin.register(SupplierProfile)
class SupplierProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'company_name')
    search_fields = ('user__username', 'company_name')
