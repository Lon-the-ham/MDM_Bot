import os
import datetime
import discord
from discord.ext import commands
import sqlite3



class OtherEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_typing(self, channel, user, when):
        #print(f"{user} is typing message in {channel} {when}")
        if user.id == 273219981465092096:
            # ddouble is typing
            print(f"{user} is typing in #{channel} {when}")
            ddouble_thread = self.bot.get_channel(1074837328226435143)
            await ddouble_thread.send(f"{user} is typing message in #{channel} {when}")


    @commands.Cog.listener()
    async def on_message(self, message):
        alphabeticonly = ''.join(x for x in message.content if x.isalpha()).lower()
        if "modsmodsmods" in alphabeticonly:
            # notify if someone wrote MODS MODS MODS or similar
            botspamchannel = self.bot.get_channel(416384984597790750)
            #await botspamchannel.send(f'<@&957253036609249363> mods were called :eyes:\n{message.jump_url}')
            await botspamchannel.send(f'Mods were called :eyes:\n{message.jump_url}')
            await message.add_reaction("👀")

    


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(
        OtherEvents(bot),
        guilds = [discord.Object(id = 413011798552477716)])