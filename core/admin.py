from django.contrib import admin
from .models import Profile, Hobby, Category, Tag, Application, Rating

# This is a minimal, safe admin configuration that only registers
# models confirmed to exist in your project.


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
