import os
import zipfile
import sys
# COG for management of different bot instances
# relevant if this application is hosted on multiple bot accounts for redundancy
# otherwise probably only the backup function is important

import datetime
from datetime import datetime
import pytz
import sqlite3
import asyncio
import discord
from discord.ext import commands
import re
from other.utils.utils import Utils as util


class Administration_of_Bot_Instance(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.application_id = os.getenv("application_id")
        self.prefix = os.getenv("prefix")

    # FUNCTIONS

    async def synchronise_databases(self, ctx, location):
        if location == "server backup":
            try:
                con = sqlite3.connect(f'databases/botsettings.db')
                cur = con.cursor()
                botspam_channel_id = int([item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("botspam channel id",)).fetchall()][-1])      
                channel = await self.bot.fetch_channel(botspam_channel_id)

                app_id_list = [item[0] for item in cur.execute("SELECT value FROM botsettings WHERE name = ?", ("app id",)).fetchall()]

                now = int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds())
                found = False
                last_occurence = 0
                async for msg in channel.history(limit=50):
                    if "`LAST ACTIVE`" in msg.content and str(msg.author.id) in app_id_list:
                        try:
                            timestamp = int(msg.content.split("last edited: <t:")[1].split(":f> i.e. <t:")[0])
                            if timestamp > last_occurence:
                                last_occurence = timestamp
                                the_message = msg
                                found = True
                        except Exception as e:
                            print(e)

                if found:
                    await ctx.send("...clearing space and retrieving files")
                    for filename in os.listdir(f"{sys.path[0]}/temp/"):
                        os.remove(f"{sys.path[0]}/temp/{filename}")
                    
                    if str(the_message.attachments) == "[]":
                        print("Error: No attachment in `LAST ACTIVE` message.")
                        await ctx.send(f"Could not find correct attachment. Please synchronise manually via `{self.prefix}loadbackup` and attaching zip file.")
                    else:
                        split_v1 = str(the_message.attachments).split("filename='")[1]
                        filename = str(split_v1).split("' ")[0]
                        if filename.endswith(".zip"): # Checks if it is a .zip file
                            await the_message.attachments[0].save(fp="temp/re_{}".format(filename))

                            with zipfile.ZipFile(f"{sys.path[0]}/temp/re_{filename}", 'r') as zip_ref:
                                zip_ref.extractall(f"{sys.path[0]}/temp/")

                            await ctx.send("...syncing")

                            for filename in os.listdir(f"{sys.path[0]}/temp/"):
                                if filename.endswith(".db"):
                                    if filename == "activity.db":
                                        pass 
                                    else:
                                        dbExist = os.path.exists(f"{sys.path[0]}/databases/{filename}")

                                        if dbExist:
                                            os.remove(f"{sys.path[0]}/databases/{filename}")
                                        os.replace(f"{sys.path[0]}/temp/{filename}", f"{sys.path[0]}/databases/{filename}")

                            for filename in os.listdir(f"{sys.path[0]}/temp/"):                
                                os.remove(f"{sys.path[0]}/temp/{filename}")
                        else:
                            await ctx.send("Error with backup attachment: File not in `.zip` format.")
                else:
                    await ctx.send(f"Could not find backup of last active instance. Please synchronise manually via `{self.prefix}loadbackup` and attaching zip file.")
            
            except Exception as e:
                print(f"Error while trying to fetch last active backup file: {e}")

        else: # location = msg file
            the_message = ctx.message
            if the_message.attachments:
                await ctx.send("...clearing space and retrieving attachment")
                for filename in os.listdir(f"{sys.path[0]}/temp/"):
                    os.remove(f"{sys.path[0]}/temp/{filename}")

                split_v1 = str(the_message.attachments).split("filename='")[1]
                filename = str(split_v1).split("' ")[0]
                if filename.endswith(".zip"): # Checks if it is a .zip file
                    await the_message.attachments[0].save(fp="temp/re_{}".format(filename))

                    with zipfile.ZipFile(f"{sys.path[0]}/temp/re_{filename}", 'r') as zip_ref:
                        zip_ref.extractall(f"{sys.path[0]}/temp/")

                    await ctx.send("...syncing")

                    for filename in os.listdir(f"{sys.path[0]}/temp/"):
                        if filename.endswith(".db"):
                            if filename == "activity.db":
                                pass 
                            else:
                                dbExist = os.path.exists(f"{sys.path[0]}/databases/{filename}")

                                if dbExist:
                                    os.remove(f"{sys.path[0]}/databases/{filename}")
                                    os.replace(f"{sys.path[0]}/temp/{filename}", f"{sys.path[0]}/databases/{filename}")

                    for filename in os.listdir(f"{sys.path[0]}/temp/"):                
                        os.remove(f"{sys.path[0]}/temp/{filename}")
                else:
                    await ctx.send("Attachment must be a `.zip` file with `.db` files in it.")
            else:
                await ctx.send("No attachment found.")


    # COMMANDS

    async def create_backups(self, ctx, last_activity):
        #print(sys.path[0])
        app_id = str(self.application_id)

        con = sqlite3.connect(f'databases/botsettings.db')
        cur = con.cursor()
        app_list = [item[0] for item in cur.execute("SELECT details FROM botsettings WHERE name = ? AND value = ?", ("app id", app_id)).fetchall()]

        if len(app_list) == 0:
            print("error: no app with this id in database")
        else:
            instance = app_list[0]
            date = datetime.today().strftime('%Y-%m-%d_%H-%M-%S')

            zf = zipfile.ZipFile(f"temp/backup_{date}_{instance}.zip", "w")
            db_directory = f"{sys.path[0]}/databases"

            lastedited = 0
            lastchanged = 0
            for filename in os.listdir(db_directory):
                zf.write(os.path.join(db_directory, filename), filename)

                edittime = int(os.path.getmtime(os.path.join(db_directory, filename)))
                if (edittime > lastedited) and ("activity.db" not in str(filename)):
                    lastedited = edittime
                if str(filename) == "aftermostchange.db":
                    try:
                        conL = sqlite3.connect(f'databases/aftermostchange.db')
                        curL = conL.cursor()
                        lastchange_list = [item[0] for item in curL.execute("SELECT value FROM lastchange WHERE name = ?", ("time",)).fetchall()]
                        lastchanged = int(lastchange_list[-1])
                    except Exception as e:
                        print(f"Error while trying to read out aftermostchange.db: {e}")
            zf.close()

            if last_activity == "active":
                textmessage = f"`LAST ACTIVE`\nlast edited: <t:{lastedited}:f> i.e. <t:{lastedited}:R>"
            else:
                textmessage = f"last edited: <t:{lastedited}:f> i.e. <t:{lastedited}:R>"
            if lastchanged > 0:
                textmessage += f"\nlast changed: <t:{lastchanged}:f> i.e. <t:{lastchanged}:R>"
            else:
                textmessage += f"\n(no last change date found)"

            try:
                botspam_channel_id = int([item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("botspam channel id",)).fetchall()][-1])      
                channel = await self.bot.fetch_channel(botspam_channel_id)
                await channel.send(textmessage, file=discord.File(rf"temp/backup_{date}_{instance}.zip"))
            except:
                print("Error while trying to send backup file.")
            os.remove(f"temp/backup_{date}_{instance}.zip")



    async def botrole_assignment(self, ctx, text):
        con = sqlite3.connect(f'databases/botsettings.db')
        cur = con.cursor()
        bot_id = self.application_id
        guild = ctx.guild
        for member in ctx.guild.members:
            if member.id == int(bot_id):
                botmember = member 
                botfound = True
                break 
        else:
            botfound = False

        if botfound:
            bot_display = [item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("bot display",)).fetchall()][0]
            if bot_display == "on":
                botrole_id = int([item[0] for item in cur.execute("SELECT role_id FROM specialroles WHERE name = ?", ("bot display role",)).fetchall()][0])
                all_roles = [r for r in ctx.guild.roles]
                for role in all_roles:
                    if role.id == botrole_id:
                        botrole = role
                        rolefound = True 
                        break 
                else:
                    rolefound = False 
                if rolefound:
                    if text == "assign":
                        await botmember.add_roles(botrole)
                        print("assigned bot display role")
                    elif text == "unassign":
                        await botmember.remove_roles(botrole)
                        print("unassigned bot display role")
                    else:
                        print("error: botrole_assignment() function was called with invalid argument")
                else: 
                    print("error: could not find bot display role within server roles")
            else:
                print("Bot sidebar display role switch disabled.")
        else:
            print("error: could not find bot's member object")



    @commands.command(name='status', aliases = ["instancestatus"])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _botstatus(self, ctx):
        """🔒 Shows bot instance's status

        Shows for each instance whether the bot is active or inactive, as well as its current version.
        """    
        try:
            lines = []
            with open('version.txt', 'r') as s:
                for line in s:
                    print(line.strip())
                    lines.append(line.strip())
            version = lines[0]
        except Exception as e:
            version = "version ?"
            print("Error with version check:", e)

        conA = sqlite3.connect(f'databases/activity.db')
        curA = conA.cursor()
        activity_list = [item[0] for item in curA.execute("SELECT value FROM activity WHERE name = ?", ("activity",)).fetchall()]
        this_instances_activity = activity_list[0]

        con = sqlite3.connect(f'databases/botsettings.db')
        cur = con.cursor()
        app_id = str(self.application_id)
        app_list = [item[0] for item in cur.execute("SELECT details FROM botsettings WHERE name = ? AND value = ?", ("app id", app_id)).fetchall()]

        if len(app_list) == 0:
            print(f"Error: no app with this id in database ({version})")
        else:
            instance = app_list[0]
            if this_instances_activity == "active":
                emoji = util.emoji("awoken")
            else:
                emoji = util.emoji("sleep")
            await ctx.send(f"This instance ({instance}) is set `{this_instances_activity}` {emoji}.\nMDM Bot {version}")
    @_botstatus.error
    async def botstatus_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='switch', aliases = ["instance", "instances"])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _switch(self, ctx, *args):
        """🔒 Switches bot instance

        Sets chosen bot instance to active and the others to inactive status. 

        Use with argument 1, 2, 3 or off.
        Optional: add argument "nosync" to prevent synchronisation with last active database set.
        """    
        def check(m): # checking if it's the same user and channel
            return ((m.author == ctx.author) and (m.channel == ctx.channel))


        if len(args) == 0:
            ctx.send(f"No argument provided. Command needs integer argument (application index) or `off` argument.")
        else:
            arg = args[0]
            if arg.lower() == "off":

                await ctx.send("Are you sure you want to deactivate all bot instances? Respond with `yes` to confirm.")

                try: # waiting for message
                    async with ctx.typing():
                        response = await self.bot.wait_for('message', check=check, timeout=30.0) # timeout - how long bot waits for message (in seconds)
                except asyncio.TimeoutError: # returning after timeout
                    await ctx.send("action timed out")
                    return

                # if response is different than yes / y - return
                if response.content.lower() not in ["yes", "y"]:
                    await ctx.send("cancelled action")
                    return

                # rest of your code
                async with ctx.typing():
                    conA = sqlite3.connect(f'databases/activity.db')
                    curA = conA.cursor()
                    activity_list = [item[0] for item in curA.execute("SELECT value FROM activity WHERE name = ?", ("activity",)).fetchall()]
                    this_instances_activity = activity_list[0]

                    curA.execute("UPDATE activity SET value = ? WHERE name = ?", ("inactive", "activity"))
                    conA.commit()

                    if this_instances_activity == "active":
                        await asyncio.sleep(1)
                        await self.create_backups(ctx, this_instances_activity)
                    try:
                        await self.botrole_assignment(ctx,"unassign")
                    except Exception as e:
                        print(e)
                    await ctx.send(f"Shut down.")

            else:
                # regular switching?
                try:
                    intarg = int(arg)
                    arg_is_integer = True
                except:
                    arg_is_integer = False

                if arg_is_integer:
                    con = sqlite3.connect(f'databases/botsettings.db')
                    cur = con.cursor()
                    app_list = [[item[0],item[1]] for item in cur.execute("SELECT details, value FROM botsettings WHERE name = ?", ("app id",)).fetchall()]

                    index_found = False
                    for item in app_list:
                        if item[0] == str(intarg):
                            app_index = item[0]
                            app_id = item[1]
                            index_found = True
                            break

                    if index_found:
                        await ctx.send("Are you sure you want to switch instances? Respond with `yes` to confirm.")

                        try: # waiting for message
                            async with ctx.typing():
                                response = await self.bot.wait_for('message', check=check, timeout=30.0) # timeout - how long bot waits for message (in seconds)
                        except asyncio.TimeoutError: # returning after timeout
                            await ctx.send("action timed out")
                            return

                        # if response is different than yes / y - return
                        if response.content.lower() not in ["yes", "y"]:
                            await ctx.send("cancelled action")
                            return

                        # rest of your code
                        await ctx.send(f"...starting switch")

                        async with ctx.typing():
                            # remember activity status for later
                            conA = sqlite3.connect(f'databases/activity.db')
                            curA = conA.cursor()
                            activity_list = [item[0] for item in curA.execute("SELECT value FROM activity WHERE name = ?", ("activity",)).fetchall()]
                            this_instances_activity = activity_list[0]

                            # first set to inactive, so no other commands are executed
                            curA.execute("UPDATE activity SET value = ? WHERE name = ?", ("inactive", "activity"))
                            conA.commit()

                            # then synchronise databases
                            await ctx.send("...creating backups")
                            await asyncio.sleep(1)
                            await self.create_backups(ctx, this_instances_activity)

                            if this_instances_activity == "active":
                                await ctx.send("...awaiting")
                                await asyncio.sleep(2)
                            else:
                                if len(args) > 1 and args[1].lower() in ["nosync","nosynchronisation","nonsync","nosynch","nosynchro","nosynchronization"]:
                                    await ctx.send("...skipping synchronisation")
                                else:
                                    await ctx.send("...start synchronisation process")
                                    await self.synchronise_databases(ctx, "server backup")


                            # then set the correct app to active
                            if app_id == str(self.application_id):
                                curA.execute("UPDATE activity SET value = ? WHERE name = ?", ("active", "activity"))
                                conA.commit()

                                emoji = util.emoji("awoken")
                                try:
                                    await self.botrole_assignment(ctx,"assign")
                                except Exception as e:
                                    print(e)
                            else:
                                # keep inactive
                                emoji = util.emoji("sleep")
                                try:
                                    await self.botrole_assignment(ctx,"unassign")
                                except Exception as e:
                                    print(e)
                            await ctx.send(f"done {emoji}")

                    else:
                        await ctx.send(f"Application with index {intarg} not found.")
                else:
                    await ctx.send(f"Faulty argument provided. Command needs integer argument (application index) or `off` argument.")
    @_switch.error
    async def switch_error(self, ctx, error):
        await util.error_handling(ctx, error)       


    @commands.command(name='synchronise', aliases = ["synchronize"])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _synchronise(self, ctx):
        """🔒 Sync databases between instances

        Synchronise all databases with the last active database set that was saved in the botspam channel.
        """    
        conA = sqlite3.connect(f'databases/activity.db')
        curA = conA.cursor()
        activity_list = [item[0] for item in curA.execute("SELECT value FROM activity WHERE name = ?", ("activity",)).fetchall()]
        this_instances_activity = activity_list[0]

        async with ctx.typing():
            # first set to inactive, so no other commands are executed
            curA.execute("UPDATE activity SET value = ? WHERE name = ?", ("inactive", "activity"))
            conA.commit()

            # then synchronise databases
            await asyncio.sleep(1)
            await self.create_backups(ctx, this_instances_activity)
            await self.synchronise_databases(ctx, "server backup")

            # set activity back
            if this_instances_activity == "active":
                curA.execute("UPDATE activity SET value = ? WHERE name = ?", ("active", "activity"))
                conA.commit()

            await ctx.send("done.")
    @_synchronise.error
    async def synchronise_error(self, ctx, error):
        await util.error_handling(ctx, error)


    @commands.command(name='backup', aliases = ["makebackup", "makebackups", "savebackup", "savebackups", "backups"])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _make_backups(self, ctx):
        """🔒 Backup of all databases

        Makes a .zip of all .db files and puts them into the botspam channel.
        """    
        conA = sqlite3.connect(f'databases/activity.db')
        curA = conA.cursor()
        activity_list = [item[0] for item in curA.execute("SELECT value FROM activity WHERE name = ?", ("activity",)).fetchall()]
        this_instances_activity = activity_list[0]

        async with ctx.typing():
            # first set to inactive, so no other commands are executed
            curA.execute("UPDATE activity SET value = ? WHERE name = ?", ("inactive", "activity"))
            conA.commit()

            # then synchronise databases
            await asyncio.sleep(1)
            await self.create_backups(ctx, this_instances_activity)

            # set activity back
            if this_instances_activity == "active":
                curA.execute("UPDATE activity SET value = ? WHERE name = ?", ("active", "activity"))
                conA.commit()
    @_make_backups.error
    async def make_backups_error(self, ctx, error):
        await util.error_handling(ctx, error)


    @commands.command(name='loadbackup', aliases = ["loaddatabases"])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _load_backups(self, ctx):
        """🔒 Upload DBs and synchronise

        Synchronise databases with .db files in a zip file.
        Use command by attaching such .zip-file.

        In case you only want to replace *some* of the files upload a .zip with only the .db files you want to replace, and the other old files will stay.
        (activity.db is the only database that will never be replaced)
        """    
        conA = sqlite3.connect(f'databases/activity.db')
        curA = conA.cursor()
        activity_list = [item[0] for item in curA.execute("SELECT value FROM activity WHERE name = ?", ("activity",)).fetchall()]
        this_instances_activity = activity_list[0]


        async with ctx.typing():
            # first set to inactive, so no other commands are executed
            curA.execute("UPDATE activity SET value = ? WHERE name = ?", ("inactive", "activity"))
            conA.commit()

            # then synchronise databases
            await asyncio.sleep(1)
            await self.create_backups(ctx, this_instances_activity)
            await self.synchronise_databases(ctx, "upload")

            # set activity back
            if this_instances_activity == "active":
                curA.execute("UPDATE activity SET value = ? WHERE name = ?", ("active", "activity"))
                conA.commit()

            await ctx.send("done.")
    @_load_backups.error
    async def load_backups_error(self, ctx, error):
        await util.error_handling(ctx, error)





async def setup(bot: commands.bot) -> None:
    await bot.add_cog(
        Administration_of_Bot_Instance(bot),
        guilds = [discord.Object(id = int(os.getenv("guild_id")))])