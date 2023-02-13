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
#from emoji import UNICODE_EMOJI
import functools
import itertools
import math
from async_timeout import timeout
import requests
#
import emojis

import config.config as config

discord_secret = config.discord_secret
discord_token = config.discord_token


class AnatoolBot(commands.Bot):
    def __init__(self) -> None:
        #self.add_commands()
        
        #def __init__(self):
        super().__init__(
            command_prefix = '-',
            intents = discord.Intents.all(),
            application_id = '958105284759400559')


        async def is_valid_server(ctx):
            server = ctx.message.guild
            if server is None:
                #raise commands.CheckFailure(f'Command does not work in DMs.')
                return False
            else:
                valid_servers = [413011798552477716]
                guild_id = server.id
                #print(guild_id)
                if guild_id in valid_servers:
                    return True
                else:
                    #raise commands.CheckFailure(f'Command does only work on specific servers.')
                    return False

        async def has_manageperms(ctx):
            perms = ctx.message.author.guild_permissions
            user_perms_full = [p for p in perms]
            user_perms = []
            for p in user_perms_full:
                if p[1]:
                    user_perms.append(p[0])
            #print(user_perms)
            if "manage_guild" in user_perms:
                return True
            else:
                return False

        ###########################################
        ###               COMMANDS              ###
        ###########################################

        @self.command(name='testing')
        async def test_command(ctx):
            validserver = await is_valid_server(ctx)
            adminrights = await has_manageperms(ctx)
            if validserver and adminrights:
                await ctx.channel.send(f'I am ready!')
            else:
                await ctx.channel.send(f'An error ocurred.')


        @self.command(name='emojirank')
        async def test_command(ctx):
            validserver = await is_valid_server(ctx)
            adminrights = await has_manageperms(ctx)
            if validserver and adminrights:
                print(">>> emojirank")

                text_channel_list = []
                thread_list = []
                guild = ctx.message.guild 
                for channel in guild.text_channels:
                    text_channel_list.append(channel)
                    #print(f'> {channel.name}')
                    for thread in channel.threads:
                        thread_list.append(thread)
                        #print(f'>>> {thread.name}')

                public_channels = []
                restricted_channels = []
                for channel in text_channel_list:
                    roles = []
                    for role in channel.changed_roles:
                        roles.append(str(role.id))

                    if "1073291335097913435" in roles:
                        public_channels.append(channel)
                    else:
                        restricted_channels.append(channel)

                #print(f'+++ public channels +++')
                #for channel in public_channels:
                #    print(channel.name)
                #print("---")
                #print(f'+++ restricted channels +++')
                #for channel in restricted_channels:
                #    print(channel.name)
                emoji_found = {}
                reactions_found = {}
                default_emojis = emojis.db.get_emoji_aliases()
                print(default_emojis)

                for channel in public_channels:
                    print(f'+++ {channel.name} +++')
                    async for msg in channel.history(limit=100):
                        custom_emojis = re.findall(r'<a?:\w*:\d*>', msg.content)
                        #custom_emojis = [int(e.split(':')[1].replace('>', '')) for e in custom_emojis]
                        #custom_emojis = [discord.utils.get(client.get_all_emojis(), id=e) for e in custom_emojis]
                        print(f'{msg.author}: {custom_emojis}')


                    #for entry in user_bg_list:
                    #    emoji = 
                    #    if emoji in emoji_dict.keys():
                    #        prev = emoji_dict[emoji]
                    #        emoji_dict[emoji] = str(int(prev)+1)
                    #    else:
                    #        emoji_dict[emoji] = "1"
                

                    




                            


            


            else:
                await ctx.channel.send(f'An error ocurred.')



    ###########################################
    ###               ON READY              ###
    ###########################################                

    async def on_ready(self):
        print('logged in as {0.user}'.format(bot))
        try:
            channel = bot.get_channel(416384984597790750)
            await channel.send(f'🛠️ `Started analysing tool` 🧰')
        except:
            print("error")




        


bot = AnatoolBot()
bot.run(discord_token)