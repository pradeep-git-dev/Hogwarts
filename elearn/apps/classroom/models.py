from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Classroom(models.Model):
    """Model for creating and managing classrooms"""
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('archived', 'Archived'),
        ('inactive', 'Inactive'),
    )
    
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='classrooms_taught')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    code = models.CharField(max_length=10, unique=True)
    subject = models.CharField(max_length=100)
    grade_level = models.CharField(max_length=50, blank=True, null=True)
    room_number = models.CharField(max_length=50, blank=True, null=True)
    schedule = models.TextField(help_text="Class schedule/timing", blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    max_students = models.IntegerField(default=50)
    banner_image = models.ImageField(upload_to='classrooms/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Classroom"
        verbose_name_plural = "Classrooms"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['teacher', '-created_at']),
            models.Index(fields=['code']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def get_student_count(self):
        """Get total number of enrolled students"""
        return self.members.filter(role='student').count()
    
    def is_full(self):
        """Check if classroom has reached max capacity"""
        return self.get_student_count() >= self.max_students


class ClassMember(models.Model):
    """Model for classroom membership"""
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('assistant', 'Teacher Assistant'),
    )
    
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='members')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrolled_classrooms')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    enrollment_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=(('active', 'Active'), ('suspended', 'Suspended'), ('dropped', 'Dropped')),
        default='active'
    )
    
    class Meta:
        unique_together = ('classroom', 'student')
        verbose_name = "Class Member"
        verbose_name_plural = "Class Members"
    
    def __str__(self):
        return f"{self.student.username} in {self.classroom.name}"


class Attendance(models.Model):
    """Model for tracking classroom attendance"""
    STATUS_CHOICES = (
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused Absence'),
    )
    
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='attendance_records')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    remarks = models.TextField(blank=True, null=True)
    recorded_at = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='attendance_recorded')
    
    class Meta:
        unique_together = ('classroom', 'student', 'date')
        verbose_name = "Attendance"
        verbose_name_plural = "Attendance Records"
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.student.username} - {self.classroom.name} ({self.date})"


class AnnouncementBoard(models.Model):
    """Model for classroom announcements"""
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='announcements')
    teacher = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content = models.TextField()
    is_pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Announcement Board"
        verbose_name_plural = "Announcement Boards"
        ordering = ['-is_pinned', '-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.classroom.name}"


class Discussion(models.Model):
    """Model for classroom discussion threads"""
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='discussions')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content = models.TextField()
    topic = models.CharField(
        max_length=50,
        choices=(
            ('general', 'General'),
            ('doubt', 'Doubt'),
            ('project', 'Project'),
            ('resource', 'Resource'),
            ('peer_learning', 'Peer Learning'),
        ),
        default='general'
    )
    is_pinned = models.BooleanField(default=False)
    is_closed = models.BooleanField(default=False)
    views_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Discussion"
        verbose_name_plural = "Discussions"
        ordering = ['-is_pinned', '-created_at']
        indexes = [
            models.Index(fields=['classroom', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.classroom.name}"
    
    def get_reply_count(self):
        """Get total number of replies"""
        return self.replies.count()


class DiscussionReply(models.Model):
    """Model for discussion replies"""
    discussion = models.ForeignKey(Discussion, on_delete=models.CASCADE, related_name='replies')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    is_answer = models.BooleanField(default=False)  # Mark helpful replies
    likes = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Discussion Reply"
        verbose_name_plural = "Discussion Replies"
        ordering = ['-is_answer', '-created_at']
    
    def __str__(self):
        return f"Reply by {self.author.username} on {self.discussion.title}"


class LearningResource(models.Model):
    """Model for storing learning resources"""
    RESOURCE_TYPE_CHOICES = (
        ('document', 'Document'),
        ('video', 'Video'),
        ('link', 'External Link'),
        ('presentation', 'Presentation'),
        ('code', 'Code/File'),
    )
    
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='resources')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    resource_type = models.CharField(max_length=50, choices=RESOURCE_TYPE_CHOICES)
    file = models.FileField(upload_to='resources/', blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    downloads = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = "Learning Resource"
        verbose_name_plural = "Learning Resources"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.classroom.name}"


class ProgressTracking(models.Model):
    """Model for tracking student progress"""
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress_records')
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    quiz_attempts = models.IntegerField(default=0)
    quiz_passed = models.IntegerField(default=0)
    average_quiz_score = models.FloatField(default=0.0)
    discussion_posts = models.IntegerField(default=0)
    attendance_count = models.IntegerField(default=0)
    total_attendance = models.IntegerField(default=0)
    completion_percentage = models.FloatField(default=0.0)
    last_active = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('student', 'classroom')
        verbose_name = "Progress Tracking"
        verbose_name_plural = "Progress Tracking"
    
    def __str__(self):
        return f"{self.student.username} - {self.classroom.name}"
    
    def get_attendance_percentage(self):
        """Calculate attendance percentage"""
        if self.total_attendance == 0:
            return 0.0
        return (self.attendance_count / self.total_attendance) * 100
