import os
import datetime
import discord
from discord.ext import commands
import re
from datetime import datetime

class BackUp(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def is_valid_server(ctx):
        server = ctx.message.guild
        if server is None:
            raise commands.CheckFailure(f'Command does not work in DMs.')
            return False
        else:
            valid_servers = [413011798552477716]
            guild_id = server.id
            print(guild_id)
            if guild_id in valid_servers:
                return True
            else:
                raise commands.CheckFailure(f'Command does only work on specific servers.')
                return False


    @commands.command(name='backup', aliases = ["backups"])
    @commands.has_permissions(manage_guild=True)
    @commands.check(is_valid_server)
    async def _backup(self, ctx, *args):
        """*data backup

        Sends internal data of bot into #bot-spam channel for backup purposes.
        Arguments that can be used are: backlogs, pingterests, settings, all
        """    
        if len(args) == 1:

            channel = await self.bot.fetch_channel(416384984597790750)

            #timenow = datetime.now()
            #year_now = timenow.strftime("%Y")
            #month_now = timenow.strftime("%m")
            #day_now = timenow.strftime("%d")
            #hour_now = timenow.strftime("%-H")
            #minute_now = timenow.strftime("%-M")
            #second_now = timenow.strftime("%-S")
            #timestring = f"{year_now}.{month_now}.{day_now}, {hour_now}:{minute_now}:{second_now} CET"

            utc_time_stamp = int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds())
            timestring = f"<t:{utc_time_stamp}:F>"

            print(f"backup: {timestring}")

            if args[0].lower() in ["all"]:
                my_files = [
                    discord.File('cogs/backlog/memobacklog.db'),
                    discord.File('cogs/pingterest/pingterest.db'),
                    discord.File('cogs/settings/default_settings.txt'),
                ]
                await channel.send(f"Backup of mdm bot data\n{timestring}", files=my_files)

            elif args[0].lower() in ["backlog", "backlogs", "memo", "memos"]:
                #await channel.send(file=discord.File(r'/home/pi/bots/MDM_Bot/cogs/backlog/memobacklog.db'))
                await channel.send(f"Backup of backlog data\n{timestring}", file=discord.File('cogs/backlog/memobacklog.db'))

            elif args[0].lower() in ["pingterest", "pingterests", "pingableinterest", "pingableinterests"]:
                await channel.send(f"Backup of pingterest data\n{timestring}", file=discord.File('cogs/pingterest/pingterest.db'))

            elif args[0].lower() in ["setting", "settings"]:
                await channel.send(f"Backup of mdm bot settings\n{timestring}", file=discord.File('cogs/settings/default_settings.txt'))

            else:
                await ctx.send(f'Argument seems to be invalid <:penguinconfuse:1017439518116298765>')

        elif len(args) == 0:
            await ctx.send(f'Command needs an argument. <:pikathink:956603401028911124>')
        else:
            await ctx.send(f'Command only takes one argument.\nUse `-help backup` for more information.')
    @_backup.error
    async def backup_error(ctx, error, *args):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f'Sorry, you do not have permissions to do this!')
        elif isinstance(error, commands.BadArgument):
            await ctx.send('Something went wrong... something something bad argument <:seenoslowpoke:975062347871842324>')
        else:
            await ctx.send(f'Some error occurred <:penguinshy:1017439941074100344>')



async def setup(bot: commands.bot) -> None:
    await bot.add_cog(
        BackUp(bot),
        guilds = [discord.Object(id = 413011798552477716)])