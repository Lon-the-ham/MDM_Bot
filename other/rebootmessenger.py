import discord
import asyncio
import config.config as config

discord_secret = config.discord_secret
discord_token = config.discord_token

#discord_secret = config.discord_secret
#discord_token = config.discord_token

async def sendit(string, d_client):
	await d_client.login(discord_token)
	channel = await d_client.fetch_channel(416384984597790750)
	await channel.send(string)

d_client = discord.Client(intents = discord.Intents.all())

asyncio.run(sendit("`--rebooting.`", d_client))