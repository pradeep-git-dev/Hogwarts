from django.contrib import admin
from .models import UserProfile, GamificationStats, NotificationPreference, UserActivity


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'is_verified', 'school_name', 'created_at')
    list_filter = ('role', 'is_verified', 'created_at')
    search_fields = ('user__username', 'user__email', 'school_name')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'role', 'is_verified')
        }),
        ('Personal Details', {
            'fields': ('bio', 'phone', 'date_of_birth', 'profile_picture')
        }),
        ('School Information', {
            'fields': ('school_name', 'class_name')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(GamificationStats)
class GamificationStatsAdmin(admin.ModelAdmin):
    list_display = ('user', 'points', 'level', 'attendance_rate', 'total_quizzes_passed')
    list_filter = ('level', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'points')
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Gamification Stats', {
            'fields': ('points', 'level', 'badges')
        }),
        ('Quiz Statistics', {
            'fields': ('total_quizzes_attempted', 'total_quizzes_passed')
        }),
        ('Participation', {
            'fields': ('total_participation_points', 'attendance_rate')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz_reminders', 'class_updates', 'discussion_replies', 'email_notifications')
    list_filter = ('quiz_reminders', 'class_updates', 'email_notifications')
    search_fields = ('user__username', 'user__email')


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'timestamp')
    list_filter = ('activity_type', 'timestamp')
    search_fields = ('user__username', 'description')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'
