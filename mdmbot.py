# MAIN PYTHON FILE

import os
import sys
from dotenv import load_dotenv
import datetime
import pytz
import discord
from discord.ext import commands
import asyncio
import sqlite3
from other.utils.utils import Utils as util
import traceback



load_dotenv()
app_id = os.getenv("application_id")
bot_instance = os.getenv("bot_instance")
discord_token = os.getenv("discord_token")
prefix = os.getenv("prefix")
guild_id = int(os.getenv("guild_id"))
bot_channel_id = int(os.getenv("bot_channel_id"))
activity = "loading..."



class YataBot(commands.Bot):
    def __init__(self):
        super().__init__(
            application_id   = app_id,
            case_insensitive = True,
            command_prefix   = prefix,
            help_command     = None,
            intents          = discord.Intents.all()
            )

        self.initial_extensions = [
            "cogs.admin.instance_management",
            "cogs.admin.servermoderation",
            "cogs.admin.settings",
            "cogs.events.eventresponse",
            "cogs.events.timeloops",
            "cogs.general.general_utility",
            "cogs.general.help",
            "cogs.general.shenanigans", 
            #"cogs.general.textedit", ❌
            "cogs.music.exchanges",
            "cogs.music.fm",
            "cogs.music.info",
            "cogs.music.scrobble_utility",
            "cogs.music.scrobble_visualization",
            "cogs.roles.roles",
            "cogs.roles.reactionroles",
            "cogs.userown.memo",
            "cogs.userown.pingterest",
            ]
        self.optional_extensions = ["cogs.sandbox"]


    async def setup_hook(self):
        # loading cogs
        for ext in self.initial_extensions:
            await self.load_extension(ext)

        # loading optional cogs
        for ext in self.optional_extensions:
            try:
                await self.load_extension(ext)
                print("loaded", str(ext))
            except Exception as e:
                print(f"did not load extension {str(ext)}")
                try:
                    if f"Extension '{ext}' raised an error:" in str(traceback.format_exc()):
                        reason = str(traceback.format_exc()).split(f"Extension '{ext}' raised an error:")[-1].strip()
                    else:
                        reason = str(traceback.format_exc()).strip().split("\n")[-1].strip()
                    if reason.endswith(f"discord.ext.commands.errors.ExtensionNotFound: Extension '{ext}' could not be loaded."):
                        pass
                    else:
                        print(f"> {reason}")
                except:
                    pass

        # putting together
        await bot.tree.sync(guild = discord.Object(id = guild_id))


    async def on_ready(self):
        print('logged in as {0.user}'.format(bot))

        try:
            channel = bot.get_channel(bot_channel_id)
            try:
                emoji = util.emoji("smug")
                await channel.send(f'`I haveth logged in` {emoji}')
            except:
                await channel.send(f'`I haveth logged in`')

            # ACTIVITY
            try:
                conA = sqlite3.connect(f'databases/activity.db')
                curA = conA.cursor()
                curA.execute('''CREATE TABLE IF NOT EXISTS activity (name text, value text)''')
                curA.execute('''CREATE TABLE IF NOT EXISTS version (name text, value text)''')
                activity_list = [item[0] for item in curA.execute("SELECT value FROM activity WHERE name = ?", ("activity",)).fetchall()]
                activity = activity_list[0]
                load_settings = True
            except Exception as e:
                load_settings = False
                activity = "inactive"
                print("Error with activity check:", e)

            # VERSION
            version = util.get_version_from_file()
            print(version)
            try:
                version_list = [item[0] for item in curA.execute("SELECT value FROM version WHERE name = ?", ("version",)).fetchall()]
                if len(version_list) == 0:
                    curA.execute("INSERT INTO version VALUES (?, ?)", ("version", version))
                    conA.commit()
                else:
                    curA.execute("UPDATE version SET value = ? WHERE name = ?", (version, "version"))
                    conA.commit()
            except Exception as e:
                print("Error while storing version number.")

            try:
                con = sqlite3.connect(f'databases/botsettings.db')
                cur = con.cursor()
                cur.execute('''CREATE TABLE IF NOT EXISTS botsettings (name text, value text, type text, details text)''')
            except Exception as e:
                print("Error:", e)

            if load_settings:

                # STATUS

                try:
                    status_list = [[item[0],item[1]] for item in cur.execute("SELECT type, value FROM botsettings WHERE name = ?", ("status",)).fetchall()]
                    stat_type = status_list[0][0]
                    stat_name = status_list[0][1]
                    
                    if stat_type in ['c', 'p', 's', 'l', 'w', 'n']:
                        if stat_type == 'c':
                            await self.change_presence(activity=discord.Activity(type=discord.ActivityType.competing, name=stat_name))
                            print(f'set status COMPETING IN {stat_name}')
                        elif stat_type == 'p':
                            await self.change_presence(activity=discord.Game(name=stat_name))
                            print(f'set status PLAYING {stat_name}')
                        elif stat_type == 's':
                            my_twitch_url = "https://www.twitch.tv/mdmbot/home"
                            await self.change_presence(activity=discord.Streaming(name=stat_name, url=my_twitch_url))
                            print(f'set status STREAMING {stat_name}')
                        elif stat_type == 'l':
                            await self.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=stat_name))
                            print(f'set status LISTENING TO {stat_name}')
                        elif stat_type == 'w':
                            await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=stat_name))
                            print(f'set status WATCHING {stat_name}')
                        elif stat_type == 'n':
                            await self.change_presence(activity=None)
                            print('empty status')
                    else:
                        print('first argument was not a valid status type, setting status type WATCHING')
                        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=value))          
                except Exception as e:
                    print(f'Error in loading default status: {e}')

                # REBOOT TIME

                try:
                    reboot_time_str = os.getenv("reboot")
                    if reboot_time_str is None:
                        reboot_time_str = os.getenv("reboot_time")
                    if reboot_time_str is None:
                        reboot_time_str = "none"

                    reboot_value = reboot_time_str.split(" ")[0].strip()

                    if len(reboot_time_str.split(" ")) > 1:
                        reboot_etc = reboot_time_str.split(" ", 1)[1]
                    else:
                        reboot_etc = ""

                    hostdata_reboot_list = [item[0] for item in curA.execute("SELECT value FROM hostdata WHERE name = ?", ("reboot time",)).fetchall()]
                    if len(hostdata_reboot_list) == 0:
                        curA.execute("INSERT INTO hostdata VALUES (?,?,?,?)", ("reboot time", reboot_value, "", reboot_etc))
                        conA.commit()
                        print("Updated hostdata table: reboot time")
                    else:
                        if len(hostdata_reboot_list) > 1:
                            print("Warning: Multiple reboot time entries in activity.db")
                        curA.execute("UPDATE hostdata SET value = ?, etc = ? WHERE name = ?", (reboot_value, reboot_etc, "reboot time"))
                        conA.commit()

                    try:
                        target_hour = util.forceinteger(reboot_value.split(":")[0].strip())
                        target_minute = util.forceinteger(reboot_value.split(":")[1].strip())

                        if target_hour < 10:
                            target_hour_str = "0" + str(target_hour)
                        else:
                            target_hour_str = str(target_hour)

                        if target_minute < 10:
                            target_minute_str = "0" + str(target_minute)
                        else:
                            target_minute_str = str(target_minute)

                        try:
                            if reboot_etc == "":
                                raise ValueError("no timezone set")
                            tz     = pytz.timezone(reboot_etc)
                            dt_now = datetime.datetime.now(tz=tz)
                            print(f"Set reboot time: {target_hour_str}:{target_minute_str} {reboot_etc}")
                        except Exception as e:
                            print(f"Set reboot time: {target_hour_str}:{target_minute_str} UTC")
                    except:
                        print("no reboot time set")


                except Exception as e:
                    print(f"Error while trying to set reboot time: {e}")

                # CLEAR SOME DATABASES

                try:
                    conC = sqlite3.connect('databases/cooldowns.db')
                    curC = conC.cursor()
                    curC.execute("DELETE FROM userrequests")
                    curC.execute("DELETE FROM scrobbleupdate")
                    conC.commit()
                except Exception as e:
                    print(f"Error while trying to clear cooldown database - user requests table: {e}")

                # CLEAR TEMP FOLDER

                try:
                    for filename in os.listdir(f"{sys.path[0]}/temp/"):  
                        if filename != ".gitignore":              
                            os.remove(f"{sys.path[0]}/temp/{filename}")
                except Exception as e:
                    print("Error while trying to clear temp folder:", e)

            else:
                stat_name = "standby mode"
                await self.change_presence(activity=discord.Game(name=stat_name))
                print(f'status: standby mode')

            # INSTANCES WIDE ACTIVITY CHECK

            try:
                # Check whether bot display role id enabled
                con = sqlite3.connect(f'databases/botsettings.db')
                cur = con.cursor()

                bot_display = [item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("bot display",)).fetchall()][0]
                if bot_display == "on":
                    # Check whether role is assinged to bot

                    server = bot.get_guild(guild_id)
                    if server is None:
                        server = await bot.fetch_guild(guild_id)
                        if server is None:
                            raise ValueError("bot.fetch_guild(<guild_id>) returned None")

                    bot_member = server.get_member(self.application_id)
                    botrole_id = int([item[0] for item in cur.execute("SELECT role_id FROM specialroles WHERE name = ?", ("bot display role",)).fetchall()][0])                   
                    bot_display_role = server.get_role(botrole_id)

                    if bot_display_role in bot_member.roles:
                        # bot has role, no need to set inactive
                        pass

                    else:
                        # bot does not have role -> set to inactive
                        conA = sqlite3.connect(f'databases/activity.db')
                        curA = conA.cursor()
                        activity_list = [item[0] for item in curA.execute("SELECT value FROM activity WHERE name = ?", ("activity",)).fetchall()]
                        this_instances_activity = activity_list[0].lower()

                        if this_instances_activity != "inactive":
                            curA.execute("UPDATE activity SET value = ? WHERE name = ?", ("inactive", "activity"))
                            conA.commit()
                            try:
                                await channel.send(f'(set inactive)')
                            except Exception as e:
                                print(f"Failed to send inactivity setting message: {e}")
            except Exception as e:
                print(f"error in serverwide instance activity check: {e}")
                        
        except Exception as e:
            print(f"error in executing on_ready: {e}")
            activity = "failed loading"



bot = YataBot()
bot.run(discord_token)