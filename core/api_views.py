from rest_framework import viewsets, permissions, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.contrib.auth.models import User
from .models import Hobby, Category, Tag, Application, Requirement, Rating, ParticipantRating, Supplier, SupplierItem
from .serializers import (
    HobbySerializer, CategorySerializer, TagSerializer, ApplicationSerializer,
    RequirementSerializer, RatingSerializer, ParticipantRatingSerializer, UserSerializer,
    SupplierSerializer, SupplierItemSerializer
)

class IsHostOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        host = getattr(obj, 'host', None) or getattr(obj, 'hobby', None).host
        return host == request.user

class HobbyViewSet(viewsets.ModelViewSet):
    queryset = Hobby.objects.all().select_related('host','category').prefetch_related('tags','requirements')
    serializer_class = HobbySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        p = self.request.query_params.get('province')
        c = self.request.query_params.get('city')
        cat = self.request.query_params.get('category')
        if p:
            qs = qs.filter(province__iexact=p)
        if c:
            qs = qs.filter(city__iexact=c)
        if cat:
            qs = qs.filter(category_id=cat)
        return qs

    def perform_create(self, serializer):
        """Set host on creation."""
        serializer.save(host=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def apply(self, request, pk=None):
        hobby = self.get_object()
        if hobby.host_id == request.user.id:
            return Response({'detail':'Host cannot apply.'}, status=400)
        app, created = Application.objects.get_or_create(hobby=hobby, applicant=request.user)
        ser = ApplicationSerializer(app)
        return Response(ser.data, status=201 if created else 200)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def rate_host(self, request, pk=None):
        hobby = self.get_object()
        if not hobby.has_ended():
            return Response({'detail':'Event not finished.'}, status=400)
        if hobby.host_id == request.user.id or not hobby.user_is_accepted(request.user):
            return Response({'detail':'Not allowed.'}, status=403)
        score = int(request.data.get('score',0))
        if score not in [1,2,3,4,5]:
            return Response({'detail':'Invalid score.'}, status=400)
        comment = request.data.get('comment','').strip()
        anonymous = bool(request.data.get('anonymous', True))
        rating, _ = Rating.objects.update_or_create(
            hobby=hobby, rater=request.user,
            defaults={'score':score,'comment':comment,'anonymous':anonymous}
        )
        return Response(RatingSerializer(rating).data)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAdminUser]

class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAdminUser]

class RequirementViewSet(mixins.CreateModelMixin,
                         mixins.UpdateModelMixin,
                         mixins.DestroyModelMixin,
                         viewsets.GenericViewSet):
    queryset = Requirement.objects.select_related('hobby','provided_by','suggested_by')
    serializer_class = RequirementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        hobby_id = self.request.data.get('hobby')
        hobby = get_object_or_404(Hobby, pk=hobby_id)
        # if suggested (participant) vs approved (host)
        is_host = hobby.host_id == self.request.user.id
        is_accepted = hobby.user_is_accepted(self.request.user)
        is_approved = is_host
        if not (is_host or is_accepted):
            raise permissions.PermissionDenied('Not allowed')
        serializer.save(hobby=hobby, suggested_by=None if is_host else self.request.user, is_approved=is_approved)

    @action(detail=True, methods=['post'])
    def claim(self, request, pk=None):
        req = self.get_object()
        hobby = req.hobby
        if not req.is_approved:
            return Response({'detail':'Not approved yet.'}, status=400)
        is_host = hobby.host_id == request.user.id
        is_accepted = hobby.user_is_accepted(request.user)
        if not (is_host or is_accepted):
            return Response({'detail':'Not allowed.'}, status=403)
        if req.provided_by_id == request.user.id:
            req.provided_by = None
        else:
            req.provided_by = request.user
        req.save()
        return Response(RequirementSerializer(req).data)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        req = self.get_object()
        if req.hobby.host_id != request.user.id or req.is_approved:
            return Response({'detail':'Not allowed.'}, status=403)
        req.is_approved = True
        req.save()
        return Response(RequirementSerializer(req).data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def link_supplier_item(self, request, pk=None):
        req = self.get_object()
        if req.hobby.host_id != request.user.id:
            return Response({'detail':'Only host can link supplier item.'}, status=403)
        item_id = request.data.get('supplier_item_id')
        if not item_id:
            return Response({'detail':'supplier_item_id required.'}, status=400)
        item = get_object_or_404(SupplierItem, pk=item_id)
        # location and category/tag match enforcement
        if (req.hobby.province.lower(), req.hobby.city.lower(), req.hobby.neighbourhood.lower()) != (
            item.supplier.province.lower(), item.supplier.city.lower(), item.supplier.neighbourhood.lower()):
            return Response({'detail':'Location mismatch.'}, status=400)
        req.supplier_item = item
        req.supplier_status = 'pending'
        from django.utils import timezone as tz
        req.supplier_requested_at = tz.now()
        req.save()
        return Response(RequirementSerializer(req).data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def supplier_decide(self, request, pk=None):
        req = self.get_object()
        if not req.supplier_item or req.supplier_item.supplier.user_id != request.user.id:
            return Response({'detail':'Not allowed.'}, status=403)
        decision = request.data.get('decision')
        if decision not in ['accepted','declined']:
            return Response({'detail':'Invalid decision.'}, status=400)
        req.supplier_status = decision
        if decision == 'accepted' and req.supplier_item.quantity > 0:
            # decrement available quantity
            req.supplier_item.quantity -= 1
            req.supplier_item.save()
        req.save()
        return Response(RequirementSerializer(req).data)

    @action(detail=False, methods=['get'], url_path='suggest')
    def suggest(self, request):
        """Suggest requirements based on hobby tags & available supplier items in same neighbourhood."""
        hobby_id = request.query_params.get('hobby')
        hobby = get_object_or_404(Hobby, pk=hobby_id)
        tag_ids = list(hobby.tags.values_list('id', flat=True))
        # supplier items matching category or tags & location
        items = SupplierItem.objects.filter(
            supplier__province__iexact=hobby.province,
            supplier__city__iexact=hobby.city,
            supplier__neighbourhood__iexact=hobby.neighbourhood,
        ).filter(models.Q(tag_id__in=tag_ids) | models.Q(category=hobby.category)).select_related('supplier','category','tag')[:20]
        return Response(SupplierItemSerializer(items, many=True).data)

class ApplicationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Application.objects.select_related('hobby','applicant')
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'])
    def set_status(self, request, pk=None):
        app = self.get_object()
        if app.hobby.host_id != request.user.id:
            return Response({'detail':'Not allowed.'}, status=403)
        status_val = request.data.get('status')
        if status_val not in ['accepted','rejected']:
            return Response({'detail':'Invalid status.'}, status=400)
        if status_val == 'accepted' and app.hobby.get_participant_count() >= app.hobby.max_participants:
            return Response({'detail':'Hobby full.'}, status=400)
        app.status = status_val
        app.save()
        return Response(ApplicationSerializer(app).data)

class RatingViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Rating.objects.select_related('hobby','rater')
    serializer_class = RatingSerializer

class ParticipantRatingViewSet(viewsets.ModelViewSet):
    queryset = ParticipantRating.objects.select_related('hobby','host','participant')
    serializer_class = ParticipantRatingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        hobby_id = self.request.data.get('hobby')
        participant_id = self.request.data.get('participant')
        hobby = get_object_or_404(Hobby, pk=hobby_id, host=self.request.user)
        participant = get_object_or_404(User, pk=participant_id)
        if not hobby.has_ended():
            raise permissions.PermissionDenied('Event not finished')
        serializer.save(hobby=hobby, host=self.request.user, participant=participant)

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.select_related('user')
    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        if hasattr(self.request.user, 'supplier'):
            raise permissions.PermissionDenied('Already a supplier')
        serializer.save(user=self.request.user)

    def get_queryset(self):
        qs = super().get_queryset().filter(active=True)
        # Allow filtering by location
        p = self.request.query_params.get('province'); c = self.request.query_params.get('city'); n = self.request.query_params.get('neighbourhood')
        if p: qs = qs.filter(province__iexact=p)
        if c: qs = qs.filter(city__iexact=c)
        if n: qs = qs.filter(neighbourhood__iexact=n)
        return qs

class SupplierItemViewSet(viewsets.ModelViewSet):
    queryset = SupplierItem.objects.select_related('supplier__user','category','tag')
    serializer_class = SupplierItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        if not hasattr(self.request.user, 'supplier'):
            raise permissions.PermissionDenied('Not a supplier')
        serializer.save(supplier=self.request.user.supplier)

    def get_queryset(self):
        qs = super().get_queryset()
        # suppliers can only manage own items
        if self.request.method not in permissions.SAFE_METHODS and hasattr(self.request.user, 'supplier'):
            qs = qs.filter(supplier=self.request.user.supplier)
        # optional filtering by category/tag
        cat = self.request.query_params.get('category'); tag = self.request.query_params.get('tag')
        if cat: qs = qs.filter(category_id=cat)
        if tag: qs = qs.filter(tag_id=tag)
        return qs
