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
                #async for msg in ctx.channel.history(limit=100):
                #    for r in msg.reactions:
                #        print(f'>>> EMOJI: {r} with count: {r.count}')
                #        async for u in r.users():
                #            print(f'> {u.id}')

            else:
                await ctx.channel.send(f'An error ocurred.')


        @self.command(name='emojirank')
        async def test_command(ctx, *args):

            # parameters
            L = 150000 #maximum of L messages checked per channel

            now = ctx.message.created_at.timestamp()

            # ARG PARSE
            if len(args) >= 1:
                try:
                    days = int(args[0])
                except:
                    days = 7
                if days < 1:
                    days = 7

                if len(args) >= 2:
                    try:
                        threshold = int(args[1])
                    except:
                        threshold = 1
                    if threshold < 1:
                        threshold = 1
                else:
                    threshold = 1
            else:
                days = 7
            
            arguments = ''.join(args).lower()
            if "nolon" in arguments:
                nolon = True
            else:
                nolon = False

            if "nomod" in arguments:
                nomod = True
            else:
                nomod = False

            if "onlymdm" in arguments or "mdmonly" in arguments or "melodeathcord" in arguments:
                mdmonly = True
            else:
                mdmonly = False

            if nomod:
                ignored_authors = ["289925809878335489", "193001294548566016", "352626134195765248", "243762933987803146", "586358910148018189"]
            elif nolon:
                ignored_authors = ["586358910148018189"]
            else:
                ignored_authors = []

            #ignore bots always:
            ignored_authors += ["356268235697553409", "537353774205894676", "155149108183695360", "720135602669879386", "411916947773587456", "958105284759400559", "655390915325591629", "85614143951892480", "585271178180952064", "929348258910859325", "1074621494568689664"]

            server_emoji_ids = []
            for emoji in ctx.guild.emojis:
                server_emoji_ids.append(str(emoji.id))

            # checks
            validserver = await is_valid_server(ctx)
            adminrights = await has_manageperms(ctx)
            if validserver and adminrights:
                print(">>> emojirank")
                await ctx.channel.send(f'>> <a:catloading:970311103630417971> Checking channels:')

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
                public_threads = []
                for channel in text_channel_list:
                    roles = []
                    for role in channel.changed_roles:
                        roles.append(str(role.id))

                    if "1073291335097913435" in roles:
                        public_channels.append(channel)
                        for thread in channel.threads:
                            public_threads.append(thread)
                            #print(f'>>> {thread.name}')
                    else:
                        restricted_channels.append(channel)

                
                c_emoji_found = []
                d_emoji_found = []
                c_reactions_found = []
                d_reactions_found = []
                default_emojis = emojis.db.get_emoji_aliases().keys()
                #print(default_emojis)
                
                public_ct = public_channels + public_threads

                for channel in public_ct:
                    message_counter = 0
                    print(f'+++ {channel.name} +++')
                    async for msg in channel.history(limit=L):
                        dayage = round((int(now) - int(msg.created_at.timestamp()))/(60*60*24),2)

                        if dayage > days:
                            break
                        else:
                            message_counter += 1
                            #print(f'{message_counter}.: by {msg.author}, about {dayage} days ago')
                            author_id = str(msg.author.id)

                            # HANDLE EMOJIS WITHIN MESSAGES
                            if author_id in ignored_authors:
                                pass
                            else:
                                custom_emojis = list(set(re.findall(r'<a?:\w*:\d*>', msg.content)))

                                #handle custom emojis
                                for cusmoji in custom_emojis:
                                    cusmoji_id = cusmoji.split(":")[2].replace(">","")
                                    if mdmonly:
                                        if cusmoji_id in server_emoji_ids:
                                            c_emoji_found.append([cusmoji, msg.author, msg.created_at, msg.id, channel.name])
                                        else:
                                            #print("no external emoji checks")
                                            pass
                                    else:
                                        c_emoji_found.append([cusmoji, msg.author, msg.created_at, msg.id, channel.name])

                                if mdmonly:
                                    #print("no default emoji checks")
                                    pass
                                else:
                                    #handle default emojis
                                    for defmoji in default_emojis:
                                        if defmoji in msg.content:
                                            d_emoji_found.append([defmoji, msg.author, msg.created_at, msg.id, channel.name])

                            # HANDLE REACTIONS
                            reactions = msg.reactions
                            for r in msg.reactions:
                                if "<" in str(r) and ":" in str(r):
                                    emoji = str(r) 
                                    is_default_emoji = False

                                    cusmoji_id = emoji.split(":")[2].replace(">","")
                                    if cusmoji_id in server_emoji_ids:
                                        is_external = False
                                    else:
                                        is_external = True
                                else:
                                    emoji = emojis.decode(str(r))
                                    is_default_emoji = True
                                    is_external = False

                                proceed = True
                                if mdmonly:
                                    if is_external or is_default_emoji:
                                        proceed = False
                                    else:
                                        proceed = True

                                if proceed:
                                    #count = r.count
                                    user_ids = []
                                    async for u in r.users():
                                        user_ids.append(str(u.id))

                                    ignore = True
                                    for uid in user_ids:
                                        if uid not in ignored_authors:
                                            ignore = False

                                    if ignore == False:
                                        if is_default_emoji:
                                            d_reactions_found.append([emoji, msg.author, msg.created_at, msg.id, channel.name])
                                        else:
                                            c_reactions_found.append([emoji, msg.author, msg.created_at, msg.id, channel.name])


                    await ctx.channel.send(f'Checked #{channel.name}')


                all_emoji_found = c_emoji_found + d_emoji_found
                emoji_dict = {}
                for item in all_emoji_found:
                    e = item[0]
                    if e in emoji_dict.keys():
                        prevnum = emoji_dict[e]
                        emoji_dict[e] = int(emoji_dict[e])+1
                    else:
                        emoji_dict[e] = 1

                all_reactions_found = c_reactions_found + d_reactions_found
                reaction_dict = {}
                for item in all_reactions_found:
                    react = item[0]
                    if react in reaction_dict.keys():
                        prevnum = reaction_dict[react]
                        reaction_dict[react] = int(reaction_dict[react])+1
                    else:
                        reaction_dict[react] = 1

                totalmoji = all_emoji_found + all_reactions_found
                total_dict = {}
                for item in totalmoji:
                    e = item[0]
                    if e in total_dict.keys():
                        prevnum = total_dict[e]
                        total_dict[e] = int(total_dict[e])+1
                    else:
                        total_dict[e] = 1


                sorted_emoji = sorted(total_dict.items(), key=lambda x:x[1], reverse=True)


                # COMPOSING MESSAGES
                messages = [""]
                i = 0
                k = 0
                msgfull = False
                for item in sorted_emoji:
                    if msgfull:
                        k = k+1
                        messages.append("")
                        msgfull = False
                    i += 1
                    emoji = item[0]
                    q = item[1]
                    if q < threshold:
                        break
                    else:
                        try:
                            ecount = emoji_dict[emoji]
                        except:
                            ecount = 0
                        try:
                            rcount = reaction_dict[emoji]
                        except:
                            rcount = 0

                        messages[k] += f"`{i}.` {emoji} - `{str(q)}  ({ecount}, {rcount})`\n"
                    if len(messages[k]) > 4020:
                        msgfull = True

                m = len(messages)
                j = 1
                for msg in messages:
                    embed=discord.Embed(title=f"Emoji Usage - Ranking ({j}/{m})", description=msg, color=0xFFBF00)
                    if j == 1:
                        embed.set_thumbnail(url="https://i.imgur.com/5LrvMd4.png")
                    if j == m:
                        footy = ""
                        if nomod:
                            footy += "Emoji: no mods & bots. "
                        elif nolon:
                            footy += "Emoji: no bots & Lon. "
                        else:
                            footy += "Emoji: no bots. "

                        if mdmonly:
                            footy += "Only emojis from this server. "
                        else:
                            pass

                        footy += f" Threshold: {threshold}. Went back {days} day(s), but max per channel: {L} messages."
                        embed.set_footer(text=footy)
                    await ctx.send(embed=embed)
                    j += 1

                if mdmonly:
                    await ctx.send(f'Now the unused emoji <:sheepfeels:1019019495806861332>')

                    messages = [""]
                    k = 0
                    msgfull = False
                    for emoji in ctx.guild.emojis:
                        if msgfull:
                            k = k+1
                            messages.append("")
                            msgfull = False 
                        emojicode = "<"
                        if emoji.animated:
                            emojicode += "a"
                        emojicode += f":{emoji.name}:{emoji.id}>"

                        if emojicode in total_dict:
                            #print(f"{emojicode} was used")
                            pass
                        else:
                            messages[k] += f"{emojicode} `:{emoji.name}:`\n"

                        if len(messages[k]) > 4020:
                            msgfull = True
                    
                    j = 0
                    m = len(messages)
                    for msg in messages:
                        j += 1
                        embed=discord.Embed(title=f"Unused emoji ({j}/{m})", description=msg, color=0xFFBF00)
                        
                        if j == m:
                            footy = ""
                            if nomod:
                                footy += "Emoji: no mods & bots. "
                            elif nolon:
                                footy += "Emoji: no bots & Lon. "
                            else:
                                footy += "Emoji: no bots. "

                            footy += ", but only emojis from this server"


                            footy += f" Threshold: {threshold}. Went back {days} day(s), but max per channel: {L} messages."
                            embed.set_footer(text=footy)

                        await ctx.send(embed=embed)

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