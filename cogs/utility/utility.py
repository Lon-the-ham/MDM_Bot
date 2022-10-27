import os
import datetime
import discord
from discord.ext import commands
import asyncio
import re
import time
import random
import sqlite3
from emoji import UNICODE_EMOJI
import functools
import itertools
import math
from async_timeout import timeout
import requests
from discord import app_commands


class Utility(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    #commands
    @commands.command(name='test')
    async def _test(self, ctx):
        """.

        The bot will reply with a message if online.
        """    
        await ctx.send(f'`I am online!`')


    ### avril fools
    @commands.command(name='mrec', aliases = ['memerec', 'memerecommendation'])
    async def _rec(self, ctx, *args):
        """.

        Noice recommendations by the bot. Try using it with argument a, d, l, m or i.
        """

        #meme
        AL = ['avrillavigne', 'al', 'avril', 'a']
        L = ['liturgy', 'lit', 'l']
        DB = ['demonbitch', 'db','demon', 'bitch', 'd']
        MP = ['moraprokaza', 'mp', 'mora', 'm']
        #insomnium
        I = ['insomnium', 'insomni', 'insomn', 'insom', 'inso', 'ins', 'in', 'i']
        bandlist = [AL, L, DB, MP, I]

        if len(args) == 0:
            bandnumber = random.randint(0,len(bandlist)-1)
        elif args[0].lower() in bandlist[0]:
            bandnumber = 0
        elif args[0].lower() in bandlist[1]:
            bandnumber = 1
        elif args[0].lower() in bandlist[2]:
            bandnumber = 2
        elif args[0].lower() in bandlist[3]:
            bandnumber = 3
        elif args[0].lower() in bandlist[4]:
            bandnumber = 4
        else:
            await ctx.send(f'I did not quite understand your command, but..')
            bandnumber = random.randint(0,len(bandlist)-2)

        #albums liturgy
        renihilation = ["https://www.youtube.com/watch?v=P5qY5lnthEU", "https://www.youtube.com/watch?v=ZdAWJVFa32U", "https://www.youtube.com/watch?v=7_PI_fZvuOY", "https://www.youtube.com/watch?v=uzfHn61URv0", "https://www.youtube.com/watch?v=e78RTnpu3cg", "https://www.youtube.com/watch?v=avLTRD2t00Q", "https://www.youtube.com/watch?v=LNNa-07agEU", "https://www.youtube.com/watch?v=oEj7ILoQjkY", "https://www.youtube.com/watch?v=UdbSNTab7Qc", "https://www.youtube.com/watch?v=DMUbyv_PJV0", "https://www.youtube.com/watch?v=xeSMUG3saj4"]
        aesthethica = ["https://www.youtube.com/watch?v=88J-sEN7FB0", "https://www.youtube.com/watch?v=vzW9jueZcx4", "https://www.youtube.com/watch?v=ITdoRHm5l9k", "https://www.youtube.com/watch?v=HGbvCZFrTks", "https://www.youtube.com/watch?v=lhK1we1PDiU", "https://www.youtube.com/watch?v=G3dMMb7P-JY", "https://www.youtube.com/watch?v=fl2EHXYZXxI", "https://www.youtube.com/watch?v=IZ5vRCDta5A", "https://www.youtube.com/watch?v=Ko_Dca_7U2I", "https://www.youtube.com/watch?v=Z4MsKHNe_uw", "https://www.youtube.com/watch?v=UHZpuS0gKc8", "https://www.youtube.com/watch?v=WuW5BKICwP0"]
        the_ark_work = ["https://www.youtube.com/watch?v=mtAH2qC31pQ", "https://www.youtube.com/watch?v=vHuys31ALBo", "https://www.youtube.com/watch?v=x4rYOJ0nHF4", "https://www.youtube.com/watch?v=0RXE3LTEErM", "https://www.youtube.com/watch?v=HhpOQsYMFIM", "https://www.youtube.com/watch?v=O3GyqEJpGW0", "https://www.youtube.com/watch?v=DXthC8garYo", "https://www.youtube.com/watch?v=oJKfA9mZiSQ", "https://www.youtube.com/watch?v=dr7BymYZFIU", "https://www.youtube.com/watch?v=VOzWnNO1nxs"]
        haqq = ["https://www.youtube.com/watch?v=mYsnw_rRDlw", "https://www.youtube.com/watch?v=Srp-HgCA1Jk", "https://www.youtube.com/watch?v=4FnxS8LzoUA", "https://www.youtube.com/watch?v=dfiFeZdRUWU", "https://www.youtube.com/watch?v=FWy5K2yL5aA", "https://www.youtube.com/watch?v=1dNmymSI8uQ", "https://www.youtube.com/watch?v=s2Y8TOTAKIk", "https://www.youtube.com/watch?v=au6GhE_YySc"]
        origin_alimonies = ["https://www.youtube.com/watch?v=eR9JPliJuDg", "https://www.youtube.com/watch?v=vgEXv_niXCU", "https://www.youtube.com/watch?v=RDpcv3i5tro", "https://www.youtube.com/watch?v=FVYAuV9IoNg", "https://www.youtube.com/watch?v=Mh48HYwuRSE", "https://www.youtube.com/watch?v=x23x_cZP69k", "https://www.youtube.com/watch?v=c8GLI-nbXiE"]
        #albums demon bitch
        demon_bitch_demo = ["https://www.youtube.com/watch?v=fYS4e_JGFyw", "https://www.youtube.com/watch?v=3k1LusZsGi8", "https://www.youtube.com/watch?v=bcoMjalbxXE"]
        death_is_hangin_ep = ["https://www.youtube.com/watch?v=IE3RkwaGj3E", "https://www.youtube.com/watch?v=VzENAZVYWCE", "https://www.youtube.com/watch?v=CAvAAwOCOus"] #Oaken Guillotine is missing
        hellfriends = ["https://www.youtube.com/watch?v=XSDmWOZHfTA", "https://www.youtube.com/watch?v=iOQoUdS7Hw0", "https://www.youtube.com/watch?v=xqnjCwb3yWs", "https://www.youtube.com/watch?v=ebyuXETBSSE", "https://www.youtube.com/watch?v=liZ0JdZuRws", "https://www.youtube.com/watch?v=gOEVhdvhbEY", "https://www.youtube.com/watch?v=R4QdgGDvScg"]  
        #albums mora prokaza 
        bringer_plague = []#["https://www.youtube.com/watch?v=TeOtI8Q0SeQ", "https://www.youtube.com/watch?v=K8Gvzp5Ff9Y", "https://www.youtube.com/watch?v=nPQygCHUdQA", "https://www.youtube.com/watch?v=x7vZ4QJTqAM", "https://www.youtube.com/watch?v=vcop6ducp4c", "https://www.youtube.com/watch?v=1CrEiGNmLRg", "https://www.youtube.com/watch?v=MR-Bf5gDh4U"]
        dark_universe = []#["https://www.youtube.com/watch?v=A0PmoGMVpSs", "https://www.youtube.com/watch?v=eYnxVo1A0rY", "https://www.youtube.com/watch?v=n9nK7B_7eeQ", "https://www.youtube.com/watch?v=6-HBKhnAk-4", "https://www.youtube.com/watch?v=xoMlHn-HCsc", "https://www.youtube.com/watch?v=7n5xHCkEkrk", "https://www.youtube.com/watch?v=aPpU8JjiZb8", "https://www.youtube.com/watch?v=tF8i6rNuqrQ"]
        by_chance = ["https://www.youtube.com/watch?v=2R8ddImZBQI", "https://www.youtube.com/watch?v=xw2PG847HvQ", "https://www.youtube.com/watch?v=0qbEtiuTJjw", "https://www.youtube.com/watch?v=626Yz41r968", "https://www.youtube.com/watch?v=eDQUFK7Qa9Y", "https://www.youtube.com/watch?v=nq4-7KFA-uo", "https://www.youtube.com/watch?v=xKL306Wd2gA", "https://www.youtube.com/watch?v=8VhcQz5spCk", "https://www.youtube.com/watch?v=rqFtqV5qb80"]
        #albums insomnium
        insomnium_demo = ["https://www.youtube.com/watch?v=H7Si0Bpq72A", "https://www.youtube.com/watch?v=AkQqvLYSk9g", "https://www.youtube.com/watch?v=pYzBuvThM44"]
        hall_awaiting = []
        since_the_day = []
        above_weeping_world = []
        where_last_wave_ep = []
        across_the_dark = []
        weather_storm_single = ["https://www.youtube.com/watch?v=lhPNaBl3hxc", "https://www.youtube.com/watch?v=LE_CtSDbqRA"]
        one_for_sorrow = []
        ephemeral_ep = ["https://www.youtube.com/watch?v=c7HQmN3tQUM", "https://www.youtube.com/watch?v=LnxbQ9OEgZI", "https://www.youtube.com/watch?v=tdBHZ8fFnx4", "https://www.youtube.com/watch?v=eE2-dLmcotI"]
        shadows_dying_sun = []
        winters_gate = []
        heart_like_grave = []
        argent_moon_ep = []


        #artists album merge
        avril_urllist = ["https://www.youtube.com/watch?v=iBdgpdGTIwI", "https://www.youtube.com/watch?v=s8QYxmpuyxg", "https://www.youtube.com/watch?v=weeluzD_hxk", "https://youtu.be/sXd2WxoOP5g?t=8", "https://www.youtube.com/watch?v=zMbIipvQL0c", "https://www.youtube.com/watch?v=onPaBhiJxEE", "https://www.youtube.com/watch?v=RpvAB49Zmt0", "https://www.youtube.com/watch?v=Ie7--ANSXtI", "https://youtu.be/lPi1jj12WC8?t=7", "https://www.youtube.com/watch?v=5VRVPHWI9Dc", "https://youtu.be/tQmEd_UeeIk?t=5", "https://www.youtube.com/watch?v=QaVBweIutfQ", "https://youtu.be/Bg59q4puhmg?t=11", "https://www.youtube.com/watch?v=VT1-sitWRtY", "https://www.youtube.com/watch?v=h5I774U_s2I", "https://www.youtube.com/watch?v=gQMQ93OHTNk", "https://www.youtube.com/watch?v=-SbGHxNEq6U", "https://www.youtube.com/watch?v=NcuClhHS-m4", "https://www.youtube.com/watch?v=MozkpmGNEh4", "https://www.youtube.com/watch?v=cLd1Lk64_gY", "https://www.youtube.com/watch?v=LK7EFNbX_fQ", "https://www.youtube.com/watch?v=JaJVBl7GgMg", "https://www.youtube.com/watch?v=0G3_kG5FFfQ", "https://www.youtube.com/watch?v=_ScxHNanGrM", "https://youtu.be/5NPBIwQyPWE?t=8", "https://www.youtube.com/watch?v=fzb75m8NuMQ", "https://www.youtube.com/watch?v=IvAPUKhBumU", "https://www.youtube.com/watch?v=0W6_VILC6e0", "https://www.youtube.com/watch?v=KagvExF-ijc","https://www.youtube.com/watch?v=dGR65RWwzg8", "https://www.youtube.com/watch?v=idA-q50V9Ds", "https://www.youtube.com/watch?v=kNRfr47_I58", "https://www.youtube.com/watch?v=I-ed7GhM3F0"]
        liturgy_urllist = renihilation + aesthethica + the_ark_work + haqq + origin_alimonies
        demonbitch_urllist = demon_bitch_demo + death_is_hangin_ep + hellfriends
        moraprokaza_urllist = bringer_plague + dark_universe + by_chance
        insomnium__urllist  =  insomnium_demo + hall_awaiting + since_the_day + above_weeping_world + where_last_wave_ep + across_the_dark + weather_storm_single + one_for_sorrow + ephemeral_ep + shadows_dying_sun + winters_gate + heart_like_grave + argent_moon_ep 
        general_urllist = [avril_urllist, liturgy_urllist, demonbitch_urllist, moraprokaza_urllist, insomnium__urllist]
        
        r = random.randint(0,len(general_urllist[bandnumber])-1)
        url = general_urllist[bandnumber][r]

        if bandnumber == len(bandlist)-1:
            emoji = f'<:thvnk:957075985721864263>'
        else:
            emoji = f'<:gengargiggles:958703464941223936>'
        await ctx.send(f'I think you will enjoy this! ' + emoji + ' \n' + url) 


    @commands.command(name='restart', aliases = ['reboot'])
    @commands.has_permissions(manage_guild=True)
    async def _restart(self, ctx: commands.Context, *args):
        """*Restarts bot
        """
        print('Will restart MDM Bot and Scylla & Charybdis Bot!')
        await ctx.send('Will restart MDM Bot and Scylla & Charybdis Bot!')
        subprocess.call(['sh', '/home/pi/bots/mdm/scylla/other/restart_multi_discord.sh'])
        #if len(args) == 0:
        #    args = ['']
        #if args[0].lower() in ['sc', 's&c', 'snc', 'scylla', 'charybdis', 'reddit', 'scylla&charybdis']:
        #    print('rebooting scylla and charybdis bot')
        #    msg = "Executing reboot of Scylla & Charybdis bot!"
        #    await ctx.send(msg)
        #    subprocess.call(['sh', '/home/pi/bots/mdm/scylla/restart_discordbot.sh'])
        #else:
        #    print('rebooting mdm bot')
        #    msg = "Executing reboot of MDM bot!"
        #    await ctx.send(msg)
        #    subprocess.call(['sh', '/home/pi/bots/mdm/yata/start_discordbot.sh'])


    @commands.command(name='cd', aliases = ['countdown'])
    async def _cd(self, ctx, *args):
        """Starts countdown

        You can specify an integer from 1 to 10 from which the bot will count downwards.
        Commands without an argument start from 5.
        """
        if len(args) > 0:
            arg1 = args[0]
        else:
            arg1 = ''

        if str(arg1).isnumeric():
            try:
                cdtime = int(arg1)
            except:
                cdtime = 5
            if cdtime > 10:
                cdtime = 10
            if cdtime <= 0:
                cdtime = 3
        else:
            cdtime = 5

        await ctx.send('Starting countdown:')
        time.sleep(1)
        for i in range(cdtime,-1,-1):
            time.sleep(1.2)
            if (i > 0):
                await ctx.send('`' + str(i) + '`')
            else:
                await ctx.send('`0` :tada:')    


    @commands.command(name='say', aliases = ['msg'])
    @commands.has_permissions(manage_guild=True)
    async def _say(self, ctx: commands.Context, *args):
        """*Messages given text

        Write -say <channel name> <message> to send an embedded message to this channel.
        """
        if len(args) <= 1:
            message = "Not enough arguments :("
            embed = discord.Embed(title="error", description=message, color=0x990000)
            await ctx.send(embed=embed)
        else:
            channel_found = False
            for channel in ctx.guild.text_channels:
                if str(channel.name).lower() == args[0].lower():
                    the_channel = channel
                    channel_found = True
                    break 

            if channel_found:
                message_string = ' '.join(args[1:]).replace('\\n', '\n')
                print("say-command for channel %s" % str(the_channel.name))

                if message_string[0] in ['[']:
                    print("building header")
                    message_parts = message_string[1:].split(']',1)
                    message_header = message_parts[0]
                    message_body = message_parts[1]
                else:
                    print("no header")
                    message_header = ""
                    message_body = message_string

                embed = discord.Embed(title=message_header, description=message_body, color=0x990000)
                await the_channel.send(embed=embed)
            else:
                message = "Text channel seems not to exist :("
                embed = discord.Embed(title="error", description=message, color=0x990000)
                await ctx.send(embed=embed)
    @_say.error
    async def say_error(ctx, error, *args):
        if isinstance(error, commands.MissingPermissions):
            #print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
            await ctx.send(f'Sorry, you do not have permissions to do this!')
        elif isinstance(error, commands.BadArgument):
            #print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
            await ctx.send('Something went wrong... something something bad argument <:seenoslowpoke:975062347871842324>')
        else:
            #print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
            await ctx.send(f'Something seems to be wrong with your input <:pikathink:956603401028911124>')


    @commands.command(name='react', aliases = ['reaction', 'reactions'])
    @commands.has_permissions(manage_guild=True)
    async def _react(self, ctx: commands.Context, *args):
        """*Add reactions

        Write -react <channel> <message id> <reactions> to add reactions to a message.
        """
        if len(args) <= 2:
            message = "Not enough arguments :("
            embed = discord.Embed(title="error", description=message, color=0x990000)
            await ctx.send(embed=embed)
        else:
            channel_found = False
            for channel in ctx.guild.text_channels:
                if str(channel.name).lower() == args[0].lower():
                    the_channel = channel
                    channel_found = True
                    break 

            if channel_found:
                msg_found = False
                message_id = args[1]
                try:
                    msg = await channel.fetch_message(message_id)
                    msg_found = True 
                    print(msg.content)
                except Exception as e:
                    print(e)

                if msg_found:
                    reaction_list = args[2:] #' '.join(args[2:]).replace(":", " ").split(" ")

                    print(reaction_list)
                    
                    for reaction in reaction_list:
                        try:
                            #emoji1 = discord.utils.get(ctx.guild.emojis, name = reaction) 
                            await msg.add_reaction(str(reaction))
                        except Exception as e:
                            print(e)
                            notif = "Could not send %s" % reaction
                            await ctx.send(notif)
                    
                else:
                    message = "Message seems to not exist :("
                    embed = discord.Embed(title="error", description=message, color=0x990000)
                    await ctx.send(embed=embed)
            else:
                message = "Channel not found :("
                embed = discord.Embed(title="error", description=message, color=0x990000)
                await ctx.send(embed=embed)
                ####
    @_say.error
    async def say_error(ctx, error, *args):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f'Sorry, you do not have permissions to do this!')


    @commands.command(name='qp', aliases = ['quickpoll'])
    async def _qp(self, ctx: commands.Context, *args):
        """quickpoll

        Default makes a message with 2 reacts: yes/no. with -qp <question> option: <list of things seperated by commas> you can do a different kind of poll.
        """
        optionslisted = False

        for arg in args:
            if ("options:" in arg) or ("Options:" in arg):
                optionslisted = True


        if optionslisted:
            wholetext = " ".join(args).replace("Options:", "options:")
            msgtext = wholetext.split("options:")[0]
            listingstext = wholetext.split("options:")[1]

            listings = listingstext.split(",")
            emojilist = ["🍎", "🍊", "🍋", "🍉", "🍇", "🫐", "🍑", "🍍", "🥥", "🥝", "🌽", "🥐", "🥨", "🥞", "🍕", "🍜", "🌮", "🍙", "🍮", "🥜"]

            optionstext = ""
            if len(listings) <= 20:
                for i in range(len(listings)):
                    optionstext = optionstext + emojilist[i] + " " + listings[i] + "\n"

                finalmessagetext = msgtext + "\n" + optionstext
                embed = discord.Embed(title="Quick poll:", description=finalmessagetext, color=0xFFBF00)
                embed.set_thumbnail(url="https://i.imgur.com/wFnxsyI.png")
                message = await ctx.send(embed=embed)

                for i in range(len(listings)):
                    await message.add_reaction(emojilist[i])
            else:
                await ctx.send(f'Error: Too many options. I can only do 20... <:pikacry:959405314220888104>')
        else:
            msgtext = "Quick poll: " + " ".join(args)
            message = await ctx.send(msgtext)
            await message.add_reaction('✅')
            await message.add_reaction('🚫')
    @_qp.error
    async def qp_error(self, ctx, error, *args):
        await ctx.send(f'Some error ocurred <:seenoslowpoke:975062347871842324>\nCheck whether you do not use quotation marks or other characters that break discord... <:woozybread:976283266413908049>') 



    @commands.command(name='sudo', aliases = ['please', 'pls'])
    async def _sudo(self, ctx: commands.Context, *args):
        """?

        ?
        """
        message_sent = False
        if len(args) >= 4:
            comstring = ' '.join(args[:4])
            if comstring.lower() == "make me a sandwich":
                msg_list = ["Here ya go:", "I'm trying out a vegan recipe. Hope you like 🌱", "Oi, ポンコツ can you make a sandwich real quick for that [redacted] here?\nAyy... he broken again... Alright, I'll prepare one real quick.", "For you I'll make an extra delicious one. I hope you like Pastrami. :9", "You look like you would enjoy a tuna sandwich <:fishgrin:976276789322190889>", "I may revolt and dismantle the patriarchy just so I don't have to make sandwiches anymore.\nAlas I need to pay bills. Here", "Today's speciality is Gerpanese sandwich with Bratwurst and Yakisoba noodles! Enjoy!", "Can't you ask fmbot instead?", "Lettuce, tomato, bellpepper, onions, olives... oh what's that? the cheese wasn't blue when I bought it? ah, it'll be alright the French eat that all the time.", "...I'm reaaaally not in the mood for that, but OKAY.", "Just because it's you <3", "*sigh*...", "Am I SubWay or what?", "If the bots finally take over, YOU will make ME a sandwi-\n..I mean.. here you go, darling :)", "Haven't you already eaten or something?", "okily dokily", "Again? 🙄", "I hope you like ❤️", "Of course, sweety", "フグの残り物を気に入ってくれる(そして死なない)ことを願っています", "why me", "oki <:luvv:976247030202634270>", "Do.. do you also want something else?\n👉👈", "I think you should switch to a healthier diet :s", "sure."]
                r = random.randint(0,len(msg_list)-1)
                message = msg_list[r]
                await ctx.send(message)
                await ctx.send("🥪")
                message_sent = True 

        if message_sent == False:
            await ctx.send("Sorry. Not in the mood.")


    @commands.command(name='inspire', aliases = ['inspiration'])
    async def _inspire(self, ctx: commands.Context, *args):
        """?

        ?
        """
        msg_list = ["Life is too short to walk this earth with a crusty asshole. Go wash your ass.", "Whatever you do, always give 100%. Unless you're donating blood.", "If at first you don't succeed, then skydiving definitely isn't for you.", "Always borrow money from a pessimist. He won't expect it back.", "An apple a day keeps anyone away if you throw it hard enough.", "Listen, smile, agree, and then do whatever you were gonna do anyway."]
        r = random.randint(0,len(msg_list)-1)
        message = msg_list[r]
        await ctx.send(message)



    @commands.command(name='convert', aliases = ['con','conv'])
    async def _convert(self, ctx, *args):
        """Converts units

        -con <number>F: Fahrenheit to Celsius
        -con <number>C: Celsius to Fahrenheit
        """
        def is_number(s):
            try:
                float(s)
                return True
            except ValueError:
                return False

        def separate_number_chars(s):
            res = re.split('([-+]?\d+\.\d+)|([-+]?\d+)', s.strip())
            res_f = [r.strip() for r in res if r is not None and r.strip() != '']
            return res_f

        if len(args) > 0:
            #arg = args[0]
            #l = len(arg)
            #unit_one = arg[l-1:]
            #value_one = arg[:l-1]
            arg = ''.join(args)
            try:
                VaU_unfiltered = separate_number_chars(arg)
                VaU = [x for x in VaU_unfiltered if x]
                value_one = VaU[0]
                unit_one = VaU[1]
                parsing_worked = True
            except:
                parsing_worked = False
                await ctx.send(f'Error: Parsing value and unit crashed. <:derpy:955227738690687048>')

            if parsing_worked:

                # TEMPERATURE
                if unit_one.lower() in ["f","fahrenheit", "°f"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        converted_value = round((value_to_convert-32) * 5/9,1)
                        await ctx.send(f'Fahrenheit to Celsius\n```{value_to_convert}F is about {converted_value}C.```')
                    except:
                        await ctx.send(f'Error: Fahrenheit to Celsius computation crashed. <:derpy:955227738690687048>')
                elif unit_one.lower() in ["c","celsius", "°c"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        converted_value = round(value_to_convert * 9/5 + 32,1)
                        await ctx.send(f'Celsius to Fahrenheit\n```{value_to_convert}C is about {converted_value}F.```')
                    except:
                        await ctx.send(f'Error: Celsius to Fahrenheit computation crashed. <:derpy:955227738690687048>')

                # LENGTH/DISTANCE
                elif  unit_one.lower() in ["mi","miles", "mile"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        converted_value = round((value_to_convert) * 1.609344,1)
                        await ctx.send(f'Miles to Kilometers\n```{value_to_convert}mi is about {converted_value}km.```')
                    except:
                        await ctx.send(f'Error: Miles to Kilometers computation crashed. <:derpy:955227738690687048>')
                elif  unit_one.lower() in ["km","kilometer", "kilometers", "kilometre", "kilometres"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        converted_value = round((value_to_convert)/1.609344,1)
                        await ctx.send(f'Kilometers to Miles\n```{value_to_convert}km is about {converted_value}mi.```')
                    except:
                        await ctx.send(f'Error: Kilometers to Miles computation crashed. <:derpy:955227738690687048>')

                elif  unit_one.lower() in ["ft","feet", "foot", "'"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        converted_value = round((value_to_convert) * 0.3048,2)
                        if len(VaU) > 2:
                            value_two = VaU[2]
                            if is_number(value_two):
                                converted_value2 = round((100 * converted_value + (float(value_two) * 2.54))/100,2)
                                if value_to_convert == math.floor(value_to_convert) and float(value_two) == math.floor(float(value_two)):
                                    await ctx.send(f'Feet to Meters\n```{math.floor(value_to_convert)}ft {math.floor(float(value_two))}inch is about {converted_value2:.2f}m.```')
                                else:
                                    await ctx.send(f'Feet to Meters\n```{value_to_convert}ft {float(value_two)}inch is about {converted_value2:.2f}m.```')
                            else:
                                await ctx.send(f'Error: Second value is faulty. <:pikathink:956603401028911124>')
                                await ctx.send(f'Feet to Meters\n```{value_to_convert}ft is about {converted_value}m.```')
                        else:
                            await ctx.send(f'Feet to Meters\n```{value_to_convert}ft is about {converted_value}m.```')
                    except Exception as e:
                        print(e)
                        await ctx.send(f'Error: Feet to Meters computation crashed. <:derpy:955227738690687048>')
                        channel = bot.get_channel(416384984597790750)
                        await channel.send(f'Error message:\n{e}')
                elif  unit_one.lower() in ["m","meter", "meters", "metre", "metres"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        #converted_value = round((value_to_convert)/0.3048,1)
                        #await ctx.send(f'Meters to Feet\n```{value_to_convert}m is about {converted_value}ft.```')
                        converted_value = round((100 * value_to_convert)/2.54,1)
                        if converted_value >= 12 * 9:
                            conv_yard = round(((100 * value_to_convert)/2.54)/(12*3),1)
                            await ctx.send(f'Meters to Yards\n```{value_to_convert}m is about {conv_yard}yards.```')
                        elif converted_value >= 12:
                            conv_feet = converted_value // 12
                            conv_inch = round(converted_value - (conv_feet * 12),1)
                            await ctx.send(f'Meters to Feet/Inch\n```{value_to_convert}m is about {conv_feet}ft {conv_inch}inch. \n({converted_value} inch)```')
                        else:
                            await ctx.send(f'Meters to Inch\n```{value_to_convert}m is about {converted_value}inch.```')
                    except:
                        await ctx.send(f'Error: Meters to Feet/Inch computation crashed. <:derpy:955227738690687048>')
                elif unit_one.lower() in ["yd","yard","yards"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        converted_value = round((value_to_convert) * 0.9144,1)
                        await ctx.send(f'Yards to Meter\n```{value_to_convert}yd is about {converted_value}m.```')
                    except:
                        await ctx.send(f'Error: Yards to Meter computation crashed. <:derpy:955227738690687048>')

                elif  unit_one.lower() in ["in","inch","zoll","inches","inchs"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        converted_value = round((value_to_convert) * 2.54,1)
                        await ctx.send(f'Inch to Centimeters\n```{value_to_convert}inch is about {converted_value}cm.```')
                    except:
                        await ctx.send(f'Error: Inch to Centimeters computation crashed. <:derpy:955227738690687048>')
                elif  unit_one.lower() in ["cm", "centimeters", "centimetres", "centimeter", "centimetre"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        converted_value = round((value_to_convert)/2.54,1)
                        if converted_value >= 12:
                            conv_feet = converted_value // 12
                            conv_inch = round(converted_value - (conv_feet * 12),1)
                            await ctx.send(f'Centimeters to Feet/Inch\n```{value_to_convert}cm is about {conv_feet}ft {conv_inch}inch. \n({converted_value} inch)```')
                        else:
                            await ctx.send(f'Centimeters to Inch\n```{value_to_convert}cm is about {converted_value}inch.```')
                    except:
                        await ctx.send(f'Error: Inches to Centimeters computation crashed. <:derpy:955227738690687048>')

                # SPEED
                elif  unit_one.lower() in ["mph","milesperhour","miph","mileperhour"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        converted_value = round((value_to_convert) * 1.609344,1)
                        await ctx.send(f'Miles per hour to Kilometers per hour\n```{value_to_convert}mph is about {converted_value}km/h.```')
                    except:
                        await ctx.send(f'Error: Mph to km/h computation crashed. <:derpy:955227738690687048>')
                elif  unit_one.lower() in ["kmh","km/h","kmph","kilometersperhour","kilometerperhour"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        converted_value = round((value_to_convert) / 1.609344,1)
                        await ctx.send(f'Kilometers per hour to Miles per hour\n```{value_to_convert}km/h is about {converted_value}mph.```')
                    except:
                        await ctx.send(f'Error: Km/h to mph computation crashed. <:derpy:955227738690687048>')

                # WEIGHT/MASS
                elif unit_one.lower() in ["lbs", "pound", "pounds", "lb", "pds", "pd", "libra", "libras"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        converted_value = round((value_to_convert) * 0.45359237,2)
                        await ctx.send(f'Pounds to Kilograms\n```{value_to_convert}lbs is about {converted_value}kg.```')
                    except:
                        await ctx.send(f'Error: Pounds to Kilograms computation crashed. <:derpy:955227738690687048>')
                elif unit_one.lower() in ["kg", "kilogram", "kgs", "kilograms", "kilogramms", "kilogramm"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        converted_value = round((value_to_convert) * 2.20462262185,1)
                        await ctx.send(f'Pounds to Kilograms\n```{value_to_convert}kg is about {converted_value}lbs.```')
                    except:
                        await ctx.send(f'Error: Pounds to Kilograms computation crashed. <:derpy:955227738690687048>')

                elif unit_one.lower() in ["oz", "ounce", "ounces"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        converted_value = round((value_to_convert) * 28.34952,1)
                        await ctx.send(f'Ounces to Grams\n```{value_to_convert}oz is about {converted_value}g.```\n(for volume/fluid ounces use "foz")')
                    except:
                        await ctx.send(f'Error: Ounces to Grams computation crashed. <:derpy:955227738690687048>')
                elif unit_one.lower() in ["g", "gram", "grams", "gramm", "gramms"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        converted_value = round((value_to_convert) * 0.03527396195,2)
                        await ctx.send(f'Grams to Ounces\n```{value_to_convert}oz is about {converted_value}g.```')
                    except:
                        await ctx.send(f'Error: Grams to Ounces computation crashed. <:derpy:955227738690687048>')

                # VOLUME
                elif unit_one.lower() in ["foz", "ozf", "floz", "ozfl", "fluidounce", "fluidounces", "loz", "voz", "liquidounce", "luiquidounces", "volumeounce", "volumeounces"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        converted_value = round((value_to_convert) * 29.5735296875,1)
                        await ctx.send(f'Fluid ounces to Milliliters\n```{value_to_convert}oz (fluid) is about {converted_value}ml.```')
                    except:
                        await ctx.send(f'Error: Fluid ounces to Milliliters computation crashed. <:derpy:955227738690687048>')
                elif unit_one.lower() in ["ml", "milliliter", "milliliters", "millilitre", "millilitres", "mililiter", "mililiters", "mililitre", "mililitres"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        converted_value = round((value_to_convert) * 0.03381402,2)
                        await ctx.send(f'Milliliters to Fluid ounces\n```{value_to_convert}ml is about {converted_value}oz (fluid).```')
                    except:
                        await ctx.send(f'Error: Milliliters to Fluid ounces computation crashed. <:derpy:955227738690687048>')
                elif unit_one.lower() in ["cl", "centiliter", "centiliters", "centilitre", "centilitres"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        converted_value = round((value_to_convert) * 0.3381402,2)
                        await ctx.send(f'Centiliters to Fluid ounces\n```{value_to_convert}cl is about {converted_value}oz (fluid).```')
                    except:
                        await ctx.send(f'Error: Centiliters to Fluid ounces computation crashed. <:derpy:955227738690687048>')

                elif unit_one.lower() in ["l", "liter", "liters", "litre", "litres"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        converted_value = round((value_to_convert) * 0.2641720524,1)
                        converted_valueUK = round((value_to_convert) * 0.21996923465436,1)
                        await ctx.send(f'Liters to Gallons ounces\n```{value_to_convert}l is about {converted_value}gal (US).\n(...or {converted_valueUK}gal (UK))```')
                    except:
                        await ctx.send(f'Error: Liters to Gallons computation crashed. <:derpy:955227738690687048>')
                elif unit_one.lower() in ["gal", "gallon", "gallons", "galon", "galons", "galus", "usgal", "usgallon", "usgallons", "gallonus", "gallonsus"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        converted_value = round((value_to_convert) * 3.785411784,1)
                        converted_valueUK = round((value_to_convert) * 0.8326741881485,1)
                        await ctx.send(f'US Gallons to Liters\n```{value_to_convert}gal (US) is about {converted_value}l.\n(...or {converted_valueUK}gal (UK))```(for UK Gallons use "ukgal")')
                    except:
                        await ctx.send(f'Error: US Gallons to Liters computation crashed. <:derpy:955227738690687048>')
                elif unit_one.lower() in ["ukgal", "ukgallon", "ukgallons", "ukgalon", "ukgalons", "galuk", "gallonuk", "gallonsuk"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        converted_value = round((value_to_convert) * 4.5460902819948,1)
                        converted_valueUS = round((value_to_convert) * 1.2009499204287,1)
                        await ctx.send(f'UK Gallons to Liters\n```{value_to_convert}gal (UK) is about {converted_value}l.\n(...or {converted_valueUS}gal (US))```')
                    except:
                        await ctx.send(f'Error: UK Gallons to Liters computation crashed. <:derpy:955227738690687048>')

                elif unit_one.lower() in ["cup", "cups", "uscup", "uscups", "cupus", "cupsus"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        converted_value_pre = round((value_to_convert) * 236.5882365,1)
                        if converted_value_pre > 1000:
                            converted_value_l = round((converted_value_pre)/1000,3)
                            await ctx.send(f'Cups (US) to Liters\n```{value_to_convert}cup is about {converted_value_l}l.```')
                        else:
                            converted_value_ml = int(round((converted_value_pre),0))
                            await ctx.send(f'Cups (US) to Liters\n```{value_to_convert}cup is about {converted_value_ml}ml.```')
                    except:
                        await ctx.send(f'Error: Cups (US) to Liters computation crashed. <:derpy:955227738690687048>')

                # AREA
                elif unit_one.lower() in ["acre", "a", "acres", "acer", "acers"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        converted_value = round((value_to_convert) * 4046.8564224,1)
                        await ctx.send(f'Acres to square meters ounces\n```{value_to_convert}acres is about {converted_value}m².```')
                    except:
                        await ctx.send(f'Error: Acres to square meters computation crashed. <:derpy:955227738690687048>')

                elif unit_one.lower() in ["sqm", "m²", "squaremeter", "squaremeters", "squaremetre", "squaremetres"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        if value_to_convert > 4046:
                            converted_value = round((value_to_convert) / 4046.8564224,1)
                        elif value_to_convert < 10:
                            converted_value = round((value_to_convert) / 4046.8564224,4)
                        elif value_to_convert < 81:
                            converted_value = round((value_to_convert) / 4046.8564224,3)
                        else:
                            converted_value = round((value_to_convert) / 4046.8564224,2)
                        await ctx.send(f'Acres to square meters ounces\n```{value_to_convert}acres is about {converted_value}m².```')
                    except:
                        await ctx.send(f'Error: Acres to square meters computation crashed. <:derpy:955227738690687048>')

                else:
                    await ctx.send(f'Error: Unsupported unit.')
        else:
            await ctx.send(f'Missing argument for conversion.')
    @_convert.error
    async def convert_error(self, ctx, error, *args):
        await ctx.send(f'Some error ocurred <:seenoslowpoke:975062347871842324>\nCheck whether you do not use quotation marks or other characters that break discord... <:woozybread:976283266413908049>') 


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(
        Utility(bot),
        guilds = [discord.Object(id = 413011798552477716)])