import discord
from discord.ext import commands
import datetime
from other.utils.utils import Utils as util
import os
import asyncio
import requests
import json
from bs4 import BeautifulSoup


class Music_Scrobbling(commands.Cog):
    def __init__(self, bot: commands.bot) -> None:
        self.bot = bot







async def setup(bot: commands.bot) -> None:
    await bot.add_cog(
        Music_Scrobbling(bot),
        guilds = [discord.Object(id = int(os.getenv("guild_id")))])