import discord
from discord.ext import commands
import re
import datetime
import sys
import requests
#from bs4 import BeautifulSoup
#from selenium import webdriver
#from selenium.webdriver.firefox.options import Options as FirefoxOptions
#from webdriver_manager.firefox import GeckoDriverManager


class WebInfo(commands.Cog):
    def __init__(self, bot: commands.bot) -> None:
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
        

    @commands.command(name='metallum', aliases = ['ma', 'metal'])
    async def _metallum(self, ctx: commands.Context, *args):
        """Metallum info

        """
        try:
            options = FirefoxOptions()
            #options.add_argument("--headless")
            #options.add_argument("--no-sandbox")
            # browser is Chromium instead of Chrome
            driver = webdriver.Firefox(executable_path=GeckoDriverManager().install())

            band_lookup = ' '.join(args).replace(" ","_")

            try:
                search_url = f'https://www.metal-archives.com/bands/{band_lookup}'
                await ctx.channel.send(f'In construction')
                #driver.get(search_url)
                #page_title = driver.title.strip()
                #print(page_title)
                #content = driver.page_source
                #soup = BeautifulSoup(content, "html.parser")

                #if #page_title.endswith("- Encyclopaedia Metallum"):
                    #bandname = page_title.split("-")[0].strip()
                    #is_a_bandpage = True
                #else:
                    #bandname = page_title
                    #is_a_bandpage = False

                #if is_a_bandpage:
                    #country = soup.find(string='Country of origin:').findNext('a').text
                    #location = soup.find(string='Location:').findNext('dd').text
                    #status = soup.find(string='Status:').findNext('dd').text
                    #formed = soup.find(string='Formed in:').findNext('dd').text
                    #genre = soup.find(string='Genre:').findNext('dd').text
                    #themes = soup.find(string='Themes:').findNext('dd').text
                    #c_label = soup.find(string='Current label:').findNext('dd').text
                    #yearsactive = soup.find(string='Years active:').findNext('dd').text

                    #msg2 = f"*Country of origin:* {country}"
                    #msg2 += f"*Location:* {location}"
                    #msg2 += f"*Status:* {status}"
                    #msg2 += f"*Formed in:* {formed}"
                    #msg2 += f"*Years active:* {yearsactive}"

                    #msg3 = f"*Genre:* {genre}"
                    #msg3 += f"*Themes:* {themes}"
                    #msg3 += f"*Current label:* {c_label}"

                    #msg = ""

                    #embed=discord.Embed(title=f"{bandname}", desciption = msg, color=0x964B00)
                    #embed.add_field(name="", value=msg2, inline=True)
                    #embed.add_field(name="", value=msg3, inline=True)

                    # to get albums f"https://www.metal-archives.com/band/discography/id/{bandid}/tab/all"

            except:
                await ctx.channel.send(f'Could not load page. <:piplupdisappointed:975461498702921778>')
        except Exception as e:
            await ctx.channel.send(f'An error occured.\n{e}')
            print(e)
    @_metallum.error
    async def metallum_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f'Sorry, you do not have permissions to do this!')
        elif isinstance(error, commands.CheckFailure):
            await ctx.channel.send(f'Error: This is a melodeathcord specific command.')
        else:
            await ctx.channel.send(f'An error ocurred.')





async def setup(bot: commands.bot) -> None:
    await bot.add_cog(
        WebInfo(bot),
        guilds = [discord.Object(id = 413011798552477716)])