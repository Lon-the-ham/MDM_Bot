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



class TimeLoops(commands.Cog):
    def __init__(self, bot: commands.bot) -> None:
        self.bot = bot
        self.index = 0
        self.minutely_check.start()
        self.hourly_check.start()
        self.update_databases.start()



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
        embed=discord.Embed(title=title, description=message, color=0x000000)
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
        print("before loop")
        con = sqlite3.connect(f'databases/timetables.db')
        cur = con.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS reminders (reminder_id text, username text, userid text, utc_timestamp text, remindertext text, channel text, channel_name text, og_message text, og_time text)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS recurring (reminder_id text, username text, userid text, pinglist text, interval text, next_time text, remindertitle text, remindertext text, adaptivelink text, channel text, channel_name text, thumbnail text, emoji text)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS timeout (username text, userid text, utc_timestamp text, role_id_list text)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS zcounter (num text)''')



    ############### CALENDAR ###########################################################################################################################



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

    @hourly_check.before_loop
    async def before_hourly_check(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(20.4)



    ############### DAILY UPDATE FOR DATABASES ##########################################################################################################



    @tasks.loop(hours=24.0)
    async def update_databases(self):
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

    @update_databases.before_loop
    async def before_update_databases(self):
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
                    emoji = await util.emoji(emoji_string)
            except Exception as e:
                print("Error in Link&Emoji parse section in recurring reminder:", e)
                content = f"Error with parsing link and text:```{e}```This recurring reminder will be blocked from future execution."
                await self.timeloop_notification("Recurring Reminder", content, False)
                await self.block_recc_reminder(item[0],item[1],item[2],item[3],item[4],item[5],item[6],item[7])
                continue

            # SEND FIRST MESSAGE

            if len(ping_list) > 0:
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
                emoji = await util.emoji("think")
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
                                
            emoji = await util.emoji("unleashed_mild")
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

            emoji = await util.emoji("note")
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
        pass 
        # under construction




async def setup(bot: commands.bot) -> None:
    await bot.add_cog(
        TimeLoops(bot),
        guilds = [discord.Object(id = int(os.getenv("guild_id")))])