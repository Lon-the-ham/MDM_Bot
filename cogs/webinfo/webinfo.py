import discord
from discord.ext import commands
import re
import datetime
import sys
import requests
import json
from bs4 import BeautifulSoup
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


    def convert_urltype_string(self, primary_input):
        search_term = primary_input.replace(" ","+")
        return search_term

    def unicoder(self, string_a):
        string_b = string_a.encode().decode("unicode-escape")
        return string_b

    def alphanum_filter(self, string_a):
        string_b = ''.join(ch for ch in string_a if ch.isalnum())
        return string_b


    async def fetch_bandinfo(self, ctx, band_link, band_aka):
        session = requests.session()
        burp0_headers = {"Upgrade-Insecure-Requests": "1", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.5481.78 Safari/537.36", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7", "Accept-Encoding": "gzip, deflate", "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7"}
        band_response = session.get(band_link, headers=burp0_headers)

        # PARSE BAND INFO FROM HTML

        soup = BeautifulSoup(band_response.text, "html.parser")

        country = soup.find(string='Country of origin:').findNext('a').text.strip()
        print(country)
        location = soup.find(string='Location:').findNext('dd').text.strip()
        print(location)
        status = soup.find(string='Status:').findNext('dd').text.strip()
        print(status)
        formed = soup.find(string='Formed in:').findNext('dd').text.strip()
        print(formed)

        genre = soup.find(string='Genre:').findNext('dd').text.strip()
        print(genre)
        themes = soup.find(string='Themes:').findNext('dd').text.strip()
        print(themes)
        c_label = soup.find(string='Current label:').findNext('dd').text.strip()
        print(c_label)
        yearsactive = soup.find(string='Years active:').findNext('dd').text.strip()
        print(yearsactive)


        page_scriptinfo = soup.find_all("script")
        parse_scriptinfo = ""
        for item in page_scriptinfo:
            parse_scriptinfo += str(item).replace("\n","")
        parse_idinfo = parse_scriptinfo.split("var bandId = ",1)[1]
        band_id = parse_idinfo.split(";",1)[0].strip()
        parse_nameinfo = parse_scriptinfo.split("var bandName = ",1)[1]
        band_name = self.unicoder(parse_nameinfo.split(";",1)[0].replace('"','').strip())

        print(band_id)
        print(band_name)

        #page_imginfo = soup.find_all("img")
        try:
            img_links = []
            for img in soup.find_all('img', src=True):
                img_links.append(img['src'])

            #for link in imglinks:
            #    if "logo" in str(link):
            #        picture_url = str(link)
            #        break
            #else:
            #    picture_url = "https://i.imgur.com/pVLH6Q0.png"

            picture_url = img_links[1]
        except:
            picture_url = "https://i.imgur.com/LzLSFCG.png"
        print(picture_url)
    

        # SENDING MESSAGE

        if band_aka == "":
            aka = ""
        else:
            aka = f"(a.k.a. {self.unicoder(band_aka)})"

        embed=discord.Embed(title = band_name, description=aka, url=band_link, color=0x1b0000)

        #embed.set_author(name=band_name,icon_url=picture_url)
        #embed.add_field(name="Country of origin:", value=country, inline=False)
        embed.set_thumbnail(url=picture_url)
        embed.add_field(name="Geography:", value=f"country of origin: {country}\nlocation: {location}", inline=False)
        embed.add_field(name="Genre:", value=genre, inline=False)
        embed.add_field(name="Themes:", value=themes, inline=False)
        embed.set_footer(text=f"{yearsactive}, current status: {status}")
        message = await ctx.send(embed=embed)



    @commands.command(name='ma', aliases = ['metallum', 'metal', "metalarchives"])
    async def _metallum(self, ctx: commands.Context, *args):
        """Metallum info

        """
        # search request
        input_string = ' '.join(args)
        async with ctx.typing():
            if ";" in input_string:
                primaryinput = input_string.split(";",1)[0].strip()
                specification = input_string.split(";",1)[1].strip()
            else:
                primaryinput = input_string
                specification = ""

            searchterm = self.convert_urltype_string(primaryinput)

            try:
                session = requests.session()
                burp0_url = f"https://www.metal-archives.com:443/search/ajax-band-search/?field=name&query={searchterm}&sEcho=1&iColumns=3&sColumns=&iDisplayStart=0&iDisplayLength=200&mDataProp_0=0&mDataProp_1=1&mDataProp_2=2"
                burp0_headers = {"Sec-Ch-Ua": "\"Not A(Brand\";v=\"24\", \"Chromium\";v=\"110\"", "Accept": "application/json, text/javascript, */*; q=0.01", "X-Requested-With": "XMLHttpRequest", "Sec-Ch-Ua-Mobile": "?0", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.5481.78 Safari/537.36", "Sec-Ch-Ua-Platform": "\"Windows\"", "Sec-Fetch-Site": "same-origin", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Dest": "empty", "Referer": "https://www.metal-archives.com/search?searchString=baa+rhythm&type=band_name", "Accept-Encoding": "gzip, deflate", "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7"}
                response = session.get(burp0_url, headers=burp0_headers)

                aa_items = json.loads(response.text)["aaData"]

                # parse band link, or disambiguation list

                if len(aa_items) == 0:
                    await ctx.channel.send(f'Could not find band with such a name on the Metal Archives. <:penguinshy:1017439941074100344>')

                elif len(aa_items) == 1:
                    try:
                        smolsoup = BeautifulSoup(str(aa_items), "html.parser")

                        band_link = ""
                        for a in smolsoup.find_all('a', href=True):
                            band_link = a['href']

                        try:
                            band_aka = response.text.split("<strong>a.k.a.</strong>")[1].split(")")[0].strip()
                        except:
                            band_aka = ""

                        await self.fetch_bandinfo(ctx, band_link, band_aka)

                    except Exception as e:
                        await ctx.channel.send(f'Error while fetching redirect:\n{e}')

                else:
                    #await ctx.channel.send(f'Found {len(aa_items)} entries.')
                    parsed_items = []
                    for item in aa_items:
                        genre = item[1]
                        country = item[2]

                        smolsoup = BeautifulSoup(str(item[0]), "html.parser")
                        band_link = ""
                        for a in smolsoup.find_all('a', href=True):
                            band_link = a['href']

                        try:
                            band_aka = str(item[0]).split("<strong>a.k.a.</strong>")[1].split(")")[0].strip()
                        except:
                            band_aka = ""

                        band_name = smolsoup.find('a', href=True).text

                        parsed_items.append([band_link, band_name, band_aka, genre, country])


                    match_counter_exact = 0
                    match_counter_aka = 0
                    match_counter_alphanum = 0 
                    match_counter_aka_alphanum = 0
                    list_match_exact = []
                    list_match_aka = []
                    list_match_alphanum = []
                    list_match_aka_alphanum = []

                    for item in parsed_items:
                        band_link = item[0]
                        band_name = item[1]
                        band_akass = item[2].split(",")

                        sl = searchterm.lower()
                        slf = self.alphanum_filter(sl)

                        if band_name.lower() == sl:
                            match_counter_exact += 1
                            list_match_exact.append(item)
                        if self.alphanum_filter(band_name.lower()) == slf:
                            match_counter_alphanum += 1
                            list_match_alphanum.append(item)

                        for band_aka in band_akass:   
                            if band_aka.lower().strip() == sl:
                                match_counter_aka += 1
                                list_match_aka.append(item)  
                            if self.alphanum_filter(band_aka.lower()) == slf:
                                match_counter_aka_alphanum += 1
                                list_match_aka_alphanum.append(item)                           

                    if match_counter_exact == 1:
                        band_link = list_match_exact[0][0]
                        band_aka = list_match_exact[0][1]
                        await self.fetch_bandinfo(ctx, band_link, band_aka)
                    else:
                        if match_counter_aka == 1:
                            band_link = list_match_aka[0][0]
                            band_aka = list_match_aka[0][1]
                            await self.fetch_bandinfo(ctx, band_link, band_aka)
                        else:
                            if match_counter_alphanum == 1:
                                band_link = list_match_alphanum[0][0]
                                band_aka = list_match_alphanum[0][1]
                                await self.fetch_bandinfo(ctx, band_link, band_aka)
                            else:
                                if match_counter_aka_alphanum == 1:
                                    band_link = list_match_aka_alphanum[0][0]
                                    band_aka = list_match_aka_alphanum[0][1]
                                    await self.fetch_bandinfo(ctx, band_link, band_aka)
                                else:
                                    
                                    # MAKE A LIST OF ALL ENTRIES
                                    message_parts = [""]
                                    i = 0
                                    k = 0
                                    for item in parsed_items:
                                        i += 1
                                        band_link = item[0]
                                        band_name = item[1]
                                        band_aka = item[2]
                                        genre = item[3]
                                        country = item[4]

                                        if band_aka.strip() == "":
                                            aka = ""
                                        else:
                                            aka = f"(a.k.a. {band_aka}) "

                                        msg = message_parts[k]
                                        nextline = f"{i}. [{band_name}]({band_link}) {aka} `{genre}`  {country}\n"

                                        if len(msg)+len(nextline) > 4000:
                                            k += 1
                                            message_parts.append(nextline)
                                        else:
                                            message_parts[k] = msg + nextline

                                    j = 0 
                                    n = len(message_parts)
                                    for message in message_parts:
                                        j += 1
                                        title = f"Search results: {searchterm} ({j}/{n})"
                                        embed=discord.Embed(title = title, description=message, color=0x1b0000)
                                        message = await ctx.send(embed=embed)
            except Exception as e:
                await ctx.channel.send(f'Error while fetching search term:\n{e}')

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