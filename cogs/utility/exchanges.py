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


class Exchanges(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot


    ##################################################################################
    def derangement(self, original_list):
        n = len(original_list)

        # create list of derangement numbers
        D = []
        for z in range(n):
            Dz_value = int((math.factorial(z+1)+1)/math.e)
            D.append(Dz_value)
        print(f"D list: {D}")

        # list of ordered numbers and markings
        A = []
        mark = []
        for z in range(n):
            A.append(z+1)
            mark.append(False)

        i = n # pointer
        u = n 
        while u >= 2:
            print(f">>> u = {str(u)}")

            if not mark[i-1]:
                print(f"> Element {i} is unmarked")

                # find an unmarked j between 1 and i-1 at random
                number_of_unmarked = mark[:i-1].count(False)
                k = random.randint(1,number_of_unmarked)
                j = 0
                while k > 0:
                    j = j+1
                    if not mark[j-1]:
                        k = k-1
                print(f"randomly chosen j = {j}")

                # swap i-th and j-th entry
                x = A[i-1]
                A[i-1] = A[j-1]
                A[j-1] = x

                # randomized marking of j-th element
                p = random.uniform(0,1)
                if p < ((u-1)*D[u-3]/D[u-1]):
                    mark[j-1] = True
                    u = u-1
                u = u-1
            else:
                print(f"> Element {i} is marked")
            i = i-1

        print(f"---\npermutation finished:\n{A}")
        permutated_list = list(range(1,n+1))
        for z in range(1,n+1):
            permutated_list[z-1] = original_list[A[z-1]-1]
        #print(permutated_list)
        return permutated_list


    def permutate(self, original_list):
        n = len(original_list)

        A = list(range(1,n+1))
        B = []
        for i in list(range(1,n+1)):
            j = random.randint(1,n+1-i)
            B.append(A[j-1])
            A.remove(A[j-1])

        permutated_list = list(range(1,n+1))
        for z in range(1,n+1):
            permutated_list[z-1] = original_list[B[z-1]-1]

        return permutated_list



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



    ##################################################################################

    @commands.command(name='cycle', aliases = ['cyclepermute', "circle", "circlepermute", "cyclic", "cyclicpermute", "cyclepermutation", "circlepermutation", "cyclicpermutation"])
    async def _cycle(self, ctx: commands.Context, *args):
        """cyclic permute

        Gives out a random cyclic permutation.
        
        Arguments should be either an integer n (then you'll get a permutation of [1,2,...,n]),
        or give a list of semicolon seperated items (and you'll get a permutation of that).
        """
        if len(args) == 0:
            await ctx.send("Error, this command needs arguments. <:tigerpensive:1017483390326415410>")
        elif len(args) == 1:
            try:
                n = int(args[0])
                is_integer = True
            except:
                n = 0
                is_integer = False
                await ctx.send("Error, in case you only give 1 argument it must be an integer. <:thonkin:1017478779293147157>")

            if is_integer:
                if n <= 1:
                    await ctx.send("Preferably an integer greater than 1 please.. <:thonkin:1017478779293147157>")
                else:
                    permutated_list = self.permutate(list(range(1,n+1)))
                    permutated_list.append(permutated_list[0])

                    message = "The cycle I came up with is:\n"
                    for i in range(1,n+1):
                        message = message + f" {permutated_list[i-1]} → {permutated_list[i]} \n"

                    await ctx.send(message)

        else:
            original_list = ' '.join(args).split(";")
            n = len(original_list)

            if n <= 1:
                ctx.send("I need at least 2 arguments to properly cycle something at all. <:thonkin:1017478779293147157>\nTo separate arguments use a semicolon ; ")
            else:
                permutated_list = self.permutate(original_list)
                permutated_list.append(permutated_list[0])

                message = "The cycle I came up with is:\n"
                for i in range(1, n+1):
                    message = message + f" {permutated_list[i-1].strip()} → {permutated_list[i].strip()} \n"

                await ctx.send(message)
    
    @commands.command(name='derange', aliases = ['rearrange', "derangement"])
    async def _derange(self, ctx: commands.Context, *args):
        """no fixpoint permute

        Gives out a random fixpointless permutation, i.e. derangements.
        Needed for 'secret santa'-type events like album exchanges, where you shouldn't end up giving a present to yourself.
        
        Arguments should be either an integer n (then you'll get a derangement of [1,2,...,n]),
        or give a list of semicolon seperated items (and you'll get a derangement of that).
        """
        if len(args) == 0:
            await ctx.send("Error, this command needs arguments. <:tigerpensive:1017483390326415410>")
        elif len(args) == 1:
            try:
                n = int(args[0])
                is_integer = True
            except:
                n = 0
                is_integer = False
                await ctx.send("Error, in case you only give 1 argument it must be an integer. <:thonkin:1017478779293147157>")

            if is_integer:
                if n <= 1:
                    await ctx.send("Preferably an integer greater than 1 please.. <:thonkin:1017478779293147157>")
                else:
                    original_list = list(range(1,n+1))
                    permutated_list = self.derangement(original_list)

                    message = "The derangement I came up with is:\n"
                    for i in original_list:
                        message = message + f" {i} → {permutated_list[i-1]} \n"

                    await ctx.send(message)

        else:
            original_list = ' '.join(args).split(";")
            n = len(original_list)

            if n <= 1:
                ctx.send("I need at least 2 arguments to derange something at all. <:thonkin:1017478779293147157>\nTo separate arguments use a semicolon ; ")
            else:
                permutated_list = self.derangement(original_list)

                message = "The derangement I came up with is:\n"
                for i in range(1,n+1):
                    message = message + f" {original_list[i-1].strip()} → {permutated_list[i-1].strip()} \n"

                await ctx.send(message)



async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(
        Exchanges(bot),
        guilds = [discord.Object(id = 413011798552477716)])