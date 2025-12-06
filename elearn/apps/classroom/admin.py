from django.contrib import admin
from .models import (
    Classroom, ClassMember, Attendance, Discussion, DiscussionReply,
    AnnouncementBoard, LearningResource, ProgressTracking
)


@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ('name', 'teacher', 'code', 'subject', 'status', 'created_at')
    list_filter = ('status', 'subject', 'created_at')
    search_fields = ('name', 'code', 'teacher__username', 'subject')
    readonly_fields = ('code', 'created_at', 'updated_at')
    fieldsets = (
        ('Classroom Information', {
            'fields': ('name', 'code', 'teacher', 'status')
        }),
        ('Details', {
            'fields': ('description', 'subject', 'grade_level', 'room_number', 'schedule')
        }),
        ('Settings', {
            'fields': ('max_students', 'banner_image')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ClassMember)
class ClassMemberAdmin(admin.ModelAdmin):
    list_display = ('classroom', 'student', 'role', 'status', 'enrollment_date')
    list_filter = ('role', 'status', 'enrollment_date')
    search_fields = ('classroom__name', 'student__username', 'student__email')
    readonly_fields = ('enrollment_date',)


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('classroom', 'student', 'date', 'status', 'recorded_by')
    list_filter = ('status', 'date', 'classroom')
    search_fields = ('classroom__name', 'student__username')
    date_hierarchy = 'date'
    readonly_fields = ('recorded_at',)


@admin.register(AnnouncementBoard)
class AnnouncementBoardAdmin(admin.ModelAdmin):
    list_display = ('title', 'classroom', 'teacher', 'is_pinned', 'created_at')
    list_filter = ('is_pinned', 'created_at', 'classroom')
    search_fields = ('title', 'content', 'classroom__name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Discussion)
class DiscussionAdmin(admin.ModelAdmin):
    list_display = ('title', 'classroom', 'author', 'topic', 'views_count', 'created_at')
    list_filter = ('topic', 'is_pinned', 'is_closed', 'created_at', 'classroom')
    search_fields = ('title', 'content', 'classroom__name', 'author__username')
    readonly_fields = ('views_count', 'created_at', 'updated_at')


@admin.register(DiscussionReply)
class DiscussionReplyAdmin(admin.ModelAdmin):
    list_display = ('discussion', 'author', 'is_answer', 'likes', 'created_at')
    list_filter = ('is_answer', 'created_at')
    search_fields = ('content', 'discussion__title', 'author__username')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(LearningResource)
class LearningResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'classroom', 'uploaded_by', 'resource_type', 'downloads', 'created_at')
    list_filter = ('resource_type', 'created_at', 'classroom')
    search_fields = ('title', 'description', 'classroom__name')
    readonly_fields = ('created_at', 'downloads')


@admin.register(ProgressTracking)
class ProgressTrackingAdmin(admin.ModelAdmin):
    list_display = ('student', 'classroom', 'completion_percentage', 'average_quiz_score', 'last_active')
    list_filter = ('classroom', 'last_active')
    search_fields = ('student__username', 'classroom__name')
    readonly_fields = ('last_active',)
