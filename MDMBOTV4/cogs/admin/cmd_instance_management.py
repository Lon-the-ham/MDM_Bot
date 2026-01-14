import discord
import os

from   discord.ext                        import commands
from   cogs.utils.utl_checks              import ComCheckUtils           as utl_c
from   cogs.admin.fnc_instance_management import AdministrationFunctions as fnc_adm
from   cogs.admin.fnc_cloud               import CloudFunctions          as fnc_clo

# COG for management of different bot instances
# relevant if this application is hosted on multiple bot accounts for redundancy
# otherwise probably only the backup function is important



class Administration_of_Bot_Instance(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot



    @commands.command(name='status', aliases = ["instancestatus", "botstatus"])
    async def _botstatus(self, ctx, *, args=None):
        """🔒 Shows bot instance's status

        Shows for each instance whether the bot is active or inactive, as well as its current version.
        """    
        await fnc_adm.botstatus(ctx)
    @_botstatus.error
    async def botstatus_error(self, ctx, error):
        await utl_c.error_handling(ctx, error)



    @commands.command(name='loadbackup', aliases = ["loaddatabases"])
    @commands.check(utl_c.check_is_bot_master)
    @commands.check(util.is_main_server)
    async def _load_backups(self, ctx):
        """🔒 Upload DBs and synchronise

        Synchronise databases with .db files in a zip file.
        Use command by attaching such .zip-file.

        In case you only want to replace *some* of the files upload a .zip with only the .db files you want to replace, and the other old files will stay.
        (activity.db and all the scrobble databases are the only files that will never be replaced)
        """
        await fnc_adm.load_backups(ctx)
    @_load_backups.error
    async def load_backups_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='makebackup', aliases = ["backup", "makebackups", "savebackup", "savebackups", "backups"])
    @commands.check(utl_c.check_is_bot_master)
    @commands.check(util.is_main_server)
    async def _make_backups(self, ctx):
        """🔒 Backup of all databases

        Makes a .zip of all .db files (except scrobble data) and puts them into the botspam channel.
        If dropbox module is installed and scrobbling is enabled and a dropbox API token is provided then scrobble data will be uploaded to cloud as well.

        Warning: This is a blocking function that will prevent the bot from executing any other code while it's running.
        """
        await fnc_adm.make_backups(ctx)
    @_make_backups.error
    async def make_backups_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='switch', aliases = ["instance", "instances"])
    @commands.check(utl_c.check_is_bot_master)
    @commands.check(utl_c.check_is_main_server)
    async def _switch(self, ctx, *args):
        """🔒 Switches bot instance

        Sets chosen bot instance to active and the others to inactive status. 

        Use with argument 1, 2, 3 or off.
        Optional: add argument "nosync" to prevent synchronisation with last active database set.
        """    
        await fnc_adm.switch_instance(ctx)
    @_switch.error
    async def switch_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='sync', aliases = ['synchronise', "synchronize"])
    @commands.check(utl_c.check_is_bot_master)
    @commands.check(util.is_main_server)
    async def _synchronise(self, ctx):
        """🔒 Sync databases between instances

        Synchronise all databases with the last active database set that was saved in the botspam channel.
        """    
        await fnc_adm.synchronise_instances(ctx)
    @_synchronise.error
    async def synchronise_error(self, ctx, error):
        await util.error_handling(ctx, error)



    #########################################################################################################
    ##                                         cloud stuff                                                 ##
    #########################################################################################################



    @commands.command(name='loadcloud', aliases = ["cloudload"])
    @commands.check(utl_c.check_is_bot_master)
    @commands.check(util.is_main_server)
    async def _load_cloud_backups(self, ctx):
        """🔜🔒 Retrieves newest files from cloud"""
        await fnc_clo.load_databases_from_cloud(ctx)
    @_load_cloud_backups.error
    async def load_cloud_backups_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='savecloud', aliases = ["cloudsave"])
    @commands.check(utl_c.check_is_bot_master)
    @commands.check(util.is_main_server)
    async def _save_cloud_backups(self, ctx):
        """🔜🔒 Loads newest files to cloud"""
        await fnc_clo.save_databases_to_cloud(ctx)
    @_save_cloud_backups.error
    async def save_cloud_backups_error(self, ctx, error):
        await util.error_handling(ctx, error)



async def setup(bot: commands.bot) -> None:
    await bot.add_cog(
        Administration_of_Bot_Instance(bot),
        guilds = [discord.Object(id = bot.main_guild_id)])