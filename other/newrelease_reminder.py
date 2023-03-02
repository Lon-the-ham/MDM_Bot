import discord
import asyncio
from datetime import date
from datetime import datetime
from datetime import timedelta
import pytz
from pytz import timezone
import config.config as config
import time   
import re
import sqlite3

discord_secret = config.discord_secret
discord_token = config.discord_token


m = 15 # number of minutes that script will be started
goodwill = 2 # number of hours willing to retry if smth went wrong



# warning this list is duplicated in cogs/settings.py
supported_timezones = [["UTC", 'UTC']]
supported_timezones += [["CET", 'Europe/Berlin'], ["GMT", 'Europe/London'], ["EET", 'Europe/Athens']]
supported_timezones += [["AKST", 'America/Anchorage'], ["EST", "America/New_York"], ["CST","America/Chicago"], ["MST","America/Denver"],["PST", "America/Los_Angeles"]]
supported_timezones += [["JST", 'Asia/Tokyo'], ["IST", 'Asia/Kolkata'], ["HKT", 'Asia/Hongkong']]
supported_timezones += [["AEST",'Australia/Sydney'], ["ACST","Australia/Adelaide"],["AWST","Australia/Perth"]]





def convert_datetime_timezone(dt, tz1, tz2):
    tz1 = pytz.timezone(tz1)
    tz2 = pytz.timezone(tz2)

    dt = datetime.strptime(dt,"%Y-%m-%d %H:%M:%S")
    dt = tz1.localize(dt)
    dt = dt.astimezone(tz2)
    dt = dt.strftime("%Y-%m-%d %H:%M:%S")

    return dt


def next_weekday(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead < 0: # Target day already in the past this week
        days_ahead += 7
    return d + timedelta(days_ahead)


def time_entry_convert(time_settings):
    validity = True
    if len(time_settings) > 3:
        validity = False
        print("too many arguments")
    if len(time_settings) < 2:
        validity = False
        print("too few arguments")
    for weekday in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "mon", "tue", "wed", "thu", "fri", "sat", "sun"]:
        if weekday in time_settings:
            posting_weekday = weekday
            time_settings.remove(weekday)
            break
    else:
        validity = False
        print("no week day specified")
    for TZitem in supported_timezones:
        tz = TZitem[0].lower()
        if tz in time_settings:
            posting_timezone = tz.upper()
            time_settings.remove(tz)
            break
    else:
        posting_timezone = "UTC"
    if len(time_settings) == 1:
        clocktime = time_settings[0]
        if ":" in clocktime:
            hour = clocktime.split(":",1)[0]
            minute = clocktime.split(":",1)[1]

            if len(hour) == 2 and len(minute) == 2:
                ten = ["0","1","2","3","4","5","6","7","8","9"]
                six = ["0","1","2","3","4","5"]
                if hour[0] in six and hour[1] in ten and minute[0] in six and minute[1]in ten:
                    posting_clock = clocktime
                else:
                    print("illegal clock time")
            else:
                validity = False
                print("clock argument format wrong")
        else:
            validity = False
            print("no colon in clock argument")
    else:
        validity = False
        print("remaining args too many")

    if validity == False:
        posting_clock = "21:00"
        posting_timezone = "UTC"
        posting_weekday = "wednesday"
        print("due to invalid time setting argument, set to default wednesday 21:00 utc")

    return posting_weekday, posting_timezone, posting_clock


def weekday_to_int(weekday):
    if weekday.lower() in ["mon", "monday"]:
        return 0 
    elif weekday.lower() in ["tue", "tuesday"]:
        return 1
    elif weekday.lower() in ["wed", "wednesday"]:
        return 2 
    elif weekday.lower() in ["thu", "thursday"]:
        return 3
    elif weekday.lower() in ["fri", "friday"]:
        return 4 
    elif weekday.lower() in ["sat", "saturday"]:
        return 5
    elif weekday.lower() in ["sun", "sunday"]:
        return 6 
    else:
        return "error"


def int_to_weekday(num):
    if num in [0,"0"]:
        return "Monday"
    elif num in [1,"1"]:
        return "Tuesday"
    elif num in [2,"2"]:
        return "Wednesday"
    elif num in [3,"3"]:
        return "Thursday"
    elif num in [4,"4"]:
        return "Friday"
    elif num in [5,"5"]:
        return "Saturday"
    elif num in [6,"6"]:
        return "Sunday"
    else:
        return "ERROR"


def check_time(ReminderName):
	# first, get settings
    settings = []
    print('+++ settings: +++')
    with open('../cogs/settings/default_settings.txt', 'r') as s:
        for line in s:
            print(line.strip())
            settings.append(line.strip())
    print('--- ---')

    for s in settings:
        if ":" in s:
            parameter = s.split(":",1)[0].strip().lower()
            value = s.split(":",1)[1].strip()

            ### PARAMETER REMINDER MDM
            if parameter in [ReminderName]:
                print(f"found {ReminderName} setting; the value: {value}")
                break
    else:
        print(f'could not find REMINDER setting')
        # setting a default
        value = "wednesday 21:00 CET"

    if value.lower() in ["off", "deactivated"]:
        print("mdm release reminder is off")
    else:
        print("mdm release reminder is on")
        time_settings = value.lower().split()

        print("vvvvvvvvvvvvvvvvvv")
        
        # convert settings string
        s_weekday, s_timezone, s_clock = time_entry_convert(time_settings)

        timenow = datetime.now()
        year_now = timenow.strftime("%Y")
        month_now = timenow.strftime("%m")
        day_now = timenow.strftime("%d")
        weekday_now = timenow.strftime("%A").lower()
        weekday_abbr_now = timenow.strftime("%a").lower()
        print(f"{year_now}-{month_now}-{day_now}, {weekday_now}")

        hour_now = timenow.strftime("%-H")
        minute_now = timenow.strftime("%-M")
        second_now = timenow.strftime("%-S")

        print(s_weekday, s_timezone, s_clock)
        s_int_weekday = weekday_to_int(s_weekday)
        print(f"target weekday as integer: {s_int_weekday}")

        for timezone in supported_timezones:
            if timezone[0] == s_timezone:

                # current day
                today_utc_string = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                print(f"today_utc_string: {today_utc_string}")
                today_itz = convert_datetime_timezone(today_utc_string, "UTC", timezone[1])
                print(f"today_itz: {today_itz}")
                r = re.split(', | |-|:', today_itz)
                #weekday_itz = datetime(int(r[0]),int(r[1]),int(r[2]),int(r[3]),int(r[4]),int(r[5]), 0).weekday()
                #print(f"weekday in timezone: {weekday_itz}")
                try:
                    weekday_for_db = int_to_weekday(s_int_weekday)
                except:
                    weekday_for_db = "time"

                # initialize target date, if not specified day remove 24 hours etc
                targethour = int(s_clock[:2]) 
                targetminute = int(s_clock[3:])
                targetclock_today = pytz.timezone(timezone[1]).localize(datetime(int(r[0]),int(r[1]),int(r[2]),targethour,targetminute,0,0))

                print(targetclock_today)
                print(targetclock_today.weekday())

                dayshift = s_int_weekday - targetclock_today.weekday()
                print(dayshift)

                targettime = targetclock_today + timedelta(days = dayshift)
                print(f'target time: {targettime}')
                print(targettime.astimezone(pytz.utc))

                utcnow = pytz.timezone("UTC").localize(datetime.utcnow())
                print(utcnow)
                target_difference = targettime - utcnow
                seconds_to_target = target_difference.total_seconds()
                print(seconds_to_target)

                if seconds_to_target <= 0 and seconds_to_target > (-goodwill * 60 * 60):
                    con = sqlite3.connect('dblogs/reminders.db')
                    cur = con.cursor()
                    cur.execute('''CREATE TABLE IF NOT EXISTS reminded (reminder_name text, utc_time text, human_time text, week_day text, msg_sent text)''')

                    now = int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds())

                    last_times_reminded = [item[0] for item in cur.execute("SELECT utc_time FROM reminded WHERE reminder_name = ?", (ReminderName,)).fetchall()]

                    last_reminder_old_enough = True
                    for times in last_times_reminded:
                        if int(times) > now - goodwill*60*60:
                            last_reminder_old_enough = False
                            break

                    if last_reminder_old_enough:
                        print(f"initialized reminder for {ReminderName}!")
                        cur.execute("INSERT INTO reminded VALUES (?, ?, ?, ?, ?)", (ReminderName, str(now), str(today_utc_string), str(weekday_for_db), "False"))
                        con.commit()
                    else:
                        print("already reminded, no action required")
                else:
                    print("not the right time to remind")
                break
        else:
            print("specified timezone not supported")
        



async def send_msg(d_client):
    con = sqlite3.connect('dblogs/reminders.db')
    cur = con.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS reminded (reminder_name text, utc_time text, human_time text, week_day text, msg_sent text)''')

    to_be_reminded = [[item[0],item[1],item[2]] for item in cur.execute("SELECT reminder_name, utc_time, week_day FROM reminded WHERE msg_sent = ?", ("False",)).fetchall()]

    await d_client.login(discord_token)
    channel = await d_client.fetch_channel(416384984597790750)


    for r in to_be_reminded:
        now = int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds())
        remindertime = int(r[1])
        if remindertime < now - 1*24*60*60:
            print(f"reminder {r[0]} for {r[1]} is already 1 day old and will not be sent")
        else:
            if r[0] == "reminder_mdm":

                await channel.send(f'Reminder! <@193001294548566016> <:smug:955227749415550996>')
                #await channel.send(f'Reminder! @ EW\nTHIS IS JUST A TEST HENCE NO PING')
                print('sent ping')
                year_now = date.today().year
                month_now = date.today().month
                day_now = date.today().day

                year_to = str(year_now)
                month_to = str(month_now)
                if len(month_to) <= 1:
                    month_to = '0' + month_to
                if day_now <= 6:
                    if month_now > 1:
                        month_from = str(month_now-1)
                        year_from = year_to
                    else:
                        month_from = '12'
                        year_from = str(year_now-1)
                else:
                    month_from = month_to
                    year_from = year_to
                if len(month_from) <= 1:
                    month_from = '0' + month_from

                MA_url = "https://www.metal-archives.com/search/advanced/searching/albums?bandName=&releaseTitle=&releaseYearFrom=" + year_from + "&releaseMonthFrom=" + month_from + "&releaseYearTo=" + year_to + "&releaseMonthTo=" + month_to + "&country=&location=&releaseLabelName=&releaseCatalogNumber=&releaseIdentifiers=&releaseRecordingInfo=&releaseDescription=&releaseNotes=&genre=Melodic+death+metal&releaseType%5B%5D=1&releaseType%5B%5D=5#albums"
                #MA_url = "https://www.metal-archives.com/search/advanced/searching/albums?bandName=&releaseTitle=&releaseYearFrom=%s&releaseMonthFrom=%s&releaseYearTo=%s&releaseMonthTo=%s&country=&location=&releaseLabelName=&releaseCatalogNumber=&releaseIdentifiers=&releaseRecordingInfo=&releaseDescription=&releaseNotes=&genre=Melodic+death+metal&releaseType%5B%5D=1&releaseType%5B%5D=5#albums" % (year_from, month_from, year_to, month_to)
                embed=discord.Embed(title="Metal Archives list", url=MA_url, description=f"It's {r[2]} my dude. 🐸 Time for some new releases!", color=0xFF5733)
                embed.set_thumbnail(url="https://i.imgur.com/NS5cFH6.png")
                await channel.send(embed=embed)
                print('sent embed')

                cur.execute("UPDATE reminded SET msg_sent = ? WHERE reminder_name = ? AND utc_time = ?", ("True", r[0], r[1]))
                con.commit()

            elif r[0] == "reminder_i&w":

                await channel.send("Reminder! <@289925809878335489> <:lurkingchick:1017443155743887511>")
                #await channel.send(f'Reminder! @ Ayla\nTHIS IS JUST A TEST HENCE NO PING')
                print('sent ping')

                embed=discord.Embed(title="Images & Words", url = "https://discord.com/channels/400572085300101120/419947972629889045", description=f"Oh shit, it's {r[2]} <:surprisedspacefrog:1014204462514065428> Time for some new prog releases!", color=0xFF5733)
                embed.set_thumbnail(url="https://i.imgur.com/inTAcPD.gif")
                await channel.send(embed=embed)
                print('sent embed')

                cur.execute("UPDATE reminded SET msg_sent = ? WHERE reminder_name = ? AND utc_time = ?", ("True", r[0], r[1]))
                con.commit()

            else:
                print(f"some error ocurred, found unknown reminder {r[0]} for {r[1]}")

    await d_client.close()


d_client = discord.Client(intents = discord.Intents.all())



print('---')
check_time("reminder_mdm")
print('---')
check_time("reminder_i&w")
print('---')
asyncio.run(send_msg(d_client))
print('-----------')
