import os
import zipfile
import sys
import traceback
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

# cloud stuff
import contextlib
import six
import time
import unicodedata
import dropbox



class Administration_of_Bot_Instance(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.application_id = os.getenv("application_id")
        self.prefix = os.getenv("prefix")

    # FUNCTIONS

    async def synchronise_databases(self, ctx, location): # ONLY LOCAL FILES NOT CLOUD
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
                async for msg in channel.history(limit=100):
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
                        if filename.endswith(".db"):
                            os.remove(f"{sys.path[0]}/temp/{filename}")
                    
                    if str(the_message.attachments) == "[]":
                        print("Error: No attachment in `LAST ACTIVE` message.")
                        await ctx.send(f"Could not find correct attachment. Please synchronise manually via `{self.prefix}loadbackup` and attaching zip file.")
                    else:
                        split_v1 = str(the_message.attachments).split("filename='")[1]
                        filename = str(split_v1).split("' ")[0]
                        if filename.endswith(".zip"): # Checks if it is a .zip file
                            await the_message.attachments[0].save(fp="temp/re_{}".format(filename))
                            continue_with_this = True

                            # CHECK FILE EXTENSIONS
                            with zipfile.ZipFile(f"{sys.path[0]}/temp/re_{filename}", 'r') as zip_ref:
                                filename_list = zip_ref.namelist()
                                for name in filename_list:
                                    if name.endswith(".db"):
                                        pass
                                    else:
                                        await ctx.send("Error with backup .zip: File must not contain anything but `.db` files!")
                                        continue_with_this = False
                                        break

                                # EXTRACT FILES
                                if continue_with_this:
                                    zip_ref.extractall(f"{sys.path[0]}/temp/")

                            # REPLACE FILES
                            if continue_with_this:
                                await ctx.send("...syncing local files")

                                for filename in os.listdir(f"{sys.path[0]}/temp/"):
                                    if filename.endswith(".db"):
                                        if filename in ["activity.db", "scrobbledata.db", "scrobbledata_releasewise.db", "scrobbledata_trackwise.db", "scrobblestats.db", "scrobblemeta.db"]:
                                            pass 
                                        else:
                                            dbExist = os.path.exists(f"{sys.path[0]}/databases/{filename}")

                                            if dbExist:
                                                os.remove(f"{sys.path[0]}/databases/{filename}")
                                            os.replace(f"{sys.path[0]}/temp/{filename}", f"{sys.path[0]}/databases/{filename}")

                            # REMOVE TEMPORARIES
                            for filename in os.listdir(f"{sys.path[0]}/temp/"):          
                                if filename.endswith(".db"):    
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
                    if filename.endswith(".db"):
                        os.remove(f"{sys.path[0]}/temp/{filename}")

                split_v1 = str(the_message.attachments).split("filename='")[1]
                filename = str(split_v1).split("' ")[0]
                if filename.endswith(".zip"): # Checks if it is a .zip file
                    await the_message.attachments[0].save(fp="temp/re_{}".format(filename))
                    continue_with_this = True

                    with zipfile.ZipFile(f"{sys.path[0]}/temp/re_{filename}", 'r') as zip_ref:
                        filename_list = zip_ref.namelist()

                        # CHECK FILE EXTENSIONS
                        for name in filename_list:
                            if name.endswith(".db"):
                                pass
                            else:
                                await ctx.send("Error: File must not contain anything but `.db` files!")
                                continue_with_this = False
                                break

                        # COPY FILES
                        if continue_with_this:
                            zip_ref.extractall(f"{sys.path[0]}/temp/")

                    # REPLACE FILES
                    if continue_with_this:
                        await ctx.send("...syncing local files")

                        for filename in os.listdir(f"{sys.path[0]}/temp/"):
                            if filename.endswith(".db"):
                                if filename in ["activity.db", "scrobbledata.db", "scrobbledata_releasewise.db", "scrobbledata_trackwise.db", "scrobblestats.db", "scrobblemeta.db"]:
                                    pass 
                                else:
                                    dbExist = os.path.exists(f"{sys.path[0]}/databases/{filename}")

                                    if dbExist:
                                        os.remove(f"{sys.path[0]}/databases/{filename}")
                                    os.replace(f"{sys.path[0]}/temp/{filename}", f"{sys.path[0]}/databases/{filename}")

                    # REMOVE TEMPORARIES
                    for filename in os.listdir(f"{sys.path[0]}/temp/"):           
                        if filename.endswith(".db"):    
                            os.remove(f"{sys.path[0]}/temp/{filename}")

                    if not continue_with_this:
                        raise ValueError("Error: File must not contain anything but `.db` files!")
                else:
                    await ctx.send("Attachment must be a `.zip` file with `.db` files in it.")
            else:
                await ctx.send("No attachment found.")



    async def create_backups(self, ctx, last_activity):
        #print(sys.path[0])
        app_id = str(self.application_id)

        con = sqlite3.connect(f'databases/botsettings.db')
        cur = con.cursor()
        app_list = [item[0] for item in cur.execute("SELECT details FROM botsettings WHERE name = ? AND value = ?", ("app id", app_id)).fetchall()]

        if len(app_list) == 0:
            print("error: no app with this id in database")
        else:
            # fetch bostpam channel
            try:
                botspam_channel_id = int([item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("botspam channel id",)).fetchall()][-1])      
            except:
                botspam_channel_id = int(os.getenv("bot_channel_id"))
            channel = await self.bot.fetch_channel(botspam_channel_id)

            await channel.send("...creating zip file") # this message content is important for the switch and sync commands

            # make backup zip
            instance = app_list[0]
            date = datetime.today().strftime('%Y-%m-%d_%H-%M-%S')

            zf = zipfile.ZipFile(f"temp/backup_{date}_{instance}.zip", "w")
            db_directory = f"{sys.path[0]}/databases"

            lastedited = 0
            lastchanged = 0
            for filename_full in os.listdir(db_directory):
                if "/" in filename_full:
                    filename = str(filename_full).split["/"][-1]
                else:
                    filename = str(filename_full)

                if filename.endswith(".db"):
                    if ("activity.db" == filename) or ("scrobbledata.db" in filename) or ("scrobbledata_releasewise.db" in filename) or ("scrobbledata_trackwise.db" in filename) or ("scrobblestats.db" in filename) or ("scrobblemeta.db" in filename):
                        continue
                        
                    zf.write(os.path.join(db_directory, filename), filename)
                    edittime = int(os.path.getmtime(os.path.join(db_directory, filename)))
                    if (edittime > lastedited) and ("activity.db" != filename) and ("scrobbledata.db" not in filename) and ("scrobbledata_releasewise.db" not in filename) and ("scrobbledata_trackwise.db" not in filename) and ("scrobblestats.db" not in filename) and ("scrobblemeta.db" not in filename):
                        lastedited = edittime
                    if filename == "aftermostchange.db":
                        try:
                            conL = sqlite3.connect(f'databases/aftermostchange.db')
                            curL = conL.cursor()
                            lastchange_list = [item[0] for item in curL.execute("SELECT value FROM lastchange WHERE name = ?", ("time",)).fetchall()]
                            lastchanged = int(lastchange_list[-1])
                        except Exception as e:
                            print(f"Error while trying to read out aftermostchange.db: {e}")
                else:
                    print(f"Ignoring file: {filename}")
            zf.close()

            if last_activity == "active":
                textmessage = f"`LAST ACTIVE`\nlast edited: <t:{lastedited}:f> i.e. <t:{lastedited}:R>"
            else:
                textmessage = f"last edited: <t:{lastedited}:f> i.e. <t:{lastedited}:R>"
            if lastchanged > 0:
                textmessage += f"\nlast changed: <t:{lastchanged}:f> i.e. <t:{lastchanged}:R>"
            else:
                textmessage += f"\n(no last change date found)"

            await channel.send(textmessage, file=discord.File(rf"temp/backup_{date}_{instance}.zip"))
            os.remove(f"temp/backup_{date}_{instance}.zip")

            # Cloud stuff

            try:
                waitingtime = max(int(instance.strip()) - 1, 0) * 3
            except:
                waitingtime = random.randint(8, 20)
            try:
                await asyncio.sleep(waitingtime)
            except:
                pass
            
            try:
                #async with ctx.typing():
                print("Starting scrobble db backup:")
                await util.cloud_upload_scrobble_backup(self.bot, ctx, app_id)
                await channel.send("Finished backup.")
            except Exception as e:
                await channel.send(f"Cloud error: {e}")
                print(traceback.format_exc())
            



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



    async def cloud_sync_wait_and_download(self, ctx, reference_time, called_from):
        """note: only call this function after backup function was called"""

        # first check if scrobbling is enabled
        conB = sqlite3.connect('databases/botsettings.db')
        curB = conB.cursor()
        scrobblefeature_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("scrobbling functionality",)).fetchall()]

        if len(scrobblefeature_list) > 0 and scrobblefeature_list[0].lower().strip() == "on":
            # remember apps that are syncing as well
            sync_list = []
            app_id_list = [item[0] for item in curB.execute("SELECT value FROM botsettings WHERE name = ?", ("app id",)).fetchall()]

            try:
                botspam_channel_id = int([item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("botspam channel id",)).fetchall()][-1])      
            except:
                botspam_channel_id = int(os.getenv("bot_channel_id"))
            channel = await self.bot.fetch_channel(botspam_channel_id)
            async for msg in channel.history(limit=100):
                if msg.created_at < reference_time:
                    break

                if "...creating zip file" in msg.content and str(msg.author.id) in app_id_list:
                    if str(msg.author.id) not in sync_list:
                        sync_list.append(str(msg.author.id))

            # wait until all apps have uploaded to cloud, or when 2 minutes passed
            all_apps_have_uploaded = False

            for t in range(60):
                async for msg in ctx.channel.history(limit=100):
                    if msg.created_at < reference_time:
                        break

                    if ("Finished backup." in msg.content or "Cloud error: " in msg.content) and str(msg.author.id) in sync_list:
                        while str(msg.author.id) in sync_list:
                            sync_list.remove(str(msg.author.id))

                if len(sync_list) == 0:
                    break

                await asyncio.sleep(2)

            # syncing
            await ctx.send("...cloud sync: downloading scrobble databases")
            await util.cloud_download_scrobble_backup(ctx, called_from)

        else:
            await ctx.send("(skipping cloud sync as scrobbling features disabled)")



    ################################################################## COMMANDS ############################################################################



    @commands.command(name='status', aliases = ["instancestatus"])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _botstatus(self, ctx):
        """🔒 Shows bot instance's status

        Shows for each instance whether the bot is active or inactive, as well as its current version.
        """    
        version = util.get_version()

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

                        # START ACTUAL SWITCH STUFF

                        reference_message   = await ctx.send(f"...starting switch") # time to check back in order to decide when cloud backup can be loaded
                        reference_time      = reference_message.created_at             

                        # remember whether to sync or not
                        syncing = True
                        if len(args) > 1 and args[1].lower() in ["nosync","nosynchronisation","nonsync","nosynch","nosynchro","nosynchronization"]:
                            syncing = False

                        async with ctx.typing():
                            # remember activity status for later
                            conA = sqlite3.connect(f'databases/activity.db')
                            curA = conA.cursor()
                            activity_list = [item[0] for item in curA.execute("SELECT value FROM activity WHERE name = ?", ("activity",)).fetchall()]
                            this_instances_activity = activity_list[0]

                            # first set to inactive, so no other commands are executed
                            curA.execute("UPDATE activity SET value = ? WHERE name = ?", ("inactive", "activity"))
                            conA.commit()

                            # then synchronise LOCAL databases
                            await ctx.send("...creating backups")
                            await asyncio.sleep(1)
                            await self.create_backups(ctx, this_instances_activity)

                            if this_instances_activity == "active":
                                await ctx.send("...awaiting")
                                if syncing:
                                    await asyncio.sleep(2)
                            else:
                                if syncing == False:
                                    await ctx.send("...skipping synchronisation")
                                else:
                                    await ctx.send("...start synchronisation process")
                                    await self.synchronise_databases(ctx, "server backup")

                            # then sync CLOUD databases

                            if syncing:
                                try:
                                    called_from = "switch"
                                    await self.cloud_sync_wait_and_download(ctx, reference_time, called_from)
                                except Exception as e:
                                    await ctx.send(f"Error while trying to sync with cloud data: {e}")

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
            reference_message   = await ctx.send(f"...starting sync") # time to check back in order to decide when cloud backup can be loaded
            reference_time      = reference_message.created_at   
            await asyncio.sleep(1) 

            await self.create_backups(ctx, this_instances_activity)
            await self.synchronise_databases(ctx, "server backup")
            called_from = "synchronise"
            await self.cloud_sync_wait_and_download(ctx, reference_time, called_from)

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

        Makes a .zip of all .db files (except scrobble data) and puts them into the botspam channel.
        If scrobbling is enabled and a dropbox API token is provided then scrobble data will be uploaded to cloud as well.

        Warning: This is a blocking function that will prevent the bot from executing any other code while it's running.

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
        (activity.db and all the scrobble databases are the only files that will never be replaced)
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



    @commands.command(name='loadcloud', aliases = ["cloudload"])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _load_cloud_backups(self, ctx):
        """🔒 Retrieves newest files from cloud"""

        async with ctx.typing():
            called_from = "loadcloud"
            await util.cloud_download_scrobble_backup(ctx, called_from)

    @_load_cloud_backups.error
    async def load_cloud_backups_error(self, ctx, error):
        await util.error_handling(ctx, error)



async def setup(bot: commands.bot) -> None:
    await bot.add_cog(
        Administration_of_Bot_Instance(bot),
        guilds = [discord.Object(id = int(os.getenv("guild_id")))])