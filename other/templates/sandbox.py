# SANDBOX COG FOR CUSTOM STUFF

import asyncio
from bs4 import BeautifulSoup
import datetime
import discord
from discord.ext import commands
from dotenv import load_dotenv
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


    @commands.command(name = 'sandbox', aliases = ['boxsand'])
    @commands.check(util.is_active)
    async def _sandbox_test(self, ctx):
        """help text
        """    
        await ctx.send(f'Sandbox was loaded!')
        
    @_sandbox_test.error
    async def sandbox_test_error(self, ctx, error):
        await util.error_handling(ctx, error)

    # new commands can go here:
    # make sure to change the 5 following things within angles <> for each function:
    # 1. name = <'sandbox'>
    # 2. aliases = <['boxsand']>
    # 3. async def <_sandbox_test>(self, ctx):
    # 4. @<_sandbox_test>.error
    # 5. async def <sandbox_test_error>(self, ctx, error):
    # 
    # (do not use an already existing command name. you can check this by using `-help name` within discord. if the response is "Don't think I got that command, chief!" then you're good to go)




# don't change this:
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(
        SandBox(bot),
        guilds = [discord.Object(id = int(os.getenv("guild_id")))])
