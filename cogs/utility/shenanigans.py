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


class Shenanigans(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def is_valid_server(ctx):
        server = ctx.message.guild
        if server is None:
            raise commands.CheckFailure(f'Command does not work in DMs.')
            return False
        else:
            valid_servers = [413011798552477716]
            guild_id = server.id
            print(guild_id)
            if guild_id in valid_servers:
                return True
            else:
                raise commands.CheckFailure(f'Command does only work on specific servers.')
                return False


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



async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(
        Shenanigans(bot),
        guilds = [discord.Object(id = 413011798552477716)])