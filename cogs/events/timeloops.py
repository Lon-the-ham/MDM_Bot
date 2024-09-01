import discord
from discord.ext import tasks, commands
import datetime
import pytz
from other.utils.utils import Utils as util
import os
import traceback
import asyncio
import sqlite3
import requests
from emoji import UNICODE_EMOJI



class TimeLoops(commands.Cog):
    def __init__(self, bot: commands.bot) -> None:
        self.bot = bot
        self.index = 0
        self.minutely_check.start()
        self.hourly_check.start()
        self.daily_check.start()



    def reminders_enabled(self):
        conB = sqlite3.connect(f'databases/botsettings.db')
        curB = conB.cursor()
        custom_reminders_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("reminder functionality",)).fetchall()]
        if len(custom_reminders_list) == 0:
            curB.execute("INSERT INTO serversettings VALUES (?, ?, ?, ?)", ("reminder functionality", "on", "", ""))
            conB.commit()
            enabled = "on"
        else:
            enabled = custom_reminders_list[0].lower().strip()

        if enabled == "on":
            return True
        else:
            return False



    async def timeloop_error(self, error, *function):
        if function is None or function == "":
            functiontext = ""
        else:
            functiontext = f" in {function}"
        print(f"TIME LOOP ERROR{functiontext}:\n>>", str(error))
        print("-------------------------------------")
        print(traceback.format_exc())
        print("-------------------------------------")



    async def timeloop_notification(self, title, message, success):
        try:
            con = sqlite3.connect(f'databases/botsettings.db')
            cur = con.cursor()
            botspamchannel_id = int([item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("botspam channel id",)).fetchall()][0])
        except:
            print("Bot spam/notification channel ID in database is faulty.")
            try:
                botspamchannel_id = int(os.getenv("bot_channel_id"))
            except Exception as e:
                print(f"Error in timeloop notification ({title}):", e)
                return
        botspamchannel = self.bot.get_channel(botspamchannel_id) 
        if success == False:
            title = "⚠️ " + title + " Error"
        embed=discord.Embed(title=title[:256], description=message[:4096], color=0x000000)
        await botspamchannel.send(embed=embed)



    ############### REMINDERS AND UNMUTING #############################################################################################################



    @tasks.loop(minutes=1.0)
    async def minutely_check(self):
        try:
            activity = util.is_active()
        except:
            return
        if not activity:
            return

        # temporary reminders (whenever after passing triggertime)
        try:
            await self.temp_reminders()
        except Exception as e:
            await self.timeloop_error(e, "minutely_check:temp_reminders")

        # recurring reminders (after passing with one step lower leeway. steps: daily, weekly, fortnightly, monthly, yearly)
        try:
            await self.recc_reminders()
        except Exception as e:
            await self.timeloop_error(e, "minutely_check:recc_reminders")

        # timeout unmuting (whenever after passing triggertime)
        try:
            await self.unmuting()
        except Exception as e:
            await self.timeloop_error(e, "minutely_check:unmuting")



    @minutely_check.before_loop
    async def before_minutely_check(self):
        await self.bot.wait_until_ready()
        con = sqlite3.connect(f'databases/timetables.db')
        cur = con.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS reminders (reminder_id text, username text, userid text, utc_timestamp text, remindertext text, channel text, channel_name text, og_message text, og_time text)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS recurring (reminder_id text, username text, userid text, pinglist text, interval text, next_time text, remindertitle text, remindertext text, adaptivelink text, channel text, channel_name text, thumbnail text, emoji text)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS timeout (username text, userid text, utc_timestamp text, role_id_list text)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS zcounter (num text)''')



    ############### CALENDAR & LFM UPDATES ###########################################################################################################################



    @tasks.loop(hours=1.0)
    async def hourly_check(self):
        try:
            activity = util.is_active()
        except:
            return
        if not activity:
            return

        # calendar notification (after passing with 1 hour leeway)
        try:
            await self.calendar_notif()
        except Exception as e:
            await self.timeloop_error(e, "hourly_check:calendar_notif")

        await asyncio.sleep(180)
        # update lastfm
        try:
            await self.lastfm_update()
        except Exception as e:
            await self.timeloop_error(e, "hourly_check:lastfm_update")

    @hourly_check.before_loop
    async def before_hourly_check(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(20.4)




    ############### DAILY UPDATE FOR DATABASES ##########################################################################################################



    @tasks.loop(hours=24.0)
    async def daily_check(self):
        print("daily check...")
        try:
            activity = util.is_active()
        except:
            return
        if not activity:
            return

        # update currency table (exact minute) [shutdown when no api/secret key or "-" is provided]
        response = ""
        success = False
        try:
            response, success = await self.update_currency()
        except Exception as e:
            if str(e) == "Failed to fetch exchangerate api key":
                try:
                    print("No API keys, using web scrape.")
                    response, success = await util.scrape_exchangerates()
                except Exception as e:
                    print("Error while trying to webscrape exchangerate info:", e)
            else:
                await self.timeloop_error(e, "daily_check:update_currency")

        await self.timeloop_notification("Update Exchange Rates", response, success)

        # update emoji table (remove unsuable emojis)
        try:
            await self.update_emoji()
        except Exception as e:
            await self.timeloop_error(e, "daily_check:update_emoji")

        # inactivity filter
        try:
            await self.inactivity_filtering()
        except Exception as e:
            await self.timeloop_error(e, "daily_check:inactivity_filter")

        # clear old data
        try:
            await self.clear_databases()
        except Exception as e:
            await self.timeloop_error(e, "daily_check:clear_databases")

    @daily_check.before_loop
    async def before_daily_check(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(40.7)

        for _ in range(60*60*24):  # loop the whole day
            h = datetime.datetime.utcnow().hour
            m = datetime.datetime.utcnow().minute
            if h in [1] and m in [1,2]:
                return
            await asyncio.sleep(60)


    #######################################################################################################################################################
    #######################################################################################################################################################
    #######################################################################################################################################################
    #######################################################################################################################################################
    #######################################################################################################################################################
    #######################################################################################################################################################
    #######################################################################################################################################################
    #######################################################################################################################################################
    #######################################################################################################################################################
    #######################################################################################################################################################
    #######################################################################################################################################################
    #######################################################################################################################################################
    #######################################################################################################################################################
    #######################################################################################################################################################
    #######################################################################################################################################################
    #######################################################################################################################################################
    #######################################################################################################################################################
    #######################################################################################################################################################
    #######################################################################################################################################################
    #######################################################################################################################################################
    #######################################################################################################################################################

    # reminder stuff

    async def temp_reminders(self):
        # FETCH DATA FROM DATABASE

        con = sqlite3.connect(f'databases/timetables.db')
        cur = con.cursor()
        now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())
        reminder_list = [[item[0],item[1],item[2],item[3],item[4],item[5]] for item in cur.execute("SELECT userid, utc_timestamp, remindertext, channel, og_message, og_time FROM reminders WHERE cast(utc_timestamp as integer) <= ?", (now,)).fetchall()]
        
        if len(reminder_list) == 0:
            return

        for item in reminder_list[:5]: # limit this to 5 for this loop

            await asyncio.sleep(1)

            # PARSE DATABASE INFORMATION

            try:
                user_id = item[0]
                utc_timestamp = int(item[1])
                remindertext = util.cleantext(item[2].strip())
                channel_id = int(item[3])
                og_message_id = int(item[4])
                og_time = int(item[5])
            except:
                print(f"Error while parsing reminder:", e)
                await self.timeloop_notification("Reminder", "Error with reminder.```" + str(item[2])[:500] + f"```Error message:```{e}```", False)
                await self.delete_reminder(item[0],item[1],item[2],item[3],item[4],item[5])
                continue

            # FETCH CHANNEL
            
            try:
                channel = self.bot.get_channel(channel_id) 
            except Exception as e:
                print(f"Error while trying to fetch channel for recurring reminder:", e)
                await self.timeloop_notification("Reminder", f"Error with channel ID {channel_id}, i.e. channel <#{channel_id}>\nError message:```{e}```", False)
                await self.delete_reminder(item[0],item[1],item[2],item[3],item[4],item[5])
                continue

            # FETCH OG MESSAGE

            try:
                og_message = await channel.fetch_message(og_message_id)
                found_og_message = True
            except:
                found_og_message = False

            # FETCH TIME DIFFERENCE

            try:
                time_difference = util.seconds_to_readabletime(now - og_time, True, now)
                time_diff_string = f"\n({time_difference} ago)"
                valid_time_difference = True
            except:
                valid_time_difference = False

            # SEND MESSAGE

            try:
                message_text = f"<@{user_id}>: "
                message_text += remindertext

                if valid_time_difference:
                    n = len(time_diff_string)
                else:
                    n = 0

                if len(message_text) > 2000-n:
                    message_text = message_text[:1997-n] + "..."

                if valid_time_difference:
                    message_text += time_diff_string

                if found_og_message:
                    await og_message.reply(message_text)
                else:
                    await channel.send(message_text)
            except Exception as e:
                print(f"Error while trying to send recurring reminder:", e)
                await self.timeloop_notification("Reminder", f"Error while trying to send reminder.\nError message:```{e}```", False)

            # REMOVE ITEM FROM TABLE
            await self.delete_reminder(item[0],item[1],item[2],item[3],item[4],item[5])



    async def delete_reminder(self, user_id, utc_timestamp, remindertext, channel_id, og_message_id, og_time):
        con = sqlite3.connect(f'databases/timetables.db')
        cur = con.cursor()
        cur.execute("DELETE FROM reminders WHERE userid = ? AND utc_timestamp = ? AND remindertext = ? AND channel = ? AND og_message = ? AND og_time = ?", (user_id, utc_timestamp, remindertext, channel_id, og_message_id, og_time))
        con.commit()
        await util.changetimeupdate()



    async def recc_reminders(self):
        # FETCH DATA FROM DATABASE

        con = sqlite3.connect(f'databases/timetables.db')
        cur = con.cursor()
        now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())
        reminder_list = [[item[0],item[1],item[2],item[3],item[4],item[5],item[6],item[7],item[8]] for item in cur.execute("SELECT pinglist, interval, remindertitle, remindertext, adaptivelink, channel, emoji, thumbnail, next_time FROM recurring WHERE cast(next_time as integer) <= ?", (now,)).fetchall()]

        if len(reminder_list) == 0:
            return

        i = 0
        for item in reminder_list:

            if item[1].strip().lower() == "blocked":
                print("Skipping blocked recurring reminder.")
                continue

            i += 1 # limit this to 5 for this loop
            if i > 5:
                print("pausing...")
                return

            await asyncio.sleep(1)

            # PARSE DB INFORMATION

            try:
                ping_list = [int(x.strip()) for x in item[0].split(",") if util.represents_integer(x.strip())]
                time_interval = item[1].strip()
                title = util.cleantext(item[2].strip())
                remindertext = await util.customtextparse(util.cleantext(item[3].strip()),"user") # the "user" would normally be a userid-string, but here we just don't pass it
                adaptive_link = item[4].strip()
                channel_id = int(item[5].strip())
                emoji_string = item[6].strip().lower()
                thumbnail = item[7].strip()
                this_time = int(item[8].strip())
            except Exception as e:
                print(f"Error while parsing recurring reminder:", e)
                content = "Error with " + str(item[1]) + " recurring reminder.```" + str(item[2])[:500] + f"```Error message:```{e}```This recurring reminder will be blocked from future execution."
                await self.timeloop_notification("Recurring Reminder", content, False)
                await self.block_recc_reminder(item[0],item[1],item[2],item[3],item[4],item[5],item[6],item[7])
                continue

            # FETCH CHANNEL
            
            try:
                channel = self.bot.get_channel(channel_id) 
            except Exception as e:
                print(f"Error while trying to fetch channel for recurring reminder:", e)
                content = f"Error with channel ID {channel_id}, i.e. channel <#{channel_id}>\nError message:```{e}```This recurring reminder will be blocked from future execution."
                await self.timeloop_notification("Recurring Reminder", content, False)
                await self.block_recc_reminder(item[0],item[1],item[2],item[3],item[4],item[5],item[6],item[7])
                continue

            # PARSE LINK AND EMOJI

            try:
                adapted_link = util.adapt_link(adaptive_link)

                if emoji_string == "":
                    emoji = ""
                elif emoji_string in [str(x) for x in self.bot.emojis]:
                    emoji = emoji_string
                else:
                    emoji = util.emoji(emoji_string)
            except Exception as e:
                print("Error in Link&Emoji parse section in recurring reminder:", e)
                content = f"Error with parsing link and text:```{e}```This recurring reminder will be blocked from future execution."
                await self.timeloop_notification("Recurring Reminder", content, False)
                await self.block_recc_reminder(item[0],item[1],item[2],item[3],item[4],item[5],item[6],item[7])
                continue

            # SEND FIRST MESSAGE

            if len(ping_list) > 0 and self.reminders_enabled():
                try:
                    firstmessage = "Reminder!"
                    for userid in ping_list:
                        firstmessage += f" <@{userid}>"

                    firstmessage += " " + emoji

                    await channel.send(firstmessage)
                except Exception as e:
                    print(f"Error while trying to send pings for recurring reminder:", e)
                    content = f"Error while trying to send pings to " + ', '.join([f"<#{str(x)}> (id: {str(x)})" for x in ping_list]) + f"\nError message:```{e}```This recurring reminder will be blocked from future execution."
                    await self.timeloop_notification("Recurring Reminder", content, False)
                    await self.block_recc_reminder(item[0],item[1],item[2],item[3],item[4],item[5],item[6],item[7])
                    continue

            # SEND SECOND MESSAGE

            try:
                if adapted_link == "":
                    embed=discord.Embed(title=title, description=remindertext, color=0xd30000)
                else:
                    embed=discord.Embed(title=title, url=adapted_link, description=remindertext, color=0xd30000)
                if thumbnail != "":
                    embed.set_thumbnail(url=thumbnail)
                if this_time < now - 24*60*60: # old reminder
                    if this_time < now - 7*24*60*60: # very old in fact
                        specify = " very"
                    else:
                        specify = "n"
                    embed.set_footer(text=f"This is a{specify} old reminder that was still stuck in db memory.")
                await channel.send(embed=embed)
            except Exception as e:
                print(f"Error while trying to send recurring reminder:", e)
                content = f"Error while trying to send recurring reminder embed.\nError message:```{e}```This recurring reminder will be blocked from future execution."
                await self.timeloop_notification("Recurring Reminder", content, False)
                continue

            # UPDATE ITEM IN TABLE

            try:
                next_time = this_time + util.reccuring_time_to_seconds(time_interval, str(this_time))
            except Exception as e:
                content = f"Error while trying to compute next reminding time:```{e}```This recurring reminder will be blocked from future execution."
                await self.timeloop_notification("Recurring Reminder", content, False)
                await self.block_recc_reminder(item[0],item[1],item[2],item[3],item[4],item[5],item[6],item[7])
                continue

            i = 0
            while next_time < now:
                i += 1
                next_time = next_time + util.reccuring_time_to_seconds(time_interval, str(next_time))
                if i > 1000:
                    print("Error: Something might be wrong with the next_time assignment loop in recc_reminders(), it looped over a thousand times.")
                    await self.timeloop_notification("Recurring Reminder", f"Potentially very old reminder. Function trying to find next appropriate date looped over a thousand times and was halted. Please review the recurring reminder entry with title {title}.", False)
                    next_time = now + util.reccuring_time_to_seconds("yearly", str(now))

            cur.execute("UPDATE recurring SET next_time = ? WHERE pinglist = ? AND interval = ? AND remindertitle = ? AND remindertext = ? AND adaptivelink = ? AND channel = ? AND emoji = ? AND thumbnail = ?", (str(next_time),item[0],item[1],item[2],item[3],item[4],item[5],item[6],item[7]))
            con.commit()
        await util.changetimeupdate()



    async def block_recc_reminder(self, pinglist, interval, remindertitle, remindertext, adaptivelink, channel, emoji, thumbnail):
        """in case an error happens in recc_reminders() the reminder gets blocked,
        so the reminder doesn't trigger every minute over and over"""
        con = sqlite3.connect(f'databases/timetables.db')
        cur = con.cursor()
        cur.execute("UPDATE recurring SET interval = ? WHERE pinglist = ? AND interval = ? AND remindertitle = ? AND remindertext = ? AND adaptivelink = ? AND channel = ? AND emoji = ? AND thumbnail = ?", ("blocked",pinglist,interval,remindertitle,remindertext,adaptivelink,channel,emoji,thumbnail))
        con.commit()
        await util.changetimeupdate()



    async def unmuting(self):
        # FETCH DATA FROM DATABASE

        con = sqlite3.connect(f'databases/timetables.db')
        cur = con.cursor()
        now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())
        reminder_list_pre = [[item[0],item[1],item[2]] for item in cur.execute("SELECT userid, utc_timestamp, role_id_list FROM timeout").fetchall()]
        
        if len(reminder_list_pre) == 0:
            return

        reminder_list = []
        for item in reminder_list_pre:
            utc_timestamp = item[1]
            if util.represents_integer(utc_timestamp) and int(utc_timestamp) <= now:
                reminder_list.append(item)
        if len(reminder_list) == 0:
            return

        for item in reminder_list[:20]: # limit to 20

            await asyncio.sleep(1)

            # PARSE DATABASE INFORMATION

            try:
                user_id = int(item[0])
                utc_timestamp = int(item[1])
                role_id_liststr = item[2].strip()
                role_id_list = role_id_liststr.replace("[","").replace("]","").replace(" ","").split(",")
                while '' in role_id_list:
                    role_id_list.remove('')
            except Exception as e:
                print(f"Error while trying to parse timeout data in __timeloops__.unmuting():", e)
                await self.timeloop_notification("Auto-Unmute", f"Error while trying to fetch guild object in __timeloops__.unmuting().\nError message:```{e}```Unmuting <@{user_id}> was cancelled. Please unmute manually.", False)
                await self.remove_from_timeout_db(user_id)
                continue

            # FETCHING GUILD OBJECT

            try:
                try:
                    conB = sqlite3.connect(f'databases/botsettings.db')
                    curB = conB.cursor()
                    botsettings_mainserver_list = [item[0] for item in curB.execute("SELECT value FROM botsettings WHERE name = ?", ("main server id",)).fetchall()]
                    server_id = int(botsettings_mainserver_list[0])
                except:
                    try:
                        server_id = int(os.getenv("guild_id"))
                    except:
                        raise ValueError("no valid guild id provided")


                server = self.bot.get_guild(server_id)
                if server is None:
                    server = await self.bot.fetch_guild(server_id)
                    if server is None:
                        raise ValueError("bot.fetch_guild(<server_id>) returned None")
            except Exception as e:
                print(f"Error while trying to fetch guild in __timeloops__.unmuting():", e)
                await self.timeloop_notification("Auto-Unmute", f"Error while trying to parse timeout data in __timeloops__.unmuting().\nError message:```{e}```Unmuting <@{user_id}> was cancelled. Please unmute manually.", False)
                await self.remove_from_timeout_db(user_id)
                continue

            # FETCH MEMBER OBJECT

            try:
                the_member = server.get_member(user_id)
            except Exception as e:
                print(f'Error while trying to fetch member in __timeloops__.unmuting(): {e}')
                await self.timeloop_notification("Auto-Unmute", f"Error while trying to fetch member in __timeloops__.unmuting().\nError message:```{e}```Unmuting <@{user_id}> was cancelled. Please unmute manually? Perhaps they aren't on this server anymore tho.", False)
                await self.remove_from_timeout_db(user_id)
                continue

            # FETCHING TIMEOUT ROLE OBJECT

            try:
                conB = sqlite3.connect(f'databases/botsettings.db')
                curB = conB.cursor()
                timeoutrole_id = int([item[0] for item in curB.execute("SELECT role_id FROM specialroles WHERE name = ?", ("timeout role",)).fetchall()][0])
                for role in server.roles:
                    if role.id == timeoutrole_id:
                        timeout_role = role
                        break 
                else:
                    raise ValueError(f"no role on {server.name} with ID {timeoutrole_id}")
            except Exception as e:
                print(f"Error while trying to find Timeout role: {e}")
                await self.timeloop_notification("Auto-Unmute", f"Error while trying to find Timeout role.\nError message:```{e}```Unmuting <@{user_id}> was cancelled. Please unmute manually.", False)
                await self.remove_from_timeout_db(user_id)
                continue

            if timeout_role not in the_member.roles:
                emoji = util.emoji("think")
                await self.timeloop_notification("Auto-Unmute", f"User <@{user_id}> was already unmuted. {emoji}\nNo futher action required ig.", False)
                await self.remove_from_timeout_db(user_id)
                continue

            # FETCHING OTHER ROLE OBJECTS

            try:
                old_roles_list = []
                all_roles = [r for r in server.roles]
                for role_id in role_id_list:
                    if int(role_id) not in [server.id, timeoutrole_id]: #ignore @everyone role and timeout role
                        try:
                            r_id = int(role_id)
                            for role in all_roles:
                                if role.id == r_id:
                                    old_roles_list.append(role)
                                    break 
                            else:
                                print(f"Warning in __timeloops__.unmuting(): role with id {role_id} not found")
                        except:
                            print(f"Warning in __timeloops__.unmuting(): role {role_id} has faulty id")
            except Exception as e:
                print(f"Error while trying to fetch user roles pre-timeout: {e}")
                await self.timeloop_notification("Auto-Unmute", f"Error while trying to handle roles.\nError message:```{e}```User <@{user_id}> was cancelled. Please unmute manually.", False)
                await self.remove_from_timeout_db(user_id)
                continue

            # END TIMEOUT: SWAPPING ROLES

            try:
                await the_member.edit(roles=old_roles_list)
            except:
                await the_member.remove_roles(timeout_role)
                if len(old_roles_list) > 0:
                    for r in old_roles_list:
                        if r.id != ctx.guild.id: #ignore @everyone role
                            try:
                                await the_member.add_roles(r)
                            except:
                                print(f"Error with: {r}, {r.id}")
                                
            emoji = util.emoji("unleashed_mild")
            await asyncio.sleep(0.5)
            await self.timeloop_notification("Auto-Unmute: Timeout ended", f"Unmuted <@{user_id}>. {emoji}", True)
            await self.remove_from_timeout_db(user_id)



    async def remove_from_timeout_db(self, user_id):
        try:
            con = sqlite3.connect(f'databases/timetables.db')
            cur = con.cursor()
            cur.execute("DELETE FROM timeout WHERE userid = ?", (str(user_id),))
            con.commit()
            await util.changetimeupdate()
        except Exception as e:
            print(f"Error while trying to remove user {user_id} from timeout database: {e}")



    #######################################################################################################################################################
    #######################################################################################################################################################
    #######################################################################################################################################################

    # calendar stuff

    async def calendar_notif(self):
        pass
        # under construction



    # lastfm scrobble update

    async def lastfm_update(self):
        # first check if auto-update is enabled
        conB = sqlite3.connect('databases/botsettings.db')
        curB = conB.cursor()
        scrobblefeature_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("scrobbling functionality",)).fetchall()]
        scrobbleautoupdate_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("scrobbling update automation",)).fetchall()]

        if len(scrobbleautoupdate_list) == 0 or len(scrobblefeature_list) == 0:
            print("No scrobble updating setting in database. Use update command first.")
            return

        scrobblefeature = scrobblefeature_list[0].lower().strip()
        scrobbleautoupdate = scrobbleautoupdate_list[0].lower().strip()

        if scrobblefeature != "on" or scrobbleautoupdate != "on":
            print("No scrobble auto-updating: Either scrobbling functionality or scrobbling auto update are disabled.")
            return

        # check if update pipeline is in use or free

        for _ in range(5):
            cooldown_list = util.check_active_scrobbleupdate()
            if len(cooldown_list) > 0:
                print(f"Update pipe in use: {cooldown_list}. | Waiting 2 seconds...")
                await asyncio.sleep(2)
            else:
                print("pipe clear: received go")
                break
        else:
            print("Skipping scrobble auto-update. Update pipe in use:", cooldown_list)
            return

        util.block_scrobbleupdate(None)

        # do the updating
        try:
            conNP = sqlite3.connect('databases/npsettings.db')
            curNP = conNP.cursor()
            lfm_list = [[item[0],item[1],item[2]] for item in curNP.execute("SELECT id, lfm_name, details FROM lastfm").fetchall()]

            member_id_list = []
            for guild in self.bot.guilds:
                for member in guild.members:
                    if member.id not in member_id_list:
                        member_id_list.append(member.id)

            for item in lfm_list:
                try:
                    user_id = int(item[0])
                    lfm_name = item[1]
                    status = item[2] # ignore: scrobble_banned ; # proceed with: NULL, "", inactive, wk_banned, crown_banned

                    if type(status) == str and status.startswith("scrobble_banned"):
                        continue
                except Exception as e:
                    print("Error in scrobble update time loop:", e)
                    continue

                if user_id not in member_id_list:
                    continue

                allow_from_scratch = False
                try:
                    await util.scrobble_update(lfm_name, allow_from_scratch, self.bot)
                except Exception as e:
                    print(f"Error while fetching info from {lfm_name}: {e}")
                    try:
                        h = datetime.datetime.utcnow().hour
                        if h in [0]:
                            await self.timeloop_notification("Scrobble Update", f"Error while trying to update newest scrobbles of [{lfm_name}](https://www.last.fm/user/{lfm_name})```{e}```(semi-caught)", False)
                    except Exception as e:
                        print("Another error:", e)

                #await asyncio.sleep(1)

            util.unblock_scrobbleupdate()
            print("finished updating scrobble data")

        except Exception as e:
            util.unblock_scrobbleupdate()
            await self.timeloop_notification("Scrobble Update", f"```{e}```", False)



    # check for users without any role

    async def missed_welcome_check(self):
        # triggers if access wall or auto-role is enabled, but a user does not have any role
        pass
        # under construction



    #######################################################################################################################################################
    #######################################################################################################################################################
    #######################################################################################################################################################

    # exchange rate stuff



    async def load_exchangerate_key(self):
        try:
            api_key = os.getenv("exchangerate_key")
        except:
            raise ValueError("Failed to fetch exchangerate api key")
            return
        return api_key



    async def update_recency_check(self):
        await asyncio.sleep(5) # give some leeway in case ExchangeRate-API had few seconds of delay

        con = sqlite3.connect('databases/exchangerate.db')
        cur = con.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS USDexchangerate (code text, value text, currency text, country text, last_updated text, time_stamp text)''')
        timestamps = [[item[0],item[1]] for item in cur.execute("SELECT last_updated, time_stamp FROM USDexchangerate").fetchall()]

        if len(timestamps) == 0:
            return True

        utc_now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds()) 
        updated_in_past_24h = False

        for item in timestamps:
            unix_secs = int(item[1])
            if unix_secs + 24*60*60 > utc_now:
                updated_in_past_24h = True
                readable_time = item[0]
                print(f"Last ExchangeRate update was already on {readable_time}. Exiting update attempt.")
                break

        if updated_in_past_24h:
            return False
        else:
            return True



    async def update_currency(self):

        # INITIALISING LOGIN DATA

        try:
            api_key = await self.load_exchangerate_key()
        except:
            message = "Error while fetching keys for ExchangeRate-API."
            success = False
            return message, success

        # CHECKING WHETHER RECENTLY UPDATED ALREADY

        try:
            do_update = await self.update_recency_check()
            if not do_update:
                message = "ExchangeRate database was updated recently enough."
                success = False
                return message, success
        except Exception as e:
            message = f"Error while trying to run update_recency_check() for ExchangaRate: {e}"
            success = False
            return message, success

        # FETCHING INFORMATION

        try:
            url = f'https://v6.exchangerate-api.com/v6/{api_key}/latest/USD'

            response = requests.get(url)
            data = response.json()
            connectionresult = data["result"]

            errormessage = ""

            if connectionresult.lower() != "success":
                message = "Error with fetched data from ExchangeRate-API."
                success = False
                return message, success

        except Exception as e:
            print("Error while trying to connect to ExchangeRate-API:", e)
            message = "Error while trying to connect to ExchangeRate-API."
            success = False
            return message, success

        # PARSING INFORMATION

        try:
            update_time = str(data['time_last_update_utc'])
            update_time_stamp = str(data['time_last_update_unix'])
            #print(data['base_code'])

            rates = data['conversion_rates']
            keysList = list(rates.keys())

            con = sqlite3.connect('databases/exchangerate.db')
            cur = con.cursor()
            cur.execute('''CREATE TABLE IF NOT EXISTS USDexchangerate (code text, value text, currency text, country text, last_updated text, time_stamp text)''')
            known_currencies = [item[0] for item in cur.execute("SELECT code FROM USDexchangerate").fetchall()]
        except Exception as e:
            message = f"Error while trying to decipher data from ExchangeRate-API:\n{e}"
            success = False
            return message, success

        # INSERTING DATA INTO DATABASE

        try:
            names_and_countries = [["AED","UAE Dirham","United Arab Emirates"],["AFN","Afghan Afghani","Afghanistan"],["ALL","Albanian Lek","Albania"],["AMD","Armenian Dram","Armenia"],["ANG","Netherlands Antillian Guilder","Netherlands Antilles"],["AOA","Angolan Kwanza","Angola"],["ARS","Argentine Peso","Argentina"],["AUD","Australian Dollar","Australia"],["AWG","Aruban Florin","Aruba"],["AZN","Azerbaijani Manat","Azerbaijan"],["BAM","Bosnia and Herzegovina Mark","Bosnia and Herzegovina"],["BBD","Barbados Dollar","Barbados"],["BDT","Bangladeshi Taka","Bangladesh"],["BGN","Bulgarian Lev","Bulgaria"],["BHD","Bahraini Dinar","Bahrain"],["BIF","Burundian Franc","Burundi"],["BMD","Bermudian Dollar","Bermuda"],["BND","Brunei Dollar","Brunei"],["BOB","Bolivian Boliviano","Bolivia"],["BRL","Brazilian Real","Brazil"],["BSD","Bahamian Dollar","Bahamas"],["BTN","Bhutanese Ngultrum","Bhutan"],["BWP","Botswana Pula","Botswana"],["BYN","Belarusian Ruble","Belarus"],["BZD","Belize Dollar","Belize"],["CAD","Canadian Dollar","Canada"],["CDF","Congolese Franc","Democratic Republic of the Congo"],["CHF","Swiss Franc","Switzerland"],["CLP","Chilean Peso","Chile"],["CNY","Chinese Renminbi","China"],["COP","Colombian Peso","Colombia"],["CRC","Costa Rican Colon","Costa Rica"],["CUP","Cuban Peso","Cuba"],["CVE","Cape Verdean Escudo","Cape Verde"],["CZK","Czech Koruna","Czech Republic"],["DJF","Djiboutian Franc","Djibouti"],["DKK","Danish Krone","Denmark"],["DOP","Dominican Peso","Dominican Republic"],["DZD","Algerian Dinar","Algeria"],["EGP","Egyptian Pound","Egypt"],["ERN","Eritrean Nakfa","Eritrea"],["ETB","Ethiopian Birr","Ethiopia"],["EUR","Euro","European Union"],["FJD","Fiji Dollar","Fiji"],["FKP","Falkland Islands Pound","Falkland Islands"],["FOK","Faroese Króna","Faroe Islands"],["GBP","Pound Sterling","United Kingdom"],["GEL","Georgian Lari","Georgia"],["GGP","Guernsey Pound","Guernsey"],["GHS","Ghanaian Cedi","Ghana"],["GIP","Gibraltar Pound","Gibraltar"],["GMD","Gambian Dalasi","The Gambia"],["GNF","Guinean Franc","Guinea"],["GTQ","Guatemalan Quetzal","Guatemala"],["GYD","Guyanese Dollar","Guyana"],["HKD","Hong Kong Dollar","Hong Kong"],["HNL","Honduran Lempira","Honduras"],["HRK","Croatian Kuna","Croatia"],["HTG","Haitian Gourde","Haiti"],["HUF","Hungarian Forint","Hungary"],["IDR","Indonesian Rupiah","Indonesia"],["ILS","Israeli New Shekel","Israel"],["IMP","Manx Pound","Isle of Man"],["INR","Indian Rupee","India"],["IQD","Iraqi Dinar","Iraq"],["IRR","Iranian Rial","Iran"],["ISK","Icelandic Króna","Iceland"],["JEP","Jersey Pound","Jersey"],["JMD","Jamaican Dollar","Jamaica"],["JOD","Jordanian Dinar","Jordan"],["JPY","Japanese Yen","Japan"],["KES","Kenyan Shilling","Kenya"],["KGS","Kyrgyzstani Som","Kyrgyzstan"],["KHR","Cambodian Riel","Cambodia"],["KID","Kiribati Dollar","Kiribati"],["KMF","Comorian Franc","Comoros"],["KRW","South Korean Won","South Korea"],["KWD","Kuwaiti Dinar","Kuwait"],["KYD","Cayman Islands Dollar","Cayman Islands"],["KZT","Kazakhstani Tenge","Kazakhstan"],["LAK","Lao Kip","Laos"],["LBP","Lebanese Pound","Lebanon"],["LKR","Sri Lanka Rupee","Sri Lanka"],["LRD","Liberian Dollar","Liberia"],["LSL","Lesotho Loti","Lesotho"],["LYD","Libyan Dinar","Libya"],["MAD","Moroccan Dirham","Morocco"],["MDL","Moldovan Leu","Moldova"],["MGA","Malagasy Ariary","Madagascar"],["MKD","Macedonian Denar","North Macedonia"],["MMK","Burmese Kyat","Myanmar"],["MNT","Mongolian Tögrög","Mongolia"],["MOP","Macanese Pataca","Macau"],["MRU","Mauritanian Ouguiya","Mauritania"],["MUR","Mauritian Rupee","Mauritius"],["MVR","Maldivian Rufiyaa","Maldives"],["MWK","Malawian Kwacha","Malawi"],["MXN","Mexican Peso","Mexico"],["MYR","Malaysian Ringgit","Malaysia"],["MZN","Mozambican Metical","Mozambique"],["NAD","Namibian Dollar","Namibia"],["NGN","Nigerian Naira","Nigeria"],["NIO","Nicaraguan Córdoba","Nicaragua"],["NOK","Norwegian Krone","Norway"],["NPR","Nepalese Rupee","Nepal"],["NZD","New Zealand Dollar","New Zealand"],["OMR","Omani Rial","Oman"],["PAB","Panamanian Balboa","Panama"],["PEN","Peruvian Sol","Peru"],["PGK","Papua New Guinean Kina","Papua New Guinea"],["PHP","Philippine Peso","Philippines"],["PKR","Pakistani Rupee","Pakistan"],["PLN","Polish Złoty","Poland"],["PYG","Paraguayan Guaraní","Paraguay"],["QAR","Qatari Riyal","Qatar"],["RON","Romanian Leu","Romania"],["RSD","Serbian Dinar","Serbia"],["RUB","Russian Ruble","Russia"],["RWF","Rwandan Franc","Rwanda"],["SAR","Saudi Riyal","Saudi Arabia"],["SBD","Solomon Islands Dollar","Solomon Islands"],["SCR","Seychellois Rupee","Seychelles"],["SDG","Sudanese Pound","Sudan"],["SEK","Swedish Krona","Sweden"],["SGD","Singapore Dollar","Singapore"],["SHP","Saint Helena Pound","Saint Helena"],["SLL","Old Sierra Leonean Leone","Sierra Leone"],["SLE","Sierra Leonean Leone","Sierra Leone"],["SOS","Somali Shilling","Somalia"],["SRD","Surinamese Dollar","Suriname"],["SSP","South Sudanese Pound","South Sudan"],["STN","São Tomé and Príncipe Dobra","São Tomé and Príncipe"],["SYP","Syrian Pound","Syria"],["SZL","Eswatini Lilangeni","Eswatini"],["THB","Thai Baht","Thailand"],["TJS","Tajikistani Somoni","Tajikistan"],["TMT","Turkmenistan Manat","Turkmenistan"],["TND","Tunisian Dinar","Tunisia"],["TOP","Tongan Pa'anga","Tonga"],["TRY","Turkish Lira","Turkey"],["TTD","Trinidad and Tobago Dollar","Trinidad and Tobago"],["TVD","Tuvaluan Dollar","Tuvalu"],["TWD","New Taiwan Dollar","Taiwan"],["TZS","Tanzanian Shilling","Tanzania"],["UAH","Ukrainian Hryvnia","Ukraine"],["UGX","Ugandan Shilling","Uganda"],["USD","United States Dollar","United States"],["UYU","Uruguayan Peso","Uruguay"],["UZS","Uzbekistani So'm","Uzbekistan"],["VES","Venezuelan Bolívar Soberano","Venezuela"],["VND","Vietnamese Đồng","Vietnam"],["VUV","Vanuatu Vatu","Vanuatu"],["WST","Samoan Tālā","Samoa"],["XAF","Central African CFA Franc","CEMAC"],["XCD","East Caribbean Dollar","Organisation of Eastern Caribbean States"],["XDR","Special Drawing Rights","International Monetary Fund"],["XOF","West African CFA franc","CFA"],["XPF","CFP Franc","Collectivités d'Outre-Mer"],["YER","Yemeni Rial","Yemen"],["ZAR","South African Rand","South Africa"],["ZMW","Zambian Kwacha","Zambia"],["ZWL","Zimbabwean Dollar","Zimbabwe"]]
            
            for currency in keysList:
                exchange = rates[currency]
                if currency in known_currencies:
                    cur.execute("UPDATE USDexchangerate SET value = ?, last_updated = ?, time_stamp = ? WHERE code = ?", (exchange, update_time, update_time_stamp, currency))
                    con.commit()
                else:
                    for item in names_and_countries:
                        if item[0].upper() == currency.upper():
                            name = item[1]
                            country = item[2]
                            break
                    else:
                        name = ""
                        country = ""
                        print(f"Warning: empty name and country passed to database. Issue with currency {currency.upper()}.")

                    cur.execute("INSERT INTO USDexchangerate VALUES (?, ?, ?, ?, ?, ?)", (currency, exchange, name, country, update_time, update_time_stamp))
                    con.commit()
            await util.changetimeupdate()

            emoji = util.emoji("note")
            message = f"Updated currency exchange rates {emoji}.\nData from {update_time}."
            success = True
            return message, success 

        except Exception as e:
            message = f"Error while trying to insert ExchangeRate data into database:\n{e}"
            success = False
            return message, success     


    #######################################################################################################################################################
    #######################################################################################################################################################
    #######################################################################################################################################################

    # emoji stuff

    async def update_emoji(self):
        """check if the emoji in botsettings.db and roles.db are still usable,
        (also update emoji names in npsettings.db, botsettings.db and roles.db)
        ++ calendar
        """

        # GET CUSTOM EMOJI DICTIONARY

        custom_emoji_dict = {}

        for emoji in self.bot.emojis:
            if str(emoji).startswith("<") and str(emoji).endswith(">") and str(emoji).count(":") == 2:
                parts = str(emoji).replace("<","").replace(">","").split(":")
                animated = parts[0].strip()
                emoji_name = parts[1].strip()
                emoji_id = parts[2].strip()

                custom_emoji_dict[animated+emoji_id] = str(emoji)
            else:
                print("Error with", str(emoji))

        # UPDATE EMOJI IN BOTSETTINGS

        conB = sqlite3.connect('databases/botsettings.db')
        curB = conB.cursor()

        botsettings_emoji = [[item[0],item[1]] for item in curB.execute("SELECT call, purpose FROM emojis WHERE call != ?", ("",)).fetchall()]

        faulty_botsettings_emoji = []
        removed_botsettings_emoji = []

        for emoji in [x[0] for x in botsettings_emoji]:
            if emoji in [str(x) for x in self.bot.emojis]:
                pass # is custom emoji
            elif emoji in UNICODE_EMOJI['en']:
                pass # is unicoded emoji
            elif emoji in list(UNICODE_EMOJI['en'].values()):
                pass # is emoji name
            else:
                faulty_botsettings_emoji.append(emoji)

        for emoji in faulty_botsettings_emoji:
            if emoji.startswith("<") and emoji.endswith(">") and emoji.count(":") == 2:
                parts = emoji.replace("<","").replace(">","").split(":")
                animated = parts[0].strip()
                emoji_name = parts[1].strip()
                emoji_id = parts[2].strip()
                emoji_a_id = animated + emoji_id

                if emoji_a_id in custom_emoji_dict:
                    emoji_new = custom_emoji_dict[emoji_a_id]
                    curB.execute("UPDATE emojis SET call = ? WHERE call = ?", (emoji_new, emoji))
                    continue

            curB.execute("UPDATE emojis SET call = ? WHERE call = ?", ("", emoji))
            removed_botsettings_emoji.append(emoji)
        conB.commit()

        # UPDATE EMOJI IN ROLES

        conR = sqlite3.connect('databases/roles.db')
        curR = conR.cursor()

        role_emoji = [[item[0],item[1]] for item in curR.execute("SELECT details, id FROM roles WHERE details != ?", ("",)).fetchall()]

        faulty_role_emoji = []
        removed_role_emoji = []

        for emoji in [x[0] for x in role_emoji]:
            if emoji in [str(x) for x in self.bot.emojis]:
                pass # is custom emoji
            elif emoji in UNICODE_EMOJI['en']:
                pass # is unicoded emoji
            elif emoji in list(UNICODE_EMOJI['en'].values()):
                pass # is emoji name
            else:
                faulty_role_emoji.append(emoji)

        for emoji in faulty_role_emoji:
            if emoji.startswith("<") and emoji.endswith(">") and emoji.count(":") == 2:
                parts = emoji.replace("<","").replace(">","").split(":")
                animated = parts[0].strip()
                emoji_name = parts[1].strip()
                emoji_id = parts[2].strip()
                emoji_a_id = animated + emoji_id

                if emoji_a_id in custom_emoji_dict:
                    emoji_new = custom_emoji_dict[emoji_a_id]
                    curR.execute("UPDATE roles SET details = ? WHERE details = ?", (emoji_new, emoji))
                    continue

            curR.execute("UPDATE roles SET details = ? WHERE details = ?", ("", emoji))
            removed_role_emoji.append(emoji)
        conR.commit()

        # UPDATE EMOJI IN NPSETTINGS

        conNP = sqlite3.connect('databases/npsettings.db')
        curNP = conNP.cursor()

        np_reactions = [[item[0],item[1],item[2],item[3],item[4]] for item in curNP.execute("SELECT emoji1, emoji2, emoji3, emoji4, emoji5 FROM npreactions").fetchall()]
        np_react_list = []

        for react_set in np_reactions:
            for react in react_set:
                if react is None or react.strip() == "":
                    pass
                else:
                    np_react_list.append(react)

        np_react_list = list(dict.fromkeys(np_react_list))

        faulty_np_emoji = []
        removed_np_emoji = []

        for emoji in np_react_list:
            if emoji in [str(x) for x in self.bot.emojis]:
                pass # is custom emoji
            elif emoji in UNICODE_EMOJI['en']:
                pass # is unicoded emoji
            elif emoji in list(UNICODE_EMOJI['en'].values()):
                pass # is emoji name
            else:
                faulty_np_emoji.append(emoji)

        for emoji in faulty_np_emoji:
            if emoji.startswith("<") and emoji.endswith(">") and emoji.count(":") == 2:
                parts = emoji.replace("<","").replace(">","").split(":")
                animated = parts[0].strip()
                emoji_name = parts[1].strip()
                emoji_id = parts[2].strip()
                emoji_a_id = animated + emoji_id

                if emoji_a_id in custom_emoji_dict:
                    emoji_new = custom_emoji_dict[emoji_a_id]
                    curNP.execute("UPDATE npreactions SET emoji1 = ? WHERE emoji1 = ?", (emoji_new, emoji))
                    curNP.execute("UPDATE npreactions SET emoji2 = ? WHERE emoji2 = ?", (emoji_new, emoji))
                    curNP.execute("UPDATE npreactions SET emoji3 = ? WHERE emoji3 = ?", (emoji_new, emoji))
                    curNP.execute("UPDATE npreactions SET emoji4 = ? WHERE emoji4 = ?", (emoji_new, emoji))
                    curNP.execute("UPDATE npreactions SET emoji5 = ? WHERE emoji5 = ?", (emoji_new, emoji))
                    continue

            curNP.execute("UPDATE npreactions SET emoji1 = ? WHERE emoji1 = ?", ("", emoji))
            curNP.execute("UPDATE npreactions SET emoji2 = ? WHERE emoji2 = ?", ("", emoji))
            curNP.execute("UPDATE npreactions SET emoji3 = ? WHERE emoji3 = ?", ("", emoji))
            curNP.execute("UPDATE npreactions SET emoji4 = ? WHERE emoji4 = ?", ("", emoji))
            curNP.execute("UPDATE npreactions SET emoji5 = ? WHERE emoji5 = ?", ("", emoji))
            removed_np_emoji.append(emoji)
        conNP.commit()

        await util.changetimeupdate()

        # BOTSPAM NOTIFICATION

        if len(removed_botsettings_emoji) == 0 and len(removed_role_emoji) == 0 and len(removed_np_emoji) == 0:
            all_good = True
        else:
            all_good = False

        if not all_good:
            title = "Removed emojis that are no longer usable"
            message = ""

            if len(removed_botsettings_emoji) > 0:
                message += "**bot settings emoji purposes**\n"

                for emoji in removed_botsettings_emoji:
                    message += emoji + " :: "

                    for emote in botsettings_emoji:
                        if emote[0] == emoji:
                            message += "`" + emote[1] + "`, "

                    if message.endswith(", "):
                        message = message[:-2]
                    else:
                        message += "?"
                    message += "\n"
                message += "\n"

            if len(removed_role_emoji) > 0:
                message += "**role database emoji**\n"

                for emoji in removed_role_emoji:
                    message += emoji + " :: "

                    for emote in role_emoji:
                        if emote[0] == emoji:
                            message += f"<@{emote[1]}>, "

                    if message.endswith(", "):
                        message = message[:-2]
                    else:
                        message += "?"
                    message += "\n"
                message += "\n"

            if len(removed_np_emoji) > 0:
                message += "**np react emoji**\n"

                for emoji in removed_np_emoji:
                    message += emoji + ", "

                    if message.endswith(", "):
                        message = message[:-2]
                    else:
                        message += "?"
                    message += "\n"
                message += "\n"

            await self.timeloop_notification(title, message.strip(), all_good)
        else:
            print("Successful emoji check: all good!")



    # inactivity stuff

    async def inactivity_filtering(self):

        # FETCH INACTIVITY FILTER SETTINGS

        conB = sqlite3.connect('databases/botsettings.db')
        curB = conB.cursor()

        inactivityfilter_setting = [[item[0], item[1], item[2]] for item in curB.execute("SELECT value, details, etc FROM serversettings WHERE name = ?", ("inactivity filter", )).fetchall()]

        if len(inactivityfilter_setting) == 0 or inactivityfilter_setting[0][0].lower() != "on":
            print("Timeloop notification: Inactivity filter is set `off`. No action was taken.")
            return

        days_string = inactivityfilter_setting[0][1]
        if util.represents_integer(days_string):
            days = int(days_string)
            if days < 90:
                days = 90
        else:
            days = 90

        # FETCH SERVER

        try:
            botsettings_mainserver_list = [item[0] for item in curB.execute("SELECT value FROM botsettings WHERE name = ?", ("main server id",)).fetchall()]
            server_id = int(botsettings_mainserver_list[0])
        except:
            try:
                server_id = int(os.getenv("guild_id"))
            except:
                print("Error: no valid guild id provided")
                return

        server = self.bot.get_guild(server_id)
        if server is None:
            server = await self.bot.fetch_guild(server_id)
            if server is None:
                print("bot.fetch_guild(<server_id>) returned None")
                return

        # FETCH ROLE

        inactivityrole_list = [item[0] for item in curB.execute("SELECT role_id FROM specialroles WHERE name = ?", ("inactivity role",)).fetchall()]        
        if len(inactivityrole_list) == 0 or not util.represents_integer(inactivityrole_list[0]):
            print("Error: No inactivity role!")
            return
        else:
            if len(inactivityrole_list) > 1:
                print("Warning: there are multiple inactivity role entries in the database")
            inactivity_role_id = int(inactivityrole_list[0])

        try:
            inactivity_role = server.get_role(inactivity_role_id)
        except Exception as e:
            print("Error:", e)
            print("Error: Faulty inactivity role id!")
            return

        if inactivity_role is None:
            print("Error: Faulty inactivity role id!")
            return

        # CHECK USERS

        now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())

        conUA = sqlite3.connect('databases/useractivity.db')
        curUA = conUA.cursor()
        users_and_times = [[item[0],item[1],item[2]] for item in curUA.execute("SELECT userid, last_active, join_time FROM useractivity").fetchall()]

        new_inactives_mention_list = []
        error_users = []
        error_count = 0
        sleep_count = 0

        for item in users_and_times:
            user_id = item[0]
            last_active = int(item[1])
            join_time = int(item[2])

            if (last_active > now - (days * 24 * 60 * 60)) or (join_time > now - (days * 24 * 60 * 60)):
                continue

            try:
                user = server.get_member(int(user_id))
                if user is None:
                    raise ValueError(f"Error: User object of user with id {user_id} is None.")
            except Exception as e:
                error_count += 1
                error_users.append(f"<@{user_id}>*")
                print("Error with user:", e)
                try: # remove user from database if not a member
                    for member in server.members:
                        if member.id == int(user_id):
                            break
                    else:
                        curUA.execute("DELETE FROM useractivity WHERE userid = ?", (str(user_id),))
                        conUA.commit()
                        print(f"Removed {user.name} (id: {user_id}) from useractivity database")
                except Exception as e:
                    print("Error:", e)
                continue

            if inactivity_role in user.roles:
                # already in inactivity channel
                continue

            user_role_ids = []
            for role in user.roles:
                if role.id != server.id: #ignore @everyone role
                    user_role_ids.append(str(role.id))

            previousroles = ';;'.join(user_role_ids)

            try:
                await user.edit(roles=[inactivity_role])
                #new_inactives_mention_list.append(f"<@{str(user.id)}> ({user.name})")
                new_inactives_mention_list.append(f"<@{str(user.id)}>")
                print(f"{user.name} was deemed inactive")

                try:
                    # NPsettings change to inactive
                    conNP = sqlite3.connect('databases/npsettings.db')
                    curNP = conNP.cursor()
                    lfm_list = [[item[0],item[1]] for item in curNP.execute("SELECT lfm_name, details FROM lastfm WHERE id = ?", (str(user.id),)).fetchall()]

                    if len(lfm_list) > 0:
                        status = lfm_list[0][1]
                        if status is None or status.lower().strip() == "":
                            new_status = "inactive"
                        else:
                            new_status = status.lower().strip() + "_inactive"
                        curNP.execute("UPDATE lastfm SET details = ? WHERE id = ?", (new_status, str(user.id)))
                        conNP.commit()
                except Exception as e:
                    print(f"Error with changing NP settings ({user.name}):", e)
            except Exception as e:
                error_count += 1
                #error_users.append(f"<@{user.id}> ({user.name})")
                error_users.append(f"<@{user.id}>")
                print(f"Error with user {user.name}:", e)
                continue

            curUA.execute("UPDATE useractivity SET previous_roles = ? WHERE userid = ?", (previousroles, str(user_id)))
            conUA.commit()
            sleep_count += 1

        if sleep_count > 0:
            await util.changetimeupdate()
            message = f"Put {sleep_count} user(s) into inactivity channel:\n"
            message += ', '.join(new_inactives_mention_list) + "\n"
            if error_count > 0:
                message += f"Error with {error_count} user(s). These users are probably either higher in role hierarchy than this bot or left the server:\n"
                message += ', '.join(error_users)
            title = "Inactivity Filter"
            await self.timeloop_notification(title, message.strip(), True)


    # clear databases of redundant data

    async def clear_databases(self):
        # robot activity
        conRA = sqlite3.connect('databases/robotactivity.db')
        curRA = conRA.cursor()
        rawreactionembed_list = [[item[0],item[1], util.forceinteger(item[2])] for item in curRA.execute("SELECT channel_id, message_id, utc_timestamp FROM raw_reaction_embeds").fetchall()]
        
        now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())

        for item in rawreactionembed_list:
            channel_id = item[0]
            message_id = item[1]
            utc_timestamp = item[2]

            if utc_timestamp < now - (365 * 24 * 60 * 60):
                curRA.execute("DELETE FROM raw_reaction_embeds WHERE message_id = ? AND channel_id = ?", (str(message_id), str(channel_id)))
        conRA.commit()
        await util.changetimeupdate()






async def setup(bot: commands.bot) -> None:
    await bot.add_cog(
        TimeLoops(bot),
        guilds = [discord.Object(id = int(os.getenv("guild_id")))])