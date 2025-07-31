from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Hobby, Category, Application, Profile, Rating, ParticipantRating, Tag, Requirement, UserRequirement
from .forms import HobbyForm, ProfileForm
from django.db.models import Count
from django.utils import timezone

def home(request):
    query = request.GET.get('q')
    category_id = request.GET.get('category')
    hobbies = Hobby.objects.all().annotate(host_hobby_count=Count('host__hosted_hobbies')).order_by('-created_at')

    if query:
        hobbies = hobbies.filter(title__icontains=query)
    if category_id:
        hobbies = hobbies.filter(category_id=category_id)

    categories = Category.objects.all()
    context = {'hobbies': hobbies, 'categories': categories}
    return render(request, 'home.html', context)

@login_required(login_url='login')
def hobby_detail(request, hobby_id):
    hobby = get_object_or_404(Hobby, id=hobby_id)
    is_host = request.user == hobby.host
    user_application = None
    if request.user.is_authenticated and not is_host:
        user_application = hobby.applications.filter(applicant=request.user).first()

    # Host: handle application status change
    if request.method == 'POST' and is_host:
        app_id = request.POST.get('app_id')
        action = request.POST.get('action')
        application = hobby.applications.filter(id=app_id).first()
        if application:
            if action == 'accept':
                application.status = 'accepted'
                application.save()
            elif action == 'reject':
                application.status = 'rejected'
                application.save()
            elif action == 'remove' and application.status == 'accepted':
                application.delete()  # Remove the participant from the event

    applications = hobby.applications.all() if is_host else None

    context = {
        'hobby': hobby,
        'is_host': is_host,
        'user_application': user_application,
        'applications': applications,
    }
    return render(request, 'hobby_detail.html', context)

from .models import Category, Tag

@login_required
def create_hobby(request):
    categories = Category.objects.all()
    all_tags = Tag.objects.all()
    if request.method == 'POST':
        form = HobbyForm(request.POST, request.FILES)
        selected_tags = request.POST.get('selected_tags', '')
        category_name = request.POST.get('category', '').strip()
        new_category = request.POST.get('new_category', '').strip()
        new_tag = request.POST.get('new_tag', '').strip()
        if form.is_valid():
            hobby = form.save(commit=False)
            hobby.host = request.user
            # Handle category
            if new_category:
                category, _ = Category.objects.get_or_create(name=new_category)
                hobby.category = category
            elif category_name:
                category, _ = Category.objects.get_or_create(name=category_name)
                hobby.category = category
            hobby.save()
            # Handle tags
            tag_names = []
            if selected_tags:
                tag_names += [t.strip() for t in selected_tags.split(',') if t.strip()]
            if new_tag:
                tag_names.append(new_tag)
            for tag_name in tag_names:
                tag, _ = Tag.objects.get_or_create(name=tag_name)
                hobby.tags.add(tag)
            return redirect('home')
        else:
            print(form.errors)
    else:
        form = HobbyForm()
    return render(request, 'hobby_form.html', {
        'form': form,
        'categories': categories,
        'all_tags': all_tags,
    })

@login_required
def apply_for_hobby(request, hobby_id):
    hobby = get_object_or_404(Hobby, id=hobby_id)
    if not request.user.hosted_hobbies.exists():
         # Requirement #3: Must have at least one hobby to apply
        return redirect('profile') # Redirect to profile to add a hobby

    Application.objects.get_or_create(hobby=hobby, applicant=request.user)
    return redirect('hobby_detail', hobby_id=hobby.id)

@login_required
def manage_application(request, app_id, status):
    application = get_object_or_404(Application, id=app_id, hobby__host=request.user)
    if status in ['accepted', 'rejected']:
        application.status = status
        application.save()
    return redirect('hobby_detail', hobby_id=application.hobby.id)

@login_required
def rate_hobby(request, hobby_id):
    hobby = get_object_or_404(Hobby, id=hobby_id)
    if hobby.date and hobby.date > timezone.now():
        return redirect('hobby_detail', hobby_id=hobby.id)  # Don't allow rating before event ends
    if request.method == 'POST':
        score = request.POST.get('score')
        if score:
            Rating.objects.update_or_create(
                hobby=hobby, rater=request.user, defaults={'score': score}
            )
    return redirect('hobby_detail', hobby_id=hobby.id)

@login_required
def rate_participant(request, hobby_id, participant_id):
    hobby = get_object_or_404(Hobby, id=hobby_id, host=request.user)
    participant = get_object_or_404(User, id=participant_id)
    if hobby.date and hobby.date > timezone.now():
        return redirect('hobby_detail', hobby_id=hobby.id)
    if request.method == 'POST':
        score = request.POST.get('score')
        if score:
            ParticipantRating.objects.update_or_create(
                hobby=hobby, participant=participant, host=request.user, defaults={'score': score}
            )
    return redirect('hobby_detail', hobby_id=hobby.id)


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(user=user)
            return redirect('login')  # Redirect to login page after signup
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def user_profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)
    user_hobbies = Hobby.objects.filter(host=request.user)
    signed_up_hobbies = Hobby.objects.filter(applications__applicant=request.user, applications__status='accepted')
    context = {
        'form': form,
        'profile': profile,
        'user_hobbies': user_hobbies,
        'signed_up_hobbies': signed_up_hobbies,
    }
    return render(request, 'profile.html', context)

def owner_profile(request, user_id):
    owner = get_object_or_404(User, id=user_id)
    profile = Profile.objects.filter(user=owner).first()
    hobbies = Hobby.objects.filter(host=owner)
    overall_rating = profile.get_host_rating() if profile else 0
    return render(request, 'owner_profile.html', {
        'owner': owner,
        'profile': profile,
        'hobbies': hobbies,
        'overall_rating': overall_rating,
    })

@login_required
def withdraw_application(request, hobby_id):
    hobby = get_object_or_404(Hobby, id=hobby_id)
    application = hobby.applications.filter(applicant=request.user).first()
    if application:
        application.delete()
    return redirect('hobby_detail', hobby_id=hobby.id)

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User

def profile(request, username):
    user = get_object_or_404(User, username=username)
    # Add any extra context you need, e.g. hobbies, reviews, etc.
    return render(request, 'profile.html', {'profile_user': user})

def host_summary(request, username):
    user = get_object_or_404(User, username=username)
    from .models import Hobby, Profile  # Import your models
    
    # Get user profile
    profile = Profile.objects.filter(user=user).first()
    
    hobbies = Hobby.objects.filter(host=user)
    reviews = user.review_set.all() if hasattr(user, 'review_set') else []
    
    return render(request, 'host_summary.html', {
        'host': user,
        'profile': profile,
        'hobbies': hobbies,
        'reviews': reviews,
    })

@login_required
def edit_hobby(request, hobby_id):
    hobby = get_object_or_404(Hobby, id=hobby_id, host=request.user)
    categories = Category.objects.all()
    all_tags = Tag.objects.all()
    if request.method == 'POST':
        form = HobbyForm(request.POST, request.FILES, instance=hobby)
        selected_tags = request.POST.get('selected_tags', '')
        category_name = request.POST.get('category', '').strip()
        if form.is_valid():
            hobby = form.save(commit=False)
            if category_name:
                category, _ = Category.objects.get_or_create(name=category_name)
                hobby.category = category
            hobby.save()
            hobby.tags.clear()
            if selected_tags:
                tag_names = [t.strip() for t in selected_tags.split(',') if t.strip()]
                for tag_name in tag_names:
                    tag, _ = Tag.objects.get_or_create(name=tag_name)
                    hobby.tags.add(tag)
            return redirect('hobby_detail', hobby_id=hobby.id)
    else:
        form = HobbyForm(instance=hobby)
    return render(request, 'hobby_form.html', {
        'form': form,
        'categories': categories,
        'all_tags': all_tags,
        'edit_mode': True,
        'hobby': hobby,
    })