from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Hobby, Category, Application, Profile, Rating, ParticipantRating, Tag
from .forms import HobbyForm, ProfileForm
from django.db.models import Count
from django.utils import timezone
from django.http import JsonResponse
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

    context = {
        'hobby': hobby,
        'is_host': is_host,
        'user_application': user_application,
        'accepted_participants': hobby.applications.filter(status='accepted'),
        'event_has_passed': timezone.now() > hobby.date if hobby.date else False,
    }
    return render(request, 'hobby_detail.html', context)

@login_required
def create_hobby(request):
    """
    Handles the creation of a new hobby.
    Processes standard form data as well as JSON data from Tagify.
    """
    if request.method == 'POST':
        # Pass request.FILES to handle potential image uploads in the future
        form = HobbyForm(request.POST, request.FILES)
        if form.is_valid():
            hobby = form.save(commit=False)
            hobby.host = request.user

            # Handle Category (ForeignKey)
            category_json = form.cleaned_data.get('category')
            if category_json:
                try:
                    category_data = json.loads(category_json)
                    if category_data:
                        category_name = category_data[0]['value']
                        category_obj, _ = Category.objects.get_or_create(name__iexact=category_name, defaults={'name': category_name})
                        hobby.category = category_obj
                except (json.JSONDecodeError, IndexError):
                    pass
            
            # Save the hobby object to get an ID before adding ManyToMany relationships
            hobby.save()

            # Handle Tags (ManyToManyField)
            tags_json = form.cleaned_data.get('tags')
            if tags_json:
                try:
                    tags_data = json.loads(tags_json)
                    for tag_info in tags_data:
                        tag_obj, _ = Tag.objects.get_or_create(name__iexact=tag_info['value'], defaults={'name': tag_info['value']})
                        hobby.tags.add(tag_obj)
                except (json.JSONDecodeError, IndexError):
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
def rate_hobby(request, hobby_id):
    """
    Allows a participant to rate a hobby after the event has passed.
    """
    hobby = get_object_or_404(Hobby, id=hobby_id)
    if hobby.date and hobby.date > timezone.now():
        return redirect('hobby_detail', hobby_id=hobby.id)
    
    if request.method == 'POST':
        score = request.POST.get('score')
        if score:
            Rating.objects.update_or_create(hobby=hobby, rater=request.user, defaults={'score': score})
    return redirect('hobby_detail', hobby_id=hobby.id)

@login_required
def rate_participant(request, hobby_id, participant_id):
    """
    Allows a host to rate a participant after the event has passed.
    """
    hobby = get_object_or_404(Hobby, id=hobby_id, host=request.user)
    participant = get_object_or_404(User, id=participant_id)
    if hobby.date and hobby.date > timezone.now():
        return redirect('hobby_detail', hobby_id=hobby.id)

    if request.method == 'POST':
        score = request.POST.get('score')
        if score:
            ParticipantRating.objects.update_or_create(hobby=hobby, participant=participant, host=request.user, defaults={'score': score})
    return redirect('hobby_detail', hobby_id=hobby.id)

def signup(request):
    """
    Handles new user registration.
    """
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(user=user) # Create a profile for the new user
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