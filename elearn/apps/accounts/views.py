from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Sum, Q
from django.http import JsonResponse

from .models import UserProfile, GamificationStats, NotificationPreference, UserActivity


# =========================================================
# AUTH
# =========================================================

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm = request.POST.get('confirm_password')
        role = request.POST.get('role', 'student')

        if password != confirm:
            messages.error(request, "Passwords do not match.")
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already used.")
            return redirect('register')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=request.POST.get('first_name', ''),
            last_name=request.POST.get('last_name', '')
        )

        # Update profile role
        profile = user.profile
        profile.role = role
        profile.save()

        GamificationStats.objects.create(user=user)
        NotificationPreference.objects.create(user=user)

        UserActivity.objects.create(
            user=user,
            activity_type='login',
            description="New account created"
        )

        messages.success(request, "Registration successful. Please log in.")
        return redirect('login')

    return render(request, "accounts/register.html")


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if not user:
            messages.error(request, "Invalid username or password.")
            return redirect('login')

        login(request, user)
        UserActivity.objects.create(user=user, activity_type='login')
        return redirect("dashboard")

    return render(request, "accounts/login.html")


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect("login")


# =========================================================
# DASHBOARD
# =========================================================

@login_required
def dashboard(request):
    user = request.user
    profile = user.profile
    stats = user.gamification_stats
    activities = user.activities.all()[:10]

    # ------------------
    # TEACHER DASHBOARD
    # ------------------
    if profile.role == "teacher":
        classrooms = user.classrooms_taught.all()

        total_students = sum(c.members.count() for c in classrooms)

        from apps.quizes.models import Quiz
        quizzes = Quiz.objects.filter(teacher=user)

        from apps.classroom.models import AnnouncementBoard
        announcements = sum(c.announcements.count() for c in classrooms)

        return render(request, "teacher/dashboard.html", {
            "profile": profile,
            "stats": stats,
            "activities": activities,
            "classrooms": classrooms,
            "total_students": total_students,
            "quizzes": quizzes,
            "announcements": announcements,
        })

    # ------------------
    # STUDENT DASHBOARD
    # ------------------
    classrooms = user.enrolled_classrooms.all()
    return render(request, "student/dashboard.html", {
        "profile": profile,
        "stats": stats,
        "activities": activities,
        "classrooms": classrooms,
    })


# =========================================================
# PROFILE
# =========================================================

@login_required
def profile_view(request):
    return render(request, "accounts/profile.html", {
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

        profile.bio = request.POST.get("bio", profile.bio)
        profile.phone = request.POST.get("phone", profile.phone)
        profile.school_name = request.POST.get("school_name", profile.school_name)
        profile.class_name = request.POST.get("class_name", profile.class_name)

        if "profile_picture" in request.FILES:
            profile.profile_picture = request.FILES["profile_picture"]

        profile.save()

        messages.success(request, "Profile updated successfully.")
        return redirect("profile_view")

    return render(request, "accounts/edit_profile.html", {"profile": profile})


# =========================================================
# STUDENT PAGES
# =========================================================

@login_required
def student_dashboard(request):
    return redirect("dashboard")


@login_required
def student_attendance(request):
    return render(request, "student/attendance.html")


@login_required
def student_feedback(request):
    return render(request, "student/feedback.html", {
        "recent_feedback": []
    })


# =========================================================
# LEADERBOARD + BADGES + STATS
# =========================================================

def leaderboard(request):
    top_users = (
        User.objects.filter(gamification_stats__isnull=False)
        .annotate(total_points=Sum("gamification_stats__points"))
        .order_by("-total_points")[:100]
    )

    rank = None
    if request.user.is_authenticated:
        my_points = request.user.gamification_stats.points
        rank = User.objects.filter(
            gamification_stats__points__gt=my_points
        ).count() + 1

    return render(request, "accounts/leaderboard.html", {
        "top_users": top_users,
        "user_rank": rank,
    })


@login_required
def badges_view(request):
    stats = request.user.gamification_stats
    return render(request, "accounts/badges.html", {
        "stats": stats,
        "all_badges": dict(GamificationStats.BADGE_CHOICES),
        "user_badges": stats.badges,
    })


@login_required
def user_stats(request):
    user = request.user
    activities = user.activities

    return render(request, "accounts/user_stats.html", {
        "profile": user.profile,
        "stats": user.gamification_stats,
        "total_activities": activities.count(),
        "login_count": activities.filter(activity_type="login").count(),
        "quiz_attempts": activities.filter(activity_type="quiz_attempt").count(),
        "discussion_posts": activities.filter(activity_type="discussion_post").count(),
    })


# =========================================================
# NOTIFICATION SETTINGS
# =========================================================

@login_required
def notification_preferences(request):
    pref = request.user.notification_preference

    if request.method == "POST":
        pref.quiz_reminders = "quiz_reminders" in request.POST
        pref.class_updates = "class_updates" in request.POST
        pref.discussion_replies = "discussion_replies" in request.POST
        pref.achievement_notifications = "achievement_notifications" in request.POST
        pref.email_notifications = "email_notifications" in request.POST
        pref.save()

        messages.success(request, "Preferences updated.")
        return redirect("notification_preferences")

    return render(request, "accounts/notification_preferences.html", {"preferences": pref})


# =========================================================
# SEARCH + API
# =========================================================

def search_users(request):
    query = request.GET.get("q", "")

    users = (
        User.objects.filter(
            Q(username__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query)
        )[:20]
        if len(query) >= 2 else []
    )

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        data = [{
            "id": u.id,
            "username": u.username,
            "full_name": u.get_full_name(),
            "email": u.email,
            "role": u.profile.role,
        } for u in users]

        return JsonResponse({"users": data})

    return render(request, "accounts/search_users.html", {"users": users, "query": query})


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
