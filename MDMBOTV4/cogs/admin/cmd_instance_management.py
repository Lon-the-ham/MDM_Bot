import discord
import os

from   discord.ext                        import commands
from   cogs.utils.utl_checks              import ComCheckUtils           as utl_c
from   cogs.admin.fnc_instance_management import AdministrationFunctions as fnc_adm

# COG for management of different bot instances
# relevant if this application is hosted on multiple bot accounts for redundancy
# otherwise probably only the backup function is important



class Administration_of_Bot_Instance(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot



    @commands.command(name='status', aliases = ["instancestatus", "botstatus"])
    #@commands.has_permissions(manage_guild=True)
    #@commands.check(util.is_main_server)
    async def _botstatus(self, ctx, *, args=None):
        """🔒 Shows bot instance's status

        Shows for each instance whether the bot is active or inactive, as well as its current version.
        """    
        await fnc_adm.botstatus(self.bot, ctx)
    @_botstatus.error
    async def botstatus_error(self, ctx, error):
        await utl_c.error_handling(ctx, error)


async def setup(bot: commands.bot) -> None:
    await bot.add_cog(
        Administration_of_Bot_Instance(bot),
        guilds = [discord.Object(id = int(os.getenv("guild_id")))])