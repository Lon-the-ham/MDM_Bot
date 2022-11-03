import discord
import asyncio
from datetime import date
import config.config as config

discord_secret = config.discord_secret
discord_token = config.discord_token

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

asyncio.run(send_msg(f'Reminder! <@193001294548566016> <:smug:955227749415550996>', d_client))
print('---')