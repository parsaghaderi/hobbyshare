from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from .models import Hobby, Category, Application, Profile, Rating, ParticipantRating
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
    user_application = None
    if request.user.is_authenticated:
        user_application = Application.objects.filter(hobby=hobby, applicant=request.user).first()

    contact_info = None
    if user_application and user_application.status == 'accepted':
        contact_info = hobby.host.email # Or other contact info

    context = {
        'hobby': hobby,
        'is_host': is_host,
        'user_application': user_application,
        'contact_info': contact_info
    }
    return render(request, 'hobby_detail.html', context)

@login_required
def create_hobby(request):
    if request.method == 'POST':
        form = HobbyForm(request.POST, request.FILES)
        if form.is_valid():
            hobby = form.save(commit=False)
            hobby.host = request.user
            hobby.save()
            form.save_m2m() # Important for ManyToMany fields
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