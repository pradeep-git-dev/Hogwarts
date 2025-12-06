from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone


class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('admin', 'Administrator'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    school_name = models.CharField(max_length=255, blank=True, null=True)
    class_name = models.CharField(max_length=50, blank=True, null=True)
    is_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} ({self.role})"

    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username

    def total_points(self):
        return self.user.gamification_stats.points


class GamificationStats(models.Model):
    BADGE_CHOICES = (
        ('first_quiz', 'First Quiz Taken'),
        ('perfect_score', 'Perfect Score'),
        ('participation', 'Active Participant'),
        ('discussion', 'Discussion Expert'),
        ('attendance', 'Perfect Attendance'),
        ('learner', 'Fast Learner'),
        ('top_performer', 'Top Performer'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='gamification_stats')
    points = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    badges = models.JSONField(default=list)

    level = models.IntegerField(default=1)
    total_quizzes_attempted = models.IntegerField(default=0)
    total_quizzes_passed = models.IntegerField(default=0)
    total_participation_points = models.IntegerField(default=0)
    attendance_rate = models.FloatField(default=0.0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.points} pts"

    # GAMIFICATION ENGINE
    def add_points(self, amount: int, reason=""):
        self.points += amount
        self.level = max(1, (self.points // 1000) + 1)
        self.save()

    def add_badge(self, badge: str):
        if badge not in self.badges:
            self.badges.append(badge)
            self.save()

    def recalc_attendance(self):
        from apps.classroom.models import Attendance

        total = Attendance.objects.filter(student=self.user).count()
        if total == 0:
            self.attendance_rate = 0
        else:
            present = Attendance.objects.filter(student=self.user, status='present').count()
            self.attendance_rate = round((present / total) * 100, 2)
        self.save()


class NotificationPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preference')

    quiz_reminders = models.BooleanField(default=True)
    class_updates = models.BooleanField(default=True)
    discussion_replies = models.BooleanField(default=True)
    achievement_notifications = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=True)

    def __str__(self):
        return f"Notification Preferences ({self.user.username})"


class UserActivity(models.Model):
    ACTIVITY_TYPES = (
        ('login', 'Login'),
        ('quiz_attempt', 'Quiz Attempt'),
        ('quiz_submission', 'Quiz Submission'),
        ('discussion_post', 'Discussion Post'),
        ('attendance', 'Attendance'),
        ('resource_view', 'Resource View'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPES)
    description = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [models.Index(fields=['user', '-timestamp'])]

    def __str__(self):
        return f"{self.user.username} - {self.activity_type}"
