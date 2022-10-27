import os
import datetime
import asyncpraw
import discord
from discord.ext import commands
import asyncio
#import asyncprawcore
import re
import time
import random
import sqlite3
#import subprocess
from emoji import UNICODE_EMOJI
import functools
import itertools
import math
from async_timeout import timeout
import requests

import other.config.config as config

discord_secret = config.discord_secret
discord_token = config.discord_token


class YataBot(commands.Bot):

    def __init__(self):
        super().__init__(
            command_prefix = '-',
            intents = discord.Intents.all(),
            application_id = '958105284759400559')

        self.initial_extensions = [
            "cogs.admin.servermod",
            "cogs.utility.utility",
            "cogs.backlog.memo",
            "cogs.pingterest.pingterest",
            "cogs.roles.roles",
            "cogs.roles.reactionroles",
            "cogs.reactionevents.reactionevents"
        ]

    async def setup_hook(self):
        for ext in self.initial_extensions:
            await self.load_extension(ext)

        await bot.tree.sync(guild = discord.Object(id = 413011798552477716))

    async def on_ready(self):
        print('logged in as {0.user}'.format(bot))
        channel = bot.get_channel(416384984597790750)
        await channel.send(f'`I haveth logged in` <:smug:955227749415550996>')


bot = YataBot()
bot.run(discord_token)