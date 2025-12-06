from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile, GamificationStats, NotificationPreference


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile when User is created"""
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def create_gamification_stats(sender, instance, created, **kwargs):
    """Create GamificationStats when User is created"""
    if created:
        GamificationStats.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def create_notification_preference(sender, instance, created, **kwargs):
    """Create NotificationPreference when User is created"""
    if created:
        NotificationPreference.objects.get_or_create(user=instance)
