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
            "cogs.admin.backup",
            "cogs.backlog.memo",
            "cogs.pingterest.pingterest",
            "cogs.reactionevents.reactionevents",
            "cogs.reactionevents.otherevents",
            "cogs.roles.roles",
            "cogs.roles.reactionroles",
            "cogs.settings.settings",
            "cogs.utility.exchanges",
            "cogs.utility.utility",
            "cogs.utility.shenanigans",
            "cogs.webinfo.webinfo"
        ]

    async def setup_hook(self):
        for ext in self.initial_extensions:
            await self.load_extension(ext)

        await bot.tree.sync(guild = discord.Object(id = 413011798552477716))

    async def on_ready(self):
        print('logged in as {0.user}'.format(bot))

        try:
            channel = bot.get_channel(416384984597790750)
            await channel.send(f'`I haveth logged in` <:smug:955227749415550996>')





            # set default settings !
            try:
                settings = []
                print('+++ settings: +++')
                with open('cogs/settings/default_settings.txt', 'r') as s:
                    for line in s:
                        print(line.strip())
                        settings.append(line.strip())
                print('--- ---')

                i = 0
                for s in settings:
                    i += 1
                    if ":" in s:
                        parameter = s.split(":",1)[0].strip().lower()
                        value = s.split(":",1)[1].strip()

                        ### PARAMETER BOT STATUS
                        if parameter in ['status']:
                            if ' ' in value:
                                stat_type = value.split(" ",1)[0].lower().strip()
                                stat_name = value.split(" ",1)[1].strip()
                                if stat_type in ['p', 's', 'l', 'w', 'n']:
                                    if stat_type == 'p':
                                        await self.change_presence(activity=discord.Game(name=stat_name))
                                        print(f'set status PLAYING {stat_name}')
                                    elif stat_type == 's':
                                        my_twitch_url = "https://www.twitch.tv/mdmbot/home"
                                        await self.change_presence(activity=discord.Streaming(name=stat_name, url=my_twitch_url))
                                        print(f'set status STREAMING {stat_name}')
                                    elif stat_type == 'l':
                                        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=stat_name))
                                        print(f'set status LISTENING TO {stat_name}')
                                    elif stat_type == 'w':
                                        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=stat_name))
                                        print(f'set status WATCHING {stat_name}')
                                    elif stat_type == 'n':
                                        await self.change_presence(activity=None)
                                        print('empty status')
                                else:
                                    print('first argument was not a valid status type, setting status type WATCHING')
                                    await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=value))
                            elif value in ['', 'n', 'N']:
                                await self.change_presence(activity=None)
                                print('no status set')
                            else:
                                print('>> could not determine status type -.-')
                                await self.change_presence(activity=None)

                        ### 
                    else:
                        print(f'cannot parse parameter and value from line {i}.: {s}')
            except Exception as e:
                print(e)
                await channel.send(f'Error in loading default settings <:nervous:975219600272801802>')
        
        except:
            print("error in executing on_ready")


bot = YataBot()
bot.run(discord_token)