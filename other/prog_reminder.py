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

	embed=discord.Embed(title="Images & Words", url = "https://discord.com/channels/400572085300101120/419947972629889045", description="Oh shit, it's Wednesday <:surprisedspacefrog:1014204462514065428> Time for some new prog releases!", color=0xFF5733)
	embed.set_thumbnail(url="https://i.imgur.com/inTAcPD.gif")
	await channel.send(embed=embed)
	print('sent embed')

d_client = discord.Client(intents = discord.Intents.all())

asyncio.run(send_msg(f'Reminder! <@289925809878335489> <:lurkingchick:1017443155743887511>', d_client))
print('---')

