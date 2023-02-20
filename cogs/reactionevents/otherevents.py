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
        global last_ddouble_instance
        if user.id == 273219981465092096:
            # ddouble is typing
            try: 
                last_ddouble_instance
            except:
                last_ddouble_instance = 0
            now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())

            print(f"{user} is typing in #{channel} {when}")
            if now <= last_ddouble_instance + 5*60:
                pass
            else:
                try:
                    settings = []
                    print('+++ settings: +++')
                    with open('cogs/settings/default_settings.txt', 'r') as s:
                        for line in s:
                            print(line.strip())
                            settings.append(line.strip())
                    print('--- ---')

                    for s in settings:
                        if ":" in s:
                            parameter = s.split(":",1)[0].strip().lower()
                            value = s.split(":",1)[1].strip()
                            #print(f"parameter: {parameter}; value: {value}")

                            if parameter in ['tracking']:
                                if value.lower() in ['on', 'yes']:
                                    last_ddouble_instance = now
                                    ddouble_thread = self.bot.get_channel(1074837328226435143)
                                    await ddouble_thread.send(f"{user} is typing in #{channel}\n<:shakingfrogeyes:975566875050262628> {when}")
                                else:
                                    print("tracking off")
                except Exception as e:
                    print(e)

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