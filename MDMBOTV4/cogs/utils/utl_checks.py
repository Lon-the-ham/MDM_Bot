import discord
import sqlite3
import traceback

from discord.ext.commands import check, Context

from cogs.utils.utl_discord import DiscordUtils as utl_d
from cogs.utils.utl_general import GeneralUtils as utl_g
from cogs.utils.utl_simple  import SimpleUtils  as utl_s

class ComCheckUtils():

    #########################################################################################################
    ##                                         boolean output                                              ##
    #########################################################################################################

    def is_active(bot) -> bool:
        return (bot.activity_status > 0)



    def is_dev(ctx: Context) -> bool:
        user = ctx.message.author 

        con = sqlite3.connect(f'databases/botsettings.db')
        cur = con.cursor()
        # TODO
        return False



    def is_dm(ctx: Context) -> bool:
        return (ctx.message.guild is None)



    def is_main_server(ctx: Context) -> bool:
        server = ctx.message.guild
        if server is None:
            return False
        else:
            # TODO 
            con = sqlite3.connect(f'databases/botsettings.db')
            cur = con.cursor()
            main_servers = [item[0] for item in cur.execute("SELECT value FROM botsettings WHERE name = ?", ("main server id",)).fetchall()]
            guild_id = str(ctx.guild.id)
            if guild_id in main_servers:
                return True
            else:
                return False



    def inactivity_filter_enabled(ctx: Context) -> bool:
        # TODO 
        conB = sqlite3.connect('databases/botsettings.db')
        curB = conB.cursor()

        # check if feature is enabled
        inactivityfilter_list = [[item[0], item[1]] for item in curB.execute("SELECT value, details FROM serversettings WHERE name = ?", ("inactivity filter",)).fetchall()]
        if len(inactivityfilter_list) == 0:
            raise ValueError("inactivity filter not enabled")
        else:
            inactivityfilter = inactivityfilter_list[0][0]
            if inactivityfilter.lower().strip() != "on":
                raise ValueError("inactivity filter not enabled")

        # check for role id
        inactivityrole_list = [item[0] for item in curB.execute("SELECT role_id FROM specialroles WHERE name = ?", ("inactivity role",)).fetchall()]        
        if len(inactivityrole_list) == 0 or not Utils.represents_integer(inactivityrole_list[0]):
            raise ValueError("inactivity role not set")
        else:
            inactivity_role_id = int(inactivityrole_list[0])

        inactivity_role = ctx.guild.get_role(inactivity_role_id)

        if inactivity_role is None:
            raise ValueError("provided inactivity role ID is faulty")

        return True


    #########################################################################################################
    ##                             check with customised error message                                     ##
    #########################################################################################################

    def check_is_active(bot):
        if ComCheckUtils.is_active(bot):
            return True
        raise commands.CheckFailure("inactive")



    def check_is_dev(ctx: Context) -> bool:
        if ComCheckUtils.is_dev(ctx):
            return True
        raise commands.CheckFailure(f'Error: Permission denied.')



    def check_is_host(ctx: Context) -> bool:
        try:
            host_id = int(os.getenv("host_user_id"))
        except:
            raise commands.CheckFailure("Failed to load host id from environment. This is a bot host-only command.")

        if ctx.author.id == host_id:
            return True

        else:
            raise commands.CheckFailure("Permssion denied, this is a host-only command.")



    def check_is_main_server(ctx: Context) -> bool:
        if ComCheckUtils.is_main_server(ctx):
            return True
        try:
            mainserver = [item[0] for item in cur.execute("SELECT details FROM botsettings WHERE name = ?", ("main server id",)).fetchall()][0]
            if mainserver.strip() == "":
                mainserver = "*main server*"
        except:
            mainserver = "*bot's main server*"
        raise commands.CheckFailure(f'Error: This is a {mainserver} specific command.')
        


    def check_mod_permissions(ctx):
        # TODO
        pass



    #########################################################################################################
    ##                                         error handler                                               ##
    #########################################################################################################


    async def error_handling(ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f'Sorry, you do not have permissions to do this!')

        elif isinstance(error, commands.CheckFailure):
            if str(error) != "inactive":
                await ctx.channel.send(error)
            else:
                if ComCheckUtils.is_dm(ctx):
                    await ctx.send("This bot instance is inactive. Check which application is actually the currently active one.")

        elif isinstance(error, commands.InvalidEndOfQuotedStringError) or isinstance(error, commands.UnexpectedQuoteError):
            await ctx.channel.send(f'Bad Argument Error:```{str(error)}```Better try to avoid quotation marks within commands.')

        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.channel.send(f'Error: Command needs arguments. Use help command for more info.')

        elif "sslv3 alert bad record mac" in str(error).lower():
            await ctx.channel.send(f"Whoopsie, seems like there was some client hiccup on discord's side (SSLv3 error). You can try it again now.")

        else:
            await ctx.channel.send(f'An error ocurred.')
            print(f"ERROR HANDLER: {str(error)}")
            print("-------------------------------------")
            print(traceback.format_exc())
            print("-------------------------------------")
            try:
                # TODO 
                conB = sqlite3.connect(f'databases/botsettings.db')
                curB = conB.cursor()
                detailederrornotif_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("detailed error reporting",)).fetchall()]
                if len(detailederrornotif_list) == 0 or detailederrornotif_list[0] != "on":
                    pass
                else:
                    detailtext = str(traceback.format_exc()).split("The above exception")[0].strip()[:2000]
                    await utl_d.bot_spam_send(ctx, f"Error in {ctx.channel.mention}", f"Error message: {str(error)}```{detailtext}```")
            except Exception as e:
                print("Error:", e)