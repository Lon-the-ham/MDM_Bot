import discord
import asyncio
from datetime import date
from datetime import datetime
from datetime import timedelta
import pytz
import config.config as config

discord_secret = config.discord_secret
discord_token = config.discord_token



supported_timezones = [["UTC", 'universal']]
supported_timezones += [["CET", 'Europe/Berlin'], ["GMT", '']]
supported_timezones += [["AST",], ["EST", "US/Eastern"], ["CST",""], ["MST",""],["PST", "US/Pacific"]]
supported_timezones += [["JST", 'Asia/Tokyo']]


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
    else:
        posting_timezone = "UTC"
    if len(time_settings) == 1:
        clocktime = time_settings[0]
        if ":" in clocktime:
            hour_str = clocktime.split(":",1)[0]
            minute_str = clocktime.split(":",1)[1]
            try:
                hour = int(hour_str)
            except:
                hour = 21
                validity = False
                print("hour argument invalid")
            try:
                minute = int(minute_str)
            except:
                minute = 0
                validity = False
                print("minute argument invalid")

            if hour < 0 or hour > 23:
                validity = False
                print("hour argument out of scope")
            if minute < 0 or minute > 59:
                validity = False
                print("minute argument out of scope")
        else:
            validity = False
            print("no colon in clock argument")
    else:
        validity = False
        print("remaining args too many")

    if validity == False:
        hour = 21
        minute = 0 
        posting_timezone = "UTC"
        posting_weekday = "wednesday"
        print("due to invalid time setting argument, set to default wednesday 21:00 utc")

    return posting_weekday, posting_timezone, hour, minute


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


def check_time():
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
            if parameter in ['reminder mdm']:
                print(f"found reminder mdm setting; the value: {value}")
                break
    else:
        print(f'could not find REMINDER MDM setting')
        # setting a default
        value = "wednesday 21:00 CET"

    if value.lower() in ["off", "deactivated"]:
        print("mdm release reminder is off")
    else:
        print("mdm release reminder is on")
        time_settings = value.lower().split()
        
        # check entries:
        s_weekday, s_timezone, s_hour, s_minute = time_entry_convert(time_settings)


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

        if s_timezone == "UTC":

            d = date(2011, 7, 2)
            next_monday = next_weekday(d, 0) # 0 = Monday, 1=Tuesday, 2=Wednesday...
            print(next_monday)
            set_datetime = datetime(int(year_now), int(month_now), int(day_now), int(hour), int(minute), 0, tzinfo = pytz.utc)
            print(set_datetime)

            my_datetime_cst = set_datetime.astimezone(pytz.timezone('US/Central')).strftime('%Y-%m-%d %H:%M:%S %Z%z')
            print(my_datetime_cst)



async def send_msg(string, d_client):
	await d_client.login(discord_token)
	channel = await d_client.fetch_channel(416384984597790750)
	await channel.send(string)
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
	embed=discord.Embed(title="Metal Archives list", url=MA_url, description="It's Wednesday my dude. 🐸 Time for some new releases!", color=0xFF5733)
	embed.set_thumbnail(url="https://i.imgur.com/NS5cFH6.png")
	await channel.send(embed=embed)
	print('sent embed')

d_client = discord.Client(intents = discord.Intents.all())




#check_time()
asyncio.run(send_msg(f'Reminder! <@193001294548566016> <:smug:955227749415550996>', d_client))
print('---')
