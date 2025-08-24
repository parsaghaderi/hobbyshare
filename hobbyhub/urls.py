# hobbyhub/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from core.api_views import (
    HobbyViewSet, CategoryViewSet, TagViewSet, RequirementViewSet,
    ApplicationViewSet, RatingViewSet, ParticipantRatingViewSet, UserViewSet,
    SupplierViewSet, SupplierItemViewSet
)

router = routers.DefaultRouter()
router.register(r'hobbies', HobbyViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'tags', TagViewSet)
router.register(r'requirements', RequirementViewSet)
router.register(r'applications', ApplicationViewSet)
router.register(r'ratings', RatingViewSet)
router.register(r'participant-ratings', ParticipantRatingViewSet)
router.register(r'users', UserViewSet)
router.register(r'suppliers', SupplierViewSet)
router.register(r'supplier-items', SupplierItemViewSet)
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('api/', include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)