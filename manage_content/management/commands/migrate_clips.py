import os
import sys
import config
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from mutagen.mp3 import MP3
from backend.discord_bot.models import *


class Command(BaseCommand):
    help = "This command will register a folder memes into the database(without tags and with the first owner user as the creator)"

    def add_arguments(self, parser):
        parser.add_argument('path', type=str)

    def handle(self, *args, **options):
        SoundClip.objects.all().delete()
        for filename in os.listdir(sys.path):
            print(filename)

            file_ending = filename.split('.')[1]
            if file_ending != "mp3":
                continue
            filepath = sys.path + "/" + filename
            soundclip_name = filename.split('.')[0]
            try:
                length = MP3(filepath).info.length
            except:
                length = 0.0
            creator = None
            if config.bot_owners:
                user_query = User.objects.filter(username=config.bot_owners[0])
                if user_query.exists():
                    creator = user_query[0]

            SoundClip.objects.create(name=soundclip_name,
                                     path=filepath,
                                     duration=length,
                                     creator=creator)
        print("Succesfully migrated" + str(len(SoundClip.objects.all())) + "soundclips.")