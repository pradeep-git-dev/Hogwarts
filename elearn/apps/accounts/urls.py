from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard and Profile
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile_view, name='profile_view'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    
    # Leaderboard and Stats
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('stats/', views.user_stats, name='user_stats'),
    path('badges/', views.badges_view, name='badges_view'),
    
    # User Settings
    path('notifications/preferences/', views.notification_preferences, name='notification_preferences'),
    
    # Search and API
    path('search/', views.search_users, name='search_users'),
    path('api/user/<int:user_id>/', views.get_user_info, name='get_user_info'),
]
