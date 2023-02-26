import discord
import asyncio
import config.config as config
from datetime import datetime

discord_secret = config.discord_secret
discord_token = config.discord_token

#discord_secret = config.discord_secret
#discord_token = config.discord_token

async def sendit(string, d_client):
    await d_client.login(discord_token)
    channel = await d_client.fetch_channel(416384984597790750)
    await channel.send(string)

    #timenow = datetime.now()
    #year_now = timenow.strftime("%Y")
    #month_now = timenow.strftime("%m")
    #day_now = timenow.strftime("%d")
    #hour_now = timenow.strftime("%-H")
    #minute_now = timenow.strftime("%-M")
    #second_now = timenow.strftime("%-S")
    #timestring = f"{year_now}.{month_now}.{day_now}, {hour_now}:{minute_now}:{second_now} CET"

    utc_time_stamp = int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds())
    timestring = f"<t:{utc_time_stamp}:F>"

    try:
        # this should work when the script is started from the shell
        my_files = [
                        discord.File('cogs/backlog/memobacklog.db'),
                        discord.File('cogs/pingterest/pingterest.db'),
                        discord.File('cogs/settings/default_settings.txt'),
                    ]
        await channel.send(f"Backup of mdm bot data\n{timestring}", files=my_files)
    except:
        try:
            # this should work when it is directly started
            my_files = [
                            discord.File('../cogs/backlog/memobacklog.db'),
                            discord.File('../cogs/pingterest/pingterest.db'),
                            discord.File('../cogs/settings/default_settings.txt'),
                        ]
            await channel.send(f"Backup of mdm bot data\n{timestring}", files=my_files)
        except Exception as e:
            await channel.send(f"Error while trying to send backup data.```{e}```")

d_client = discord.Client(intents = discord.Intents.all())

asyncio.run(sendit("`--rebooting.`", d_client))