from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.db.models import Q, Sum, Count
from django.contrib import messages
from .models import UserProfile, GamificationStats, NotificationPreference, UserActivity

# User Registration
def register(request):
    """Handle user registration"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        role = request.POST.get('role', 'student')
        
        # Validation
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('register')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('register')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return redirect('register')
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        # Create user profile
        UserProfile.objects.create(user=user, role=role)
        
        # Create gamification stats
        GamificationStats.objects.create(user=user)
        
        # Create notification preference
        NotificationPreference.objects.create(user=user)
        
        # Log activity
        UserActivity.objects.create(user=user, activity_type='login', description='Account created')
        
        messages.success(request, 'Registration successful! Please log in.')
        return redirect('login')
    
    return render(request, 'accounts/register.html')


# User Login
def login_view(request):
    """Handle user login"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            UserActivity.objects.create(user=user, activity_type='login')
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'accounts/login.html')


# User Logout
@login_required(login_url='login')
def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('login')


# User Dashboard
@login_required(login_url='login')
def dashboard(request):
    """User dashboard with stats and activity"""
    user = request.user
    profile = user.profile
    gamification_stats = user.gamification_stats
    
    # Get user activities
    activities = user.activities.all()[:10]
    
    # Get enrolled classrooms
    if profile.role == 'student':
        classrooms = user.enrolled_classrooms.all()
    else:
        classrooms = user.classrooms_taught.all()
    
    context = {
        'profile': profile,
        'gamification_stats': gamification_stats,
        'activities': activities,
        'classrooms': classrooms,
    }
    
    return render(request, 'accounts/dashboard.html', context)


# User Profile
@login_required(login_url='login')
def profile_view(request):
    """Display user profile"""
    user = request.user
    profile = user.profile
    gamification_stats = user.gamification_stats
    
    context = {
        'profile': profile,
        'gamification_stats': gamification_stats,
    }
    
    return render(request, 'accounts/profile.html', context)


# Edit Profile
@login_required(login_url='login')
def edit_profile(request):
    """Edit user profile"""
    user = request.user
    profile = user.profile
    
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()
        
        profile.bio = request.POST.get('bio', '')
        profile.phone = request.POST.get('phone', '')
        profile.school_name = request.POST.get('school_name', '')
        profile.class_name = request.POST.get('class_name', '')
        
        if 'profile_picture' in request.FILES:
            profile.profile_picture = request.FILES['profile_picture']
        
        profile.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile_view')
    
    context = {
        'profile': profile,
    }
    
    return render(request, 'accounts/edit_profile.html', context)


# Leaderboard
def leaderboard(request):
    """Display global leaderboard based on points"""
    # Get top 100 users by points
    top_users = User.objects.filter(
        gamification_stats__isnull=False
    ).annotate(
        total_points=Sum('gamification_stats__points')
    ).order_by('-total_points')[:100]
    
    # Get user's rank
    user_rank = None
    if request.user.is_authenticated:
        user_points = request.user.gamification_stats.points
        user_rank = User.objects.filter(
            gamification_stats__points__gt=user_points
        ).count() + 1
    
    context = {
        'top_users': top_users,
        'user_rank': user_rank,
    }
    
    return render(request, 'accounts/leaderboard.html', context)


# User Statistics
@login_required(login_url='login')
def user_stats(request):
    """Display detailed user statistics"""
    user = request.user
    profile = user.profile
    gamification_stats = user.gamification_stats
    
    # Calculate stats
    total_activities = user.activities.count()
    login_count = user.activities.filter(activity_type='login').count()
    quiz_attempts = user.activities.filter(activity_type='quiz_attempt').count()
    discussion_posts = user.activities.filter(activity_type='discussion_post').count()
    
    context = {
        'profile': profile,
        'gamification_stats': gamification_stats,
        'total_activities': total_activities,
        'login_count': login_count,
        'quiz_attempts': quiz_attempts,
        'discussion_posts': discussion_posts,
    }
    
    return render(request, 'accounts/user_stats.html', context)


# Badges View
@login_required(login_url='login')
def badges_view(request):
    """Display user badges and achievements"""
    user = request.user
    gamification_stats = user.gamification_stats
    
    # Get all badge choices
    all_badges = dict(GamificationStats.BADGE_CHOICES)
    user_badges = gamification_stats.badges
    
    context = {
        'gamification_stats': gamification_stats,
        'all_badges': all_badges,
        'user_badges': user_badges,
    }
    
    return render(request, 'accounts/badges.html', context)


# Notification Preferences
@login_required(login_url='login')
def notification_preferences(request):
    """Update notification preferences"""
    user = request.user
    pref, created = NotificationPreference.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        pref.quiz_reminders = request.POST.get('quiz_reminders') == 'on'
        pref.class_updates = request.POST.get('class_updates') == 'on'
        pref.discussion_replies = request.POST.get('discussion_replies') == 'on'
        pref.achievement_notifications = request.POST.get('achievement_notifications') == 'on'
        pref.email_notifications = request.POST.get('email_notifications') == 'on'
        pref.save()
        
        messages.success(request, 'Notification preferences updated!')
        return redirect('notification_preferences')
    
    context = {
        'preferences': pref,
    }
    
    return render(request, 'accounts/notification_preferences.html', context)


# Search Users
def search_users(request):
    """Search for users"""
    query = request.GET.get('q', '')
    users = []
    
    if len(query) >= 2:
        users = User.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )[:20]
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        user_data = [
            {
                'id': user.id,
                'username': user.username,
                'full_name': user.get_full_name() or user.username,
                'email': user.email,
                'role': user.profile.get_role_display() if hasattr(user, 'profile') else 'N/A',
            }
            for user in users
        ]
        return JsonResponse({'users': user_data})
    
    context = {
        'users': users,
        'query': query,
    }
    
    return render(request, 'accounts/search_users.html', context)


# Get User Info (API)
def get_user_info(request, user_id):
    """Get user information (API endpoint)"""
    try:
        user = get_object_or_404(User, id=user_id)
        profile = user.profile
        gamification_stats = user.gamification_stats
        
        data = {
            'id': user.id,
            'username': user.username,
            'full_name': user.get_full_name() or user.username,
            'email': user.email,
            'role': profile.get_role_display(),
            'points': gamification_stats.points,
            'level': gamification_stats.level,
            'badges': gamification_stats.badges,
            'attendance_rate': gamification_stats.attendance_rate,
        }
        return JsonResponse(data)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
