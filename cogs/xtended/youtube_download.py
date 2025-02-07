import discord
from discord.ext import commands
import asyncio
from other.utils.utils import Utils as util
import os
import sqlite3
import datetime
import functools
import typing

try:
    import yt_dlp
    youtube_download_enabled = True
except:
    print("Not importing YouTube Download functionality.")
    youtube_download_enabled = False



class YT_Check():
    def is_youtubedownload_enabled(*ctx):
        if youtube_download_enabled:
            return True
        else:
            raise commands.CheckFailure("This functionality is turned off.")



class YouTube_Download(commands.Cog):
    def __init__(self, bot: commands.bot) -> None:
        self.bot = bot
        self.prefix = os.getenv("prefix")



    def to_thread(func: typing.Callable) -> typing.Coroutine:
        """wrapper for blocking functions"""
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await asyncio.to_thread(func, *args, **kwargs)
        return wrapper



    @to_thread
    def downloadYouTubeVideo(self, videourl_list, ydl_opts, filename):
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(videourl_list[0], download=False)
            try:
                title = ydl.sanitize_info(info)['title']
            except Exception as e:
                print("Error:", e)
                title = "<video>"
            ydl.download(videourl_list)

        return title

        

    @commands.command(name='ytdl', aliases = ['youtubedownload'])
    @commands.check(YT_Check.is_youtubedownload_enabled)
    #@commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _youtube_download(self, ctx: commands.Context, *args):
        """㊙️ Downloads YouTube video
        """

        if len(args) == 0:
            await ctx.send("Command needs youtube url as argument.")
            return

        emoji = util.emoji("load")

        try:
            await ctx.message.add_reaction(emoji)
        except:
            pass

        try:
            userid   = ctx.message.author.id
            now      = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())

            videourl_list = []

            for arg in args:
                url = arg.replace("<","").replace(">","").replace(",","").strip()
                if url == "":
                    continue

                videourl_list.append(url)
                break # download only one file

            if len(videourl_list) == 0:
                await ctx.send("Arguments must be URLs.")
                return

            filename = f'ytdl_{userid}_{now}.mp4'

            ydl_opts = {
                'format': 'mp4',
                'paths': {'home': './temp', 'temp': './temp'},
                'outtmpl': {'default': filename}
            }

            title = await self.downloadYouTubeVideo(videourl_list, ydl_opts, filename)

            try:
                title_clean = util.cleantext(title)
                caption = f"Downloaded `{title_clean}`:"
                print("sending file...")
                await ctx.reply(caption[:2000], file=discord.File(rf"temp/{filename}"))
            except Exception as e:
                message = f"Error while trying to send YouTube video:\n{e}"
                await ctx.send(message[:2000])

            try:
                os.rmdir("temp/temp")
            except:
                pass
            os.remove(f"temp/{filename}")

        except Exception as e:
            message = f"Error while trying to download YouTube video:\n{e}"
            await ctx.send(message[:2000])

        try:
            mdmbot_id = int(self.bot.application_id)
            mdmbot = ctx.guild.get_member(mdmbot_id)
            await ctx.message.remove_reaction(emoji, mdmbot)
        except Exception as e:
            print("Error:", e)
    
    @_youtube_download.error
    async def youtube_download_error(self, ctx, error):
        await util.error_handling(ctx, error)


async def setup(bot: commands.bot) -> None:
    await bot.add_cog(
        YouTube_Download(bot),
        guilds = [discord.Object(id = int(os.getenv("guild_id")))])