from django.contrib import admin
from .models import Profile, Category, Tag, Hobby, Requirement, Application, Rating, ParticipantRating

# Register your models here to make them accessible in the admin panel.
admin.site.register(Profile)
admin.site.register(Category)
admin.site.register(Tag)
admin.site.register(Hobby)
admin.site.register(Requirement)
admin.site.register(Application)
admin.site.register(Rating)
admin.site.register(ParticipantRating)
