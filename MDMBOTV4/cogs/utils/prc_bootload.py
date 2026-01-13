import asyncio
import discord
import os
import sqlite3
import sys

import datetime
import pytz

from dotenv  import load_dotenv
from pathlib import Path

from cogs.utils.utl_discord import DiscordUtils as utl_d
from cogs.utils.utl_general import GeneralUtils as utl_g
from cogs.utils.utl_simple  import SimpleUtils  as utl_s
from cogs.utils.prc_update  import BotUpdate    as prc_update


class Environment():
    def __init__(self):
        load_dotenv()
        self.application_id = os.getenv("application_id")
        self.bot_instance   = os.getenv("bot_instance")
        self.discord_token  = os.getenv("discord_token")
        self.prefix         = os.getenv("prefix")
        self.main_guild_id  = int(os.getenv("guild_id"))
        self.bot_channel_id = int(os.getenv("bot_channel_id"))

        self.reboot_time_string = os.getenv("reboot")
        if self.reboot_time_string is None:
            reboot_time_string = os.getenv("reboot_time")

        self.main_extension_dict = {}
        self.main_extension_dict["cogs.admin.cmd_instance_management"]    = os.getenv("instance_management")
        self.main_extension_dict["cogs.admin.cmd_servermoderation"]       = os.getenv("servermoderation")
        self.main_extension_dict["cogs.admin.cmd_settings"]               = os.getenv("settings")
        self.main_extension_dict["cogs.events.prc_eventresponse"]         = os.getenv("eventresponse")
        self.main_extension_dict["cogs.events.prc_timeloops"]             = os.getenv("timeloops")
        self.main_extension_dict["cogs.general.cmd_general_utility"]      = os.getenv("general_utility")
        self.main_extension_dict["cogs.general.cmd_help"]                 = os.getenv("general_help")
        self.main_extension_dict["cogs.general.cmd_shenanigans"]          = os.getenv("shenanigans")
        self.main_extension_dict["cogs.music.cmd_exchanges"]              = os.getenv("music_exchanges")
        self.main_extension_dict["cogs.music.cmd_fm"]                     = os.getenv("music_fm")
        self.main_extension_dict["cogs.music.cmd_info"]                   = os.getenv("music_info")
        self.main_extension_dict["cogs.music.cmd_scrobble_utility"]       = os.getenv("scrobble_utility")
        self.main_extension_dict["cogs.music.cmd_scrobble_visualization"] = os.getenv("scrobble_visualization")
        self.main_extension_dict["cogs.roles.cmd_roles"]                  = os.getenv("roles")
        self.main_extension_dict["cogs.roles.prc_reactionroles"]          = os.getenv("reactionroles")
        self.main_extension_dict["cogs.userown.cmd_memo"]                 = os.getenv("memo")
        self.main_extension_dict["cogs.userown.cmd_pingterest"]           = os.getenv("pingterest")
        self.main_extension_dict["cogs.xtended.cmd_youtube_download"]     = os.getenv("youtube_download")

        self.optional_extension_dict = {}
        self.optional_extension_dict["cogs.sandbox"]                      = os.getenv("sandbox")



class BootLoadFunctions():

    #########################################################################################################
    ##                                       common def                                                    ##
    #########################################################################################################

    def create_necessary_databases(bot) -> None:
        Path(f"databases").mkdir(parents=True, exist_ok=True)
        Path(f"temp").mkdir(parents=True, exist_ok=True)
        try:
            con0 = sqlite3.connect('databases/0host.db') 
            cur0 = con0.cursor()
            cur0.execute('''CREATE TABLE IF NOT EXISTS meta     (name text, value text)''')
            cur0.execute('''CREATE TABLE IF NOT EXISTS settings (name text, value text, details text)''')
        except Exception as e:
            print("> error with host database:", e)

        try:
            conB = sqlite3.connect('databases/botsettings.db')
            curB = conB.cursor()
            curB.execute('''CREATE TABLE IF NOT EXISTS bot_settings      (name text, num integer, value text, details text)''')
            curB.execute('''CREATE TABLE IF NOT EXISTS cooldown_settings (service text, cd_user integer, cd_mod_t4 integer, cd_mod_t3 integer, cd_mod_t2 integer, cd_mod_t1 integer, cd_type text, cd_bot integer, botwide_timeframe integer, botwide_amount_limit integer)''')
            curB.execute('''CREATE TABLE IF NOT EXISTS emoji             (name text, value text, fallback text, alt_name text)''')
            curB.execute('''CREATE TABLE IF NOT EXISTS mirrors           (service text, url text, priority integer, details text)''')
            curB.execute('''CREATE TABLE IF NOT EXISTS permissions       (perm text, user bool, mod_t4 bool, mod_t3 bool, mod_t2 bool, mod_t1 bool)''')
            curB.execute('''CREATE TABLE IF NOT EXISTS unwanted_tags     (string text, compare_type text, details text)''')
        except Exception as e:
            print("> error with bot settings database:", e)

        try:
            conR = sqlite3.connect('databases/schedule.db')
            curR = conR.cursor()
            curR.execute('''CREATE TABLE IF NOT EXISTS recurring  (reminder_id text, username text, user_id integer, pinglist text, interval text, next_time integer, remindertitle text, remindertext text, adaptivelink text, guild_id integer, guild_name text, channel_id integer, channel_name text, thumbnail text, emoji text)''')
            curR.execute('''CREATE TABLE IF NOT EXISTS reminders  (reminder_id integer, username text, user_id integer, utc_timestamp integer, remindertext text, guild_id integer, guild_name text, channel_id integer, channel_name text, og_message_id integer, og_time integer)''')
            curR.execute('''CREATE TABLE IF NOT EXISTS taskmarker (type text, num integer)''')
        except Exception as e:
            print("> error with schedule database:", e)

        try:
            conT = sqlite3.connect('databases/tracking.db')
            curT = conT.cursor()
            curT.execute('''CREATE TABLE IF NOT EXISTS cooldowns                  (service text, user_id integer, utc_timestamp integer)''')
            curT.execute('''CREATE TABLE IF NOT EXISTS last_changed               (server_id integer, db_name text, utc_timestamp integer, time_string text)''')
            curT.execute('''CREATE TABLE IF NOT EXISTS pipes                      (name text, user text, utc_timestamp integer, estimate integer)''')
            curT.execute('''CREATE TABLE IF NOT EXISTS reaction_embeds_multipage  (embed_type text, guild_id integer, channel_id integer, message_id integer, app_id integer, invoker_id integer, page integer, title text, url text, thumbnail text, color integer, content text, fields_titles text, fields_contents text, footer text, author_name text, author_url text, author_icon text, invoker_name text, guild_name text, channel_name text, utc_timestamp integer)''')
            curT.execute('''CREATE TABLE IF NOT EXISTS reaction_embeds_singlepage (embed_type text, guild_id integer, channel_id integer, message_id integer, app_id integer, invoker_id integer, invoker_name text, guild_name text, channel_name text, utc_timestamp integer)''') 
            curT.execute('''CREATE TABLE IF NOT EXISTS user_activity              (guild_id integer, guild_name text, user_id integer, user_name text, last_active integer, join_time integer, previous_roles text)''') 
            curT.execute('''CREATE TABLE IF NOT EXISTS users_excluded             (status text, guild_id integer, guild_name text, user_id integer, user_name text, role_id_list text, utc_timestamp integer)''') 
        except Exception as e:
            print("> error with tracking database:", e)

        try:
            conU = sqlite3.connect('databases/userdata.db')
            curU = conU.cursor()
            curU.execute('''CREATE TABLE IF NOT EXISTS lastfm       (user_id integer, username text, lfm_name text, lfm_link text, details text)''')
            curU.execute('''CREATE TABLE IF NOT EXISTS location     (user_id integer, username text, city text, state text, country text, zip_code text, longitude text, latitude text)''')
            curU.execute('''CREATE TABLE IF NOT EXISTS memo         (memo_id text, user_id integer, username text, content text, category text, utc_timestamp integer)''')
            curU.execute('''CREATE TABLE IF NOT EXISTS tag_settings (user_id integer, username text, artist_scrobbles integer, album_scrobbles integer, track_scrobbles integer, server_rank integer, server_crown integer, server_artistplays integer, spotify_monthlylisteners integer, spotify_genretags integer, lastfm_listeners integer, lastfm_total_artistplays integer, lastfm_tags integer, musicbrainz_tags integer, musicbrainz_area integer, musicbrainz_date integer, rym_genretags integer, rym_area integer, rym_date integer, rym_releasetype integer, rym_average_rating integer, rym_individual_rating integer, redundancy_filter integer)''')
        except Exception as e:
            print("> error with user data database:", e)

        try:
            conI = sqlite3.connect('databases/info.db')
            curI = conI.cursor()
            curI.execute('''CREATE TABLE IF NOT EXISTS exchangerates_USD (code text, value text, currency text, country text, last_updated text, utc_timestamp integer)''')
        except Exception as e:
            print("> error with info database:", e)

        try:
            Path(f"databases/music").mkdir(parents=True, exist_ok=True)
            conRw = sqlite3.connect('databases/music/rawdata.db')
            curRw = conRw.cursor()
            conFm = sqlite3.connect('databases/music/fm.db')
            curFm = conFm.cursor()
            curFm.execute('''CREATE TABLE IF NOT EXISTS info_artists       (artist_key text, ambiguity_id integer, lfm_tags  text, lfm_image text, lfm_listeners integer, lfm_plays integer, lfm_updated integer, mb_area text, mbid text, mb_updated integer, spotify_tags text, spotify_image text, spotify_followers integer, spotify_popularity integer, spotify_id text, spotify_updated text, spotify_monthly_listeners integer, spotify_ml_updated integer, rym_tags text, rym_area text, rym_id integer, rym_updated integer, artist_full text)''')
            curFm.execute('''CREATE TABLE IF NOT EXISTS info_releases      (artist_key text, ambiguity_id integer, album_key text, album_extra text, lfm_listeners integer, lfm_plays integer, lfm_cover text, lfm_tags text, lfm_updated integer, mb_tags text, mb_year integer, mb_date integer, mbid text, mb_updated integer, spotify_release_type text, spotify_cover text, spotify_tags text, spotify_popularity integer, spotify_id text, spotify_updated integer, rym_release_type text, rym_cover text, rym_tags_1 text, rym_tags_2 text, rym_descriptors text, rym_year integer, rym_date integer, rym_image text, rym_avg_score text, rym_voters integer, rym_artist_id integer, rym_album_id integer, rym_updated integer, artist_full text, album_full text)''')
            curFm.execute('''CREATE TABLE IF NOT EXISTS info_tracks        (artist_key text, album_key text, track_key text, ambiguity_id integer, album_extra text, track_extra text, lfm_tags text, lfm_duration_sec integer, mbid text, mb_duration_sec integer, spotify_id text, spotify_popularity integer, spotify_duration_ms integer, rym_duration_sec integer, rym_avg_score text, rym_voters text, artist_full text, album_full text, track_full text)''')
            curFm.execute('''CREATE TABLE IF NOT EXISTS namealias_artists  (artist_alias text, artist_key text, ambiguity_id integer, details text, utc_timestamp integer)''')
            curFm.execute('''CREATE TABLE IF NOT EXISTS namealias_releases (artist_key text, ambiguity_id integer, album_alias text, album_key text, details text, utc_timestamp integer)''')
            curFm.execute('''CREATE TABLE IF NOT EXISTS scrobbles          (lfm_name text, utc_time integer, artist_key text, album_key text, track_key text, ambiguity_id integer, album_extra text, track_extra text, artist_full text, album_full text, track_full text)''')
        except Exception as e:
            print("> error with scrobble databases:", e)

        try:
            utl_g.create_serverspecific_mod_database(bot.main_guild_id)
        except Exception as e:
            print("> error with server specific moderation database for main server:", e)

        try:
            utl_g.create_serverspecific_qol_databases(bot.main_guild_id)
        except Exception as e:
            print("> error with server specific QoL databases for main server:", e)



    def load_activeness() -> tuple[str, bool]:
        try:
            con0 = sqlite3.connect(f'databases/0host.db')
            cur0 = con0.cursor()
            activity_list = [item[0] for item in cur0.execute("SELECT value FROM meta WHERE name = ?", ("active",)).fetchall()]
            if len(activity_list) > 0:
                load_settings = True
                if activity_list[0].lower() == "no":
                    activity = 0 #"inactive"
                else:
                    activity = 1 #"active"
            else:
                load_settings = False
                activity = 0 #"inactive"
                cur0.execute("INSERT INTO artistinfo VALUES (?, ?)", ("active", "no"))
                con0.commit()
        except Exception as e:
            load_settings = False
            activity = 0 #"inactive"
            print("> error with activity check:", e) # TODO give user directive

        return activity, load_settings



    def getsave_version_from_file() -> str:

        # GET part
        try:
            lines = []
            with open('other/version.txt', 'r') as s:
                for line in s:
                    lines.append(line.strip())
            version = lines[0]
        except Exception as e:
            version = "version ?"
            print("> error with version check:", e)

        print(f"> {version}")

        # SAVE part
        try:
            con0 = sqlite3.connect(f'databases/0host.db')
            cur0 = con0.cursor()
            version_list = [item[0] for item in cur0.execute("SELECT value FROM meta WHERE name = ?", ("version",)).fetchall()]
            if len(version_list) == 0:
                cur0.execute("INSERT INTO meta VALUES (?, ?)", ("version", version))
            else:
                cur0.execute("UPDATE meta SET value = ? WHERE name = ?", (version, "version"))
            con0.commit()
        except Exception as e:
            print("> error while storing version number in DB:", e)

        return version



    def clear_db_residue() -> None:

        # clear some databases
        try:
            conT = sqlite3.connect('databases/tracking.db')
            curT = conT.cursor()
            curT.execute("DELETE FROM cooldowns")
            curT.execute("DELETE FROM pipes")
            conT.commit()
        except Exception as e:
            print(f"> error while trying to clear cooldown database - user requests table: {e}")

        # clear temp folder
        try:
            for filename in os.listdir(f"{sys.path[0]}/temp/"):  
                if filename != ".gitignore":              
                    os.remove(f"{sys.path[0]}/temp/{filename}")
        except Exception as e:
            print("> error while trying to clear temp folder:", e)



    def setup_cooldown_settings(bot) -> None:
        """save cooldown + mod_tier settings as dictionary in bot objects member variable"""
        conB = sqlite3.connect('databases/botsettings.db')
        curB = conB.cursor()
        cooldown_setting_list  = [[item[0],item[1],item[2],item[3],item[4],item[5],item[6],item[7],item[8],item[9]] for item in curB.execute("SELECT service, cd_user, cd_mod_t4, cd_mod_t3, cd_mod_t2, cd_mod_t1, cd_type, cd_bot, botwide_timeframe, botwide_amount_limit FROM cooldown_settings").fetchall()]

        for item in cooldown_setting_list:
            service    = item[0] 
            cd_user    = item[1] 
            cd_mod_t4  = item[2] 
            cd_mod_t3  = item[3] 
            cd_mod_t2  = item[4] 
            cd_mod_t1  = item[5] 
            cd_type    = item[6].lower().strip()
            cd_bot     = item[7] 
            botwide_timeframe    = item[8]  
            botwide_amount_limit = item[9]

            bot.cooldown_settings[service] = {}
            bot.cooldown_settings[service]["usr"] = cd_user / 10
            bot.cooldown_settings[service]["mt4"] = min(cd_mod_t4 / 10, bot.cooldown_settings[service]["usr"])
            bot.cooldown_settings[service]["mt3"] = min(cd_mod_t3 / 10, bot.cooldown_settings[service]["mt4"])
            bot.cooldown_settings[service]["mt2"] = min(cd_mod_t2 / 10, bot.cooldown_settings[service]["mt3"])
            bot.cooldown_settings[service]["mt1"] = min(cd_mod_t1 / 10, bot.cooldown_settings[service]["mt2"])
            bot.cooldown_settings[service]["tpe"] = (cd_type == "soft") # True: soft, False: hard
            bot.cooldown_settings[service]["bot"] = cd_bot  / 10
            bot.cooldown_settings[service]["btf"] = botwide_timeframe / 10
            bot.cooldown_settings[service]["bal"] = botwide_amount_limit
            bot.cooldown_settings[service]["pre"] = (min(cd_user, botwide_timeframe) < 10) # precision

        for server_id in utl_g.get_moderated_servers():
            bot.modtier_settings[server_id] = {}
            tx_mod_ids                      = [-1, -1, -1, -1]

            try:
                conS = sqlite3.connect(f'databases/{server_id}/serversettings.db')
                curS = conS.cursor()
                special_roles_list = [[item[0],item[1]] for item in curS.execute("SELECT role_key, role_id FROM special_roles").fetchall()]

                for role_item in special_roles_list:
                    role_key = role_item[0]
                    if role_key.endswith("_moderator"):
                        num = utl_s.force_integer(role_key[1])
                        if num > 0 and num < 5:
                            tx_mod_ids[num-1] = role_item[1]
            except Exception as e:
                print(f"Error while trying to find moderator role settings in server with ID {server_id}: {e}")

            for i in range(4):
                bot.modtier_settings[server_id][i+1] = tx_mod_ids[i]



    def setup_cooldown_in_memory_db() -> None:
        conRAM = sqlite3.connect('file::memory:?cache=shared', uri=True)
        curRAM = conRAM.cursor()
        curRAM.execute('''CREATE TABLE IF NOT EXISTS cooldowns (service text, user_id integer, utc_timestamp_ds integer)''')
        curRAM.execute("DELETE FROM cooldowns")
        conRAM.commit()



    def set_reboot_time(reboot_time_string: str) -> None:
        try:
            # get time and timezone 
            reboot_value = reboot_time_string.split(" ")[0].strip()

            if len(reboot_time_string.split(" ")) > 1:
                reboot_etc = reboot_time_string.split(" ", 1)[1]
            else:
                reboot_etc = ""

            # save to database
            con0 = sqlite3.connect(f'databases/0host.db')
            cur0 = con0.cursor()

            hostdata_reboot_list = [item[0] for item in cur0.execute("SELECT value FROM settings WHERE name = ?", ("time reboot",)).fetchall()]
            if len(hostdata_reboot_list) == 0:
                cur0.execute("INSERT INTO settings VALUES (?,?,?,?)", ("time reboot", reboot_value, "", reboot_etc))
                con0.commit()
                print("> Updated hostdata table: reboot time")
            else:
                if len(hostdata_reboot_list) > 1:
                    print("> Warning: Multiple reboot time entries in host database")
                cur0.execute("UPDATE settings SET value = ?, details = ? WHERE name = ?", (reboot_value, reboot_etc, "time reboot"))
                con0.commit()

            try:
                target_hour = utl_s.force_integer(reboot_value.split(":")[0].strip())
                target_minute = utl_s.force_integer(reboot_value.split(":")[1].strip())

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

                    print(f"> set reboot time: {target_hour_str}:{target_minute_str} {reboot_etc}")
                except Exception as e:
                    print(f"> set reboot time: {target_hour_str}:{target_minute_str} UTC")
            except:
                print("> no reboot time set")
                print("(reboot time is only relevant so the bot knows around which time it should not start lengthier operations)")
        except Exception as e:
            print(f"> error while trying to set reboot time: {e}")



    #########################################################################################################
    ##                                        async def                                                    ##
    #########################################################################################################



    async def set_discord_status(bot, load_settings = True) -> None:
        if load_settings:
            try:
                conB = sqlite3.connect(f'databases/botsettings.db')
                curB = conB.cursor()

                status_list = [[item[0],item[1]] for item in curB.execute("SELECT details, value FROM bot_settings WHERE name = ?", ("status",)).fetchall()]
                stat_type = status_list[0][0]
                stat_name = status_list[0][1]
                
                if stat_type in ['c', 'p', 's', 'l', 'w', 'n']:
                    if stat_type == 'c':
                        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.competing, name=stat_name))
                        print(f'> set status COMPETING IN {stat_name}')
                    elif stat_type == 'p':
                        await bot.change_presence(activity=discord.Game(name=stat_name))
                        print(f'> set status PLAYING {stat_name}')
                    elif stat_type == 's':
                        my_twitch_url = "https://www.twitch.tv/mdmbot/home"
                        await bot.change_presence(activity=discord.Streaming(name=stat_name, url=my_twitch_url))
                        print(f'> set status STREAMING {stat_name}')
                    elif stat_type == 'l':
                        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=stat_name))
                        print(f'> set status LISTENING TO {stat_name}')
                    elif stat_type == 'w':
                        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=stat_name))
                        print(f'> set status WATCHING {stat_name}')
                    elif stat_type == 'n':
                        await bot.change_presence(activity=None)
                        print('> empty status')
                else:
                    print('> first argument was not a valid status type, setting status type WATCHING')
                    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=value))          
            except Exception as e:
                print(f'> error in loading default status: {e}')
        else:
            stat_name = "standby mode"
            await bot.change_presence(activity=discord.Game(name=stat_name))
            print(f'> status: standby mode')



    async def instance_wide_activity_check(bot) -> None:
        """if multiple instances are online it can happen that:
            1. THIS instance has connection issues
            2. you then switch the active instance 
            3. THIS instance comes back online and you have 2 instances claiming to be active
        -> the goal with this function is to then automatically set the instance without the bot display role offline,
           this is possible because if bot display role is enabled only one instance has that role and an activity switch also switches who has the role"""

        try:
            # Check whether bot display role is enabled
            conB = sqlite3.connect(f'databases/{bot.main_guild_id}/serversettings.db')
            curB = conB.cursor()

            bot_display_list = [item[0] for item in curB.execute("SELECT active FROM functionalities WHERE name = ?", ("bot display",)).fetchall()]
            if len(bot_display_list) > 0 and bot_display_list[0] == True:
                # Check whether role is assinged to bot

                server = await utl_d.get_server(bot)
                if server is None:
                    raise ValueError("bot.fetch_guild(<guild_id>) returned None")

                bot_member = server.get_member(bot.application_id)
                botrole_id = [item[0] for item in curB.execute("SELECT role_id FROM special_roles WHERE role_key = ?", ("bot display role",)).fetchall()][0]                 
                bot_display_role = server.get_role(botrole_id)

                if bot_display_role in bot_member.roles:
                    # bot has role, no need to set inactive
                    pass

                else:
                    # bot does not have role -> set to inactive
                    conA = sqlite3.connect(f'databases/0host.db')
                    curA = conA.cursor()
                    activity_list = [item[0] for item in curA.execute("SELECT value FROM meta WHERE name = ?", ("active",)).fetchall()]
                    this_instances_activity = activity_list[0].lower()

                    if this_instances_activity != "no":
                        curA.execute("UPDATE meta SET value = ? WHERE name = ?", ("no", "active"))
                        conA.commit()
                        bot.activity_status = 0
                        try:
                            await channel.send(f'(set inactive)')
                        except Exception as e:
                            print(f"> failed to send inactivity setting message: {e}")
                            
        except Exception as e:
            print(f"> error in serverwide instance activity check: {e}")


