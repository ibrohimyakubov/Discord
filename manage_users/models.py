from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from backend.discord_bot.models import SoundClip, Guild
from backend.manage_content.models import Collection


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    playlists = models.ManyToManyField(Collection)
    joinclips = models.ManyToManyField(SoundClip)

    # caches the current guilds of a user for a login - use a real caching mechanism if deployed at large scale
    guilds = models.ManyToManyField(Guild)

    class Meta:
        ordering = ['user']

    def __str__(self):
        return str(self.user)


# Can this be put into one method?
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
