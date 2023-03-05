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
import asyncio


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

    def utf8_decode(self, string_a):
        string_b = string_a.encode('latin1').decode()
        return string_b

    def alphanum_filter(self, string_a):
        string_b = ''.join(ch for ch in string_a if ch.isalnum())
        return string_b

    def country_abbr(self, cstr):
        countries = [['Afghanistan', '🇦🇫', 'AF'], ['Åland Islands', '🇦🇽', 'AX'], ['Albania', '🇦🇱', 'AL'], ['Algeria', '🇩🇿', 'DZ'], ['American Samoa', '🇦🇸', 'AS'], ['Andorra', '🇦🇩', 'AD'], ['Angola', '🇦🇴', 'AO'], ['Anguilla', '🇦🇮', 'AI'], ['Antarctica', '🇦🇶', 'AQ'], ['Antigua and Barbuda', '🇦🇬', 'AG'], ['Argentina', '🇦🇷', 'AR'], ['Armenia', '🇦🇲', 'AM'], ['Aruba', '🇦🇼', 'AW'], ['Australia', '🇦🇺', 'AU'], ['Austria', '🇦🇹', 'AT'], ['Azerbaijan', '🇦🇿', 'AZ'], ['Bahamas', '🇧🇸', 'BS'], ['Bahrain', '🇧🇭', 'BH'], ['Bangladesh', '🇧🇩', 'BD'], ['Barbados', '🇧🇧', 'BB'], ['Belarus', '🇧🇾', 'BY'], ['Belgium', '🇧🇪', 'BE'], ['Belize', '🇧🇿', 'BZ'], ['Benin', '🇧🇯', 'BJ'], ['Bermuda', '🇧🇲', 'BM'], ['Bhutan', '🇧🇹', 'BT'], ['Bolivia', '🇧🇴', 'BO'], ['Bonaire, Sint Eustatius and Saba', '🇧🇶', 'BQ'], ['Bosnia and Herzegovina', '🇧🇦', 'BA'], ['Botswana', '🇧🇼', 'BW'], ['Bouvet Island', '🇧🇻', 'BV'], ['Brazil', '🇧🇷', 'BR'], ['British Indian Ocean Territory', '🇮🇴', 'IO'], ['Brunei', '🇧🇳', 'BN'], ['Bulgaria', '🇧🇬', 'BG'], ['Burkina Faso', '🇧🇫', 'BF'], ['Burundi', '🇧🇮', 'BI'], ['Cambodia', '🇰🇭', 'KH'], ['Cameroon', '🇨🇲', 'CM'], ['Canada', '🇨🇦', 'CA'], ['Cape Verde', '🇨🇻', 'CV'], ['Cayman Islands', '🇰🇾', 'KY'], ['Central African Republic', '🇨🇫', 'CF'], ['Chad', '🇹🇩', 'TD'], ['Chile', '🇨🇱', 'CL'], ['China', '🇨🇳', 'CN'], ['Christmas Island', '🇨🇽', 'CX'], ['Cocos (Keeling) Islands', '🇨🇨', 'CC'], ['Colombia', '🇨🇴', 'CO'], ['Comoros', '🇰🇲', 'KM'], ['Congo, Democratic Republic of', '🇨🇩', 'CD'], ['Congo, Republic of', '🇨🇬', 'CG'], ['Cook Islands', '🇨🇰', 'CK'], ['Costa Rica', '🇨🇷', 'CR'], ["Côte d'Ivoire", '🇨🇮', 'CI'], ['Croatia', '🇭🇷', 'HR'], ['Cuba', '🇨🇺', 'CU'], ['Curaçao', '🇨🇼', 'CW'], ['Cyprus', '🇨🇾', 'CY'], ['Czechia', '🇨🇿', 'CZ'], ['Denmark', '🇩🇰', 'DK'], ['Djibouti', '🇩🇯', 'DJ'], ['Dominica', '🇩🇲', 'DM'], ['Dominican Republic', '🇩🇴', 'DO'], ['East Timor', '🇹🇱', 'TL'], ['Ecuador', '🇪🇨', 'EC'], ['Egypt', '🇪🇬', 'EG'], ['El Salvador', '🇸🇻', 'SV'], ['Equatorial Guinea', '🇬🇶', 'GQ'], ['Eritrea', '🇪🇷', 'ER'], ['Estonia', '🇪🇪', 'EE'], ['Eswatini', '🇸🇿', 'SZ'], ['Ethiopia', '🇪🇹', 'ET'], ['Falkland Islands', '🇫🇰', 'FK'], ['Faroe Islands', '🇫🇴', 'FO'], ['Fiji', '🇫🇯', 'FJ'], ['Finland', '🇫🇮', 'FI'], ['France', '🇫🇷', 'FR'], ['French Guiana', '🇬🇫', 'GF'], ['French Polynesia', '🇵🇫', 'PF'], ['French Southern Territories', '🇹🇫', 'TF'], ['Gabon', '🇬🇦', 'GA'], ['Gambia', '🇬🇲', 'GM'], ['Georgia', '🇬🇪', 'GE'], ['Germany', '🇩🇪', 'DE'], ['Ghana', '🇬🇭', 'GH'], ['Gibraltar', '🇬🇮', 'GI'], ['Greece', '🇬🇷', 'GR'], ['Greenland', '🇬🇱', 'GL'], ['Grenada', '🇬🇩', 'GD'], ['Guadeloupe', '🇬🇵', 'GP'], ['Guam', '🇬🇺', 'GU'], ['Guatemala', '🇬🇹', 'GT'], ['Guernsey', '🇬🇬', 'GG'], ['Guinea', '🇬🇳', 'GN'], ['Guinea-Bissau', '🇬🇼', 'GW'], ['Guyana', '🇬🇾', 'GY'], ['Haiti', '🇭🇹', 'HT'], ['Heard and McDonald Islands', '🇭🇲', 'HM'], ['Honduras', '🇭🇳', 'HN'], ['Hong Kong', '🇭🇰', 'HK'], ['Hungary', '🇭🇺', 'HU'], ['Iceland', '🇮🇸', 'IS'], ['India', '🇮🇳', 'IN'], ['Indonesia', '🇮🇩', 'ID'], ['International', '🇺🇳', 'i'], ['Iran', '🇮🇷', 'IR'], ['Iraq', '🇮🇶', 'IQ'], ['Ireland', '🇮🇪', 'IE'], ['Isle of Man', '🇮🇲', 'IM'], ['Israel', '🇮🇱', 'IL'], ['Italy', '🇮🇹', 'IT'], ['Jamaica', '🇯🇲', 'JM'], ['Japan', '🇯🇵', 'JP'], ['Jersey', '🇯🇪', 'JE'], ['Jordan', '🇯🇴', 'JO'], ['Kazakhstan', '🇰🇿', 'KZ'], ['Kenya', '🇰🇪', 'KE'], ['Kiribati', '🇰🇮', 'KI'], ['Korea, North', '🇰🇵', 'KP'], ['Korea, South', '🇰🇷', 'KR'], ['Kuwait', '🇰🇼', 'KW'], ['Kyrgyzstan', '🇰🇬', 'KG'], ['Laos', '🇱🇦', 'LA'], ['Latvia', '🇱🇻', 'LV'], ['Lebanon', '🇱🇧', 'LB'], ['Lesotho', '🇱🇸', 'LS'], ['Liberia', '🇱🇷', 'LR'], ['Libya', '🇱🇾', 'LY'], ['Liechtenstein', '🇱🇮', 'LI'], ['Lithuania', '🇱🇹', 'LT'], ['Luxembourg', '🇱🇺', 'LU'], ['Macau', '🇲🇴', 'MO'], ['Madagascar', '🇲🇬', 'MG'], ['Malawi', '🇲🇼', 'MW'], ['Malaysia', '🇲🇾', 'MY'], ['Maldives', '🇲🇻', 'MV'], ['Mali', '🇲🇱', 'ML'], ['Malta', '🇲🇹', 'MT'], ['Marshall Islands', '🇲🇭', 'MH'], ['Martinique', '🇲🇶', 'MQ'], ['Mauritania', '🇲🇷', 'MR'], ['Mauritius', '🇲🇺', 'MU'], ['Mayotte', '🇾🇹', 'YT'], ['Mexico', '🇲🇽', 'MX'], ['Micronesia, Federated States of', '🇫🇲', 'FM'], ['Moldova', '🇲🇩', 'MD'], ['Monaco', '🇲🇨', 'MC'], ['Mongolia', '🇲🇳', 'MN'], ['Montenegro', '🇲🇪', 'ME'], ['Montserrat', '🇲🇸', 'MS'], ['Morocco', '🇲🇦', 'MS'], ['Mozambique', '🇲🇿', 'MZ'], ['Myanmar', '🇲🇲', 'MM'], ['Namibia', '🇳🇦', 'NA'], ['Nauru', '🇳🇷', 'NR'], ['Nepal', '🇳🇵', 'NP'], ['Netherlands', '🇳🇱', 'NL'], ['New Caledonia', '🇳🇨', 'NC'], ['New Zealand', '🇳🇿', 'NZ'], ['Nicaragua', '🇳🇮', 'NI'], ['Niger', '🇳🇪', 'NE'], ['Nigeria', '🇳🇬', 'NG'], ['Niue', '🇳🇺', 'NU'], ['Norfolk Island', '🇳🇫', 'NF'], ['North Macedonia', '🇲🇰', 'MK'], ['Northern Mariana Islands', '🇲🇵', 'MP'], ['Norway', '🇳🇴', 'NO'], ['Oman', '🇴🇲', 'OM'], ['Pakistan', '🇵🇰', 'PK'], ['Palau', '🇵🇼', 'PW'], ['Palestine', '🇵🇸', 'PS'], ['Panama', '🇵🇦', 'PA'], ['Papua New Guinea', '🇵🇬', 'PG'], ['Paraguay', '🇵🇾', 'PY'], ['Peru', '🇵🇪', 'PE'], ['Philippines', '🇵🇭', 'PH'], ['Pitcairn Island', '🇵🇳', 'PN'], ['Poland', '🇵🇱', 'PL'], ['Portugal', '🇵🇹', 'PT'], ['Puerto Rico', '🇵🇷', 'PR'], ['Qatar', '🇶🇦', 'QA'], ['Reunion', '🇷🇪', 'RE'], ['Romania', '🇷🇴', 'RO'], ['Russia', '🇷🇺', 'RU'], ['Rwanda', '🇷🇼', 'RW'], ['Saint Barthélemy', '🇧🇱', 'BL'], ['Saint Kitts & Nevis', '🇰🇳', 'KN'], ['Saint Lucia', '🇱🇨', 'LC'], ['Saint Martin (French part)', '🇲🇫', 'MF'], ['Saint Pierre and Miquelon', '🇵🇲', 'PM'], ['Saint Vincent and The Grenadines', '🇻🇨', 'VC'], ['Samoa', '🇼🇸', 'WS'], ['San Marino', '🇸🇲', 'SM'], ['Sao Tome and Principe', '🇸🇹', 'ST'], ['Saudi Arabia', '🇸🇦', 'SA'], ['Senegal', '🇸🇳', 'SN'], ['Serbia', '🇷🇸', 'RS'], ['Seychelles', '🇸🇨', 'SC'], ['Sierra Leone', '🇸🇱', 'SL'], ['Singapore', '🇸🇬', 'SG'], ['Sint Maarten (Dutch part)', '🇸🇽', 'SX'], ['Slovakia', '🇸🇰', 'SK'], ['Slovenia', '🇸🇮', 'SI'], ['Solomon Islands', '🇸🇧', 'SB'], ['Somalia', '🇸🇴', 'SO'], ['South Africa', '🇿🇦', 'ZA'], ['South Georgia & South Sandwich Islands', '🇬🇸', 'GS'], ['South Sudan', '🇸🇸', 'SS'], ['Spain', '🇪🇸', 'ES'], ['Sri Lanka', '🇱🇰', 'LK'], ['St Helena, Ascension & Tristan da Cunha', '🇸🇭', 'SH'], ['Sudan', '🇸🇩', 'SD'], ['Suriname', '🇸🇷', 'SR'], ['Svalbard', '🇸🇯', 'SJ'], ['Sweden', '🇸🇪', 'SE'], ['Switzerland', '🇨🇭', 'CH'], ['Syria', '🇸🇾', 'SY'], ['Taiwan', '🇹🇼', 'TW'], ['Tajikistan', '🇹🇯', 'TJ'], ['Tanzania', '🇹🇿', 'TZ'], ['Thailand', '🇹🇭', 'TH'], ['Togo', '🇹🇬', 'TG'], ['Tokelau', '🇹🇰', 'TK'], ['Tonga', '🇹🇴', 'TO'], ['Trinidad and Tobago', '🇹🇹', 'TT'], ['Tunisia', '🇹🇳', 'TN'], ['Türkiye', '🇹🇷', 'TR'], ['Turkmenistan', '🇹🇲', 'TM'], ['Turks and Caicos Islands', '🇹🇨', 'TC'], ['Tuvalu', '🇹🇻', 'TV'], ['U.S. Minor Outlying Islands', '🇺🇲', 'UM'], ['Uganda', '🇺🇬', 'UG'], ['Ukraine', '🇺🇦', 'UA'], ['United Arab Emirates', '🇦🇪', 'AE'], ['United Kingdom', '🇬🇧', 'GB'], ['United States', '🇺🇸', 'US'], ['Unknown', '❓', '??'], ['Uruguay', '🇺🇾', 'UY'], ['Uzbekistan', '🇺🇿', 'UZ'], ['Vanuatu', '🇻🇺', 'VU'], ['Vatican City', '🇻🇦', 'VA'], ['Venezuela', '🇻🇪', 'VE'], ['Vietnam', '🇻🇳', 'VN'], ['Virgin Islands (British)', '🇻🇬', 'VG'], ['Virgin Islands (US)', '🇻🇮', 'VI'], ['Wallis and Futuna', '🇼🇫', 'WF'], ['Western Sahara', '🇪🇭', 'EH'], ['Yemen', '🇾🇪', 'YE'], ['Zambia', '🇿🇲', 'ZM'], ['Zimbabwe', '🇿🇼', 'ZW'], ['Kosovo', '🇽🇰', 'XK'], ['England', '🏴󠁧󠁢󠁥󠁮󠁧󠁿', 'GB-ENG'], ['Scotland', '🏴󠁧󠁢󠁳󠁣󠁴󠁿', 'GB-SCT'], ['Wales', '🏴󠁧󠁢󠁷󠁬󠁳󠁿', 'GB-CYM'], ['Northern Ireland', '🏴󠁧󠁢󠁮󠁩󠁲󠁿', 'GB-NIR'], ['Europe', '🇪🇺', 'EU']]
        for country in countries:
            if cstr.lower() == country[0].lower():
                emoji = country[1]
                abbr = country[2]
                break
        else:
            emoji = "?"
            abbr = "?"
        return [emoji, abbr]


    async def fetch_bandinfo(self, ctx, band_link, band_aka):
        async with ctx.typing():
            session = requests.session()
            burp0_headers = {"Upgrade-Insecure-Requests": "1", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.5481.78 Safari/537.36", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7", "Accept-Encoding": "gzip, deflate", "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7"}
            band_response = session.get(band_link, headers=burp0_headers)

            # PARSE BAND INFO FROM HTML

            soup = BeautifulSoup(band_response.text, "html.parser")

            try:
                country = soup.find(string='Country of origin:').findNext('a').text.strip()
            except:
                country = "?"
            print(country)
            try:
                location = soup.find(string='Location:').findNext('dd').text.strip()
            except:
                location = "?"
            print(location)
            try:
                status = soup.find(string='Status:').findNext('dd').text.strip()
            except:
                status = "?"
            print(status)
            try:
                formed = soup.find(string='Formed in:').findNext('dd').text.strip()
            except:
                formed = "?"
            print(formed)

            try:
                genre = soup.find(string='Genre:').findNext('dd').text.strip()
            except:
                genre = "?"
            print(genre)
            try:
                themes = soup.find(string='Themes:').findNext('dd').text.strip()
            except:
                themes = "?"
            print(themes)
            try:
                c_label = soup.find(string='Current label:').findNext('dd').text.strip()
            except:
                c_label = "?"
            print(c_label)
            try:
                yearsactive = soup.find(string='Years active:').findNext('dd').text.strip()
            except:
                yearsactive = "?"
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
                print(band_aka)
                all_the_akas = band_aka.split(",")

                converted_akas = []
                for a in all_the_akas:
                    try:
                        conv_a = self.utf8_decode(a.strip())
                    except Exception as e:
                        print(e)
                        conv_a = a.strip()
                    converted_akas.append(conv_a)
                if band_name in converted_akas:
                    converted_akas.remove(band_name)
                if len(converted_akas) == 0:
                    aka = ""
                else: 
                    conv_string = ", ".join(converted_akas)
                    aka = f"(a.k.a. {conv_string})"
                print(aka)

            embed=discord.Embed(title=band_name, description=aka, url=band_link, color=0x1b0000)

            #embed.set_author(name=band_name,icon_url=picture_url)
            #embed.add_field(name="Country of origin:", value=country, inline=False)
            embed.set_thumbnail(url=picture_url)
            cabr = self.country_abbr(country)
            embed.add_field(name="Geography:", value=f"country of origin: {country} {cabr[0]}\nlocation: {location}", inline=False)
            embed.add_field(name="Genre:", value=genre, inline=False)
            embed.add_field(name="Themes:", value=themes, inline=False)
            embed.set_footer(text=f"{yearsactive}, current status: {status}")
            message = await ctx.send(embed=embed)

        await message.add_reaction("<a:catloading:970311103630417971>")

        # PREPARE EXTRA INFO
        # PREPARE DISCOGRAPHY INFO
        try:
            #session = requests.session()
            burp0_url = f"https://www.metal-archives.com:443/band/discography/id/{band_id}/tab/all"
            burp0_headers = {"Sec-Ch-Ua": "\"Not A(Brand\";v=\"24\", \"Chromium\";v=\"110\"", "Accept": "*/*", "X-Requested-With": "XMLHttpRequest", "Sec-Ch-Ua-Mobile": "?0", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.5481.178 Safari/537.36", "Sec-Ch-Ua-Platform": "\"Windows\"", "Sec-Fetch-Site": "same-origin", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Dest": "empty", "Referer": "https://www.metal-archives.com/bands/Wolvenfrost/3540474813", "Accept-Encoding": "gzip, deflate", "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7"}
            disco_response = session.get(burp0_url, headers=burp0_headers)

            discosoup = BeautifulSoup(disco_response.text, "html.parser")
            discography = []
            for tag in discosoup.find_all('tr'):
                #print(tag)
                record = tag.text

                #print(record)
                recordinfo = record.split("\n")
                while "" in recordinfo:
                    recordinfo.remove("")

                for a in tag.find_all('a', href=True):
                    r_link = a['href']
                    recordinfo.append(r_link)
                discography.append(recordinfo)

            str_fullalbums = ""
            count_albums = 0
            str_eps = ""
            count_eps = 0
            str_demos = ""
            count_demos = 0
            str_singles = ""
            count_singles = 0
            str_splits = ""
            count_splits = 0
            str_other = ""
            count_other = 0
            for item in discography:
                record_type = self.alphanum_filter(item[1].lower())
                if record_type == "fulllength":
                    str_fullalbums += f"[**{item[0]}**]({item[4]}) ({item[2]})\n"
                    count_albums += 1
                elif record_type == "ep":
                    str_eps += f"[{item[0]}]({item[4]}) ({item[2]})\n"
                    count_eps += 1
                elif record_type == "demo":
                    str_demos += f"[{item[0]}]({item[4]}) ({item[2]})\n"
                    count_demos += 1
                elif record_type == "single":
                    str_singles += f"[{item[0]}]({item[4]}) ({item[2]})\n"
                    count_singles += 1
                elif record_type == "split":
                    str_splits += f"[{item[0]}]({item[4]}) ({item[2]})\n"
                    count_splits += 1
                elif record_type == "type":
                    pass
                else:
                    str_other += f"[{item[0]}]({item[4]}) {item[1]} ({item[2]})"
                    count_other += 1
            

            curlineup_msg = "show last known lineup here"

            similar_msg = "show similar bands here"

            guild = ctx.guild
            mdmbot = ctx.guild.get_member(958105284759400559)
        except Exception as e:
            await ctx.send(f"Error while trying to fetch band discography.\n{e}")


        # BAND MEMBER INFO
        try:
            #burp0_url = f"https://www.metal-archives.com:443/bands/{}/{}"
            #burp0_headers = {"Cache-Control": "max-age=0", "Sec-Ch-Ua": "\"Not A(Brand\";v=\"24\", \"Chromium\";v=\"110\"", "Sec-Ch-Ua-Mobile": "?0", "Sec-Ch-Ua-Platform": "\"Windows\"", "Upgrade-Insecure-Requests": "1", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.5481.178 Safari/537.36", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7", "Sec-Fetch-Site": "none", "Sec-Fetch-Mode": "navigate", "Sec-Fetch-User": "?1", "Sec-Fetch-Dest": "document", "Accept-Encoding": "gzip, deflate", "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7"}
            #memb_response = session.get(burp0_url, headers=burp0_headers)
            #membersoup = BeautifulSoup(memb_response.text, "html.parser")

            if "Current lineup" in str(band_response.text):
                lineupstatus = "Current "
            elif "Last known lineup" in str(band_response.text):
                lineupstatus = "Last known "
            else:
                lineupstatus = ""

            table_members_current = ""
            for div in soup.find_all('div', id=True):
                if str(div["id"]) == "band_tab_members_current": 
                    table_members_current += str(div) 

            memberrows = []
            for tr in BeautifulSoup(table_members_current, "html.parser").find_all('tr'):
                tag = BeautifulSoup(str(tr), "html.parser")

                memberinfo = []

                if "lineupRow" in tr["class"]:
                    memberinfo.append("member")
                    for td in tag.find_all('td'):
                        memberinfo.append(td.text.strip())
                        #print(f"td: {td.text.strip()}")
                    for a in tag.find_all('a', href=True):
                        memberinfo.append(str(a["href"]).strip())
                        #print(str(a["href"]).strip())

                elif "lineupBandsRow" in tr["class"]:
                    memberinfo.append("seealso")
                    for a in tag.find_all('a', href=True):
                        #print(a.text.strip())
                        #print(str(a["href"]).strip())
                        memberinfo.append([a.text.strip(), str(a["href"]).strip()])
                else:
                    print("error?")
                
                memberrows.append(memberinfo)

            member_string = f"**{lineupstatus}Line-Up:**"
            member_fields = []
            for item in memberrows:
                if item[0] == "member":
                    try:
                        member = item[1]
                        instrument = item[2]
                    except:
                        member = item[1]
                        instrument = "?"
                    member_fields.append([member,instrument,""])
                elif item[0] == "seealso":
                    try:
                        otherbands_string = ""
                        bands = []
                        for band in item[1:]:
                            bandstring = str(band[0])
                            #try:
                            #    bandstring = f"[{band[0]}]({band[1]})"
                            #except:
                            #    bandstring = str(band[0])
                            bands.append(bandstring)
                        otherbands_string += ', '.join(bands)
                    except:
                        otherbands_string += ''
                    try:
                        member_fields[-1][2] = otherbands_string
                    except:
                        print("error with adding otherbands_string")

        except Exception as e:
            member_string = "Error while trying to fetch band members."
            member_fields = []
            await ctx.send(f"Error while trying to fetch band members.\n{e}")

        # SIMILAR ARTISTS INFO
        try:
            burp0_url = f"https://www.metal-archives.com:443/band/ajax-recommendations/id/{band_id}"
            burp0_headers = {"Sec-Ch-Ua": "\"Not A(Brand\";v=\"24\", \"Chromium\";v=\"110\"", "Accept": "*/*", "X-Requested-With": "XMLHttpRequest", "Sec-Ch-Ua-Mobile": "?0", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.5481.178 Safari/537.36", "Sec-Ch-Ua-Platform": "\"Windows\"", "Sec-Fetch-Site": "same-origin", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Dest": "empty", "Referer": "https://www.metal-archives.com/bands/Intestine_Baalism/5810", "Accept-Encoding": "gzip, deflate", "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7"}
            similar_response = session.get(burp0_url, headers=burp0_headers)
            similarsoup = BeautifulSoup(similar_response.text, "html.parser")

            similar_artists = []
            for tr in similarsoup.find_all('tr', id=True):
                artistinfo = []
                tag = BeautifulSoup(str(tr), "html.parser")

                for td in tag.find_all('td'):
                    artistinfo.append(td.text.strip())
                    #print(f"td: {td.text.strip()}")
                for a in tag.find_all('a', href=True):
                    artistinfo.append(str(a["href"]).strip())
                    #print(str(a["href"]).strip())

                similar_artists.append(artistinfo)

            SALIMIT = 10 #limit of similar artists to display

            if len(similar_artists) == 0:
                similarartist_text = "No similar artists mentioned on the Metal Archives."
            else:
                similarartist_text = "**Similar Artists:**\n"
            for artist in similar_artists[:SALIMIT]:
                cabr = self.country_abbr(artist[1])
                similarartist_text += f"[{artist[0]}]({artist[4]}) - {cabr[1]} {cabr[0]}\n{artist[2]} `:{artist[3]}:`\n"
        except:
            similarartist_text = "Error while trying to fetch similar artists."
            await ctx.send(f"Error while trying to fetch similar artists.\n{e}")

        await message.remove_reaction("<a:catloading:970311103630417971>", mdmbot)
        await message.add_reaction("ℹ️")
        await message.add_reaction("💽")
        await message.add_reaction("👥")
        await message.add_reaction("♻️")

        def check(reaction, user):
            return str(reaction.emoji) in ["ℹ️","💽","👥","♻️"]

        cur_page = 1

        while True:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=60, check=check)
                # waiting for a reaction to be added - times out after x seconds, 60 in this

                if str(reaction.emoji) == "ℹ️" and cur_page != 1:
                    cur_page = 1
                    #new_embed = discord.Embed(title = band_name, description=aka, url=band_link, color=0x1b0000)
                    #new_embed.set_thumbnail(url=picture_url)
                    #new_embed.add_field(name="Geography:", value=f"country of origin: {country}\nlocation: {location}", inline=False)
                    #new_embed.add_field(name="Genre:", value=genre, inline=False)
                    #new_embed.add_field(name="Themes:", value=themes, inline=False)
                    #new_embed.set_footer(text=f"{yearsactive}, current status: {status}")
                    #await message.edit(embed=new_embed)
                    await message.edit(embed=embed)
                    await message.remove_reaction(reaction, user)

                elif str(reaction.emoji) == "💽" and cur_page != 2:
                    cur_page = 2
                    try:
                        if len(discography) > 1:
                            if count_albums > 0:
                                description = "**Main discography:**\n" + str_fullalbums
                            else:
                                description = ""
                            unmentioned = []
                            if len(str_fullalbums) <= 4096:
                                new_embed = discord.Embed(title = band_name, description=description.strip(), url=band_link, color=0x1b0000)
                            else:
                                new_embed = discord.Embed(title = band_name, description=f"{count_albums} full-length Albums", url=band_link, color=0x1b0000)

                            new_embed.set_thumbnail(url=picture_url)

                            if count_eps > 0:
                                if count_albums < 10 and count_eps < 10 and len(str_eps) <= 1024:
                                    new_embed.add_field(name="EPs:", value=str_eps.strip(), inline=False)
                                else:
                                    unmentioned.append(f"{count_eps} EPs")

                            if count_demos > 0:
                                if count_albums == 0 and count_eps < 3 and count_demos > 0 and count_demos < 6 and len(str_demos) <= 1024 and (len(str_eps)) <= 3000:
                                    new_embed.add_field(name="Demos:", value=str_demos.strip(), inline=False)
                                else:
                                    unmentioned.append(f"{count_demos} Demos")

                            if count_splits > 0:
                                if count_albums == 0 and count_eps < 3 and count_demos < 5 and count_splits > 0 and count_splits < 6 and len(str_splits) <= 1024 and (len(str_eps)+len(str_demos)) <= 3000:
                                    new_embed.add_field(name="Splits:", value=str_splits.strip(), inline=False)
                                else:
                                    unmentioned.append(f"{count_splits} Splits")

                            if count_singles > 0:
                                if count_albums == 0 and count_eps == 0 and count_demos == 0 and count_singles > 0 and count_singles < 6 and len(str_singles) <= 1024:
                                    new_embed.add_field(name="Singles:", value=str_singles.strip(), inline=False)
                                else:
                                    unmentioned.append(f"{count_singles} Singles")

                            if count_other > 0:    
                                if count_albums == 0 and count_eps == 0 and count_demos == 0 and count_singles == 0 and count_splits == 0 and count_other > 0 and count_other < 6 and len(str_other) <= 1024:
                                    new_embed.add_field(name="Misc Releases:", value=str_other.strip(), inline=False)
                                else:
                                    unmentioned.append(f"{count_other} other releases")

                            if len(unmentioned) > 0:
                                foot = ", ".join(unmentioned)
                                new_embed.set_footer(text=f"{foot}")
                        else:
                            # no releases?
                            new_embed = discord.Embed(title = band_name, description="There are no releases.", url=band_link, color=0x1b0000)
                    except:
                        new_embed = discord.Embed(title = band_name, description="Error while trying to fetch discography.", url=band_link, color=0x1b0000)

                    await message.edit(embed=new_embed)
                    await message.remove_reaction(reaction, user)

                elif str(reaction.emoji) == "👥" and cur_page != 3:
                    print("👥 reaction")
                    cur_page = 3
                    new_embed = discord.Embed(title = band_name, description=member_string, url=band_link, color=0x1b0000)
                    new_embed.set_thumbnail(url=picture_url)

                    mem_string_count = len(band_name)+len(member_string)
                    actual_fields_count = 0

                    for member in member_fields[:10]:
                        name = member[0]
                        if member[2] == "":
                            description = f"{member[1]}\n"
                        else:
                            description = f"{member[1]}\n> {member[2]}\n"
                            if len(description) > 1024:
                                description = description[:1021] + "..."

                        mem_string_count += len(name)+len(description)
                        if mem_string_count > 5980:
                            print("character limit warning")
                            break
                        else:
                            new_embed.add_field(name=name, value=description.strip(), inline=False)
                            actual_fields_count += 1

                    if len(member_fields) > actual_fields_count:
                        difference = len(member_fields) - actual_fields_count
                        new_embed.set_footer(text=f"{difference} members omitted")

                    await message.edit(embed=new_embed)
                    await message.remove_reaction(reaction, user)

                elif str(reaction.emoji) == "♻️" and cur_page != 4:
                    cur_page = 4
                    new_embed = discord.Embed(title = band_name, description=similarartist_text[:4096], url=band_link, color=0x1b0000)
                    new_embed.set_thumbnail(url=picture_url)
                    await message.edit(embed=new_embed)
                    await message.remove_reaction(reaction, user)

                else:
                    await message.remove_reaction(reaction, user)
            except asyncio.TimeoutError:
                print("▶️ remove bot reactions ◀️")
                await message.remove_reaction("♻️", mdmbot)
                await message.remove_reaction("👥", mdmbot)
                await message.remove_reaction("💽", mdmbot)
                await message.remove_reaction("ℹ️", mdmbot)
                break


    async def send_bandlist(self, ctx, parsed_items, searchterm):
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

            cabr = self.country_abbr(country)
            msg = message_parts[k]
            nextline = f"{i}. [{band_name}]({band_link}) {aka} `{genre}`  {cabr[1]} {cabr[0]}\n"

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


            if input_string == "":
                await ctx.channel.send(f'Need a proper searchterm to look up on Metal Archives. <a:catloading:970311103630417971>')
            else:
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
                                band_aka = self.unicoder(response.text.split("<strong>a.k.a.</strong>")[1].split(")")[0].strip())
                            except:
                                band_aka = ""

                            # requirements met to fetch band
                            fetchingband = True

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

                            # requirements met to fetch band
                            fetchingband = True
                        else:
                            if match_counter_aka == 1:
                                band_link = list_match_aka[0][0]
                                band_aka = list_match_aka[0][1]
                                
                                # requirements met to fetch band
                                fetchingband = True
                            else:
                                if match_counter_alphanum == 1:
                                    band_link = list_match_alphanum[0][0]
                                    band_aka = list_match_alphanum[0][1]
                                    
                                    # requirements met to fetch band
                                    fetchingband = True
                                else:
                                    if match_counter_aka_alphanum == 1:
                                        band_link = list_match_aka_alphanum[0][0]
                                        band_aka = list_match_aka_alphanum[0][1]
                                        
                                        # requirements met to fetch band
                                        fetchingband = True
                                    else:
                                        # do we have specification?
                                        if specification == "":
                                            await self.send_bandlist(ctx, parsed_items, searchterm)
                                        else:
                                            valid_specification = True
                                            try:
                                                index = int(specification)
                                            except:
                                                index = -1

                                            n = len(parsed_items)
                                            if index < 1 or index > n:
                                                valid_specification = False

                                            if valid_specification:
                                                banditem = parsed_items[index-1]
                                                band_link = banditem[0]
                                                band_aka = banditem[2]
                                                
                                                # requirements met to fetch band
                                                fetchingband = True
                                            else:
                                                await self.send_bandlist(ctx, parsed_items, searchterm)
                                                
                except Exception as e:
                    await ctx.channel.send(f'Error while fetching search term:\n{e}')

        if fetchingband:
            await self.fetch_bandinfo(ctx, band_link, band_aka)

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