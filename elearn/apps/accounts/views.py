from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Sum
from django.contrib import messages

from .models import UserProfile, GamificationStats, NotificationPreference, UserActivity


# ---------------------------
#   AUTHENTICATION
# ---------------------------

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm = request.POST['confirm_password']
        role = request.POST.get('role', 'student')

        if password != confirm:
            messages.error(request, "Passwords do not match.")
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect('register')

        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=request.POST.get('first_name', ''),
            last_name=request.POST.get('last_name', ''),
        )

        profile = user.profile
        profile.role = role
        profile.save()

        UserActivity.objects.create(user=user, activity_type='login', description="Account created")

        messages.success(request, "Registration successful. Please log in.")
        return redirect('login')

    return render(request, 'accounts/register.html')


def login_view(request):
    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST['username'],
            password=request.POST['password']
        )
        
        if user:
            login(request, user)
            UserActivity.objects.create(user=user, activity_type='login')
            return redirect('dashboard')

        messages.error(request, "Invalid username or password.")
    
    return render(request, 'accounts/login.html')


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect('login')


# ---------------------------
#   DASHBOARD + PROFILE
# ---------------------------

@login_required
def dashboard(request):
    user = request.user
    profile = user.profile

    classrooms = (
        user.enrolled_classrooms.all()
        if profile.role == 'student'
        else user.classrooms_taught.all()
    )

    context = {
        "profile": profile,
        "stats": user.gamification_stats,
        "activities": user.activities.all()[:10],
        "classrooms": classrooms,
    }
    return render(request, 'accounts/dashboard.html', context)


@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html', {
        "profile": request.user.profile,
        "stats": request.user.gamification_stats
    })


@login_required
def edit_profile(request):
    user = request.user
    profile = user.profile

    if request.method == "POST":
        user.first_name = request.POST.get("first_name", user.first_name)
        user.last_name = request.POST.get("last_name", user.last_name)
        user.email = request.POST.get("email", user.email)
        user.save()

        profile.bio = request.POST.get('bio', profile.bio)
        profile.phone = request.POST.get('phone', profile.phone)
        profile.school_name = request.POST.get('school_name', profile.school_name)
        profile.class_name = request.POST.get('class_name', profile.class_name)

        if 'profile_picture' in request.FILES:
            profile.profile_picture = request.FILES['profile_picture']

        profile.save()

        messages.success(request, "Profile updated.")
        return redirect('profile_view')

    return render(request, 'accounts/edit_profile.html', {"profile": profile})


# ---------------------------
#   LEADERBOARD
# ---------------------------

def leaderboard(request):
    top_users = (
        User.objects.filter(gamification_stats__isnull=False)
        .annotate(points=Sum("gamification_stats__points"))
        .order_by("-points")[:100]
    )

    rank = None
    if request.user.is_authenticated:
        user_points = request.user.gamification_stats.points
        rank = User.objects.filter(
            gamification_stats__points__gt=user_points
        ).count() + 1

    return render(request, 'accounts/leaderboard.html', {
        "top_users": top_users,
        "rank": rank
    })


# ---------------------------
#   BADGES + STATS
# ---------------------------

@login_required
def badges_view(request):
    stats = request.user.gamification_stats
    return render(request, 'accounts/badges.html', {
        "stats": stats,
        "all_badges": dict(GamificationStats.BADGE_CHOICES),
        "user_badges": stats.badges
    })


@login_required
def user_stats(request):
    user = request.user
    return render(request, 'accounts/user_stats.html', {
        "stats": user.gamification_stats,
        "profile": user.profile,
        "total_activities": user.activities.count(),
        "login_count": user.activities.filter(activity_type='login').count(),
        "quiz_attempts": user.activities.filter(activity_type='quiz_attempt').count(),
        "discussion_posts": user.activities.filter(activity_type='discussion_post').count(),
    })


# ---------------------------
#   NOTIFICATION PREFERENCES
# ---------------------------

@login_required
def notification_preferences(request):
    pref = request.user.notification_preference

    if request.method == 'POST':
        pref.quiz_reminders = 'quiz_reminders' in request.POST
        pref.class_updates = 'class_updates' in request.POST
        pref.discussion_replies = 'discussion_replies' in request.POST
        pref.achievement_notifications = 'achievement_notifications' in request.POST
        pref.email_notifications = 'email_notifications' in request.POST
        pref.save()

        messages.success(request, "Preferences updated.")
        return redirect('notification_preferences')

    return render(request, 'accounts/notification_preferences.html', {"preferences": pref})


# ---------------------------
#   SEARCH + API
# ---------------------------

def search_users(request):
    q = request.GET.get("q", "")
    users = User.objects.filter(
        Q(username__icontains=q) | Q(first_name__icontains=q) |
        Q(last_name__icontains=q) | Q(email__icontains=q)
    )[:20] if len(q) >= 2 else []

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({
            "users": [
                {
                    "id": u.id,
                    "username": u.username,
                    "full_name": u.get_full_name(),
                    "email": u.email,
                    "role": u.profile.role,
                }
                for u in users
            ]
        })

    return render(request, 'accounts/search_users.html', {"users": users, "query": q})


def get_user_info(request, user_id):
    user = get_object_or_404(User, id=user_id)
    stats = user.gamification_stats

    return JsonResponse({
        "id": user.id,
        "username": user.username,
        "full_name": user.get_full_name(),
        "email": user.email,
        "role": user.profile.role,
        "points": stats.points,
        "level": stats.level,
        "badges": stats.badges,
        "attendance_rate": stats.attendance_rate,
    })
