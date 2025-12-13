from django.contrib import admin
from .models import Profile, Category, Tag, Hobby, HobbyImage, Requirement, Application, Rating, ParticipantRating


class HobbyImageInline(admin.TabularInline):
    model = HobbyImage
    extra = 0

@admin.register(Hobby)
class HobbyAdmin(admin.ModelAdmin):
    list_display = ('title','host','date','place','recurrence')
    list_filter = ('recurrence','category','city','province')
    search_fields = ('title','description','place','city','province')
    inlines = [HobbyImageInline]

admin.site.register(Profile)
admin.site.register(Category)
admin.site.register(Tag)
admin.site.register(Requirement)
admin.site.register(Application)
admin.site.register(Rating)
admin.site.register(ParticipantRating)
