from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Hobby, Category, Application, Profile, Rating, ParticipantRating, Tag, Requirement
from .forms import HobbyForm, ProfileForm
from django.db.models import Count
from django.utils import timezone
from django.http import JsonResponse, HttpResponseForbidden
from django.db import transaction
from django.views.decorators.http import require_POST
import json

def home(request):
    """
    Displays the homepage with a list of all hobbies.
    Supports filtering by search query and category.
    """
    query = request.GET.get('q')
    category_id = request.GET.get('category')
    hobbies = Hobby.objects.all().order_by('-created_at')

    if query:
        hobbies = hobbies.filter(title__icontains=query)
    if category_id:
        hobbies = hobbies.filter(category_id=category_id)

    categories = Category.objects.all()
    context = {'hobbies': hobbies, 'categories': categories}
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

    context = {
        'hobby': hobby,
        'is_host': is_host,
        'user_application': user_application,
        'contact_info': contact_info,
        'applications': applications,
        'accepted_participants': accepted_participants,
        'event_has_passed': timezone.now() > hobby.date if hobby.date else False,
        'has_rated': has_rated,
    }
    return render(request, 'hobby_detail.html', context)

@login_required
def create_hobby(request):
    """
    Handles the creation of a new hobby.
    Processes standard form data as well as JSON data from Tagify.
    """
    if request.method == 'POST':
        form = HobbyForm(request.POST, request.FILES)
        if form.is_valid():
            hobby = form.save(commit=False)
            hobby.host = request.user

            category_json = form.cleaned_data.get('category')
            if category_json:
                try:
                    data = json.loads(category_json)
                    if data:
                        name = data[0]['value']
                        category_obj, _ = Category.objects.get_or_create(name__iexact=name, defaults={'name': name})
                        hobby.category = category_obj
                except (json.JSONDecodeError, IndexError, KeyError):
                    pass

            hobby.save()

            tags_json = form.cleaned_data.get('tags')
            if tags_json:
                try:
                    data = json.loads(tags_json)
                    for t in data:
                        tag_name = t.get('value')
                        if tag_name:
                            tag_obj, _ = Tag.objects.get_or_create(name__iexact=tag_name, defaults={'name': tag_name})
                            hobby.tags.add(tag_obj)
                except (json.JSONDecodeError, KeyError, TypeError):
                    pass

            # Save requirements
            req_json = form.cleaned_data.get('requirements')
            if req_json:
                try:
                    reqs = json.loads(req_json)
                    for r in reqs:
                        name = r.get('name')
                        provided = r.get('provided', False)
                        if name:
                            Requirement.objects.create(
                                hobby=hobby,
                                name=name,
                                provided_by=request.user if provided else None
                            )
                except json.JSONDecodeError:
                    pass

            return redirect('hobby_detail', hobby_id=hobby.id)
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
        form = UserCreationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save()
                # Safe even if a post_save signal already created the profile
                Profile.objects.get_or_create(user=user)
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()

    return render(request, 'registration/signup.html', {'form': form})

@login_required
def user_profile(request):
    """
    Displays the profile page for the currently logged-in user.
    """
    return render(request, 'profile.html')

@login_required
def edit_profile(request):
    """
    Handles editing the user's profile.
    """
    profile, created = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'edit_profile.html', {'form': form})

def owner_profile(request, user_id):
    owner = get_object_or_404(User, id=user_id)
    hosted_hobbies = Hobby.objects.filter(host=owner)
    owner_tags = Tag.objects.filter(hobby__in=hosted_hobbies).distinct()
    return render(request, 'owner_profile.html', {'owner': owner, 'owner_tags': owner_tags})

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