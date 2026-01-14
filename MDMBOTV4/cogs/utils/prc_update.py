import asyncio
import discord
import sqlite3

from dotenv import load_dotenv
from cogs.utils.utl_discord import DiscordUtils as utl_d
from cogs.utils.utl_general import GeneralUtils as utl_g
from cogs.utils.utl_simple  import SimpleUtils  as utl_s


class BotUpdate():

    def update_bot():
        pass # TODO: transfer from v3, get all important settings

        # host0:
        # dropbox token, encryption key, rym/ma/scrobbling import, time reboot, time update