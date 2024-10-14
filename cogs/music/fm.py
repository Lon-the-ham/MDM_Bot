import discord
from discord.ext import commands
import sqlite3
import datetime
import pytz
from other.utils.utils import Utils as util
import os
import sys
import asyncio
import requests
import json
from bs4 import BeautifulSoup
import html
from discord import Spotify
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from emoji import UNICODE_EMOJI
import traceback


class Music_NowPlaying(commands.Cog):
    def __init__(self, bot: commands.bot) -> None:
        self.bot = bot
        self.prefix = os.getenv("prefix")
        self.tagseparator = " ‧ "


    ########################################################### ACTIVITY FETCH AND SEND FUNCTIONS #######################################################



    async def musicbee_activity(self, ctx, member, show_tags, called_services, custom):
        for activity in member.activities:
            if str(activity.type) == "ActivityType.playing" and activity.name == "MusicBee":

                # FETCH ARTIST/ALBUM/SONG INFORMATION

                try:
                    if "ꜰʀᴏᴍ " in util.cleantext2(activity.state):
                        if " - " in str(activity.details):
                            details = activity.details.split(" - ", 1)
                        else:
                            details = activity.details.split("-", 1)
                        artist = util.cleantext2(details[0].strip())
                        song = util.cleantext2(details[1].strip())
                        try:
                            album = util.cleantext2(activity.state).split("ꜰʀᴏᴍ ")[1]
                        except:
                            album = ""
                        artist_rep = artist.replace(" ","+")
                        song_rep = title.replace(" ","+")
                        lfm_link = f"https://www.last.fm/music/{artist_rep}/_/{song_rep}".replace("\\", "")

                        if album.strip() != "":
                            description = f"[{song}]({lfm_link})\nby **{artist}** | {album}"
                        else:
                            description = f"[{song}]({lfm_link})\nby **{artist}**"

                    elif "-" in str(activity.details):
                        if " - " in str(activity.details):
                            details = activity.details.split(" - ", 1)
                        else:
                            details = activity.details.split("-", 1)
                        artist = util.cleantext2(details[0].strip())
                        album = util.cleantext2(details[1].strip())
                        try:
                            song = util.cleantext2(activity.state.strip())
                            artist_rep = artist.replace(" ","+")
                            song_rep = song.replace(" ","+")
                            lfm_link = f"https://www.last.fm/music/{artist_rep}/_/{song_rep}".replace("\\", "")
                            description = f"[{song}]({lfm_link})\nby **{artist}** | {album}"
                        except:
                            song = ""
                            artist_rep = artist.replace(" ","+")
                            album_re = album.replace(" ","+")
                            lfm_link = f"https://www.last.fm/music/{artist_rep}/{album_rep}".replace("\\", "")
                            description = f"**{artist}** | [{album}]({lfm_link})"                         
                    else:
                        description = f"{activity.details}\n{activity.state}"
                except:
                    description = f"{activity.details}\n{activity.state}"

                # CREATE EMBED

                color = 0x000000
                #try:
                #    color = member.color
                #except:
                #    color = 0x000000
                embed = discord.Embed(description=description, color = color)
                embed.set_author(name=f"{member.display_name}'s MusicBee" , icon_url=member.avatar)
                try:
                    embed.set_thumbnail(url=activity.large_image_url)
                except Exception as e:
                    print(e)
                    try:
                        embed.set_thumbnail(url=activity.small_image_url)
                    except Exception as e:
                        print(f"could not find image: {e}")

                # HANDLE TAGS
                if show_tags:
                    try:
                        tag_string = await self.fetch_tags(ctx, "musicbee", artist, album, song, None, None, called_services, custom, str(member.id))
                        try:
                            embed.set_footer(text = tag_string.strip())
                        except Exception as e:
                            print("Error while creating footer for musicbee np: ", e)
                    except Exception as e:
                        print("Unable to fetch tags:", e)

                message = await ctx.send(embed=embed)
                return message
        else:
            raise ValueError(f"no MusicBee activity found")



    async def applemusic_activity(self, ctx, member, show_tags, called_services, custom):
        activity_list = []
        for activity in member.activities:
            try:
                activity_list.append(str(activity.name))
            except:
                pass 
        if "iTunes Rich Presence for Discord" in activity_list:
            applemusic_richpresence = True
        else:
            applemusic_richpresence = False

        for activity in member.activities:
            if str(activity.type) == "ActivityType.playing":
                print(str(activity.name))
                if str(activity.name) == "Music": 
                    # FETCH ARTIST/ALBUM/SONG INFORMATION
                    try:
                        song = util.cleantext2(activity.details.replace("🎶", "").strip())
                        artist = util.cleantext2(activity.state.split("💿")[0].replace("👤","").strip())
                        album = util.cleantext2(activity.state.split("💿")[1].strip())

                        try:
                            if applemusic_richpresence:
                                song_url = f"https://music.apple.com/us/search?term={artist}%20{album}%20{song}".replace(" ","%20").replace("\\", "")
                            else:
                                searchterm = f"{artist}+{album}+{song}".replace(" ", "+").replace("\\", "").replace("/", "").replace("\\", "")
                                song_url = f"https://music.youtube.com/search?q={artist}+{album}+{song}".replace(" ", "+")

                            description = f"[{song}]({song_url})\nby **{artist}** | {album}"
                        except:
                            description = f"{song}\nby **{artist}** | {album}"
                    except:
                        description = f"{activity.details}\n{activity.state}"

                elif str(activity.name) == "Apple Music":
                    applemusic_richpresence = True

                    # FETCH ARTIST/ALBUM/SONG INFORMATION
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
                                artist = util.cleantext2(activity.state.strip())
                                song = util.cleantext2(activity.details.strip())
                                album = ""


                        try:
                            song_url = f"https://music.apple.com/us/search?term={artist}%20{album}%20{song}".replace(" ","%20").replace("\\", "")
                            description = f"[{song}]({song_url})\nby **{artist}** | {album}"
                        except:
                            description = f"{song}\nby **{artist}** | {album}"
                    except:
                        description = f"{activity.details}\n{activity.state}"

                else:
                    continue

                # Correct Album Title

                if len(album.strip()) > 5 and album.endswith(" - EP"):
                    album = album[:-5]

                # EMBED THINGS

                if applemusic_richpresence:

                    # CREATE EMBED
                    color = 0xFE647B
                    embed = discord.Embed(description=description, color = color)

                    # SET AUTHOR
                    embed.set_author(name=f"{member.display_name}'s Apple Music" , icon_url=member.avatar)
                    try:
                        cooldown = True
                        picture_list = await self.find_applemusic_pictures(ctx, artist, album, song, cooldown)
                        print(picture_list[0])
                        embed.set_thumbnail(url=picture_list[0].strip())
                    except Exception as e:
                        print("Error while trying to fetch album cover from Apple Music", e)
                        try:
                            embed.set_thumbnail(url=activity.large_image_url)
                        except Exception as e:
                            print(e)
                            try:
                                embed.set_thumbnail(url=activity.small_image_url)
                            except Exception as e:
                                embed.set_thumbnail(url="https://i.imgur.com/4Ims0Ed.png")
                                print(f"could not find image: {e}")

                    # HANDLE TAGS
                    if show_tags:
                        try:
                            tag_string = await self.fetch_tags(ctx, "applemusic", artist, album, song, None, None, called_services, custom, str(member.id))
                            try:
                                embed.set_footer(text = tag_string.strip())
                            except Exception as e:
                                print("Error while creating footer for applemusic np: ", e)
                        except Exception as e:
                            print("Error while trying to fetch tags:", e)
                else:
                    # EMBED
                    color = 0x808080
                    embed = discord.Embed(description=description, color = color)
                    embed.set_author(name=f"{member.display_name}'s unspecified player" , icon_url=member.avatar)
                    try:
                        embed.set_thumbnail(url=activity.large_image_url) 
                    except Exception as e:
                        print(e)
                        try:
                            embed.set_thumbnail(url=activity.small_image_url)
                        except Exception as e:
                            embed.set_thumbnail(url="https://i.imgur.com/0Djj7I6.jpg")
                            print(f"could not find image: {e}")

                    # HANDLE TAGS
                    if show_tags:
                        try:
                            tag_string = await self.fetch_tags(ctx, "unspecified", artist, album, song, None, None, called_services, custom, str(member.id))
                            try:
                                embed.set_footer(text = tag_string.strip())
                            except Exception as e:
                                print("Error while creating footer for unspecified player np (probably applemusic): ", e)
                        except Exception as e:
                            print("Error while trying to fetch tags:", e)


                message = await ctx.send(embed=embed)
                return message

        else:
            raise ValueError(f"no Apple Music activity found")



    async def lastfm_apifetch(self, ctx, member, show_tags, called_services, cooldown, custom):
        # FETCH LFM USERNAME

        con = sqlite3.connect('databases/npsettings.db')
        cur = con.cursor()
        lfm_list = [[item[0],item[1]] for item in cur.execute("SELECT lfm_name, lfm_link FROM lastfm WHERE id = ?", (str(member.id),)).fetchall()]

        if len(lfm_list) == 0:
            raise ValueError(f"user has not set lastfm")
            return

        lfm_name = lfm_list[0][0]

        try:
            # FETCH INFORMATION VIA API
            payload = {
                'method': 'user.getRecentTracks',
                'user': lfm_name,
                'limit': "1",
            }
            response = await util.lastfm_get(ctx, payload, cooldown)
            if response == "rate limit":
                return
            rjson = response.json()
            tjson = rjson['recenttracks']['track'][0] # track json

            # PARSE INFO

            song = tjson['name']
            song_link = tjson['url']
            artist = tjson['artist']['#text']
            album = tjson['album']['#text']
            album_cover = tjson['image'][-1]['#text']

            #musicbrainz ids
            mb_track_id = tjson['mbid'] 
            mb_album_id = tjson['album']['mbid']
            mb_artist_id = tjson['artist']['mbid']
            musicbrainz_ids = [mb_artist_id, mb_album_id, mb_track_id]

            try:
                if tjson['@attr']['nowplaying'] == "true":
                    recency = "current track"
                else:
                    recency = "last track"
            except:
                recency = "last track"

            # MAKE EMBED

            try:
                color = member.color
            except:
                color = 0xFFFFFF
            description = f"[{song}]({song_link})\nby **{util.cleantext2(artist)}** | {album}"
            embed = discord.Embed(description=description, color = color)
            embed.set_author(name=f"{lfm_name}'s {recency} on LastFM" , icon_url=member.avatar)
            try:
                default_whitestar_image = "https://lastfm.freetls.fastly.net/i/u/68s/2a96cbd8b46e442fc41c2b86b821562f.png"
                if album_cover != "" and not album_cover.endswith("2a96cbd8b46e442fc41c2b86b821562f.png"):
                    embed.set_thumbnail(url=album_cover)
                else:
                    # try to fetch from database
                    artist_compact = util.compactnamefilter(artist, "artist", "alias")
                    album_compact = util.compactnamefilter(album, "album")
                    _, _, cover_url, details, _, last_updated = await util.get_album_details_from_compact(artist_compact, album_compact)
                    try:
                        now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())
                        if last_updated > now - 180*24*60*60:
                            embed.set_thumbnail(url=cover_url)
                        else:
                            raise ValueError("image too old")
                    except Exception as e:
                        embed.set_thumbnail(url=default_whitestar_image)
            except Exception as e:
                print(e)

            # HANDLE TAGS

            if show_tags:
                try:
                    tag_string = await self.fetch_tags(ctx, "lastfm", artist, album, song, None, musicbrainz_ids, called_services, custom, str(member.id))
                    try:
                        if tag_string != "":
                            embed.set_footer(text = tag_string.strip())
                    except Exception as e:
                        print("Error while creating footer for spotify tags and listener stats: ", e)
                except Exception as e:
                    print("Unable to fetch tags", e)

            message = await ctx.send(embed=embed)
            return message

        except Exception as e:
            print("Error:", e)
            cooldown = False
            message = await self.lastfm_webscrape(ctx, member, show_tags, called_services, cooldown, custom) # last argument for whether a cooldown is needed
            return message



    async def lastfm_webscrape(self, ctx, member, show_tags, called_services, cooldown, custom):

        # FETCH LFM USERNAME

        con = sqlite3.connect('databases/npsettings.db')
        cur = con.cursor()
        lfm_list = [[item[0],item[1]] for item in cur.execute("SELECT lfm_name, lfm_link FROM lastfm WHERE id = ?", (str(member.id),)).fetchall()]

        if len(lfm_list) == 0:
            raise ValueError(f"user has not set lastfm")
            return

        lfm_name = lfm_list[0][0]

        # WEBSCRAPE INFORMATION

        try:
            if cooldown:
                try: # cooldown to not trigger actual rate limits or IP blocks
                    await util.cooldown(ctx, "lastfm")
                except Exception as e:
                    await util.cooldown_exception(ctx, e, "LastFM")
                    return

            burp0_url = f"https://www.last.fm:443/user/{lfm_name}"
            burp0_headers = {"Sec-Ch-Ua": "\"Chromium\";v=\"121\", \"Not A(Brand\";v=\"99\"", "Sec-Ch-Ua-Mobile": "?0", "Sec-Ch-Ua-Platform": "\"Windows\"", "Upgrade-Insecure-Requests": "1", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.160 Safari/537.36", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7", "Sec-Fetch-Site": "none", "Sec-Fetch-Mode": "navigate", "Sec-Fetch-User": "?1", "Sec-Fetch-Dest": "document", "Accept-Encoding": "gzip, deflate, br", "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7", "Priority": "u=0, i", "Connection": "close"}
            response = requests.get(burp0_url, headers=burp0_headers)

            # FETCH INFORMATION DIRECTLY FROM PROFILE PAGE

            if "/pro/modal?action=scrobbling-now-theirs" in response.text:
                recency = "current track"
            else:
                recency = "last track"

            response_filtered = response.text.split("Recent Tracks")[1]
            soup = BeautifulSoup(response_filtered, "html.parser")

            album_soup = soup.find("img")
            album = util.cleantext2(html.unescape(album_soup['alt']))
            album_cover = album_soup['src']

            try:
                a = soup.find('a', href=True)
                song_link = "https://www.last.fm" + a['data-track-url']
                song = a['data-track-name']
                artist = a['data-artist-name']
            except:
                i = 0
                for a in soup.find_all('a', href=True):
                    i += 1
                    if i == 1:
                        pass
                    elif i == 2:
                        song_link = "https://www.last.fm" + a['href']
                        song = a['title']
                    elif i == 3:
                        artist = a['title']
                    else:
                        break

            # CHECK ALBUM COVER qualities

            album_cover2 = album_cover.replace("u/64s/", "u/ar0/")
            if not util.is_url_image(album_cover2):
                album_cover2 = album_cover.replace("u/64s/", "u/500x500/")
                if not util.is_url_image(album_cover2):
                    album_cover2 = ""

            print(f"SONG: {song}\nARTIST: {artist}\nALBUM: {album}\n{album_cover}\n{album_cover2}")

        except Exception as e:
            print(e)
            raise ValueError(f"an error ocurred while trying to fetch song from {lfm_name}'s lastfm")
            return

        # MAKE EMBED

        try:
            color = member.color
        except:
            color = 0xFFFFFF
        description = f"[{song}]({song_link})\nby **{util.cleantext2(artist)}** | {album}"
        embed = discord.Embed(description=description, color = color)
        embed.set_author(name=f"{lfm_name}'s {recency} on LastFM" , icon_url=member.avatar)
        try:
            default_whitestar_image = "https://lastfm.freetls.fastly.net/i/u/68s/2a96cbd8b46e442fc41c2b86b821562f.png"
            if album_cover2 != "" and not album_cover2.endswith("2a96cbd8b46e442fc41c2b86b821562f.png"):
                try:
                    embed.set_thumbnail(url=album_cover2.strip())
                except:
                    embed.set_thumbnail(url=album_cover.strip())
            else:
                # try to fetch from database
                artist_compact = util.compactnamefilter(artist, "artist", "alias")
                album_compact = util.compactnamefilter(album, "album")
                _, _, cover_url, details, _, last_updated = await util.get_album_details_from_compact(artist_compact, album_compact)
                try:
                    now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())
                    if last_updated > now - 180*24*60*60:
                        embed.set_thumbnail(url=cover_url)
                    else:
                        raise ValueError("image too old")
                except Exception as e:
                    embed.set_thumbnail(url=default_whitestar_image)
        except Exception as e:
            print(e)
            try:
                embed.set_thumbnail(url="https://www.last.fm/static/images/defaults/player_default_album.430223706b14.png")
            except:
                pass

        # HANDLE TAGS

        if show_tags:
            try:
                tag_string = await self.fetch_tags(ctx, "lastfm", artist, album, song, None, None, called_services, custom, str(member.id))
                try:
                    embed.set_footer(text = tag_string.strip())
                except Exception as e:
                    print("Error while creating footer for spotify tags and listener stats: ", e)
            except Exception as e:
                print("Unable to fetch tags", e)

        message = await ctx.send(embed=embed)
        return message



    async def spotify_activity(self, ctx, member, show_tags, called_services, custom):
        for activity in member.activities:
            if isinstance(activity, Spotify):

                # MAIN EMBED

                song = util.cleantext2(activity.title)
                artist = util.cleantext2(activity.artist)
                album = util.cleantext2(activity.album)
                track_id = activity.track_id

                songdescription = f"[{song}]({activity.track_url})\nby **{artist}** | {album}"
                embed = discord.Embed(
                                description=songdescription.strip(),
                                color = activity.color) #spotify green
                embed.set_thumbnail(url=activity.album_cover_url)
                embed.set_author(name=f"{member.display_name}'s Spoofy" , icon_url=member.avatar)

                # HANDLE TAGS
                if show_tags:
                    try:
                        tag_string = await self.fetch_tags(ctx, "spotify", artist, album, song, track_id, None, called_services, custom, str(member.id))
                        try:
                            embed.set_footer(text = tag_string.strip())
                        except Exception as e:
                            print("Error while creating footer for spotify tags and listener stats: ", e)
                    except Exception as e:
                        print("Unable to fetch tags:", e)
                        print(traceback.format_exc())

                # SEND EMBED

                message = await ctx.send(embed=embed)
                return message
        else:
            raise ValueError("no Spotify activity found")

        

    #################################################################################################################################

    #################################################################################################################################

    #################################################################################################################################

    #################################################################################################################################

    #################################################################################################################################

    #################################################################################################################################

    #################################################################################################################################

    ####################################################### TAGGING FUNCTIONS #######################################################



    async def fetch_tags(self, ctx, np_service, artist, album, song, spotify_track_id, musicbrainz_ids, called_services, custom, np_user_id):
        """
            decide where to fetch genre tags from and retrieve
            return string
        """
        async with ctx.typing():
            user_id = str(ctx.message.author.id)
            try:
                mbid = musicbrainz_ids[0]
            except:
                mbid = None

            #default settings: (last 3 added later)
            tagsetting_list = [["", "", "standard", "standard", "standard", "standard", "off", "off", "off", "off", "standard_substitute", "off", "off", "off", "off", "standard_substitute", "off", "off"]]
            
            if custom:
                con = sqlite3.connect('databases/npsettings.db')
                cur = con.cursor()
                custom_tagsetting_list = [[item[0],item[1],item[2],item[3],item[4],item[5],item[6],item[7],item[8],item[9],item[10],item[11],item[12],item[13],item[14],item[15],item[16],item[17]] for item in cur.execute("SELECT id, name, spotify_monthlylisteners, spotify_genretags, lastfm_listeners, lastfm_total_artistplays, lastfm_artistscrobbles, lastfm_albumscrobbles, lastfm_trackscrobbles, lastfm_rank, musicbrainz_tags, musicbrainz_area , musicbrainz_date , rym_genretags, rym_albumrating, lastfm_tags, redundancy_filter, crown FROM tagsettings WHERE id = ?", (user_id,)).fetchall()]
                if len(custom_tagsetting_list) == 0:
                    username = util.cleantext2(str(ctx.message.author.name))
                    cur.execute("INSERT INTO tagsettings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (user_id, username, "standard", "standard", "standard", "standard", "on", "on", "on", "on", "standard_substitute", "standard_substitute", "off", "off", "on", "off", "on", "on"))
                    con.commit()
                    await util.changetimeupdate()
                else:
                    tagsetting_list = custom_tagsetting_list

            # CHECK WHICH TAGS TO FETCH

            tagsettings = tagsetting_list[0]
            spotify_monthlylisteners = tagsettings[2].lower().strip()
            spotify_genretags = tagsettings[3].lower().strip()
            lastfm_listeners = tagsettings[4].lower().strip() 
            lastfm_total_artistplays = tagsettings[5].lower().strip()
            lastfm_artistscrobbles = tagsettings[6].lower().strip()
            lastfm_albumscrobbles = tagsettings[7].lower().strip()
            lastfm_trackscrobbles = tagsettings[8].lower().strip()
            lastfm_rank = tagsettings[9].lower().strip()
            musicbrainz_tags = tagsettings[10].lower().strip() 
            musicbrainz_area = tagsettings[11].lower().strip() 
            musicbrainz_date = tagsettings[12].lower().strip() 
            rym_genretags = tagsettings[13].lower().strip() 
            rym_albumrating = tagsettings[14].lower().strip() 
            lastfm_tags = tagsettings[15].lower().strip() # added later
            redundancy_filter = tagsettings[16].lower().strip() # added later
            crown = tagsettings[17].lower().strip() # added later

            tag_settings_dict = { # only needs those that fetch from API
                                "spotify_monthlylisteners": spotify_monthlylisteners, 
                                "spotify_genretags": spotify_genretags, 
                                "lastfm_listeners": lastfm_listeners, 
                                "lastfm_total_artistplays": lastfm_total_artistplays, 
                                #"lastfm_artistscrobbles": lastfm_artistscrobbles, 
                                #"lastfm_albumscrobbles": lastfm_albumscrobbles, 
                                #"lastfm_trackscrobbles": lastfm_trackscrobbles, 
                                #"lastfm_rank": lastfm_rank, 
                                "lastfm_tags": lastfm_tags,
                                "musicbrainz_tags": musicbrainz_tags, 
                                "musicbrainz_area": musicbrainz_area, 
                                "musicbrainz_date": musicbrainz_date, 
                                "rym_genretags": rym_genretags, 
                                #"rym_albumrating": rym_albumrating,
                                #"redundancy_filter": redundancy_filter,
                                #"crown": crown,
                                }
            tag_services_dict = {
                                "lastfm": False, 
                                "musicbrainz": False, 
                                "spotify": False, 
                                "rym": False,
                                }

            if ";" in artist and artist[0] != ";":
                subst_artist = artist.split(";",1)[0]
            else:
                subst_artist = artist

            substitute_tags = []
            for setting in tag_settings_dict:
                service = setting.split("_")[0]

                if tag_settings_dict[setting] == "on":
                    tag_services_dict[service] = True

                elif tag_settings_dict[setting] == "standard":
                    if np_service.lower() == service:
                        tag_services_dict[service] = True
                        tag_settings_dict[setting] = "on"
                    else:
                        tag_settings_dict[setting] = "off"

                elif tag_settings_dict[setting] == "callable":
                    if service in called_services:
                        tag_services_dict[service] = True
                        tag_settings_dict[setting] = "on"
                    else:
                        tag_settings_dict[setting] = "off"

                elif tag_settings_dict[setting] == "standard_substitute": # same as standard but also acts as substitute if tags are missing
                    if np_service.lower() == service:
                        tag_services_dict[service] = True
                        tag_settings_dict[setting] = "on"
                    else:
                        tag_settings_dict[setting] = "off"
                        substitute_tags.append(service)

            substitute_tags = list(dict.fromkeys(substitute_tags))

            anything_to_fetch = False
            for service in tag_services_dict:
                if tag_services_dict[service]:
                    anything_to_fetch = True

            if not anything_to_fetch and len(substitute_tags) == 0:
                return ""

            print("Fetching tags (primary):", tag_services_dict)
            print("Fetching tags (secondary):", substitute_tags)

            # FETCH TAGS FROM APIs

            genre_tags = {}
            listener_stats = []
            year = ""
            area = ""
            user_stats = ""

            for tagservice in tag_services_dict:
                if tag_services_dict[tagservice]:
                    fetching = True
                    if tagservice.lower() == "lastfm" and np_service.lower() == "lastfm":
                        pass # cooldown was already checked in parent function
                    else:
                        try:
                            await util.cooldown(ctx, tagservice)
                        except Exception as e:
                            fetching = False

                    # DO THE ACTUAL TAG FETCHING

                    if fetching:
                        
                        if tagservice == "spotify":
                            if spotify_track_id is None or spotify_track_id == "":
                                spotify_track_id = await self.fetch_spotify_track_id(artist, album, song)

                            if spotify_track_id != "":
                                g_tags = False
                                listenertags = False
                                if tag_settings_dict["spotify_genretags"] == "on":
                                    g_tags = True
                                if tag_settings_dict["spotify_monthlylisteners"] == "on":
                                    listenertags = True
                                
                                genretag_list, ml_string = await self.fetch_spotify_tags(spotify_track_id, g_tags, listenertags)

                                try:
                                    if redundancy_filter == "on" and len(genretag_list) > 1:
                                        genretag_list = util.filter_tagredundancies(genretag_list)
                                except Exception as e:
                                    print("Error while trying to remove redundancies from tag list:", e)

                                if len(genretag_list) > 0:
                                    genre_tags["spotify"] = f"{self.tagseparator}".join(genretag_list)

                                if ml_string != "":
                                    if tagservice != np_service:
                                        new_ml_string = ml_string.split("monthly")[0] + "monthly spoofy listeners"
                                        listener_stats.append(new_ml_string.strip())
                                    else:
                                        listener_stats.append(ml_string.strip())

                        elif tagservice == "lastfm":
                            lfm_listeners = False
                            lfm_playcount = False
                            lfm_tags = False
                            if tag_settings_dict["lastfm_listeners"] == "on":
                                lfm_listeners = True
                            if tag_settings_dict["lastfm_total_artistplays"] == "on":
                                lfm_playcount = True
                            if tag_settings_dict["lastfm_tags"] == "on":
                                lfm_tags = True

                            if lfm_listeners or lfm_playcount:
                                if np_service.lower() == "lastfm":
                                    cooldown = False
                                else:
                                    cooldown = True
                                try:
                                    listeners, total_scrobbles, lfm_genre_tag_list = await self.fetch_lastfm_data_via_api(ctx, mbid, subst_artist, song, cooldown)
                                    lfm_fetch_client = "api"
                                except Exception as e:
                                    print(f"Probably no Last.fm API credentials, switching to Web Scraping information.\n(Exception message: {e})")
                                    listeners, total_scrobbles, lfm_genre_tag_list = await self.fetch_lastfm_data_via_web(ctx, subst_artist, cooldown)
                                    lfm_fetch_client = "web"

                                if listeners.strip() != "" and lfm_listeners:
                                    listeners_readable = util.shortnum(listeners)
                                    listener_stats.append(f"{listeners_readable} lfm listeners")

                                if total_scrobbles.strip() != "" and lfm_playcount:
                                    total_scrobbles_readable = util.shortnum(total_scrobbles)
                                    listener_stats.append(f"{total_scrobbles_readable} total scrobbles")

                                if lfm_tags and len(lfm_genre_tag_list) > 0:
                                    try:
                                        if redundancy_filter == "on" and len(lfm_genre_tag_list) > 1:
                                            lfm_genre_tag_list = util.filter_tagredundancies(lfm_genre_tag_list)
                                    except Exception as e:
                                        print("Error while trying to remove redundancies from tag list:", e)
                                    genre_tags["lastfm"] = f"{self.tagseparator}".join(lfm_genre_tag_list)

                        elif tagservice == "musicbrainz":
                            if tag_settings_dict['musicbrainz_date'] == "on":
                                checkyear = True
                            else:
                                checkyear = False
                            if tag_settings_dict['musicbrainz_area'] == "on":
                                checkarea = True
                            else:
                                checkarea = False
                            if tag_settings_dict['musicbrainz_tags'] == "on":
                                checktags = True
                            else:
                                checktags = False
                            cooldown = False
                            mbid, genretag_list, year, area = await self.fetch_musicbrainz_tags(ctx, mbid, subst_artist, album, song, checkyear, checkarea, checktags, cooldown)

                            try:
                                if redundancy_filter == "on" and len(genretag_list) > 1:
                                    genretag_list = util.filter_tagredundancies(genretag_list)
                            except Exception as e:
                                print("Error while trying to remove redundancies from tag list:", e)

                            if len(genretag_list) > 0:
                                genre_tags["musicbrainz"] = f"{self.tagseparator}".join(genretag_list)

                        elif tagservice == "rym": # for genre tags
                            #under construction: hopefully when RYM provides an API or isn't so block-happy when scraping
                            pass

                        else:
                            print(f"Error: tag service {tagservice} unknown")

            # SUBSTITUTE TAGS

            if len(genre_tags) == 0 and len(substitute_tags) > 0: # if no genre tags found, try substitutes
                print("searching for substitute tags...")
                for setting in substitute_tags:
                    if setting == "lastfm":
                        cooldown = False

                        try:
                            listeners, total_scrobbles, lfm_genre_tag_list = await self.fetch_lastfm_data_via_api(ctx, mbid, subst_artist, song, cooldown)
                            lfm_fetch_client = "api"
                        except Exception as e:
                            try:
                                print(f"Probably no Last.fm API credentials, switching to Web Scraping information.\n(Exception message: {e})")
                                listeners, total_scrobbles, lfm_genre_tag_list = await self.fetch_lastfm_data_via_web(ctx, subst_artist, cooldown)
                                lfm_fetch_client = "web"
                            except Exception as e:
                                print("Error while trying to fetch subst. tags from lastfm:", e)
                                continue
                                
                        try:
                            if redundancy_filter == "on" and len(lfm_genre_tag_list) > 1:
                                lfm_genre_tag_list = util.filter_tagredundancies(lfm_genre_tag_list)
                        except Exception as e:
                            print("Error while trying to remove redundancies from tag list:", e)

                        if len(lfm_genre_tag_list) > 0:
                            genre_tags["lastfm"] = f"{self.tagseparator}".join(lfm_genre_tag_list)
                            #print(genre_tags["lastfm"])
                            if genre_tags["lastfm"].strip() != "":
                                break

                    elif setting == "musicbrainz":
                        checkyear = False
                        checkarea = False
                        checktags = True
                        cooldown = False

                        try:
                            mbid, genretag_list, year, area = await self.fetch_musicbrainz_tags(ctx, mbid, subst_artist, album, song, checkyear, checkarea, checktags, cooldown)
                        except Exception as e:
                            print("Error while trying to fetch subst. tags from musicbrainz:", e)
                            continue

                        try:
                            if redundancy_filter == "on" and len(genretag_list) > 1:
                                genretag_list = util.filter_tagredundancies(genretag_list)
                        except Exception as e:
                            print("Error while trying to remove redundancies from tag list:", e)

                        if len(genretag_list) > 0:
                            genre_tags["musicbrainz"] = f"{self.tagseparator}".join(genretag_list)
                            #print(genre_tags["musicbrainz"])
                            if genre_tags["musicbrainz"].strip() != "":
                                break

                    elif setting == "spotify":
                        g_tags = True
                        listenertags = False
                        try:
                            spotify_track_id = await self.fetch_spotify_track_id(subst_artist, album, song)
                            genretag_list, ml_string = await self.fetch_spotify_tags(spotify_track_id, g_tags, listenertags)
                        except Exception as e:
                            print("Error while trying to fetch subst. tags from spotify:", e)
                        if len(genretag_list) > 0:
                            genre_tags["spotify"] = f"{self.tagseparator}".join(genretag_list)
                            break

                    elif setting == "rym":
                        pass # under construction

            # TAG DICT TO STRING

            for key in genre_tags:
                if genre_tags[key].strip() == "":
                    del genre_tags[key]

            genre_tag_string = ""

            if len(genre_tags) > 1 or (len(genre_tags) == 1 and np_service not in genre_tags):
                for service in genre_tags:
                    if service == "spotify" and genre_tags["spotify"].strip() != "":
                        genre_tag_string += "\nSpoofy: " + genre_tags["spotify"]

                    elif service == "lastfm" and genre_tags["lastfm"].strip() != "":
                        try:
                            if lfm_fetch_client == "web":
                                add_asterisk = True
                            else:
                                add_asterisk = False
                        except:
                            add_asterisk = False
                        if add_asterisk:
                            genre_tag_string += "\nLFM*: " + genre_tags["lastfm"]
                        else:
                            genre_tag_string += "\nLFM: " + genre_tags["lastfm"]

                    elif service == "musicbrainz" and genre_tags["musicbrainz"].strip() != "":
                        genre_tag_string += "\nMB: " + genre_tags["musicbrainz"]

                    elif service == "rym" and genre_tags["rym"].strip() != "":
                        genre_tag_string += "\nRYM: " + genre_tags["rym"]

                if genre_tag_string.strip() == "":
                    genre_tag_string = "\nno genre tags found"
            else:
                for service in genre_tags:
                    genre_tag_string += "\n" + genre_tags[service]
                    if genre_tags[service].strip() == "":
                        genre_tag_string = "\nno genre tags found" # only do that if there actually was a service that looked for tags

            # USER STATS

            conFM = sqlite3.connect('databases/scrobbledata.db')
            curFM = conFM.cursor()

            conFM2 = sqlite3.connect('databases/scrobbledata_releasewise.db')
            curFM2 = conFM2.cursor()

            conFM3 = sqlite3.connect('databases/scrobbledata_trackwise.db')
            curFM3 = conFM3.cursor()

            conSS = sqlite3.connect('databases/scrobblestats.db')
            curSS = conSS.cursor()

            if np_user_id == None:
                np_user_id == user_id

            try:
                lfm_name, scrobble_status = util.get_lfmname(np_user_id)
            except Exception as e:
                print("Error while calling util.get_lfmname():", e)
                lfm_name = None
                scrobble_status = None

            if lfm_name != None:
                rank = None
                crown_holder = None
                crown_count = None
                artistcount = None
                albumcount = None
                trackcount = None

                if (crown == "on" or crown == "only_own") or lastfm_rank == "on":
                    try:
                        rank, crown_holder, crown_count = util.get_rank(ctx, lfm_name, subst_artist)
                    except Exception as e:
                        print("Error while calling util.get_rank():", e)
                        rank = ""
                        crown_holder = None
                        crown_count = None

                if crown == "on" or crown == "only_own":
                    mention_crownuser = False
                    crown_text = ""
                    emoji = util.emoji("crown")
                    if emoji == "" or (emoji.startswith("<") and emoji.endswith(">") and emoji.count(":") > 1):
                        emoji = "♕"

                    if scrobble_status not in ["wk_banned", "crown_banned"]:
                        if (type(crown_holder) is str) and (crown_holder.strip() != ""):
                            if (str(lfm_name).upper().strip() == crown_holder.upper().strip()):
                                user_stats += f"{emoji} "
                            elif crown == "on":
                                mention_crownuser = True
                                if crown_count is not None:
                                    crown_holder_discord = util.convert_lfmname_to_discordname(ctx, crown_holder)
                                    crown_count_formatted = "{:,}".format(crown_count)
                                    crown_text = f"{self.tagseparator} {emoji}{crown_count_formatted} ({crown_holder_discord})"

                if lastfm_artistscrobbles == "on":
                    try:
                        result = curFM2.execute(f"SELECT SUM(count) FROM [{lfm_name}] WHERE artist_name = ?", (util.compactnamefilter(subst_artist,"artist"),))
                        rtuple = result.fetchone()
                        try:
                            artistcount = int(rtuple[0])
                        except:
                            artistcount = 0

                        if artistcount == 1:
                            user_stats += f"{artistcount} artist play "
                        else:
                            user_stats += f"{artistcount} artist plays "
                    except Exception as e:
                        print("Error while trying to fetch artist plays:", e)
                        lastfm_artistscrobbles = "off"
                
                if lastfm_albumscrobbles == "on" and album.strip() != "":
                    try:
                        result = curFM2.execute(f"SELECT count FROM [{lfm_name}] WHERE artist_name = ? AND album_name = ?", (util.compactnamefilter(subst_artist,"artist"),util.compactnamefilter(album,"album")))
                        rtuple = result.fetchone()
                        try:
                            albumcount = int(rtuple[0])
                        except:
                            albumcount = 0

                        if artistcount is None:
                            if albumcount == 1:
                                user_stats += f"{albumcount} album play "  
                            else:
                                user_stats += f"{albumcount} album plays "
                        else:
                            if lastfm_trackscrobbles == "on":
                                user_stats += f"(album: {albumcount}, "
                            else:
                                user_stats += f"(album: {albumcount}) "
                    except Exception as e:
                        print("Error while trying to fetch album plays:", e)

                if lastfm_trackscrobbles == "on":
                    try:
                        result = curFM3.execute(f"SELECT count FROM [{lfm_name}] WHERE artist_name = ? AND track_name = ?", (util.compactnamefilter(subst_artist,"artist"),util.compactnamefilter(song,"track")))
                        #result = curFM.execute(f"SELECT COUNT(id) FROM [{lfm_name}] WHERE {util.compact_sql('artist_name')} = {util.compact_sql('?')} AND {util.compact_sql('track_name')} = {util.compact_sql('?')}", (subst_artist,song))
                        rtuple = result.fetchone()
                        try:
                            trackcount = int(rtuple[0])
                        except:
                            trackcount = 0

                        if artistcount is None and albumcount is None:
                            if trackcount == 1:
                                user_stats += f"{trackcount} track play "  
                            else:
                                user_stats += f"{trackcount} track plays "
                        else:
                            if lastfm_albumscrobbles == "on" and album.strip() != "" and "(album:" in user_stats:
                                user_stats += f"track: {trackcount}) "
                            else:
                                user_stats += f"(track: {trackcount}) "
                    except Exception as e:
                        print("Error while trying to fetch track plays:", e)
                        if "(album:" in user_stats and user_stats.endswith(", "):
                            user_stats = user_stats[:-2] + ") "

                if lastfm_rank == "on" and type(rank) == str:
                    if crown == "on":
                        if mention_crownuser:
                            # a different user is crown holder:
                            if rank != "":
                                if len(crown_text) <= 29:
                                    rank2 = "server rank: " + rank.replace("[", "").replace("]", "")
                                else:
                                    rank2 = "rank: " + rank.replace("[", "").replace("]", "")
                                user_stats += f"\n{rank2} {crown_text}"
                        else:
                            # command invoker is crown holder:
                            user_stats += rank
                            #if len(user_stats) > 42:
                            #    user_stats += "\nserver rank: " + rank.replace("[", "").replace("]", "")
                            #else:
                            #    user_stats += rank

            if rym_albumrating == "on":
                # rym import under construction
                pass

            # PUTTING TOGETHER INFORMATION

            art_info = []
            if area.strip() != "":
                art_info.append(area.strip())
            if year.strip() != "":
                art_info.append(year.strip())
            listener_stats_string = f"{self.tagseparator}".join(listener_stats + art_info).strip()

            if genre_tag_string.strip() == "" and (tag_settings_dict["spotify_genretags"] == "on" or tag_settings_dict["musicbrainz_tags"] == "on" or tag_settings_dict["rym_genretags"] == "on" or tag_settings_dict["lastfm_tags"] == "on" or len(substitute_tags) > 0):
                genre_tag_string = "\nno genre tags found"

            if user_stats.strip() == "":
                user_stats = ""
            else:
                user_stats = user_stats.strip() + "\n"

            #tag_string = user_stats + listener_stats_string + genre_tag_string
            footer_list = [user_stats.strip(), listener_stats_string.strip(), genre_tag_string.strip()]
            while "" in footer_list:
                footer_list.remove("")
            tag_string = '\n'.join(footer_list)
            if len(tag_string) > 2048:
                tag_string = tag_string[:2045] + "..."

            return tag_string[:2048]



    async def parse_called_services(self, args):
        try:
            if len(args) == 0:
                return []

            argument_list = []
            get_arg = False
            for arg in args:
                if get_arg:
                    argument_list.append(arg.lower())
                if arg.lower() in ["get:", "call:"]:
                    get_arg = True

            if len(argument_list) == 0:
                return []

            delimiters = [",",";","|"," "]
            argument_string = ' '.join(argument_list)
            for delimiter in delimiters:
                argument_string = ' '.join(argument_string.split(delimiter))

            parsed_argument_list = argument_string.split()

            called_services = []
            for arg in parsed_argument_list:
                if arg.strip() in ["spotify", "spoofy"]:
                    called_services.append("spotify")
                if arg.strip() in ["lasftm", "lastfm", "lfm"]:
                    called_services.append("lastfm")
                if arg.strip() in ["musicbrainz", "msuicbrainz", "musicbrains"]:
                    called_services.append("musicbrainz")
                if arg.strip() in ["rateyourmusic", "rym"]:
                    called_services.append("rym")
            called_services = list(dict.fromkeys(called_services))

            return called_services

        except Exception as e:
            print("Error:", e)
            return []




    async def fetch_spotify_tags(self, track_id, genre_tags, listener_stats):
        """fetch spotify genre tags and spotify monthly listeners
        
        returns list of genre_tags and string of listener stats
        """

        if genre_tags:
            try:
                ClientID = os.getenv("Spotify_ClientID")
                ClientSecret = os.getenv("Spotify_ClientSecret")
                if ClientID is None:
                    raise ValueError("No SpotiPy API provided")
            except Exception as e:
                print("Error:", e)
                return [], ""

            print("initialising authentication")
            auth_manager = SpotifyClientCredentials(client_id=ClientID, client_secret=ClientSecret)
            sp = spotipy.Spotify(auth_manager=auth_manager)

            print(f"getting track via id: {track_id}")
            track = sp.track(f"spotify:track:{track_id}")
            artist = sp.artist(track["artists"][0]["external_urls"]["spotify"])
            print("artist genres:", artist["genres"])
            album = sp.album(track["album"]["external_urls"]["spotify"])
            print("album genres:", album["genres"])
            print("album release-date:", album["release_date"])

            print("processing genre lists")
            genres_wo_duplicates = []
            for genre in artist["genres"] + album["genres"]:
                if genre in genres_wo_duplicates:
                    pass 
                else:
                    genres_wo_duplicates.append(genre)

            if listener_stats:
                artist_id = str(artist["id"])
                listenerstring = await self.fetch_spotify_listeners(artist_id, "")
                return genres_wo_duplicates, listenerstring
            else:
                return genres_wo_duplicates, ""

        elif listener_stats:
            listenerstring = await self.fetch_spotify_listeners("", track_id)
            return [], listenerstring

        else:
            return [], ""



    async def fetch_spotify_track_id(self, artist_string, album, track):

        # INITIALISE

        try:
            ClientID = os.getenv("Spotify_ClientID")
            ClientSecret = os.getenv("Spotify_ClientSecret")
            if ClientID is None:
                raise ValueError("Could not initialise Spotipy Crednetials")
        except:
            raise ValueError("Could not initialise Spotipy Crednetials")

        auth_manager = SpotifyClientCredentials(client_id=ClientID, client_secret=ClientSecret)
        sp = spotipy.Spotify(auth_manager=auth_manager)

        query = f"artist:{artist_string} track:{track}"
        response = sp.search(q=query, type="track", limit=10)
        item_list = response['tracks']['items']

        artist_list = artist_string.split(";")
        search_track_id = ""

        if len(item_list) == 0:
            return ""

        # GO THROUGH SEARCH RESULTS

        # check if album matches as well

        for item in item_list:
            search_album = item['album']['name']
            if util.alphanum(search_album,"lower") == util.alphanum(album,"lower"):
                search_track_id = item['id']
                break
        else:
            # check if album matches at least without info in brackets

            for item in item_list:
                search_album = item['album']['name']
                if util.alphanum(util.cut_xtrainfo(search_album),"lower") == util.alphanum(util.cut_xtrainfo(album),"lower") and util.alphanum(util.cut_xtrainfo(search_album),"lower") != "":
                    search_track_id = item['id']
                    break
            else:
                # check if at least track and artist(s) match

                search_track_name = util.alphanum(util.cut_xtrainfo(item_list[0]['name']),"lower")
                search_artists = item_list[0]['artists']
                search_artist_names = []
                for search_artist in search_artists:
                    search_artist_names.append(util.alphanum(search_artist['name'],"lower"))

                if search_track_name != "" and search_track_name == util.alphanum(util.cut_xtrainfo(track),"lower"):
                    if len(artist_list) <= 1:
                        if util.alphanum(artist_string,"lower") in search_artist_names:
                            search_track_id = item_list[0]['id']
                    else:
                        found = True
                        for artist in artist_list:
                            a = util.alphanum(artist,"lower")
                            if a not in search_artist_names:
                                found = False
                        if found:
                            search_track_id = item_list[0]['id']

        return search_track_id

        

    async def fetch_spotify_listeners(self, artist_id, track_id):
        """getting monthly listener data"""
        
        if artist_id.strip() == "" and track_id.strip() == "":
            return ""

        if artist_id.strip() == "" and track_id.strip() != "":
            # fetch artist id from track id
            try:
                session = requests.session()
                burp0_url = f"https://open.spotify.com:443/track/{track_id}"
                burp0_headers = {"Sec-Ch-Ua": "\"Chromium\";v=\"111\", \"Not(A:Brand\";v=\"8\"", "Sec-Ch-Ua-Mobile": "?0", "Sec-Ch-Ua-Platform": "\"Windows\"", "Upgrade-Insecure-Requests": "1", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.5563.111 Safari/537.36", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7", "Sec-Fetch-Site": "none", "Sec-Fetch-Mode": "navigate", "Sec-Fetch-User": "?1", "Sec-Fetch-Dest": "document", "Accept-Encoding": "gzip, deflate", "Accept-Language": "en-US;q=0.8,en;q=0.7", "Connection": "close"}
                response = session.get(burp0_url, headers=burp0_headers)

                if not "/artist/" in response.text:
                    return ""

                artist_id = response.text.split("/artist/")[1].split('"')[0]
            except Exception as e:
                print("Error while trying to fetch artist link from track id: ", e)
                return ""

        # fetch listener stats from artist page
        monthly_listeners = "?"
        try:
            session = requests.session()
            burp0_url = f"https://open.spotify.com:443/artist/{artist_id}"
            burp0_headers = {"Sec-Ch-Ua": "\"Chromium\";v=\"111\", \"Not(A:Brand\";v=\"8\"", "Sec-Ch-Ua-Mobile": "?0", "Sec-Ch-Ua-Platform": "\"Windows\"", "Upgrade-Insecure-Requests": "1", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.5563.111 Safari/537.36", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7", "Sec-Fetch-Site": "none", "Sec-Fetch-Mode": "navigate", "Sec-Fetch-User": "?1", "Sec-Fetch-Dest": "document", "Accept-Encoding": "gzip, deflate", "Accept-Language": "en-US;q=0.8,en;q=0.7", "Connection": "close"}
            response = session.get(burp0_url, headers=burp0_headers)

            soup = BeautifulSoup(response.text, "html.parser")

            try:
                metalist = soup.find_all("meta")
                for metadata in metalist:
                    if "monthly listener" in str(metadata):
                        content = str(metadata).split()
                        if len(content) > 2:
                            for i in range(len(content)-2):
                                if content[i+1] == "monthly" and "listener" in content[i+2]:
                                    #print(content[i])
                                    monthly_listeners = content[i]
                                    break
                if monthly_listeners == "?":
                    ml_string = ""
                else:
                    ml_string = f"{monthly_listeners} monthly listeners\n"

            except Exception as e:
                print(f"Error while parsing html: {e}")
                return ""
        except Exception as e:
            print(f"Error while fetching from spotify web: {e}")
            return ""

        print("monthly listeners:", monthly_listeners)
        return ml_string



    async def fetch_lastfm_data_via_api(self, ctx, musicbrainz_id, artistname, songname, cooldown):
        """fetch lastfm genre tags and total scrobbles"""

        payload = {'method': 'artist.getInfo'}

        if musicbrainz_id is None or musicbrainz_id.strip() == "":
            print("try to get mbid...")
            payload_prefetch = {
                    'method': 'track.getInfo',
                    'track': songname,
                    'artist': artistname,
                }
            cooldown_prefetch = False
            try:
                response = await util.lastfm_get(ctx, payload_prefetch, cooldown_prefetch)
                if response == "rate limit":
                    print("rate limit")
                    return
                try:
                    rjson = response.json()
                    mbid = rjson['track']['artist']['mbid']
                    payload['mbid'] = mbid
                except Exception as e:
                    print(f"Could not find mbid: {e}\n{rjson}")
                    #payload['artist'] = artistname
                    mbid = None
            except Exception as e:
                print(f"Error while trying to fetch MBID from LastFM: {e}")
                payload['artist'] = artistname
                print("using plain artist name instead")
        else:
            payload['mbid'] = musicbrainz_id
            print("artist mbid:", musicbrainz_id)

        response = await util.lastfm_get(ctx, payload, cooldown)
        if response == "rate limit":
            return "", "", []
        rjson = response.json()

        try: # just a check, e.g. some artists return error message
            artist = rjson['artist']
        except:
            print(rjson)
            raise ValueError(f"Error: Response did not contain artist information. {rjson}")
            #return "", "", []

        try:
            stats = rjson['artist']['stats']
            LFM_listeners = stats['listeners']
            LFM_playcount = stats['playcount']
            #print("LFM listeners:", LFM_listeners)
            #print("LFM playcount:", LFM_playcount)
        except:
            # no stats
            pass

        genre_tags = []
        tag_json = rjson['artist']['tags']['tag']
        i = 0
        for tag in tag_json:
            try:
                if util.alphanum(tag['name'],"lower") == util.alphanum(artistname,"lower"):
                    pass
                else:
                    genre_tags.append(tag['name'].lower())
                    i += 1
                    if i > 10:
                        break
            except:
                pass

        genre_tags = util.filter_genretags(genre_tags)

        return LFM_listeners, LFM_playcount, genre_tags



    async def fetch_lastfm_data_via_web(self, ctx, artistname, cooldown):
        """fetch lastfm genre tags and total scrobbles"""

        if cooldown:
            try: 
                await util.cooldown(ctx, "lastfm")
            except Exception as e:
                await util.cooldown_exception(ctx, e, "LastFM")
                return "rate limit"

        listeners = ""
        total_scrobbles = ""
        genretags = []

        try:
            session = requests.session()
            artist = artistname.replace(" ","+")
            burp0_url = f"https://www.last.fm/music/{artist}"
            burp0_headers = {"Sec-Ch-Ua": "\"Chromium\";v=\"111\", \"Not(A:Brand\";v=\"8\"", "Sec-Ch-Ua-Mobile": "?0", "Sec-Ch-Ua-Platform": "\"Windows\"", "Upgrade-Insecure-Requests": "1", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.5563.111 Safari/537.36", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7", "Sec-Fetch-Site": "none", "Sec-Fetch-Mode": "navigate", "Sec-Fetch-User": "?1", "Sec-Fetch-Dest": "document", "Accept-Encoding": "gzip, deflate", "Accept-Language": "en-US;q=0.8,en;q=0.7", "Connection": "close"}
            response = session.get(burp0_url, headers=burp0_headers)

            soup = BeautifulSoup(response.text, "html.parser")

            i = 0
            for abbr in soup.find_all('abbr'):
                try:
                    if 'js-abbreviated-counter' in abbr['class'] or "counter" in ' '.join(abbr['class']):
                        i += 1

                        if i == 1:
                            listeners = abbr.get_text().strip() #+ " lfm listeners"
                        if i == 2:
                            total_scrobbles = abbr.get_text().strip() #+ " total scrobbles"
                            break
                except Exception as e:
                    print(e)

            try:
                for ul in soup.find_all('ul'):
                    try:
                        ul_class = str(ul.get("class")[0])
                        if ul_class.startswith("tags-list"):
                            for a in ul.find_all("a"):
                                tagname = a.getText().strip().lower()
                                genretags.append(tagname)
                            break
                    except:
                        pass
            except:
                pass

            genretags = util.filter_genretags(genretags)

            return listeners, total_scrobbles, genretags

        except:
            return "", "", []



    async def fetch_musicbrainz_tags(self, ctx, mbid, artist, album, song, checkyear, checkarea, checktags, cooldown):   
        if cooldown:
            try: # cooldown to not trigger actual rate limits or IP blocks
                await util.cooldown(ctx, "musicbrainz")
            except Exception as e:
                await util.cooldown_exception(ctx, e, "musicbrainz")
                return

        try:
            version = util.get_version().replace("version","v").replace(" ","").strip()
        except:
            version = "v_X"

        try:
            contact = os.getenv("contact_email")
        except:
            contact = ""

        USER_AGENT = f'MDM_Bot/{version}_({contact})'

        # define headers
        headers = {'user-agent': USER_AGENT}
        payload = {"fmt": "json"}

        tags = []
        year = ""
        area = ""
        mbid_mismatch = False

        song = util.urlfriendlytext(song)
        album = util.urlfriendlytext(album)
        artist = util.urlfriendlytext(artist)

        disambiguation = None

        # GET MBID
        if mbid is None or mbid == "":
            print("try to get mbid...")
            payload_lastfm = {
                    'method': 'track.getInfo',
                    'track': song,
                    'artist': artist,
                }
            cooldown = False
            try:
                response = await util.lastfm_get(ctx, payload_lastfm, cooldown)
                if response == "rate limit":
                    print("rate limit")
                    return
                try:
                    rjson = response.json()
                    mbid = rjson['track']['artist']['mbid']
                except:
                    mbid = None
            except Exception as e:
                print(f"Error while trying to fetch MBID from LastFM: {e}")

        # GET YEAR

        if checkyear or (mbid is None or mbid == ""):
            print("check year...")
            try:
                if artist == "":
                    return mbid, tags, year, area

                if album != "" and song != "":
                    url = f"http://musicbrainz.org/ws/2/recording"
                    if album != "":
                        payload['query'] = f"recording:{song}%20AND%20artist:{artist}%20AND%20releasegroup:{album}"
                    else:
                        payload['query'] = f"recording:{song}%20AND%20artist:{artist}"
                    response = requests.get(url, headers=headers, params=payload)
                    try:
                        rjson = response.json()
                        rjson = rjson['recordings'][0]
                        #print("Found recording:", rjson)
                    except:
                        raise ValueError("Could not find recording. Response:", response)
                elif album != "":
                    url = f"http://musicbrainz.org/ws/2/release-group"
                    payload['query'] = f"releasegroup:{album}%20AND%20artist:{artist}"
                    response = requests.get(url, headers=headers, params=payload)
                    try:
                        rjson = response.json()
                        rjson = rjson['release-groups'][0]
                        #print("Found release group:", rjson)
                    except:
                        raise ValueError("Could not find release group. Response:", response)
                elif song != "":
                    url = f"http://musicbrainz.org/ws/2/recording"
                    payload['query'] = f"recording:{song}%20AND%20artist:{artist}"
                    response = requests.get(url, headers=headers, params=payload)
                    try:
                        rjson = response.json()
                        rjson = rjson['recordings'][0]
                        #print("Found recording:", rjson)
                    except:
                        raise ValueError("Could not find recording. Response:", response)
                else:
                    return mbid, tags, year, area

                if mbid is None or mbid == "":
                    mbid = rjson['artist-credit'][0]['artist']['id']

                if mbid == rjson['artist-credit'][0]['artist']['id']:
                    try:
                        disambiguation = rjson['artist-credit'][0]['artist']['disambiguation']
                        print(f"Found description: {disambiguation}")
                    except:
                        pass
                    if checkyear:
                        year = rjson['first-release-date'].split("-")[0]
                        print(f"Found date: {year}")
                    #tags.append(disambiguation) # add disambiguation to tags?
                else:
                    mbid_mismatch = True
                    print("Error: the found artist on musicbrainz doesn't match the provided mbid")
            except Exception as e: 
                print("Error while checking year/mbid:", e)
                #print(traceback.format_exc())

        # GET AREA

        payload = {"fmt": "json"}

        if checkarea and (mbid != None and mbid != "") and not mbid_mismatch:
            print("check area...")
            try:
                url = f"https://musicbrainz.org/ws/2/artist/{mbid}"
                response = requests.get(url, headers=headers, params=payload)
                rjson = response.json()['area']
                area_name = rjson['name']

                area = util.areaicon(area_name)
            except Exception as e:
                print("Error while checking area:", e)

        # GET TAGS

        if checktags:
            print("check MB tags...")
            try:
                session = requests.session()
                burp0_url = f"https://musicbrainz.org:443/artist/{mbid}/tags"
                burp0_headers = {"Sec-Ch-Ua": "\"Chromium\";v=\"123\", \"Not:A-Brand\";v=\"8\"", "Sec-Ch-Ua-Mobile": "?0", "Sec-Ch-Ua-Platform": "\"Windows\"", "Upgrade-Insecure-Requests": "1", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.58 Safari/537.36", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7", "Sec-Fetch-Site": "none", "Sec-Fetch-Mode": "navigate", "Sec-Fetch-User": "?1", "Sec-Fetch-Dest": "document", "Accept-Encoding": "gzip, deflate, br", "Accept-Language": "en-US;q=0.8,en;q=0.7", "Priority": "u=0, i", "Connection": "close"}
                response = session.get(burp0_url, headers=burp0_headers)

                soup = BeautifulSoup(response.text, "html.parser")
                htmltags = soup.find('script', type="application/json")

                try:
                    rjson = json.loads(htmltags.text)
                except:
                    print("trying manual parse...")
                    manualparse = response.text.split('<script type="application/json">')[1].split('</script>')[0].strip()
                    rjson = json.loads(manualparse)

                #print(rjson['aggregatedTags'])
                tag_dict = {}
                maximal_count = 0
                for item in rjson['aggregatedTags']:
                    #print(item)
                    try:
                        tagname = item['tag']['name']
                        is_genre = item['tag']['genre']
                        votecount = int(item['count'])
                        print(f"found tag: {tagname} - {votecount}")
                        if tagname not in tag_dict:
                            tag_dict[tagname] = votecount
                        if votecount > maximal_count:
                            maximal_count = votecount
                    except:
                        pass

                #if type(disambiguation) == str and disambiguation.strip() != "":
                #    tags.append(disambiguation.lower().strip())

                i = 0
                for tag in tag_dict:
                    i += 1
                    if tag_dict[tag] > 0 and tag_dict[tag] >= maximal_count/2:
                        tags.append(tag)

                    if i > 9: # maximum of 10 tags
                        break
            except Exception as e:
                print("Error while checking tags:", e)

        tags = util.filter_genretags(tags)

        return mbid, tags, year, area



    async def find_applemusic_pictures(self, ctx, artist, album, song, cooldown):
        if cooldown:
            try: # cooldown to not trigger actual rate limits or IP blocks
                await util.cooldown(ctx, "applemusic")
            except Exception as e:
                await util.cooldown_exception(ctx, e, "applemusic")
                return []

        try:
            session = requests.session()
            artist2 = ''.join([x for x in artist if x.isalnum() or x == " "]).replace(" ", "%20")
            album2 = ''.join([x for x in album if x.isalnum() or x == " "]).replace(" ", "%20")
            song2 = ''.join([x for x in song if x.isalnum() or x == " "]).replace(" ", "%20")
            burp0_url = f"https://music.apple.com/us/search?term={artist2}%20{album2}%20{song2}"
            burp0_headers = {"Sec-Ch-Ua": "\"Chromium\";v=\"111\", \"Not(A:Brand\";v=\"8\"", "Sec-Ch-Ua-Mobile": "?0", "Sec-Ch-Ua-Platform": "\"Windows\"", "Upgrade-Insecure-Requests": "1", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.5563.111 Safari/537.36", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7", "Sec-Fetch-Site": "none", "Sec-Fetch-Mode": "navigate", "Sec-Fetch-User": "?1", "Sec-Fetch-Dest": "document", "Accept-Encoding": "gzip, deflate", "Accept-Language": "en-US;q=0.8,en;q=0.7", "Connection": "close"}
            response = session.get(burp0_url, headers=burp0_headers)

            soup = BeautifulSoup(response.text, "html.parser")

            found_albumname_in_html = False
            found_artistname_in_html = False
            picture_links = []

            for div in soup.find_all("div"):
                try:
                    div_class = div.get("class")
                    if str(div_class[0]).startswith("shelf-grid__body"):
                        for a in div.find_all("a"):
                            try:
                                a_text = util.alphanum(a.getText().strip().split("(")[0],"lower")
                                if a_text == util.alphanum(album,"lower"):
                                    found_albumname_in_html = True
                                if a_text == util.alphanum(artist,"lower"):
                                    found_artistname_in_html = True
                            except:
                                pass

                        for source in div.find_all("source"):
                            try:
                                source_srcset = str(source.get("srcset")).replace(","," ").split()

                                for pic in source_srcset:
                                    if pic.startswith("https://") and (pic.endswith(".jpg") or pic.endswith(".png") or pic.endswith(".webp")):
                                        picture_links.append(pic)
                            except: 
                                pass

                        if found_albumname_in_html and found_artistname_in_html:
                            return picture_links
                        else:
                            picture_links = []
                except Exception as e:
                    print("Error while trying to find album cover jpg/png/webp from AppleMusic:", e)
        except Exception as e:
            print("Error while trying to fetch album cover from AppleMusic:", e)

        return []


    #################################################################################################################################
    #################################################################################################################################
    #################################################################################################################################

    #### AUXILIARY FUNCTIONS



    async def add_np_reactions(self, ctx, message, the_member):
        """add self selected reaction emojis to now-playing-embed"""
        try:
            if ctx.message.author.id != the_member.id:
                return

            con = sqlite3.connect('databases/npsettings.db')
            cur = con.cursor()
            emoji_listlist = [[item[0],item[1],item[2],item[3],item[4]] for item in cur.execute("SELECT emoji1, emoji2, emoji3, emoji4, emoji5 FROM npreactions WHERE id = ?", (str(ctx.message.author.id),)).fetchall()]

            if len(emoji_listlist) == 0:
                return

            if len(emoji_listlist) > 1:
                print(f"Warning: user {util.cleantext2(str(ctx.message.author.name))} (ID: {str(ctx.message.author.id)}) has multiple NP-reaction entries in database")

            emoji_list = emoji_listlist[0]

            for emoji in emoji_list:
                if not emoji is None and emoji.strip() != "":
                    if emoji in util.convert_stringlist(self.bot.emojis) or emoji in UNICODE_EMOJI['en']:
                        try:
                            await message.add_reaction(emoji)
                            await asyncio.sleep(0.5)
                        except Exception as e:
                            print(f"Error while trying to add reaction: {e}")
                    else:
                        print(f"Could not find emoji: {emoji}")

        except Exception as e:
            print(f"Error during add_np_reactions: {e}")



    async def error_embed(self, ctx, text, footer):
        emoji = util.emoji("attention")
        text = emoji + " " + text
        embed = discord.Embed(description=text[:4096], color = 0xd30000)
        if footer.strip() != "":
            embed.set_footer(text=footer.strip())
        await ctx.send(embed=embed)


    #############################################################################################################################################
    #############################################################################################################################################
    #############################################################################################################################################
    #############################################################################################################################################
    #############################################################################################################################################
    #############################################################################################################################################
    #############################################################################################################################################
    #############################################################################################################################################
    #############################################################################################################################################
    #############################################################################################################################################
    #############################################################################################################################################
    #############################################################################################################################################
    #############################################################################################################################################
    #############################################################################################################################################
    #################################################### THIS HELPS ME FOR ORIENTATION IN THE CODE ##############################################
    #############################################################################################################################################
    #############################################################################################################################################
    #############################################################################################################################################
    #############################################################################################################################################
    #############################################################################################################################################
    #############################################################################################################################################
    #############################################################################################################################################
    #############################################################################################################################################
    #############################################################################################################################################
    #############################################################################################################################################
    #############################################################################################################################################
    #############################################################################################################################################
    #############################################################################################################################################
    #############################################################################################################################################
    #############################################################################################################################################

    ########################################################### pre command functions ###########################################################



    async def getmember(self, ctx, args):
        # FETCH MEMBER
        try:
            user_id, rest = await util.fetch_id_from_args("user", "first", args)
            for member in ctx.guild.members:
                if str(member.id) == user_id:
                    the_member = member
                    break
            else:
                the_member = ctx.message.author
        except:
            the_member = ctx.message.author

        return the_member



    async def spotify(self, ctx, args, tags, custom):
        the_member = await self.getmember(ctx, args)
        called_services = await self.parse_called_services(args)
        try:
            message = await self.spotify_activity(ctx, the_member, tags, called_services, custom)
            await self.add_np_reactions(ctx, message, the_member)
        except Exception as e:
            print(e)
            text = "No Spoofy status found 🔇"
            if the_member.id == ctx.message.author.id:
                footer = "Make sure to check that your Spotify is properly connected to Discord, and that your status is not set to 'invisible'."
            else:
                footer = f"{the_member.name} is either not using Spotify at the moment, it's not properly connected to discord or their status is set to 'invisible'."
            await self.error_embed(ctx, text, footer)



    async def musicbee(self, ctx, args, tags, custom):
        the_member = await self.getmember(ctx, args)
        called_services = await self.parse_called_services(args)
        try:
            message = await self.musicbee_activity(ctx, the_member, tags, called_services, custom)
            await self.add_np_reactions(ctx, message, the_member)
        except:
            text = "No MusicBee status found 🐝"
            if the_member.id == ctx.message.author.id:
                footer = "Make sure to check that your MusicBee is properly connected to Discord, and that your status is not set to 'invisible'."
            else:
                footer = f"{the_member.name} is either not using MusicBee at the moment, it's not properly connected to discord or their status is set to 'invisible'."
            await self.error_embed(ctx, text, footer)



    async def applemusic(self, ctx, args, tags, custom):
        the_member = await self.getmember(ctx, args)
        called_services = await self.parse_called_services(args)
        try:
            message = await self.applemusic_activity(ctx, the_member, tags, called_services, custom)
            await self.add_np_reactions(ctx, message, the_member)
        except:
            text = "No Apple Music status found 🍏"
            if the_member.id == ctx.message.author.id:
                footer = "Make sure to check that your Apple Music is properly connected to Discord, and that your status is not set to 'invisible'."
            else:
                footer = f"{the_member.name} is either not using Apple Music at the moment, it's not properly connected to discord or their status is set to 'invisible'."
            await self.error_embed(ctx, text, footer)



    async def lastfm(self, ctx, args, api_or_web, tags, custom):
        the_member = await self.getmember(ctx, args)
        called_services = await self.parse_called_services(args)
        try:
            cooldown = True
            if api_or_web.lower() == "api":
                message = await self.lastfm_apifetch(ctx, the_member, tags, called_services, cooldown, custom)
            else:
                message = await self.lastfm_webscrape(ctx, the_member, tags, called_services, cooldown, custom) # last argument for whether a cooldown is needed
            await self.add_np_reactions(ctx, message, the_member)
        except Exception as e:
            if str(e) == "user has not set lastfm":
                text = f"no lastfm name set for {the_member.mention}"
                footer = f"use '{self.prefix}fmset <username>' to set your lastfm username"
            else:
                text = str(e)
                print(traceback.format_exc())
                footer = ""
            await self.error_embed(ctx, text, footer)



    async def nowplaying(self, ctx, args, tags, custom):
        the_member = await self.getmember(ctx, args)
        called_services = await self.parse_called_services(args)
        try:
            message = await self.spotify_activity(ctx, the_member, tags, called_services, custom)
        except:
            try:
                message = await self.musicbee_activity(ctx, the_member, tags, called_services, custom)
            except:
                try:
                    message = await self.applemusic_activity(ctx, the_member, tags, called_services, custom)
                except:
                    try:
                        cooldown = True
                        message = await self.lastfm_apifetch(ctx, the_member, tags, called_services, cooldown, custom)
                    except:
                        emoji = util.emoji("disappointed")
                        text = f"No played music found {emoji}"
                        #if the_member.id == ctx.message.author.id:
                        #    footer = "Make sure to check that your music streaming service (Spotify/MusicBee/AppleMusic) is properly connected to Discord, and that your status is not set to 'invisible'."
                        #else:
                        #    footer = f"{the_member.name} is either not using any music streaming service at the moment, it's not properly connected to discord or their status is set to 'invisible'."
                        footer += f"\nUse '{self.prefix}fmset <username>' to set your lastfm username to display your current/last track on LFM."
                        await self.error_embed(ctx, text, footer)
                        return

        await self.add_np_reactions(ctx, message, the_member)
            


    ########################################################### COMMANDS ###########################################################



    @commands.command(name='spotify', aliases = ['spoofy', 'sp'])
    @commands.check(util.is_active)
    async def _spotify_plain(self, ctx: commands.Context, *args):
        """NowPlaying for Spotify

        Use spx to also get (customisable) tags and info to the track you're playing.
        """
        tags = True
        custom = False
        await self.spotify(ctx, args, tags, custom)
    @_spotify_plain.error
    async def spotify_plain_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='spx', aliases = ['spoofyx', 'spotifyx'])
    @commands.check(util.is_active)
    async def _spotify_extra(self, ctx: commands.Context, *args):
        """㊙️ NowPlaying for Spotify with customisable tags
        """
        tags = True
        custom = True
        await self.spotify(ctx, args, tags, custom)
    @_spotify_extra.error
    async def spotify_extra_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='musicbee', aliases = ['bee', 'mb'])
    @commands.check(util.is_active)
    async def _musicbee(self, ctx: commands.Context, *args):
        """NowPlaying for MusicBee

        Use mbx to also get (customisable) tags and info to the track you're playing."""
        tags = True
        custom = False
        await self.musicbee(ctx, args, tags, custom)
    @_musicbee.error
    async def musicbee_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='mx', aliases = ['musicbeex','beex', 'mbx', 'bx'])
    @commands.check(util.is_active)
    async def _musicbee_extra(self, ctx: commands.Context, *args):
        """㊙️ NowPlaying for MusicBee with customisable tags"""
        tags = True
        custom = True
        await self.musicbee(ctx, args, tags, custom)
    @_musicbee_extra.error
    async def musicbee_extra_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='applemusic', aliases = ['apple', 'am', 'itunes'])
    @commands.check(util.is_active)
    async def _applemusic(self, ctx: commands.Context, *args):
        """NowPlaying for Apple Music

        Use apx to also get (customisable) tags and info to the track you're playing."""
        tags = True
        custom = False
        await self.applemusic(ctx, args, tags, custom)
    @_applemusic.error
    async def applemusic_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='apx', aliases = ['applemusicx', 'applex', 'amx', 'itunesx'])
    @commands.check(util.is_active)
    async def _applemusic_extra(self, ctx: commands.Context, *args):
        """㊙️ NowPlaying for Apple Music with customisable tags"""
        tags = True
        custom = True
        await self.applemusic(ctx, args, tags, custom)
    @_applemusic_extra.error
    async def applemusic_extra_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='fm', aliases = ['lastfm', 'lfm'])
    @commands.check(util.is_active)
    async def _lastfm(self, ctx: commands.Context, *args):
        """NowPlaying for LastFM

        Use fmx to also get (customisable) tags and info to the track you're playing."""
        tags = True
        custom = False
        await self.lastfm(ctx, args, "api", tags, custom)
    @_lastfm.error
    async def lastfm_error(self, ctx, error):
        await util.error_handling(ctx, error) 



    @commands.command(name='fmx', aliases = ['lfmx', 'lastfmx'])
    @commands.check(util.is_active)
    async def _lastfm_extra(self, ctx: commands.Context, *args):
        """㊙️ NowPlaying for LastFM with customisable tags"""
        tags = True
        custom = True
        await self.lastfm(ctx, args, "api", tags, custom)
    @_lastfm_extra.error
    async def lastfm_extra_error(self, ctx, error):
        await util.error_handling(ctx, error) 



    #@commands.command(name='lastfmw', aliases = ['fmw', 'lfmw'])
    #@commands.check(util.is_active)
    #async def _lastfm_web(self, ctx: commands.Context, *args):
    #    """NowPlaying for LastFM, force webscraping"""
    #    await self.lastfm(ctx, args, "web", False)
    #@_lastfm_web.error
    #async def lastfm_web_error(self, ctx, error):
    #    await util.error_handling(ctx, error) 



    #@commands.command(name='lastfmwx', aliases = ['fmwx', 'lfmwx'])
    #@commands.check(util.is_active)
    #async def _lastfm_web_extra(self, ctx: commands.Context, *args):
    #    """NowPlaying for LastFM with tags, force webscraping"""
    #    await self.lastfm(ctx, args, "web", True)
    #@_lastfm_web_extra.error
    #async def lastfm_web_extra_error(self, ctx, error):
    #    await util.error_handling(ctx, error)



    @commands.command(name='nowplaying', aliases = ['np'])
    @commands.check(util.is_active)
    async def _nowplaying(self, ctx: commands.Context, *args):
        """NowPlaying

        Going through all integrated music sreaming services (Spotify, MusicBee, AppleMusic, LastFM) until it finds a track you are listening to and displays it.
        Use `<prefix>npx` to also display customisable tags (beyond the standard info), or use `<prefix>n` to display without *any* tags.
        """
        tags = True
        custom = False
        await self.nowplaying(ctx, args, tags, custom)
    @_nowplaying.error
    async def nowplaying_error(self, ctx, error):
        await util.error_handling(ctx, error) 



    @commands.command(name='npx', aliases = ['nowplayingx'])
    @commands.check(util.is_active)
    async def _nowplaying_extra(self, ctx: commands.Context, *args):
        """㊙️ NowPlaying with customisable tags

        Going through all integrated music sreaming services (Spotify, MusicBee, AppleMusic, LastFM) until it finds a track you are listening to and displays it.
        Use `<prefix>np` to only display standard tags, or use `<prefix>n` to display without *any* tags."""
        tags = True
        custom = True
        await self.nowplaying(ctx, args, tags, custom)
    @_nowplaying_extra.error
    async def nowplaying_extra_error(self, ctx, error):
        await util.error_handling(ctx, error) 



    @commands.command(name='n', aliases = ['np0', 'nowplaying0'])
    @commands.check(util.is_active)
    async def _nowplayingzero(self, ctx: commands.Context, *args):
        """㊙️ NowPlaying without any tags

        Going through all integrated music sreaming services (Spotify, MusicBee, AppleMusic, LastFM) until it finds a track you are listening to and displays it.
        Use `<prefix>npx` to also display customisable tags, or use `<prefix>np` to only display standard tags."""
        tags = False
        custom = False
        await self.nowplaying(ctx, args, tags, custom)
    @_nowplayingzero.error
    async def nowplayingzero_error(self, ctx, error):
        await util.error_handling(ctx, error) 



    ##################################################################################################################################



    async def fakenowplaying(self, ctx, args, tags):
        async with ctx.typing():
            argument = ' '.join(args)
            number_hyphens = argument.count("-")

            if number_hyphens == 0:
                await ctx.send(f"Error: Could not parse artist and track. Please use a hyphen as separator.")
                return
            else:
                if number_hyphens == 1:
                    artist = argument.split("-")[0].strip()
                    track = argument.split("-")[1].strip()
                else:
                    number_spacehyphens = argument.count(" - ")
                    if number_spacehyphens == 1:
                        artist = argument.split(" - ")[0].strip()
                        track = argument.split(" - ")[1].strip()
                    else:
                        # unsure about parsing
                        artist = argument.split("-")[0].strip()
                        track = "-".join(argument.split("-")[1:]).strip()
                        print(f"Warning: uncertain parsing")

            try:
                # FETCH TRACK FROM LASTFM API

                payload = {
                    'method': 'track.getInfo',
                    'track': track,
                    'artist': artist,
                }
                cooldown = True
                try:
                    response = await util.lastfm_get(ctx, payload, cooldown)
                    if response == "rate limit":
                        print("rate limit")
                        return
                except Exception as e:
                    print("Error:", e)
                    if str(e) == "No LastFM keys provided":
                        await ctx.send("Error: No LastFM API key provided to search for artist and track. Ask mods to add one to the bot's environment file.")
                    return

                # PARSE JSON

                try:
                    rjson = response.json()['track']
                    track = rjson['name']
                    song_link = rjson['url']
                    artist = rjson['artist']['name']
                    try:
                        mbid = rjson['artist']['mbid']
                    except:
                        mbid = None
                    try:
                        album = rjson['album']['title']
                    except:
                        album = ""
                    try:
                        albumart = rjson['album']['image'][-1]['#text']
                    except:
                        albumart = "https://i.imgur.com/0Djj7I6.jpeg"
                    try:
                        artisturl = "https://www.last.fm/music/" + song_link.split("https://www.last.fm/music/")[1].split("/")[0]
                    except:
                        artisturl = ""
                except:
                    await ctx.send(f"Error: Could not find track via LastFM.")
                    return

                tag_string = ""
                if tags == True:
                    try:
                        # FETCH TRACK TAGS

                        track_genre_tags = []
                        tag_json = rjson['toptags']['tag'] 
                        i = 0
                        for tag in tag_json:
                            try:
                                if util.alphanum(tag['name'],"lower") == util.alphanum(artist,"lower"):
                                    pass
                                else:
                                    track_genre_tags.append(tag['name'].lower())
                                    i += 1
                                    if i > 9:
                                        break
                            except:
                                pass

                        # FETCH ARTIST TAGS

                        cooldown = False
                        try:
                            listeners, total_scrobbles, artist_genre_tag_list = await self.fetch_lastfm_data_via_api(ctx, mbid, artist, track, cooldown)
                        except Exception as e:
                            print("Error, while trying to fetch artist data from lastfm API:", e)
                            listeners = ""
                            total_scrobbles = ""
                            artist_genre_tag_list = []

                        genre_tag_list = util.filter_genretags(artist_genre_tag_list + track_genre_tags)

                        if len(genre_tag_list) > 0:
                            genre_tag_string = "LFM: " + f"{self.tagseparator}".join(genre_tag_list)
                        else:
                            genre_tag_string = "no genre tags found"

                        listener_tags = []
                        if str(listeners).strip() != "":
                            listener_tags.append(f"{util.shortnum(listeners)} lfm listeners")
                        if str(total_scrobbles).strip() != "":
                            listener_tags.append(f"{util.shortnum(total_scrobbles)} total scrobbles")

                        # FETCH ALTERNATIVELY WEB TAGS

                        try:
                            if genre_tag_string == "no genre tags found":
                                listeners2, total_scrobbles2, artist_genre_tag_list = await self.fetch_lastfm_data_via_web(ctx, artist, cooldown)
                                artist_genre_tag_list = util.filter_genretags(artist_genre_tag_list)
                                if len(artist_genre_tag_list) > 0:
                                    genre_tag_string = "LFM*: " + f"{self.tagseparator}".join(artist_genre_tag_list).strip()
                                else:
                                    genre_tag_string = "no genre tags found"
                        except Exception as e:
                            print("Error:", e)

                        # COMPOSE TAG STRING

                        tag_string += f"{self.tagseparator}".join(listener_tags).strip()
                        tag_string += f"\n{genre_tag_string}"
                    except Exception as e:
                        print("Error while trying to fetch tags:", e)

                elif tags == "custom":
                    try:
                        custom = True
                        tag_string = await self.fetch_tags(ctx, "unspecified", artist, album, track, None, [mbid,None,None], [], custom, str(ctx.author.id))
                    except Exception as e:
                        print("Unable to fetch tags:", e)
                        print(traceback.format_exc())

            except Exception as e:
                print("Error:", e)
                await ctx.send(f"Error while trying to retrieve data from LastFM.")
                return

            try:
                # MAKE EMBED

                member = ctx.message.author
                if album == "":
                    description = f"[{track}]({song_link})\nby **{util.cleantext2(artist)}**"
                else:
                    description = f"[{track}]({song_link})\nby **{util.cleantext2(artist)}** | {album}"
                embed = discord.Embed(description=description, color = member.color)
                embed.set_author(name=f"{member.display_name}'s fakenowplaying" , icon_url=member.avatar)
                try:
                    default_whitestar_image = "https://lastfm.freetls.fastly.net/i/u/68s/2a96cbd8b46e442fc41c2b86b821562f.png"
                    if albumart != "" and not albumart.endswith("2a96cbd8b46e442fc41c2b86b821562f.png"):
                        embed.set_thumbnail(url=albumart)
                    else:
                        # try to fetch from database
                        artist_compact = util.compactnamefilter(artist, "artist", "alias")
                        album_compact = util.compactnamefilter(album, "album")
                        _, _, cover_url, details, _, last_updated = await util.get_album_details_from_compact(artist_compact, album_compact)
                        try:
                            now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())
                            if last_updated > now - 180*24*60*60:
                                embed.set_thumbnail(url=cover_url)
                            else:
                                raise ValueError("image too old")
                        except Exception as e:
                            embed.set_thumbnail(url=default_whitestar_image)
                except Exception as e:
                    print(e)
                if tags == True or tags == "custom":
                    embed.set_footer(text=tag_string[:2048].strip())

                message = await ctx.send(embed=embed)
            except Exception as e:
                print("Error:", e)
                await ctx.send(f"Error while trying to make embed.")

        try:
            await self.add_np_reactions(ctx, message, member)
        except Exception as e:
            print("Error while trying to add NP reactions:", e)



    @commands.command(name='fakenowplaying', aliases = ['fnp', 'fakenp', 'fakeplaying', 'fake', 'fp'])
    @commands.check(util.is_active)
    async def _fakenowplaying(self, ctx: commands.Context, *args):
        """now playing by giving artist and song, gives out embed with tags
        """
        tags = True
        await self.fakenowplaying(ctx, args, tags)
    @_fakenowplaying.error
    async def fakenowplaying_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='fnp0', aliases = ['fakenowplaying0', 'fakenp0', 'fakeplaying0', 'fake0', 'fp0'])
    @commands.check(util.is_active)
    async def _fakenowplaying_zero(self, ctx: commands.Context, *args):
        """now playing by giving artist and song, gives out embed without tags
        """
        tags = False
        await self.fakenowplaying(ctx, args, tags)
    @_fakenowplaying_zero.error
    async def fakenowplaying_zero_error(self, ctx, error):
        await util.error_handling(ctx, error)
        



    @commands.command(name='fnpx', aliases = ['fakenowplayingx', 'fakenpx', 'fakeplayingx', 'fakex', 'fpx'])
    @commands.check(util.is_active)
    async def _fakenowplaying_zero(self, ctx: commands.Context, *args):
        """now playing by giving artist and song, gives out embed without tags
        """
        tags = "custom"
        await self.fakenowplaying(ctx, args, tags)
    @_fakenowplaying_zero.error
    async def fakenowplaying_zero_error(self, ctx, error):
        await util.error_handling(ctx, error)




    @commands.command(name='serverplaying', aliases = ['playing'])
    @commands.check(util.is_active)
    async def _serverplaying(self, ctx: commands.Context, *args):
        """Show what ppl on this server are listening to in their status

        Command goes through music sreaming services: Spotify, MusicBee, AppleMusic. In case these features are enabled users with the inactivity role, access wall role or timeout role will be excluded.
        
        Optional arg: spotify, musicbee, applemusic to only filter for people using these services.
        """

        # PARSE ARGS

        show_spotify = True
        show_musicbee = True
        show_applemusic = True
        args_given = False
        if len(args) > 0:
            arguments = []
            for arg in args:
                arguments.append(util.alphanum(arg,"lower"))

            args_given = True

            spotify_alias = ["spotify", "spoofy", "sp"]
            musicbee_alias = ["musicbee", "mb"]
            applemusic_alias = ["applemusic", "apple", "itunes", "am"]

            for arg in arguments:
                if arg not in spotify_alias:
                    show_spotify = False
                if arg not in musicbee_alias:
                    show_musicbee = False
                if arg not in applemusic_alias:
                    show_applemusic = False

        if not show_spotify and not show_musicbee and not show_applemusic:
            # pretend there were no arguments given
            show_spotify = True
            show_musicbee = True
            show_applemusic = True

        # CHECK INACTIVITY ROLE

        conB = sqlite3.connect('databases/botsettings.db')
        curB = conB.cursor()
        inactivityfilter_setting = [[item[0], item[1], item[2]] for item in curB.execute("SELECT value, details, etc FROM serversettings WHERE name = ?", ("inactivity filter", )).fetchall()]

        if len(inactivityfilter_setting) == 0 or inactivityfilter_setting[0][0].lower() != "on":
            inactivityfilter = "off"
        else:
            inactivityfilter = "on"

            try:# FETCH ROLE
                inactivityrole_list = [item[0] for item in curB.execute("SELECT role_id FROM specialroles WHERE name = ?", ("inactivity role",)).fetchall()]        
                if len(inactivityrole_list) == 0 or not util.represents_integer(inactivityrole_list[0]):
                    inactivity_role = None
                else:
                    inactivity_role_id = int(inactivityrole_list[0])
                    inactivity_role = ctx.guild.get_role(inactivity_role_id)
            except Exception as e:
                print("Error:", e)
                inactivity_role = None

        # CHECK TIMEOUT ROLE

        timeout_setting = [[item[0], item[1], item[2]] for item in curB.execute("SELECT value, details, etc FROM serversettings WHERE name = ?", ("timeout system", )).fetchall()]

        if len(timeout_setting) == 0 or timeout_setting[0][0].lower() != "on":
            timeout = "off"
        else:
            timeout = "on"

            try:# FETCH ROLE
                timeoutrole_list = [item[0] for item in curB.execute("SELECT role_id FROM specialroles WHERE name = ?", ("timeout role",)).fetchall()]        
                if len(timeoutrole_list) == 0 or not util.represents_integer(timeoutrole_list[0]):
                    timeout_role = None
                else:
                    timeout_role_id = int(timeoutrole_list[0])
                    timeout_role = ctx.guild.get_role(timeout_role_id)
            except Exception as e:
                print("Error:", e)
                timeout_role = None

        # CHECK ACCESSWALL ROLE

        accesswall_setting = [[item[0], item[1], item[2]] for item in curB.execute("SELECT value, details, etc FROM serversettings WHERE name = ?", ("access wall", )).fetchall()]

        if len(accesswall_setting) == 0 or accesswall_setting[0][0].lower() != "on":
            accesswall = "off"
        else:
            accesswall = "on"

            try:# FETCH ROLE
                accesswallrole_list = [item[0] for item in curB.execute("SELECT role_id FROM specialroles WHERE name = ?", ("access wall role",)).fetchall()]        
                if len(accesswallrole_list) == 0 or not util.represents_integer(accesswallrole_list[0]):
                    accesswallrole = None
                else:
                    accesswallrole_id = int(accesswallrole_list[0])
                    accesswall_role = ctx.guild.get_role(accesswallrole_id)
            except Exception as e:
                print("Error:", e)
                accesswall_role = None

        # AGGREGATE ACTIVITIES

        guild = ctx.message.guild
        spotify_list = []
        musicbee_list = []
        applemusic_list = []

        for member in guild.members:
            if len(member.roles) < 3:
                if inactivityfilter == "on":
                    if inactivity_role in member.roles: # only inactivity and everyone role
                        #print(f"skip {member.name}")
                        continue

                if timeout == "on":
                    if timeout_role in member.roles: # only timeout and everyone role
                        #print(f"skip {member.name}")
                        continue

                if accesswall == "on":
                    if accesswall_role in member.roles: # only accesswall and everyone role
                        #print(f"skip {member.name}")
                        continue

            activity_list = []
            for activity in member.activities:
                try:
                    activity_list.append(str(activity.name))
                except:
                    pass 

            for activity in member.activities:
                if isinstance(activity, Spotify):
                    spotify_list.append([member.display_name, member.id, util.cleantext2(activity.title), util.cleantext2(activity.artist), util.cleantext2(activity.album), activity.track_url])

                if str(activity.type) == "ActivityType.playing" and activity.name == "MusicBee":
                    try:
                        if "ꜰʀᴏᴍ " in util.cleantext2(activity.state):
                            if " - " in str(activity.details):
                                details = activity.details.split(" - ", 1)
                            else:
                                details = activity.details.split("-", 1)
                            artist = util.cleantext2(details[0].strip())
                            title = util.cleantext2(details[1].strip())
                            try:
                                album = util.cleantext2(activity.state).split("ꜰʀᴏᴍ ")[1]
                            except:
                                album = ""
                            artist_rep = artist.replace(" ","+")
                            song_rep = title.replace(" ","+")
                            url = f"https://www.last.fm/music/{artist_rep}/_/{song_rep}".replace("\\", "")

                        else:
                            if " - " in str(activity.details):
                                details = activity.details.split(" - ", 1)
                            else:
                                details = activity.details.split("-", 1)
                            artist = util.cleantext2(details[0].strip())
                            album = util.cleantext2(details[1].strip())
                            try:
                                title = util.cleantext2(activity.state.strip())
                                artist_rep = artist.replace(" ","+")
                                song_rep = title.replace(" ","+")
                                url = f"https://www.last.fm/music/{artist_rep}/_/{song_rep}".replace("\\", "")
                            except:
                                title = ""
                                artist_rep = artist.replace(" ","+")
                                album_re = album.replace(" ","+")
                                url = f"https://www.last.fm/music/{artist_rep}/{album_rep}".replace("\\", "")
                        musicbee_list.append([member.display_name, member.id, title, artist, album, url])
                    except:
                        musicbee_list.append([member.display_name, member.id, "", "", "", ""])

                if str(activity.type) == "ActivityType.playing" and (activity.name == "Apple Music" or (activity.name == "Music" and "iTunes Rich Presence for Discord" in activity_list)):
                    try:
                        try:
                            title = util.cleantext2(activity.details.replace("🎶", "").strip())
                            artist = util.cleantext2(activity.state.split("💿")[0].replace("👤","").strip())
                            album = util.cleantext2(activity.state.split("💿")[1].strip())
                        except:
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
                                    artist = util.cleantext2(activity.state.strip())
                                    song = util.cleantext2(activity.details.strip())
                                    album = ""

                        url = f"https://music.apple.com/us/search?term={artist}_{album}_{title}".replace(" ","_").replace("\\", "")
                        applemusic_list.append([member.display_name, member.id, title, artist, album, url])
                    except:
                        applemusic_list.append([member.display_name, member.id, "", "", "", ""])

        if len(spotify_list + musicbee_list + applemusic_list) == 0:
            emoji = util.emoji("pensive2")
            await ctx.send(f"No one is listening to music right now.. {emoji}\n(or they just too shy to show this on discord)")
            return

        spotify_list.sort(key=lambda x: x[0])
        musicbee_list.sort(key=lambda x: x[0])
        applemusic_list.sort(key=lambda x: x[0])

        # SPOTIFY

        if show_spotify:

            if len(spotify_list) == 0:
                if args_given:
                    await ctx.send("No Spotify listeners.")

            elif len(spotify_list) == 1:
                Ldescription = f"<@{spotify_list[0][1]}>: [{spotify_list[0][2]}]({spotify_list[0][5]}) by **{spotify_list[0][3]}**"
                embed = discord.Embed(
                                description=Ldescription,
                                color = 0x1F8B4C)
                embed.set_author(name=f"Lonesome Spoofy listener.." , icon_url="https://i.imgur.com/NHQO2SW.png")
                await ctx.send(embed=embed)
            else:
                complete_description = ""
                unmentioned_listeners = 0
                for item in spotify_list:
                    Ldescription = f"<@{item[1]}>: [{item[2]}]({item[5]}) by **{item[3]}**\n"

                    if len(complete_description) + len(Ldescription) < 4000:
                        complete_description += Ldescription
                    else:
                        unmentioned_listeners += 1

                embed = discord.Embed(
                                description=complete_description.strip(),
                                color = 0x1F8B4C)
                embed.set_author(name=f"Server Spoofy listeners" , icon_url="https://i.imgur.com/NHQO2SW.png")
                if unmentioned_listeners == 0:
                    embed.set_footer(text=f"{len(spotify_list)} listeners")
                else:
                    embed.set_footer(text=f"{len(spotify_list)} listeners, {unmentioned_listeners} unmentioned ones")
                await ctx.send(embed=embed)

        # MUSICBEE

        if show_musicbee:

            if len(musicbee_list) == 0:
                if args_given:
                    await ctx.send("No MusicBee listeners.")

            elif len(musicbee_list) == 1:
                Ldescription = f"<@{musicbee_list[0][1]}>: [{musicbee_list[0][2]}]({musicbee_list[0][5]}) by **{musicbee_list[0][3]}**"
                embed = discord.Embed(
                                description=Ldescription,
                                color = 0x000000)
                embed.set_author(name=f"Lonesome Music Bee.." , icon_url="https://i.imgur.com/7YXIimO.png")
                await ctx.send(embed=embed)
            else:
                complete_description = ""
                unmentioned_listeners = 0
                for item in musicbee_list:
                    Ldescription = f"<@{item[1]}>: [{item[2]}]({item[5]}) by **{item[3]}**\n"

                    if item[2] == "" and item[3] == "" and item[3] == "" and item[4] == "":
                        Ldescription = f"<@{item[1]}>: _error_\n"

                    if len(complete_description) + len(Ldescription) < 4000:
                        complete_description += Ldescription
                    else:
                        unmentioned_listeners += 1

                embed = discord.Embed(
                                description=complete_description.strip(),
                                color = 0x000000)
                embed.set_author(name=f"Server Music Bee listeners" , icon_url="https://i.imgur.com/7YXIimO.png")
                if unmentioned_listeners == 0:
                    embed.set_footer(text=f"{len(musicbee_list)} listeners")
                else:
                    embed.set_footer(text=f"{len(musicbee_list)} listeners, {unmentioned_listeners} unmentioned ones")
                await ctx.send(embed=embed)

        # APPLE MUSIC

        if show_applemusic:

            if len(applemusic_list) == 0:
                if args_given:
                    await ctx.send("No AppleMusic listeners.")

            elif len(applemusic_list) == 1:
                Ldescription = f"<@{applemusic_list[0][1]}>: [{applemusic_list[0][2]}]({applemusic_list[0][5]}) by **{applemusic_list[0][3]}**"
                embed = discord.Embed(
                                description=Ldescription,
                                color = 0xFE647B)
                embed.set_author(name=f"Lonesome Apple Music listener.." , icon_url="https://i.imgur.com/4Ims0Ed.png")
                await ctx.send(embed=embed)
            else:
                complete_description = ""
                unmentioned_listeners = 0
                for item in applemusic_list:
                    Ldescription = f"<@{item[1]}>: [{item[2]}]({item[5]}) by **{item[3]}**\n"

                    if item[2] == "" and item[3] == "" and item[3] == "" and item[4] == "":
                        Ldescription = f"<@{item[1]}>: _error_\n"

                    if len(complete_description) + len(Ldescription) < 4000:
                        complete_description += Ldescription
                    else:
                        unmentioned_listeners += 1

                embed = discord.Embed(
                                description=complete_description.strip(),
                                color = 0xFE647B)
                embed.set_author(name=f"Server AppleMusic listeners" , icon_url="https://i.imgur.com/4Ims0Ed.png")
                if unmentioned_listeners == 0:
                    embed.set_footer(text=f"{len(applemusic_list)} listeners")
                else:
                    embed.set_footer(text=f"{len(applemusic_list)} listeners, {unmentioned_listeners} unmentioned ones")
                await ctx.send(embed=embed)
    @_serverplaying.error
    async def serverplaying_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='activities', aliases = ['activity'])
    #@commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _useractivities(self, ctx: commands.Context, *args):
        """Show activities

        This is a bot testing command. Don't bother.
        """
        member = await self.getmember(ctx, args)

        activity_list = []
        i = 0
        for activity in member.activities:
            i += 1
            string = f"`{i}.` **" + util.cleantext2(activity.name) + "**"
            try:
                string += "\n[type: " + util.cleantext2(str(activity.type)) + "]"
            except:
                pass
            try:
                string += "\n[details: " + util.cleantext2(str(activity.details)) + "]"
            except:
                pass
            try:
                string += "\n[state: " + util.cleantext2(str(activity.state)) + "]"
            except:
                pass
            string += "\n"
            activity_list.append(string)

        text = '\n'.join(activity_list)

        if text.strip() == "":
            text = "None"

        embed = discord.Embed(description=text, color = member.color)
        embed.set_author(name=f"{member.display_name}'s activities" , icon_url=member.avatar)
        await ctx.send(embed=embed)
    @_useractivities.error
    async def useractivities_error(self, ctx, error):
        await util.error_handling(ctx, error) 



    ######################################################## SETTING COMMANDS ########################################################





    @commands.command(name='setfm', aliases = ['fmset', 'setlfm', "setlastfm", "lfmset", "lastfmset", "fmname", "lfmname", "lastfmname", "fmacc", "lfmacc"])
    @commands.check(util.is_active)
    async def _setfm(self, ctx: commands.Context, *args):
        """Set your last.fm account name
        """

        if len(args) == 0:
            await ctx.send("Command needs an argument!")
            return 

        user_id = str(ctx.message.author.id)
        user_name = util.cleantext2(str(ctx.message.author.name))
        new_lfm_name = util.cleantext2('_'.join(args)).replace("\\", "")
        new_lfm_link = "https://www.last.fm/user/" + new_lfm_name
        details = ""

        letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
        digits = ['0','1','2','3','4','5','6','7','8','9']
        extra = ['_','-']

        if new_lfm_name[0].lower() not in letters:
            await ctx.send("Error: Invalid name. Needs to start with a letter.")
            return 

        for char in new_lfm_name:
            if char.lower() not in letters+digits+extra:
                await ctx.send("Error: Invalid characters. Name can only contain letters, numbers, a `-` or a `_`.")
                return 

        if len(new_lfm_name) < 2 or len(new_lfm_name) > 15:
            await ctx.send("Error: Invalid name-length. Needs to be between 2 and 15 chars.")
            return 

        con = sqlite3.connect('databases/npsettings.db')
        cur = con.cursor()
        lfm_list = [[item[0],item[1]] for item in cur.execute("SELECT lfm_name, lfm_link FROM lastfm WHERE id = ?", (user_id,)).fetchall()]

        if len(lfm_list) == 0:
            cur.execute("INSERT INTO lastfm VALUES (?, ?, ?, ?, ?)", (user_id, user_name, new_lfm_name, new_lfm_link, details))
            textmessage = f"Added your LastFM account: `{new_lfm_name}`!\n\nIf you want your scrobbles to be imported into the bot use `{self.prefix}u`. This is a one-time thing and the bot will automatically update your scrobbles after that."
        else:
            if new_lfm_name.lower() == lfm_list[0][0].lower().strip():
                textmessage = f"That's already your lastfm account."

            #else if new_lfm_name.lower() in [item[0] for item in cur.execute("SELECT lfm_name FROM lastfm").fetchall()]:
            #    textmessage = f"That's someone else's lastfm account... If this is not a mistake ask mods to make the changes." # deprecated for now to allow users to add the same lfm account to multiple discord accounts

            else:
                text = "You are about to change your lastfm account."
                response = await util.are_you_sure_msg(ctx, self.bot, text)
                if response == False:
                    return
                cur.execute("UPDATE lastfm SET lfm_name = ?, lfm_link = ? WHERE id = ?", (new_lfm_name, new_lfm_link, user_id))
                textmessage = f"Changed your LastFM account to `{new_lfm_name}`."

                # under construction: change also details (from inactive to active?)
        con.commit()
        await util.changetimeupdate()

        await ctx.send(textmessage)
    @_setfm.error
    async def setfm_error(self, ctx, error):
        await util.error_handling(ctx, error) 



    @commands.command(name='setreacts', aliases = ['setreact', 'reacts', 'npreact', 'npreacts', 'fmreact', 'fmreacts', 'npemoji', 'npemojis', 'fmemoji', 'fmemojis'])
    @commands.check(util.is_active)
    async def _npreactions(self, ctx: commands.Context, *args):
        """Set np reacts
        
        Sets up to 5 reaction emojis for -np/-npx command.
        However, only emojis of servers where this bot is in are valid.

        If you do not have nitro but want to add emojis from other servers you can use :name: or id as well. 
        Just keep in mind that :name: might not be unique and is therefore prone to errors.

        Use `-reacts clear` to remove np reacts.

        Warning: Locked emoji due to a boost loss will show as "successfully added", but cannot be used until the server level is restored.
        """
        if len(args) == 0:
            await ctx.send(f"With this command you can add up to 5 reaction emojis to your `{self.prefix}np`, `{self.prefix}npx`, `{self.prefix}fm`, `{self.prefix}spotify`, `{self.prefix}musicbee`, `{self.prefix}applemusic`. \nUse `{self.prefix}help reacts` for more info.")
            return 

        con = sqlite3.connect('databases/npsettings.db')
        cur = con.cursor()

        user = ctx.message.author
        user_id = str(user.id)
        user_name = str(user.name)

        # CHECK CLEAR ARG

        if args[0].lower() in ["clear", "remove", "delete"]:
            try:
                cur.execute("DELETE FROM npreactions WHERE id = ?", (user_id,))
                con.commit()
                await ctx.send("Cleared your np reacts!")
                await util.changetimeupdate()
            except Exception as e:
                print(e)
                await ctx.send(f"Error: {e}")
            return

        # MAIN PART

        async with ctx.typing():

            # CHECK EMOJI PRIORITY PER SERVER

            default_emojis_unicode = UNICODE_EMOJI['en']
            custom_other_emojis = []
            custom_mdm_emojis = []

            conB = sqlite3.connect(f'databases/botsettings.db')
            curB = conB.cursor()    
            main_server = [item[0] for item in curB.execute("SELECT value FROM botsettings WHERE name = ?", ("main server id", )).fetchall()]

            for guild in self.bot.guilds:
                if str(guild.id) in main_server:
                    for emoji in guild.emojis:
                        custom_mdm_emojis.append([str(emoji), emoji.name, str(emoji.id), guild.name])
                else:
                    for emoji in guild.emojis:
                        custom_other_emojis.append([str(emoji), emoji.name, str(emoji.id), guild.name])

            # CHECK PROVIDED REACTION EMOJIS

            counter = 0
            valid_emojis = []
            invalid_emojis = []

            new_args = (' '.join(args).replace("><", "> <").replace(":<", ": <").replace(">:", "> :")).split(" ")

            for arg in new_args:
                emoji_to_add = str(arg)

                # check mdm: full format and id only
                for db_emoji in custom_mdm_emojis:
                    if emoji_to_add in [db_emoji[0],db_emoji[2]]:
                        valid_emojis.append(db_emoji[0])
                        counter += 1
                        break
                else:
                    # check other custom: full format and id only
                    for db_emoji in custom_other_emojis:
                        if emoji_to_add in [db_emoji[0],db_emoji[2]]:
                            valid_emojis.append(db_emoji[0])
                            counter += 1
                            break
                    else:
                        # check default emojis
                        for db_emoji in default_emojis_unicode:
                            db_emoji_unicode = db_emoji
                            db_emoji_name = default_emojis_unicode[db_emoji_unicode]
                            if emoji_to_add in [db_emoji_name, db_emoji_unicode]:
                                valid_emojis.append(db_emoji_unicode)
                                counter += 1
                                break
                        else:
                            # check mdm: name
                            for db_emoji in custom_mdm_emojis:
                                if emoji_to_add == db_emoji[1] or emoji_to_add == f":{db_emoji[1]}:":
                                    valid_emojis.append(db_emoji[0])
                                    counter += 1
                                    break
                            else:
                                # check other: name
                                for db_emoji in custom_other_emojis:
                                    if emoji_to_add == db_emoji[1] or emoji_to_add == f":{db_emoji[1]}:":
                                        valid_emojis.append(db_emoji[0])
                                        counter += 1
                                        break
                                else:
                                    invalid_emojis.append(emoji_to_add)

            if len(valid_emojis) == 0:
                emoji = util.emoji("disappointed")
                await ctx.send(f"None of the given emojis are valid. {emoji}\nAre you sure I am on the server these emojis are on?\n(Also make sure that there are spaces between the emoji.)")
                return

            # EDIT DATABASE ENTRY

            valid_emojis_filtered = [] # first remove duplicates
            for item in valid_emojis:
                if item in valid_emojis_filtered:
                    print("duplicate emoji")
                else:
                    valid_emojis_filtered.append(item)

            try: # clear old entry
                cur.execute("DELETE FROM npreactions WHERE id = ?", (user_id,))
                con.commit()
            except Exception as e:
                print("Error while trying to remove old npreactions entry: ", e)

            the_reacts = valid_emojis_filtered + ["","","",""]

            cur.execute("INSERT INTO npreactions VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (user_id, user_name, the_reacts[0], the_reacts[1], the_reacts[2], the_reacts[3], the_reacts[4], ""))
            con.commit()
            await util.changetimeupdate()

            # PREPARE RESPONSE/CONFIRMATION EMBED

            msg_valid = "Successfully set your reacts to:\n"
            msg_toomany = ""
            msg_invalid = ""
            c = 0
            for emoji in the_reacts:
                c += 1
                if c <= 5:
                    msg_valid += f" {emoji} "
                else:
                    if emoji != "":
                        msg_toomany += f" {emoji} "

            for arg in invalid_emojis:
                msg_invalid += f" {arg} "

            if len(msg_toomany) > 0:
                msg_toomany = "\n\nOnly up to 5 reacts allowed, so could not add:\n" + msg_toomany
            if len(msg_invalid) > 0:
                msg_invalid = "\n\nDid not understand the following emojis:\n" + msg_invalid + "\n(Make sure that there are spaces between the emoji.)"

            text = msg_valid + msg_toomany + msg_invalid
            try:
                color = user.color
            except:
                color = 0x000000
            embed=discord.Embed(title="", description=text, color=color)
            await ctx.send(embed=embed)
    @_npreactions.error
    async def npreactions_error(self, ctx, error):
        await util.error_handling(ctx, error) 



    ####################################################################################################################################



    @commands.command(name='tagban', aliases = ['bantag', 'bantags', 'blocktag', 'blocktags'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _bantag(self, ctx: commands.Context, *args):
        """🔒 Blocks last.fm/musicbrainz tags from displaying
        
        You can block multiple tags by separating them with a semicolon.

        Use first argument `p` to ban entire phrases. If a phrase is banned it means that any tag that contains this word phrase will get banned.

        Note that tags and phrases are compared by getting rid of all non-alphanumeric characters (everything that is not a letter or number). So banning entire phrases with few letters might be risky and ban too many tags unintentionally.
        """

        if len(args) == 0:
            await ctx.send("Command needs arguments.")
            return

        conNP = sqlite3.connect('databases/npsettings.db')  
        curNP = conNP.cursor()
        db_list = [[util.alphanum(item[0],"lower").strip(), item[1].lower().strip()] for item in curNP.execute("SELECT tagname, bantype FROM unwantedtags").fetchall()]

        if args[0].lower() == "p":
            if len(args) < 2:
                await ctx.send("Command needs a phrase arguments.")
                return

            phrases = ' '.join(args[1:]).split(";")

            for phrase in phrases:
                if [util.alphanum(phrase,"lower").strip(), "phrase"] in db_list:
                    await ctx.send(f"Phrase {phrase.strip()} is already banned.")
                    return
                else:
                    if [util.alphanum(phrase,"lower").strip(), "tag"] in db_list:
                        tag_list = [item[0] for item in curNP.execute("SELECT tagname FROM unwantedtags").fetchall()]
                        i = 0
                        for item in tag_list:
                            if util.alphanum(item,"lower").strip() == util.alphanum(phrase,"lower").strip():
                                curNP.execute("UPDATE unwantedtags SET bantype = ? WHERE tagname = ?", ("phrase", item))
                                conNP.commit()
                                i += 1
                        await ctx.send(f"Changed ban of `{phrase.strip()}` from tag to phrase. [{i}]")
                    else:
                        curNP.execute("INSERT INTO unwantedtags VALUES (?, ?, ?)", (phrase.strip(), "phrase", ""))
                        conNP.commit()
                        await ctx.send(f"Banned entire phrase `{phrase.strip()}`.")

                    await util.changetimeupdate()
                    db_list.append([util.alphanum(phrase,"lower").strip(), "phrase"])
        else:
            tags  = ' '.join(args).split(";")
            for tag in tags:
                if [util.alphanum(tag,"lower").strip(), "tag"] in db_list:
                    await ctx.send(f"Tag {tag.strip()} is already banned.")
                    return
                else:
                    if [util.alphanum(tag,"lower").strip(), "phrase"] in db_list:
                        tag_list = [item[0] for item in curNP.execute("SELECT tagname FROM unwantedtags").fetchall()]
                        i = 0
                        for item in tag_list:
                            if util.alphanum(item,"lower").strip() == util.alphanum(tag,"lower").strip():
                                curNP.execute("UPDATE unwantedtags SET bantype = ? WHERE tagname = ?", ("tag", item))
                                conNP.commit()
                                i += 1
                        await ctx.send(f"Changed ban of `{tag.strip()}` from entire phrase to tag as is. [{i}]")
                    else:
                        curNP.execute("INSERT INTO unwantedtags VALUES (?, ?, ?)", (tag.strip(), "tag", ""))
                        conNP.commit()
                        await ctx.send(f"Banned tag `{tag.strip()}`.")

                    await util.changetimeupdate()
                    db_list.append([util.alphanum(tag,"lower").strip(), "tag"])

    @_bantag.error
    async def bantag_error(self, ctx, error):
        await util.error_handling(ctx, error) 



    @commands.command(name='tagunban', aliases = ['unbantag', 'unbantags', 'unblocktag', 'unblocktags'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _unbantag(self, ctx: commands.Context, *args):
        """🔒 Unblocks last.fm/musicbrainz tags from displaying
        
        You can unblock multiple tags by separating them with a semicolon.
        """
        if len(args) == 0:
            await ctx.send("Command needs arguments.")
            return

        conNP = sqlite3.connect('databases/npsettings.db')  
        curNP = conNP.cursor()
        tag_list = [item[0] for item in curNP.execute("SELECT tagname FROM unwantedtags").fetchall()]

        tags  = ' '.join(args).split(";")

        i = 0
        for tag in tags:
            for item in tag_list:
                if util.alphanum(item,"lower").strip() == util.alphanum(tag,"lower").strip():
                    curNP.execute("DELETE FROM unwantedtags WHERE tagname = ?", (item,))
                    conNP.commit()
                    if item in tag_list:
                        tag_list.remove(item)
                        i += 1

        await util.changetimeupdate()
        await ctx.send(f"Removed {i} tag(s) from unwanted tags database.")

    @_unbantag.error
    async def unbantag_error(self, ctx, error):
        await util.error_handling(ctx, error) 



    @commands.command(name='tagbanregex', aliases = ['bantagregex', 'bantagsregex', 'blocktagregex', 'blocktagsregex', 'banregex', 'blockregex'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _bantagregex(self, ctx: commands.Context, *args):
        """🔒 Blocks last.fm/musicbrainz tags via regular expression
        """
        if len(args) == 0:
            await ctx.send("Command needs arguments.")
            return

        conNP = sqlite3.connect('databases/npsettings.db')  
        curNP = conNP.cursor()
        db_list = [item[0] for item in curNP.execute("SELECT regex FROM unwantedtags_regex").fetchall()]

        argument = ' '.join(args)

        if argument in db_list:
            await ctx.send("This regular expression is already in the database!")
            return

        num_list = [util.forceinteger(item[0]) for item in curNP.execute("SELECT id FROM unwantedtags_regex").fetchall()]

        if len(num_list) == 0:
            num = 1
        else:
            num = max(num_list) + 1
            
        curNP.execute("INSERT INTO unwantedtags_regex VALUES (?, ?, ?)", (str(num), argument, ""))
        conNP.commit()
        await util.changetimeupdate()
        await ctx.send(f"Banned regular expression.```{argument}```")

    @_bantagregex.error
    async def bantagregex_error(self, ctx, error):
        await util.error_handling(ctx, error) 




    @commands.command(name='tagunbanregex', aliases = ['unbantagregex', 'unbantagsregex', 'unblocktagregex', 'unblocktagsregex', 'unbanregex', 'unblockregex'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _unbantagregex(self, ctx: commands.Context, *args):
        """🔒 Unblocks last.fm/musicbrainz tagbans via regular expression
        """
        if len(args) == 0:
            await ctx.send("Command needs arguments.")
            return

        conNP = sqlite3.connect('databases/npsettings.db')  
        curNP = conNP.cursor()
        db_list = [item[0] for item in curNP.execute("SELECT regex FROM unwantedtags_regex").fetchall()]

        argument = ' '.join(args)

        if argument not in db_list:
            await ctx.send("This regular expression was not in the database!")
            return

        curNP.execute("DELETE FROM unwantedtags_regex WHERE regex = ?", (argument,))
        conNP.commit()

        await util.changetimeupdate()
        await ctx.send(f"This regular expression was removed from database!```{argument}```")

    @_unbantagregex.error
    async def unbantagregex_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='testtag', aliases = ['tagtest', 'testtags'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _testgenretags(self, ctx: commands.Context, *args):
        """🔒 Test whether tags would be excluded or not

        You can test multiple tags at once by separating them with a semicolon.
        Just keep in mind that combinations of tags may lead to different results than testing them one by one, because the command will also filter out tags it deems duplicates (such as 2 tags that only differ by one being the singular and the other the plural word).
        """
        if len(args) == 0:
            await ctx.send("Command needs arguments.")
            return

        conNP = sqlite3.connect('databases/npsettings.db')  
        curNP = conNP.cursor()
        
        arguments = ' '.join(args).split(";")

        tag_list = [argument.strip() for argument in arguments]
        
        filtered_list = util.filter_genretags(tag_list)

        if len(filtered_list) == 0:
            if len(tag_list) > 1:
                await ctx.send("All tags are blocked.")
            else:
                await ctx.send("Tag is blocked.")
        else:
            output = ', '.join(filtered_list)
            if len(filtered_list) == len(tag_list):
                if len(tag_list) > 1:
                    await ctx.send(f"None of the tags are blocked.\n\nOutput:```{output}```")
                else:
                    await ctx.send(f"Tag not blocked.\n\nOutput:```{output}```")
            else:
                await ctx.send(f"Some of the tags were filtered out.\n\nOutput:```{output}```")

    @_testgenretags.error
    async def testgenretags_error(self, ctx, error):
        await util.error_handling(ctx, error)



    async def tagbanimport(self, ctx, bantype):
        user_id = str(ctx.author.id)
        user_name = str(ctx.author.name)
        the_message = ctx.message
        if not the_message.attachments:
            await ctx.send("No attachment found. Needs a .txt file with one tag per line.")
            return

        split_v1 = str(the_message.attachments).split("filename='")[1]
        filename = str(split_v1).split("' ")[0]

        if filename.endswith(".txt"):
            await the_message.attachments[0].save(fp=f"temp/tagban_{bantype}_import_{user_id}.txt")

            conNP = sqlite3.connect('databases/npsettings.db')  
            curNP = conNP.cursor()

            # OPEN FILE AND CHECK SIZE
            with open(f'{sys.path[0]}/temp/tagban_{bantype}_import_{user_id}.txt', 'r') as txtfile:
                row_count = sum(1 for line in txtfile)
                if row_count > 10000:
                    await ctx.send("Error: File is too large for the tagban functionality.")
                    continuing = False

            # OPEN FILE AND ADD ITEMS
            with open(f'{sys.path[0]}/temp/tagban_{bantype}_import_{user_id}.txt', 'r') as txtfile:

                # PARSE AND WRITE INTO DATABASE
                if bantype == "tag":
                    item_list = [item[0] for item in curNP.execute("SELECT tagname FROM unwantedtags WHERE bantype = ?", ("tag",)).fetchall()]
                elif bantype == "phrase":
                    item_list = [item[0] for item in curNP.execute("SELECT tagname FROM unwantedtags WHERE bantype = ?", ("phrase",)).fetchall()]
                elif bantype == "regex":
                    item_list = [item[0] for item in curNP.execute("SELECT regex FROM unwantedtags_regex").fetchall()]
                    num_list = [util.forceinteger(item[0]) for item in curNP.execute("SELECT id FROM unwantedtags_regex").fetchall()]
                    if len(num_list) == 0:
                        num = 0
                    else:
                        num = max(num_list)

                counter = 0
                for line in txtfile:
                    argument = line.strip()

                    if bantype == "tag":
                        argument = argument.lower()
                        if argument in item_list:
                            continue
                        curNP.execute("INSERT INTO unwantedtags VALUES (?, ?, ?)", (argument, "tag", ""))
                    
                    elif bantype == "phrase":
                        argument = argument.lower()
                        if argument in item_list:
                            continue
                        curNP.execute("INSERT INTO unwantedtags VALUES (?, ?, ?)", (argument, "phrase", ""))
                    
                    elif bantype == "regex":
                        if argument in item_list:
                            continue
                        num += 1
                        curNP.execute("INSERT INTO unwantedtags_regex VALUES (?, ?, ?)", (str(num), argument, ""))

                    counter += 1
                conNP.commit()

            if counter == 0:
                await ctx.send(f"No items added to tagban database ({bantype})...")
            else:
                await util.changetimeupdate()
                await ctx.send(f"Added {counter} items to the tagban database ({bantype}).")
            os.remove(f"{sys.path[0]}/temp/tagban_{bantype}_import_{user_id}.txt")



    @commands.group(name='tagbanimport', pass_context=True, invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _tagbanimport(self, ctx: commands.Context, *args):
        """🔒 import .txt file with tags to ban
        
        Put one tag per line. And then use command with file attachment.
        
        Use subcommand `p` to import as phrase block.
        Use subcommand `regex` to import as regex block.
        """

        await self.tagbanimport(ctx, "tag")

    @_tagbanimport.error
    async def tagbanimport_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_tagbanimport.command(name="regex", pass_context=True)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _tagbanimport_regex(self, ctx: commands.Context, *args):
        """🔒 import .txt file with tags to ban as regex

        Put one expression per line. And then use command with file attachment."""

        await self.tagbanimport(ctx, "regex")

    @_tagbanimport_regex.error
    async def tagbanimport_regex_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_tagbanimport.command(name="p", aliases = ["phrase"], pass_context=True)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _tagbanimport_phrase(self, ctx: commands.Context, *args):
        """🔒 import .txt file with tags to ban as phrase

        Put one phrase per line. And then use command with file attachment."""

        await self.tagbanimport(ctx, "phrase")

    @_tagbanimport_phrase.error
    async def tagbanimport_phrase_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='tagbanexport', aliases = ["phrase"])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _tagbanexport(self, ctx: commands.Context, *args):
        """🔒 export .txt files with tags to ban
        """

        timestamp_utc = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())

        conNP = sqlite3.connect('databases/npsettings.db')  
        curNP = conNP.cursor()

        with open(f"temp/tagban_norm_{str(timestamp_utc)}.txt", 'w') as f:
            item_list = [item[0] for item in curNP.execute("SELECT tagname FROM unwantedtags WHERE bantype = ?", ("tag",)).fetchall()]
            item_list.sort()

            for item in item_list:
                f.write(f"{item.strip().lower()}\n")

        with open(f"temp/tagban_phrases_{str(timestamp_utc)}.txt", 'w') as f:
            item_list = [item[0] for item in curNP.execute("SELECT tagname FROM unwantedtags WHERE bantype = ?", ("phrase",)).fetchall()]
            item_list.sort()

            for item in item_list:
                f.write(f"{item.strip().lower()}\n")

        with open(f"temp/tagban_regex_{str(timestamp_utc)}.txt", 'w') as f:
            item_list = [item[0] for item in curNP.execute("SELECT regex FROM unwantedtags_regex").fetchall()]

            for item in item_list:
                f.write(f"{item.strip().lower()}\n")

        my_files = [
                        discord.File(f'temp/tagban_norm_{str(timestamp_utc)}.txt'),
                        discord.File(f'temp/tagban_phrases_{str(timestamp_utc)}.txt'),
                        discord.File(f'temp/tagban_regex_{str(timestamp_utc)}.txt'),
                    ]

        textmessage = f"Here are the full lists of banned tags, banned phrases and regex match exclusions for last.fm and musicbrainz tags."
        await ctx.send(textmessage, files=my_files)
        os.remove(f"{sys.path[0]}/temp/tagban_norm_{str(timestamp_utc)}.txt")
        os.remove(f"{sys.path[0]}/temp/tagban_phrases_{str(timestamp_utc)}.txt")
        os.remove(f"{sys.path[0]}/temp/tagban_regex_{str(timestamp_utc)}.txt")

    @_tagbanexport.error
    async def tagbanexport_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='removefm', aliases = ["delfm"])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _removefm(self, ctx: commands.Context, *args):
        """🔜🔒 removes someone's fm account

        e.g. when someone loses access to their discord account and rejoins with a new one remove the lastfm account from the first discord account.
        """

        await ctx.send("under construction")

    @_removefm.error
    async def removefm_error(self, ctx, error):
        await util.error_handling(ctx, error)



    ####################################################################################################################################

            

    @commands.command(name='tagsettings', aliases = ['settags', 'tags', "tagset", "tag"])
    @commands.check(util.is_active)
    async def _nptags(self, ctx: commands.Context, *args):
        """🔜 Configure np tags"""

        # under construction

        await ctx.send("⚠️ under construction")
    @_nptags.error
    async def nptags_error(self, ctx, error):
        await util.error_handling(ctx, error) 






async def setup(bot: commands.bot) -> None:
    await bot.add_cog(
        Music_NowPlaying(bot),
        guilds = [discord.Object(id = int(os.getenv("guild_id")))])