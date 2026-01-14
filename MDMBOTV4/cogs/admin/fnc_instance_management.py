import sqlite3

from cogs.utils.utl_discord import DiscordUtils        as utl_d
from cogs.utils.utl_general import GeneralUtils        as utl_g
from cogs.utils.utl_simple  import SimpleUtils         as utl_s

from cogs.admin.utl_admin   import AdministrationUtils as utl_a




class AdministrationFunctions():
    
    async def botstatus(ctx):
        version = utl_a.get_version()
        app_num = utl_a.get_instance_number(ctx.bot.application_id)

        if app_num is None:
            await ctx.send("Error:")
        else:
            if ctx.bot.is_active():
                emoji    = utl_g.emoji("awoken")
                activity = "active"
            else:
                emoji    = utl_g.emoji("sleep")
                activity = "inactive"
            await ctx.send(f"This instance ({app_num}) is set `{activity}` {emoji}.\nMDM Bot {version}")



    async def load_backups(ctx):
        pass
        


    async def make_backups(ctx):
        pass



    async def switch_instance(ctx):
        pass



    async def synchronise_instances(ctx):
        pass