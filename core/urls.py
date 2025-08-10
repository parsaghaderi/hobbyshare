# core/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('hobby/<int:hobby_id>/', views.hobby_detail, name='hobby_detail'),
    path('hobby/new/', views.create_hobby, name='create_hobby'),
    path('hobby/<int:hobby_id>/apply/', views.apply_for_hobby, name='apply_for_hobby'),
    path('hobby/<int:hobby_id>/rate/', views.rate_hobby, name='rate_hobby'),
    path('hobby/<int:hobby_id>/rate/participant/<int:participant_id>/', views.rate_participant, name='rate_participant'),
    path('application/<int:app_id>/<str:status>/', views.manage_application, name='manage_application'),
    
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('profile/', views.user_profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('user/<int:user_id>/', views.owner_profile, name='owner_profile'),
    path('requirement/<int:req_id>/claim/', views.claim_requirement, name='claim_requirement'),
    path('api/tags/', views.get_tags, name='get_tags'),
    path('api/categories/', views.get_categories, name='get_categories'),
    path('requirement/<int:req_id>/toggle/', views.claim_requirement, name='claim_requirement'),  # POST
    path('hobby/<int:hobby_id>/requirements/suggest/', views.suggest_requirement, name='suggest_requirement'),  # POST
    path('requirement/<int:req_id>/approve/', views.approve_requirement, name='approve_requirement'),  # POST
    path('requirement/<int:req_id>/reject/', views.reject_requirement, name='reject_requirement'),  # POST
    path('hobby/<int:hobby_id>/requirements/add/', views.add_requirement, name='add_requirement'),
    path('requirement/<int:req_id>/update/', views.update_requirement, name='update_requirement'),
    path('requirement/<int:req_id>/delete/', views.delete_requirement, name='delete_requirement'),
]