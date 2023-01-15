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


class Pingable_Interests(commands.Cog):
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



    @commands.command(name='pingterest', aliases=['pingableinterest', 'createpi', 'newpi', 'pi'])
    @commands.has_permissions(manage_guild=True, manage_roles=True)
    @commands.check(is_valid_server)
    async def _pingterest(self, ctx, *args):
        """*(New) PI + message

        Creates a message with the pingterest to be able to join via react, but also makes an entry in the db for said interest, so that members can join it via -joinpi."""
        pi_name = " ".join(args).lower()

        if pi_name != "":
            if ("," in pi_name) or (":" in pi_name):
                await ctx.send(f"pingterest name cannot have commas or colons!") 
            else:
                conpi = sqlite3.connect('cogs/pingterest/pingterest.db')
                curpi = conpi.cursor()
                curpi.execute('''CREATE TABLE IF NOT EXISTS pingterests (pingterest text, userid text, username text, details text)''')

                pi_list = [[item[0], item[1], item[2], item[3]] for item in curpi.execute("SELECT pingterest, userid, username, details FROM pingterests WHERE pingterest = ?", (pi_name,)).fetchall()]

                if len(pi_list) == 0:
                    print("pingterest: %s (newly created)" % pi_name)
                    curpi.execute("INSERT INTO pingterests VALUES (?, ?, ?, ?)", (pi_name, "", "", "template"))
                    conpi.commit()
                else:
                    print("pingterest: %s (already exists)" % pi_name)

                pi_title = "pingterest: %s" % pi_name
                pi_desc = "Interested in `%s` and getting pinged? \nReact with ✅ to join this pingable interest. React with 🚫 to leave it." % pi_name

                embed = discord.Embed(title=pi_title, description=pi_desc, color=0x000080)
                embed.set_footer(text="You can always use -joinpi <pingterest name> or -leavepi <pingeterest name> to join or leave later. Check with -listmypi to get a list of all the pingterests you joined.")
                message = await ctx.send(embed=embed)
                await message.add_reaction('✅')
                await message.add_reaction('🚫')
        else:
            await ctx.send("No name for pingterest given! <:attention:961365426091229234>")
    @_pingterest.error
    async def pingterest_error(ctx, error, *args):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f'Sorry, you do not have permissions to do this!')  


    @commands.command(name='joinpi', aliases=['joinpingterest'])
    async def _joinpi(self, ctx, *args):
        """joins PI

        """
        user = ctx.message.author
        pi_name = " ".join(args).lower()

        if pi_name != "":
            conpi = sqlite3.connect('cogs/pingterest/pingterest.db')
            curpi = conpi.cursor()
            curpi.execute('''CREATE TABLE IF NOT EXISTS pingterests (pingterest text, userid text, username text, details text)''')

            pi_list = [[item[0], item[1], item[2], item[3]] for item in curpi.execute("SELECT pingterest, userid, username, details FROM pingterests WHERE pingterest = ? AND details = ?", (pi_name, "template")).fetchall()]

            if len(pi_list) == 0:
                await ctx.send("This pingterest does not exist! <:attention:961365426091229234>")
            else:
                pi_user = [[item[0], item[1], item[2], item[3]] for item in curpi.execute("SELECT pingterest, userid, username, details FROM pingterests WHERE pingterest = ? AND userid = ?", (pi_name, str(user.id))).fetchall()]
                if len(pi_user) == 0:
                    print("pingterest: %s (user joined)" % pi_name)
                    curpi.execute("INSERT INTO pingterests VALUES (?, ?, ?, ?)", (pi_name, str(user.id), str(user.name), ""))
                    conpi.commit()
                    await ctx.send("You successfully joined this pingterest! <:excitedfrog:975568907526082620>")
                else:
                    print("pingterest: %s (already joined)" % pi_name)
                    await ctx.send("You already joined this pingterest! <:pikaohh:975165648168697947>")
        else:
            await ctx.send("No name for pingterest given! <:attention:961365426091229234>")


    @commands.command(name='leavepi', aliases=['leavepingterest'])
    async def _leavepi(self, ctx, *args):
        """leaves PI

        """
        user = ctx.message.author
        pi_name = " ".join(args).lower()

        if pi_name != "":
            conpi = sqlite3.connect('cogs/pingterest/pingterest.db')
            curpi = conpi.cursor()
            curpi.execute('''CREATE TABLE IF NOT EXISTS pingterests (pingterest text, userid text, username text, details text)''')

            pi_list = [[item[0], item[1], item[2], item[3]] for item in curpi.execute("SELECT pingterest, userid, username, details FROM pingterests WHERE pingterest = ? AND details = ?", (pi_name, "template")).fetchall()]

            if len(pi_list) == 0:
                await ctx.send("This pingterest does not exist! <:attention:961365426091229234>")
            else:
                pi_user = [[item[0], item[1], item[2], item[3]] for item in curpi.execute("SELECT pingterest, userid, username, details FROM pingterests WHERE pingterest = ? AND userid = ?", (pi_name, str(user.id))).fetchall()]
                if len(pi_user) != 0:
                    print("pingterest: %s (user joined)" % pi_name)
                    curpi.execute("DELETE FROM pingterests WHERE pingterest = ? AND userid = ?", (pi_name, str(user.id)))
                    conpi.commit()
                    await ctx.send("You successfully left this pingterest! <:fishgrin:976276789322190889>")
                else:
                    print("pingterest: %s (hasnt joined)" % pi_name)
                    await ctx.send("You haven't even joined this pingterest! <:pikaohh:975165648168697947>")
        else:
            await ctx.send("No name for pingterest given! <:attention:961365426091229234>")



    @commands.command(name='listmypi', aliases=['listmypis', 'listmypingterests', 'listmypingterest'])
    async def _listmypi(self, ctx, *args):
        """lists user's PI

        """
        conpi = sqlite3.connect('cogs/pingterest/pingterest.db')
        curpi = conpi.cursor()
        curpi.execute('''CREATE TABLE IF NOT EXISTS pingterests (pingterest text, userid text, username text, details text)''')
        user = ctx.message.author
        user_pis = [[item[0], item[1], item[2], item[3]] for item in curpi.execute("SELECT pingterest, userid, username, details FROM pingterests WHERE userid = ?", (str(user.id),)).fetchall()]
        
        userpistring = ""
        for pi in user_pis:
            print(str(pi))
            userpistring = userpistring + str(pi[0]) + "\n"

        titl = "pingterests of %s:" % str(user.name)
        embed = discord.Embed(title=titl, description=userpistring, color=0xFBCEB1)
        await ctx.send(embed=embed)


    @commands.command(name='listallpi', aliases=['listpi', 'listpis', 'listallpis', 'listallpingterests', 'listallpingterest'])
    async def _listpi(self, ctx, *args):
        """lists all PI

        """
        conpi = sqlite3.connect('cogs/pingterest/pingterest.db')
        curpi = conpi.cursor()
        curpi.execute('''CREATE TABLE IF NOT EXISTS pingterests (pingterest text, userid text, username text, details text)''')
        
        all_pis = [[item[0], item[1], item[2], item[3]] for item in curpi.execute("SELECT pingterest, userid, username, details FROM pingterests WHERE details = ?", ("template",)).fetchall()]
        
        allpistring = ""
        for pi in all_pis:
            print(str(pi))
            allpistring = allpistring + str(pi[0]) + "\n"

        embed = discord.Embed(title="all pingterests:", description=allpistring, color=0xFBCEB1)
        await ctx.send(embed=embed)


    @commands.command(name='clearpi', aliases=['clearpingterest'])
    @commands.has_permissions(manage_guild=True, manage_roles=True)
    @commands.check(is_valid_server)
    async def _clearpi(self, ctx, *args):
        """*removes PI

        """
        conpi = sqlite3.connect('cogs/pingterest/pingterest.db')
        curpi = conpi.cursor()
        curpi.execute('''CREATE TABLE IF NOT EXISTS pingterests (pingterest text, userid text, username text, details text)''')

        pi_name = " ".join(args).lower()
        curpi.execute("DELETE FROM pingterests WHERE pingterest = ?", (pi_name,))
        conpi.commit()
        await ctx.send("Successfully deleted this pingterest! <:smug:955227749415550996>")
    @_clearpi.error
    async def clearpi_error(ctx, error, *args):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f'Sorry, you do not have permissions to do this!')  


    @commands.command(name='clearallpi', aliases=['clearallpis', 'clearallpingterest', 'clearallpingterests'])
    @commands.has_permissions(manage_guild=True, manage_roles=True)
    @commands.check(is_valid_server)
    async def _clearallpi(self, ctx, *args):
        """*removes all PIs

        """
        conpi = sqlite3.connect('cogs/pingterest/pingterest.db')
        curpi = conpi.cursor()
        curpi.execute('''CREATE TABLE IF NOT EXISTS pingterests (pingterest text, userid text, username text, details text)''')
        curpi.execute("DELETE FROM pingterests")
        conpi.commit()
        await ctx.send("Successfully cleared the entire pingterest database! <:hellmo:954376033921040425>")
    @_clearallpi.error
    async def clearallpi_error(ctx, error, *args):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f'Sorry, you do not have permissions to do this!') 


    @commands.command(name='ping', aliases=['pingall'])
    @commands.check(is_valid_server)
    #@commands.has_permissions(manage_guild=True, manage_roles=True)
    async def _ping(self, ctx, *args):
        """*Pings members of PI

        You can use a comma to add a message to the ping, i.e. write -ping <pinterest name>, <message content>"""
        conpi = sqlite3.connect('cogs/pingterest/pingterest.db')
        curpi = conpi.cursor()
        curpi.execute('''CREATE TABLE IF NOT EXISTS pingterests (pingterest text, userid text, username text, details text)''')

        argsstring = " ".join(args).lower()

        if "," in argsstring:
            pi_name = " ".join(args).lower().split(",")[0]
            additional_msg = "\n" + " ".join(args).split(",", 1)[-1]
        else:
            pi_name = argsstring
            additional_msg = ""

        all_pis = [[item[0], item[1], item[2], item[3]] for item in curpi.execute("SELECT pingterest, userid, username, details FROM pingterests WHERE pingterest = ? AND details = ?", (pi_name,"")).fetchall()]
        
        if len(all_pis) == 0:
            await ctx.send(f"no one has said pingterest <:cryersoftheplague:969570217439137792>")
        else:
            pingmessage = "**New %s ping!**\n" % pi_name
            for pi in all_pis:
                pingmessage = pingmessage + "<@" + str(pi[1]) + "> " 

            reminder = '\n\n(If you also wish to be pinged in the future use -joinpi %s, if you no longer want to be pinged for these events use -leavepi %s)' % (pi_name, pi_name)
            await ctx.send(pingmessage + additional_msg + reminder)
    #@_ping.error
    #async def ping_error(ctx, error, *args):
    #    if isinstance(error, commands.MissingPermissions):
    #       await ctx.send(f'Sorry, you do not have permissions to do this!') 



async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(
        Pingable_Interests(bot),
        guilds = [discord.Object(id = 413011798552477716)])