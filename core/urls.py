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
]