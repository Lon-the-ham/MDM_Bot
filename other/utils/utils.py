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

class Utils():

    ############################################### COMMAND CHECKS

    def is_main_server(ctx):
        server = ctx.message.guild
        if server is None:
            raise commands.CheckFailure(f'Error: Command does not work in DMs.')
            return False
        else:
            con = sqlite3.connect(f'databases/botsettings.db')
            cur = con.cursor()
            main_servers = [item[0] for item in cur.execute("SELECT value FROM botsettings WHERE name = ?", ("main server id",)).fetchall()]
            guild_id = str(ctx.guild.id)
            if guild_id in main_servers:
                return True
            else:
                try:
                    mainserver = [item[0] for item in cur.execute("SELECT details FROM botsettings WHERE name = ?", ("main server id",)).fetchall()][0]
                    if mainserver.strip() == "":
                        mainserver = "*main server*"
                except:
                    mainserver = "main server"
                raise commands.CheckFailure(f'Error: This is a {mainserver} specific command.')
                return False


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


    def is_active(*ctx):
        conA = sqlite3.connect(f'databases/activity.db')
        curA = conA.cursor()
        activity_list = [item[0] for item in curA.execute("SELECT value FROM activity WHERE name = ?", ("activity",)).fetchall()]
        
        if len(activity_list) != 1:
            raise commands.CheckFailure("inactive")
            return False
        else:
            activity = activity_list[0]
            if activity == "active":
                return True
            else:
                raise commands.CheckFailure("inactive")
                return False



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
                print("Error in util.adapt_link():", e)
                try: #2) ?
                    error = int("error")  # just a place holder for potential next function
                except Exception as e:
                    #print("Error in util.adapt_link():", e)
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
            print("Issue with provided link: util.adapt_time() could not parse time")
            raise ValueError("Issue with provided link: util.adapt_time() could not parse time")




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



    def confirmation_check(ctx, message): # checking if it's the same user and channel
            return ((message.author == ctx.author) and (message.channel == ctx.channel))



    def cleantext(s):
        ctxt = str(s).replace("`","'").replace('"',"'").replace("´","'").replace("‘","'").replace("’","'").replace("“","'").replace("”","'")
        return ctxt



    def cleantext2(s):
        ctxt = Utils.cleantext(str(s))
        ctxt2 = ctxt.replace("*","\*").replace("_","\_").replace("#","\#").replace("\n> ","\n\> ")
        return ctxt2



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

            if emote == "":                
                print(f"Notice: Emoji with name '{name}' returned an empty string.")

            return emote

        except Exception as e:
            print("Error:", e)
            return ""



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



    def forceinteger(s):
        try:
            i = int(s.strip())
        except:
            i = 0
        return i



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

        if len(s) < 4:
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

        if len(from_timestamp) == 0:

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
                print(f"Error in util.bot_spam_send() ({title}):", e)
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
                    curC.execute("DELETE FROM userrequests WHERE LOWER(service) = ? AND userid = ? AND time_stamp = ?", (service.lower(), str(ctx.message.author.id), str(invoketime)))
                    conC.commit()
                    raise ValueError(f"rate limited")
                    return

                # all good
                break

            else:
                # soft type cooldown: delay

                if long_counter >= long_limit_amount or short_counter > 0:
                    async with ctx.typing():
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
        curC.execute("DELETE FROM userrequests WHERE cast(time_stamp as integer) < ?", (invoketime - 3600,))
        curC.execute("DELETE FROM userrequests WHERE LOWER(service) = ? AND userid = ? AND time_stamp = ?", (service.lower(), str(ctx.message.author.id), str(invoketime)))
        conC.commit()
        conC.close()
        await Utils.changetimeupdate()



    async def cooldown_exception(ctx, exception, service):
        print(exception)
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



    async def embed_pages(ctx, bot, header, description_list, color, footer):
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
        embed.set_footer(text=f"Page {cur_page}/{pages}{smalltext}")
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
            raise ValueError(f"Error in util.fetch_id_from_args: search scope not found")
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
            else:
                rest_list.append(arg_clean)

        if not other_user_mentioned:
            member = ctx.message.author
            try:
                color = member.color
            except:
                color = 0xffffff

        return member, color, rest_list



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



    async def get_all_integers(args):
        indices = []
        for arg in args:
            try:
                x = int(arg)
                indices.append(x)
            except:
                pass

        return indices



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



    async def get_reference_role(ctx):
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
                raise ValueError(f'Error: Could not find reference role. Application needs renewed setup.')
                return

        return reference_role



    async def lastfm_get(ctx, payload, cooldown):
        if cooldown:
            try: 
                await Utils.cooldown(ctx, "lastfm")
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

        response = requests.get(url, headers=headers, params=payload)
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

        message = f"Successfully updated {counter} entries in exchangerate database via web scrape."
        success = True
        print(f"Successfully updated {counter} entries in exchangerate database via web scrape.")
        return message, success



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


