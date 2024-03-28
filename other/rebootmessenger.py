

import discord
import asyncio
import os
from os.path import dirname
import sys
import zipfile
from dotenv import load_dotenv
from datetime import datetime
import sqlite3


load_dotenv()
app_id = os.getenv("application_id")
bot_instance = os.getenv("bot_instance")
discord_token = os.getenv("discord_token")
prefix = os.getenv("prefix")
guild_id = int(os.getenv("guild_id"))
bot_channel_id = int(os.getenv("bot_channel_id"))


async def sendit(string, d_client):
    await d_client.login(discord_token)
    channel = await d_client.fetch_channel(bot_channel_id)
    await channel.send(string)

    utc_time_stamp = int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds())
    timestring = f"<t:{utc_time_stamp}:F>"

    try:

        # FETCH APP 

        try:
            con = sqlite3.connect(f'databases/botsettings.db')
        except:
            con = sqlite3.connect(f'../databases/botsettings.db')
        cur = con.cursor()
        app_list = [item[0] for item in cur.execute("SELECT details FROM botsettings WHERE name = ? AND value = ?", ("app id", app_id)).fetchall()]

        if len(app_list) == 0:
            print("error: no app with this id in database")
        else:
            instance = app_list[0]
            date = datetime.today().strftime('%Y-%m-%d_%H-%M-%S')

            # COPY FILES

            try:
                zf = zipfile.ZipFile(f"temp/backup_{date}_{instance}.zip", "w")
            except:
                zf = zipfile.ZipFile(f"../temp/backup_{date}_{instance}.zip", "w")
            db_directory = f"{dirname(sys.path[0])}/databases"

            lastedited = 0
            lastchanged = 0
            for filename in os.listdir(db_directory):
                zf.write(os.path.join(db_directory, filename), filename)

                edittime = int(os.path.getmtime(os.path.join(db_directory, filename)))
                if (edittime > lastedited) and ("activity.db" not in str(filename)):
                    lastedited = edittime
                if str(filename) == "aftermostchange.db":
                    try:
                        try:
                            conL = sqlite3.connect(f'databases/aftermostchange.db')
                        except:
                            conL = sqlite3.connect(f'../databases/aftermostchange.db')
                        curL = conL.cursor()
                        lastchange_list = [item[0] for item in curL.execute("SELECT value FROM lastchange WHERE name = ?", ("time",)).fetchall()]
                        lastchanged = int(lastchange_list[-1])
                    except Exception as e:
                        print(f"Error while trying to read out aftermostchange.db: {e}")
            zf.close()


            # CHECK ACTIVITY

            try:
                conA = sqlite3.connect(f'databases/activity.db')
            except:
                conA = sqlite3.connect(f'../databases/activity.db')
            curA = conA.cursor()
            activity_list = [item[0] for item in curA.execute("SELECT value FROM activity WHERE name = ?", ("activity",)).fetchall()]
            last_activity = activity_list[0]
            if last_activity == "active":
                textmessage = f"`LAST ACTIVE`\nlast edited: <t:{lastedited}:f> i.e. <t:{lastedited}:R>"
            else:
                textmessage = f"last edited: <t:{lastedited}:f> i.e. <t:{lastedited}:R>"
            if lastchanged > 0:
                textmessage += f"\nlast changed: <t:{lastchanged}:f> i.e. <t:{lastchanged}:R>"
            else:
                textmessage += f"\n(no last change date found)"


            # SEND STUFF

            try:
                try:
                    await channel.send(textmessage, file=discord.File(rf"temp/backup_{date}_{instance}.zip"))
                except:
                    try:
                        await channel.send(textmessage, file=discord.File(rf"../temp/backup_{date}_{instance}.zip"))
                    except:
                        await channel.send(textmessage, file=discord.File(rf"{dirname(sys.path[0])}/temp/backup_{date}_{instance}.zip"))
            except Exception as e:
                print(f"Error while trying to send backup file: {e}")
            try:
                os.remove(f"temp/backup_{date}_{instance}.zip")
            except:
                os.remove(f"../temp/backup_{date}_{instance}.zip")

    except Exception as e:
        await channel.send(f"Error while trying to send backup data.```{e}```")


# vvv 

d_client = discord.Client(intents = discord.Intents.all())

asyncio.run(sendit("`--rebooting.`", d_client))