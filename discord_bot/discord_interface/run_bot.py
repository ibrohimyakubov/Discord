import discord
from discord.ext import commands
from backend.discord_bot.discord_interface.config.config import *
from backend.discord_bot.discord_interface.audiocontroller import AudioController
from backend.discord_bot.discord_interface.utils import guild_to_auidocontroller, get_guild
from backend.discord_bot.discord_interface.audioelements.localclip import LocalClipHelper
from backend.discord_bot.models import *
from discord.ext.commands import CommandNotFound


initial_extensions = ['discord_bot.discord_interface.commands.music','discord_bot.discord_interface.commands.general']
bot = commands.Bot(command_prefix="!",pm_help=True)

def start_bot_routine(loop):
    for extension in initial_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            print(e)

    loop.run_until_complete(bot.start(Token))

@bot.event
async def on_ready():
    print(STARTUP_MESSAGE)
    await bot.change_presence(status=discord.Status.online, activity=discord.Game(name="Music, type!help"))
    for guild in bot.guilds:
        print(guild.name)
        await guild.me.edit(nick=DEFAULT_NICKNAME)

        if guild.afk_channel == guild.voice_channels[0]:
            voice_channel = guild.voice_channels[1]
        else:
            voice_channel = guild.voice_channels[0]
        guild_query = Guild.objects.filter(id=str(guild.id))
        if not guild_query.exists():
            guild = Guild(id=str(guild.id),name=guild.name, connected_channel=str(voice_channel.id))
            guild.save()
        else:
            last_channel = bot.get_channel(int(guild_query[0].connected_channel))
            if last_channel and guild.afk_channel != last_channel:
                voice_channel = last_channel
                print(last_channel)
            else:
                db_guild = guild_query[0]
                db_guild.connected_channel = str(voice_channel.id)
                db_guild.save()
        guild_to_auidocontroller[guild] = AudioController(bot,guild,DEFAULT_VOLUME)
        try:
            await guild_to_auidocontroller[guild].register_voice_channel(voice_channel)
        except:
            print("could not join"+guild.name)
    print(STARTUP_COMPLETE_MESSAGE)

@bot.event
async def on_guild_join(guild):
    print(guild.name)
    guild_to_auidocontroller[guild] = AudioController(bot,guild,DEFAULT_VOLUME)
    try:
        if guild.afk_channel == guild.voice_channels[0]:
            voice_channel = guild.voice_channels[1]
        else:
            voice_channel = guild.voice_channels[0]
        await guild_to_auidocontroller[guild].register_voice_channel(voice_channel)
        guild = Guild(id=str(guild.id),name=guild.name, connected_channel=str(voice_channel.id))
        guild.save()
    except:
        print("Could not join"+guild.name)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error,CommandNotFound):
        if ctx.message.content.startswith('!'):
            guild = get_guild(bot,ctx.message)
            if guild is not None:
                await LocalClipHelper.add_soundclip_from_name(
                    guild_to_auidocontroller[guild],  ctx.message.content[1:],
                    )
                return
        raise error

@bot.event
async def on_voice_state_update(member,before,after):
    if member == bot.user and before.channel!=after.channel and after.channel:
        guild_query = Guild.objects.filter(id=str(member.guild.id))
        if guild_query.exists():
            db_guild = guild_query[0]
            db_guild.connected_channel = str(after.channel.id)
            db_guild.save()


