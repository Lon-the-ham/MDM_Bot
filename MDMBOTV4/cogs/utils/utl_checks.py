import discord
import os
import sqlite3
import traceback

from discord.ext import commands
from discord.ext.commands import Context

from cogs.utils.utl_discord import DiscordUtils as utl_d
from cogs.utils.utl_general import GeneralUtils as utl_g
from cogs.utils.utl_simple  import SimpleUtils  as utl_s



class ComCheckUtils():

    #########################################################################################################
    ##                                         boolean output                                              ##
    #########################################################################################################


    def is_bot_master(ctx: Context) -> bool:
        return (ctx.message.author.id in ctx.bot.bot_master_ids)



    def is_dev(ctx: Context) -> bool:
        user     = ctx.message.author 
        conB     = sqlite3.connect(f'databases/botsettings.db')
        curB     = conB.cursor()
        dev_list = [utl_s.force_integer(item[0]) for item in curB.execute("SELECT value FROM bot_settings WHERE name = ? AND details = ?", ("master", "dev")).fetchall()]
        return (user.id in dev_list)



    def is_dm(ctx: Context) -> bool:
        return (ctx.message.guild is None)



    def is_host(ctx: Context) -> bool:
        return (ctx.message.author.id == ctx.bot.host_id)



    def is_main_server(ctx: Context) -> bool:
        server = ctx.guild
        if server is None:
            return False
        elif server.id == ctx.bot.main_guild_id:
            return True
        #elif bot.main_guild_id is None or bot.main_guild_id < 1:
        #    con = sqlite3.connect(f'databases/botsettings.db')
        #    cur = con.cursor()
        #    main_servers = [utl_s.force_integer(item[0]) for item in cur.execute("SELECT value FROM bot_settings WHERE name = ? AND num = ?", ("server id", 0)).fetchall()]
        #    if server.id in main_servers:
        #        return True
        #    else:
        #        return False
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

    def check_is_active(ctx: Context) -> bool:
        if not ctx.bot.is_active():
            raise commands.CheckFailure("inactive")
        return True



    def check_is_bot_master(ctx: Context) -> bool:
        if not ComCheckUtils.is_bot_master:
            raise commands.CheckFailure("Error: Permission denied.\n-# You'd need to have bot master permissions.")
        return True



    def check_is_dev(ctx: Context) -> bool:
        if not ComCheckUtils.is_dev(ctx):
            raise commands.CheckFailure(f"Error: Permission denied.\n-# You'd need to have dev permissions.")
        return True



    def check_is_host(ctx: Context) -> bool:
        if not ComCheckUtils.is_host(ctx):
            raise commands.CheckFailure("Error: Permssion denied, this is a host-only command.")
        return True



    def check_is_import_rym_enabled(ctx: Context) -> bool:
        if not ctx.bot.webinfo_import["rym"]:
            raise commands.CheckFailure("Error: RYM scraper disabled")
        return True



    def check_is_import_metallum_enabled(ctx: Context) -> bool:
        if not ctx.bot.webinfo_import["ma"]:
            raise commands.CheckFailure("Error: MA scraper disabled")
        return True



    def check_is_import_scrobbles_enabled(ctx: Context) -> bool:
        if not ctx.bot.webinfo_import["lfm"]:
            raise commands.CheckFailure("Error: Scrobbling disabled")
        return True



    def check_is_main_server(ctx: Context) -> bool:
        if not ComCheckUtils.is_main_server(ctx):
            try:
                con = sqlite3.connect(f'databases/botsettings.db')
                cur = con.cursor()
                mainserver = [item[0] for item in cur.execute("SELECT details FROM bot_settings WHERE name = ? AND num = ?", ("server id", 0)).fetchall()][0]
                if mainserver.strip() == "":
                    mainserver = "*main server*"
            except:
                mainserver = "*bot's main server*"
            raise commands.CheckFailure(f'Error: This is a {mainserver} specific command.')
        return True
        


    def check_mod_permissions(ctx: Context):
        # TODO
        pass



    #########################################################################################################
    ##                                         error handler                                               ##
    #########################################################################################################


    async def error_handling(ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f'Sorry, you do not have permissions to do this!')

        elif isinstance(error, commands.CheckFailure):
            if str(error) == "ignore":
                pass
            else:
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
                topic     = "detailed error reporting"
                server_id = ctx.guild.id
                if server_id != ctx.bot.main_guild_id and (not os.path.isdir(f'databases/{server_id}') or not os.path.isfile(f'databases/{server_id}/serversettings.db')):
                    server_id = ctx.bot.main_guild_id

                conB = sqlite3.connect(f'databases/{server_id}/serversettings.db')
                curB = conB.cursor()
                detailederrornotif_list = [item[0] for item in curB.execute("SELECT active FROM notifications WHERE name = ?", (topic,)).fetchall()]
                if len(detailederrornotif_list) == 0 or detailederrornotif_list[0] == 0:
                    pass
                else:
                    detailtext   = str(traceback.format_exc()).split("The above exception")[0].strip()[:2000]
                    msg_title    = f"Error in {ctx.channel.mention}"
                    errormessage = f"Error message: {str(error)}```{detailtext}```"
                    await utl_d.notification_send(ctx.bot, msg_title, errormessage, topic)
            except Exception as e:
                print("Error:", e)

