import discord
from discord.ext import commands
import datetime
import pytz
from other.utils.utils import Utils as util
import os
import asyncio
import requests
import json
from bs4 import BeautifulSoup
from discord import Spotify
import sqlite3


class Music_Info(commands.Cog):
    def __init__(self, bot: commands.bot) -> None:
        self.bot = bot



    # small utility functions

    def convert_urltype_string(self, primary_input):
        # in case there is more to adjust
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

    def theafilter(self, string_a):
        string_b = ''.join(ch for ch in string_a if (ch.isalnum() or ch == " "))
        words = string_b.lower().split()
        
        reducables = ["", "the", "a", "an", "le", "la", "un", "une", "der", "die", "das", "ein", "eine", "o", "as", "os", "of", "ov"]

        for r in reducables:
            while r in words:
                words.remove(r)

        return (' '.join(words)).strip()

    def country_abbr(self, cstr):
        countries = [['Afghanistan', '🇦🇫', 'AF'], ['Åland Islands', '🇦🇽', 'AX'], ['Albania', '🇦🇱', 'AL'], ['Algeria', '🇩🇿', 'DZ'], ['American Samoa', '🇦🇸', 'AS'], ['Andorra', '🇦🇩', 'AD'], ['Angola', '🇦🇴', 'AO'], ['Anguilla', '🇦🇮', 'AI'], ['Antarctica', '🇦🇶', 'AQ'], ['Antigua and Barbuda', '🇦🇬', 'AG'], ['Argentina', '🇦🇷', 'AR'], ['Armenia', '🇦🇲', 'AM'], ['Aruba', '🇦🇼', 'AW'], ['Australia', '🇦🇺', 'AU'], ['Austria', '🇦🇹', 'AT'], ['Azerbaijan', '🇦🇿', 'AZ'], ['Bahamas', '🇧🇸', 'BS'], ['Bahrain', '🇧🇭', 'BH'], ['Bangladesh', '🇧🇩', 'BD'], ['Barbados', '🇧🇧', 'BB'], ['Belarus', '🇧🇾', 'BY'], ['Belgium', '🇧🇪', 'BE'], ['Belize', '🇧🇿', 'BZ'], ['Benin', '🇧🇯', 'BJ'], ['Bermuda', '🇧🇲', 'BM'], ['Bhutan', '🇧🇹', 'BT'], ['Bolivia', '🇧🇴', 'BO'], ['Bonaire, Sint Eustatius and Saba', '🇧🇶', 'BQ'], ['Bosnia and Herzegovina', '🇧🇦', 'BA'], ['Botswana', '🇧🇼', 'BW'], ['Bouvet Island', '🇧🇻', 'BV'], ['Brazil', '🇧🇷', 'BR'], ['British Indian Ocean Territory', '🇮🇴', 'IO'], ['Brunei', '🇧🇳', 'BN'], ['Bulgaria', '🇧🇬', 'BG'], ['Burkina Faso', '🇧🇫', 'BF'], ['Burundi', '🇧🇮', 'BI'], ['Cambodia', '🇰🇭', 'KH'], ['Cameroon', '🇨🇲', 'CM'], ['Canada', '🇨🇦', 'CA'], ['Cape Verde', '🇨🇻', 'CV'], ['Cayman Islands', '🇰🇾', 'KY'], ['Central African Republic', '🇨🇫', 'CF'], ['Chad', '🇹🇩', 'TD'], ['Chile', '🇨🇱', 'CL'], ['China', '🇨🇳', 'CN'], ['Christmas Island', '🇨🇽', 'CX'], ['Cocos (Keeling) Islands', '🇨🇨', 'CC'], ['Colombia', '🇨🇴', 'CO'], ['Comoros', '🇰🇲', 'KM'], ['Congo, Democratic Republic of', '🇨🇩', 'CD'], ['Congo, Republic of', '🇨🇬', 'CG'], ['Cook Islands', '🇨🇰', 'CK'], ['Costa Rica', '🇨🇷', 'CR'], ["Côte d'Ivoire", '🇨🇮', 'CI'], ['Croatia', '🇭🇷', 'HR'], ['Cuba', '🇨🇺', 'CU'], ['Curaçao', '🇨🇼', 'CW'], ['Cyprus', '🇨🇾', 'CY'], ['Czechia', '🇨🇿', 'CZ'], ['Denmark', '🇩🇰', 'DK'], ['Djibouti', '🇩🇯', 'DJ'], ['Dominica', '🇩🇲', 'DM'], ['Dominican Republic', '🇩🇴', 'DO'], ['East Timor', '🇹🇱', 'TL'], ['Ecuador', '🇪🇨', 'EC'], ['Egypt', '🇪🇬', 'EG'], ['El Salvador', '🇸🇻', 'SV'], ['Equatorial Guinea', '🇬🇶', 'GQ'], ['Eritrea', '🇪🇷', 'ER'], ['Estonia', '🇪🇪', 'EE'], ['Eswatini', '🇸🇿', 'SZ'], ['Ethiopia', '🇪🇹', 'ET'], ['Falkland Islands', '🇫🇰', 'FK'], ['Faroe Islands', '🇫🇴', 'FO'], ['Fiji', '🇫🇯', 'FJ'], ['Finland', '🇫🇮', 'FI'], ['France', '🇫🇷', 'FR'], ['French Guiana', '🇬🇫', 'GF'], ['French Polynesia', '🇵🇫', 'PF'], ['French Southern Territories', '🇹🇫', 'TF'], ['Gabon', '🇬🇦', 'GA'], ['Gambia', '🇬🇲', 'GM'], ['Georgia', '🇬🇪', 'GE'], ['Germany', '🇩🇪', 'DE'], ['Ghana', '🇬🇭', 'GH'], ['Gibraltar', '🇬🇮', 'GI'], ['Greece', '🇬🇷', 'GR'], ['Greenland', '🇬🇱', 'GL'], ['Grenada', '🇬🇩', 'GD'], ['Guadeloupe', '🇬🇵', 'GP'], ['Guam', '🇬🇺', 'GU'], ['Guatemala', '🇬🇹', 'GT'], ['Guernsey', '🇬🇬', 'GG'], ['Guinea', '🇬🇳', 'GN'], ['Guinea-Bissau', '🇬🇼', 'GW'], ['Guyana', '🇬🇾', 'GY'], ['Haiti', '🇭🇹', 'HT'], ['Heard and McDonald Islands', '🇭🇲', 'HM'], ['Honduras', '🇭🇳', 'HN'], ['Hong Kong', '🇭🇰', 'HK'], ['Hungary', '🇭🇺', 'HU'], ['Iceland', '🇮🇸', 'IS'], ['India', '🇮🇳', 'IN'], ['Indonesia', '🇮🇩', 'ID'], ['International', '🇺🇳', 'int'], ['Iran', '🇮🇷', 'IR'], ['Iraq', '🇮🇶', 'IQ'], ['Ireland', '🇮🇪', 'IE'], ['Isle of Man', '🇮🇲', 'IM'], ['Israel', '🇮🇱', 'IL'], ['Italy', '🇮🇹', 'IT'], ['Jamaica', '🇯🇲', 'JM'], ['Japan', '🇯🇵', 'JP'], ['Jersey', '🇯🇪', 'JE'], ['Jordan', '🇯🇴', 'JO'], ['Kazakhstan', '🇰🇿', 'KZ'], ['Kenya', '🇰🇪', 'KE'], ['Kiribati', '🇰🇮', 'KI'], ['Korea, North', '🇰🇵', 'KP'], ['Korea, South', '🇰🇷', 'KR'], ['Kuwait', '🇰🇼', 'KW'], ['Kyrgyzstan', '🇰🇬', 'KG'], ['Laos', '🇱🇦', 'LA'], ['Latvia', '🇱🇻', 'LV'], ['Lebanon', '🇱🇧', 'LB'], ['Lesotho', '🇱🇸', 'LS'], ['Liberia', '🇱🇷', 'LR'], ['Libya', '🇱🇾', 'LY'], ['Liechtenstein', '🇱🇮', 'LI'], ['Lithuania', '🇱🇹', 'LT'], ['Luxembourg', '🇱🇺', 'LU'], ['Macau', '🇲🇴', 'MO'], ['Madagascar', '🇲🇬', 'MG'], ['Malawi', '🇲🇼', 'MW'], ['Malaysia', '🇲🇾', 'MY'], ['Maldives', '🇲🇻', 'MV'], ['Mali', '🇲🇱', 'ML'], ['Malta', '🇲🇹', 'MT'], ['Marshall Islands', '🇲🇭', 'MH'], ['Martinique', '🇲🇶', 'MQ'], ['Mauritania', '🇲🇷', 'MR'], ['Mauritius', '🇲🇺', 'MU'], ['Mayotte', '🇾🇹', 'YT'], ['Mexico', '🇲🇽', 'MX'], ['Micronesia, Federated States of', '🇫🇲', 'FM'], ['Moldova', '🇲🇩', 'MD'], ['Monaco', '🇲🇨', 'MC'], ['Mongolia', '🇲🇳', 'MN'], ['Montenegro', '🇲🇪', 'ME'], ['Montserrat', '🇲🇸', 'MS'], ['Morocco', '🇲🇦', 'MS'], ['Mozambique', '🇲🇿', 'MZ'], ['Myanmar', '🇲🇲', 'MM'], ['Namibia', '🇳🇦', 'NA'], ['Nauru', '🇳🇷', 'NR'], ['Nepal', '🇳🇵', 'NP'], ['Netherlands', '🇳🇱', 'NL'], ['New Caledonia', '🇳🇨', 'NC'], ['New Zealand', '🇳🇿', 'NZ'], ['Nicaragua', '🇳🇮', 'NI'], ['Niger', '🇳🇪', 'NE'], ['Nigeria', '🇳🇬', 'NG'], ['Niue', '🇳🇺', 'NU'], ['Norfolk Island', '🇳🇫', 'NF'], ['North Macedonia', '🇲🇰', 'MK'], ['Northern Mariana Islands', '🇲🇵', 'MP'], ['Norway', '🇳🇴', 'NO'], ['Oman', '🇴🇲', 'OM'], ['Pakistan', '🇵🇰', 'PK'], ['Palau', '🇵🇼', 'PW'], ['Palestine', '🇵🇸', 'PS'], ['Panama', '🇵🇦', 'PA'], ['Papua New Guinea', '🇵🇬', 'PG'], ['Paraguay', '🇵🇾', 'PY'], ['Peru', '🇵🇪', 'PE'], ['Philippines', '🇵🇭', 'PH'], ['Pitcairn Island', '🇵🇳', 'PN'], ['Poland', '🇵🇱', 'PL'], ['Portugal', '🇵🇹', 'PT'], ['Puerto Rico', '🇵🇷', 'PR'], ['Qatar', '🇶🇦', 'QA'], ['Reunion', '🇷🇪', 'RE'], ['Romania', '🇷🇴', 'RO'], ['Russia', '🇷🇺', 'RU'], ['Rwanda', '🇷🇼', 'RW'], ['Saint Barthélemy', '🇧🇱', 'BL'], ['Saint Kitts & Nevis', '🇰🇳', 'KN'], ['Saint Lucia', '🇱🇨', 'LC'], ['Saint Martin (French part)', '🇲🇫', 'MF'], ['Saint Pierre and Miquelon', '🇵🇲', 'PM'], ['Saint Vincent and The Grenadines', '🇻🇨', 'VC'], ['Samoa', '🇼🇸', 'WS'], ['San Marino', '🇸🇲', 'SM'], ['Sao Tome and Principe', '🇸🇹', 'ST'], ['Saudi Arabia', '🇸🇦', 'SA'], ['Senegal', '🇸🇳', 'SN'], ['Serbia', '🇷🇸', 'RS'], ['Seychelles', '🇸🇨', 'SC'], ['Sierra Leone', '🇸🇱', 'SL'], ['Singapore', '🇸🇬', 'SG'], ['Sint Maarten (Dutch part)', '🇸🇽', 'SX'], ['Slovakia', '🇸🇰', 'SK'], ['Slovenia', '🇸🇮', 'SI'], ['Solomon Islands', '🇸🇧', 'SB'], ['Somalia', '🇸🇴', 'SO'], ['South Africa', '🇿🇦', 'ZA'], ['South Georgia & South Sandwich Islands', '🇬🇸', 'GS'], ['South Sudan', '🇸🇸', 'SS'], ['Spain', '🇪🇸', 'ES'], ['Sri Lanka', '🇱🇰', 'LK'], ['St Helena, Ascension & Tristan da Cunha', '🇸🇭', 'SH'], ['Sudan', '🇸🇩', 'SD'], ['Suriname', '🇸🇷', 'SR'], ['Svalbard', '🇸🇯', 'SJ'], ['Sweden', '🇸🇪', 'SE'], ['Switzerland', '🇨🇭', 'CH'], ['Syria', '🇸🇾', 'SY'], ['Taiwan', '🇹🇼', 'TW'], ['Tajikistan', '🇹🇯', 'TJ'], ['Tanzania', '🇹🇿', 'TZ'], ['Thailand', '🇹🇭', 'TH'], ['Togo', '🇹🇬', 'TG'], ['Tokelau', '🇹🇰', 'TK'], ['Tonga', '🇹🇴', 'TO'], ['Trinidad and Tobago', '🇹🇹', 'TT'], ['Tunisia', '🇹🇳', 'TN'], ['Türkiye', '🇹🇷', 'TR'], ['Turkmenistan', '🇹🇲', 'TM'], ['Turks and Caicos Islands', '🇹🇨', 'TC'], ['Tuvalu', '🇹🇻', 'TV'], ['U.S. Minor Outlying Islands', '🇺🇲', 'UM'], ['Uganda', '🇺🇬', 'UG'], ['Ukraine', '🇺🇦', 'UA'], ['United Arab Emirates', '🇦🇪', 'AE'], ['United Kingdom', '🇬🇧', 'GB'], ['United States', '🇺🇸', 'US'], ['Unknown', '❓', '??'], ['Uruguay', '🇺🇾', 'UY'], ['Uzbekistan', '🇺🇿', 'UZ'], ['Vanuatu', '🇻🇺', 'VU'], ['Vatican City', '🇻🇦', 'VA'], ['Venezuela', '🇻🇪', 'VE'], ['Vietnam', '🇻🇳', 'VN'], ['Virgin Islands (British)', '🇻🇬', 'VG'], ['Virgin Islands (US)', '🇻🇮', 'VI'], ['Wallis and Futuna', '🇼🇫', 'WF'], ['Western Sahara', '🇪🇭', 'EH'], ['Yemen', '🇾🇪', 'YE'], ['Zambia', '🇿🇲', 'ZM'], ['Zimbabwe', '🇿🇼', 'ZW'], ['Kosovo', '🇽🇰', 'XK'], ['England', '🏴󠁧󠁢󠁥󠁮󠁧󠁿', 'GB-ENG'], ['Scotland', '🏴󠁧󠁢󠁳󠁣󠁴󠁿', 'GB-SCT'], ['Wales', '🏴󠁧󠁢󠁷󠁬󠁳󠁿', 'GB-CYM'], ['Northern Ireland', '🏴󠁧󠁢󠁮󠁩󠁲󠁿', 'GB-NIR'], ['Europe', '🇪🇺', 'EU']]
        for country in countries:
            if cstr.lower() == country[0].lower():
                emoji = country[1]
                abbr = country[2]
                break
        else:
            emoji = "?"
            abbr = "?"
        return [emoji, abbr]





    ###################################################################################################
    ##############                          METAL ARCHIVES                               ##############
    ###################################################################################################


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

            try:
                img_links = []
                for img in soup.find_all('img', src=True):
                    img_links.append(img['src'])
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
            embed.set_thumbnail(url=picture_url)
            cabr = self.country_abbr(country)
            embed.add_field(name="Geography:", value=f"country of origin: {country} {cabr[0]}\nlocation: {location}", inline=False)
            embed.add_field(name="Genre:", value=genre, inline=False)
            embed.add_field(name="Themes:", value=themes, inline=False)
            embed.set_footer(text=f"{yearsactive}, current status: {status}")
            message = await ctx.send(embed=embed)

        try:
            loading_emoji = util.emoji("load")
            await message.add_reaction(loading_emoji)
        except Exception as e:
            print(e)

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
                    if item[4].strip() == "":
                        str_fullalbums += f"{item[0]} ({item[2]})\n"
                    else:
                        str_fullalbums += f"[{item[0]}]({item[-1]}) ({item[2]})\n"
                    count_albums += 1
                elif record_type == "ep":
                    if item[4].strip() == "":
                        str_eps += f"{item[0]} ({item[2]})\n"
                    else:
                        str_eps += f"[{item[0]}]({item[-1]}) ({item[2]})\n"
                    count_eps += 1
                elif record_type == "demo":
                    if item[4].strip() == "":
                        str_demos += f"{item[0]} ({item[2]})\n"
                    else:
                        str_demos += f"[{item[0]}]({item[-1]}) ({item[2]})\n"
                    count_demos += 1
                elif record_type == "single":
                    if item[4].strip() == "":
                        str_singles += f"{item[0]} ({item[2]})\n"
                    else:
                        str_singles += f"[{item[0]}]({item[-1]}) ({item[2]})\n"
                    count_singles += 1
                elif record_type == "split":
                    if item[4].strip() == "":
                        str_splits += f"{item[0]} ({item[2]})\n"
                    else:
                        str_splits += f"[{item[0]}]({item[-1]}) ({item[2]})\n"
                    count_splits += 1
                elif record_type == "type":
                    pass
                else:
                    if item[4].strip() == "":
                        str_other += f"{item[0]} ({item[2]})\n"
                    else:
                        str_other += f"[{item[0]}]({item[-1]}) {item[1]} ({item[2]})"
                    count_other += 1
            
            curlineup_msg = "show last known lineup here"
            similar_msg = "show similar bands here"
            mdmbot = self.bot.get_user(self.bot.application_id)
        except Exception as e:
            await ctx.send(f"Error while trying to fetch band discography.\n{e}")

        # BAND MEMBER INFO
        try:
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
                similarartist_text += f"[{artist[0]}]({artist[4]}) - {cabr[1]} {cabr[0]}\n{artist[2]} `({artist[3]})`\n"
        except:
            similarartist_text = "Error while trying to fetch similar artists."
            await ctx.send(f"Error while trying to fetch similar artists.\n{e}")

        emoji = util.emoji("load")
        await message.remove_reaction(emoji, mdmbot)
        await message.add_reaction("ℹ️")
        await message.add_reaction("💽")
        await message.add_reaction("👥")
        await message.add_reaction("♻️")

        def check(reaction, user):
            return message.id == reaction.message.id and str(reaction.emoji) in ["ℹ️","💽","👥","♻️"] and user != mdmbot

        cur_page = 1

        while True:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=60, check=check)
                # waiting for a reaction to be added - times out after x seconds, 60 in this

                if str(reaction.emoji) == "ℹ️" and cur_page != 1:
                    cur_page = 1
                    await message.edit(embed=embed)
                    try:
                        await message.remove_reaction(reaction, user)
                    except:
                        print("could not remove reaction")

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
                                new_embed = discord.Embed(title = band_name, description=f"{count_albums} full-length Album(s)", url=band_link, color=0x1b0000)

                            new_embed.set_thumbnail(url=picture_url)

                            if count_eps > 0:
                                if count_albums < 10 and count_eps < 10 and len(str_eps) <= 1024:
                                    new_embed.add_field(name="EPs:", value=str_eps.strip(), inline=False)
                                else:
                                    unmentioned.append(f"{count_eps} EP(s)")

                            if count_demos > 0:
                                if count_albums == 0 and count_eps < 3 and count_demos > 0 and count_demos < 6 and len(str_demos) <= 1024 and (len(str_eps)) <= 3000:
                                    new_embed.add_field(name="Demos:", value=str_demos.strip(), inline=False)
                                else:
                                    unmentioned.append(f"{count_demos} Demo(s)")

                            if count_splits > 0:
                                if count_albums == 0 and count_eps < 3 and count_demos < 5 and count_splits > 0 and count_splits < 6 and len(str_splits) <= 1024 and (len(str_eps)+len(str_demos)) <= 3000:
                                    new_embed.add_field(name="Splits:", value=str_splits.strip(), inline=False)
                                else:
                                    unmentioned.append(f"{count_splits} Split(s)")

                            if count_singles > 0:
                                if count_albums == 0 and count_eps == 0 and count_demos == 0 and count_singles > 0 and count_singles < 6 and len(str_singles) <= 1024:
                                    new_embed.add_field(name="Singles:", value=str_singles.strip(), inline=False)
                                else:
                                    unmentioned.append(f"{count_singles} Single(s)")

                            if count_other > 0:    
                                if count_albums == 0 and count_eps == 0 and count_demos == 0 and count_singles == 0 and count_splits == 0 and count_other > 0 and count_other < 6 and len(str_other) <= 1024:
                                    new_embed.add_field(name="Misc Releases:", value=str_other.strip(), inline=False)
                                else:
                                    unmentioned.append(f"{count_other} other release(s)")

                            if len(unmentioned) > 0:
                                foot = ", ".join(unmentioned)
                                new_embed.set_footer(text=f"{foot}")
                        else:
                            # no releases?
                            new_embed = discord.Embed(title = band_name, description="There are no releases.", url=band_link, color=0x1b0000)
                    except:
                        new_embed = discord.Embed(title = band_name, description="Error while trying to fetch discography.", url=band_link, color=0x1b0000)

                    await message.edit(embed=new_embed)
                    try:
                        await message.remove_reaction(reaction, user)
                    except:
                        print("could not remove reaction")

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
                    try:
                        await message.remove_reaction(reaction, user)
                    except:
                        print("could not remove reaction")

                elif str(reaction.emoji) == "♻️" and cur_page != 4:
                    cur_page = 4
                    new_embed = discord.Embed(title = band_name, description=similarartist_text[:4096], url=band_link, color=0x1b0000)
                    new_embed.set_thumbnail(url=picture_url)
                    await message.edit(embed=new_embed)
                    try:
                        await message.remove_reaction(reaction, user)
                    except:
                        print("could not remove reaction")

                else:
                    try:
                        await message.remove_reaction(reaction, user)
                    except:
                        print("could not remove reaction")
            except asyncio.TimeoutError:
                print("▶️ remove bot reactions ◀️")
                await message.remove_reaction("♻️", mdmbot)
                await message.remove_reaction("👥", mdmbot)
                await message.remove_reaction("💽", mdmbot)
                await message.remove_reaction("ℹ️", mdmbot)
                break



    async def send_bandlist(self, ctx, parsed_items, searchterm, iTotalRecords):
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
            nextline = f"{i}. [{band_name}]({band_link}) {aka} {cabr[1]} {cabr[0]} `{genre}`\n"

            if len(msg)+len(nextline) > 4000:
                k += 1
                message_parts.append(nextline)
            else:
                message_parts[k] = msg + nextline

        j = 0 
        n = len(message_parts)
        for message in message_parts:
            j += 1
            if n == 1:
                title = f"Search results: {searchterm}"
            else:
                title = f"Search results: {searchterm} ({j}/{n})"
            embed=discord.Embed(title = title, description=message, color=0x1b0000)
            if j == n:
                embed.set_footer(text=f"{iTotalRecords} search results on MA")
            message = await ctx.send(embed=embed)



    async def input_from_nowplaying(self, ctx, fetch_album):
        input_string = ""
        try:
            # CHECK ACTIVITIES FOR SPOTIFY
            user = ctx.message.author
            for activity in user.activities:
                if isinstance(activity, Spotify):
                    input_string = str(activity.artist)
                    if fetch_album:
                        if "(" in str(activity.album) and str(activity.album)[0]:
                            input_string += " - " + str(activity.album).split("(")[0]
                        else:
                            input_string += " - " + str(activity.album)
                    primaryinput = input_string
                    specification = ""
                    break
            else:
                # CHECK FOR MUSIC BEE
                for activity in user.activities:
                    if str(activity.type) == "ActivityType.playing" and activity.name == "MusicBee":
                        if "ꜰʀᴏᴍ " in util.cleantext2(activity.state):
                            if " - " in str(activity.details):
                                details = activity.details.split(" - ", 1)
                            else:
                                details = activity.details.split("-", 1)
                            input_string = util.cleantext2(details[0].strip()) # artist
                            if fetch_album:
                                try:
                                    album = util.cleantext2(activity.state).split("ꜰʀᴏᴍ ")[1]
                                    input_string += " - " + album
                                except:
                                    input_string = util.cleantext2(str(activity.details))
                            break

                        elif "-" in str(activity.details):
                            if " - " in str(activity.details):
                                details = activity.details.split(" - ", 1)
                            else:
                                details = activity.details.split("-", 1)
                            input_string = util.cleantext2(details[0].strip()) # artist
                            if fetch_album:
                                try:
                                    input_string += " - " + util.cleantext2(details[1].strip()) # album
                                except:
                                    input_string = util.cleantext2(str(activity.details))
                            break
                else:
                    # CHECK FOR APPLE MUSIC
                    activity_list = []
                    for activity in user.activities:
                        try:
                            activity_list.append(str(activity.name))
                        except:
                            pass
                    for activity in user.activities:
                        if str(activity.type) == "ActivityType.playing" and (activity.name == "Apple Music" or (activity.name == "Music" and "iTunes Rich Presence for Discord" in activity_list)):
                            if activity.name == "Apple Music":
                                try:
                                    try:
                                        artist = util.cleantext2(activity.details.split(" - ", 1)[0].strip())
                                        song = util.cleantext2(activity.details.split(" - ", 1)[1].strip())
                                        album = util.cleantext2(activity.state.split("on ", 1)[1].strip())
                                    except:
                                        try:
                                            artist = util.cleantext2(activity.state.split(" — ", 1)[0].strip())
                                            song = util.cleantext2(activity.details.strip())
                                            album = util.cleantext2(activity.state.split(" — ", 1)[1].strip())
                                        except:
                                            continue

                                    input_string = artist
                                    if fetch_album:
                                        input_string += " - " + album 
                                    break
                                except:
                                    pass
                            elif activity.name == "Music":
                                try:
                                    input_string = util.cleantext2(activity.state.split("💿")[0].replace("👤","").strip()) # artist
                                    if fetch_album:
                                        input_string += " - " + util.cleantext2(activity.state.split("💿")[1].strip()) # album
                                    break
                                except:
                                    pass
                    else:
                        # CHECK LASTFM
                        conNP = sqlite3.connect('databases/npsettings.db')
                        curNP = conNP.cursor()
                        lfm_list = [[item[0],item[1]] for item in curNP.execute("SELECT lfm_name, lfm_link FROM lastfm WHERE id = ?", (str(user.id),)).fetchall()]

                        if len(lfm_list) == 0:
                            raise ValueError(f"could bot find any artist")

                        lfm_name = lfm_list[0][0]
                        lfm_link = lfm_list[0][1]

                        try:
                            # FETCH INFORMATION VIA API
                            payload = {
                                'method': 'user.getRecentTracks',
                                'user': lfm_name,
                                'limit': "1",
                            }
                            cooldown = True
                            response = await util.lastfm_get(ctx, payload, cooldown)
                            if response == "rate limit":
                                raise ValueError(f"could bot find any artist")
                            rjson = response.json()
                            tjson = rjson['recenttracks']['track'][0] # track json
                            input_string = tjson['artist']['#text'] # artist
                            if fetch_album:
                                try:
                                    input_string += " - " + tjson['album']['#text'] # album
                                except:
                                    pass
                        except Exception as e:
                            print(f"Error while trying to fetch information via LastFM API: {e}")
        except Exception as e:
            print(f"Error while checking activities: {e}")

        primaryinput = input_string
        specification = ""
        return input_string, primaryinput, specification



    @commands.command(name='metal', aliases = ['metallum', 'ma', "metalarchives"])
    @commands.check(util.is_active)
    async def _metallum(self, ctx: commands.Context, *args):
        """Metallum info
        
        use `<prefix>ma <bandname>` to get an 4-page embed with `general info`, `discography`, `band members` and `similar artists`.

        If the bandname is not unique you will get a list of possible options indexed from 1 to n.
        In this case you can use `<prefix>ma <bandname>; <index>` (integer after a semicolon) to get the info from he respective band.
        You can also use the 2-letter country code (or 'int' for international) if this happens to be a unique combination.

        (If you don't give any argument the command will try to search for the artist you are currently listening to. Works for Spotify, MusicBee, AppleMusic and LastFM.)
        """
        # search request
        input_string = ' '.join(args)
        fetchingband = False
        async with ctx.typing():
            if ";" in input_string:
                primaryinput = input_string.split(";",1)[0].strip()
                specification = input_string.split(";",1)[1].strip()
            else:
                primaryinput = input_string.strip()
                specification = ""

            if primaryinput == "":
                fetch_album = False
                input_string, primaryinput, spec = await self.input_from_nowplaying(ctx, fetch_album)

            if input_string == "":
                emoji = util.emoji("load")
                await ctx.channel.send(f'Need a proper searchterm to look up on Metal Archives. {emoji}')
                return
            
            searchterm = self.convert_urltype_string(primaryinput)

            try: # cooldown to not trigger actual rate limits or IP blocks
                await util.cooldown(ctx, "metallum")
            except Exception as e:
                await util.cooldown_exception(ctx, e, "metal archives")
                return

            try:
                session = requests.session()
                burp0_url = f"https://www.metal-archives.com:443/search/ajax-band-search/?field=name&query={searchterm}&sEcho=1&iColumns=3&sColumns=&iDisplayStart=0&iDisplayLength=200&mDataProp_0=0&mDataProp_1=1&mDataProp_2=2"
                burp0_headers = {"Sec-Ch-Ua": "\"Not A(Brand\";v=\"24\", \"Chromium\";v=\"110\"", "Accept": "application/json, text/javascript, */*; q=0.01", "X-Requested-With": "XMLHttpRequest", "Sec-Ch-Ua-Mobile": "?0", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.5481.78 Safari/537.36", "Sec-Ch-Ua-Platform": "\"Windows\"", "Sec-Fetch-Site": "same-origin", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Dest": "empty", "Referer": "https://www.metal-archives.com/search?searchString=baa+rhythm&type=band_name", "Accept-Encoding": "gzip, deflate", "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7"}
                response = session.get(burp0_url, headers=burp0_headers)

                aa_items = json.loads(response.text)["aaData"]
                try:
                    iTotalRecords = str(json.loads(response.text)["iTotalRecords"])
                except:
                    iTotalRecords = ""

                # parse band link, or disambiguation list

                if len(aa_items) == 0:
                    emoji = util.emoji("shy")
                    try:
                        namespec = f" ({primaryinput})"
                    except:
                        namespec = ""
                    await ctx.channel.send(f'Could not find band with such a name{namespec} on the Metal Archives. {emoji}')

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

                    # FIND MATCHING BAND NAME OR ALIAS

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

                        sl = primaryinput.lower()
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
                        if match_counter_exact == 0 and match_counter_aka == 1:
                            band_link = list_match_aka[0][0]
                            band_aka = list_match_aka[0][1]
                            
                            # requirements met to fetch band
                            fetchingband = True
                        else:
                            if match_counter_exact == 0 and match_counter_alphanum == 1:
                                band_link = list_match_alphanum[0][0]
                                band_aka = list_match_alphanum[0][1]
                                
                                # requirements met to fetch band
                                fetchingband = True
                            else:
                                if match_counter_exact == 0 and match_counter_aka == 0 and match_counter_alphanum == 0 and match_counter_aka_alphanum == 1:
                                    band_link = list_match_aka_alphanum[0][0]
                                    band_aka = list_match_aka_alphanum[0][1]
                                    
                                    # requirements met to fetch band
                                    fetchingband = True
                                else:
                                    ################################################################
                                    # filter parsed list
                                    parsed_items_f = []
                                    if len(parsed_items) > 20:
                                        sl = primaryinput.lower()
                                        slf = self.alphanum_filter(sl)
                                        slff = self.theafilter(sl)
                                        for item in parsed_items:
                                            band_name = item[1].lower().strip()
                                            band_akass = item[2].split(",")

                                            bandaliases = [band_name, self.alphanum_filter(band_name).strip(), self.theafilter(band_name).strip()]
                                            for band_aka in band_akass:
                                                ba = band_aka.lower().strip()
                                                bandaliases.append(ba)
                                                bandaliases.append(self.alphanum_filter(ba).strip())
                                                bandaliases.append(self.alphanum_filter(ba).strip())
                                            
                                            if (sl in bandaliases) or (slf != "" and slf in bandaliases) or (slff != "" and slff in bandaliases):
                                                parsed_items_f.append(item)

                                    if len(parsed_items_f) == 0:
                                        parsed_items_f = parsed_items

                                    # do we have specification?
                                    if specification == "":
                                        await self.send_bandlist(ctx, parsed_items_f, primaryinput, iTotalRecords)
                                    else:
                                        try:
                                            index = int(specification)
                                            int_specification = True
                                        except:
                                            index = -1
                                            int_specification = False

                                        if int_specification:
                                            # GET THE LIST ENTRY BY INDEX
                                            n = len(parsed_items_f)
                                            if index < 1 or index > n:
                                                # INVALID INTEGER
                                                util.emoji("derpy_playful")
                                                await ctx.send(f"Invalid integer, giving out list. {emoji}")
                                                await self.send_bandlist(ctx, parsed_items_f, primaryinput, iTotalRecords)
                                            else:
                                                # VALID INTEGER
                                                banditem = parsed_items_f[index-1]
                                                band_link = banditem[0]
                                                band_aka = banditem[2]
                                                
                                                # requirements met to fetch band
                                                fetchingband = True
                                        else:
                                            # [band_link, band_name, band_aka, genre, country]

                                            # GET THE LIST ENTRY BY COUNTRY
                                            # assume spec to be country
                                            target_cntry = self.alphanum_filter(specification.lower().strip())
                                            if target_cntry == "":
                                                emoji1 = util.emoji("think_sceptic")
                                                emoji2 = util.emoji("derpy")
                                                await ctx.send(f"Is that a country specification..? {emoji1}\nMe no recognise... {derpy}")
                                                await self.send_bandlist(ctx, parsed_items_f, primaryinput, iTotalRecords)
                                            else:
                                                cntry_counter = 0
                                                for item in parsed_items_f:
                                                    cntry = item[4].lower()
                                                    cntry_strp = self.alphanum_filter(cntry)
                                                    cntry_abbr = self.country_abbr(cntry)[1].lower()
                                                    if target_cntry in [cntry, cntry_strp, cntry_abbr]:
                                                        cntry_counter += 1
                                                        # vvv --- vvv
                                                        target_item = item 

                                                if cntry_counter == 0:
                                                    emoji = util.emoji("cover_eyes2")
                                                    await ctx.send(f"Either I did not recognise that country, or a band with this name originating from that country is not on the Metal Archives... {emoji}")
                                                elif cntry_counter == 1:
                                                    band_link = target_item[0]
                                                    band_aka = target_item[2]
                                                    fetchingband = True
                                                else:
                                                    ####################################################
                                                    # searchterm + country not unique
                                                    # TRY FILTERING ONLY (MORE OR LESS) EXACT MATCHES

                                                    parsed_items_f2 = []
                                                    # repeat this even if len <= 20
                                                    sl = primaryinput.lower()
                                                    slf = self.alphanum_filter(sl)
                                                    slff = self.theafilter(sl)
                                                    for item in parsed_items:
                                                        band_name = item[1].lower().strip()
                                                        band_akass = item[2].split(",")

                                                        bandaliases = [band_name, self.alphanum_filter(band_name).strip(), self.theafilter(band_name).strip()]
                                                        for band_aka in band_akass:
                                                            ba = band_aka.lower().strip()
                                                            bandaliases.append(ba)
                                                            bandaliases.append(self.alphanum_filter(ba).strip())
                                                            bandaliases.append(self.alphanum_filter(ba).strip())
                                                        
                                                        if (sl in bandaliases) or (slf != "" and slf in bandaliases) or (slff != "" and slff in bandaliases):
                                                            parsed_items_f2.append(item)

                                                    cntry_counter = 0
                                                    for item in parsed_items_f2:
                                                        cntry = item[4].lower()
                                                        cntry_strp = self.alphanum_filter(cntry)
                                                        cntry_abbr = self.country_abbr(cntry)[1].lower()
                                                        if target_cntry in [cntry, cntry_strp, cntry_abbr]:
                                                            cntry_counter += 1
                                                            target_item = item 

                                                    if cntry_counter == 1:
                                                        band_link = target_item[0]
                                                        band_aka = target_item[2]
                                                        fetchingband = True
                                                    else:
                                                        emoji = util.emoji("think")
                                                        await ctx.send(f"Searchterm + country not unique.. {emoji}")
                                                        await self.send_bandlist(ctx, parsed_items_f, primaryinput, iTotalRecords)
                                            
            except Exception as e:
                if str(e) == "Expecting value: line 1 column 1 (char 0)":
                    await ctx.channel.send(f"Error: Request was probably blocked.")
                else:
                    await ctx.channel.send(f'Error while searching term:\n{e}')

        if fetchingband:
            await self.fetch_bandinfo(ctx, band_link, band_aka)

    @_metallum.error
    async def metallum_error(self, ctx, error):
        await util.error_handling(ctx, error)







    ###################################################################################################
    ##############                          RATE YOUR MUSIC                              ##############
    ###################################################################################################



    async def rym_info_scrape(self, ctx, args):
        """decide whether to fetch artist, album or a genre"""

        arguments = ' '.join(args)

        if arguments.strip() == "":
            try:
                fetch_album = True
                dummystring1, arguments, dummystring2 = await self.input_from_nowplaying(ctx, fetch_album)
                if " - " in arguments and len(arguments.split(" - ")[0].strip()) > 0 and len(arguments.split(" - ")[1].strip()) > 0:
                    await self.rym_album_scrape(ctx, arguments)
                else:
                    await ctx.send(f"Could not find album: {arguments}")
            except Exception as e:
                print("Error:", e)
                await ctx.send("You need to provide an artist or a hyphen-separated `artist - album` pair.\nOr start with argument `genre:` to search for a genre.")

        elif arguments.startswith("genre:"):
            genrename_raw = util.cleantext2(arguments.split("genre:",1)[1])
            genre_word_list = []
            for word in genrename_raw.split():
                if word.strip() != "":
                    genre_word_list.append(word.lower().strip())
            genrename = "-".join(genre_word_list)
            await self.rym_genre_scrape(ctx, genrename)

        elif " - " in arguments:
            arg_list = []
            for arg in args:
                element = ''.join(x for x in arg if arg.isalnum())
                if element != "":
                    arg_list.append(element)
            arg_string = ' '.join(arg_list)

            await self.rym_album_scrape(ctx, arg_string)

        else:
            if ";" in arguments:
                artist = arguments.split(";")[0].strip()
                extrainfo = arguments.split(";")[1].strip()

            else:
                artist = arguments.strip()
                extrainfo = ""

            await self.rym_artist_scrape(ctx, artist, extrainfo)



    async def rym_artist_scrape(self, ctx, artist, extrainfo):
        """fetch artist, but if additionally semicolon + country or genre is provided use search"""
        try: # cooldown to not trigger actual rate limits or IP blocks
            await util.cooldown(ctx, "rym")
        except Exception as e:
            print(e)
            await util.cooldown_exception(ctx, e, "rym")
            return

        try:
            # GET LINK TO ARTIST

            search_url = f"https://rateyourmusic.com:443/search?searchterm={artist}&searchtype=a"
            session = requests.session()
            burp0_headers = {"Sec-Ch-Ua": "\"Not-A.Brand\";v=\"99\", \"Chromium\";v=\"124\"", "Sec-Ch-Ua-Mobile": "?0", "Sec-Ch-Ua-Platform": "\"Windows\"", "Upgrade-Insecure-Requests": "1", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.118 Safari/537.36", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7", "Sec-Fetch-Site": "none", "Sec-Fetch-Mode": "navigate", "Sec-Fetch-User": "?1", "Sec-Fetch-Dest": "document", "Accept-Encoding": "gzip, deflate, br", "Accept-Language": "en-US;q=0.8,en;q=0.7", "Priority": "u=0, i", "Connection": "close"}
            response = session.get(search_url, headers=burp0_headers)

            soup = BeautifulSoup(response.text, "html.parser")

            if len(extrainfo.strip()) == 2:
                extrainfo = util.isocode_to_name(extrainfo.strip()).split("of")[0].strip()


            artist_list = []
            for table in soup.find_all("table"):
                for tr in table.find_all("tr"):
                    try:
                        if str(tr.get("class")[0]) == "infobox":

                            for a in tr.find_all("a"):

                                try:
                                    is_link = False
                                    a_href = a.get("href")

                                    if a_href is not None and str(a_href) != "" and str(a_href).startswith("/artist/"):
                                        is_link = True
                                    elif str(a_href[0]) != "" and str(a_href[0]).startswith("/artist/"):
                                        is_link = True

                                    if is_link:
                                        if extrainfo.strip() != "":
                                            if util.alphanum(extrainfo.lower().strip()) in util.alphanum(str(tr).lower()):
                                                artist_list.append(f"https://rateyourmusic.com{str(a_href)}")
                                        else:
                                            artist_list.append(f"https://rateyourmusic.com{str(a_href)}")
                                except:
                                    pass
                            break
                    except:
                        pass

            if len(artist_list) == 0:
                emoji = util.emoji("disappointed")
                await ctx.send(f"Could not find artist. {emoji}")
                return

            # REQUEST ARTIST PAGE
            
            burp0_url = artist_list[0]

            session = requests.session()
            burp0_headers = {"Sec-Ch-Ua": "\"Not-A.Brand\";v=\"99\", \"Chromium\";v=\"124\"", "Sec-Ch-Ua-Mobile": "?0", "Sec-Ch-Ua-Platform": "\"Windows\"", "Upgrade-Insecure-Requests": "1", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.60 Safari/537.36", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7", "Sec-Fetch-Site": "none", "Sec-Fetch-Mode": "navigate", "Sec-Fetch-User": "?1", "Sec-Fetch-Dest": "document", "Accept-Encoding": "gzip, deflate, br", "Accept-Language": "en-US;q=0.8,en;q=0.7", "Priority": "u=0, i", "Connection": "close"}
            response = session.get(burp0_url, headers=burp0_headers)

            soup = BeautifulSoup(response.text, "html.parser")

            # GET META DATA FROM ARTIST PAGE

            artistname = []
            for h1 in soup.find_all("h1"):
                try:
                    h1_class = h1.get("class")

                    if str(h1_class[0]) == "artist_name_hdr":
                        artistname.append(str(h1.getText())).strip()
                except:
                    pass

            # GET GENRES AND RELEASES
            location = []
            genres = []
            albums = []
            i = -1 # album counter
            found_live = False
            for div in soup.find_all("div"):
                try:
                    div_class = div.get("class")

                    # BREAK WHEN "APPEARS ON"-PART IS REACHED

                    if str(div_class[0]) == "disco_header_top":
                        try:
                            h3 = div.find('h3')
                            innertext = str(h3.getText()).strip()
                        except:
                            innertext = ""

                        if "Live Album" in str(div):
                            found_live = True

                        if innertext == "Appears On":
                            break

                    # GET LOCATION AND GENRES

                    if str(div_class[0]) == "info_content":
                        for a in div.find_all("a"):
                            a_class = str(a.get("class")[0])

                            if a_class.lower() == "location":
                                location_name = str(a.getText()).strip()
                                location.append(location_name)

                            elif a_class.lower() == "genre":
                                genre_name = str(a.getText()).strip()
                                genres.append(genre_name)

                    # ORGANIZE RELEASE ENTRIES

                    if str(div_class[0]).startswith("disco_release"):
                        albums.append([])
                        i += 1

                    elif str(div_class[0]).startswith("disco_avg_rating"):
                        albums[i].append(div.getText())

                    elif str(div_class[0]) == "disco_ratings":
                        albums[i].append(div.getText())

                    elif str(div_class[0]) == "disco_reviews":
                        albums[i].append(div.getText())

                    elif str(div_class[0]) == "disco_mainline":
                        a = div.find('a')
                        title = a.getText()
                        url = a.get("href")
                        albums[i].append(title)
                        albums[i].append(str(url))
                        try:
                            release_type = str(url).split("/release/")[1].split("/")[0]
                            if found_live and release_type.lower() == "album":
                                albums[i].append("live album")
                            else:
                                albums[i].append(release_type)
                        except:
                            albums[i].append("")

                    elif str(div_class[0]) == "disco_subline":
                        span = div.find('span')
                        year = span.getText()
                        albums[i].append(year)

                except Exception as e:
                    pass

            # SANITY CHECK

            if len(artistname) == 0 and len(albums) == 0:
                emoji = util.emoji("disappointed")
                await ctx.send(f"Error while trying to fetch artist information. {emoji}")
                return

            # COMPOSE EMBED

            title = "RateYourMusic Artist Info"
            description = ""

            try:
                description += f"**{artistname[0]}**\n"
            except:
                description += f"`{artist.lower()}`\n"

            if len(location) > 0:
                description += "Location: " + ', '.join(location) + "\n"

            if len(genres) > 0:
                description += "Genres: " +  ', '.join(genres) + "\n\n"

            release_count = {}
            if len(albums) > 0:
                #description += "**Discography:**\n"
                previous_type = ""
                i = 0
                for item in albums:
                    avg_rating = item[0]
                    num_ratings = item[1]
                    num_reviews = item[2]
                    album_title = item[3]
                    album_url = item[4]
                    release_type = item[5]
                    release_year = item[6]

                    if release_type in release_count:
                        release_count[release_type] += 1
                    else:
                        release_count[release_type] = 1

                    if release_type.lower() in ["single", "musicvideo", "live album", "comp", "unauth"]:
                        continue

                    if release_type != previous_type:
                        if release_type.lower() != "album" and i > 14:
                            continue
                        if release_type == "ep":
                            description += "**" + release_type.upper() + "(s):**\n"
                        else:
                            description += "**" + release_type.capitalize() + "(s):**\n"

                    albumtitleurl = album_title.strip()
                    if release_type.lower() == "album":
                        albumtitleurl = "**" + albumtitleurl + "**"
                    if url.strip() != "":
                        albumtitleurl = "[" + albumtitleurl + "](https://rateyourmusic.com/" + url.strip() + ")"

                    if avg_rating.strip() != "":
                        description += albumtitleurl + f" {release_year} : `{avg_rating}` ({num_ratings})\n"
                    else:
                        description += albumtitleurl + f" {release_year} : `?` ({num_ratings})\n"

                    previous_type = release_type
                    i += 1

                if i == 0:
                    description += "*no Albums or EPs found*"

            embed = discord.Embed(title=title, description=description[:4096], url=burp0_url, color = 0x1C6FB6)

            footer_list = []
            for key in release_count:
                footer_list.append(str(release_count[key]) + f" {key}(s)")
            embed.set_footer(text=', '.join(footer_list))
            await ctx.send(embed=embed)


        except Exception as e:
            await ctx.send(f"Error: {e}")



    async def rym_album_scrape(self, ctx, arguments):
        """use search to find album, then fetch data from release page"""

        try: # cooldown to not trigger actual rate limits or IP blocks
            await util.cooldown(ctx, "rym")
        except Exception as e:
            print(e)
            await util.cooldown_exception(ctx, e, "rym")
            return

        # SEARCH ALBUM

        search_url = f"https://rateyourmusic.com/search?searchterm={arguments}&searchtype=l"
        session = requests.session()
        burp0_headers = {"Sec-Ch-Ua": "\"Not-A.Brand\";v=\"99\", \"Chromium\";v=\"124\"", "Sec-Ch-Ua-Mobile": "?0", "Sec-Ch-Ua-Platform": "\"Windows\"", "Upgrade-Insecure-Requests": "1", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.118 Safari/537.36", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7", "Sec-Fetch-Site": "none", "Sec-Fetch-Mode": "navigate", "Sec-Fetch-User": "?1", "Sec-Fetch-Dest": "document", "Accept-Encoding": "gzip, deflate, br", "Accept-Language": "en-US;q=0.8,en;q=0.7", "Priority": "u=0, i", "Connection": "close"}
        response = session.get(search_url, headers=burp0_headers)

        soup = BeautifulSoup(response.text, "html.parser")
        album_url = ""

        for a in soup.find_all("a"):
            a_class = a.get("class")

            if str(a_class[0]).strip() == "searchpage":
                album_url = a.get("href")
                break

        else:
            await ctx.send("Could not find release on RateYourMusic.")
            return

        # FETCH ALBUM PAGE

        #await asyncio.sleep(0.5)

        burp0_url = f"https://rateyourmusic.com:443{album_url}"
        response = session.get(burp0_url, headers=burp0_headers)

        soup = BeautifulSoup(response.text, "html.parser")

        rating_value = []
        rating_count = []
        artist_name = []
        album_name = []
        album_cover = []
        release_date = []
        primary_genres = []
        secondary_genres = []
        descriptors = []

        for div in soup.find_all("div"):
            try:
                div_id = div.get("id")

                if str(div_id.strip()).startswith("media_link_button_container"):
                    artist = div.get("data-artists")
                    album = div.get("data-albums")

                    artist_name.append(str(artist).strip())
                    album_name.append(str(album).strip())
            except:
                pass


        for img in soup.find_all("img"):
            try:
                img_alt = img.get("alt")
                    
                try:
                    img_src = img.get("src")
                    if img_src is None or str(img_src).strip() == "":
                        raise ValueError("img tag has no attribute src")
                    for link in str(img_src).split(","):
                        if link.strip().endswith(".jpg") or link.strip().endswith(".png") or link.strip().endswith(".webp"):
                            album_cover.append(link.strip())
                except:
                    img_srcset = img.get("srcset")
                    for link in str(img_srcset).split(","):
                        if link.strip().endswith(".jpg") or link.strip().endswith(".png") or link.strip().endswith(".webp"):
                            album_cover.append(link.strip())
            except:
                pass


        for meta in soup.find_all("meta"):
            try:
                meta_itemprop = meta.get("itemprop")

                if str(meta_itemprop.strip()) == "ratingValue":
                    content = meta.get("content")
                    rating_value.append(str(content))

                if str(meta_itemprop.strip()) == "ratingCount":
                    content = meta.get("content")
                    rating_count.append(str(content))

                if str(meta_itemprop.strip()) == "name":
                    content = meta.get("content")
                    album_name.append(str(content))
            except:
                pass


        for span in soup.find_all("span"):
            try:
                span_class = span.get("class")

                if str(span_class[0]).startswith("issue_year"):
                    title = span.get("title")
                    release_date.append(str(title).strip())

                if str(span_class[0]) == "release_pri_genres":
                    for a in span.find_all("a"):
                        text = a.getText()
                        primary_genres.append(str(text))

                if str(span_class[0]) == "release_sec_genres":
                    for a in span.find_all("a"):
                        text = a.getText()
                        secondary_genres.append(str(text))

                if str(span_class[0]) == "release_pri_descriptors":
                    for text in str(span.getText()).split(","):
                        descriptors.append(text.strip())
            except:
                pass

        # MAKE EMBED
        try:
            artist = artist_name[0]
        except:
            artist = "???"
        try:
            album = album_name[0]
        except:
            album = "???"
        try:
            cover = album_cover[0]
        except:
            cover = ""
        try:
            date = release_date[0]
        except:
            date = ""
        primgenres = ', '.join(primary_genres)
        secgenres = ', '.join(secondary_genres)
        desc = ', '.join(descriptors)
        try:
            ratingval = rating_value[0]
        except:
            ratingval = "?"
        try:
            ratingnum = rating_count[0]
        except:
            ratingnum = "?"

        title = f"RateYourMusic Album Info"

        description = f"**{album}**\nby {artist}\n{date}\n\n"

        if len(primary_genres) > 0:
            description += f"**Primary genres:**\n{primgenres}\n"
        else:
            description += "(no primary genre given)\n"

        if len(secondary_genres) > 0:
            description += f"**Secondary genres:**\n{secgenres}\n"
        else:
            description += "(no secondary genre given)\n"

        if len(descriptors):
            description += "\n**Descriptors:** " + desc + "\n"

        description += f"\n**Rating Avg.:** `{ratingval}` "

        if ratingnum == 1:
            description += f"(rated by 1)"
        else:
            description += f"(rated by {ratingnum})"

        try:
            embed = discord.Embed(title=title, description=description[:4096], url=f"https://rateyourmusic.com{album_url}", color = 0x1C6FB6)
        except:
            embed = discord.Embed(title=title, description=description[:4096], color = 0x1C6FB6)
        try:
            if cover != "":
                embed.set_thumbnail(url=f"https:{cover}")
        except:
            pass
        await ctx.send(embed=embed)



    async def rym_genre_scrape(self, ctx, genrename):
        try: # cooldown to not trigger actual rate limits or IP blocks
            await util.cooldown(ctx, "rym")
        except Exception as e:
            print(e)
            await util.cooldown_exception(ctx, e, "rym")
            return
        try:
            genre_url = f"https://rateyourmusic.com/genre/{genrename}/"
            session = requests.session()

            burp0_headers = {"Sec-Ch-Ua": "\"Not-A.Brand\";v=\"99\", \"Chromium\";v=\"124\"", "Sec-Ch-Ua-Mobile": "?0", "Sec-Ch-Ua-Platform": "\"Windows\"", "Upgrade-Insecure-Requests": "1", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.118 Safari/537.36", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7", "Sec-Fetch-Site": "none", "Sec-Fetch-Mode": "navigate", "Sec-Fetch-User": "?1", "Sec-Fetch-Dest": "document", "Accept-Encoding": "gzip, deflate, br", "Accept-Language": "en-US;q=0.8,en;q=0.7", "Priority": "u=0, i", "Connection": "close"}
            response = session.get(genre_url, headers=burp0_headers)

            soup = BeautifulSoup(response.text, "html.parser")

            detail_text = ""

            for span in soup.find_all("span"):
                try:
                    span_class = span.get("class")

                    if str(span_class[0]).strip() == "rendered_text":
                        text = BeautifulSoup(str(span).split("<br")[0], "html.parser")
                        detail_text = str(text.getText()).strip()
                except:
                    pass

            top_releases = []

            for div in soup.find_all("div"):
                try:
                    div_class = div.get("class")
                    if str(div_class[0]).strip() == "page_section_charts_carousel_title":

                        top_artist = ""
                        top_album = ""
                        top_url = ""
                        
                        for a in div.find_all("a"):

                            a_href = a.get("href")
                            a_class = a.get("class")

                            if str(a_class[0]).strip() == "release":
                                if a.getText().strip() != "":
                                    top_album = a.getText().strip()

                                if str(a_href).strip() != "":
                                    top_url = f"https://rateyourmusic.com{str(a_href)}"

                            if str(a_class[0]).strip() == "artist":
                                if a.getText().strip() != "":
                                    top_artist = a.getText().strip()

                        if top_artist != "" and top_album != "":
                            top_releases.append([top_artist, top_album, top_url])
                except:
                    pass

            if len(top_releases) == 0 and detail_text.strip() == 0:
                raise ValueError("Error: received empty response")

            top_releases_string = "**Top Releases:**\n"
            i = 0
            for item in top_releases:
                i += 1
                top_releases_string += f"`{i}.` {item[0]} - [{item[1]}]({item[2]})\n"

            top_releases_string = top_releases_string
            t_length = len(top_releases_string)

            # MAKE EMBED

            title = f"RateYourMusic Genre Info"

            if len(detail_text) > 4094-t_length:
                detail_text[:4091-t_length] + "..."
            description = detail_text + "\n\n" + top_releases_string.strip()

            try:
                embed = discord.Embed(title=title, description=description[:4096], url=genre_url, color = 0x1C6FB6)
            except:
                embed = discord.Embed(title=title, description=description[:4096], color = 0x1C6FB6)
            await ctx.send(embed=embed)
        except:
            emoji = util.emoji("disappointed")
            await ctx.send(f"Error: could not find genre. {emoji}")



    @commands.command(name='rym', aliases = ['rateyourmusic', 'sonemic'])
    @commands.check(util.is_active)
    async def _rym(self, ctx: commands.Context, *args):
        """RateYourMusic.com inforamtion

        Use this command to get information for
        1. an artist with argument `<artist>`
        2. an album with argument `<artist> - <album>`
        3. a genre with argument `genre: <genre name>`

        Note: RateYourMusic is quite touchy when it comes to machine fetching information from their site and is quite quick in blocking network adresses outright, so hosts may decide to disable this command instead of setting a higher rate limit.
        """
        conA = sqlite3.connect(f'databases/activity.db')
        curA = conA.cursor()
        rymsetting_list = [item[0] for item in curA.execute("SELECT value FROM hostdata WHERE name = ?", ("rym scraping",)).fetchall()]

        if len(rymsetting_list) == 0 or rymsetting_list[0] != "on":
            emoji = util.emoji("pensive")
            await ctx.send(f"This command is currently disabled. {emoji}")
            return

        async with ctx.typing():
            await self.rym_info_scrape(ctx, args)
    @_rym.error
    async def rym_error(self, ctx, error):
        await util.error_handling(ctx, error)




async def setup(bot: commands.bot) -> None:
    await bot.add_cog(
        Music_Info(bot),
        guilds = [discord.Object(id = int(os.getenv("guild_id")))])