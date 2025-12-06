from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile, GamificationStats, NotificationPreference


@receiver(post_save, sender=User)
def create_related(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
        GamificationStats.objects.create(user=instance)
        NotificationPreference.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_related(sender, instance, **kwargs):
    if hasattr(instance, "profile"):
        instance.profile.save()
    if hasattr(instance, "gamification_stats"):
        instance.gamification_stats.save()
    if hasattr(instance, "notification_preference"):
        instance.notification_preference.save()
