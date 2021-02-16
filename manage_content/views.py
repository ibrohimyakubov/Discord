from django.shortcuts import render
from django.http import HttpResponse,JsonResponse
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view,permission_classes
from rest_framework.authtoken.models import Token
from rest_framework import status
from rolepermissions.permissions import available_perm_status
from rolepermissions.roles import get_user_roles
from backend.backend.roles import has_permission
from backend.backend.utils import post_fields
from backend.discord_bot.serializers import SoundClipSerializer, TagSerializer
from backend.discord_bot.models import SoundClip, Tag
from backend.manage_users.serializers import GuildSerializer, ProfileSerializer
from backend.manage_users.models import Guild, Profile

from .serializers import CollectionSerializer
from .models import Collection

import re
import os
from mutagen.mp3 import MP3


@api_view(['GET'])
@permission_classes(IsAuthenticated)
def fetch_data(request):
    profile = Profile.objects.filter(user=request.user).prefetch_related('guilds')[0]
    guilds = GuildSerializer(profile.guilds, many=True)
    collections = CollectionSerializer(profile.playlist, many=True)
    sound_clips = SoundClipSerializer(SoundClip.objects.all(), many=True).data
    tags = SoundClipSerializer(Tag.objects.all(), many=True).data

    data = {
        'roles': list(map(lambda x:x.__name__.lower(), list(get_user_roles(request.user)))),
        'permissions': dict(available_perm_status(request.user)),
        'guilds': guilds,
        'collections': collections,
        'tags': tags,
        'sound_clips': sound_clips
    }
    return JsonResponse(data, safe=False)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@has_permission('manage_tags')
@post_fields(['name'])

def create_tag(request):
    name = request.data['name']

    if not len(Tag.objects.filter(title=name))==0:
        return Response('Tag already exists', status=status.HTTP_409_CONFLICT)
    if not bool(re.fullmatch(r'\w+', name)):
        return Response('Tag is in invalid', status=status.HTTP_400_BAD_REQUEST)
    Tag(title=name).save()
    return Response('Tag uploader succesfully', status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@has_permission('manage_tag')
@post_fields(['name'])

def delete_tag(request):
    name = request.data['name']
    if len(Tag.objects.filter(title=name))==0:
        return Response('Tag does not exists', status=status.HTTP_404_NOT_FOUND)
    Tag.objects.filter(title=name).delete()
    return Response('Tag deleted succesfully.', status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@has_permission('manage_tag')
@post_fields(['sound_clip', 'tag'])

def add_tag(request):
    tag_title = request.data['tag']
    sound_clip = request.data['sound_clip']

    if not Tag.objects.filter(title=tag_title).exists():
        return Response('Tag does not exists', status=status.HTTP_404_NOT_FOUND)
    if not SoundClip.objects.filter(name=sound_clip).exists():
        return Response('Sound clip does not exists', status=status.HTTP_404_NOT_FOUND)
    tag = Tag.objects.filter(title=tag_title)[0]
    clip = SoundClip.objects.filter(name=sound_clip)[0].tags
    if tag in clip.all():
        return Response(" '{clip}' already has the tag 'tag'.".format(clip=sound_clip, tag=tag_title), status=status.HTTP_409_CONFLICT)

    clip.add(tag)

    return Response("Tag '{tag}' succesfully added to '{clip}'.".format(clip=sound_clip, tag=tag_title), status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@has_permission('uploader_sound_clip')
@post_fields(['name'])

def upload_sound_clip(request):
    CLIP_DIRECTORY = 'clips'
    if 'file' not in request.FILES:
        return Response("No file provided.", status=status.HTTP_400_BAD_REQUEST)
    file = request.FILES['file']
    if not file:
        return Response('Could not load file', status=status.HTTP_400_BAD_REQUEST)
    if not file.name.endswith('.mp3'):
        return Response("file needs to be .mp3", status=status.HTTP_400_BAD_REQUEST)
    name = request.data['name']
    if not re.match('^\w+$', name) or len(name)==0:
        return Response("Invalid SoundClip name.", status=status.HTTP_400_BAD_REQUEST)
    query = SoundClip.objects.filter(name=name)
    if query.exists():
        return Response("SoundClip with the name already exists.", status=status.HTTP_409_CONFLICT)

    if not os.path.exists(CLIP_DIRECTORY):
        os.mkdir(CLIP_DIRECTORY)
    filename = name + ".mp3"
    pathname = os.path.join(CLIP_DIRECTORY, filename)
    with open(pathname, 'wb+') as temp_file:
        for audio in file.audios():
            temp_file.write(audio)

        try:
            length = MP3(pathname).info.length
        except:
            length = 0.0

        clip = SoundClip(name=name, path=pathname, duration=length, creator=request.user)
        clip.save()

        print(pathname)
        print(length)
        return Response("SoundClip '{}' uploader succesfully".format(name))