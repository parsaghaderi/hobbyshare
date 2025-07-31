# core/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('hobby/<int:hobby_id>/', views.hobby_detail, name='hobby_detail'),
    path('hobby/new/', views.create_hobby, name='create_hobby'),
    path('hobby/<int:hobby_id>/apply/', views.apply_for_hobby, name='apply_for_hobby'),
    path('application/<int:app_id>/<str:status>/', views.manage_application, name='manage_application'),
    path('hobby/<int:hobby_id>/rate/', views.rate_hobby, name='rate_hobby'),
    
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('profile/', views.user_profile, name='profile'),
    path('user/<int:user_id>/', views.owner_profile, name='owner_profile'),
    path('hobby/<int:hobby_id>/withdraw/', views.withdraw_application, name='withdraw_application'),
    path('profile/<str:username>/', views.profile, name='profile'),
    path('host/<str:username>/summary/', views.host_summary, name='host_summary'),
    path('hobby/<int:hobby_id>/edit/', views.edit_hobby, name='edit_hobby'),
]