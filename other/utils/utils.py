import os
import zipfile
import sys
import traceback
from datetime import datetime, date, timedelta
import pytz
import sqlite3
import asyncio
import discord
from discord.ext import commands
import re
import math
import random
import requests
from bs4 import BeautifulSoup
import json
from emoji import UNICODE_EMOJI
from calendar import monthrange
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# cloud stuff
import contextlib
import six
import time
import unicodedata
import functools
import typing
import base64
import string

try:
    import dropbox
    dropbox_enabled = True
except:
    dropbox_enabled = False



class Utils():

    ############################################### COMMAND CHECKS

    def is_main_server_returnbool(ctx):
        server = ctx.message.guild
        if server is None:
            return False
        else:
            con = sqlite3.connect(f'databases/botsettings.db')
            cur = con.cursor()
            main_servers = [item[0] for item in cur.execute("SELECT value FROM botsettings WHERE name = ?", ("main server id",)).fetchall()]
            guild_id = str(ctx.guild.id)
            if guild_id in main_servers:
                return True
            else:
                return False


    def is_main_server(ctx):
        if Utils.is_main_server_returnbool(ctx):
            return True
        try:
            mainserver = [item[0] for item in cur.execute("SELECT details FROM botsettings WHERE name = ?", ("main server id",)).fetchall()][0]
            if mainserver.strip() == "":
                mainserver = "*main server*"
        except:
            mainserver = "*bot's main server*"
        raise commands.CheckFailure(f'Error: This is a {mainserver} specific command.')


    def is_dev(ctx):
        user = ctx.message.author 
        user_id = str(user.id)

        con = sqlite3.connect(f'databases/botsettings.db')
        cur = con.cursor()
        moderators = [item[0] for item in cur.execute("SELECT userid FROM moderators WHERE details = ? OR details = ?", ("dev", "owner")).fetchall()]

        if user_id in moderators:
            return True
        else:
            raise commands.CheckFailure(f'Error: Permission denied.')
            return False


    def is_active_returnbool(*ctx):
        conA = sqlite3.connect(f'databases/activity.db')
        curA = conA.cursor()
        activity_list = [item[0] for item in curA.execute("SELECT value FROM activity WHERE name = ?", ("activity",)).fetchall()]
        
        if len(activity_list) != 1:
            return False
        else:
            activity = activity_list[0]
            if activity == "active":
                return True
            else:
                return False


    def is_active(*ctx):
        if Utils.is_active_returnbool():
            return True
        raise commands.CheckFailure("inactive")


    def is_host(ctx):
        try:
            host_id = int(os.getenv("host_user_id"))
        except:
            raise commands.CheckFailure("Failed to load host id from environment. This is a bot host-only command.")
            return False

        if ctx.author.id == host_id:
            return True

        else:
            raise commands.CheckFailure("Permssion denied, this is a host-only command.")
            return False


    def is_mod(ctx):
        # depracate this in future
        for perms in ctx.message.author.guild_permissions:
            if perms[0] == "manage_guild":
                if perms[1]:
                    is_mod = True
                else:
                    is_mod = False
                break
        else:
            print("Error: Something is wrong with permission manage_guild.")
            is_mod = False

        return is_mod


    def is_dm(ctx):
        server = ctx.message.guild
        if server is None:
            return True
        return False
        

    def inactivity_filter_enabled(ctx):
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



    async def error_handling(ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f'Sorry, you do not have permissions to do this!')
        elif isinstance(error, commands.CheckFailure):
            if str(error) != "inactive":
                await ctx.channel.send(error)
            else:
                if ctx.guild == None:
                    # IF IT'S DM
                    await ctx.send("This bot instance is inactive. Check which application is actually the currently active one.")
        elif isinstance(error, commands.InvalidEndOfQuotedStringError):
            await ctx.channel.send(f'Bad Argument Error:```{str(error)}```Better try to avoid quotation marks within commands.')
        elif isinstance(error, commands.UnexpectedQuoteError):
            await ctx.channel.send(f'Bad Argument Error:```{str(error)}```Better try to avoid quotation marks within commands.')
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.channel.send(f'Error: Command needs arguments. Use help command for more info.')
        elif "sslv3 alert bad record mac" in str(error).lower():
            await ctx.channel.send(f"Whoopsie, seems like there was some client hiccup on discord's side (SSLv3 error). You can try it again now.")
        else:
            await ctx.channel.send(f'An error ocurred.')
            print("ERROR HANDLER: ", str(error))
            print("-------------------------------------")
            print(traceback.format_exc())
            print("-------------------------------------")
            try:
                conB = sqlite3.connect(f'databases/botsettings.db')
                curB = conB.cursor()
                detailederrornotif_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("detailed error reporting",)).fetchall()]
                if len(detailederrornotif_list) == 0 or detailederrornotif_list[0] != "on":
                    pass
                else:
                    detailtext = str(traceback.format_exc()).split("The above exception")[0].strip()
                    await Utils.bot_spam_send(ctx, f"Error in {ctx.channel.mention}", f"Error message: {str(error)}```{detailtext}```")
            except Exception as e:
                print("Error:", e)



    ############################################### VARIABLES / LISTS / DICTIONARIES

    def unit_seconds():
        unit_seconds = {
            "s": 1,
            "sec": 1,
            "second": 1,
            "seconds": 1,
            "m": 60,
            "min": 60,
            "minute": 60,
            "minutes": 60,
            "h": 60*60,
            "hr": 60*60,
            "hrs": 60*60,
            "hour": 60*60,
            "hours": 60*60,
            "d": 24*60*60,
            "day": 24*60*60,
            "days": 24*60*60,
            "w": 7*24*60*60,
            "week": 7*24*60*60,
            "weeks": 7*24*60*60,
            "fortnight": 14*24*60*60,
            "fortnights": 14*24*60*60,
            "moon": int(29.5*24*60*60),
            "moons": int(29.5*24*60*60),
            "naive_month": 30*24*60*60,
            #"month": Utils.reccuring_time_to_seconds("monthly"),
            #"months": Utils.reccuring_time_to_seconds("monthly"),
            "naive_year": 365*24*60*60,
            #"year": Utils.reccuring_time_to_seconds("yearly"),
            #"years": Utils.reccuring_time_to_seconds("yearly"),
            }
        return unit_seconds



    ############################################### ASYNC REQUESTS



    def run_async(callback):
        def inner(func):
            def wrapper(*args, **kwargs):
                def __exec():
                    out = func(*args, **kwargs)
                    callback(out)
                    return out

                return asyncio.get_event_loop().run_in_executor(None, __exec)

            return wrapper

        return inner


    def _callback(*args):
        if len(args) > 0:
            if str(args[0]).strip() == "<Response [200]>":
                #print("good response")
                pass
            else:
                print(f"Error: {str(args[0])}")
        else:
            print("Asyncio: No callback?")



    # Must provide a callback function, callback func will be executed after the func completes execution !!
    @run_async(_callback)
    def asyncrequest_get(url, headers, params):
        return requests.get(url, headers=headers, params=params)



    def to_thread(func: typing.Callable) -> typing.Coroutine:
        """wrapper for blocking functions, seems to not properly work though"""
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await asyncio.to_thread(func, *args, **kwargs)
        return wrapper



    async def run_blocking(bot, blocking_func: typing.Callable, *args, **kwargs) -> typing.Any:
        """Runs a blocking function in a non-blocking way"""
        func = functools.partial(blocking_func, *args, **kwargs) # `run_in_executor` doesn't support kwargs, `functools.partial` does
        return await bot.loop.run_in_executor(None, func)



    ###############################################


    def encode(key, clear):
        enc = []
        for i in range(len(clear)):
            key_c = key[i % len(key)]
            enc_c = chr((ord(clear[i]) + ord(key_c)) % 256)
            enc.append(enc_c)
        return base64.urlsafe_b64encode("".join(enc).encode()).decode()

    def decode(key, enc):
        dec = []
        enc = base64.urlsafe_b64decode(enc).decode()
        for i in range(len(enc)):
            key_c = key[i % len(key)]
            dec_c = chr((256 + ord(enc[i]) - ord(key_c)) % 256)
            dec.append(dec_c)
        return "".join(dec)

    def get_random_string(length):
        characters = string.ascii_letters + string.digits + string.punctuation
        result_str = ''.join(random.choice(characters) for i in range(length))
        return result_str

    def get_enc_key():
        key = os.getenv('encryption_key')

        if key is None:
            con = sqlite3.connect(f'databases/activity.db')
            cur = con.cursor()
            key_list = [item[0] for item in cur.execute("SELECT value FROM hostdata WHERE name = ?", ("encryption key",)).fetchall()]

            if len(key_list) > 0:
                key = key_list[0]
            else:
                i = random.randint(100, 200)
                key = Utils.get_random_string(i)
                cur.execute("INSERT INTO hostdata VALUES (?,?,?,?)", ("encryption key", key, "", ""))
                con.commit()

        return key



    ####################################################################################################################################


















































    ############################################### GENERAL UTILITY FUNCTIONS (sorted alphabetically)



    def adapt_link(text):
        followtext = text
        new_link = ""
        while "[" in followtext and "]" in followtext.split("[",1)[1]:
            new_link += followtext.split("[",1)[0]
            keyword = followtext.split("[",1)[1].split("]",1)[0]

            # NEST DIFFERENT ADAPT FUNCTIONS
            try: #1) ADAPT TIME
                new_link += Utils.adapt_time(keyword)
            except Exception as e:
                print("Error in utils.adapt_link():", e)
                try: #2) ?
                    error = int("error")  # just a place holder for potential next function
                except Exception as e:
                    #print("Error in utils.adapt_link():", e)
                    raise ValueError("Bracket block in provided link contained syntax error.")

            followtext = followtext.split("[",1)[1].split("]",1)[1]
        new_link += followtext

        if "[" in new_link or "]" in new_link:
            print("Error while adapting link. Provided link still contained left or right brackets after swapping bracket blocks.")
            raise ValueError("Provided link still contained left or right brackets after swapping bracket blocks.")
            return ""

        return new_link



    def adapt_time(s):
        """
        parses arguments like
            > month:last_week
        to the month number of last week etc.

        syntax is
            > arg1:arg2_arg3
        where
        arg1 needs to be year or month
        arg2 needs to be last, this or next
        arg3 needs to be week or month
        """
        if s.count(":") != 1 and s.split(":",1)[1].count("_"):
            print("Error while adapting link. Bracket block contained invalid syntax.")
            raise ValueError("Bracket block in provided link contained invalid syntax.")
            return ""

        s = s.lower().strip().replace(" ","")

        date_unit = s.split(":",1)[0] # year or month
        order_specifier = s.split(":",1)[1].split("_",1)[0] # last, this or next
        time_frame = s.split(":",1)[1].split("_",1)[1] # week or month

        today = date.today()
        month_today = today.month
        year_today = today.year
        weekday_today = today.weekday()

        #print(f"{month_today}-{year_today}, weekday: {weekday_today}")

        this_weeks_end_DTobj   = today + timedelta(days = 7 - weekday_today)
        this_weeks_ends_month  = this_weeks_end_DTobj.month
        this_weeks_ends_year   = this_weeks_end_DTobj.year
        next_weeks_end_DTobj   = this_weeks_end_DTobj + timedelta(days = 7)
        next_weeks_ends_month  = next_weeks_end_DTobj.month
        next_weeks_ends_year   = next_weeks_end_DTobj.year
        last_weeks_start_DTobj = today - timedelta(days = 7 + weekday_today)
        last_weeks_start_month  = last_weeks_start_DTobj.month
        last_weeks_start_year   = last_weeks_start_DTobj.year

        this_months_month = month_today
        this_months_year  = year_today
        next_months_month = (month_today//12) + 1
        if next_months_month == 1:
            next_months_year = year_today + 1
        else:
            next_months_year = year_today
        last_months_month = ((month_today+10)//12) + 1
        if last_months_month == 12:
            last_months_year = year_today - 1
        else:
            last_months_year = year_today

        return_dict = {
                "month": {
                        "this":{
                                "week": str(this_weeks_ends_month),
                                "month": str(this_months_month),
                            },
                        "next":{
                                "week": str(next_weeks_ends_month),
                                "month": str(next_months_month),
                            },
                        "last":{
                                "week": str(last_weeks_start_month),
                                "month": str(last_months_month),
                            },
                },
                #
                "year": {
                        "this":{
                                "week": str(this_weeks_ends_year),
                                "month": str(this_months_year),
                            },
                        "next":{
                                "week": str(next_weeks_ends_year),
                                "month": str(next_months_year),
                            },
                        "last":{
                                "week": str(last_weeks_start_year),
                                "month": str(last_months_year),
                            },
                },
            }

        try:
            return return_dict[date_unit][order_specifier][time_frame]
        except:
            print("Issue with provided link: utils.adapt_time() could not parse time")
            raise ValueError("Issue with provided link: utils.adapt_time() could not parse time")



    def album_is_nsfw(artist, album):
        is_nsfw = False
        artistcompact = Utils.compactnamefilter(artist, "artist", "alias")
        albumcompact = Utils.compactnamefilter(album, "album")

        conSM = sqlite3.connect('databases/scrobblemeta.db')
        curSM = conSM.cursor()
        artistinfo_list = [item[0] for item in curSM.execute("SELECT details FROM albuminfo WHERE artist_filtername = ? AND album_filtername = ?", (artistcompact, albumcompact)).fetchall()]

        if len(artistinfo_list) > 0 and artistinfo_list[-1].lower().strip() == "nsfw":
            is_nsfw = True

        return is_nsfw



    def alphanum(text, *args):
        if len(args) > 0:
            extra_step = ' '.join(args).lower()

            if extra_step == "lower":
                text = text.lower()
            elif extra_step == "upper":
                text = text.upper()

        ctext = ''.join([e for e in text.strip() if e.isalpha() or e.isnumeric()])
        return ctext



    def areaicon(area_name):
        """converts place name to flag"""
        emoji = ""
        
        countrycode_icon_dict = {'??': '❓', 'AD': '🇦🇩', 'AE': '🇦🇪', 'AF': '🇦🇫', 'AG': '🇦🇬', 'AI': '🇦🇮', 'AL': '🇦🇱', 'AM': '🇦🇲', 'AO': '🇦🇴', 'AQ': '🇦🇶', 'AR': '🇦🇷', 'AS': '🇦🇸', 'AT': '🇦🇹', 'AU': '🇦🇺', 'AW': '🇦🇼', 'AX': '🇦🇽', 'AZ': '🇦🇿', 'BA': '🇧🇦', 'BB': '🇧🇧', 'BD': '🇧🇩', 'BE': '🇧🇪', 'BF': '🇧🇫', 'BG': '🇧🇬', 'BH': '🇧🇭', 'BI': '🇧🇮', 'BJ': '🇧🇯', 'BL': '🇧🇱', 'BM': '🇧🇲', 'BN': '🇧🇳', 'BO': '🇧🇴', 'BQ': '🇧🇶', 'BR': '🇧🇷', 'BS': '🇧🇸', 'BT': '🇧🇹', 'BV': '🇧🇻', 'BW': '🇧🇼', 'BY': '🇧🇾', 'BZ': '🇧🇿', 'CA': '🇨🇦', 'CC': '🇨🇨', 'CD': '🇨🇩', 'CF': '🇨🇫', 'CG': '🇨🇬', 'CH': '🇨🇭', 'CI': '🇨🇮', 'CK': '🇨🇰', 'CL': '🇨🇱', 'CM': '🇨🇲', 'CN': '🇨🇳', 'CO': '🇨🇴', 'CR': '🇨🇷', 'CU': '🇨🇺', 'CV': '🇨🇻', 'CW': '🇨🇼', 'CX': '🇨🇽', 'CY': '🇨🇾', 'CZ': '🇨🇿', 'DE': '🇩🇪', 'DJ': '🇩🇯', 'DK': '🇩🇰', 'DM': '🇩🇲', 'DO': '🇩🇴', 'DZ': '🇩🇿', 'EC': '🇪🇨', 'EE': '🇪🇪', 'EG': '🇪🇬', 'EH': '🇪🇭', 'ER': '🇪🇷', 'ES': '🇪🇸', 'ET': '🇪🇹', 'EU': '🇪🇺', 'FI': '🇫🇮', 'FJ': '🇫🇯', 'FK': '🇫🇰', 'FM': '🇫🇲', 'FO': '🇫🇴', 'FR': '🇫🇷', 'GA': '🇬🇦', 'GB': '🇬🇧', 'GB-CYM': '🏴\U000e0067\U000e0062\U000e0077\U000e006c\U000e0073\U000e007f', 'GB-ENG': '🏴\U000e0067\U000e0062\U000e0065\U000e006e\U000e0067\U000e007f', 'GB-NIR': '🏴\U000e0067\U000e0062\U000e006e\U000e0069\U000e0072\U000e007f', 'GB-SCT': '🏴\U000e0067\U000e0062\U000e0073\U000e0063\U000e0074\U000e007f', 'GD': '🇬🇩', 'GE': '🇬🇪', 'GF': '🇬🇫', 'GG': '🇬🇬', 'GH': '🇬🇭', 'GI': '🇬🇮', 'GL': '🇬🇱', 'GM': '🇬🇲', 'GN': '🇬🇳', 'GP': '🇬🇵', 'GQ': '🇬🇶', 'GR': '🇬🇷', 'GS': '🇬🇸', 'GT': '🇬🇹', 'GU': '🇬🇺', 'GW': '🇬🇼', 'GY': '🇬🇾', 'HK': '🇭🇰', 'HM': '🇭🇲', 'HN': '🇭🇳', 'HR': '🇭🇷', 'HT': '🇭🇹', 'HU': '🇭🇺', 'ID': '🇮🇩', 'IE': '🇮🇪', 'IL': '🇮🇱', 'IM': '🇮🇲', 'IN': '🇮🇳', 'IO': '🇮🇴', 'IQ': '🇮🇶', 'IR': '🇮🇷', 'IS': '🇮🇸', 'IT': '🇮🇹', 'JE': '🇯🇪', 'JM': '🇯🇲', 'JO': '🇯🇴', 'JP': '🇯🇵', 'KE': '🇰🇪', 'KG': '🇰🇬', 'KH': '🇰🇭', 'KI': '🇰🇮', 'KM': '🇰🇲', 'KN': '🇰🇳', 'KP': '🇰🇵', 'KR': '🇰🇷', 'KW': '🇰🇼', 'KY': '🇰🇾', 'KZ': '🇰🇿', 'LA': '🇱🇦', 'LB': '🇱🇧', 'LC': '🇱🇨', 'LI': '🇱🇮', 'LK': '🇱🇰', 'LR': '🇱🇷', 'LS': '🇱🇸', 'LT': '🇱🇹', 'LU': '🇱🇺', 'LV': '🇱🇻', 'LY': '🇱🇾', 'MC': '🇲🇨', 'MD': '🇲🇩', 'ME': '🇲🇪', 'MF': '🇲🇫', 'MG': '🇲🇬', 'MH': '🇲🇭', 'MK': '🇲🇰', 'ML': '🇲🇱', 'MM': '🇲🇲', 'MN': '🇲🇳', 'MO': '🇲🇴', 'MP': '🇲🇵', 'MQ': '🇲🇶', 'MR': '🇲🇷', 'MS': '🇲🇦', 'MT': '🇲🇹', 'MU': '🇲🇺', 'MV': '🇲🇻', 'MW': '🇲🇼', 'MX': '🇲🇽', 'MY': '🇲🇾', 'MZ': '🇲🇿', 'NA': '🇳🇦', 'NC': '🇳🇨', 'NE': '🇳🇪', 'NF': '🇳🇫', 'NG': '🇳🇬', 'NI': '🇳🇮', 'NL': '🇳🇱', 'NO': '🇳🇴', 'NP': '🇳🇵', 'NR': '🇳🇷', 'NU': '🇳🇺', 'NZ': '🇳🇿', 'OM': '🇴🇲', 'PA': '🇵🇦', 'PE': '🇵🇪', 'PF': '🇵🇫', 'PG': '🇵🇬', 'PH': '🇵🇭', 'PK': '🇵🇰', 'PL': '🇵🇱', 'PM': '🇵🇲', 'PN': '🇵🇳', 'PR': '🇵🇷', 'PS': '🇵🇸', 'PT': '🇵🇹', 'PW': '🇵🇼', 'PY': '🇵🇾', 'QA': '🇶🇦', 'RE': '🇷🇪', 'RO': '🇷🇴', 'RS': '🇷🇸', 'RU': '🇷🇺', 'RW': '🇷🇼', 'SA': '🇸🇦', 'SB': '🇸🇧', 'SC': '🇸🇨', 'SD': '🇸🇩', 'SE': '🇸🇪', 'SG': '🇸🇬', 'SH': '🇸🇭', 'SI': '🇸🇮', 'SJ': '🇸🇯', 'SK': '🇸🇰', 'SL': '🇸🇱', 'SM': '🇸🇲', 'SN': '🇸🇳', 'SO': '🇸🇴', 'SR': '🇸🇷', 'SS': '🇸🇸', 'ST': '🇸🇹', 'SV': '🇸🇻', 'SX': '🇸🇽', 'SY': '🇸🇾', 'SZ': '🇸🇿', 'TC': '🇹🇨', 'TD': '🇹🇩', 'TF': '🇹🇫', 'TG': '🇹🇬', 'TH': '🇹🇭', 'TJ': '🇹🇯', 'TK': '🇹🇰', 'TL': '🇹🇱', 'TM': '🇹🇲', 'TN': '🇹🇳', 'TO': '🇹🇴', 'TR': '🇹🇷', 'TT': '🇹🇹', 'TV': '🇹🇻', 'TW': '🇹🇼', 'TZ': '🇹🇿', 'UA': '🇺🇦', 'UG': '🇺🇬', 'UM': '🇺🇲', 'US': '🇺🇸', 'UY': '🇺🇾', 'UZ': '🇺🇿', 'VA': '🇻🇦', 'VC': '🇻🇨', 'VE': '🇻🇪', 'VG': '🇻🇬', 'VI': '🇻🇮', 'VN': '🇻🇳', 'VU': '🇻🇺', 'WF': '🇼🇫', 'WS': '🇼🇸', 'XK': '🇽🇰', 'YE': '🇾🇪', 'YT': '🇾🇹', 'ZA': '🇿🇦', 'ZM': '🇿🇲', 'ZW': '🇿🇼', 'int': '🇺🇳'}

        if area_name.upper() in countrycode_icon_dict:
            return area_icon_dict[area_name.lower()]
        else:
            country_name_code_dict = {'AFGHANISTAN': 'AF', 'ÅLAND ISLANDS': 'AX', 'ALAND ISLANDS': 'AX', 'ALBANIA': 'AL', 'ALGERIA': 'DZ', 'AMERICAN SAMOA': 'AS', 'ANDORRA': 'AD', 'ANGOLA': 'AO', 'ANGUILLA': 'AI', 'ANTARCTICA': 'AQ', 'ANTIGUA AND BARBUDA': 'AG', 'ARGENTINA': 'AR', 'ARMENIA': 'AM', 'ARUBA': 'AW', 'AUSTRALIA': 'AU', 'AUSTRIA': 'AT', 'AZERBAIJAN': 'AZ', 'BAHAMAS': 'BS', 'BAHRAIN': 'BH', 'BANGLADESH': 'BD', 'BARBADOS': 'BB', 'BELARUS': 'BY', 'BELGIUM': 'BE', 'BELIZE': 'BZ', 'BENIN': 'BJ', 'BERMUDA': 'BM', 'BHUTAN': 'BT', 'BOLIVIA': 'BO', 'BONAIRE, SINT EUSTATIUS AND SABA': 'BQ', 'BOSNIA AND HERZEGOVINA': 'BA', 'BOTSWANA': 'BW', 'BOUVET ISLAND': 'BV', 'BRAZIL': 'BR', 'BRITISH INDIAN OCEAN TERRITORY': 'IO', 'BRUNEI': 'BN', 'BULGARIA': 'BG', 'BURKINA FASO': 'BF', 'BURUNDI': 'BI', 'CAMBODIA': 'KH', 'CAMEROON': 'CM', 'CANADA': 'CA', 'CAPE VERDE': 'CV', 'CAYMAN ISLANDS': 'KY', 'CENTRAL AFRICAN REPUBLIC': 'CF', 'CHAD': 'TD', 'CHILE': 'CL', 'CHINA': 'CN', 'CHRISTMAS ISLAND': 'CX', 'COCOS (KEELING) ISLANDS': 'CC', 'COLOMBIA': 'CO', 'COMOROS': 'KM', 'CONGO, DEMOCRATIC REPUBLIC OF': 'CD', 'CONGO, REPUBLIC OF': 'CG', 'COOK ISLANDS': 'CK', 'COSTA RICA': 'CR', "CÔTE D'IVOIRE": 'CI', 'CROATIA': 'HR', 'CUBA': 'CU', 'CURAÇAO': 'CW', 'CYPRUS': 'CY', 'CZECHIA': 'CZ', 'DENMARK': 'DK', 'DJIBOUTI': 'DJ', 'DOMINICA': 'DM', 'DOMINICAN REPUBLIC': 'DO', 'EAST TIMOR': 'TL', 'ECUADOR': 'EC', 'EGYPT': 'EG', 'EL SALVADOR': 'SV', 'EQUATORIAL GUINEA': 'GQ', 'ERITREA': 'ER', 'ESTONIA': 'EE', 'ESWATINI': 'SZ', 'ETHIOPIA': 'ET', 'FALKLAND ISLANDS': 'FK', 'FAROE ISLANDS': 'FO', 'FIJI': 'FJ', 'FINLAND': 'FI', 'FRANCE': 'FR', 'FRENCH GUIANA': 'GF', 'FRENCH POLYNESIA': 'PF', 'FRENCH SOUTHERN TERRITORIES': 'TF', 'GABON': 'GA', 'GAMBIA': 'GM', 'GEORGIA': 'GE', 'GERMANY': 'DE', 'GHANA': 'GH', 'GIBRALTAR': 'GI', 'GREECE': 'GR', 'GREENLAND': 'GL', 'GRENADA': 'GD', 'GUADELOUPE': 'GP', 'GUAM': 'GU', 'GUATEMALA': 'GT', 'GUERNSEY': 'GG', 'GUINEA': 'GN', 'GUINEA-BISSAU': 'GW', 'GUYANA': 'GY', 'HAITI': 'HT', 'HEARD AND MCDONALD ISLANDS': 'HM', 'HONDURAS': 'HN', 'HONG KONG': 'HK', 'HUNGARY': 'HU', 'ICELAND': 'IS', 'INDIA': 'IN', 'INDONESIA': 'ID', 'INTERNATIONAL': 'int', 'IRAN': 'IR', 'IRAQ': 'IQ', 'IRELAND': 'IE', 'ISLE OF MAN': 'IM', 'ISRAEL': 'IL', 'ITALY': 'IT', 'JAMAICA': 'JM', 'JAPAN': 'JP', 'JERSEY': 'JE', 'JORDAN': 'JO', 'KAZAKHSTAN': 'KZ', 'KENYA': 'KE', 'KIRIBATI': 'KI', 'KOREA, NORTH': 'KP', 'KOREA, SOUTH': 'KR', 'KUWAIT': 'KW', 'KYRGYZSTAN': 'KG', 'LAOS': 'LA', 'LATVIA': 'LV', 'LEBANON': 'LB', 'LESOTHO': 'LS', 'LIBERIA': 'LR', 'LIBYA': 'LY', 'LIECHTENSTEIN': 'LI', 'LITHUANIA': 'LT', 'LUXEMBOURG': 'LU', 'MACAU': 'MO', 'MADAGASCAR': 'MG', 'MALAWI': 'MW', 'MALAYSIA': 'MY', 'MALDIVES': 'MV', 'MALI': 'ML', 'MALTA': 'MT', 'MARSHALL ISLANDS': 'MH', 'MARTINIQUE': 'MQ', 'MAURITANIA': 'MR', 'MAURITIUS': 'MU', 'MAYOTTE': 'YT', 'MEXICO': 'MX', 'MICRONESIA, FEDERATED STATES OF': 'FM', 'MOLDOVA': 'MD', 'MONACO': 'MC', 'MONGOLIA': 'MN', 'MONTENEGRO': 'ME', 'MONTSERRAT': 'MS', 'MOROCCO': 'MS', 'MOZAMBIQUE': 'MZ', 'MYANMAR': 'MM', 'NAMIBIA': 'NA', 'NAURU': 'NR', 'NEPAL': 'NP', 'NETHERLANDS': 'NL', 'NEW CALEDONIA': 'NC', 'NEW ZEALAND': 'NZ', 'NICARAGUA': 'NI', 'NIGER': 'NE', 'NIGERIA': 'NG', 'NIUE': 'NU', 'NORFOLK ISLAND': 'NF', 'NORTH MACEDONIA': 'MK', 'NORTHERN MARIANA ISLANDS': 'MP', 'NORWAY': 'NO', 'OMAN': 'OM', 'PAKISTAN': 'PK', 'PALAU': 'PW', 'PALESTINE': 'PS', 'PANAMA': 'PA', 'PAPUA NEW GUINEA': 'PG', 'PARAGUAY': 'PY', 'PERU': 'PE', 'PHILIPPINES': 'PH', 'PITCAIRN ISLAND': 'PN', 'POLAND': 'PL', 'PORTUGAL': 'PT', 'PUERTO RICO': 'PR', 'QATAR': 'QA', 'REUNION': 'RE', 'ROMANIA': 'RO', 'RUSSIA': 'RU', 'RWANDA': 'RW', 'SAINT BARTHÉLEMY': 'BL', 'SAINT KITTS & NEVIS': 'KN', 'SAINT LUCIA': 'LC', 'SAINT MARTIN (FRENCH PART)': 'MF', 'SAINT PIERRE AND MIQUELON': 'PM', 'SAINT VINCENT AND THE GRENADINES': 'VC', 'SAMOA': 'WS', 'SAN MARINO': 'SM', 'SAO TOME AND PRINCIPE': 'ST', 'SAUDI ARABIA': 'SA', 'SENEGAL': 'SN', 'SERBIA': 'RS', 'SEYCHELLES': 'SC', 'SIERRA LEONE': 'SL', 'SINGAPORE': 'SG', 'SINT MAARTEN (DUTCH PART)': 'SX', 'SLOVAKIA': 'SK', 'SLOVENIA': 'SI', 'SOLOMON ISLANDS': 'SB', 'SOMALIA': 'SO', 'SOUTH AFRICA': 'ZA', 'SOUTH GEORGIA & SOUTH SANDWICH ISLANDS': 'GS', 'SOUTH SUDAN': 'SS', 'SPAIN': 'ES', 'SRI LANKA': 'LK', 'ST HELENA, ASCENSION & TRISTAN DA CUNHA': 'SH', 'SUDAN': 'SD', 'SURINAME': 'SR', 'SVALBARD': 'SJ', 'SWEDEN': 'SE', 'SWITZERLAND': 'CH', 'SYRIA': 'SY', 'TAIWAN': 'TW', 'TAJIKISTAN': 'TJ', 'TANZANIA': 'TZ', 'THAILAND': 'TH', 'TOGO': 'TG', 'TOKELAU': 'TK', 'TONGA': 'TO', 'TRINIDAD AND TOBAGO': 'TT', 'TUNISIA': 'TN', 'TÜRKIYE': 'TR', 'TURKMENISTAN': 'TM', 'TURKS AND CAICOS ISLANDS': 'TC', 'TUVALU': 'TV', 'U.S. MINOR OUTLYING ISLANDS': 'UM', 'UGANDA': 'UG', 'UKRAINE': 'UA', 'UNITED ARAB EMIRATES': 'AE', 'UNITED KINGDOM': 'GB', 'UNITED STATES': 'US', 'UNKNOWN': '??', 'URUGUAY': 'UY', 'UZBEKISTAN': 'UZ', 'VANUATU': 'VU', 'VATICAN CITY': 'VA', 'VENEZUELA': 'VE', 'VIETNAM': 'VN', 'VIRGIN ISLANDS (BRITISH)': 'VG', 'VIRGIN ISLANDS (US)': 'VI', 'WALLIS AND FUTUNA': 'WF', 'WESTERN SAHARA': 'EH', 'YEMEN': 'YE', 'ZAMBIA': 'ZM', 'ZIMBABWE': 'ZW', 'KOSOVO': 'XK', 'ENGLAND': 'GB-ENG', 'SCOTLAND': 'GB-SCT', 'WALES': 'GB-CYM', 'NORTHERN IRELAND': 'GB-NIR', 'EUROPE': 'EU'}
            if area_name.upper() in country_name_code_dict:
                code = country_name_code_dict[area_name.upper()]
                return countrycode_icon_dict[code]
            else:
                return ""



    def clean_up_crown_db():
        conSS = sqlite3.connect('databases/scrobblestats.db')
        curSS = conSS.cursor()

        for guild_crown_table in [item[0] for item in curSS.execute("SELECT name FROM sqlite_master WHERE type = ?", ("table",)).fetchall()]:

            if guild_crown_table == "artistinfo":
                duplicate_list = [[item[0],item[1],item[2],item[3],item[4],item[5],item[6]] for item in curSS.execute("SELECT * FROM artistinfo GROUP BY artist HAVING COUNT(artist) > 1").fetchall()]
                for item in duplicate_list:
                    artist      = item[0]
                    thumbnail   = item[1]
                    tags_lfm    = item[2]
                    tags_other  = item[3]
                    last_update = item[4]
                    filtername  = item[5]
                    filteralias = item[6]
                    curSS.execute(f"DELETE FROM {guild_crown_table} WHERE artist = ?", (artist,))
                    curSS.execute(f"INSERT INTO {guild_crown_table} VALUES (?, ?, ?, ?, ?, ?, ?)", (artist, thumbnail, tags_lfm, tags_other, last_update, filtername, filteralias))
                    conSS.commit()

            if not guild_crown_table.startswith("crowns_"):
                continue

            duplicate_list = [[item[0],item[1],item[2],item[3],item[4],item[5]] for item in curSS.execute(f"SELECT * FROM {guild_crown_table} GROUP BY artist HAVING COUNT(artist) > 1").fetchall()]
            for item in duplicate_list:
                artist       = item[0]
                alias        = item[1]
                alias2       = item[2]
                lfm_name     = item[3]
                discord_name = item[4]
                playcount    = item[5]
                curSS.execute(f"DELETE FROM {guild_crown_table} WHERE artist = ?", (artist,))
                curSS.execute(f"INSERT INTO {guild_crown_table} VALUES (?, ?, ?, ?, ?, ?)", (artist, alias, alias2, lfm_name, discord_name, playcount))
                conSS.commit()

            duplicate_list2 = [[item[0],item[1],item[2],item[3],item[4],item[5]] for item in curSS.execute(f"SELECT * FROM {guild_crown_table} GROUP BY alias HAVING COUNT(alias) > 1").fetchall()]
            for item in duplicate_list2:
                artist       = item[0]
                alias        = item[1]
                alias2       = item[2]
                lfm_name     = item[3]
                discord_name = item[4]
                playcount    = item[5]
                curSS.execute(f"DELETE FROM {guild_crown_table} WHERE alias = ?", (alias,))
                curSS.execute(f"INSERT INTO {guild_crown_table} VALUES (?, ?, ?, ?, ?, ?)", (artist, alias, alias2, lfm_name, discord_name, playcount))
                conSS.commit()



    def cleantext(s):
        ctxt = str(s).replace("`","'").replace('"',"'").replace("´","'").replace("‘","'").replace("’","'").replace("“","'").replace("”","'")
        return ctxt



    def cleantext2(s):
        ctxt = Utils.cleantext(str(s))
        ctxt2 = ctxt.replace("*","\*").replace("_","\_").replace("#","\#").replace("\n> ","\n\> ")
        return ctxt2



    def close_to_daytime_utc(target_hour, target_minute, buffer_min=15):
        """
        daytime_string: string in format HH:MM
        buffer_min: integer between 0 and 720
        """
        if buffer_min > 12*60:
            buffer_min = 12*60
        elif buffer_min < 0:
            buffer_min = 0

        try:
            h = datetime.utcnow().hour
            m = datetime.utcnow().minute

            day_minutes = h * 60 + m

            target_dayminutes = target_hour * 60 + target_minute

            diff = target_dayminutes - day_minutes

            if diff < 0:
                diff = diff + 24*60

            if diff <= buffer_min:
                return True #within buffer close to target time

        except Exception as e:
            print("Error in check for closeness to target time:", e)
        
        return False



    def close_to_reboottime(buffer_min=15):
        # FETCH TIME FROM DATABASE
        conA = sqlite3.connect(f'databases/activity.db')
        curA = conA.cursor()
        hostdata_reboot_list = [[item[0],item[1]] for item in curA.execute("SELECT value, etc FROM hostdata WHERE name = ?", ("reboot time",)).fetchall()]

        if len(hostdata_reboot_list) == 0:
            return False

        reboot_loctime = hostdata_reboot_list[0][0].strip() # string
        timezone_data = hostdata_reboot_list[0][1].strip()

        #CONVERT

        if ":" not in reboot_loctime:
            if reboot_loctime.lower() != "none":
                print("invalid reboot time given, ignoring and proceeding")
            return False

        target_hour = Utils.forceinteger(reboot_loctime.split(":")[0].strip())
        target_minute = Utils.forceinteger(reboot_loctime.split(":")[1].strip())

        try:
            # CREATING DATETIME OBJECT
            try:
                tz     = pytz.timezone(timezone_data)
                dt_now = datetime.now(tz=tz)
            except Exception as e:
                tz     = pytz.UTC
                dt_now = datetime.now(tz=tz)

            year  = dt_now.year
            month = dt_now.month
            day   = dt_now.day
            hour = dt_now.hour
            minute = dt_now.minute

            dt_now_simplified = datetime(year, month, day, hour, minute, 0, tzinfo=tz) # without seconds and smaller units

            dt_target = datetime(year, month, day, target_hour, target_minute, 0, tzinfo=tz)

            if target_hour < hour or (target_hour == hour and target_minute < minute):
                dt_target = dt_target + timedelta(days=1)

            # TIME DIFFERENCE

            timedelta_obj = dt_target - dt_now_simplified

            minutes_until = timedelta_obj.total_seconds() // 60

            if minutes_until >= 0 and minutes_until <= buffer_min:
                return True

        except Exception as e:
            print("Error in reboot time checker:", e)
        
        return False



    def compact_sql(string):
        return f"""REPLACE(REPLACE(REPLACE(REPLACE(UPPER({string}), " ", ""), "-", ""), "_", ""), "'", "")"""
        #return f"""UPPER({string})"""



    def compactaddendumfilter(input_string, *info):
        intermediate_string = input_string

        if len(info) > 0 :
            if info[0] == "artist":
                if input_string.endswith(" - Topic"):
                    intermediate_string = input_string.replace(" - Topic", "")
            elif info[0] == "album":
                if input_string.endswith(" - EP"):
                    intermediate_string = input_string.replace(" - EP", "")

        if (len(info) == 0 or (len(info) > 0 and info[0] != "track")):
            if "(" in intermediate_string and not intermediate_string.startswith("("):
                intermediate_string = intermediate_string.split("(",1)[0]
            if "[" in intermediate_string and not intermediate_string.startswith("["):
                intermediate_string = intermediate_string.split("[",1)[0]

        return intermediate_string



    def compactaliasconvert(input_string):
        conSM = sqlite3.connect('databases/scrobblemeta.db')
        curSM = conSM.cursor()
        
        alias_list = [item[0] for item in curSM.execute("SELECT artist_key FROM artist_aliases WHERE alias_name = ?", (input_string,)).fetchall()]

        if len(alias_list) == 0:
            return input_string

        else:
            result_string = alias_list[-1]

            return result_string



    def compactnamefilter(input_string, *info):
        # https://en.wikipedia.org/wiki/List_of_Latin-script_letters
        # get rid of bracket info
        if input_string is None or input_string == "":
            return ""

        edited_string = ""
        try:
            # upper case and remove brackets etc
            if len(info) > 0:
                edited_string = Utils.compactaddendumfilter(input_string, info[0]).upper()
            else:
                edited_string = input_string.upper()

            # replace & with AND
            if " & " in edited_string:
                edited_string = edited_string.replace(" & ", " AND ")

            # get rid of starting THE/A/AN
            if edited_string.startswith("THE "):
                if len(edited_string) > 4:
                    edited_string = edited_string[4:]
            elif edited_string.startswith("A "):
                if len(edited_string) > 2:
                    edited_string = edited_string[2:]
            elif edited_string.startswith("AN "):
                if len(edited_string) > 3:
                    edited_string = edited_string[3:]

            # get rid of non-alphanumeric
            filtered_string = ''.join([x for x in edited_string if x.isalnum()])

            if filtered_string == "":
                return edited_string
            else:
                edited_string = filtered_string

            # adapt accents
            edited_string = Utils.diacritic_uppercase_translation(edited_string)

            if len(info) > 1 and info[0] == "artist" and info[1] == "alias":
                edited_string = Utils.compactaliasconvert(edited_string)

            return edited_string

        except Exception as e:
            print(f"Error: {e}")
            print(traceback.format_exc())
            return edited_string



    def confirmation_check(ctx, message): # checking if it's the same user and channel
        return ((message.author == ctx.author) and (message.channel == ctx.channel))



    def convert_lfmname_to_discordname(ctx, lfmname):
        """if not possible it keeps the name but precedes it with >>lfm:<<"""
        try:
            substitute = "lfm:" + lfmname

            conNP = sqlite3.connect('databases/npsettings.db')
            curNP = conNP.cursor()
            try:
                result = curNP.execute("SELECT id FROM lastfm WHERE lfm_name = ?", (lfmname,)).fetchone()
                user_id = str(result[0])
            except Exception as e:
                return substitute

            for member in ctx.guild.members:
                if str(member.id) == user_id:
                    return member.name
            else:
                return substitute
        except:
            return substitute



    def convert_stringlist(object_list):
        result = []
        for obj in object_list:
            result.append(str(obj))
        return result


    def cut_xtrainfo(string):
        """for song titles etc: cuts everything that is probably just extra information, and not part of the song's name"""
        if "(" in string:
            string = string.split("(")[0]
        if "[" in string:
            string = string.split("[")[0]
        if "{" in string:
            string = string.split("{")[0]
        if "," in string:
            string = string.split(",")[0]
        if "Part " in string and not string.startswith("Part "):
            string = string.split("Part ")[0]
        if "Pt. " in string and not string.startswith("Pt. "):
            string = string.split("Pt. ")[0]

        return string.strip()



    def diacritic_translation(old_string):
        new_string = ""
        for c in old_string:
            c_up = c.upper()
            if c == c_up:
                new_string += Utils.diacritic_uppercase_translation(c)
            else:
                new_string += Utils.diacritic_uppercase_translation(c_up).lower()

        return new_string



    def diacritic_uppercase_translation(old_string):
        diacritics = {
            ord("Æ"): "AE",
            ord("Ã"): "A",
            ord("Å"): "A",
            ord("Ā"): "A",
            ord("Ä"): "A",
            ord("Â"): "A",
            ord("À"): "A",
            ord("Á"): "A",
            ord("Å"): "A",
            ord("Ầ"): "A",
            ord("Ấ"): "A",
            ord("Ẫ"): "A",
            ord("Ẩ"): "A",
            ord("Ą"): "A",
            ord("Ç"): "C",
            ord("Č"): "C",
            ord("Ď"): "D",
            ord("Ė"): "E",
            ord("Ê"): "E",
            ord("Ë"): "E",
            ord("È"): "E",
            ord("É"): "E",
            ord("Ě"): "E",
            ord("Ē"): "E",
            ord("Ę"): "E",
            ord("Ğ"): "G",
            ord("Í"): "I",
            ord("İ"): "I",
            ord("Ï"): "I",
            ord("Î"): "I",
            ord("Ī"): "I",
            ord("Ł"): "L",
            ord("Ñ"): "N",
            ord("Ń"): "N",
            ord("Ň"): "N",
            ord("Ō"): "O",
            ord("Ø"): "O",
            ord("Õ"): "O",
            ord("Œ"): "OE",
            ord("Ó"): "O",
            ord("Ò"): "O",
            ord("Ô"): "O",
            ord("Ö"): "O",
            ord("Ř"): "R",
            ord("Š"): "S",
            ord("ẞ"): "SS",
            ord("Ś"): "S",
            ord("Š"): "S",
            ord("Ş"): "S",
            ord("Ť"): "T",
            ord("Ū"): "U",
            ord("Ù"): "U",
            ord("Ú"): "U",
            ord("Û"): "U",
            ord("Ü"): "U",
            ord("Ů"): "U",
            ord("Ý"): "Y",
            ord("Ÿ"): "Y",
            ord("Ž"): "Z",
        }
        new_string = old_string.translate(diacritics)

        return new_string



    def emoji(name):
        try:
            con = sqlite3.connect(f'databases/botsettings.db')
            cur = con.cursor()
            emoji_list = [[item[0],item[1],item[2]] for item in cur.execute("SELECT purpose, call, extra FROM emojis").fetchall()]

            # fetch emoji by purpose name: if call is empty choose extra

            term = name.lower().strip()
            for item in emoji_list:
                if term == item[0]:
                    if item[1].strip() == "":
                        emote = item[2]
                    else:
                        emote = item[1]
                    break
            else:
                term = ''.join(e for e in name.strip().lower().replace(" ","_") if e.isalnum() or e == "_")
                for item in emoji_list:
                    if term == item[0]:
                        if item[1].strip() == "":
                            emote = item[2]
                        else:
                            emote = item[1]
                        break
                    else:
                        term = ''.join(e for e in name.strip().lower() if e.isalnum())
                        for item in emoji_list:
                            if term == item[0]:
                                if item[1].strip() == "":
                                    emote = item[2]
                                else:
                                    emote = item[1]
                                break
                            else:
                                emote = ""

            # if search was unsuccessful look for alias and choose one at random

            if emote == "":
                term = ''.join(e for e in name.strip().lower().replace(" ","_") if e.isalnum() or e == "_")
                alias_list = [[item[0],item[1]] for item in cur.execute("SELECT call, extra FROM emojis WHERE LOWER(alias) = ?", (term,)).fetchall()]

                if len(alias_list) > 0:
                    first_choice_list = []
                    second_choice_list = []

                    for item in alias_list:
                        if item[0].strip() == "":
                            emoji = item[1].strip()
                            if emoji not in second_choice_list:
                                second_choice_list.append(emoji)
                        else:
                            emoji = item[0].strip()
                            if emoji not in first_choice_list:
                                first_choice_list.append(emoji)

                    if len(first_choice_list) > 0:
                        emote = random.choice(first_choice_list)

                    elif len(second_choice_list) > 0:
                        emote = random.choice(second_choice_list)

            if emote.strip() == "":                
                print(f"Notice: Emoji with name '{name}' returned an empty string.")

            return emote.strip()

        except Exception as e:
            print("Error:", e)
            return ""



    def escapequotemarks(s):
        ctxt = str(s).replace('"','\"').replace("‘","\‘").replace("’","\’").replace("“","\“").replace("”","\”")
        return ctxt



    def filter_genretags(genre_tags):

        genre_tags_new = [] # tags to return
        genre_tags_new_alphanum = [] # check to avoid duplicates
        
        # GET BAD TAGS AND PHRASES

        conNP = sqlite3.connect('databases/npsettings.db')  
        curNP = conNP.cursor()
        bad_tags_alphanum = []
        bad_phrase_alphanum = []
        db_list = [[Utils.alphanum(item[0],"lower").strip(), item[1].lower().strip()] for item in curNP.execute("SELECT tagname, bantype FROM unwantedtags").fetchall()]

        for item in db_list:
            bantype = item[1]
            if bantype == "phrase":
                bad_phrase_alphanum.append(item[0])
            else:
                bad_tags_alphanum.append(item[0])

        regex_list = [item[0] for item in curNP.execute("SELECT regex FROM unwantedtags_regex").fetchall()]

        # FILTER

        for genre in genre_tags:
            compactname = Utils.alphanum(genre,"lower").strip()
            if len(compactname) > 2:
                if compactname[-1] == "s":
                    secondary = compactname[:-1]
                else:
                    secondary = compactname + "s"
                if compactname[-2:] == "es":
                    tertiary = compactname[-2:]
                else:
                    tertiary = compactname + "es"

                contains_no_bad_phrase = True
                for expression in regex_list:
                    try:
                        found_match = bool(re.search(expression, genre.lower()))
                        if found_match:
                            contains_no_bad_phrase = False
                    except:
                        pass

                if contains_no_bad_phrase:
                    for word in bad_phrase_alphanum:
                        if word in compactname:
                            contains_no_bad_phrase = False

                if contains_no_bad_phrase:
                    if (compactname not in bad_tags_alphanum) and (secondary not in bad_tags_alphanum) and (tertiary not in bad_tags_alphanum):
                        if (compactname not in genre_tags_new_alphanum)  and (secondary not in genre_tags_new_alphanum) and (tertiary not in genre_tags_new_alphanum):
                            genre_tags_new.append(genre.lower())
                            genre_tags_new_alphanum.append(Utils.alphanum(genre,"lower").strip())

        return genre_tags_new



    def filter_tagredundancies(genre_tags):
        # save tags along with their original position
        tag_position_list = []
        i = 0
        for tag in genre_tags:
            i += 1
            tag_position_list.append([tag.lower(), i])

        # sort tags from longest to shortest
        tag_position_list.sort(key=lambda x: len(x[0]), reverse=True)

        # filter out tags where all words were included in previous tags somewhere
        tags_to_keep = []
        found_words = []
        for tag_and_position in tag_position_list:
            tag_words = tag_and_position[0].split()

            all_words_present = True
            for word in tag_words:
                for previous_word in found_words:
                    if word in previous_word:
                        break
                else:
                    all_words_present = False
                    break

            if not all_words_present:
                tags_to_keep.append(tag_and_position)
                found_words += tag_words

        tags_to_keep.sort(key=lambda x: x[1])
        tags_to_return = []

        for tag in tags_to_keep:
            tags_to_return.append(tag[0])

        return tags_to_return



    def forcefloat(s):
        try:
            x = float(s)
        except:
            try:
                x = float(s.strip())
            except:
                x = 0
        return x



    def forcefloat_nonnegative(s):
        x = Utils.forcefloat(s)
        if x < 0:
            x = 0
        return x



    def forceinteger(s):
        try:
            i = int(s)
        except:
            try:
                i = int(s.strip())
            except:
                i = 0
        return i



    @to_thread
    def get_album_details_from_compact(artistcompact, albumcompact):
        conSM = sqlite3.connect('databases/scrobblemeta.db')
        curSM = conSM.cursor()
        albuminfo_list = [[item[0], item[1], item[2], item[3], item[4], item[5]] for item in curSM.execute("SELECT artist, album, cover_url, details, tags, last_update FROM albuminfo WHERE artist_filtername = ? AND album_filtername = ?", (artistcompact, albumcompact)).fetchall()]

        if len(albuminfo_list) > 0:
            artist = albuminfo_list[-1][0]
            album = albuminfo_list[-1][1]
            url = albuminfo_list[-1][2]
            details = str(albuminfo_list[-1][3])
            tagstring = albuminfo_list[-1][4]
            last_updated = albuminfo_list[-1][5]
        else:
            artist = None
            album = None
            url = None
            details = None
            tagstring = None
            last_updated = None

        return artist, album, url, details, tagstring, last_updated



    def get_lfmname(user_id):
        try:
            conNP = sqlite3.connect('databases/npsettings.db')
            curNP = conNP.cursor()
            lfm_list = [[item[0],item[1].lower().strip()] for item in curNP.execute("SELECT lfm_name, details FROM lastfm WHERE id = ?", (str(user_id),)).fetchall()]

            if len(lfm_list) == 0:
                return None, None

            lfm_name = lfm_list[0][0]
            status = lfm_list[0][1]

            if type(status) == str and (status.startswith("scrobble_banned") or status.endswith("inactive")):
                return None, None

            return lfm_name, status # ""/NULL or wk_banned or crown_banned

        except Exception as e:
            print(f"Error in utils.get_lfm_name(): {e}")
            return None, None



    def get_loadingbar(n, p):
        """
        n Breite des Balkens
        p = 0,1,...,100 Prozent"""
        bar = ""
        for x in range(n):
            if x < int(p * n / 100):
                bar += "█"
            else:
                bar += "░"
        return bar



    def get_main_server_id():
        try:
            con = sqlite3.connect(f'databases/botsettings.db')
            cur = con.cursor()
            return int([item[0] for item in cur.execute("SELECT value FROM botsettings WHERE name = ?", ("main server id",)).fetchall()][0])
        except:
            try:
                return int(os.getenv("guild_id"))
            except:
                return 0



    def get_milestonelist():
        milestone_list = [1]
        for x in [1,2,3,4,5,6,7,8,9]:
            for y in [1,2,3,4,5,6,7,8,9]:
                milestone = (10 ** x) * y
                milestone_list.append(milestone)
                if x == 5:
                    milestone += (10 ** (x-1)) * 5
                    milestone_list.append(milestone)
                if x > 5:
                    for z in range(9):
                        milestone += (10 ** (x-1)) * z
                        milestone_list.append(milestone)
                        
        return milestone_list



    def get_rank(ctx, ctx_lfm_name, artist):
        try:
            conNP = sqlite3.connect('databases/npsettings.db')
            curNP = conNP.cursor()
            lfm_list = [[item[0],item[1],item[2].lower().strip()] for item in curNP.execute("SELECT id, lfm_name, details FROM lastfm").fetchall()]

            conFM2 = sqlite3.connect('databases/scrobbledata_releasewise.db')
            curFM2 = conFM2.cursor()

            now = int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds())

            discordname_dict = {}
            lfmname_dict = {}
            count_list = []
            crownbanned = []
            total_plays = 0

            server_member_ids = [x.id for x in ctx.guild.members]

            # FILTER BY USER STATUS

            for useritem in lfm_list:
                try:
                    user_id = int(useritem[0])
                except Exception as e:
                    print("Error:", e)
                    continue

                lfm_name = useritem[1]
                status = useritem[2]

                if type(status) == str and (status.startswith(("wk_banned", "scrobble_banned")) or (status.endswith("inactive") and str(ctx.guild.id) == str(os.getenv("guild_id")))):
                    continue
                elif type(status) == str and status.startswith("crown_banned"):
                    crownbanned.append(user_id)

                if user_id not in server_member_ids:
                    continue

                if lfm_name in lfmname_dict:
                    continue

                lfmname_dict[user_id] = lfm_name

                # GET COUNT

                try:
                    result = curFM2.execute(f"SELECT SUM(count), MAX(last_time) FROM [{lfm_name}] WHERE artist_name = ?", (Utils.compactnamefilter(artist,"artist","alias"),))

                    try:
                        rtuple = result.fetchone()
                        try:
                            count = int(rtuple[0])
                        except:
                            count = 0
                        try:
                            last = int(rtuple[1])
                        except:
                            last = now
                            if user_id == ctx.author.id:
                                last -= 1
                    except:
                        count = 0
                        last = now
                        if user_id == ctx.author.id:
                            last -= 1

                except Exception as e:
                    if str(e).startswith("no such table"):
                        pass
                    else:
                        print("Error:", e)
                    count = 0
                    last = now
                    if user_id == ctx.author.id:
                        last -= 1

                count_list.append([user_id, count, last])
                total_plays += count

            # FETCH SERVER NAMES

            for member in ctx.guild.members:
                if member.id in lfmname_dict:
                    discordname_dict[member.id] = str(member.name)

            # GET RANK

            ctx_rank = -1
            posuser_counter = 0

            count_list.sort(key=lambda x: x[2])
            count_list.sort(key=lambda x: x[1], reverse=True)

            for listitem in count_list:
                user_id = listitem[0]
                playcount = listitem[1]
                lastplay = listitem[2]

                if user_id not in discordname_dict:
                    continue

                if playcount > 0:
                    posuser_counter += 1

                    if ctx_lfm_name.upper().strip() == lfmname_dict[user_id].upper().strip():
                        ctx_rank = posuser_counter

            if ctx_rank != -1:
                ordinal = Utils.ordinal_suffix(ctx_rank)
                ctx_rank_string = f"[{ctx_rank}{ordinal}/{posuser_counter}]"
            else:
                ordinal = Utils.ordinal_suffix(posuser_counter+1)
                ctx_rank_string = f"[{posuser_counter+1}{ordinal}/{posuser_counter}]"

            # GET CROWN HOLDER

            crown_user = None
            crown_count = None

            try:
                conSS = sqlite3.connect('databases/scrobblestats.db')
                curSS = conSS.cursor()
                crowns_list = [[item[0],item[1]] for item in curSS.execute(f"SELECT crown_holder, playcount FROM crowns_{ctx.guild.id} WHERE UPPER(artist) = ?", (artist.upper(),)).fetchall()]
                crown_user = crowns_list[0][0]
                crown_count = crowns_list[0][1]
            except:
                pass

            return ctx_rank_string, crown_user, crown_count

        except Exception as e:
            print(f"Error in utils.get_rank(): {e}")
            return "", None


    
    def get_scrobble_fullname(compactname, wk_type):
        """INPUT is either an upper case alphanumeric string for artist, or such a string with a hyphen to seperate artist from track/album

        returns 1 string for wk_type artist, return 2 strings for wk_type album and track"""

        conSM = sqlite3.connect('databases/scrobblemeta.db')
        curSM = conSM.cursor()

        ### ARTIST ###
        if wk_type.lower().strip() == "artist":

            if "-" not in compactname:
                artistcompact = compactname.strip().upper()

                try:
                    result = curSM.execute(f"SELECT artist FROM artistinfo WHERE filtername = ?", (artistcompact,))
                    rtuple = result.fetchone()

                    artist = str(rtuple[0])
                    db_entry_exists = True
                except:
                    artist = artistcompact
                    db_entry_exists = False

            else:
                artistcompact  = compactname.split("-")[0].strip().upper()
                releasecompact = compactname.split("-")[1].strip().upper()

                # 1) TRY ARTIST-ALBUM MATCH
                try:
                    result = curSM.execute(f"SELECT artist FROM albuminfo WHERE artist_filtername = ? AND album_filtername = ?", (artistcompact, releasecompact))
                    rtuple = result.fetchone()

                    artist = str(rtuple[0])
                    db_entry_exists = True
                except:
                    # 2) TRY ARTIST-TRACK MATCH
                    try:
                        result = curSM.execute(f"SELECT artist FROM trackinfo WHERE artist_filtername = ? AND track_filtername = ?", (artistcompact, releasecompact))
                        rtuple = result.fetchone()

                        artist = str(rtuple[0])
                        db_entry_exists = True
                    except:
                        # 3) TRY ARTIST MATCH
                        try:
                            result = curSM.execute(f"SELECT artist FROM artistinfo WHERE filtername = ?", (artistcompact,))
                            rtuple = result.fetchone()

                            artist = str(rtuple[0])
                            db_entry_exists = True
                        except:
                            # 4) USE INPUT
                            artist = artistcompact
                            db_entry_exists = False

            return artist

        ### ALBUM/TRACK ###
        else:
            if "-" not in compactname:
                raise ValueError("util.get_scrobble_fullname() received argument in wrong format")

            artistcompact  = compactname.split("-")[0].strip().upper()
            releasecompact = compactname.split("-")[1].strip().upper()

            if wk_type.lower().strip() == "album":
                # SEARCH4 ARTIST-ALBUM MATCH
                try:
                    result = curSM.execute(f"SELECT artist, album FROM albuminfo WHERE artist_filtername = ? AND album_filtername = ?", (artistcompact, releasecompact))
                    rtuple = result.fetchone()

                    artist  = str(rtuple[0])
                    release = str(rtuple[1])
                    db_entry_exists = True
                except:
                    db_entry_exists = False
            else:
                # SEARCH4 ARTIST-TRACK MATCH
                try:
                    result = curSM.execute(f"SELECT artist, track FROM trackinfo WHERE artist_filtername = ? AND track_filtername = ?", (artistcompact, releasecompact))
                    rtuple = result.fetchone()

                    artist  = str(rtuple[0])
                    release = str(rtuple[1])
                    db_entry_exists = True
                except:
                    db_entry_exists = False

            if not db_entry_exists:
                # OTHERWISE TRY ARTIST ONLY
                try:
                    result = curSM.execute(f"SELECT artist FROM artistinfo WHERE filtername = ?", (artistcompact,))
                    rtuple = result.fetchone()

                    artist = str(rtuple[0])
                    db_entry_exists = True
                except:
                    # 4) USE INPUT
                    artist = artistcompact
                    db_entry_exists = False

                release = releasecompact

            return artist, release



    def get_server_created_utc(ctx):
        creation_time = ctx.guild.created_at
        return int((creation_time.replace(tzinfo=None) - datetime(1970, 1, 1)).total_seconds())



    def get_version():
        con = sqlite3.connect(f'databases/activity.db')
        cur = con.cursor()
        version_list = [item[0] for item in cur.execute("SELECT value FROM version WHERE name = ?", ("version",)).fetchall()]

        if len(version_list) == 0:
            version = "version ?"            
        else:
            version = version_list[0] 

        return version



    def get_version_from_file():
        try:
            lines = []
            with open('other/version.txt', 'r') as s:
                for line in s:
                    lines.append(line.strip())
            version = lines[0]
        except Exception as e:
            version = "version ?"
            print("Error with version check:", e)

        return version



    def hexcolor(arg):
        color_dict = {
            #BLUE
            "dodger blue":          0x1e90ff,
            "night blue":           0x151b54,
            "aqua":                 0x00ffff,
            "turquoise":            0x30d5c8,
            #PINK
            "rose":                 0xf33a6a,
            "pink":                 0xffc0cb,
            "dark pink":            0xaa336a,
            #PURPLE
            "violet":               0x7f00ff,
            "bright purple":        0xbf40bf,
            #RED
            "crimson red":          0xb90e0a, 
            #ORANGE
            "orange":               0xffa500,
            #GREEN
            "emerald green":        0x50c878,
            "forest green":         0x228b22,
            "light green":          0x90ee90,
            #YELLOW
            "amber":                0xffbf00,
            "yellow":               0xffff00,
            #BROWN
            "beige":                0xf5f5dc,
            "reddish brown":        0xa8422d,
            #GRAYSCALE
            "white":                0xffffff,
            "black":                0x000000,
        }

        if arg.lower().strip() in color_dict:
            return color_dict[arg.lower().strip()]
        else:
            return 0x000000


    def hexmatch(arg):
        # return True if arg is a hexcolor in #000000 format
        return re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', arg)



    def hexstring(arg):
        try:
            s = "#" + '{0:06x}'.format(arg)
            return s
        except:
            return "#000000"



    def int_to_numemoji(number, *fill):
        emojinum_dict = {
                "0": "0️⃣",
                "1": "1️⃣",
                "2": "2️⃣",
                "3": "3️⃣",
                "4": "4️⃣",
                "5": "5️⃣",
                "6": "6️⃣",
                "7": "7️⃣",
                "8": "8️⃣",
                "9": "9️⃣",
            }
        string = str(number)
        emoji_string = ""

        count = 0
        for c in string:
            if c in emojinum_dict:
                emoji_string += emojinum_dict[c]
                count += 1

        try:
            if len(fill) > 0:
                digits = int(fill[0])

                while digits > count:
                    emoji_string = emojinum_dict["0"] + emoji_string
                    count += 1
        except Exception as e:
            print(e)

        return emoji_string



    def is_url_image(image_url):
        burp0_headers = {"Sec-Ch-Ua": "\"Chromium\";v=\"121\", \"Not A(Brand\";v=\"99\"", "Sec-Ch-Ua-Mobile": "?0", "Sec-Ch-Ua-Platform": "\"Windows\"", "Upgrade-Insecure-Requests": "1", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.160 Safari/537.36", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7", "Sec-Fetch-Site": "none", "Sec-Fetch-Mode": "navigate", "Sec-Fetch-User": "?1", "Sec-Fetch-Dest": "document", "Accept-Encoding": "gzip, deflate, br", "Accept-Language": "en-US;q=0.8,en;q=0.7", "Priority": "u=0, i", "Connection": "close"}      
        image_formats = ("image/png", "image/jpeg", "image/jpg", "image/webp", "image/gif")
        r = requests.head(image_url, headers=burp0_headers)
        #print("URL TEST:", r.headers["content-type"])
        if r.headers["content-type"] in image_formats:
            return True
        return False



    def isocode(s):
        """tries to convert string to ISO country code
        can return ERROR string if no matches found"""
        ISO3166 = Utils.isolist()
        substitute_dict = {
                'UK': 'GB',
        }

        if len(s) < 4:
            if s.upper() in substitute_dict.keys():
                v = substitute_dict[s.upper()]
                return v
                
            return s.upper()

        for k,v in ISO3166.items():
            if s.lower() == v.lower():
                return k
        else:
            for k,v in ISO3166.items():
                if s.lower() in v.lower():
                    return k
            else:
                for k,v in ISO3166.items():
                    if len(s) > 2 and Utils.alphanum(s,"lower") in Utils.alphanum(v,"lower"):
                        return k
                else:
                    return "ERROR"



    def isocode_to_name(s):
        """tries to convert string to ISO country code
        can return ERROR string if no matches found"""
        if len(s) != 2:
            return s

        ISO3166 = Utils.isolist()

        if s.upper() in ISO3166:
            finding = ISO3166[s.upper()]

            return finding.split("(")[0].split(",")[0].strip()



    def isolist():
        ISO3166 = {
            'AD': 'Andorra',
            'AE': 'United Arab Emirates',
            'AF': 'Afghanistan',
            'AG': 'Antigua & Barbuda',
            'AI': 'Anguilla',
            'AL': 'Albania',
            'AM': 'Armenia',
            'AN': 'Netherlands Antilles',
            'AO': 'Angola',
            'AQ': 'Antarctica',
            'AR': 'Argentina',
            'AS': 'American Samoa',
            'AT': 'Austria',
            'AU': 'Australia',
            'AW': 'Aruba',
            'AZ': 'Azerbaijan',
            'BA': 'Bosnia and Herzegovina',
            'BB': 'Barbados',
            'BD': 'Bangladesh',
            'BE': 'Belgium',
            'BF': 'Burkina Faso',
            'BG': 'Bulgaria',
            'BH': 'Bahrain',
            'BI': 'Burundi',
            'BJ': 'Benin',
            'BM': 'Bermuda',
            'BN': 'Brunei Darussalam',
            'BO': 'Bolivia',
            'BR': 'Brazil',
            'BS': 'Bahama',
            'BT': 'Bhutan',
            'BU': 'Burma (no longer exists)',
            'BV': 'Bouvet Island',
            'BW': 'Botswana',
            'BY': 'Belarus',
            'BZ': 'Belize',
            'CA': 'Canada',
            'CC': 'Cocos (Keeling) Islands',
            'CF': 'Central African Republic',
            'CG': 'Congo',
            'CH': 'Switzerland',
            'CI': 'Côte D\'ivoire (Ivory Coast)',
            'CK': 'Cook Iislands',
            'CL': 'Chile',
            'CM': 'Cameroon',
            'CN': 'China',
            'CO': 'Colombia',
            'CR': 'Costa Rica',
            'CS': 'Czechoslovakia (no longer exists)',
            'CU': 'Cuba',
            'CV': 'Cape Verde',
            'CX': 'Christmas Island',
            'CY': 'Cyprus',
            'CZ': 'Czech Republic',
            'DD': 'German Democratic Republic (no longer exists)',
            'DE': 'Germany',
            'DJ': 'Djibouti',
            'DK': 'Denmark',
            'DM': 'Dominica',
            'DO': 'Dominican Republic',
            'DZ': 'Algeria',
            'EC': 'Ecuador',
            'EE': 'Estonia',
            'EG': 'Egypt',
            'EH': 'Western Sahara',
            'ER': 'Eritrea',
            'ES': 'Spain',
            'ET': 'Ethiopia',
            'FI': 'Finland',
            'FJ': 'Fiji',
            'FK': 'Falkland Islands (Malvinas)',
            'FM': 'Micronesia',
            'FO': 'Faroe Islands',
            'FR': 'France',
            'FX': 'France, Metropolitan',
            'GA': 'Gabon',
            'GB': 'United Kingdom (Great Britain)',
            'GD': 'Grenada',
            'GE': 'Georgia',
            'GF': 'French Guiana',
            'GH': 'Ghana',
            'GI': 'Gibraltar',
            'GL': 'Greenland',
            'GM': 'Gambia',
            'GN': 'Guinea',
            'GP': 'Guadeloupe',
            'GQ': 'Equatorial Guinea',
            'GR': 'Greece',
            'GS': 'South Georgia and the South Sandwich Islands',
            'GT': 'Guatemala',
            'GU': 'Guam',
            'GW': 'Guinea-Bissau',
            'GY': 'Guyana',
            'HK': 'Hong Kong',
            'HM': 'Heard & McDonald Islands',
            'HN': 'Honduras',
            'HR': 'Croatia',
            'HT': 'Haiti',
            'HU': 'Hungary',
            'ID': 'Indonesia',
            'IE': 'Ireland',
            'IL': 'Israel',
            'IN': 'India',
            'IO': 'British Indian Ocean Territory',
            'IQ': 'Iraq',
            'IR': 'Islamic Republic of Iran',
            'IS': 'Iceland',
            'IT': 'Italy',
            'JM': 'Jamaica',
            'JO': 'Jordan',
            'JP': 'Japan',
            'KE': 'Kenya',
            'KG': 'Kyrgyzstan',
            'KH': 'Cambodia',
            'KI': 'Kiribati',
            'KM': 'Comoros',
            'KN': 'St. Kitts and Nevis',
            'KP': 'Korea, Democratic People\'s Republic of',
            'KR': 'Korea, Republic of',
            'KW': 'Kuwait',
            'KY': 'Cayman Islands',
            'KZ': 'Kazakhstan',
            'LA': 'Lao People\'s Democratic Republic',
            'LB': 'Lebanon',
            'LC': 'Saint Lucia',
            'LI': 'Liechtenstein',
            'LK': 'Sri Lanka',
            'LR': 'Liberia',
            'LS': 'Lesotho',
            'LT': 'Lithuania',
            'LU': 'Luxembourg',
            'LV': 'Latvia',
            'LY': 'Libyan Arab Jamahiriya',
            'MA': 'Morocco',
            'MC': 'Monaco',
            'MD': 'Moldova, Republic of',
            'MG': 'Madagascar',
            'MH': 'Marshall Islands',
            'ML': 'Mali',
            'MN': 'Mongolia',
            'MM': 'Myanmar',
            'MO': 'Macau',
            'MP': 'Northern Mariana Islands',
            'MQ': 'Martinique',
            'MR': 'Mauritania',
            'MS': 'Monserrat',
            'MT': 'Malta',
            'MU': 'Mauritius',
            'MV': 'Maldives',
            'MW': 'Malawi',
            'MX': 'Mexico',
            'MY': 'Malaysia',
            'MZ': 'Mozambique',
            'NA': 'Namibia',
            'NC': 'New Caledonia',
            'NE': 'Niger',
            'NF': 'Norfolk Island',
            'NG': 'Nigeria',
            'NI': 'Nicaragua',
            'NL': 'Netherlands',
            'NO': 'Norway',
            'NP': 'Nepal',
            'NR': 'Nauru',
            'NT': 'Neutral Zone (no longer exists)',
            'NU': 'Niue',
            'NZ': 'New Zealand',
            'OM': 'Oman',
            'PA': 'Panama',
            'PE': 'Peru',
            'PF': 'French Polynesia',
            'PG': 'Papua New Guinea',
            'PH': 'Philippines',
            'PK': 'Pakistan',
            'PL': 'Poland',
            'PM': 'St. Pierre & Miquelon',
            'PN': 'Pitcairn',
            'PR': 'Puerto Rico',
            'PT': 'Portugal',
            'PW': 'Palau',
            'PY': 'Paraguay',
            'QA': 'Qatar',
            'RE': 'Réunion',
            'RO': 'Romania',
            'RU': 'Russian Federation',
            'RW': 'Rwanda',
            'SA': 'Saudi Arabia',
            'SB': 'Solomon Islands',
            'SC': 'Seychelles',
            'SD': 'Sudan',
            'SE': 'Sweden',
            'SG': 'Singapore',
            'SH': 'St. Helena',
            'SI': 'Slovenia',
            'SJ': 'Svalbard & Jan Mayen Islands',
            'SK': 'Slovakia',
            'SL': 'Sierra Leone',
            'SM': 'San Marino',
            'SN': 'Senegal',
            'SO': 'Somalia',
            'SR': 'Suriname',
            'ST': 'Sao Tome & Principe',
            'SU': 'Union of Soviet Socialist Republics (no longer exists)',
            'SV': 'El Salvador',
            'SY': 'Syrian Arab Republic',
            'SZ': 'Swaziland',
            'TC': 'Turks & Caicos Islands',
            'TD': 'Chad',
            'TF': 'French Southern Territories',
            'TG': 'Togo',
            'TH': 'Thailand',
            'TJ': 'Tajikistan',
            'TK': 'Tokelau',
            'TM': 'Turkmenistan',
            'TN': 'Tunisia',
            'TO': 'Tonga',
            'TP': 'East Timor',
            'TR': 'Turkey',
            'TT': 'Trinidad & Tobago',
            'TV': 'Tuvalu',
            'TW': 'Taiwan, Province of China',
            'TZ': 'Tanzania, United Republic of',
            'UA': 'Ukraine',
            'UG': 'Uganda',
            'UM': 'United States Minor Outlying Islands',
            'US': 'United States of America',
            'UY': 'Uruguay',
            'UZ': 'Uzbekistan',
            'VA': 'Vatican City State (Holy See)',
            'VC': 'St. Vincent & the Grenadines',
            'VE': 'Venezuela',
            'VG': 'British Virgin Islands',
            'VI': 'United States Virgin Islands',
            'VN': 'Viet Nam',
            'VU': 'Vanuatu',
            'WF': 'Wallis & Futuna Islands',
            'WS': 'Samoa',
            'XK': 'Kosovo (user assigned code)',
            'YD': 'Democratic Yemen (no longer exists)',
            'YE': 'Yemen',
            'YT': 'Mayotte',
            'YU': 'Yugoslavia',
            'ZA': 'South Africa',
            'ZM': 'Zambia',
            'ZR': 'Zaire',
            'ZW': 'Zimbabwe',
            'ZZ': 'Unknown or unspecified country',
        }

        return ISO3166



    def jprint(obj):
        # create a formatted string of the Python JSON object
        try:
            text = json.dumps(obj, sort_keys=True, indent=4)
            print(text)
        except:
            text = json.dumps(obj.json(), sort_keys=True, indent=4)
            print(text)



    def last_scrobble_time_in_db():
        lasttime = 0
        con = sqlite3.connect(f'databases/scrobbledata_releasewise.db')
        cur = con.cursor()  
        table_list = [item[0] for item in cur.execute("SELECT name FROM sqlite_master WHERE type = ?", ("table",)).fetchall()]
        #print(table_list)
        for table in table_list:
            try:
                result = con.execute(f'SELECT MAX(last_time) FROM [{table}]')
                rtuple = result.fetchone()
                if int(rtuple[0]) > lasttime:
                    lasttime = int(rtuple[0])
            except Exception as e:
                print(f"Skipping table {table}:", e)
                continue

        return lasttime



    def months_to_seconds(number_of_months, day_of_month, from_timestamp):

        # FETCH REFERENCE POINT IN TIME

        if from_timestamp is not None and from_timestamp != "":
            ts = int(from_timestamp)
            year = datetime.utcfromtimestamp(ts).year
            month = datetime.utcfromtimestamp(ts).month
            day = datetime.utcfromtimestamp(ts).day
        else:
            year = datetime.utcnow().year
            month = datetime.utcnow().month
            day = datetime.utcnow().day
        today = date(year, month, day)

        # PARSE ARGUMENTS

        try:
            number_of_months = int(number_of_months)
        except:
            raise ValueError("months_to_seconds() got a non-integer variable as number_of_months")
        try:
            if day_of_month is None or day_of_month == "":
                day_of_month = day
            elif day_of_month.lower() == "last":
                day_of_month = 31
            else:
                day_of_month = int(day_of_month)
        except:
            raise ValueError("months_to_seconds() got a non-integer variable as day_of_month")

        # CALCULATE NEXT

        if month + number_of_months <= 12:
            newyear = year
            newmonth = month + number_of_months
        else:
            newyear = year + ((month + number_of_months - 1) // 12)
            newmonth = ((month + number_of_months - 1) % 12) + 1

        newmonth_daystotal = monthrange(newyear, newmonth)[1]

        if day_of_month > 0 and day_of_month < 32:
            # NEXT DATE BY PRE-GIVEN DAY OF MONTH
            if day_of_month > newmonth_daystotal:
                newday = newmonth_daystotal
            else:
                newday = day_of_month
        else:
            # NEXT DATE VIA *THIS* DAY OF MONTH
            if day > newmonth_daystotal:
                newday = newmonth_daystotal
            else:
                newday = day
            
        future = date(newyear, newmonth, newday)
        diff = (future - today).days
        seconds = diff * 24*60*60

        return seconds 



    def ordinal_suffix(num):
        try:
            n = int(num)
            s = str(n)

            if s[-1] in ["1", "2", "3"]:
                if len(s) > 1 and s[-2] == "1":
                    return "th"
                else:
                    if s[-1] == "1":
                        return "st"
                    elif s[-1] == "2":
                        return "nd"
                    elif s[-1] == "3":
                        return "rd"
                    else:
                        return ""
            else:
                return "th" 
        except:
            return ""



    def reccuring_time_to_seconds(text, *from_timestamp):
        """takes 2 string arguments
        returns amount of seconds needed to add to unixtime to arrive at next ocurrence

        for monthly and yearly this needs to be relative to a timestamp or the current day

        possible text parameters:
            > daily, weekly, fortnightly, biweekly
            > monthly, yearly
            > monthly on 17th
            > yearly march 5th
            > every 2nd day
            > every 3rd week
            > every 4th month
            > every 1st month on last
        for month and year parameters you can provide from_timestamp which should be a string of a UNIX timestamp integer
        """
        if len(from_timestamp) > 0:
            ts = from_timestamp[0]
        else:
            ts = None

        text = text.lower().strip()
        if text in ["daily"]:
            seconds = 24*60*60
            return seconds

        if text in ["weekly"]:
            seconds = 7*24*60*60
            return seconds

        if text in ["fortnightly", "biweekly"]:
            seconds = 2*7*24*60*60
            return seconds

        if text.startswith("monthly"):

            second_arg = text.split()[-1]
            if second_arg.endswith("st") or second_arg.endswith("nd") or second_arg.endswith("rd") or second_arg.endswith("th"):
                second_arg = second_arg[:-2]

            seconds = Utils.months_to_seconds(1, second_arg, ts)
            return seconds

        if text.startswith("yearly"):
            provided_date_arg = False

            if len(text.split()) >= 3:
                i = 0
                if len(text.split()) >= 4 and text.split()[1] == "on":
                    i = 1
                second_arg = text.split()[1+i]
                third_arg = text.split()[2+i]
                if third_arg.endswith("st", "nd", "rd", "th"):
                    third_arg = third_arg[:-2]

                if Utils.represents_integer(third_arg) and int(third_arg) > 0 and int(third_arg) < 32:
                    target_day = int(third_arg)
                    if second_arg.endswith("bre"):
                        second_arg.replace("bre", "ber")
                    months = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]
                    if second_arg in months:
                        target_month = months.index(second_arg) + 1
                        provided_date_arg = True

            seconds = Utils.years_to_seconds(amount_of_years, target_month, third_arg, ts)
            return seconds

        if text.startswith("every") and len(text.split()) >= 3:
            second_arg = text.split()[1]
            if second_arg.endswith("st") or second_arg.endswith("nd") or second_arg.endswith("rd") or second_arg.endswith("th"):
                second_arg = second_arg[:-2]
            third_arg = text.split()[2]

            if Utils.represents_integer(second_arg) and int(second_arg) > 0 and third_arg in ["day", "week", "month"]:
                amount = int(second_arg)
                if third_arg in ["day", "week"]:
                    if third_arg == "day":
                        days = 1
                    else:
                        days = 7
                    seconds = amount*days*24*60*60
                    return seconds

                # every x-th month
                if len(text.split()) >= 4 and text.split()[-1].strip() == "last":
                    seconds = Utils.months_to_seconds(amount, 31, ts)
                else:
                    seconds = Utils.months_to_seconds(amount, second_arg, ts)

                return seconds

        # ERROR, SHOULD HAVE RETURNED BY NOW
        print(f"Error in reccuring_time_to_seconds with the term: {text}")
        raise ValueError(f"function reccuring_time_to_seconds() had issues parsing: {text}")



    def represents_float(s):
        """checks if string is float or integer"""
        dots = s.count(".")
        if dots > 1:
            return False

        if s.startswith("."):
            return False

        s = s.replace(".","")
        if len(s) == 0:
            return False

        for char in s:
            if char not in ["0","1","2","3","4","5","6","7","8","9"]:
                return False 

        return True



    def represents_integer(s):
        """checks if string is integer or float ending with .0"""
        if s.startswith("-") or s.startswith("+"):
            s = s[1:]
        if s.endswith(".0"):
            s = s[:-2]

        if len(s) < 1:
            return False 

        is_int = True 
        for char in s:
            if char not in ["0","1","2","3","4","5","6","7","8","9"]:
                is_int = False 

        return is_int



    def seconds_to_readabletime(i, shortform, *from_timestamp):
        """arg: integer
           optional arg: integer
           return: text """
        if shortform is None:
            shortform = False

        if i < 0:
            negative = True 
            abs_value = -1 * i
        else:
            negative = False 
            abs_value = i

        # FETCHING VALUES

        years = 0 
        months = 0 
        days = 0 
        hours = 0
        minutes = 0
        seconds = 0

        unit_seconds = Utils.unit_seconds()

        if len(from_timestamp) == 0 or from_timestamp[0] == None:

            # NAIVE WAY TO CALCULATE

            if abs_value >= 4 * unit_seconds["naive_year"] + unit_seconds["day"]: 
                quadyears = math.floor(abs_value / (4 * unit_seconds["naive_year"] + unit_seconds["day"]))
                years += 4 * quadyears
                abs_value -= quadyears * (4 * unit_seconds["naive_year"] + unit_seconds["day"])

            if abs_value >= unit_seconds["naive_year"]:
                additional_years = math.floor(abs_value / unit_seconds["naive_year"])
                years += additional_years
                abs_value -= additional_years * unit_seconds["naive_year"]

            if abs_value >= unit_seconds["naive_month"]: 
                months += math.floor(abs_value / unit_seconds["naive_month"])
                abs_value -= months * unit_seconds["naive_month"]

            if abs_value >= unit_seconds["days"]:
                days += math.floor(abs_value / unit_seconds["days"])
                abs_value -= days * unit_seconds["days"]

            if abs_value >= unit_seconds["hours"]:
                hours += math.floor(abs_value / unit_seconds["hours"])
                abs_value -= hours * unit_seconds["hours"]

            if abs_value >= unit_seconds["minutes"]:
                minutes += math.floor(abs_value / unit_seconds["minutes"])
                abs_value -= minutes * unit_seconds["minutes"]

            seconds += abs_value

        else:
            # RELATIVE WAY
            ts = int(from_timestamp[0])

            today = datetime.utcfromtimestamp(ts)
            future = datetime.utcfromtimestamp(ts+abs_value)
            delta = future - today

            days = delta.days
            hours = delta.seconds // 3600
            minutes = (delta.seconds - 3600 * hours) // 60
            seconds = delta.seconds - 3600 * hours - 60 * minutes

            oldyear = datetime.utcfromtimestamp(ts).year
            oldmonth = datetime.utcfromtimestamp(ts).month
            oldday = datetime.utcfromtimestamp(ts).day

            newyear = (datetime.utcfromtimestamp(ts) + timedelta(days = days)).year
            newmonth = (datetime.utcfromtimestamp(ts) + timedelta(days = days)).month
            newday = (datetime.utcfromtimestamp(ts) + timedelta(days = days)).day

            years = newyear - oldyear

            if newmonth - oldmonth < 0:
                years -= 1
                months = newmonth + 12 - oldmonth
            else:
                months = newmonth - oldmonth

            if newday - oldday < 0:
                if newmonth == 1:
                    if newmonth - oldmonth == 0:
                        years -= 1
                months -= 1
                days = newday - oldday + monthrange(newyear, newmonth)[1]
            else:
                days = newday - oldday # overwrite
        

        ### TURNING VALUES INTO TEXT

        if shortform:
            if years > 0:
                timetext = f"{years}y"
                if months > 0:
                    timetext += f" {months}mon"
                if days > 0:
                    timetext += f" {days}d"

            elif months > 0:
                timetext = f"{months}mon"
                if days > 0:
                    timetext += f" {days}d"

            elif days > 0:
                timetext = f"{days}d"
                if hours > 0:
                    timetext += f" {hours}h"

            elif hours > 0:
                timetext = f"{hours}h"
                if minutes > 0:
                    timetext += f" {minutes}min"

            elif minutes > 0:
                timetext = f"{minutes}min"
                if seconds > 0:
                    timetext += f" {seconds}s"
            else:
                timetext = f"{seconds}s"

            if negative:
                timetext = "-" + timetext 

        else:
            if years > 0:
                timetext = f"{years} year"
                if years > 1:
                    timetext += "s"
                if months > 0:
                    timetext += f" {months} month"
                    if months > 1:
                        timetext += "s"
                if days > 0:
                    timetext += f" {days} day"
                    if days > 1:
                        timetext += "s"

            elif months > 0:
                timetext = f"{months} month"
                if months > 1:
                    timetext += "s"
                if days > 0:
                    timetext += f" {days} day"
                    if days > 1:
                        timetext += "s"

            elif days > 0:
                timetext = f"{days} day"
                if days > 1:
                    timetext += "s"
                if hours > 0:
                    timetext += f" {hours} hour"
                    if hours > 1:
                        timetext += "s"

            elif hours > 0:
                timetext = f"{hours} hour"
                if hours > 1:
                    timetext += "s"
                if minutes > 0:
                    timetext += f" {minutes} minute"
                    if minutes > 1:
                        timetext += "s"

            elif minutes > 0:
                timetext = f"{minutes} minute"
                if minutes > 1:
                    timetext += "s"
                if seconds > 0:
                    timetext += f" {seconds} second"
                    if seconds > 1:
                        timetext += "s"

            else:
                timetext = f"{seconds} second"
                if seconds > 1:
                    timetext += "s" 

            if negative:
                timetext = "negative " + timetext 

        return timetext



    def separate_num_alph(s):
        res = re.split('([-+]?\d+\.\d+)|([-+]?\d+)', s.strip())
        res_filtered = [r.strip() for r in res if r is not None and r.strip() != '']
        return res_filtered



    def separate_num_alph_componentpreserving(s):
        """preserves emoji, channels, roles, pings and timestamps"""
        pre_list = s.strip().split()
        final_list = []
        for word in pre_list:
            if len(word) > 17 and word.endswith(">") and (word.startswith("<@") or word.startswith("<#")) and Utils.represents_integer(word[2:-1]):
                # channel or role
                final_list.append(word)

            elif len(word) > 17 and word.endswith(">") and word.startswith("<@&") and Utils.represents_integer(word[3:-1]):
                # user ping
                final_list.append(word)

            elif len(word) > 7 and word.endswith(">") and word[-3] == ":" and word[-2] in ["d", "D", "t", "T", "f", "F", "R"] and word.startswith("<t:") and Utils.represents_integer(word[3:-3]):
                # hammer time
                final_list.append(word)

            elif len(word) > 17 and word.endswith(">") and word.startswith("<:") and ":" in word[2:-1] and len(word[2:-1].split(":")[0]) > 1 and Utils.represents_integer(word[2:-1].split(":")[1]):
                # custom static emoji
                final_list.append(word)
            
            elif len(word) > 18 and word.endswith(">") and word.startswith("<a:") and ":" in word[3:-1] and len(word[3:-1].split(":")[0]) > 1 and Utils.represents_integer(word[3:-1].split(":")[1]):    
                # custom animated emoji
                final_list.append(word)

            elif word in UNICODE_EMOJI['en']:
                # default emoji
                final_list.append(word)

            elif word.startswith("https://") or (word.startswith("[") and "](https://" in word and word.endswith(")")):
                # URL
                final_list.append(word)

            elif word.startswith("<https://") and word.endswith(">"):
                # unembedded URL
                final_list.append(word)

            else:
                res = re.split('([-+]?\d+\.\d+)|([-+]?\d+)', word.strip())
                res_filtered = [r.strip() for r in res if r is not None and r.strip() != '']
                final_list += res_filtered

        return final_list



    def separate_num_alph_string(s):
        res = ' '.join(Utils.separate_num_alph(s))
        return res



    def separate_num_alph_string_componentpreserving(s):
        res = ' '.join(Utils.separate_num_alph_componentpreserving(s))
        return res



    def setting_enabled(name):
        """Checks if a setting is enabled and returns True or False"""
        conB = sqlite3.connect(f'databases/botsettings.db')
        curB = conB.cursor()
        setting_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", (name,)).fetchall()]
        if len(setting_list) == 0:
            setting = "off"
        else:
            if len(setting_list) > 1:
                print(f"Warning: Multiple '{name}' entries in serversettings.")
            setting = setting_list[0].lower().strip()

        if setting == "on":
            return True
        else:
            return False



    def shortnum(s):
        """converts number to shortform for readability
            accepts string or integer
        """
        def leading_order(x, exp):
            lo_term = round(x/(10 ** exp), 1)
            lo_string = str(lo_term)

            if len(lo_string) > 4:
                lo_string = lo_string[:-2]

            if lo_string.endswith(".0") and exp < 15:
                lo_string = lo_string[:-2]

            return lo_string


        try:
            num = int(s)

            if num >= 1000 ** 5:
                order = len(str(num)) - 1
                shortnum = leading_order(num, order) + f"10^{order}"
            elif num >= 1000 ** 4:
                shortnum = leading_order(num, 12) + "T"
            elif num >= 1000 ** 3:
                shortnum = leading_order(num, 9) + "B"
            elif num >= 1000 ** 2:
                shortnum = leading_order(num, 6) + "M"
            elif num >= 1000 ** 1:
                shortnum = leading_order(num, 3) + "K"
            else:
                shortnum = str(num)

            return shortnum
        except:
            return s



    def urlfriendlytext(string):

        if string[0] != "(" and "(" in string and ")" in string.split("(",1)[1]:
            filtered_string = string.split("(",1)[0]
        elif string[0] != "[" and "[" in string and "]" in string.split("[",1)[1]:
            filtered_string = string.split("[",1)[0]
        else:
            filtered_string = string

        new_string = " "
        i = 0
        for c in filtered_string:
            if c.isalnum():
                new_string += c.lower()
                i += 1
            else:
                if new_string[i] == "":
                    pass
                else:
                    new_string += " "
                    i += 1

        return new_string.strip()      



    def update_artistinfo(artist, artist_thumbnail, tags): # doubled from scrobble_utility.py
        try: # update stats
            now = int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds())
            artist_fltr = Utils.compactnamefilter(artist,"artist","alias")
            tags_lfm = ';'.join(tags)
            try:
                conSS = sqlite3.connect('databases/scrobblestats.db')
                curSS = conSS.cursor()
                result = curSS.execute(f"SELECT artist, thumbnail, tags_lfm, tags_other, last_update FROM artistinfo WHERE filtername = ? OR filteralias = ?", (artist_fltr,artist_fltr))
                rtuple = result.fetchone()
                #print("DB finding:", rtuple)
                test1 = str(rtuple[0])
                test2 = str(rtuple[1])
                test3 = str(rtuple[2]).split(";") + str(rtuple[3]).split(";")
                tset4 = int(rtuple[4])
                db_entry_exists = True
            except:
                db_entry_exists = False
            if db_entry_exists:
                # do not update thumbnail
                curSS.execute(f"UPDATE artistinfo SET tags_lfm = ?, last_update = ? WHERE filtername = ? OR filteralias = ?", (tags_lfm, now, artist_fltr, artist_fltr))
            else:
                curSS.execute(f"INSERT INTO artistinfo VALUES (?, ?, ?, ?, ?, ?, ?)", (artist, artist_thumbnail, tags_lfm, "", now, artist_fltr, ""))
            conSS.commit()
        except Exception as e:
            print("Error:", e)    



    def us_state_code(s):
        us_state_to_abbrev = {
            "Alabama": "AL",
            "Alaska": "AK",
            "Arizona": "AZ",
            "Arkansas": "AR",
            "California": "CA",
            "Colorado": "CO",
            "Connecticut": "CT",
            "Delaware": "DE",
            "Florida": "FL",
            "Georgia": "GA",
            "Hawaii": "HI",
            "Idaho": "ID",
            "Illinois": "IL",
            "Indiana": "IN",
            "Iowa": "IA",
            "Kansas": "KS",
            "Kentucky": "KY",
            "Louisiana": "LA",
            "Maine": "ME",
            "Maryland": "MD",
            "Massachusetts": "MA",
            "Michigan": "MI",
            "Minnesota": "MN",
            "Mississippi": "MS",
            "Missouri": "MO",
            "Montana": "MT",
            "Nebraska": "NE",
            "Nevada": "NV",
            "New Hampshire": "NH",
            "New Jersey": "NJ",
            "New Mexico": "NM",
            "New York": "NY",
            "North Carolina": "NC",
            "North Dakota": "ND",
            "Ohio": "OH",
            "Oklahoma": "OK",
            "Oregon": "OR",
            "Pennsylvania": "PA",
            "Rhode Island": "RI",
            "South Carolina": "SC",
            "South Dakota": "SD",
            "Tennessee": "TN",
            "Texas": "TX",
            "Utah": "UT",
            "Vermont": "VT",
            "Virginia": "VA",
            "Washington": "WA",
            "West Virginia": "WV",
            "Wisconsin": "WI",
            "Wyoming": "WY",
            "District of Columbia": "DC",
            "American Samoa": "AS",
            "Guam": "GU",
            "Northern Mariana Islands": "MP",
            "Puerto Rico": "PR",
            "United States Minor Outlying Islands": "UM",
            "U.S. Virgin Islands": "VI",
        }

        if len(s) <= 2:
            return s.upper()

        for k,v in us_state_to_abbrev.items():
            if s.lower() == k.lower():
                return v
        else:
            for k,v in us_state_to_abbrev.items():
                if s.lower() in k.lower():
                    return v
            else:
                for k,v in us_state_to_abbrev.items():
                    if Utils.alphanum(s,"lower") in Utils.alphanum(k,"lower"):
                        return v
                else:
                    return s



    def valid_memo_category(text):
        forbidden_memocategory_names = [
            "to",
            "last",
            "category",
            "all"
            ]

        forbidden_chars = [
            "`",
            "´",
            '"',
            "‘",
            "’",
            "“",
            "”",
            ";"
            ]

        try:
            x = int(text)
            return False
        except:
            pass

        for c in forbidden_chars:
            if c in text:
                return False

        if Utils.cleantext2(text) in forbidden_memocategory_names:
            return False

        return True



    def year9999():
        """UNIX timestamp for year 9999, December 31st"""
        return 253402210800



    def years_to_seconds(amount_of_years, month_of_year, day_of_year, from_timestamp):
        if from_timestamp is not None and Utils.represents_float(from_timestamp):
            ts = int(from_timestamp)
            year = datetime.utcfromtimestamp(ts).year
            month = datetime.utcfromtimestamp(ts).month
            day = datetime.utcfromtimestamp(ts).day
        else:
            year = datetime.utcnow().year
            month = datetime.utcnow().month
            day = datetime.utcnow().day
        today = date(year, month, day)

        if (day_of_year is None or day_of_year == ""):
            if (month_of_year is None or month_of_year == ""):
                future = date(year+int(amount_of_years), month, day)
            else:
                future = date(year+int(amount_of_years), int(month_of_year), 1)
        else:
            future = date(year+int(amount_of_years), int(month_of_year), int(day_of_year))

        diff = (future - today).days
        seconds = diff * 24*60*60
        return seconds

















































    ############################################### BOT SPECIFIC FUNCTIONS (sorted alphabetically)



    async def are_you_sure_embed(ctx, bot, header, text, color):
        # seeks confirmation via react buttons
        # returns True, False or Timed_Out

        # FIRST CREATE EMBED

        embed=discord.Embed(title=header, description=text, color=color)
        embed.set_footer(text=f"status: pending")
        message = await ctx.send(embed=embed)

        await message.add_reaction("✅")
        await message.add_reaction("⛔")

        def check(reaction, user):
            return message.id == reaction.message.id and user == ctx.author and str(reaction.emoji) in ["✅","⛔"]
            # This makes sure nobody except the command sender can interact with the "menu"

        try:
            mdmbot_id = int(bot.application_id)
            mdmbot = ctx.guild.get_member(mdmbot_id)
        except:
            print("could not find mdm bot member object")

        # WAIT FOR RESPONSE

        async with ctx.typing():
            try:
                reaction, user = await bot.wait_for("reaction_add", timeout=60, check=check)
                # waiting for a reaction to be added - times out after x seconds, 60 in this example

                if str(reaction.emoji) == "✅":
                    new_embed=discord.Embed(title=header, description=text, color=color)
                    new_embed.set_footer(text=f"status: approved")
                    await message.edit(embed=new_embed)
                    #await message.remove_reaction("✅", mdmbot)
                    #await message.remove_reaction("⛔", mdmbot)
                    return "True"

                elif str(reaction.emoji) == "⛔":
                    new_embed=discord.Embed(title=header, description=text, color=color)
                    new_embed.set_footer(text=f"status: denied")
                    await message.edit(embed=new_embed)
                    #await message.remove_reaction("✅", mdmbot)
                    #await message.remove_reaction("⛔", mdmbot)
                    return "False"

                else:
                    new_embed=discord.Embed(title=header, description=text, color=color)
                    new_embed.set_footer(text=f"error: cancelled action")
                    await message.edit(embed=new_embed)
                    return "Error"

            except asyncio.TimeoutError:
                new_embed=discord.Embed(title=header, description=text, color=color)
                new_embed.set_footer(text=f"status: timeouted (auto-denied)")
                await message.edit(embed=new_embed)
                #await message.remove_reaction("✅", mdmbot)
                #await message.remove_reaction("⛔", mdmbot)
                print("timeout")
                return "Timed_Out" 



    async def are_you_sure_msg(ctx, bot, text):
        def check(m): # checking if it's the same user and channel
            return ((m.author == ctx.author) and (m.channel == ctx.channel))

        await ctx.send(f"{text}\nRespond with `yes` to confirm.")

        try: # waiting for message
            async with ctx.typing():
                response = await bot.wait_for('message', check=check, timeout=30.0) # timeout - how long bot waits for message (in seconds)
        except asyncio.TimeoutError: # returning after timeout
            await ctx.send("action timed out")
            return False

        if response.content.lower() in ["yes", "y", "-y", "-yes"]:
            return True
        else:
            await ctx.send("cancelled action")
            return False



    async def backlog_roll(ctx, user, cat_type, cat_list):
        con = sqlite3.connect('databases/memobacklog.db')
        cur = con.cursor()
        user_bl_list = [[item[0], item[1], item[2], item[3], item[4]] for item in cur.execute("SELECT bgid, userid, username, backlog, details FROM memobacklog WHERE userid = ? ORDER BY bgid", (str(user.id),)).fetchall()]
        
        if cat_type == "all":
            filtered_list = user_bl_list

        elif cat_type == "blc":
            filtered_list = []
            for item in user_bl_list:
                cat = item[4].lower()
                if cat == "":
                    cat = "default"
                if cat in cat_list:
                    filtered_list.append(item)

        elif cat_type == "blx":
            filtered_list = []
            for item in user_bl_list:
                cat = item[4].lower()
                if cat == "":
                    cat = "default"
                if cat not in cat_list:
                    filtered_list.append(item)
        else:
            await ctx.send("Error: unknown type.")
            return

        n = len(filtered_list)
        if n == 0:
            emoji = Utils.emoji("disappointed")
            await ctx.send(f"Nothing to roll from... {emoji}")
            return

        r = random.randint(1, n)
        rand_item = filtered_list[r-1]
        rand_bl_entry = rand_item[3]
        cat = rand_item[4]
        if cat.strip() == "":
            cat = "default"

        if rand_item in user_bl_list:
            index = str(user_bl_list.index(rand_item) + 1)
        else:
            index = 'ERROR'
        await ctx.send(f'🎲 D{n}-bl roll says:\n`{rand_bl_entry[:300]}`\n(index: {index}) | [cat: {cat}]')



    async def bot_spam_send(bot, title, text): 
        try:
            con = sqlite3.connect(f'databases/botsettings.db')
            cur = con.cursor()
            botspamchannel_id = int([item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("botspam channel id",)).fetchall()][0])
        except:
            print("Bot spam/notification channel ID in database is faulty.")
            try:
                botspamchannel_id = int(os.getenv("bot_channel_id"))
                if botspamchannel_id is None:
                    raise ValueError("No botspamchannel id provided in .env file")
            except Exception as e:
                print(f"Error in utils.bot_spam_send() ({title}):", e)
                return
        try:
            botspamchannel = bot.get_channel(botspamchannel_id) 
        except Exception as e:
            botspamchannel = discord.utils.get(bot.guild.channels, id=botspamchannel_id) # in case self.bot couldn't be provided and instead ctx was passed
        embed=discord.Embed(title=title, description=text, color=0x000000)
        await botspamchannel.send(embed=embed)



    async def changetimeupdate():
        utc_timestamp = int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds())
        try:
            human_readable_time = str(datetime.utcfromtimestamp(utc_timestamp).strftime('%Y-%m-%d %H:%M:%S UTC'))
        except:
            human_readable_time = "error"

        conL = sqlite3.connect(f'databases/aftermostchange.db')
        curL = conL.cursor()
        curL.execute('''CREATE TABLE IF NOT EXISTS lastchange (name text, value text, details text)''')
        curL.execute("UPDATE lastchange SET value = ?, details = ? WHERE name = ?", (utc_timestamp, human_readable_time, "time"))
        conL.commit()
        conL.close()



    async def cooldown(ctx, service):
        """waiting function: returns nothing, only raises error or waits time"""

        conC = sqlite3.connect('databases/cooldowns.db')
        curC = conC.cursor()

        # SPAM PREVENTION

        invoketime = int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds())
        curC.execute("DELETE FROM userrequests WHERE cast(time_stamp as integer) < ?", (invoketime - 3600,))
        conC.commit()

        if ctx != None:
            userrequest_list = [item[0] for item in curC.execute("SELECT time_stamp FROM userrequests WHERE LOWER(service) = ? AND userid = ?", (service.lower(), str(ctx.message.author.id))).fetchall()]
            temp_ban = [item[0] for item in curC.execute("SELECT time_stamp FROM userrequests WHERE LOWER(service) = ? AND userid = ?", ("ban", str(ctx.message.author.id))).fetchall()]

            if len(userrequest_list) > 5 or len(temp_ban) > 0:
                curC.execute("INSERT INTO userrequests VALUES (?, ?, ?, ?)", ("ban", str(ctx.message.author.id), str(ctx.message.author.name), str(invoketime)))
                conC.commit()
                print("request abuse: 1 hour temporary ban from web requests")
                raise ValueError(f"request abuse")
                return

            curC.execute("INSERT INTO userrequests VALUES (?, ?, ?, ?)", (service, str(ctx.message.author.id), str(ctx.message.author.name), str(invoketime)))
            conC.commit()

        # INITIALISE SERVICE PARAMETERS

        while True:

            cooldown_list = [[item[0],item[1],item[2],item[3],item[4]] for item in curC.execute("SELECT last_used, limit_seconds, limit_type, long_limit_seconds, long_limit_amount FROM cooldowns WHERE LOWER(service) = ?", (service.lower(),)).fetchall()]

            # default parameters
            limit_seconds = 1
            limit_type = "soft"
            long_limit_seconds = 20
            long_limit_amount = 10
            if len(cooldown_list) == 0:
                last_used = [0]
                print(f"Warning: service has no cooldown entry in database. creating default entry.")
                curC.execute("INSERT INTO cooldowns VALUES (?, ?, ?, ?, ?, ?)", (service, "0", "1", "soft", "20", "10"))
                conC.commit()
                await Utils.changetimeupdate()
            else:

                # database parameters
                cooldown = cooldown_list[0]
                if len(cooldown_list) > 1:
                    print(f"Warning: {service} has multiple entries in cooldown database")
                try:
                    last_used_stringlist = cooldown[0].split(",")
                    last_used = []
                    for lu_string in last_used_stringlist:
                        last_used.append(int(lu_string.strip()))
                except:
                    print(f"Error with 'LAST USED' cooldown entry of {service}: {e}")
                    last_used = [0]
                try:
                    limit_seconds = int(cooldown[1].strip())
                    limit_type = cooldown[2].lower().strip()
                    long_limit_seconds = int(cooldown[3].strip())
                    long_limit_amount = int(cooldown[4].strip())
                except Exception as e:
                    print(f"Error with cooldown entries of {service}: {e}")

            # COMPPARE TIME NOW WITH SAVED TIMES

            now = int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds())

            short_counter = 0
            long_counter = 0
            relevant_last_used = []
            for lu_time in last_used:
                counter_moved = False
                if lu_time + long_limit_seconds > now:
                    long_counter += 1
                    counter_moved = True
                if lu_time + limit_seconds > now:
                    short_counter += 1
                    counter_moved = True
                if counter_moved:
                    relevant_last_used.append(lu_time)

            # TAKE ACTION

            if limit_type == "hard":

                # hard type cooldown: break

                if long_counter >= long_limit_amount or short_counter > 0:
                    if ctx != None:
                        curC.execute("DELETE FROM userrequests WHERE LOWER(service) = ? AND userid = ? AND time_stamp = ?", (service.lower(), str(ctx.message.author.id), str(invoketime)))
                        conC.commit()
                    raise ValueError(f"rate limited")
                    return

                # all good
                break

            else:
                # soft type cooldown: delay

                if long_counter >= long_limit_amount or short_counter > 0:
                    if ctx != None:
                        async with ctx.typing():
                            await asyncio.sleep(1)
                    else:
                        await asyncio.sleep(1)

                else:
                    # all good
                    break

            print(f"{service} cooldown")

        relevant_last_used_str = []
        for item in relevant_last_used:
            relevant_last_used_str.append(str(item))
        new_last_used = ','.join(relevant_last_used_str + [str(now)])
        curC.execute("UPDATE cooldowns SET last_used = ? WHERE LOWER(service) = ?", (new_last_used, service))
        if ctx != None:
            curC.execute("DELETE FROM userrequests WHERE cast(time_stamp as integer) < ?", (invoketime - 3600,))
            curC.execute("DELETE FROM userrequests WHERE LOWER(service) = ? AND userid = ? AND time_stamp = ?", (service.lower(), str(ctx.message.author.id), str(invoketime)))
        conC.commit()
        conC.close()
        await Utils.changetimeupdate()



    async def cooldown_exception(ctx, exception, service):
        print(exception)
        if ctx != None:
            if str(exception) == "rate limited":
                emoji = Utils.emoji("shy")
                await ctx.send(f"We are being rate limited ({service}). {emoji}")
            elif str(exception) == "request abuse":
                emoji = Utils.emoji("ban")
                try:
                    await ctx.message.reply(f"Request abuse: You are temporarily banned from using 3rd party requests. {emoji}")
                except:
                    await ctx.send(f"Request abuse: You are temporarily banned from using 3rd party requests. {emoji}")
            else:
                print(traceback.format_exc())
                emoji = Utils.emoji("panic")
                await ctx.send(f"Error with 3rd party service request: unforeseen exception. {emoji}")



    async def customtextparse(text_preparse, userid):
        """
        write \\n for linebreaks
        @user to insert a mention of provided user via id
        emoji:name to insert emoji from database
        """
        text_linebreaks = text_preparse.replace("\\n","\n")
        text_commaformatting = ""
        for i in range(len(text_linebreaks)): # adds spaces if alphanumeric character follows immediately after a comma or semicolon
            char = text_linebreaks[i]
            if (i < len(text_linebreaks) - 1) and (char in [",", ";"]) and text_linebreaks[i+1].isalnum():
                text_commaformatting += char + " "
            else:
                text_commaformatting += char
        text_prelist = text_commaformatting.split(" ")
        text_list = []
        for phrase in text_prelist:
            words = phrase.split("\n")
            new_phrase_list = []
            for word in words:
                if "@user" in word:
                    new_word = ''.join([x for x in word.replace("@user", f"<@{userid}>") if not x.isalpha()])
                elif word.startswith("emoji:") and len(word) > 6:
                    emoji = word.split(":")[1]
                    new_word = Utils.emoji(emoji)
                else:
                    new_word = word
                new_phrase_list.append(new_word)
            new_phrase = '\n'.join(new_phrase_list)
            text_list.append(new_phrase)
        text = ' '.join(text_list)

        return text



    async def database_connect_with_retries(name, waiting_time = 10):
        try:
            con = sqlite3.connect(f'databases/{name}.db')
            cur = con.cursor()
        except Exception as e1:
            try:
                print(f"Connecting to {name}.db failed. {e1} \nRetrying 2nd time in 10 seconds...")
                await asyncio.sleep(waiting_time)
                con = sqlite3.connect(f'databases/{name}.db')
                cur = con.cursor()
            except Exception as e2:
                try:
                    print(f"Connecting to {name}.db failed again. {e1} \nRetrying 3rd time in 10 seconds...")
                    await asyncio.sleep(waiting_time)
                    con = sqlite3.connect(f'databases/{name}.db')
                    cur = con.cursor()
                except Exception as e3:    
                    print(f"Connecting to {name}.db failed yet again. >_<")
                    error_string = f"Error: ```{e3}```"
                    error_string += f"\nError Traceback: ``` " + f"{traceback.format_exc()}"[:3600] + f"```"
                    try:
                        botspamchannel_id = int(os.getenv("bot_channel_id"))
                        botspamchannel = self.bot.get_channel(botspamchannel_id)             
                        title = "⚠️ Error"
                        embed=discord.Embed(title=title, description=error_string[:4096], color=0x000000)
                        await botspamchannel.send(embed=embed)
                    except:
                        print("ERROR:", error_string)
                    return None, None
        return con, cur



    async def embed_pages(ctx, bot, header, description_list, color, footer, reply=False, show_author=False):
        """show_author can be a bool or a tuple of user_id and author text"""
        pages = len(description_list)
        if pages == 0:
            await ctx.send("Error: empty pages")
            return

        if len(header) > 256:
            header = header[:253] + "..."

        if footer is None or footer == "":
            smalltext = ""
        else:
            smalltext = f" - {footer[:1000]}"

        cur_page = 1
        embed=discord.Embed(title=header, description=(f"{description_list[cur_page-1][:4096]}"), color=color)
        if show_author == True:
            try:
                embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar)
            except Exception as e:
                print("Utils.embed_pages raised error:", e)
        elif show_author == False:
            pass
        elif len(show_author) == 2:
            try:
                user_id = int(show_author[0])
                text = show_author[1]
                member = ctx.guild.get_member(bot.application_id)
                embed.set_author(name=text, icon_url=member.avatar)
            except Exception as e:
                print("Utils.embed_pages raised error:", e)

        embed.set_footer(text=f"Page {cur_page}/{pages}{smalltext}")

        if reply:
            message = await ctx.reply(embed=embed, mention_author=False)
        else:
            message = await ctx.send(embed=embed)

        if pages > 1:
            if pages > 2:
                await message.add_reaction("⏮️")

            await message.add_reaction("◀️")
            await message.add_reaction("▶️")

            if pages > 2:
                await message.add_reaction("⏭️")

            def check(reaction, user):
                return message.id == reaction.message.id and user == ctx.author and str(reaction.emoji) in ["◀️", "▶️", "⏮️", "⏭️"]
                # This makes sure nobody except the command sender can interact with the "menu"

            while True:
                try:
                    reaction, user = await bot.wait_for("reaction_add", timeout=60, check=check)
                    # waiting for a reaction to be added - times out after x seconds, 60 in this example

                    if str(reaction.emoji) == "▶️" and cur_page != pages:
                        cur_page += 1
                        new_embed=discord.Embed(title=header, description=(f"{description_list[cur_page-1][:4096]}"), color=color)
                        new_embed.set_footer(text=f"Page {cur_page}/{pages}{smalltext}")
                        await message.edit(embed=new_embed)
                        try:
                            await message.remove_reaction(reaction, user)
                        except:
                            print("could not remove reaction")

                    elif str(reaction.emoji) == "◀️" and cur_page > 1:
                        cur_page -= 1
                        new_embed=discord.Embed(title=header, description=(f"{description_list[cur_page-1][:4096]}"), color=color)
                        new_embed.set_footer(text=f"Page {cur_page}/{pages}{smalltext}")
                        await message.edit(embed=new_embed)
                        try:
                            await message.remove_reaction(reaction, user)
                        except:
                            print("could not remove reaction")

                    elif str(reaction.emoji) == "⏮️" and cur_page > 1:
                        cur_page = 1 #back to first page
                        new_embed=discord.Embed(title=header, description=(f"{description_list[cur_page-1][:4096]}"), color=color)
                        new_embed.set_footer(text=f"Page {cur_page}/{pages}{smalltext}")
                        await message.edit(embed=new_embed)
                        try:
                            await message.remove_reaction(reaction, user)
                        except:
                            print("could not remove reaction")

                    elif str(reaction.emoji) == "⏭️" and cur_page != pages:
                        cur_page = pages #to last page
                        new_embed=discord.Embed(title=header, description=(f"{description_list[cur_page-1][:4096]}"), color=color)
                        new_embed.set_footer(text=f"Page {cur_page}/{pages}{smalltext}")
                        await message.edit(embed=new_embed)
                        try:
                            await message.remove_reaction(reaction, user)
                        except:
                            print("could not remove reaction")
                            
                    else:
                        try:
                            await message.remove_reaction(reaction, user)
                        except:
                            print("could not remove reaction")
                        # removes reactions if the user tries to go forward on the last page or
                        # backwards on the first page
                except asyncio.TimeoutError:
                    new_embed=discord.Embed(title=header, description=(f"{description_list[cur_page-1][:4096]}"), color=color)
                    new_embed.set_footer(text=f"Page {cur_page}/{pages}{smalltext}")
                    await message.edit(embed=new_embed)

                    print("▶️ remove bot reactions ◀️")
                    guild = ctx.guild
                    mdmbot = ctx.guild.get_member(bot.application_id)
                    await message.remove_reaction("⏭️", mdmbot)
                    await message.remove_reaction("▶️", mdmbot)
                    await message.remove_reaction("◀️", mdmbot)
                    await message.remove_reaction("⏮️", mdmbot)
                    break
                    # ending 



    async def fetch_id_from_args(object_type, searchscope, word_list):
        # object_type needs to be user, channel or role
        # searchscope needs to be either "first", "all" or "multiple"
        # determines whether the user argument is looked for in first word only or all words
        idprefix_dict = {
            "user": "@",
            "channel": "#",
            "role": "@&"
        }
        idprefix = idprefix_dict[object_type]

        if searchscope == "first": # check only first argument for id
            if len(word_list) == 0:
                return "None", ""
            else:
                object_arg = word_list[0]
                if len(word_list) >= 2:
                    rest = ' '.join(word_list[1:])
                else:
                    rest = ""

                object_id = object_arg
                if len(object_arg) > 3 and object_arg.startswith(f"<{idprefix}") and object_arg[-1] == ">":
                    object_id = object_arg.replace(f"<{idprefix}", "").replace(">","")

                if len(object_id) < 7:
                    raise ValueError(f"provided {object_type} id not a valid snowflake ❄️")
                    return

                try:
                    id_test = int(object_id)
                except:
                    raise ValueError(f"provided {object_type} id not an integer or valid {object_type} mention")
                    return 

                # both returned variables are strings
                return object_id, rest

        elif searchscope == "all": # check all arguments for one id
            if len(word_list) == 0:
                return "None", ""
            else:
                found_object = False
                rest_list = []
                for object_arg in word_list:
                    if found_object == False:
                        object_id = object_arg
                        if len(object_arg) > 3 and object_arg.startswith(f"<{idprefix}") and object_arg[-1] == ">":
                            object_id = object_arg.replace(f"<{idprefix}", "").replace(">","")

                        try:
                            id_test = int(object_id)
                            is_integer = True 
                        except:
                            is_integer = False

                        if is_integer and int(object_id) >= 4194304:
                            found_object = True
                        else:
                            rest_list.append(object_arg)
                    else:
                        rest_list.append(object_arg)
                
                if not found_object:
                    raise ValueError(f"No valid {object_type} id or {object_type} mention found.")
                    return 

                if len(rest_list) == 0:
                    rest = ""
                else:
                    rest = ' '.join(rest_list)

                return object_id, rest


        elif searchscope == "multiple": # check all arguments for multiple ids

            if len(word_list) == 0:
                return "None", ""
            else:
                object_list = []
                rest_list = []
                for object_arg in word_list:
                    object_id = object_arg
                    if len(object_arg) > 3 and object_arg.startswith(f"<{idprefix}") and object_arg[-1] == ">":
                        object_id = object_arg.replace(f"<{idprefix}", "").replace(">","")

                    try:
                        id_test = int(object_id)
                        is_integer = True 
                    except:
                        is_integer = False

                    if is_integer and int(object_id) > 4194303:
                        object_list.append(object_id)
                    else:
                        rest_list.append(object_arg)

                if len(object_list) == 0:
                    raise ValueError(f"No valid {object_type} id or {object_type} mention found.")
                    return 

                object_ids = ';'.join(object_list)
                if len(rest_list) == 0:
                    rest = ""
                else:
                    rest = ' '.join(rest_list)

                return object_ids, rest
        else:
            raise ValueError(f"Error in utils.fetch_id_from_args: search scope not found")
            return 



    async def fetch_member_and_color(ctx, args):
        other_user_mentioned = False
        rest_list = []
        for arg in args:
            arg_clean = Utils.cleantext(arg)
            if arg_clean.startswith("<@") and arg_clean.endswith(">"):
                member_id_str = arg_clean.replace("<@","").replace(">","")
                try:
                    member_id_int = int(member_id_str)
                    if other_user_mentioned == False:
                        member = ctx.guild.get_member(member_id_int)
                        try:
                            color = member.color
                        except:
                            color = 0xffffff
                        other_user_mentioned = True
                    else:
                        user = ctx.guild.get_member(member_id_int)
                        rest_list.append(user.name)
                except Exception as e:
                    #print("Error while trying to fetch_member_and_color():", e)
                    pass
            elif len(arg_clean) >= 17 and Utils.represents_integer(arg_clean):
                try:
                    member_id_int = int(arg_clean)
                    if other_user_mentioned == False:
                        member = ctx.guild.get_member(member_id_int)
                        try:
                            color = member.color
                        except:
                            color = 0xffffff
                        other_user_mentioned = True
                    else:
                        user = ctx.guild.get_member(member_id_int)
                        rest_list.append(user.name)
                except:
                    rest_list.append(arg_clean)
            else:
                rest_list.append(arg_clean)

        if not other_user_mentioned:
            member = ctx.message.author
            try:
                color = member.color
            except:
                color = 0xffffff

        return member, color, rest_list



    async def fetch_member_tryloop(ctx, args):
        # SEARCH USER VIA ID
        try:
            user_id, rest = await Utils.fetch_id_from_args("user", "first", args)
            for member in ctx.guild.members:
                if str(member.id) == user_id:
                    return member
        except:
            pass # fetching probably 

        # SEARCH USER VIA EXACT NAME
        user_name = '_'.join(args).lower()
        for member in ctx.guild.members:
            if str(member.name).lower() == user_name:
                return member

        # SEARCH USER VIA EXACT NICK
        user_nick = ' '.join(args).lower()
        for member in ctx.guild.members:
            if str(member.display_name).lower() == user_nick:
                return member

        # SEARCH USER VIA COMPACT NAME
        user_name_compact = Utils.alphanum(' '.join(args).lower())
        if len(user_name_compact) > 0:
            for member in ctx.guild.members:
                if Utils.alphanum(str(member.name).lower()) == user_name_compact:
                    return member

        # SEARCH USER VIA COMPACT NICK
        user_nick_compact = Utils.alphanum(' '.join(args).lower())
        if len(user_nick_compact) > 0:
            for member in ctx.guild.members:
                if Utils.alphanum(str(member.display_name).lower()) == user_nick_compact:
                    return member
        
        return None



    async def fetch_role_by_name(ctx, word_string):
        # input string of role name
        # output role object
        rolename_full = word_string.lower()
        rolename_compact = ''.join(x for x in rolename_full if x.isalpha() or x.isnumeric())

        for role in ctx.guild.roles:
            r_full = str(role.name).lower()

            if r_full == rolename_full:
                the_role = role 
                break
        else:
            for role in ctx.guild.roles:
                r_full = str(role.name).lower()
                r_compact = ''.join(x for x in r_full if x.isalpha() or x.isnumeric())

                if r_compact == rolename_compact:
                    the_role = role 
                    break
            else:
                raise ValueError(f"Could not find role {word_string}.")
                return 

        return the_role



    async def fetch_update_lastfm_artistalbuminfo(ctx, artist, album):
        cooldown = False # is ok?
        payload = {
            'method': 'album.getInfo',
            'album': album,
            'artist': artist,
        }
        response = await Utils.lastfm_get(ctx, payload, cooldown)
        if response == "rate limit":
            raise ValueError("rate limit")
        try:
            rjson = response.json()
            artist_name = rjson['album']['artist']
            album_name = rjson['album']['name']

            try:
                thumbnail = rjson['album']['image'][-1]['#text']
            except:
                thumbnail = ""

            tags = []
            try:
                for tag in rjson['album']['tags']['tag']:
                    try:
                        tagname = tag['name'].lower()
                        tags.append(tagname)
                    except Exception as e:
                        print("Tag error:", e)
            except:
                pass

        except:
            raise ValueError("Could not find `artist - album`.")

        await Utils.update_lastfm_artistalbuminfo(artist_name, album_name, thumbnail, tags)

        return thumbnail, tags



    async def get_all_integers(args):
        indices = []
        for arg in args:
            try:
                x = int(arg)
                indices.append(x)
            except:
                pass

        return indices



    async def get_artist_name_and_image(artistinput, ctx = None, albuminput = ""):
        now = int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds())
        try:
            if artistinput.strip() == "":
                try:
                    artist, album, song, thumbnail, cover, tags = await Utils.get_last_track(ctx)
                    if thumbnail.strip() == "" or thumbnail.strip().endswith("/2a96cbd8b46e442fc41c2b86b821562f.png"):
                        thumbnail, update_time = await Utils.get_database_artistimage(artist)
                        if thumbnail == "" or update_time < now - 30*24*60*60:
                            lfm_name, status = Utils.get_lfmname(ctx.author.id)
                            thumbnail = await Utils.get_spotify_artistimage(artist, lfm_name, "", albuminput)
                    return artist, thumbnail
                except Exception as e:
                    return artistinput, ""

            conSM = sqlite3.connect('databases/scrobblemeta.db')
            curSM = conSM.cursor()
            artist_fltr = Utils.compactnamefilter(artistinput,"artist","alias")

            try:
                result = curSM.execute(f"SELECT artist, thumbnail, spotify_update, lfm_update FROM artistinfo WHERE filtername = ?", (artist_fltr,))
                rtuple = result.fetchone()

                artist = str(rtuple[0])
                thumbnail = str(rtuple[1])
                spotify_update = int(rtuple[2])
                lfm_update = int(rtuple[3])
                db_entry_exists = True
            except:
                artist = artistinput
                thumbnail = ""
                db_entry_exists = False

            if not db_entry_exists: #or lfm_update < now - 180*24*60*60:
                try:
                    cooldown = True
                    payload = {'method': 'artist.getInfo'}
                    payload['artist'] = artist

                    response = await Utils.lastfm_get(ctx, payload, cooldown)
                    if response == "rate limit":
                        print("Error: Rate limit.")
                        return artist, thumbnail
                    rjson = response.json()
                    artist = rjson['artist']['name']
                except:
                    artist = artistinput

            if thumbnail.strip() == "" or thumbnail.strip().endswith("/2a96cbd8b46e442fc41c2b86b821562f.png") or spotify_update < now - 180*24*60*60:
                try:
                    if ctx is None:
                        user_id = 0
                    else:
                        user_id = ctx.author.id

                    lfm_name, status = Utils.get_lfmname(user_id)
                    thumbnail = await Utils.get_spotify_artistimage(artist, lfm_name, "", albuminput)
                    print("thumbail")
                except Exception as e:
                    print(e)

            return artist, thumbnail

        except Exception as e:
            print("Error:", e)
            return artistinput, ""


    async def get_defaultperms(ctx):
        # GET PERMS OF REFERENCE ROLE
        reference_role = await Utils.get_reference_role(ctx)
        perm_list = [perm[0] for perm in reference_role.permissions if perm[1]]

        # GET PERMS OF EVERYONE ROLE
        everyone_perm_list = await Utils.get_everyone_perms(ctx)

        # RETURN CONCATINATION
        for perm in everyone_perm_list:
            if perm not in perm_list:
                perm_list.append(perm)
        return perm_list



    async def get_everyone_perms(ctx):
        con = sqlite3.connect(f'databases/botsettings.db')
        cur = con.cursor()
        everyone_role_id = int([item[0] for item in cur.execute("SELECT value FROM botsettings WHERE name = ?", ("main server id",)).fetchall()][0])
        everyone_role = discord.utils.get(ctx.guild.roles, id = everyone_role_id)
        perm_list = [perm[0] for perm in everyone_role.permissions if perm[1]]
        return perm_list



    async def get_last_track(ctx): # doubling of the same function in scrobble_utility.py
        member = ctx.author
        con = sqlite3.connect('databases/npsettings.db')
        cur = con.cursor()
        lfm_list = [item[0] for item in cur.execute("SELECT lfm_name FROM lastfm WHERE id = ?", (str(member.id),)).fetchall()]

        if len(lfm_list) == 0:
            raise ValueError("no lfm name set")

        lfm_name = lfm_list[0]
        cooldown = True
        payload = {
            'method': 'user.getRecentTracks',
            'user': lfm_name,
            'limit': "1",
        }
        response = await Utils.lastfm_get(ctx, payload, cooldown)
        if response == "rate limit":
            raise ValueError("rate limit")

        try:
            rjson = response.json()
            tjson = rjson['recenttracks']['track'][0] # track json

            # PARSE LAST TRACK INFO

            song = tjson['name']
            #song_link = tjson['url']
            artist = tjson['artist']['#text']
            try:
                album = tjson['album']['#text']
            except:
                album = ""
            try:
                album_cover = tjson['image'][-1]['#text']
            except:
                album_cover = ""
            try:
                mbid = tjson['artist']['mbid']
            except:
                mbid = ""

            # FETCH ARTIST INFO
            try:
                cooldown = False
                payload = {
                    'method': 'artist.getInfo',
                }
                if mbid.strip() == "":
                    payload['mbid'] = mbid
                else:
                    payload['artist'] = artist
                response = await Utils.lastfm_get(ctx, payload, cooldown)

                if response == "rate limit":
                    raise ValueError("rate limit")

                rjson = response.json()

                try:
                    artist_thumbnail = rjson['artist']['image'][0]['#text']
                except:
                    artist_thumbnail = ""

                tags = []
                try:
                    for tag in rjson['artist']['tags']['tag']:
                        try:
                            tagname = tag['name'].lower()
                            tags.append(tagname)
                        except Exception as e:
                            print("Tag error:", e)
                except:
                    pass
            except Exception as e:
                print("Error while fetching artist info:", e)
                return artist, album, song, "", "", []

            # UPDATE DATABASES
            if len(tags) > 0:
                Utils.update_artistinfo(artist, artist_thumbnail, tags)

            try:
                if album.strip() != "" and album_cover.strip() != "":
                    await Utils.update_lastfm_artistalbuminfo(artist, album, album_cover, tags)
            except Exception as e:
                print("Error while trying to update albuminfo database:", e)

            return artist, album, song, artist_thumbnail, album_cover, tags

        except Exception as e:
            if "503 service unavailable" in str(rjson).lower():
                # under construction: fetch artist album song from discord rich presence instead
                raise ValueError(f"Last FM is not responding. Try in a few seconds again or try command with explicit arguments instead.")

            raise ValueError(f"{str(rjson)} - {e}")



    async def get_libretranslate_mirrors():
        try:
            session = requests.session()
            burp0_url = "https://github.com:443/LibreTranslate/LibreTranslate?tab=readme-ov-file"
            burp0_headers = {"Sec-Ch-Ua": "\"Not-A.Brand\";v=\"99\", \"Chromium\";v=\"124\"", "Sec-Ch-Ua-Mobile": "?0", "Sec-Ch-Ua-Platform": "\"Windows\"", "Upgrade-Insecure-Requests": "1", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.118 Safari/537.36", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7", "Sec-Fetch-Site": "none", "Sec-Fetch-Mode": "navigate", "Sec-Fetch-User": "?1", "Sec-Fetch-Dest": "document", "Accept-Encoding": "gzip, deflate, br", "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7", "Priority": "u=0, i", "Connection": "close"}
            response = session.get(burp0_url, headers=burp0_headers)

            soup = BeautifulSoup(response.text.split("href=\"#mirrors\"")[1].split("Mirrors")[0], "html.parser")

            url_list = []

            for a in soup.find_all('a', href=True):
                link = str(a['href']).strip()

                if link not in ["https://libretranslate.com", "https://portal.libretranslate.com", "https://status.libretranslate.com/"]:
                    if "@" not in link:
                        url_list.append(link.replace("https://", ""))

            if len(url_list) == 0:
                raise ValueError("Could not find URLs in the webscraped mirror section. Either there are no working mirrors listed at the moment, or the webpage changed in which case this is a case for the devs to fix.")
        except Exception as e:
            print("Error while trying to fetch libre-translate mirrors:", e)
            url_list = ["translate.terraprint.co", "trans.zillyhuhn.com", "translate.lotigara.ru"]

        return url_list



    async def get_reference_role(ctx):
        """baseline role for permissions"""
        if Utils.is_main_server_returnbool(ctx):
            try:
                reference_role = await Utils.get_reference_role_mainserver(ctx)
                return reference_role
            except:
                pass
            
        everyone_role_id = ctx.guild.id
        everyone_role = discord.utils.get(ctx.guild.roles, id = everyone_role_id)
        return everyone_role



    async def get_reference_role_mainserver(ctx):
        """baseline role for permissions: either @everyone, autorole or verified role
        """
        con = sqlite3.connect(f'databases/botsettings.db')
        cur = con.cursor()

        # CHECK ACCESS WALL SETTING

        accesswall_list = [item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("access wall",)).fetchall()]
        if len(accesswall_list) == 0:
            accesswall = "error⚠️"
            print("Error: no accesswall on/off in database")
            #raise ValueError(f'Error: No accesswall setting found.')
            #return False
        else:
            if len(accesswall_list) > 1:
                print("Warning: there are multiple accesswall on/off entries in the database")
            accesswall = accesswall_list[0]

        # FETCH REFERENCE ROLE FOR COMMON USERS

        if accesswall == "on":
            try:
                verified_role_id = int([item[0] for item in cur.execute("SELECT role_id FROM specialroles WHERE name = ?", ("verified role",)).fetchall()][0])
                reference_role = discord.utils.get(ctx.guild.roles, id = verified_role_id)
                found_role = True
            except:
                found_role = False
        elif accesswall == "off":
            try:
                community_role_id = int([item[0] for item in cur.execute("SELECT role_id FROM specialroles WHERE name = ?", ("community role",)).fetchall()][0])
                reference_role = discord.utils.get(ctx.guild.roles, id = community_role_id)
                found_role = True
            except:
                found_role = False
        else:
            # i.e. accesswall == "error⚠️"
            found_role = False

        if not found_role:
            try:
                everyone_role_id = int([item[0] for item in cur.execute("SELECT value FROM botsettings WHERE name = ?", ("main server id",)).fetchall()][0])
                reference_role = discord.utils.get(ctx.guild.roles, id = everyone_role_id)
            except Exception as e:
                print("Error:", e)
                try:
                    everyone_role_id = int(os.getenv(guild_id))
                    reference_role = discord.utils.get(ctx.guild.roles, id = everyone_role_id)
                except:
                    raise ValueError(f'Error: Could not find reference role. Application needs renewed setup.')
                    return

        return reference_role



    async def get_database_albumimage(artist, album, substitute=""):
        if substitute == "https://lastfm.freetls.fastly.net/i/u/34s/2a96cbd8b46e442fc41c2b86b821562f.png":
            substitute = ""

        artist_fltr = Utils.compactnamefilter(artist, "artist", "alias")
        album_fltr = Utils.compactnamefilter(album, "album")

        try:
            conSM = sqlite3.connect('databases/scrobblemeta.db')
            curSM = conSM.cursor()
            result = curSM.execute("SELECT cover_url, last_update FROM albuminfo WHERE artist_filtername = ? AND album_filtername = ?", (artist_fltr, album_fltr))
            rtuple = result.fetchone()

            if rtuple is None:
                return substitute, 0

            image = str(rtuple[0])
            last_update = int(rtuple[1])

        except Exception as e:
            print("Error:", e)
            image = substitute
            last_update = 0

        return image, last_update



    async def get_database_artistimage(artist):
        artist_fltr = Utils.compactnamefilter(artist,"artist","alias")

        try:
            conSM = sqlite3.connect('databases/scrobblemeta.db')
            curSM = conSM.cursor()
            result = curSM.execute("SELECT thumbnail, spotify_update FROM artistinfo WHERE filtername = ?", (artist_fltr,))
            rtuple = result.fetchone()

            if rtuple is None:
                return "", 0

            thumbnail = str(rtuple[0])
            update_time = Utils.forceinteger(rtuple[1])

            if thumbnail == "https://lastfm.freetls.fastly.net/i/u/34s/2a96cbd8b46e442fc41c2b86b821562f.png":
                thumbnail = ""
        except Exception as e:
            print("Error:", e)
            thumbnail = ""
            update_time = 0

        return thumbnail, update_time



    async def get_spotify_artistimage(artist, lfm_name=None, substitute="", albumname=""):
        """main idea is to fetch the albumname from a users table.
        subsitute is an alternative image url if no image is found.
        in case an albumname is known, just use that.
        """
        try:
            ClientID = os.getenv("Spotify_ClientID")
            ClientSecret = os.getenv("Spotify_ClientSecret")
            if ClientID is None:
                raise ValueError("No SpotiPy API provided")
        except Exception as e:
            print("Error while trying to fetch artist images:", e)
            return ""

        auth_manager = SpotifyClientCredentials(client_id=ClientID, client_secret=ClientSecret)
        sp = spotipy.Spotify(auth_manager=auth_manager)

        try:
            if lfm_name is None and albumname == "":
                raise ValueError("unknown user, cannot fetch album info from database, fetching artist info directly")

            fetch_with_albuminfo = True
            album = ""

            # GET ALBUM INFO

            if albumname == "":
                now = int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds())
                cutofftime = now - 365*24*60*60
                conFM = sqlite3.connect('databases/scrobbledata.db')
                curFM = conFM.cursor()
                result = [item[0] for item in curFM.execute(f"SELECT album_name FROM [{lfm_name}] WHERE UPPER(artist_name) = ? AND album_name != ? AND date_uts > ? ORDER BY date_uts DESC LIMIT 1", (artist.upper(), "", cutofftime)).fetchall()]

                if len(result) == 0:
                    raise ValueError("could not find recent album entry in database")

            if (albumname != "") or (albumname == "" and len(result) > 0 and result[0] != ""):

                if (albumname == "" and len(result) > 0 and result[0] != ""):
                    album = Utils.compactaddendumfilter(result[0], "album")
                else:
                    album = albumname

                artist = artist.replace("'","")
                query = f"artist:{artist} album:{album}"
                response = sp.search(q=query, type="album", limit=1)
                try:
                    album_dict = response['albums']['items'][0]
                    artist_id = album_dict['artists'][0]['id']
                except Exception as e:
                    raise ValueError(f"could not find artist/album combination on spotify, searching for artist only instead")
            else:
                raise ValueError("could not find recent valid album entry in database")

        except Exception as e:
            print(f"Artist Info Warning: {e} --- {artist} - {album}")
            fetch_with_albuminfo = False

            # FETCH ARTIST DIRECTLY
            query = f"artist:{artist}"
            response = sp.search(q=query, type="artist", limit=1)
            try:
                artist_id = response['artists']['items'][0]['id']
            except:
                return substitute


        try:
            artist_info = sp.artist(artist_id)
            image = artist_info['images'][0]['url']
            fetched_artist = artist_info['name']
            try:
                tags = artist_info["genres"]
            except:
                tags = []

            if image != "":
                if fetch_with_albuminfo:
                    # higher confidence of accuracy if album info is used
                    try:
                        await Utils.update_spotify_artist_info(artist, artist_id, image, tags)
                    except Exception as e:
                        print("Failed to update artist info in scrobble meta database:", e)
                else:
                    # otherwise check whether the artist name even resembles the original search
                    compact_artist = Utils.compactnamefilter(artist, "artist", "alias")
                    compact_fetched_artist = Utils.compactnamefilter(fetched_artist, "artist", "alias")

                    if compact_artist != compact_fetched_artist:
                        print("Spotify delivered a presumably wrong artist... using default picture instead")
                        return substitute
        except:
            image = substitute

        return image



    async def lastfm_get(ctx, payload, cooldown, *args):
        if cooldown:
            cooldown_slot = "lastfm"

            if len(args) > 0:
                if args[0].lower() == "userupdate":
                    cooldown_slot = "lastfm_update"

            try: 
                await Utils.cooldown(ctx, cooldown_slot)
            except Exception as e:
                await Utils.cooldown_exception(ctx, e, "LastFM")
                return "rate limit"

        try:
            APP_NAME = "_" + os.getenv("lfm_app_name")
        except:
            APP_NAME = ""

        try:
            REGISTERED_TO = "_by:" + os.getenv("lfm_registered_to")
        except:
            REGISTERED_TO = ""

        try:
            API_KEY = os.getenv("lfm_api_key")
            SHARED_SECRET = os.getenv("lfm_shared_secret")
            if API_KEY is None:
                raise ValueError("No LastFM keys provided")
        except:
            raise ValueError("No LastFM keys provided")
        
        try:
            version = Utils.get_version().replace("version","v").replace(" ","").strip()
        except:
            version = "v_X"

        USER_AGENT = f'MDM_Bot_{version}{APP_NAME}{REGISTERED_TO}_function:NowPlaying'

        # define headers and URL
        headers = {'user-agent': USER_AGENT}
        url = 'https://ws.audioscrobbler.com/2.0/'

        # Add API key and format to the payload
        payload['api_key'] = API_KEY
        payload['format'] = 'json'

        #response = requests.get(url, headers=headers, params=payload)
        response = await Utils.asyncrequest_get(url, headers=headers, params=payload)
        return response
        


    async def multi_embed_message(ctx, header, text_list, color, footer, channel):
        # Embed title is limited to 256 characters
        # Embed description is limited to 4096 characters
        # An embed can contain a maximum of 25 fields
        # A field name/title is limited to 256 character and the value of the field is limited to 1024 characters
        # Embed footer is limited to 2048 characters
        # Embed author name is limited to 256 characters
        # The total of characters allowed in an embed is 6000

        if len(text_list) == 0:
            print("error: text list empty")
            return

        if channel == None or channel == "":
            channel = ctx.channel 

        embedtexts = [""]
        k = 0
        for text in text_list:
            if len(embedtexts[k]) + len(text) < 4000:
                embedtexts[k] += f"\n{text}"
            else:
                embedtexts.append(text[:4000])
                k += 1
        i = 0
        n = len(embedtexts)
        if n == 1:
            # character limit
            if len(header) > 256:
                header = header[:253] + "..."
                if len(footer) > 1544:
                    footer = footer[:1541] + "..."
            # send embed
            embed = discord.Embed(title=header, description=embedtexts[0], color=color)
            if footer.strip() != "":
                embed.set_footer(text=footer)
            last_message = await channel.send(embed=embed)
        else:
            for description in embedtexts:
                i += 1
                # character limit
                counterlength = len(f" ({i}/{n})")
                if len(header) + counterlength > 256:
                    header_final = header[:253-counterlength] + "..."
                else:
                    header_final = header
                if len(footer) > 1544:
                    footer = footer[:1541] + "..."
                # send embed
                if i == 1:
                    embed = discord.Embed(title=header_final, description=description, color=color)
                else:
                    embed = discord.Embed(title="", description=description, color=color)
                if footer.strip() != "" and i == n:
                    embed.set_footer(text=footer)
                last_message = await channel.send(embed=embed)
        
        return last_message



    async def multi_field_embed(ctx, header, text_string, fields_list, color, footer, channel):
        # limit text to 3440 char (for 1st embed only)
        # limit footer to 1024 char (for last embed only)
        # every field limited to 256 + 1024 char
        if len(fields_list) == 0:
            print("error: field list empty")
            return

        if channel == None or channel == "":
            channel = ctx.channel 

        if len(header) > 256:
            header = header[:253] + "..."
        if len(text_string) > 3440:
            text_string = text_string[:3437] + "..."
        if len(footer) > 1024:
            footer = footer[:1021] + "..."

        embeds_list = []
        k = 0
        embeds_list.append(discord.Embed(title=header, description=text_string, color=color))
        current_length = len(header) + len(text_string)

        fieldcount = 0
        for item in fields_list:
            if len(item) > 0:
                field_header = item[0]
                if len(field_header) > 256:
                    field_header = field_header[:253] + "..."
                if len(item) > 1:
                    field_text = '\n'.join(item[1:])
                    if len(field_text) > 1024:
                        field_text = field_text[:1020] + "\n..."
                else:
                    field_text = ""

                if current_length + len(field_header) + len(field_text) < 6000 and fieldcount < 24:
                    fieldcount += 1
                    current_length += len(field_header) + len(field_text)
                    embeds_list[k].add_field(name=field_header, value=field_text, inline=False)
                else:
                    k += 1
                    fieldcount = 0
                    embeds_list.append(discord.Embed(title="", description="", color=color))
                    current_length = len(field_header) + len(field_text)
                    embeds_list[k].add_field(name=field_header, value=field_text, inline=False)

        if current_length + len(footer) < 6000:
            embeds_list[k].set_footer(text=footer)
        else:
            k += 1
            embeds_list.append(discord.Embed(title="", description="", color=color))
            embeds_list[k].set_footer(text=footer)

        for embed in embeds_list:
            await ctx.send(embed=embed)



    async def multi_message(ctx, word_list, channel):
        if len(word_list) == 0:
            print("error: word list empty")
            return

        if channel == None or channel == "":
            channel = ctx.channel 

        msgtexts = [""]
        k = 0
        for word in word_list:
            if len(msgtexts[k]) + len(word) < 2000:
                msgtexts[k] += f" {word}"
            else:
                msgtexts.append(word)
                k += 1

        for msg in msgtexts:
            await ctx.send(msg)



    async def remove_role_mentions_from_string(textstring, ctx):
        """ctx = None in case function has no access to ctx"""
        try:
            textstring_split = textstring.replace(">", "> ").replace("<", " <").split()
            while "" in textstring_split:
                textstring_split.remove("")

            textstring_filteredlist = []
            for arg in textstring_split:
                if arg.startswith("<@&") and arg.endswith(">") and Utils.represents_integer(arg[3:-1]):
                    if ctx is None:
                        textstring_filteredlist.append("@disabled_rolemention")
                    else:
                        try:
                            role = ctx.guild.get_role(int(arg[3:-1]))
                            rolename = str(role.name)
                            if len(rolename) > 50:
                                rolename = rolename[:47] + "..."
                        except:
                            rolename = "inavlid_role"
                        textstring_filteredlist.append(f"@{rolename}")
                else:
                    textstring_filteredlist.append(arg)
            textstring_new = " ".join(textstring_filteredlist)
        except:
            textstring_new = textstring

        return textstring_new



    async def reply_verifification(ctx, args, general_channel):
        # todo: include optional arg "--fw" to forward every message of that user that was replied to
        if ctx.message.reference is None:
            return
            
        target_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)

        argument_string = ' '.join(args)
        mention         = "<@" + str(target_message.author.id) + ">"

        if mention in argument_string:
            emoji = Utils.emoji("yay")
            header = f"Introducing {target_message.author.display_name} {emoji}"
            intro_text = str(target_message.content)
            embed = discord.Embed(title=header, description=intro_text[:4000], color=0xFFFFFF)
            embed.set_footer(text=f"- {target_message.author.name}")
            await general_channel.send(embed=embed)



    async def scrape_exchangerates():
        """In case Exchangerate API key isn't provided this gives rudimentary support for currency conversion"""
        conER = sqlite3.connect('databases/exchangerate.db')
        curER = conER.cursor()
        curER.execute('''CREATE TABLE IF NOT EXISTS USDexchangerate (code text, value text, currency text, country text, last_updated text, time_stamp text)''')
        known_currencies = [item[0] for item in curER.execute("SELECT code FROM USDexchangerate").fetchall()]

        currency_list = [
                        ["EUR", "", "Euro", "European Union", "Euro"],
                        ["GBP", "", "Pound Sterling", "United Kingdom", "British Pound"],
                        ["JPY", "", "Japanese Yen", "Japan", "Japanese Yen"],
                        ["KRW", "", "South Korean Won", "South Korea", "South Korean Won"],
                        ["TWD", "", "New Taiwan Dollar", "Taiwan", "Taiwan New Dollar"],
                        ["CAD", "", "Canadian Dollar", "Canada", "Canadian Dollar"],
                        ["CHF", "", "Swiss Franc", "Switzerland", "Swiss Franc"],
                        ["CNY", "", "Chinese Renminbi", "China", "Chinese Yuan Renminbi"],
                        ["AUD", "", "Australian Dollar", "Australia", "Australian Dollar"],
                        ["INR", "", "Indian Rupee", "India", "Indian Rupee"],
                        ["SEK", "", "Swedish Krona", "Sweden", "Swedish Krona"],
                        ["DKK", "", "Danish Krone", "Denmark", "Danish Krone"],
                        ["NOK", "", "Norwegian Krone", "Norway", "Norwegian Krone"],
                        ["RUB", "", "Russian Ruble", "Russia", "Russian Ruble"],
                        ["TRY", "", "Turkish Lira", "Turkey", "Turkish Lira"],
                        ]
        currency_webnames = [item[4] for item in currency_list]

        if len(known_currencies) > len(currency_list) + 1:
            print("It seems that API data has been used in the past. No web scraping needed. If you want to perform the webscrape anyway, you need to delete databases/exchangerate.db first.")
            message = "ExchangeRate API seems to have been used in the past. WebScraping not performed to not mess with data.\n(If you want to perform the webscrape anyway, host needs to delete databases/exchangerate.db first or mods need to load backup with empty database file.)"
            success = False
            return message, success

        try:
            session = requests.session()
            burp0_url = "https://www.x-rates.com:443/table/?from=USD&amount=1"
            burp0_headers = {"Sec-Ch-Ua": "\"Chromium\";v=\"121\", \"Not A(Brand\";v=\"99\"", "Sec-Ch-Ua-Mobile": "?0", "Sec-Ch-Ua-Platform": "\"Windows\"", "Upgrade-Insecure-Requests": "1", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.160 Safari/537.36", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7", "Sec-Fetch-Site": "none", "Sec-Fetch-Mode": "navigate", "Sec-Fetch-User": "?1", "Sec-Fetch-Dest": "document", "Accept-Encoding": "gzip, deflate, br", "Accept-Language": "en-US;q=0.8,en;q=0.7", "Priority": "u=0, i", "Connection": "close"}
            response = session.get(burp0_url, headers=burp0_headers)

            soup = BeautifulSoup(response.text, "html.parser")

            for td in soup.find_all('td'):
                try:
                    if td.contents[0] in currency_webnames:
                        for i in range(len(currency_list)):
                            if currency_list[i][4] == td.contents[0]:
                                next_td = td.findNext('td')
                                a = next_td.find('a')
                                rate = a.contents[0]
                                currency_list[i][1] = rate
                                break
                except:
                    pass

        except Exception as e:
            print("Error while trying to scrape x-rates web page")
            message = "Error while trying to scrape x-rates web page.)"
            success = False
            return message, success

        utc_string_now = str(datetime.utcnow()).split(".")[0]
        update_time_string = f"{utc_string_now} UTC (webscraped)"

        counter = 0
        try:
            if len(known_currencies) == 0:
                curER.execute("INSERT INTO USDexchangerate VALUES (?, ?, ?, ?, ?, ?)", ("USD", "1", "United States Dollar", "United States", update_time_string, "0"))

            else:
                curER.execute("UPDATE USDexchangerate SET last_updated = ? WHERE code = ?", (update_time_string, "USD"))

            for item in currency_list:
                currencycode = item[0]
                exchangevalue = item[1]
                name = item[2]
                country = item[3]
                if Utils.represents_float(exchangevalue):
                    counter += 1
                    if currencycode in known_currencies:
                        curER.execute("UPDATE USDexchangerate SET value = ?, last_updated = ? WHERE code = ?", (exchangevalue, update_time_string, currencycode))
                    else:
                        curER.execute("INSERT INTO USDexchangerate VALUES (?, ?, ?, ?, ?, ?)", (currencycode, exchangevalue, name, country, update_time_string, "0"))
            conER.commit()
            conER.close()

            await Utils.changetimeupdate()
        except Exception as e:
            print(e)
            message = "Error while trying to insert ExchangeRate data into database."
            success = False
            return message, success

        if counter > 0:
            message = f"Successfully updated {counter} entries in exchangerate database via web scrape."
            success = True
            print(f"Successfully updated {counter} entries in exchangerate database via web scrape.")
            return message, success

        else:
            message = f"Could not update any entries in exchangerate database via web scrape."
            success = False
            print(f"Could not update any entries in exchangerate database via web scrape.")
            return message, success



    @to_thread 
    def scrobble_metaupdate(scrobble_list):
        conSM = sqlite3.connect('databases/scrobblemeta.db')
        curSM = conSM.cursor()

        artist_list = [item[0] for item in curSM.execute("SELECT filtername FROM artistinfo").fetchall()]
        aa_list = [(item[0], item[1]) for item in curSM.execute("SELECT artist_filtername, album_filtername FROM albuminfo").fetchall()]

        for item in scrobble_list:
            artist_name = item[1]
            album_name = item[2]

            artist_filtername = Utils.compactnamefilter(artist_name, "artist", "alias")
            album_filter = Utils.compactnamefilter(album_name, "album")

            if artist_filtername not in artist_list:
                curSM.execute("INSERT INTO artistinfo VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (artist_name, artist_filtername, "", "", 0, "", "", "", 0, "", ""))
                artist_list.append(artist_filtername)

            if (artist_filtername, album_filter) not in aa_list:
                curSM.execute("INSERT INTO albuminfo VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (artist_name, artist_filtername, album_name, album_filter, "", "", 0, "", 0))
                aa_list.append((artist_filtername, album_filter))
        conSM.commit()



    async def scrobble_update(lfm_name, allow_from_scratch, bot):
        def to_thread(func: typing.Callable) -> typing.Coroutine:
            """wrapper for blocking functions"""
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                return await asyncio.to_thread(func, *args, **kwargs)
            return wrapper

        async def get_userscrobbles_from_page(lfm_name, page):
            try:
                payload = {
                    'method': 'user.getRecentTracks',
                    'user': lfm_name,
                    'limit': "200",
                    'page': page,
                }
                cooldown = True
                response = await Utils.lastfm_get(None, payload, cooldown, "userupdate")
                if response == "rate limit":
                    raise ValueError("Hit internal lastfm rate limit.")
                try:
                    rjson = response.json()
                    total_pages = rjson['recenttracks']['@attr']['totalPages']
                    page = rjson['recenttracks']['@attr']['page']
                    total = rjson['recenttracks']['@attr']['total']
                    tracklist = rjson['recenttracks']['track']
                    return tracklist, total_pages, total
                except:
                    try:
                        raise ValueError(f"```{str(response.json())}```")
                    except:
                        raise ValueError(f"{str(response)}")
            except Exception as e:
                print("Error:", e)
                raise ValueError(f"while trying to fetch user information: {e}.")

        def parse_scrobbled_track(trackdata):
            try:
                artist_name = trackdata['artist']['#text']
            except:
                artist_name = ""
            try:
                album_name = trackdata['album']['#text']
            except:
                album_name = ""
            try:
                track_name = trackdata['name']
            except:
                track_name = ""
            try:
                date_uts = trackdata['date']['uts']
            except:
                date_uts = 0
            return (artist_name, album_name, track_name, date_uts)

        @to_thread    
        def databases_insert(lfm_name):
            conFM1 = sqlite3.connect('databases/scrobbledata.db')
            curFM1 = conFM1.cursor()
            curFM1.execute(f"CREATE TABLE IF NOT EXISTS [{lfm_name}] (id integer, artist_name text, album_name text, track_name text, date_uts integer)")

            conFM2 = sqlite3.connect('databases/scrobbledata_releasewise.db')
            curFM2 = conFM2.cursor()
            curFM2.execute(f"CREATE TABLE IF NOT EXISTS [{lfm_name}] (artist_name text, album_name text, count integer, last_time integer, first_time integer)")

            conFM3 = sqlite3.connect('databases/scrobbledata_trackwise.db')
            curFM3 = conFM3.cursor()
            curFM3.execute(f"CREATE TABLE IF NOT EXISTS [{lfm_name}] (artist_name text, track_name text, count integer, last_time integer, first_time integer)")

            for item_indexed in sorted(scrobble_list, key = lambda x : x[0]):
                curFM1.execute(f"INSERT INTO [{lfm_name}] VALUES (?, ?, ?, ?, ?)", item_indexed)

            print(">>>> DB 1")
            for k,v in album_dict.items():
                artist = k[0]
                album  = k[1]
                try:
                    count = int(v[0])
                except:
                    count = 0
                try:
                    now_time = int(v[1])
                except:
                    now_time = 0

                try:
                    first_time = int(v[2])
                except:
                    first_time = Utils.year9999()
                
                try:
                    result = curFM2.execute(f"SELECT count, last_time, first_time FROM [{lfm_name}] WHERE artist_name = ? AND album_name = ?", (artist, album))
                    rtuple = result.fetchone()
                    prev_count = int(rtuple[0])
                    try:
                        prev_time = int(rtuple[1])
                    except:
                        prev_time = 0
                    try:
                        prev_first = int(rtuple[2])
                    except:
                        prev_first = Utils.year9999()
                except:
                    prev_count = 0
                    prev_time = 0
                    prev_first = Utils.year9999()

                if prev_count == 0:
                    curFM2.execute(f"INSERT INTO [{lfm_name}] VALUES (?, ?, ?, ?, ?)", (artist, album, count, now_time, first_time))

                else:
                    new_count = prev_count + count
                    if prev_time < now_time:
                        time = now_time
                    else:
                        time = prev_time
                    if first_time < prev_first:
                        curFM2.execute(f"UPDATE [{lfm_name}] SET count = ?, last_time = ?, first_time = ? WHERE artist_name = ? AND album_name = ?", (new_count, time, first_time, artist, album))
                    else:
                        curFM2.execute(f"UPDATE [{lfm_name}] SET count = ?, last_time = ? WHERE artist_name = ? AND album_name = ?", (new_count, time, artist, album))
            
            print(">>>> DB 2")
            for k,v in track_dict.items():
                artist = k[0]
                track  = k[1]
                try:
                    count = int(v[0])
                except Exception as e:
                    count = 0
                try:
                    now_time = int(v[1])
                except:
                    now_time = 0

                try:
                    first_time = int(v[2])
                except:
                    first_time = Utils.year9999()
                
                try:
                    result = curFM3.execute(f"SELECT count, last_time, first_time FROM [{lfm_name}] WHERE artist_name = ? AND track_name = ?", (artist, track))
                    rtuple = result.fetchone()
                    prev_count = int(rtuple[0])
                    try:
                        prev_time = int(rtuple[1])
                    except:
                        prev_time = 0
                    try:
                        prev_first = int(rtuple[2])
                    except:
                        prev_first = Utils.year9999()
                except:
                    prev_count = 0
                    prev_time = 0
                    prev_first = Utils.year9999()

                if prev_count == 0:
                    curFM3.execute(f"INSERT INTO [{lfm_name}] VALUES (?, ?, ?, ?, ?)", (artist, track, count, now_time, first_time))

                else:
                    new_count = prev_count + count
                    if prev_time < now_time:
                        time = now_time
                    else:
                        time = prev_time
                    # keep first time
                    if first_time < prev_first:
                        curFM3.execute(f"UPDATE [{lfm_name}] SET count = ?, last_time = ?, first_time = ? WHERE artist_name = ? AND track_name = ?", (new_count, time, first_time, artist, track))
                    else:
                        curFM3.execute(f"UPDATE [{lfm_name}] SET count = ?, last_time = ? WHERE artist_name = ? AND track_name = ?", (new_count, time, artist, track))
            
            print(">>>> DB 3")

            conFM1.commit()
            conFM2.commit()
            conFM3.commit()

            print(">>>> commit.")

        def recent_scrobble_auto_update_error_messaging(lfm_name):
            hours = 24 # hours that count as recent, within this time another message for an update error won't be sent

            try:
                # first check whether an error happened (recently)
                now = int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds())

                conC = sqlite3.connect('databases/cooldowns.db')
                curC = conC.cursor()
                curC.execute('''CREATE TABLE IF NOT EXISTS scrobbleupdate_errortransmission (lfm_name text, time_stamp integer)''')

                cooldown_db_list = [item[0] for item in curC.execute("SELECT time_stamp FROM scrobbleupdate_errortransmission WHERE lfm_name = ?", (lfm_name,)).fetchall()]

                if (len(cooldown_db_list) > 0 and min(cooldown_db_list) > now - hours * 3600):
                    recently_messaged = True
                else:
                    recently_messaged = False

                # if not save username
                if not recently_messaged:
                    curC.execute("UPDATE scrobbleupdate_errortransmission SET time_stamp = ? WHERE lfm_name = ?", (now, lfm_name))
                    conC.commit()

                # delete all older than set amount of hours above
                curC.execute("DELETE FROM scrobbleupdate_errortransmission WHERE time_stamp < ?", (now - hours * 3600,))
                conC.commit()

                # return
                return recently_messaged

            except Exception as e:
                print("ERROR WHILE CHECKING ERROR MESSAGING DB:", e)
                return False

        def add_recent_scrobble_auto_update_error_messaging(lfm_name):
            now = int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds())

            conC = sqlite3.connect('databases/cooldowns.db')
            curC = conC.cursor()
            curC.execute("INSERT INTO scrobbleupdate_errortransmission VALUES (?, ?)", (lfm_name, now))
            conC.commit()

        ##########################################################################################################################################
        ### actual function

        scrobble_list = []
        album_dict = {}
        track_dict = {}

        try:
            conFM = sqlite3.connect('databases/scrobbledata.db')
            curFM = conFM.cursor()
            curFM.execute(f"CREATE TABLE IF NOT EXISTS [{lfm_name}] (id integer, artist_name text, album_name text, track_name text, date_uts integer)")
            lasttime = int([item[0] for item in curFM.execute(f"SELECT MAX(date_uts) FROM [{lfm_name}]").fetchall()][0])
        except Exception as e:
            lasttime = 0

        if lasttime == 0 and allow_from_scratch == False:
            return

        print(f">>>> scrobble update: {lfm_name}")

        page_int = 0
        total_pages_int = 1
        continue_loop = True
        count = 0
        i = -1

        try:
            previous_item = None
            while page_int < total_pages_int:
                if not continue_loop:
                    break
                page_int += 1
                page_string = str(page_int)

                try_list = [5,10,15]
                if page_int <= 1:
                    try_list.append(30)

                for t in try_list:
                    try:
                        tracklist, total_pages, total = await get_userscrobbles_from_page(lfm_name, page_string)
                        break
                    except Exception as e:
                        print(f"Waiting {t} seconds... ({e})")
                        await asyncio.sleep(t)
                        print("continue...")
                else:
                    print("Cancelled action.")
                    raise ValueError(f"Unable to fetch scrobble data from: {lfm_name}")

                if i == -1: # first page
                    i = int(total)

                total_pages_int = int(total_pages)

                # PARSE PAGE ENTRIES
                for trackdata in tracklist:
                    item = parse_scrobbled_track(trackdata)
                    uts = int(item[-1])
                    if uts == 0: #print("skipping currently listened to track")
                        continue
                    elif uts <= lasttime:
                        continue_loop = False
                        break
                    if previous_item == item: 
                        print("skipping double entry")
                        continue
                    elif previous_item != None and uts > int(previous_item[-1]):
                        print("skipping entry with time anomaly")
                        continue

                    # add item to scrobble DB
                    item_indexed = (i,) + item
                    scrobble_list.append(item_indexed)  
                    count += 1
                    i -= 1

                    # prepare for inserting into releasewise DB
                    artist_filtername = Utils.compactnamefilter(item[0],"artist","alias") #''.join([x for x in item[0].upper() if x.isalnum()])
                    album_filtername = Utils.compactnamefilter(item[1],"album") #''.join([x for x in item[1].upper() if x.isalnum()])
                    track_filtername = Utils.compactnamefilter(item[2],"track")
                    
                    if (artist_filtername, album_filtername) in album_dict:
                        release = album_dict[(artist_filtername, album_filtername)]
                        try:
                            releasecount = int(release[0])
                        except:
                            releasecount = 0
                        try:
                            releaselastprev = int(release[1])
                        except:
                            releaselastprev = 0

                        releasefirst = release[2]

                        album_dict[(artist_filtername, album_filtername)] = (releasecount + 1, releaselastprev, releasefirst)
                    else:
                        try:
                            releaselast = int(item[3])
                            releasefirst = releaselast
                            if releasefirst < 1000000000:
                                releasefirst = Utils.year9999()
                        except:
                            releaselast = 0
                            releasefirst = Utils.year9999()
                        album_dict[(artist_filtername, album_filtername)] = (1, releaselast, releasefirst)

                    # TRACKWISE DATABASE PREPARATION
                    if (artist_filtername, track_filtername) in track_dict:
                        trackitem = track_dict[(artist_filtername, track_filtername)]
                        try:
                            trackcount = int(trackitem[0])
                        except:
                            trackcount = 0
                        try:
                            tracklastprev = int(trackitem[1])
                        except:
                            tracklastprev = 0

                        trackfirst = trackitem[2]

                        track_dict[(artist_filtername, track_filtername)] = (trackcount + 1, tracklastprev, trackfirst)
                    else:
                        try:
                            tracklast = int(item[3])
                            trackfirst = tracklast
                            if trackfirst < 1000000000:
                                trackfirst = Utils.year9999()
                        except:
                            tracklast = 0
                            trackfirst = Utils.year9999()
                        track_dict[(artist_filtername, track_filtername)] = (1, tracklast, trackfirst)

                    # next iteration
                    previous_item = item
            if count > 0:
                print(f"loaded scrobble data of {lfm_name} : ({count} entries)")

        except Exception as e:
            if str(e).startswith("Unable to fetch scrobble data from:"):
                standard_scrobble_fetching_error = True
                text = f"Could not fetch last.fm information from user `{lfm_name}`.\nCheck on https://www.last.fm/user/{lfm_name} whether the page still exists. If not and this error persists it is recommended to either scrobble-ban them or purge their data from the np-settings database via command `removefm`.\n\n"
            else:
                standard_scrobble_fetching_error = False
                text = f"There was a problem while handling data of user `{lfm_name}`.\n\n`Error message:` {e}"

            title = "⚠️ Scrobble Auto-Update Error"
            if (standard_scrobble_fetching_error and recent_scrobble_auto_update_error_messaging(lfm_name)):
                print(text)
            else:
                await Utils.bot_spam_send(bot, title, text)
                add_recent_scrobble_auto_update_error_messaging(lfm_name)

        await databases_insert(lfm_name)

        try:
            await Utils.scrobble_metaupdate(scrobble_list)
        except Exception as e:
            print("Error:", e)
        await Utils.changetimeupdate()




    async def setup_msg(ctx, bot, text):
        def check(m): # checking if it's the same user and channel
            return ((m.author == ctx.author) and (m.channel == ctx.channel))

        await ctx.send(f"{text}\n\nRespond with `skip` to skip step, or with `cancel` to stop entire process.")

        try: # waiting for message
            async with ctx.typing():
                response = await bot.wait_for('message', check=check, timeout=300.0) # timeout - how long bot waits for message (in seconds)
        except asyncio.TimeoutError: # returning after timeout
            await ctx.send("action timed out")
            return "cancel"

        if response.content.lower().strip() not in ["cancel", "skip"]:
            return response.content.strip()

        elif response.content.lower().strip() == "cancel":
            await ctx.send("cancelled action")
            return "cancel"

        else:
            await ctx.send("skipping action")
            return "skip"



    async def setup_channel(ctx, bot, channel, text):
        def check(m): # checking if it's the same user and channel
            return ((m.author == ctx.author) and (m.channel == channel))

        await ctx.send(f"{text}")

        try: # waiting for message
            async with ctx.typing():
                response = await bot.wait_for('message', check=check, timeout=300.0) # timeout - how long bot waits for message (in seconds)
        except asyncio.TimeoutError: # returning after timeout
            await ctx.send("action timed out")
            return None

        return response # return message object



    async def timeparse(textstring, *from_timestamp):
        if len(from_timestamp) == 0:
            ts = None
        else:
            ts = from_timestamp[0]

        if textstring.strip() == "":
            return "infinity", "indefinite", ""

        # buffer for <>-objects and swap out role pings for plain text
        textstring = await Utils.remove_role_mentions_from_string(textstring, None)

        # parse "until" time or "in" time

        if textstring.lower().strip().startswith("until"):

            ### parse time from end timestamp
            word_list = Utils.separate_num_alph_string_componentpreserving(textstring).strip().split()
            if len(word_list) < 2:
                return "infinity", "indefinite", textstring

            if word_list[0].lower().strip() == "until" and Utils.represents_integer(word_list[1]):
                utc_endtime = int(word_list[1])
                if len(word_list) > 2:
                    rest = ' '.join(word_list[2:])
                else:
                    rest = ""
            else:
                return "infinity", "indefinite", textstring

            utc_now = int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds())

            total_seconds = utc_endtime - utc_now
            timetext = Utils.seconds_to_readabletime(total_seconds, False, ts)
            timeseconds = str(total_seconds)

            return timeseconds, timetext, rest

        else:
            ### parse time from given values and units

            word_list_pre = Utils.separate_num_alph_componentpreserving(textstring)
            word_list = []
            for word in word_list_pre: # this is to separate reason text from the unit text
                wordsplit = word.split()
                for split in wordsplit:
                    word_list.append(split)

            if len(word_list) > 0 and word_list[0].lower().strip() == "for":
                if len(word_list) > 1 and Utils.represents_integer(word_list[1].strip()):
                    word_list.pop(0)
                else:
                    return "infinity", "indefinite", textstring

            unit_seconds = Utils.unit_seconds()
            timeelements = []
            rest = ""
            j = 0
            for i in range(math.floor(len(word_list)/2)):
                value = word_list[2*i].strip()
                unit = word_list[2*i + 1].lower().strip()
                j += 2

                if Utils.represents_integer(value) and (unit in unit_seconds or unit in ["mon", "month", "months", "y", "year", "years"]):
                    timeelements.append([value, unit])
                else:
                    rest = ' '.join(word_list[2*i:])
                    break
            else:
                rest = ' '.join(word_list[j:])

            # FINALIZE

            if len(timeelements) == 0:
                return "infinity", "indefinite", textstring
            else:
                total_seconds = 0
                for timeelement in timeelements:
                    value = int(timeelement[0])
                    unit = timeelement[1]
                    if unit in unit_seconds:
                        total_seconds += value * unit_seconds[unit]
                    elif unit in ["mon", "month", "months"]:
                        total_seconds += Utils.months_to_seconds(value, None, None)
                    elif unit in ["y", "year", "years"]:
                        total_seconds += Utils.years_to_seconds(value, None, None, None)
                    else:
                        print(f"did not recognise time unit {unit}")

                timetext = Utils.seconds_to_readabletime(total_seconds, False, ts)
                timeseconds = str(total_seconds)

                return timeseconds, timetext, rest



    async def update_lastfm_artistalbuminfo(artist, album, thumbnail, tags):
        """first 3 arguments must be strings, 
        tags must be either a list of strings or can be None object if changes there are unwanted"""
        now = int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds())
        artistcompact = Utils.compactnamefilter(artist, "artist", "alias")
        albumcompact = Utils.compactnamefilter(album, "album")
        if tags is not None:
            tag_string = ';'.join(tags)
        else:
            tag_string = ""
        conSM = sqlite3.connect('databases/scrobblemeta.db')
        curSM = conSM.cursor()
        artistinfo_list = [item[0] for item in curSM.execute("SELECT last_update FROM albuminfo WHERE artist_filtername = ? AND album_filtername = ?", (artistcompact, albumcompact)).fetchall()]

        if len(artistinfo_list) == 0:
            curSM.execute("INSERT INTO albuminfo VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (artist, str(artistcompact), str(album), albumcompact, tag_string, thumbnail, now, "", 0))
        else:
            curSM.execute("UPDATE albuminfo SET artist = ?, album = ?, cover_url = ?, last_update = ? WHERE artist_filtername = ? AND album_filtername = ?", (artist, album, thumbnail, now, artistcompact, albumcompact))
            if tags is not None:
                curSM.execute("UPDATE albuminfo SET tags = ? WHERE artist_filtername = ? AND album_filtername = ?", (tag_string, artistcompact, albumcompact))
        conSM.commit()



    async def update_spotify_artist_info(artist, spotify_id, image, tags):
        artist_fltr = Utils.compactnamefilter(artist,"artist","alias")
        now = int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds())

        try:
            conSM = sqlite3.connect('databases/scrobblemeta.db')
            curSM = conSM.cursor()
            result = curSM.execute(f"SELECT thumbnail, tags_spotify, spotify_update FROM artistinfo WHERE filtername = ?", (artist_fltr,))
            rtuple = result.fetchone()

            try:
                thumbnail = str(rtuple[0])
                tagstring = str(rtuple[1])
                update_time = Utils.forceinteger(rtuple[2])
                entry_exists = True
            except:
                entry_exists = False

            tags_standardised = []
            for tag in tags:
                if tag not in tags_standardised:
                    tags_standardised.append(tag.lower().strip())
            tagstring = ';'.join(tags_standardised)

            if entry_exists:
                curSM.execute(f"UPDATE artistinfo SET thumbnail = ?, tags_spotify = ?, spotify_update = ? WHERE filtername = ?", (image, tagstring, now, artist_fltr))
            else:
                curSM.execute(f"INSERT INTO artistinfo VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (artist, artist_fltr, "", "", 0, spotify_id, image, tagstring, now, "", ""))
            conSM.commit()

        except Exception as e:
            print("Error while trying to update artist info with Spotify data:", e)




    async def update_role_database(ctx):
        con = sqlite3.connect('databases/roles.db')
        cur = con.cursor()
        
        known_ids = []
        r = cur.execute("SELECT id FROM roles")
        for row in r:
            known_ids.append(row[0])

        # add missing roles to db    
        existing_roles = [[str(r.id),str(r.name),'#' + str(r.color)[1:]] for r in ctx.guild.roles]
        for role in existing_roles:
            if not (role[0] in known_ids):
                cur.execute("INSERT INTO roles VALUES (?, ?, ?, ?, ?, ?, ?)", (role[0], role[1], 'False', 'none', '', role[2], ''))
                con.commit()

        # remove non-existing roles from db
        existing_role_ids = [r[0] for r in existing_roles]
        for role_id in known_ids:
            if not (role_id in existing_role_ids):
                cur.execute("DELETE FROM roles WHERE id = ?", (role_id,))
                con.commit()

        # update permissions and colors
        default_perms = await Utils.get_defaultperms(ctx)

        roles_n_perms = [[str(r.id), r.permissions, '#' + str(r.color)[1:]] for r in ctx.guild.roles]
        for rp in roles_n_perms:
            r_id = rp[0]
            r_col = rp[2]
            r_perm_list = [perm[0] for perm in rp[1] if perm[1]]
   
            r_perm_list_wodef = []
            for perm in r_perm_list:
                if perm not in default_perms:
                    r_perm_list_wodef.append(perm) 
            r_perms = ', '.join(r_perm_list_wodef)
            cur.execute("UPDATE roles SET permissions = ? WHERE id = ?", (str(r_perms), str(r_id)))
            cur.execute("UPDATE roles SET color = ? WHERE id = ?", (r_col, str(r_id)))
            con.commit()

        #update names
        names = [[str(r.id), r.name] for r in ctx.guild.roles]
        for n in names:
            r_id = n[0]
            r_name = n[1]
            cur.execute("UPDATE roles SET name = ? WHERE id = ?", (str(r_name), str(r_id)))
            con.commit()

        con.close()
        await Utils.changetimeupdate()



    async def user_role_protection(ctx, user_id, action):
        con = sqlite3.connect('databases/roles.db')
        cur = con.cursor()
        action_ = Utils.alphanum(action,"lower")

        soft = False

        userfound = [item[0] for item in cur.execute(f"SELECT {action_} FROM protections WHERE id_type = ? AND id = ?", ("user", str(user_id))).fetchall()]

        if "hard" in userfound:
            return "hard"
        elif "soft" in userfound:
            soft = True

        all_protected_role_ids = [[Utils.forceinteger(item[0]), item[1]] for item in cur.execute(f"SELECT id, {action_} FROM protections WHERE id_type = ?", ("role", )).fetchall()]

        member          = ctx.guild.get_member(Utils.forceinteger(user_id))
        member_role_ids = [role.id for role in member.roles]

        for r_item in all_protected_role_ids:
            r_id        = r_item[0]
            r_intensity = r_item[1]

            if r_intensity == "none" or r_id == 0:
                continue

            if r_id in member_role_ids:
                if r_intensity == "hard":
                    return "hard"
                elif r_intensity == "soft":
                    soft = True

        if soft:
            return "soft"

        return "none"





    
























































    ######################################################## CLOUD STUFF ###################################################################



    def dropbox_list_folder(dbx, folder, subfolder):
        """List a folder.

        Return a dict mapping unicode filenames to
        FileMetadata|FolderMetadata entries.
        """
        path = '/%s/%s' % (folder, subfolder.replace(os.path.sep, '/'))
        while '//' in path:
            path = path.replace('//', '/')
        path = path.rstrip('/')
        try:
            with Utils.stopwatch('list_folder'):
                res = dbx.files_list_folder(path)
        except dropbox.exceptions.ApiError as err:
            print('Folder listing failed for', path, '-- assumed empty:', err)
            return {}
        else:
            rv = {}
            for entry in res.entries:
                rv[entry.name] = entry
            return rv



    def dropbox_download(dbx, folder, subfolder, name):
        """Download a file.

        Return the bytes of the file, or None if it doesn't exist.
        """
        path = '/%s/%s/%s' % (folder, subfolder.replace(os.path.sep, '/'), name)
        while '//' in path:
            path = path.replace('//', '/')
        with Utils.stopwatch('download'):
            try:
                md, res = dbx.files_download(path)
            except dropbox.exceptions.HttpError as err:
                print('*** HTTP error', err)
                return None
        data = res.content
        print(len(data), 'bytes; md:', md)
        return data



    def dropbox_upload(dbx, fullname, folder, subfolder, name, overwrite=False):
        """Upload a file.

        Return the request response, or None in case of error.
        """
        path = '/%s/%s/%s' % (folder, subfolder.replace(os.path.sep, '/'), name)
        while '//' in path:
            path = path.replace('//', '/')
        mode = (dropbox.files.WriteMode.overwrite
                if overwrite
                else dropbox.files.WriteMode.add)
        mtime = os.path.getmtime(fullname)
        with open(fullname, 'rb') as f:
            data = f.read()
        with Utils.stopwatch('upload %d bytes' % len(data)):
            try:
                res = dbx.files_upload(data, path, mode, client_modified=datetime(*time.gmtime(mtime)[:6]), mute=True)
            except dropbox.exceptions.ApiError as err:
                print('*** API error', err)
                return None
        try:
            print('uploaded as', res.name.encode('utf-8'))
        except Exception as e:
            pass
        return res


    @contextlib.contextmanager
    def stopwatch(message):
        """Context manager to print how long a block of code took."""
        t0 = time.time()
        try:
            yield
        finally:
            t1 = time.time()
            print('Total elapsed time for %s: %.3f' % (message, t1 - t0))



    async def get_temporary_dropbox_token(ctx, bot):
        if ctx == None:
            try:
                con = sqlite3.connect(f'databases/botsettings.db')
                cur = con.cursor()
                botspamchannel_id = int([item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("botspam channel id",)).fetchall()][0])
            except:
                print("Bot spam/notification channel ID in database is faulty.")
                try:
                    botspamchannel_id = int(os.getenv("bot_channel_id"))
                    if botspamchannel_id is None:
                        raise ValueError("No botspamchannel id provided in .env file")
                except Exception as e:
                    print(f"Error in utils.get_temporary_dropbox_token():", e)
                    return
            try:
                channel = bot.get_channel(botspamchannel_id)
                if channel is None:
                    channel = await bot.fetch_channel(botspamchannel_id)
            except Exception as e:
                print("Error in utils.get_temporary_dropbox_token():", e)
                return
        else:
            channel = ctx.channel

        con = sqlite3.connect(f'databases/activity.db')
        cur = con.cursor()
        token_list = [[item[0],item[1]] for item in cur.execute("SELECT value, details FROM hostdata WHERE name = ?", ("dropbox token",)).fetchall()]
        now = int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds())

        # first check database
        if len(token_list) > 0 and Utils.represents_integer(token_list[0][1]) and now < int(token_list[0][1]) - 120:
            temp_token = str(token_list[0][0]).strip()
            expiration_time = int(token_list[0][1])
            print("using token saved in database")

        else:
            # check botspam messages
            the_message = None
            found = False
            conB = sqlite3.connect(f'databases/botsettings.db')
            curB = conB.cursor()
            app_id_list = [item[0] for item in curB.execute("SELECT value FROM botsettings WHERE name = ?", ("app id",)).fetchall()]

            async for msg in channel.history(limit=100):
                if "`token:`" in msg.content and str(msg.author.id) in app_id_list:
                    try:
                        the_message = msg
                        found = True
                        break
                    except Exception as e:
                        print(e)

            could_parse_token = False

            if found:
                try:
                    encrypted_thingy = str(the_message.content).split('`token:` ')[1].split('\n`expires:`')[0]
                    temp_token = Utils.decode(Utils.get_enc_key(), encrypted_thingy)
                    expiration_time = int(the_message.content.split('\n`expires:` ')[1].strip())

                    if now > int(expiration_time) - 120:
                        raise ValueError("old token")
                    print("using token from discord share")

                    could_parse_token = True
                except Exception as e:
                    print("Issue:", e)
                    could_parse_token = False
            
            if not could_parse_token:
                # receive new temporary token

                refresh_token = os.getenv('dropbox_refresh_token')
                client_id = os.getenv('dropbox_key')
                client_secret = os.getenv('dropbox_secret')

                url = f"https://api.dropbox.com/oauth2/token"
                payload = {
                    'refresh_token': refresh_token,
                    'grant_type': 'refresh_token',
                    'client_id': client_id,
                    'client_secret': client_secret,
                }
                response = requests.post(url, data=payload)

                try:
                    temp_token = response.json()['access_token']
                except:
                    temp_token = str(response.text).split('"access_token": "',1)[1].split('", "',1)[0].strip()
                try:
                    duration = int(response.json()['expires_in'])
                except:
                    duration = int(str(response.text).split('"expires_in":',1)[1].split('}',1)[0].strip())

                encoded_key = Utils.encode(Utils.get_enc_key(), temp_token)
                expiration_time = now + duration
                print("using fresh token")

                await channel.send(f"`token:` {encoded_key}\n`expires:` {expiration_time}")

        if len(token_list) > 0:
            cur.execute("UPDATE hostdata SET value = ?, details = ? WHERE name = ?", (temp_token, str(expiration_time), "dropbox token"))
        else:
            cur.execute("INSERT INTO hostdata VALUES (?,?,?,?)", ("dropbox token", temp_token, str(expiration_time), ""))
        con.commit()

        return temp_token, expiration_time



    async def cloud_upload_scrobble_backup(bot, ctx, app_id):
        if not dropbox_enabled:
            await ctx.send("Error: Dropbox module not installed. Not syncing scrobble databases.")
            return

        # ZIP ALL DATABASES
        con = sqlite3.connect(f'databases/botsettings.db')
        cur = con.cursor()
        app_list = [item[0] for item in cur.execute("SELECT details FROM botsettings WHERE name = ? AND value = ?", ("app id", app_id)).fetchall()]
        try:
            instance = app_list[0]
        except:
            instance = f"unknown{app_id}"

        # FETCH DROPBOX AUTH INFO

        client_id = os.getenv('dropbox_key')
        client_secret = os.getenv('dropbox_secret')
        refresh_token = os.getenv('dropbox_refresh_token')
        redirect_uri = "https://localhost"

        rootdir = f"{sys.path[0]}/databases"
        folder = f'backups_instance_{instance}'

        if client_id is None or client_secret is None or refresh_token is None:
            scrobblefeature_list = [item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("scrobbling functionality",)).fetchall()]
            if len(scrobblefeature_list) == 0 or scrobblefeature_list[0] != "on":
                pass
            else:
                await ctx.send(f"(No backup for scrobble databases made. You need to add dropbox cloud service to this application for that.)")
            return

        # CHECKING IF FILES ARE CORRUPTED

        all_files_good = True

        for filename in ['scrobbledata.db', 'scrobbledata_releasewise.db', "scrobbledata_trackwise.db", 'scrobblestats.db', 'scrobblemeta.db']:
            try:
                con = sqlite3.connect(f'databases/{filename}')
                cur = con.cursor()  
                table_list = [item[0] for item in cur.execute("SELECT name FROM sqlite_master WHERE type = ?", ("table",)).fetchall()]
                #print(table_list)
                try:
                    for table in table_list:
                        cursor = con.execute(f'SELECT * FROM [{table}]')
                        column_names = list(map(lambda x: x[0], cursor.description))
                        #print(column_names)
                        try:
                            item_list = [item[0] for item in cur.execute(f"SELECT * FROM [{table}] ORDER BY {column_names[0]} ASC LIMIT 1").fetchall()]
                            #print(item_list)
                        except Exception as e:
                            print(f"Error with {filename} table {table} query:", e)
                            #await ctx.send(f"Error with {filename} table {table} query: {e}")
                            all_files_good = False
                except Exception as e:
                    print(f"Error with {filename} table {table} structure:", e)
                    #await ctx.send(f"Error with {filename} table {table} structure: {e}")
                    all_files_good = False
            except Exception as e:
                print(f"Error with {filename}:", e)
                #await ctx.send(f"Error with {filename}: {e}")
                all_files_good = False

        if not all_files_good:
            prefix = os.getenv("prefix")
            await ctx.send(f"Cloud backup skipped. Corrupted file among scrobble databases found.\nUse `{prefix}troubleshoot` and delete troublesome databases. Then retrieve backup from cloud.")
            return

        # CONNECT TO DROPBOX

        await ctx.send("Starting backup for scrobble databases. Saving to cloud. ☁️")

        TOKEN, expiration_time = await Utils.get_temporary_dropbox_token(ctx, None)

        dbx = dropbox.Dropbox(TOKEN)

        # UPLOAD FILES

        for dn, dirs, files in os.walk(rootdir):
            subfolder = dn[len(rootdir):].strip(os.path.sep)
            listing = Utils.dropbox_list_folder(dbx, folder, subfolder)
            print('Descending into', subfolder, '...')

            # First do all the files.
            for name in files:
                if not (name.startswith('scrobble') and name.endswith('.db')):
                    continue

                fullname = os.path.join(dn, name)
                try:
                    if not isinstance(name, six.text_type):
                        name = name.decode('utf-8')
                    nname = unicodedata.normalize('NFC', name)
                except:
                    nname = name
                if name.startswith('.'):
                    print('Skipping dot file:', name)
                elif name.startswith('@') or name.endswith('~'):
                    print('Skipping temporary file:', name)
                elif name.endswith('.pyc') or name.endswith('.pyo'):
                    print('Skipping generated file:', name)
                elif nname in listing:
                    md = listing[nname]
                    mtime = os.path.getmtime(fullname)
                    mtime_dt = datetime(*time.gmtime(mtime)[:6])
                    size = os.path.getsize(fullname)
                    if (isinstance(md, dropbox.files.FileMetadata) and
                            mtime_dt == md.client_modified and size == md.size):
                        print(name, 'is already synced [stats match]')
                    else:
                        #print(name, 'exists with different stats, downloading')
                        #res = Utils.dropbox_download(dbx, folder, subfolder, name)
                        #with open(fullname) as f:
                        #    data = f.read()
                        #if res == data:
                        #    print(name, 'is already synced [content match]')
                        #else:
                        #    print(name, 'has changed since last sync')
                        await Utils.run_blocking(bot, Utils.dropbox_upload, dbx, fullname, folder, subfolder, name, overwrite=True)
                else:
                    await Utils.run_blocking(bot, Utils.dropbox_upload, dbx, fullname, folder, subfolder, name)

            # Then choose which subdirectories to traverse.
            keep = []
            for name in dirs:
                if name.startswith('.'):
                    print('Skipping dot directory:', name)
                elif name.startswith('@') or name.endswith('~'):
                    print('Skipping temporary directory:', name)
                elif name == '__pycache__':
                    print('Skipping generated directory:', name)
                elif yesno('Descend into %s' % name, True, args):
                    print('Keeping directory:', name)
                    keep.append(name)
                else:
                    print('OK, skipping directory:', name)
            dirs[:] = keep

        # CREATE TXT FILE WITH LATEST UPDATE DATE

        try:
            lasttime = Utils.last_scrobble_time_in_db()

            newdir = f"{sys.path[0]}/temp"
            with open(f"{newdir}/time.txt", "w") as file:
                file.write(f"{lasttime}")
            try:
                # UPLOAD TXT FILE

                for dn, dirs, files in os.walk(newdir):
                    subfolder = dn[len(newdir):].strip(os.path.sep)
                    listing = Utils.dropbox_list_folder(dbx, folder, subfolder)

                    for name in files:
                        if not name == f"time.txt":
                            continue

                        fullname = os.path.join(dn, name)
                        try:
                            if not isinstance(name, six.text_type):
                                name = name.decode('utf-8')
                            nname = unicodedata.normalize('NFC', name)
                        except:
                            nname = name
                        if name.startswith('.'):
                            print('Skipping dot file:', name)
                        elif name.startswith('@') or name.endswith('~'):
                            print('Skipping temporary file:', name)
                        elif name.endswith('.pyc') or name.endswith('.pyo'):
                            print('Skipping generated file:', name)
                        elif nname in listing:
                            md = listing[nname]
                            mtime = os.path.getmtime(fullname)
                            mtime_dt = datetime(*time.gmtime(mtime)[:6])
                            size = os.path.getsize(fullname)
                            if (isinstance(md, dropbox.files.FileMetadata) and
                                    mtime_dt == md.client_modified and size == md.size):
                                print(name, 'is already synced [stats match]')
                            else:
                                await Utils.run_blocking(bot, Utils.dropbox_upload, dbx, fullname, folder, subfolder, name, overwrite=True)
                        else:
                            await Utils.run_blocking(bot, Utils.dropbox_upload, dbx, fullname, folder, subfolder, name)
            except Exception as e:
                print("Error while trying to save last time stamp in cloud:", e)

            os.remove(f"{newdir}/time.txt")
        except Exception as e:
            print("Error while trying to set last time stamp:", e)

        dbx.close()
        print("done")



    def check_active_scrobbleupdate(ctx):
        conC = sqlite3.connect('databases/cooldowns.db')
        curC = conC.cursor()
        cooldown_list = [[item[0],item[1],item[2]] for item in curC.execute("SELECT userid, username, time_stamp FROM scrobbleupdate").fetchall()]

        if ctx is None:
            return cooldown_list
            
        else:
            filtered_cooldown_list = []
            guild_member_ids       = [str(x.id) for x in ctx.guild.members]

            for item in cooldown_list:
                userid = str(item[0]).strip()
                username = item[1]
                time_stamp = item[2]

                if (userid in guild_member_ids) or (Utils.represents_integer(userid) == False):
                    filtered_cooldown_list.append(item)
                else:
                    filtered_cooldown_list.append([userid, "<user>", time_stamp])

            return filtered_cooldown_list



    def block_scrobbleupdate(ctx):
        now = int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds())

        if ctx is None:
            userid = "bot"
            username = "auto-update"
        elif type(ctx) == str:
            userid = "mod"
            username = str(ctx)
        else:
            userid = ctx.author.id
            username = ctx.author.name

        conC = sqlite3.connect('databases/cooldowns.db')
        curC = conC.cursor()
        curC.execute("INSERT INTO scrobbleupdate VALUES (?, ?, ?)", (str(userid), str(username), str(now)))
        conC.commit()



    def unblock_scrobbleupdate():
        conC = sqlite3.connect('databases/cooldowns.db')
        curC = conC.cursor()
        curC.execute("DELETE FROM scrobbleupdate")
        conC.commit()



    async def cloud_download_scrobble_backup(ctx, called_from):
        """gets the latest scrobble databases"""

        cooldown_list = Utils.check_active_scrobbleupdate(ctx)
        if len(cooldown_list) > 0:
            user_string = ""
            for item in cooldown_list:
                userid = item[0]
                username = item[1]
                time_stamp = item[2]

                if Utils.represents_integer(userid):
                    # user update
                    user_string += f"{username} <@{userid}> <t:{time_stamp}:R> "
                else:
                    # bot's auto-update
                    user_string += f"bot's auto-update <t:{time_stamp}:R> "

            await ctx.send(f"Scrobbling database is being updated at the moment. Will not fetch data from cloud.\nUpdated by: {user_string}"[:2000])
            return

        Utils.block_scrobbleupdate("cloud download")

        try:
            local_lasttime = Utils.last_scrobble_time_in_db()
        except Exception as e:
            await ctx.send(f"Error while trying to read out local scrobble databases: {e}")
            Utils.unblock_scrobbleupdate()
            return

        lateststatus_dict = {
                "local": local_lasttime,
        }

        # CHECKING UPDATE TIMES

        try:
            print("connecting to dropbox...")
            TOKEN, expiration_time = await Utils.get_temporary_dropbox_token(ctx, None)

            dbx = dropbox.Dropbox(TOKEN)

            con = sqlite3.connect(f'databases/botsettings.db')
            cur = con.cursor()
            instances = [item[0] for item in cur.execute("SELECT details FROM botsettings WHERE name = ?", ("app id",)).fetchall()]

            subfolder = f"{sys.path[0]}/temp"
            names = ["scrobbledata.db", "scrobbledata_releasewise.db",  "scrobbledata_trackwise.db", "scrobblestats.db", "scrobblemeta.db"]
            filepathes = {}

            for instance in instances:
                folder = f'backups_instance_{instance}'
                try:
                    try:
                        files = dbx.files_list_folder(f"/{folder}/").entries
                        print(f"Fetching metadata from folder of instance {instance}.")
                    except Exception as e:
                        print(f"Did not find folder of instance {instance}:", e)
                        continue 

                    for file in files:
                        if file.name == "time.txt":
                            try:
                                # clean up temp folder
                                os.remove(f"{subfolder}/time_{instance}.txt")
                            except:
                                pass
                            try:
                                # download timestamp file
                                dbx.files_download_to_file(f"{subfolder}/time_{instance}.txt", file.path_display)
                                f = open(f"{subfolder}/time_{instance}.txt", "r")

                                # read out time
                                try:
                                    utc_time = str(f.read()).strip()
                                    lateststatus_dict[f"instance_{instance}"] = int(utc_time)
                                except Exception as e:
                                    print(f"Error while trying to read time_{instance}.txt", e)

                                # remove timestamp file
                                os.remove(f"{subfolder}/time_{instance}.txt")
                            except Exception as e:
                                print(f"Error while checking time_{instance}.txt", e)
                        else:
                            if file.name in names:
                                filepathes[file.name] = file.path_display
                except Exception as e:
                    print('Error getting list of files from Dropbox:', e)

            print("Saves and last time updated:", lateststatus_dict)

            if len(lateststatus_dict) <= 1:
                await ctx.send(f"Could not find any valid cloud backups to draw from.")
                Utils.unblock_scrobbleupdate()
                return

            # GETTING STORAGE PLACE OF NEWEST VERSION

            overall_lasttime = local_lasttime
            device = "local"

            for k, v in lateststatus_dict.items():
                if v > overall_lasttime:
                    device = k
                    overall_lasttime = v

            if device == "local":
                await ctx.send("Already latest version stored locally.")
                Utils.unblock_scrobbleupdate()
                return

            # DOWNLOADING LATEST VERSION

            for filename in names: # move local files
                try:
                    os.replace(f"{sys.path[0]}/databases/{filename}", f"{sys.path[0]}/temp/{filename}.bak")
                except Exception as e:
                    print(f"Error while trying to move {filename}", e)
                    await ctx.send("Error while trying to move local files:", e)
                    Utils.unblock_scrobbleupdate()
                    return

            print("downloading files...")

            try: # download new files
                for filename in names:
                    print(f"...downloading {filename}")
                    dbx.files_download_to_file(f"databases/{filename}", filepathes[filename])
                    try:
                        con = sqlite3.connect(f'databases/{filename}')
                        cur = con.cursor()  
                        table_list = [item[0] for item in cur.execute("SELECT name FROM sqlite_master WHERE type = ?", ("table",)).fetchall()]
                        try:
                            for table in table_list:
                                cursor = con.execute(f'SELECT * FROM [{table}]')
                                column_names = list(map(lambda x: x[0], cursor.description))
                                try:
                                    item_list = [item[0] for item in cur.execute(f"SELECT * FROM [{table}] ORDER BY {column_names[0]} ASC LIMIT 1").fetchall()]
                                except Exception as e:
                                    print(f"Error with {filename} table {table} query:", e)
                                    raise ValueError(f"{filename} file check : query error - {e}")
                        except Exception as e:
                            print(f"Error with {filename} table {table} structure:", e)
                            raise ValueError(f"{filename} file check : structure error - {e}")
                    except Exception as e:
                        print(f"Error with {filename}:", e)
                        raise ValueError(f"{filename} file check : general error - {e}")
            except Exception as e_dl:
                print("-----------------------------")
                print("SEVERE ERROR")
                print("-----------------------------")
                print("reverse changes...")
                # if download fails reverse things
                for filename in names:
                    try:
                        os.remove(f"{subfolder}/{filename}")
                    except:
                        pass
                    try:
                        os.replace(f"{sys.path[0]}/temp/{filename}.bak", f"{sys.path[0]}/databases/{filename}")
                    except Exception as e:
                        print(f"Error while trying to put {filename} back", e)
                        emoji = Utils.emoji("panic")
                        await ctx.send(f"SEVERE ERROR: Scrobble databases might got damaged. {emoji}\nLet host manually replace scrobble databases and disable scrobbling functionality in the mean time.")
                        #Utils.unblock_scrobbleupdate()
                        return

                await ctx.send(f"Error while trying to download backup files: {e_dl}")
                Utils.unblock_scrobbleupdate()
                return

            print("removing temporaries...")

            # success: delete old files in temp folder
            for filename in names:
                try:
                    os.remove(f"{sys.path[0]}/temp/{filename}.bak")
                except:
                    pass

            print("done!")
            await ctx.send(f"Successfully updated scrobbledatabases!\nLast scrobble time in DB: <t:{overall_lasttime}:f>")
            Utils.unblock_scrobbleupdate()

        except Exception as e:
            Utils.unblock_scrobbleupdate()
            await ctx.send(f"Error: {e}")
