from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Hobby, Category, Application, Profile, Rating, ParticipantRating, Tag, Requirement, Supplier, SupplierItem, HobbyImage
from .forms import HobbyForm, ProfileForm, SupplierUserCreationForm
from django.db.models import Count
from django.utils import timezone
from django.http import JsonResponse, HttpResponseForbidden
from django.db import transaction
from django.views.decorators.http import require_POST
from django.contrib import messages
import json
from types import SimpleNamespace
from django.db.models import Q

def home(request):
    hobbies = (
        Hobby.objects.all()
        .select_related('category', 'host')
        .prefetch_related('tags')
        .order_by('-date', '-id')
    )
    categories = Category.objects.all().order_by('name')

    def _parse_csv_list(value):
        if not value:
            return []
        return [v.strip() for v in value.split(',') if v.strip()]

    q = (request.GET.get('q') or '').strip()
    category_id = (request.GET.get('category') or '').strip()
    province = (request.GET.get('province') or '').strip()
    city = (request.GET.get('city') or '').strip()
    neighbourhood = (request.GET.get('neighbourhood') or '').strip()
    tag_names = _parse_csv_list(request.GET.get('tags'))

    if q:
        hobbies = hobbies.filter(
            Q(title__icontains=q)
            | Q(description__icontains=q)
            | Q(place__icontains=q)
            | Q(category__name__icontains=q)
            | Q(tags__name__icontains=q)
        ).distinct()
    if category_id:
        hobbies = hobbies.filter(category_id=category_id)
    if province:
        hobbies = hobbies.filter(province__iexact=province)
    if city:
        hobbies = hobbies.filter(city__iexact=city)
    if neighbourhood:
        hobbies = hobbies.filter(neighbourhood__icontains=neighbourhood)
    if tag_names:
        hobbies = hobbies.filter(tags__name__in=tag_names).distinct()

    applied_filters = any([q, category_id, province, city, neighbourhood, tag_names])

    static_preview = False
    display_hobbies = hobbies

    if not request.user.is_authenticated and not applied_filters:
        static_preview = True
        # Static preview objects use only fields template expects
        display_hobbies = [
            SimpleNamespace(
                id=None,
                title='Guitar Jam Circle',
                description='Casual beginner-friendly acoustic jam.',
                category=SimpleNamespace(name='Music'),
                city='Montreal', province='QC', neighbourhood='Plateau',
                image=None
            ),
            SimpleNamespace(
                id=None,
                title='Saturday Sketch Meetup',
                description='Outdoor urban sketching + critiques.',
                category=SimpleNamespace(name='Art'),
                city='Toronto', province='ON', neighbourhood='Kensington',
                image=None
            ),
            SimpleNamespace(
                id=None,
                title='Trail Run & Stretch',
                description='5K social trail run & cooldown.',
                category=SimpleNamespace(name='Outdoors'),
                city='Vancouver', province='BC', neighbourhood='North Shore',
                image=None
            ),
            SimpleNamespace(
                id=None,
                title='Board Game Night',
                description='Strategy & party games—bring one!',
                category=SimpleNamespace(name='Games'),
                city='Calgary', province='AB', neighbourhood='Beltline',
                image=None
            ),
            SimpleNamespace(
                id=None,
                title='Intro to Bread Baking',
                description='Hands-on sourdough basics.',
                category=SimpleNamespace(name='Cooking'),
                city='Ottawa', province='ON', neighbourhood='Glebe',
                image=None
            ),
            SimpleNamespace(
                id=None,
                title='Community Photography Walk',
                description='Golden hour photo walk & tips.',
                category=SimpleNamespace(name='Photography'),
                city='Quebec City', province='QC', neighbourhood='Old Town',
                image=None
            ),
        ]

    context = {
        'hobbies': hobbies,
        'display_hobbies': display_hobbies,
        'static_preview': static_preview,
        'categories': categories,
        'tags': Tag.objects.all().order_by('name'),
        'province_selected': province,
        'city_selected': city,
    }
    return render(request, 'home.html', context)

def hobby_detail(request, hobby_id):
    """
    Displays the detailed view for a single hobby.
    """
    hobby = get_object_or_404(Hobby, id=hobby_id)
    is_host = request.user == hobby.host
    user_application = None
    if request.user.is_authenticated:
        user_application = hobby.applications.filter(applicant=request.user).first()

    contact_info = None
    if user_application and user_application.status == 'accepted':
        contact_info = hobby.host.email or hobby.host.username

    has_rated = Rating.objects.filter(hobby=hobby, rater=request.user).exists() if request.user.is_authenticated else False
    applications = hobby.applications.all() if is_host else None
    accepted_participants = hobby.applications.filter(status='accepted')

    supplier_items = None
    if is_host:
        qs = SupplierItem.objects.select_related('supplier__user','category','tag').filter(
            supplier__province__iexact=hobby.province or '',
            supplier__city__iexact=hobby.city or '',
            quantity__gt=0,
            supplier__active=True
        )
        if hobby.neighbourhood:
            qs = qs.filter(supplier__neighbourhood__iexact=hobby.neighbourhood)
        supplier_items = qs[:50]

    context = {
        'hobby': hobby,
        'is_host': is_host,
        'user_application': user_application,
        'contact_info': contact_info,
        'applications': applications,
        'accepted_participants': accepted_participants,
        'event_has_passed': timezone.now() > hobby.date if hobby.date else False,
        'has_rated': has_rated,
        'supplier_items': supplier_items,
    }
    return render(request, 'hobby_detail.html', context)

@login_required
def create_hobby(request):
    """
    Handles the creation of a new hobby.
    Processes standard form data as well as JSON data from Tagify.
    """
    def _parse_tagify(value):
        """
        Tagify returns JSON like: [{"value": "Foo"}]. Accept JSON, CSV, or plain strings.
        """
        if not value:
            return []
        raw = (value or "").strip()
        if not raw:
            return []
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            # Allow comma-separated or single values
            return [v.strip() for v in raw.split(",") if v.strip()]
        if isinstance(data, list):
            out = []
            for item in data:
                if isinstance(item, dict):
                    v = (item.get("value") or "").strip()
                    if v:
                        out.append(v)
                elif isinstance(item, str):
                    v = item.strip()
                    if v:
                        out.append(v)
            return out
        if isinstance(data, dict):
            v = (data.get("value") or "").strip()
            return [v] if v else []
        return []

    if request.method == 'POST':
        form = HobbyForm(request.POST, request.FILES)
        if form.is_valid():
            hobby = form.save(commit=False)
            hobby.host = request.user

            category_names = _parse_tagify(form.cleaned_data.get('category'))
            if category_names:
                name = category_names[0]
                category_obj = Category.objects.filter(name__iexact=name).first()
                if not category_obj:
                    category_obj = Category.objects.create(name=name)
                hobby.category = category_obj

            # Location fields
            hobby.province = form.cleaned_data.get('province') or ''
            hobby.city = form.cleaned_data.get('city') or ''
            hobby.neighbourhood = form.cleaned_data.get('neighbourhood') or ''
            hobby.save()

            extra_files = request.FILES.getlist('images')
            if extra_files:
                max_extra = 5
                for idx, f in enumerate(extra_files[:max_extra]):
                    HobbyImage.objects.create(hobby=hobby, image=f, position=idx)
                if len(extra_files) > max_extra:
                    messages.info(request, f'Only the first {max_extra} images were saved.')
                if not hobby.image:
                    hobby.image = extra_files[0]
                    hobby.save(update_fields=['image'])

            tag_names = _parse_tagify(form.cleaned_data.get('tags'))
            for tag_name in tag_names:
                tag_obj = Tag.objects.filter(name__iexact=tag_name).first()
                if not tag_obj:
                    tag_obj = Tag.objects.create(name=tag_name)
                hobby.tags.add(tag_obj)

            # Save requirements (primary: JSON from hidden field; fallback: discrete form inputs)
            req_json = form.cleaned_data.get('requirements')
            created_any = False
            if req_json:
                try:
                    reqs = json.loads(req_json)
                    if isinstance(reqs, list):
                        for r in reqs:
                            if not isinstance(r, dict):
                                continue
                            name = (r.get('name') or '').strip()
                            provided = bool(r.get('provided'))
                            if name:
                                Requirement.objects.create(
                                    hobby=hobby,
                                    name=name,
                                    provided_by=request.user if provided else None,
                                    is_approved=True  # explicit for clarity
                                )
                                created_any = True
                except json.JSONDecodeError:
                    pass

            if not created_any:
                # Fallback: look for array-style inputs (req_name[] / req_provided[])
                names = request.POST.getlist('req_name[]')
                provided_flags = request.POST.getlist('req_provided[]')
                for idx, raw_name in enumerate(names):
                    name = (raw_name or '').strip()
                    if not name:
                        continue
                    provided = False
                    if idx < len(provided_flags):
                        flag = provided_flags[idx]
                        provided = flag in ['on', 'true', '1', 'yes']
                    Requirement.objects.create(
                        hobby=hobby,
                        name=name,
                        provided_by=request.user if provided else None,
                        is_approved=True
                    )

            return redirect('hobby_detail', hobby_id=hobby.id)
        messages.error(request, "Please fix the errors below and try again.")
    else:
        form = HobbyForm()
    return render(request, 'hobby_form.html', {'form': form})

@login_required
def apply_for_hobby(request, hobby_id):
    """
    Allows a logged-in user to apply for a hobby.
    """
    hobby = get_object_or_404(Hobby, id=hobby_id)
    Application.objects.get_or_create(hobby=hobby, applicant=request.user)
    return redirect('hobby_detail', hobby_id=hobby.id)

@login_required
def manage_application(request, app_id, status):
    """
    Allows a hobby host to accept or reject an application.
    """
    application = get_object_or_404(Application, id=app_id, hobby__host=request.user)
    if status in ['accepted', 'rejected']:
        if status == 'accepted' and application.hobby.get_participant_count() >= application.hobby.max_participants:
            # Hobby is full, do not accept.
            # Optionally, add a Django message to inform the user.
            pass
        else:
            application.status = status
            application.save()
    return redirect('hobby_detail', hobby_id=application.hobby.id)

@login_required
@require_POST
def claim_requirement(request, req_id):
    req = get_object_or_404(Requirement, id=req_id)
    hobby = req.hobby
    is_host = hobby.host_id == request.user.id
    is_accepted = hobby.user_is_accepted(request.user)

    if not (is_host or is_accepted):
        return HttpResponseForbidden("Not allowed")

    # Only approved requirements can be claimed
    if not req.is_approved:
        return redirect('hobby_detail', hobby_id=hobby.id)

    if req.provided_by is None:
        # Claim (host or accepted participant)
        if is_host or is_accepted:
            req.provided_by = request.user
            req.save()
    else:
        # Unclaim (same user or host)
        if is_host or req.provided_by_id == request.user.id:
            req.provided_by = None
            req.save()
    return redirect('hobby_detail', hobby_id=hobby.id)

@login_required
@require_POST
def suggest_requirement(request, hobby_id):
    """
    Accepted participants can suggest requirements (pending approval).
    """
    hobby = get_object_or_404(Hobby, id=hobby_id)
    if not hobby.user_is_accepted(request.user):
        return HttpResponseForbidden("Not allowed")

    name = (request.POST.get('name') or '').strip()
    if name:
        Requirement.objects.create(
            hobby=hobby,
            name=name,
            suggested_by=request.user,
            is_approved=False
        )
    return redirect('hobby_detail', hobby_id=hobby.id)

@login_required
@require_POST
def approve_requirement(request, req_id):
    """
    Host approves a suggested requirement.
    """
    req = get_object_or_404(Requirement, id=req_id, hobby__host=request.user, is_approved=False)
    req.is_approved = True
    req.save()
    return redirect('hobby_detail', hobby_id=req.hobby_id)

@login_required
@require_POST
def reject_requirement(request, req_id):
    """
    Host rejects (deletes) a suggested requirement.
    """
    req = get_object_or_404(Requirement, id=req_id, hobby__host=request.user, is_approved=False)
    hobby_id = req.hobby_id
    req.delete()
    return redirect('hobby_detail', hobby_id=hobby_id)

@login_required
def rate_hobby(request, hobby_id):
    """
    Participants can rate host only after the event has ended.
    """
    hobby = get_object_or_404(Hobby, id=hobby_id)
    if not hobby.has_ended():
        return redirect('hobby_detail', hobby_id=hobby.id)

    # must be an accepted participant (not the host)
    if hobby.host_id == request.user.id or not hobby.user_is_accepted(request.user):
        return HttpResponseForbidden("Not allowed")

    if request.method == 'POST':
        score = request.POST.get('score')
        comment = request.POST.get('comment', '').strip()
        anonymous = request.POST.get('anonymous') == 'on'
        if score:
            Rating.objects.update_or_create(
                hobby=hobby,
                rater=request.user,
                defaults={'score': score, 'comment': comment, 'anonymous': anonymous}
            )
    return redirect('hobby_detail', hobby_id=hobby.id)

@login_required
def rate_participant(request, hobby_id, participant_id):
    """
    Host rates participants only after the event has ended.
    """
    hobby = get_object_or_404(Hobby, id=hobby_id, host=request.user)
    if not hobby.has_ended():
        return redirect('hobby_detail', hobby_id=hobby.id)

    participant = get_object_or_404(User, id=participant_id)
    if request.method == 'POST':
        score = request.POST.get('score')
        comment = request.POST.get('comment', '').strip()
        if score:
            ParticipantRating.objects.update_or_create(
                hobby=hobby,
                participant=participant,
                host=request.user,
                defaults={'score': score, 'comment': comment}
            )
    return redirect('hobby_detail', hobby_id=hobby.id)

def signup(request):
    """
    Handles new user registration.
    """
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = SupplierUserCreationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save()
                # Safe even if a post_save signal already created the profile
                Profile.objects.get_or_create(user=user)
            login(request, user)
            return redirect('home')
    else:
        form = SupplierUserCreationForm()

    return render(request, 'registration/signup.html', {'form': form})

@login_required
def profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    from django.templatetags.static import static
    default_profile_image = static('icons/default-profile.svg')
    hosted_hobbies = Hobby.objects.filter(host=request.user).order_by('-date')
    my_apps = (
        Application.objects
        .filter(applicant=request.user)
        .select_related('hobby')
        .order_by('-id')
    )
    return render(
        request,
        'profile.html',
        {
            'profile': profile,
            'hosted_hobbies': hosted_hobbies,
            'my_apps': my_apps,
            'default_profile_image': default_profile_image,
        },
    )

@login_required
def edit_profile(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            with transaction.atomic():
                obj = form.save(commit=False)
                for field, remove_field in [
                    ('image', 'remove_image'),
                    ('image2', 'remove_image2'),
                    ('image3', 'remove_image3'),
                ]:
                    if remove_field in form.cleaned_data and form.cleaned_data[remove_field]:
                        old = getattr(profile, field)
                        if old:
                            old.delete(save=False)
                        setattr(obj, field, None)
                        continue
                    if field in request.FILES:
                        old = getattr(profile, field)
                        if old:
                            old.delete(save=False)
                obj.save()
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'profile_edit.html', {'form': form, 'profile': profile})

def owner_profile(request, user_id):
    owner = get_object_or_404(User, id=user_id)
    hosted_hobbies = Hobby.objects.filter(host=owner)
    owner_tags = Tag.objects.filter(hobby__in=hosted_hobbies).distinct()
    return render(request, 'owner_profile.html', {'owner': owner, 'owner_tags': owner_tags})

@login_required
def supplier_dashboard(request):
    """Dashboard for suppliers to manage inventory."""
    if not hasattr(request.user, 'supplier'):
        return redirect('home')
    supplier = request.user.supplier
    items = supplier.items.select_related('category','tag').all().order_by('-created_at')
    categories = Category.objects.all()
    tags = Tag.objects.all()
    pending_requests = Requirement.objects.select_related('hobby','supplier_item').filter(
        supplier_item__supplier=supplier, supplier_status='pending'
    ).order_by('-supplier_requested_at')
    recent_accepted = Requirement.objects.select_related('hobby','supplier_item').filter(
        supplier_item__supplier=supplier, supplier_status='accepted'
    ).order_by('-supplier_requested_at')[:10]
    if request.method == 'POST':
        name = (request.POST.get('name') or '').strip()
        category_id = request.POST.get('category')
        tag_id = request.POST.get('tag')
        quantity = int(request.POST.get('quantity') or 1)
        is_rental = request.POST.get('is_rental') == 'on'
        price = request.POST.get('price') or '0'
        image = request.FILES.get('image')
        if name:
            SupplierItem.objects.create(
                supplier=supplier,
                name=name,
                category_id=category_id or None,
                tag_id=tag_id or None,
                quantity=quantity,
                is_rental=is_rental,
                price=price,
                image=image
            )
            return redirect('supplier_dashboard')
    return render(request, 'supplier_dashboard.html', {
        'supplier': supplier,
        'items': items,
        'categories': categories,
        'tags': tags,
        'pending_requests': pending_requests,
        'recent_accepted': recent_accepted,
    })

from django.views.decorators.http import require_GET

@login_required
@require_GET
def supplier_item_suggestions(request):
    """Return JSON of supplier items matching provisional hobby details.
    Params: province, city, neighbourhood, category (name), tags (comma separated names)
    """
    province = (request.GET.get('province') or '').strip()
    city = (request.GET.get('city') or '').strip()
    neighbourhood = (request.GET.get('neighbourhood') or '').strip()
    category_name = (request.GET.get('category') or '').strip()
    tag_names = [t.strip() for t in (request.GET.get('tags') or '').split(',') if t.strip()]

    qs = SupplierItem.objects.select_related('supplier__user','category','tag','supplier')
    if province: qs = qs.filter(supplier__province__iexact=province)
    if city: qs = qs.filter(supplier__city__iexact=city)
    if neighbourhood: qs = qs.filter(supplier__neighbourhood__iexact=neighbourhood)
    if category_name:
        cat_obj = Category.objects.filter(name__iexact=category_name).first()
        if cat_obj:
            qs = qs.filter(Q(category=cat_obj) | Q(tag__isnull=False))  # allow any tag, refined below
    if tag_names:
        existing_tags = Tag.objects.filter(name__in=tag_names)
        qs = qs.filter(Q(tag__in=existing_tags) | Q(category__name__iexact=category_name))
    qs = qs.filter(quantity__gt=0, supplier__active=True)[:25]
    data = [
        {
            'id': item.id,
            'name': item.name,
            'is_rental': item.is_rental,
            'price': str(item.price),
            'quantity': item.quantity,
            'category': item.category.name if item.category else None,
            'tag': item.tag.name if item.tag else None,
            'supplier': item.supplier.user.username,
        } for item in qs
    ]
    return JsonResponse(data, safe=False)

# --- API-style views for JavaScript ---

def get_tags(request):
    """
    Returns a JSON list of all tag names for Tagify.
    """
    tags = Tag.objects.values_list('name', flat=True)
    return JsonResponse(list(tags), safe=False)

def get_categories(request):
    """
    Returns a JSON list of all category names for Tagify.
    """
    categories = Category.objects.values_list('name', flat=True)
    return JsonResponse(list(categories), safe=False)

@login_required
@require_POST
def add_requirement(request, hobby_id):
    """
    Host adds a new approved requirement to their hobby.
    """
    hobby = get_object_or_404(Hobby, id=hobby_id, host=request.user)
    name = (request.POST.get('name') or '').strip()
    if name:
        Requirement.objects.create(hobby=hobby, name=name, is_approved=True)
    return redirect('hobby_detail', hobby_id=hobby.id)

@login_required
@require_POST
def update_requirement(request, req_id):
    """
    Host renames an existing requirement.
    """
    req = get_object_or_404(Requirement, id=req_id, hobby__host=request.user)
    name = (request.POST.get('name') or '').strip()
    if name:
        req.name = name
        req.save()
    return redirect('hobby_detail', hobby_id=req.hobby_id)

@login_required
@require_POST
def delete_requirement(request, req_id):
    """
    Host deletes a requirement.
    """
    req = get_object_or_404(Requirement, id=req_id, hobby__host=request.user)
    hobby_id = req.hobby_id
    req.delete()
    return redirect('hobby_detail', hobby_id=hobby_id)

@login_required
@require_POST
def supplier_decide_requirement(request, req_id, decision):
    req = get_object_or_404(Requirement, id=req_id, supplier_item__supplier__user=request.user)
    if decision not in ['accepted','declined']:
        return HttpResponseForbidden('Invalid decision')
    if decision == 'accepted' and req.supplier_status != 'accepted':
        item = req.supplier_item
        if item and item.quantity > 0:
            item.quantity -= 1
            item.save()
    req.supplier_status = decision
    req.save()
    messages.success(request, f'Request {decision}.')
    return redirect('supplier_dashboard')

@login_required
@require_POST
def host_link_supplier_item(request, req_id):
    """Host links an approved requirement to a supplier item to request fulfillment."""
    req = get_object_or_404(Requirement, id=req_id, hobby__host=request.user)
    if not req.is_approved:
        return redirect('hobby_detail', hobby_id=req.hobby_id)
    if req.supplier_item:  # already linked
        return redirect('hobby_detail', hobby_id=req.hobby_id)
    item_id = request.POST.get('supplier_item_id')
    if not item_id:
        return redirect('hobby_detail', hobby_id=req.hobby_id)
    try:
        item = SupplierItem.objects.get(id=item_id)
    except SupplierItem.DoesNotExist:
        messages.error(request, 'Invalid supplier item.')
        return redirect('hobby_detail', hobby_id=req.hobby_id)
    # Location validation (province + city required; neighbourhood only if both have values)
    def norm(s):
        return (s or '').strip().lower()
    if norm(req.hobby.province) != norm(item.supplier.province) or norm(req.hobby.city) != norm(item.supplier.city):
        messages.error(request, 'Supplier item province/city mismatch.')
        return redirect('hobby_detail', hobby_id=req.hobby_id)
    if req.hobby.neighbourhood and item.supplier.neighbourhood and norm(req.hobby.neighbourhood) != norm(item.supplier.neighbourhood):
        messages.error(request, 'Supplier item neighbourhood mismatch.')
        return redirect('hobby_detail', hobby_id=req.hobby_id)
    from django.utils import timezone as tz
    req.supplier_item = item
    req.supplier_status = 'pending'
    req.supplier_requested_at = tz.now()
    req.save()
    messages.success(request, f'Request sent to supplier {item.supplier.user.username}.')
    return redirect('hobby_detail', hobby_id=req.hobby_id)
