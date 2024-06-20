# SANDBOX COG FOR CUSTOM STUFF

import asyncio
from bs4 import BeautifulSoup
import datetime
import discord
from discord.ext import commands
from emoji import UNICODE_EMOJI
import json
import math
import os
from other.utils.utils import Utils as util
import pytz
import random
import re
import requests
import sqlite3
import sys
import traceback


class SandBox(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.prefix = os.getenv("prefix")


    @commands.command(name='sandbox')
    @commands.check(util.is_active)
    async def _sandbox_test(self, ctx):
        """help text
        """    
        await ctx.send(f'Sandbox was loaded!')
        
    @_sandbox_test.error
    async def sandbox_test_error(self, ctx, error):
        await util.error_handling(ctx, error)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(
        SandBox(bot),
        guilds = [discord.Object(id = int(os.getenv("guild_id")))])