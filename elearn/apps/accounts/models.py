from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone

class UserProfile(models.Model):
    """Extended user profile with role and additional info"""
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
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.get_role_display()}"
    
    def get_total_points(self):
        """Calculate total points from all gamification stats"""
        return self.gamification_stats.aggregate(
            total=models.Sum('points')
        )['total'] or 0


class GamificationStats(models.Model):
    """Track points, badges, and achievements for each user"""
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
    badges = models.JSONField(default=list, help_text="List of earned badges")
    level = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    total_quizzes_attempted = models.IntegerField(default=0)
    total_quizzes_passed = models.IntegerField(default=0)
    total_participation_points = models.IntegerField(default=0)
    attendance_rate = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Gamification Stats"
        verbose_name_plural = "Gamification Stats"
    
    def __str__(self):
        return f"{self.user.username} - {self.points} Points"
    
    def add_points(self, amount, reason=""):
        """Add points and update level"""
        self.points += amount
        # Level up every 1000 points
        new_level = (self.points // 1000) + 1
        if new_level > self.level:
            self.level = new_level
        self.save()
    
    def add_badge(self, badge):
        """Add a badge to user's collection"""
        if badge not in self.badges:
            self.badges.append(badge)
            self.save()
    
    def calculate_attendance_rate(self):
        """Calculate attendance rate based on classroom attendance"""
        from apps.classroom.models import Attendance
        attendance_records = Attendance.objects.filter(student=self.user)
        if attendance_records.exists():
            attended = attendance_records.filter(status='present').count()
            total = attendance_records.count()
            self.attendance_rate = (attended / total) * 100
            self.save()
        return self.attendance_rate


class NotificationPreference(models.Model):
    """User notification preferences"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preference')
    quiz_reminders = models.BooleanField(default=True)
    class_updates = models.BooleanField(default=True)
    discussion_replies = models.BooleanField(default=True)
    achievement_notifications = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Notification Preference - {self.user.username}"


class UserActivity(models.Model):
    """Track user activities for analytics"""
    ACTIVITY_TYPE_CHOICES = (
        ('login', 'Login'),
        ('quiz_attempt', 'Quiz Attempt'),
        ('discussion_post', 'Discussion Post'),
        ('quiz_submission', 'Quiz Submission'),
        ('attendance', 'Attendance'),
        ('resource_view', 'Resource View'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPE_CHOICES)
    description = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "User Activity"
        verbose_name_plural = "User Activities"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_activity_type_display()}"
