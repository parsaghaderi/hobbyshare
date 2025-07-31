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

def hobby_detail(request, hobby_id):
    hobby = get_object_or_404(Hobby, id=hobby_id)
    is_host = request.user == hobby.host

    user_met_requirements = UserRequirement.objects.filter(
        user=request.user, hobby=hobby
    ).values_list('requirement_id', flat=True)

    if request.method == 'POST' and not is_host:
        selected = request.POST.getlist('met_requirements')
        UserRequirement.objects.filter(user=request.user, hobby=hobby).delete()
        for req_id in selected:
            UserRequirement.objects.create(user=request.user, hobby=hobby, requirement_id=req_id)
        user_met_requirements = selected

    # For host: show which requirements each user meets
    user_requirements = {}
    if is_host:
        applications = hobby.applications.all()
        for app in applications:
            reqs = UserRequirement.objects.filter(user=app.applicant, hobby=hobby).values_list('requirement__name', flat=True)
            user_requirements[app.applicant.username] = list(reqs)

    context = {
        'hobby': hobby,
        'is_host': is_host,
        'user_met_requirements': user_met_requirements,
        'user_requirements': user_requirements,
    }
    return render(request, 'hobby_detail.html', context)

@login_required
def create_hobby(request):
    if request.method == 'POST':
        form = HobbyForm(request.POST, request.FILES)
        if form.is_valid():
            hobby = form.save(commit=False)
            hobby.host = request.user

            # Handle new category, tags, requirements
            new_category = form.cleaned_data.get('new_category')
            if new_category:
                category_obj, created = Category.objects.get_or_create(name=new_category)
                hobby.category = category_obj

            hobby.save()
            form.save_m2m()

            # Handle new requirements
            new_requirements = form.cleaned_data.get('new_requirements')
            if new_requirements:
                req_names = [r.strip() for r in new_requirements.split(',') if r.strip()]
                for req_name in req_names:
                    req_obj, created = Requirement.objects.get_or_create(name=req_name)
                    hobby.requirements.add(req_obj)

            return redirect('hobby_detail', hobby_id=hobby.id)
    else:
        form = HobbyForm()
    return render(request, 'hobby_form.html', {'form': form})

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