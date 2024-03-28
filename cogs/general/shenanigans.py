import discord
from discord.ext import commands
import datetime
import pytz
from other.utils.utils import Utils as util
import os
import random
import sqlite3


class Shenanigans(commands.Cog):
    def __init__(self, bot: commands.bot) -> None:
        self.bot = bot



    @commands.command(name='sudo', aliases = ['please', 'pls'])
    async def _sudo(self, ctx: commands.Context, *args):
        """sudo"""

        conSH = sqlite3.connect('databases/shenanigans.db')
        curSH = conSH.cursor()

        comstring = ' '.join(args).lower()
        possible_outcomes = [[item[0],item[1]] for item in curSH.execute("SELECT response1, response2 FROM sudo WHERE command = ?", (comstring,)).fetchall()]
            
        if len(possible_outcomes) == 0:
            await ctx.send("Sorry. Not in the mood.")
            return

        r = random.randint(0,len(possible_outcomes)-1)

        message1 = await util.customtextparse(possible_outcomes[r][0], str(ctx.author.id))
        message2 = await util.customtextparse(possible_outcomes[r][1], str(ctx.author.id))
        message_sent = False

        if message1.strip() != "":
            await ctx.send(message1)
            message_sent = True

        if message2.strip() != "":
            await ctx.send(message2)
            message_sent = True

        if not message_sent:
            await ctx.send("Mhm yeah, not today.")
            return



    @commands.command(name='inspire', aliases = ['inspiration'])
    async def _inspire(self, ctx: commands.Context, *args):
        """quote that may or may not be inspiring"""

        conSH = sqlite3.connect('databases/shenanigans.db')
        curSH = conSH.cursor()

        possible_outcomes = [[item[0],item[1],item[2]] for item in curSH.execute("SELECT quote, author, link FROM inspire").fetchall()]

        if len(possible_outcomes) == 0:
            await ctx.send("Sorry. I am not inspired.")
            return

        r = random.randint(0,len(possible_outcomes)-1)
        
        quote = possible_outcomes[r][0]
        author = possible_outcomes[r][1]
        link = possible_outcomes[r][2]

        if str(link).startswith("https:") or str(link).startswith("www."):
            is_url = True
        else:
            is_url = False

        if quote.strip() == "":
            await ctx.send("Mhm yeah, not today.")
            return

        text = await util.customtextparse(quote, str(ctx.author.id))
        text = "*" + util.cleantext2(text) + "*"

        if author.strip() != "":
            text += "\n-"

            if is_url:
                text += "["

            text += author.strip()

            if is_url:
                text += f"]({link.strip()})"


        if link.strip() != "" and not is_url:
            text += f" ({link})"

        embed=discord.Embed(title="", description=text, color=0x63c5da)
        await ctx.send(embed=embed)




    @commands.command(name='mrec', aliases = ['memerec', 'memerecommendation'])
    async def _rec(self, ctx, *args):
        """great recommendation"""

        conSH = sqlite3.connect('databases/shenanigans.db')
        curSH = conSH.cursor()

        comstring = ''.join(args).lower()

        if comstring.strip() != "":
            possible_outcomes = [item[0] for item in curSH.execute("SELECT link FROM mrec WHERE subcommand = ? or alias = ?", (comstring, comstring)).fetchall()]
        else:
            possible_subcommands = [item[0] for item in curSH.execute("SELECT subcommand FROM mrec").fetchall()]
            possible_subcommands = list(dict.fromkeys(possible_subcommands))
            r = random.randint(0,len(possible_subcommands)-1)
            subcommand = possible_subcommands[r]
            possible_outcomes = [item[0] for item in curSH.execute("SELECT link FROM mrec WHERE subcommand = ?", (subcommand,)).fetchall()]

        if len(possible_outcomes) == 0:
            await ctx.send("Sorry. Nothing to recommend.")
            return

        r = random.randint(0,len(possible_outcomes)-1)
        url = possible_outcomes[r]
        emoji = util.emoji("giggle")
        await ctx.send(f'I think you will enjoy this! {emoji}\n{url}')  



async def setup(bot: commands.bot) -> None:
    await bot.add_cog(
        Shenanigans(bot),
        guilds = [discord.Object(id = int(os.getenv("guild_id")))])