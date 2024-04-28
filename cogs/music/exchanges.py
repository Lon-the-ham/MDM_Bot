import discord
from discord.ext import commands
import datetime
import pytz
from other.utils.utils import Utils as util
import os
import asyncio


class Music_Exchange(commands.Cog):
    def __init__(self, bot: commands.bot) -> None:
        self.bot = bot


    # PERMUTATION FUNCTIONS

    def derangement(self, original_list):
        """gives uniformly random permutation without identities"""

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


    def pair_mutation(self, original_list):
        n = len(original_list)
        copy = original_list

        tuple_list = []
        if n % 2 == 1:
            partner_A = copy[0]
            i = random.randint(2,len(copy))
            partner_B = copy[i-1]
            tuple_list.append([partner_A, partner_B])
            copy.remove(partner_B)

        while len(copy) > 1:
            partner_A = copy[0]
            i = random.randint(2,len(copy))
            partner_B = copy[i-1]
            tuple_list.append([partner_A, partner_B])

            copy.remove(partner_A)
            copy.remove(partner_B)

        return tuple_list



    ########################################################### COMMANDS ###########################################################################
    


    @commands.command(name='cycle', aliases = ['cyclepermute', "circle", "circlepermute", "cyclic", "cyclicpermute", "cyclepermutation", "circlepermutation", "cyclicpermutation"])
    @commands.check(util.is_active)
    async def _cycle(self, ctx: commands.Context, *args):
        """cyclic permute

        Gives out a random cyclic permutation.
        
        Arguments should be either an integer n (then you'll get a permutation of [1,2,...,n]),
        or give a list of semicolon seperated items (and you'll get a permutation of that).
        """ 
        argstring = ' '.join(args)
        if len(args) == 0:
            emoji = util.emoji("pensive2")
            await ctx.send(f"Error, this command needs arguments. {emoji}")
            return

        if len(args) == 1 and ";" not in argstring:
            try:
                n = int(args[0])
            except:
                await ctx.send("Error, in case you only give 1 argument it must be an integer.\nOtherwise arguments need to be delimited by semicolons <:thonkin:1017478779293147157>")
                return

            if n <= 1:
                emoji = util.emoji("think_smug")
                await ctx.send(f"Preferably an integer greater than 1 please.. {emoji}")
                return
            permutated_list = self.permutate(list(range(1,n+1)))
            permutated_list.append(permutated_list[0])
            message = "The cycle I came up with is:\n"
            for i in range(1,n+1):
                message = message + f" {permutated_list[i-1]} → {permutated_list[i]} \n"
            await ctx.send(message)

        else:
            original_list = ' '.join(args).split(";")
            while "" in original_list:
                original_list.remove("")
            n = len(original_list)
            try:
                duplicatecheck = len(list(dict.fromkeys(original_list)))
                if duplicatecheck == n:
                    #no duplicates
                    pass 
                else:
                    emoji = util.emoji("hmm2")
                    await ctx.send(f"Warning: There are duplicates in your list! {emoji}")
            except:
                pass 
            if n <= 1:
                emoji = util.emoji("think_smug")
                ctx.send(f"I need at least 2 arguments to properly cycle something at all. {emoji}\nTo separate arguments use a semicolon ; ")
                return

            permutated_list = self.permutate(original_list)
            permutated_list.append(permutated_list[0])
            message = "The cycle I came up with is:\n"
            for i in range(1, n+1):
                message = message + f" {permutated_list[i-1].strip()} → {permutated_list[i].strip()} \n"
            await ctx.send(message)
    @_cycle.error
    async def cycle_error(self, ctx, error):
        await util.error_handling(ctx, error)


    
    @commands.command(name='permute', aliases = ["rearrange", "derange", "derangement", "permutate", "permutation"])
    @commands.check(util.is_active)
    async def _derange(self, ctx: commands.Context, *args):
        """no fixpoint permute

        Gives out a random fixpointless permutation, i.e. derangements.
        Needed for 'secret santa'-type events like album exchanges, where you shouldn't end up giving a present to yourself.
        
        Arguments should be either an integer n (then you'll get a derangement of [1,2,...,n]),
        or give a list of semicolon seperated items (and you'll get a derangement of that).
        """
        argstring = ' '.join(args)
        if len(args) == 0:
            emoji = util.emoji("pensive2")
            await ctx.send(f"Error, this command needs arguments. {emoji}")
            return

        if len(args) == 1 and ";" not in argstring:
            try:
                n = int(args[0])
            except:
                emoji = util.emoji("think_smug")
                await ctx.send(f"Error, in case you only give 1 argument it must be an integer. {emoji}")
                return

            if n <= 1:
                emoji = util.emoji("think_smug")
                await ctx.send(f"Preferably an integer greater than 1 please.. {emoji}")
                return

            original_list = list(range(1,n+1))
            permutated_list = self.derangement(original_list)
            message = "The derangement I came up with is:\n"
            for i in original_list:
                message = message + f" {i} → {permutated_list[i-1]} \n"
            await ctx.send(message)

        else:
            original_list = ' '.join(args).split(";")
            while "" in original_list:
                original_list.remove("")
            n = len(original_list)

            try:
                duplicatecheck = len(list(dict.fromkeys(original_list)))
                if duplicatecheck == n:
                    #no duplicates
                    pass 
                else:
                    emoji = util.emoji("hmm2")
                    await ctx.send(f"Warning: There are duplicates in your list! {emoji}")
            except:
                pass

            if n <= 1:
                emoji = util.emoji("think_smug")
                await ctx.send(f"I need at least 2 arguments to derange something at all. {emoji}\nTo separate arguments use a semicolon ; ")
                return

            permutated_list = self.derangement(original_list)
            message = "The derangement I came up with is:\n"
            for i in range(1,n+1):
                message = message + f" {original_list[i-1].strip()} → {permutated_list[i-1].strip()} \n"
            await ctx.send(message)
    @_derange.error
    async def derange_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='pairs', aliases = ['pair', "pairing", "pairings"])
    @commands.check(util.is_active)
    async def _pairs(self, ctx: commands.Context, *args):
        """pairings

        Gives out a random random pairing. In case of an odd number, the first entry is paired twice.
        
        Arguments should be either an integer n (then you'll get a permutation of [1,2,...,n]),
        or give a list of semicolon seperated items (and you'll get a permutation of that).
        """ 
        argstring = ' '.join(args)
        if len(args) == 0:
            emoji = util.emoji("pensive2")
            await ctx.send(f"Error, this command needs arguments. {emoji}")
            return

        if len(args) == 1 and ";" not in argstring:
            try:
                n = int(args[0])
            except:
                await ctx.send("Error, in case you only give 1 argument it must be an integer.\nOtherwise arguments need to be delimited by semicolons <:thonkin:1017478779293147157>")
                return
            
            if n <= 1:
                emoji = util.emoji("think_smug")
                await ctx.send(f"Preferably an integer greater than 1 please.. {emoji}")
                return
            
            pairs_list = self.pair_mutation(list(range(1,n+1)))
            message = "The pairing I came up with is:\n"
            for i in range(1,len(pairs_list)+1):
                message = message + f" {pairs_list[i-1][0]} ↔ {pairs_list[i-1][1]} \n"
            await ctx.send(message)

        else:
            original_list = ' '.join(args).split(";")
            while "" in original_list:
                original_list.remove("")
            n = len(original_list)

            if n <= 1:
                emoji = util.emoji("think_smug")
                await ctx.send(f"I need at least 2 arguments to properly cycle something at all. {emoji}\nTo separate arguments use a semicolon ; ")
                return
            duplicatecheck = len(list(dict.fromkeys(original_list)))
            if duplicatecheck != n:
                emoji = util.emoji("hmm2")
                await ctx.send(f"Error: There are duplicates in your list! {emoji}\nIn case you have an uneven number of members, put the one you want to pair twice at the beginning!")
                return

            #no duplicates
            pairs_list = self.pair_mutation(original_list)
            message = "The pairing I came up with is:\n"
            for i in range(1,len(pairs_list)+1):
                message = message + f" {pairs_list[i-1][0]} ↔ {pairs_list[i-1][1]} \n"
            await ctx.send(message)
    @_pairs.error
    async def pairs_error(self, ctx, error):
        await util.error_handling(ctx, error)


    ####################################################################################

    @commands.command(name='countdown', aliases = ['cd'])
    @commands.check(util.is_active)
    async def _cd(self, ctx, *args):
        """Starts countdown

        You can specify an integer from 1 to 10 from which the bot will count downwards.
        Commands without an argument start from 5.

        (Note that this command does not count down exact seconds, but rather something close to 1.2 seconds per number)
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
        await asyncio.sleep(1)
        for i in range(cdtime,-1,-1):
            await asyncio.sleep(1.2)
            if (i > 0):
                await ctx.send(f'`{i}`')
            else:
                await ctx.send('`0` :tada:')  
    @_cd.error
    async def cd_error(self, ctx, error):
        await util.error_handling(ctx, error) 



async def setup(bot: commands.bot) -> None:
    await bot.add_cog(
        Music_Exchange(bot),
        guilds = [discord.Object(id = int(os.getenv("guild_id")))])