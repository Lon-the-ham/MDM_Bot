import discord
from discord.ext import commands
import datetime
from other.utils.utils import Utils as util
import os
import asyncio
import sqlite3
import requests
import json
from bs4 import BeautifulSoup
import random

import traceback


class ScrobblingCheck():
    def scrobbling_enabled(ctx):
        conM = sqlite3.connect(f'databases/botsettings.db')
        curM = conM.cursor()
        scrob_func_list = [item[0] for item in curM.execute("SELECT value FROM serversettings WHERE name = ?", ("scrobbling functionality",)).fetchall()]

        if len(scrob_func_list) < 1:
            raise commands.CheckFailure("This functionality is turned off.")
            return False
        else:
            scrob_func = scrob_func_list[0].lower()
            if scrob_func == "on":
                return True
            else:
                raise commands.CheckFailure("This functionality is turned off.")
                return False



class Music_Scrobbling(commands.Cog):
    def __init__(self, bot: commands.bot) -> None:
        self.bot = bot
        self.prefix = os.getenv("prefix")
        self.tagseparator = " ‧ "
        self.loadingbar_width = 16



    ################################## update functions



    def parse_scrobbled_track(self, trackdata):
        try:
            artist_name = trackdata['artist']['#text']
        except:
            artist_name = ""

        try:
            artist_mbid = trackdata['artist']['mbid']
        except:
            artist_mbid = ""

        try:
            album_name = trackdata['album']['#text']
        except:
            album_name = ""

        try:
            album_mbid = trackdata['album']['mbid']
        except:
            album_mbid = ""

        try:
            track_name = trackdata['name']
        except:
            track_name = ""

        try:
            track_mbid = trackdata['mbid']
        except:
            track_mbid = ""

        try:
            image_url = trackdata['image'][-1]['#text']
        except:
            image_url = ""

        try:
            lfm_url = trackdata['url']
        except:
            lfm_url = ""

        try:
            date_uts = trackdata['date']['uts']
        except:
            date_uts = 0

        try:
            date_text = trackdata['date']['#text']
        except:
            date_text = ""

        #return (artist_name, artist_mbid, album_name, album_mbid, track_name, track_mbid, image_url, lfm_url, date_uts, date_text)
        return (artist_name, album_name, track_name, date_uts)



    async def get_userscrobbles_from_page(self, ctx, lfm_name, page):
        try:
            # FETCH SCROBBLE INFORMATION
            payload = {
                'method': 'user.getRecentTracks',
                'user': lfm_name,
                'limit': "200",
                'page': page,
            }
            cooldown = True
            response = await util.lastfm_get(ctx, payload, cooldown, "userupdate")
            if response == "rate limit":
                raise ValueError("Hit internal lastfm rate limit.")

            try:
                rjson = response.json()
                #print(rjson['recenttracks']['@attr'])

                total_pages = rjson['recenttracks']['@attr']['totalPages']
                page = rjson['recenttracks']['@attr']['page']
                total = rjson['recenttracks']['@attr']['total']

                # FETCH FIRST PAGE
                tracklist = rjson['recenttracks']['track']

                return tracklist, total_pages, total
            except:
                try:
                    raise ValueError(f"```{str(response.json())}```")
                except:
                    raise ValueError(f"{str(response)}")

        except Exception as e:
            print("Error:", e)
            raise ValueError(f"while trying to fetch user information: {e}.")



    def releasewise_insert(self, lfm_name, item_dict):
        conFM2 = sqlite3.connect('databases/scrobbledata_releasewise.db')
        curFM2 = conFM2.cursor()
        curFM2.execute(f"CREATE TABLE IF NOT EXISTS [{lfm_name}] (artist_name text, album_name text, count integer, last_time integer, first_time integer)")

        for k,v in item_dict.items():
            artist = k[0]
            album  = k[1]
            try:
                count = int(v[0])
            except Exception as e:
                count = 0
            try:
                now_time = int(v[1])
            except:
                now_time = 0

            try:
                first_time = int(v[2])
            except:
                first_time = util.year9999()
            
            try:
                result = curFM2.execute(f"SELECT count, last_time, first_time FROM [{lfm_name}] WHERE artist_name = ? AND album_name = ?", (artist, album))
                rtuple = result.fetchone()
                prev_count = int(rtuple[0])
                try:
                    prev_time = int(rtuple[1])
                except:
                    prev_time = 0
                try:
                    prev_first = int(rtuple[2])
                except:
                    prev_first = util.year9999()
            except:
                prev_count = 0
                prev_time = 0
                prev_first = util.year9999()

            if prev_count == 0:
                curFM2.execute(f"INSERT INTO [{lfm_name}] VALUES (?, ?, ?, ?, ?)", (artist, album, count, now_time, first_time))

            else:
                new_count = prev_count + count
                if prev_time < now_time:
                    time = now_time
                else:
                    time = prev_time
                # keep first time
                if first_time < prev_first:
                    curFM2.execute(f"UPDATE [{lfm_name}] SET count = ?, last_time = ?, first_time = ? WHERE artist_name = ? AND album_name = ?", (new_count, time, first_time, artist, album))
                else:
                    curFM2.execute(f"UPDATE [{lfm_name}] SET count = ?, last_time = ? WHERE artist_name = ? AND album_name = ?", (new_count, time, artist, album))
        conFM2.commit()
        #print("inserted into secondary database as well")



    def trackwise_insert(self, lfm_name, item_dict):
        conFM3 = sqlite3.connect('databases/scrobbledata_trackwise.db')
        curFM3 = conFM3.cursor()
        curFM3.execute(f"CREATE TABLE IF NOT EXISTS [{lfm_name}] (artist_name text, track_name text, count integer, last_time integer, first_time integer)")

        for k,v in item_dict.items():
            artist = k[0]
            track  = k[1]
            try:
                count = int(v[0])
            except Exception as e:
                count = 0
            try:
                now_time = int(v[1])
            except:
                now_time = 0

            try:
                first_time = int(v[2])
            except:
                first_time = util.year9999()
            
            try:
                result = curFM3.execute(f"SELECT count, last_time, first_time FROM [{lfm_name}] WHERE artist_name = ? AND track_name = ?", (artist, track))
                rtuple = result.fetchone()
                prev_count = int(rtuple[0])
                try:
                    prev_time = int(rtuple[1])
                except:
                    prev_time = 0
                try:
                    prev_first = int(rtuple[2])
                except:
                    prev_first = util.year9999()
            except:
                prev_count = 0
                prev_time = 0
                prev_first = util.year9999()

            if prev_count == 0:
                curFM3.execute(f"INSERT INTO [{lfm_name}] VALUES (?, ?, ?, ?, ?)", (artist, track, count, now_time, first_time))

            else:
                new_count = prev_count + count
                if prev_time < now_time:
                    time = now_time
                else:
                    time = prev_time
                # keep first time
                if first_time < prev_first:
                    curFM3.execute(f"UPDATE [{lfm_name}] SET count = ?, last_time = ?, first_time = ? WHERE artist_name = ? AND track_name = ?", (new_count, time, first_time, artist, track))
                else:
                    curFM3.execute(f"UPDATE [{lfm_name}] SET count = ?, last_time = ? WHERE artist_name = ? AND track_name = ?", (new_count, time, artist, track))
        conFM3.commit()

        

    async def fetch_scrobbles(self, ctx, lfm_name, argument):
        cooldown = True

        # GET LAST TRACK OF USER FROM DATABASE

        conFM = sqlite3.connect('databases/scrobbledata.db')
        curFM = conFM.cursor()
        curFM.execute(f"CREATE TABLE IF NOT EXISTS [{lfm_name}] (id integer, artist_name text, album_name text, track_name text, date_uts integer)")
        timetext = ""

        if argument.strip().startswith("--force"):
            force_now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())

            force_arguments = argument.replace("--force","").strip().lower()

            if force_arguments in ["all", "everything"]:
                cutoff_time = -1
                timetext = "everything"
            else:
                try:
                    timeseconds, timetext, rest = await util.timeparse(force_arguments, force_now)
                    if int(timeseconds) <= 0 or int(timeseconds) > force_now:
                        raise ValueError("invalid number of seconds")
                except:
                    timetext = "2 weeks"
                    timeseconds = 14 * 24 * 60 * 60

                cutoff_time = force_now - int(timeseconds)

            curFM.execute(f"DELETE FROM [{lfm_name}] WHERE date_uts > ?", (cutoff_time,))
            conFM.commit()

            conFM2 = sqlite3.connect('databases/scrobbledata_releasewise.db')
            curFM2 = conFM2.cursor()
            curFM2.execute(f"CREATE TABLE IF NOT EXISTS [{lfm_name}] (artist_name text, album_name text, count integer, last_time integer)")
            curFM2.execute(f"DELETE FROM [{lfm_name}]")
            conFM2.commit()
            conFM3 = sqlite3.connect('databases/scrobbledata_trackwise.db')
            curFM3 = conFM3.cursor()
            curFM3.execute(f"CREATE TABLE IF NOT EXISTS [{lfm_name}] (artist_name text, track_name text, count integer, last_time integer)")
            curFM3.execute(f"DELETE FROM [{lfm_name}]")
            conFM3.commit()

            print(f"deleted {timetext} of {lfm_name}'s scrobble information")

        try:
            lasttime = int([item[0] for item in curFM.execute(f"SELECT MAX(date_uts) FROM [{lfm_name}]").fetchall()][0])
        except Exception as e:
            lasttime = 0
        try:
            num_items_previously = int([item[0] for item in curFM.execute(f"SELECT COUNT(id) FROM [{lfm_name}]").fetchall()][0])
            ignorable_pages = int(num_items_previously // 200)
        except:
            num_items_previously = 0
            ignorable_pages = 0

        page_int = 0
        total_pages_int = 1
        continue_loop = True
        count = 0
        i = -1

        emoji = util.emoji("load")
        if argument.strip().startswith("--force"):
            if cutoff_time <= 0:
                description = f"Forcing update from scratch...\nFetching scrobble information {emoji}\n\n"
            else:
                description = f"Forcing update from <t:{cutoff_time}:f> ({timetext} ago)...\nFetching scrobble information {emoji}\n\n"
        else:
            description = f"Fetching scrobble information {emoji}\n\n"

        progress = 0
        loadingbar = util.get_loadingbar(self.loadingbar_width, progress)
        embed = discord.Embed(title="", description=description+loadingbar+f" 0%", color=0x000000)
        message = await ctx.reply(embed=embed, mention_author=False)

        old_now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())

        # FETCH NEW DATA

        try:
            scrobble_list = []

            if not argument.strip().startswith("--force"):
                item_dict = {} # ALBUMS
                track_dict = {} # TRACKS
            previous_item = None
            print("Start fetching data...")
            while page_int < total_pages_int:
                if not continue_loop:
                    break
                page_int += 1
                page_string = str(page_int)
                print(f"Fetching page {page_string} from {lfm_name}")

                for t in [5,10,15,20,25]:
                    try:
                        tracklist, total_pages, total = await self.get_userscrobbles_from_page(ctx, lfm_name, page_string)
                        break
                    except Exception as e:
                        print(f"Waiting {t} seconds... ({e})")
                        await asyncio.sleep(t)
                        print("continue...")
                else:
                    print("Cancelled action.")
                    await ctx.send(f"Error: {e}")
                    continue

                if i == -1: # first page
                    i = int(total)
                elif str(total_pages_int) != total_pages: # following pages
                    print("---page was added in the meantime---")

                total_pages_int = int(total_pages)

                # PARSE PAGE ENTRIES
                for trackdata in tracklist:
                    item = self.parse_scrobbled_track(trackdata)
                    uts = int(item[-1])
                    if uts == 0: #print("skipping currently listened to track")
                        continue
                    elif uts <= lasttime:
                        continue_loop = False
                        break
                    if previous_item == item:
                        print("skipping double entry")
                        continue
                    elif previous_item != None and uts > int(previous_item[-1]):
                        print("skipping entry with time anomaly")
                        continue

                    #insert into scrobble database
                    item_indexed = (i,) + item
                    scrobble_list.append(item_indexed)
                    count += 1
                    i -= 1

                    if not argument.strip().startswith("--force"):
                        # prepare for inserting into releasewise DB
                        artist_filtername = util.compactnamefilter(item[0],"artist") #''.join([x for x in item[0].upper() if x.isalnum()])
                        album_filtername = util.compactnamefilter(item[1],"album") #''.join([x for x in item[1].upper() if x.isalnum()])
                        track_filtername = util.compactnamefilter(item[2],"track")
                        
                        # RELEASEWISE DATABASE PREPARATION
                        if (artist_filtername, album_filtername) in item_dict:
                            release = item_dict[(artist_filtername, album_filtername)]
                            try:
                                releasecount = int(release[0])
                            except:
                                releasecount = 0
                            try:
                                releaselastprev = int(release[1])
                            except:
                                releaselastprev = 0

                            releasefirst = release[2]

                            item_dict[(artist_filtername, album_filtername)] = (releasecount + 1, releaselastprev, releasefirst)
                        else:
                            try:
                                releaselast = int(item[3])
                                releasefirst = releaselast
                                if releasefirst < 1000000000:
                                    releasefirst = util.year9999()
                            except:
                                releaselast = 0
                                releasefirst = util.year9999()
                            item_dict[(artist_filtername, album_filtername)] = (1, releaselast, releasefirst)

                        # TRACKWISE DATABASE PREPARATION
                        if (artist_filtername, track_filtername) in track_dict:
                            trackitem = track_dict[(artist_filtername, track_filtername)]
                            try:
                                trackcount = int(trackitem[0])
                            except:
                                trackcount = 0
                            try:
                                tracklastprev = int(trackitem[1])
                            except:
                                tracklastprev = 0

                            trackfirst = trackitem[2]

                            track_dict[(artist_filtername, track_filtername)] = (trackcount + 1, tracklastprev, trackfirst)
                        else:
                            try:
                                tracklast = int(item[3])
                                trackfirst = tracklast
                                if trackfirst < 1000000000:
                                    trackfirst = util.year9999()
                            except:
                                tracklast = 0
                                trackfirst = util.year9999()
                            track_dict[(artist_filtername, track_filtername)] = (1, tracklast, trackfirst)

                    # for next iteration
                    previous_item = item

                    # loading bar
                    try:
                        new_now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())
                        new_progress = min(int((page_int / max(total_pages_int - ignorable_pages, 1)) * 100), 99)

                        if new_progress > progress and ((new_now > old_now + 1) or ((new_now >= old_now + 1) and progress == 0)):
                            loadingbar = util.get_loadingbar(self.loadingbar_width, new_progress)
                            embed = discord.Embed(title="", description=description+loadingbar+f" {new_progress}%", color=0x000000)
                            await message.edit(embed=embed)
                            progress = new_progress
                            old_now = new_now
                    except Exception as e:
                        print("Error:", e)

            for item_indexed in sorted(scrobble_list, key = lambda x : x[0]):
                curFM.execute(f"INSERT INTO [{lfm_name}] VALUES (?, ?, ?, ?, ?)", item_indexed)
            conFM.commit()
            if argument.strip().startswith("--force"):
                await self.reload_userdbs(lfm_name)
            else:
                self.releasewise_insert(lfm_name, item_dict)
                self.trackwise_insert(lfm_name, track_dict)
            await util.changetimeupdate()
            print("done")

        except Exception as e:
            print("Error:", e)
            raise ValueError(f"Issue while trying to handle scrobble information from page {page_int}.```{e}```")

        return message, count



    async def run_scrobbledata_sanitycheck(self, lfm_name, leeway):
        if type(leeway) == str:
            leeway = int(leeway)

        conFM = sqlite3.connect('databases/scrobbledata.db')
        curFM = conFM.cursor()

        scrobbles = [[item[0],item[1],item[2],item[3]] for item in curFM.execute(f"SELECT artist_name, album_name, track_name, date_uts FROM [{lfm_name}] ORDER BY date_uts ASC").fetchall()]
        print("previous number of items:", len(scrobbles))

        prev_artist = ""
        prev_album = ""
        prev_track = ""
        prev_uts = ""

        new_scrobbles = []
        i = 0
        sus = 0
        release_dict = {}

        for item in scrobbles:
            artist = item[0]
            album = item[1]
            track = item[2]
            uts = item[3]

            if uts < 1000000000:
                first_time = util.year9999()
            else:
                first_time = uts

            if (artist == prev_artist) and (album == prev_album) and (track == prev_track) and (abs(uts - prev_uts) < (leeway+1)) and uts > 999999999:
                print(f"Removing: {artist} - {track} ({album}) scrobbled at {uts}")
                continue

            if uts == prev_uts:
                sus += 1

            i += 1
            new_scrobbles.append((i, artist, album, track, uts))

            artist_compact = util.compactnamefilter(artist,"artist")
            album_compact = util.compactnamefilter(album,"album")

            if (artist_compact,album_compact) in release_dict:
                entry = release_dict[(artist_compact,album_compact)]
                prev_count = entry[0]
                prev_time = entry[1]
                prev_first = entry[2]

                if first_time > prev_first:
                    first_time = prev_first

                if prev_time > uts:
                    release_dict[(artist_compact,album_compact)] = (prev_count + 1, prev_time, first_time)
                else:
                    release_dict[(artist_compact,album_compact)] = (prev_count + 1, uts, first_time)
            else:
                release_dict[(artist_compact,album_compact)] = (1, uts, first_time)

            # assign for next itereration
            prev_artist = artist
            prev_album = album
            prev_track = track
            prev_uts = uts

        print("new number of itmes:", len(new_scrobbles))

        curFM.execute(f"DELETE FROM [{lfm_name}]")
        for item in new_scrobbles:
            curFM.execute(f"INSERT INTO [{lfm_name}] VALUES (?, ?, ?, ?, ?)", item)
        conFM.commit()

        conFM2 = sqlite3.connect('databases/scrobbledata_releasewise.db')
        curFM2 = conFM2.cursor()
        curFM2.execute(f"CREATE TABLE IF NOT EXISTS [{lfm_name}] (artist_name text, album_name text, count integer, last_time integer)")
        curFM2.execute(f"DELETE FROM [{lfm_name}]")
        for k,v in release_dict.items():
            artist = k[0]
            album = k[1]
            count = v[0]
            time = v[1]
            first = v[2]
            curFM2.execute(f"INSERT INTO [{lfm_name}] VALUES (?, ?, ?, ?, ?)", (artist, album, count, time, first))
        conFM2.commit()

        return len(scrobbles), len(new_scrobbles), sus



    async def reload_userdbs(self, lfm_name):
        print(f"Try summarising {lfm_name} data")
        i = 0
        try:
            conFM = sqlite3.connect('databases/scrobbledata.db')
            curFM = conFM.cursor()
            conFM2 = sqlite3.connect('databases/scrobbledata_releasewise.db')
            curFM2 = conFM2.cursor()
            conFM3 = sqlite3.connect('databases/scrobbledata_trackwise.db')
            curFM3 = conFM3.cursor()

            curFM.execute(f"CREATE TABLE IF NOT EXISTS [{lfm_name}] (id integer, artist_name text, album_name text, track_name text, date_uts integer)")
            curFM2.execute(f"CREATE TABLE IF NOT EXISTS [{lfm_name}] (artist_name text, album_name text, count integer, last_time integer, first_time integer)")
            curFM2.execute(f"DELETE FROM [{lfm_name}]")
            conFM2.commit()
            curFM3.execute(f"CREATE TABLE IF NOT EXISTS [{lfm_name}] (artist_name text, track_name text, count integer, last_time integer, first_time integer)")
            curFM3.execute(f"DELETE FROM [{lfm_name}]")
            conFM3.commit()

            scrobbles = [[util.compactnamefilter(item[0],"artist"),util.compactnamefilter(item[1],"album"),util.compactnamefilter(item[2],"track"),item[3]] for item in curFM.execute(f"SELECT artist_name, album_name, track_name, date_uts FROM [{lfm_name}]").fetchall()]

            release_dict = {}
            track_dict = {}

            for item in scrobbles:
                i += 1

                # ALBUMS
                artist = item[0]
                album = item[1]
                try:
                    time = int(item[3])
                except:
                    time = 0
                if time < 1000000000:
                    first = util.year9999()
                else:
                    first = time

                if (artist, album) in release_dict:
                    entry = release_dict[(artist, album)]
                    prev_count = entry[0]
                    prev_time = entry[1]
                    prev_first = entry[2]
                    
                    if first > prev_first:
                        first_of2 = prev_first
                    else:
                        first_of2 = first

                    if prev_time > time:
                        release_dict[(artist, album)] = (prev_count + 1, prev_time, first_of2)
                    else:
                        release_dict[(artist, album)] = (prev_count + 1, time, first_of2)
                else:
                    release_dict[(artist, album)] = (1, time, first)

                # TRACKS
                track = item[2]
                if (artist, track) in track_dict:
                    entry = track_dict[(artist, track)]
                    prev_count = entry[0]
                    prev_time = entry[1]
                    prev_first = entry[2]
                    
                    if first > prev_first:
                        first_of2 = prev_first
                    else:
                        first_of2 = first

                    if prev_time > time:
                        track_dict[(artist, track)] = (prev_count + 1, prev_time, first_of2)
                    else:
                        track_dict[(artist, track)] = (prev_count + 1, time, first_of2)
                else:
                    track_dict[(artist, track)] = (1, time, first)

            print(">release wise")
            for k,v in release_dict.items():
                artist = k[0]
                album = k[1]
                count = v[0]
                time = v[1]
                first = v[2]
                curFM2.execute(f"INSERT INTO [{lfm_name}] VALUES (?, ?, ?, ?, ?)", (artist, album, count, time, first))
            conFM2.commit()

            print(">track wise")
            for k,v in track_dict.items():
                artist = k[0]
                track = k[1]
                count = v[0]
                time = v[1]
                first = v[2]
                curFM3.execute(f"INSERT INTO [{lfm_name}] VALUES (?, ?, ?, ?, ?)", (artist, track, count, time, first))
            conFM3.commit()

            return i

        except Exception as e:
            print(f"Error with reloading {lfm_name} data: {e}")
            return 0



    async def reload_releasewise_database(self, reindex):
        """re-indexes if reindex == True"""
        con = sqlite3.connect('databases/npsettings.db')
        cur = con.cursor()
        lfm_namelist = [item[0] for item in cur.execute("SELECT lfm_name FROM lastfm").fetchall()]

        i = 0

        for lfm_name in lfm_namelist:
            print(f"++++ {lfm_name} ++++")

            if reindex:
                try:
                    len_before, len_after, sus = await self.run_scrobbledata_sanitycheck(lfm_name, 0)
                    print(f"re-indexed scrobbles of {lfm_name} (removed {len_before-len_after} duplicate entries)")
                except Exception as e:
                    print(f"Error while trying to re-index {lfm_name} table")

            try:
                i += await self.reload_userdbs(lfm_name)
                print("done")
            except Exception as e:
                print("Error:", e)

        print("++++DONE+++")
        return i



    ################################## who knows functions



    def update_artistinfo(self, artist, artist_thumbnail, tags):
        try: # update stats
            now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())
            artist_fltr = util.compactnamefilter(artist,"artist")
            tags_lfm = ';'.join(tags)
            try:
                conSS = sqlite3.connect('databases/scrobblestats.db')
                curSS = conSS.cursor()
                result = curSS.execute(f"SELECT artist, thumbnail, tags_lfm, tags_other, last_update FROM artistinfo WHERE filtername = ? OR filteralias = ?", (artist_fltr,artist_fltr))
                rtuple = result.fetchone()
                #print("DB finding:", rtuple)
                test1 = str(rtuple[0])
                test2 = str(rtuple[1])
                test3 = str(rtuple[2]).split(";") + str(rtuple[3]).split(";")
                tset4 = int(rtuple[4])
                db_entry_exists = True
            except:
                db_entry_exists = False
            if db_entry_exists:
                curSS.execute(f"UPDATE artistinfo SET tags_lfm = ?, last_update = ? WHERE filtername = ? OR filteralias = ?", (tags_lfm, now, artist_fltr, artist_fltr))
            else:
                curSS.execute(f"INSERT INTO artistinfo VALUES (?, ?, ?, ?, ?, ?, ?)", (artist, artist_thumbnail, tags_lfm, "", now, artist_fltr, ""))
            conSS.commit()
        except Exception as e:
            print("Error:", e)



    async def get_last_track(self, ctx):
        member = ctx.author
        con = sqlite3.connect('databases/npsettings.db')
        cur = con.cursor()
        lfm_list = [item[0] for item in cur.execute("SELECT lfm_name FROM lastfm WHERE id = ?", (str(member.id),)).fetchall()]

        if len(lfm_list) == 0:
            # under construction: try to fetch from Discord Rich Presence instead
            raise ValueError(f"You haven't set your lastfm user account yet.\nUse `{self.prefix}setfm <your username>` to do that.")

        lfm_name = lfm_list[0]
        cooldown = True
        payload = {
            'method': 'user.getRecentTracks',
            'user': lfm_name,
            'limit': "1",
        }
        response = await util.lastfm_get(ctx, payload, cooldown)
        if response == "rate limit":
            raise ValueError("rate limit")

        try:
            rjson = response.json()
            tjson = rjson['recenttracks']['track'][0] # track json

            # PARSE LAST TRACK INFO

            song = tjson['name']
            #song_link = tjson['url']
            artist = tjson['artist']['#text']
            try:
                album = tjson['album']['#text']
            except:
                album = ""
            try:
                album_cover = tjson['image'][-1]['#text']
            except:
                album_cover = ""
            try:
                mbid = tjson['artist']['mbid']
            except:
                mbid = ""

            # FETCH ARTIST INFO
            try:
                cooldown = False
                payload = {
                    'method': 'artist.getInfo',
                }
                if mbid.strip() == "":
                    payload['mbid'] = mbid
                else:
                    payload['artist'] = artist
                response = await util.lastfm_get(ctx, payload, cooldown)

                if response == "rate limit":
                    raise ValueError("rate limit")

                rjson = response.json()

                try:
                    artist_thumbnail = rjson['artist']['image'][0]['#text']
                except:
                    artist_thumbnail = ""

                tags = []
                try:
                    for tag in rjson['artist']['tags']['tag']:
                        try:
                            tagname = tag['name'].lower()
                            tags.append(tagname)
                        except Exception as e:
                            print("Tag error:", e)
                except:
                    pass
            except Exception as e:
                print("Error while fetching artist info:", e)
                return artist, album, song, "", "", []

            if len(tags) > 0:
                self.update_artistinfo(artist, artist_thumbnail, tags)

            return artist, album, song, artist_thumbnail, album_cover, tags

        except Exception as e:
            raise ValueError(f"{str(rjson)} - {e}")



    async def wk_artist_match(self, ctx, argument):
        if argument.strip() == "":
            artist, album, song, thumbnail, cover, tags = await self.get_last_track(ctx)
            return artist, thumbnail, tags

        else:
            now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())
            fetch_api_info = False

            conSS = sqlite3.connect('databases/scrobblestats.db')
            curSS = conSS.cursor()
            artist_fltr = util.compactnamefilter(argument,"artist")
            db_entry_exists = False

            try:
                if artist_fltr == "":
                    print("WARNING: Compact conversion turns provided artist name into empty string. Wtf is this name even lol.")

                result = curSS.execute(f"SELECT artist, thumbnail, tags_lfm, tags_other, last_update FROM artistinfo WHERE filtername = ? OR filteralias = ?", (artist_fltr,artist_fltr))
                rtuple = result.fetchone()
                #print("DB finding:", rtuple)
                db_entry_exists = True

                artist = str(rtuple[0])
                thumbnail = str(rtuple[1])
                rawtags = str(rtuple[2]).split(";") + str(rtuple[3]).split(";")
                last_update = int(rtuple[4])

                if now - 180 * 24 * 3600 > last_update:
                    raise ValueError("update too old, fetching new")

                tags = []
                for tag in rawtags:
                    tag_filtered = tag.lower().strip()
                    if tag_filtered != "":
                        tags.append(tag_filtered)

                if len(tags) == 0:
                    raise ValueError("no tags in DB, better fetch from API again")

                return artist, thumbnail, tags

            except Exception as e:
                if str(e) == "'NoneType' object is not subscriptable":
                    print("artist was not in DB, will fetch...")
                else:
                    print("Notification:", e)
                #print(traceback.format_exc())

                cooldown = True
                payload = {'method': 'artist.getInfo'}
                payload['artist'] = argument

                response = await util.lastfm_get(ctx, payload, cooldown)
                if response == "rate limit":
                    print("Error: Rate limit.")
                    return argument, "", []

                rjson = response.json()

                try:
                    artist = rjson['artist']['name']
                    try:
                        thumbnail = rjson['artist']['image'][0]['#text']
                    except:
                        thumbnail = ""

                    tags = []
                    try:
                        for tag in rjson['artist']['tags']['tag']:
                            try:
                                tagname = tag['name'].lower()
                                tags.append(tagname)
                            except Exception as e:
                                print("Tag error:", e)
                    except:
                        pass

                    if len(tags) > 0:
                        self.update_artistinfo(artist, thumbnail, tags)

                    return artist, thumbnail, tags

                except Exception as e:
                    try:
                        # emergency fetch from database
                        result = curSS.execute(f"SELECT artist, thumbnail, tags_lfm, tags_other, last_update FROM artistinfo WHERE filtername = ? OR filteralias = ?", (artist_fltr,artist_fltr))
                        rtuple = result.fetchone()
                        db_entry_exists = True

                        artist = str(rtuple[0])
                        thumbnail = str(rtuple[1])
                        rawtags = str(rtuple[2]).split(";") + str(rtuple[3]).split(";")
                        last_update = int(rtuple[4])

                        tags = []
                        for tag in rawtags:
                            tag_filtered = tag.lower().strip()
                            if tag_filtered != "":
                                tags.append(tag_filtered)

                        return artist, thumbnail, tags

                    except:
                        print(f"Error: {str(rjson)} - {e}")
                        return argument, "", []



    async def wk_album_match(self, ctx, argument):
        if argument.strip() == "":
            artist, album, song, thumbnail, cover, tags = await self.get_last_track(ctx)
            return artist, album, cover, tags

        else:
            if " - " in argument:
                artist = argument.split(" - ", 1)[0]
                album = argument.split(" - ", 1)[1]
            elif "-" in argument:
                artist = argument.split("-", 1)[0]
                album = argument.split("-", 1)[1]
            else:
                raise ValueError("Could not parse artist and album.")

            payload = {
                'method': 'album.getInfo',
                'album': album,
                'artist': artist,
            }
            cooldown = True
            try:
                response = await util.lastfm_get(ctx, payload, cooldown)
                if response == "rate limit":
                    print("Error: Rate limit.")
                    return artist, album, "", []

            except Exception as e:
                print("Error:", e)
                if str(e) == "No LastFM keys provided":
                    raise ValueError("No LastFM API key provided to search for artist and track. Ask mods to add one to the bot's environment file.")
                else:
                    print(f"Issue while trying to find matching artist+track on last.fm - {e}")
                    return artist, album, "", []

            try:
                rjson = response.json()

                artist_name = rjson['album']['artist']
                album_name = rjson['album']['name']

                try:
                    thumbnail = rjson['album']['image'][-1]['#text']
                except:
                    thumbnail = ""

                tags = []
                try:
                    for tag in rjson['album']['tags']['tag']:
                        try:
                            tagname = tag['name'].lower()
                            tags.append(tagname)
                        except Exception as e:
                            print("Tag error:", e)
                except:
                    pass

                return artist_name, album_name, thumbnail, tags
            except Exception as e:
                print(f"Error: {str(response)} - {e}")
                return artist, album, "", []




    async def wk_track_match(self, ctx, argument):
        if argument.strip() == "":
            artist, album, song, thumbnail, cover, tags = await self.get_last_track(ctx)
            return artist, song, cover, tags

        else:
            if " - " in argument:
                artist = argument.split(" - ", 1)[0]
                track = argument.split(" - ", 1)[1]
            elif "-" in argument:
                artist = argument.split("-", 1)[0]
                track = argument.split("-", 1)[1]
            else:
                raise ValueError("Could not parse artist and track.")

            payload = {
                'method': 'track.getInfo',
                'track': track,
                'artist': artist,
            }
            cooldown = True
            try:
                response = await util.lastfm_get(ctx, payload, cooldown)
                if response == "rate limit":
                    print("Error: Rate limit.")
                    return artist, track, "", []

            except Exception as e:
                print("Error:", e)
                if str(e) == "No LastFM keys provided":
                    raise ValueError("No LastFM API key provided to search for artist and track. Ask mods to add one to the bot's environment file.")
                else:
                    print(f"Issue while trying to find matching artist+track on last.fm - {e}")
                    return artist, track, "", []

            try:
                rjson = response.json()
                artist_name = rjson['track']['artist']['name']
                track_name = rjson['track']['name']

                try:
                    thumbnail = rjson['track']['album']['image'][-1]['#text']
                except:
                    thumbnail = ""

                tags = []
                try:
                    for tag in rjson['track']['toptags']['tag']:
                        try:
                            tagname = tag['name'].lower()
                            tags.append(tagname)
                        except Exception as e:
                            print("Tag error:", e)
                except:
                    pass

                return artist_name, track_name, thumbnail, tags

            except Exception as e:
                print(f"Error: {str(response)} - {e}")
                return artist, track, "", []



    async def whoknows(self, ctx, argument, wk_type):
        # under construction : if argument is user mention or id then fetch from their lastfm

        con = sqlite3.connect('databases/npsettings.db')
        cur = con.cursor()
        lfm_list = [[item[0],item[1],str(item[2]).lower().strip()] for item in cur.execute("SELECT id, lfm_name, details FROM lastfm").fetchall()]

        if wk_type == "artist":
            artist, thumbnail, tags = await self.wk_artist_match(ctx, argument)
            header = util.compactaddendumfilter(artist,"artist")

            if util.compactnamefilter(artist,"artist") == "":
                emoji = util.emoji("shrug")
                await ctx.send(f"oof... what's this artist name?? ping dev to do something about it, i'm out {emoji}")
                return

        elif wk_type == "album":
            try:
                artist, album, thumbnail, tags = await self.wk_album_match(ctx, argument)
                header = util.compactaddendumfilter(artist,"artist") + " - " + util.compactaddendumfilter(album,"album")
            except Exception as e:
                if str(e) == "Could not parse artist and album.":
                    #artistless_albummatch
                    artist = ""
                    thumbnail = ""
                    tags = []
                    album = argument.upper()
                    wk_type = "album without artist"
                    header = "Album: " + util.compactaddendumfilter(album,"album")
                else:
                    raise ValueError(f"while parsing artist/album - {e}")
                    return

        elif wk_type == "track":
            try:
                artist, track, thumbnail, tags = await self.wk_track_match(ctx, argument)
                header = util.compactaddendumfilter(artist,"artist") + " - " + util.compactaddendumfilter(track,"track")
            except Exception as e:
                if str(e) == "Could not parse artist and track.":
                    #artistless_trackmatch
                    artist = ""
                    thumbnail = ""
                    tags = []
                    track = argument.upper()
                    wk_type = "track without artist"
                    header = "Track: " + util.compactaddendumfilter(track,"track")
                else:
                    raise ValueError(f"while parsing artist/track - {e}")
                    return
        else:
            raise ValueError("unknown WK type")

        #conFM = sqlite3.connect('databases/scrobbledata.db')
        #curFM = conFM.cursor()

        conFM2 = sqlite3.connect('databases/scrobbledata_releasewise.db')
        curFM2 = conFM2.cursor()

        conFM3 = sqlite3.connect('databases/scrobbledata_trackwise.db')
        curFM3 = conFM3.cursor()

        conSS = sqlite3.connect('databases/scrobblestats.db')
        curSS = conSS.cursor()
        curSS.execute(f'''CREATE TABLE IF NOT EXISTS [crowns_{str(ctx.guild.id)}] (artist text, alias text, alias2 text, crown_holder text, discord_name text, playcount integer)''')

        # ignore: inactive, wk_banned and scrobble_banned
        # proceed with: NULL, "", crown_banned

        now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())

        discordname_dict = {}
        lfmname_dict = {}
        count_list = []
        crownbanned = []
        total_plays = 0
        artistlist = [] # only for albums/tracks without provided artist

        server_member_ids = [x.id for x in ctx.guild.members]

        # FILTER BY USER STATUS

        lfm_names_in_use = []

        for useritem in lfm_list:
            try:
                user_id = int(useritem[0])
            except Exception as e:
                print("Error:", e)
                continue

            lfm_name = useritem[1]
            status = useritem[2]

            if type(status) == str and (status.startswith(("wk_banned", "scrobble_banned")) or (status.endswith("inactive") and str(ctx.guild.id) == str(os.getenv("guild_id")))):
                continue
            elif type(status) == str and status.startswith("crown_banned"):
                crownbanned.append(user_id)

            if user_id not in server_member_ids:
                continue

            if lfm_name in lfmname_dict.keys(): # check if lfm_name was already added
                continue

            lfmname_dict[user_id] = lfm_name

            # GET COUNT

            try:
                if wk_type == "artist":
                    result = curFM2.execute(f"SELECT SUM(count), MAX(last_time) FROM [{lfm_name}] WHERE artist_name = ?", (util.compactnamefilter(artist,"artist"),))

                elif wk_type == "album":
                    result = curFM2.execute(f"SELECT count, last_time FROM [{lfm_name}] WHERE artist_name = ? AND album_name = ?", (util.compactnamefilter(artist,"artist"),util.compactnamefilter(album,"album")))

                elif wk_type == "track":
                    result = curFM3.execute(f"SELECT count, last_time FROM [{lfm_name}] WHERE artist_name = ? AND track_name = ?", (util.compactnamefilter(artist,"artist"),util.compactnamefilter(track,"track")))

                ############ error case feature

                elif wk_type == "album without artist":
                    result = curFM2.execute(f"SELECT SUM(count), MAX(last_time) FROM [{lfm_name}] WHERE album_name = ?", (util.compactnamefilter(album,"album"),))
                    try:
                        rtuple = result.fetchone()
                        count = int(rtuple[0])
                        last = int(rtuple[1])
                    except:
                        count = 0
                        last = 0
                    temp_artist_list = [item[0] for item in curFM2.execute(f"SELECT artist_name FROM [{lfm_name}] WHERE album_name = ?", (util.compactnamefilter(album,"album"),)).fetchall()]  
                    for temp_artist in temp_artist_list:
                        if temp_artist not in artistlist:
                            artistlist.append(temp_artist)

                elif wk_type == "track without artist":
                    result = curFM3.execute(f"SELECT SUM(count), MAX(last_time) FROM [{lfm_name}] WHERE track_name = ?", (util.compactnamefilter(track,"track"),))
                    try:
                        rtuple = result.fetchone()
                        count = int(rtuple[0])
                        last = int(rtuple[1])
                    except:
                        count = 0
                        last = 0
                    temp_artist_list = [item[0] for item in curFM3.execute(f"SELECT artist_name FROM [{lfm_name}] WHERE track_name = ?", (util.compactnamefilter(track,"track"),)).fetchall()]  
                    for temp_artist in temp_artist_list:
                        if temp_artist not in artistlist:
                            artistlist.append(temp_artist)

                else:
                    result = (None, None)
                    print("Error: Unknown WK type")

                ############
                if wk_type in ["artist", "album", "track"]:
                    try:
                        rtuple = result.fetchone()
                        try:
                            count = int(rtuple[0])
                        except:
                            count = 0
                        try:
                            last = int(rtuple[1])
                        except:
                            last = now
                            if user_id == ctx.author.id:
                                last -= 1
                    except Exception as e:
                        print(e)
                        count = 0
                        last = now
                        if user_id == ctx.author.id:
                            last -= 1

            except Exception as e:
                if str(e).startswith("no such table"):
                    pass
                else:
                    print("Error:", e)
                count = 0
                last = now
                if user_id == ctx.author.id:
                    last -= 1

            #count_dict[user_id] = count
            count_list.append([user_id, count, last])
            total_plays += count

        # FETCH SERVER NAMES

        for member in ctx.guild.members:
            if member.id in lfmname_dict:
                discordname_dict[member.id] = str(member.name)

        # CREATE EMBED

        description = ""
        halloffame_counter = 0
        alluser_counter = 0
        posuser_counter = 0

        all_zero = True
        first = True
        crown_user = None

        count_list.sort(key=lambda x: x[2])
        count_list.sort(key=lambda x: x[1], reverse=True)

        #for key in {k: v for k, v in sorted(count_dict.items(), key=lambda item: item[1], reverse=True)}:
        for listitem in count_list:
            user_id = listitem[0]
            playcount = listitem[1]
            lastplay = listitem[2]

            if user_id not in discordname_dict:
                continue

            #if count_dict[key] > 0:
            if playcount > 0:
                posuser_counter += 1
                all_zero = False

            alluser_counter += 1
            #if key != ctx.author.id and (halloffame_counter > 14 or count_dict[key] == 0):
            if user_id != ctx.author.id and (halloffame_counter > 14 or playcount == 0):
                continue

            #if wk_type == "artist" and first and count_dict[key] >= 30 and key not in crownbanned:
            if wk_type == "artist" and first and playcount >= 30 and user_id not in crownbanned:
                placing = util.emoji("crown")
                crown_user = user_id
                crown_count = playcount
                first = False
            else:
                placing = f"{alluser_counter}."

            halloffame_counter += 1
            if user_id != ctx.author.id:
                description += f"{placing} [{discordname_dict[user_id]}](https://www.last.fm/user/{lfmname_dict[user_id]}) - **{playcount}** plays\n"
            else:
                description += f"{placing} **[{discordname_dict[user_id]}](https://www.last.fm/user/{lfmname_dict[user_id]})** - **{playcount}** plays\n"

        header += f" in {ctx.guild.name}"

        if all_zero:
            if wk_type in ["artist", "album", "track"]:
                description = f"No one here has listened to this {wk_type}."
            else:
                description = f"Error with {wk_type}. Could not find any matches."

        else:
            # CROWN update: only for artists

            if crown_user != None:
                results = [[item[0],item[1],item[2]] for item in curSS.execute(f"SELECT crown_holder, discord_name, playcount FROM [crowns_{ctx.guild.id}] WHERE alias = ? OR alias2 = ?", (util.compactnamefilter(artist,"artist"), util.compactnamefilter(artist,"artist"))).fetchall()]
                if len(results) > 0:
                    prev_crownholder = results[0][0]
                    prev_discord_name = results[0][1]
                    prev_playcount = results[0][2]

                    if prev_crownholder.upper().strip() == lfmname_dict[crown_user].upper().strip():
                        # keeping the crown
                        if crown_count > util.forceinteger(prev_playcount):
                            stonks = util.emoji("stonks")
                            description += f"\n(Updated crown playcount from {prev_playcount} to {crown_count}. {stonks})"
                    else:
                        emoji = util.emoji("unleashed")
                        description += f"\n{discordname_dict[crown_user]} yoinked crown (with {crown_count} plays) from {prev_discord_name} ({prev_playcount} plays)! {emoji}"
                    curSS.execute(f"UPDATE crowns_{ctx.guild.id} SET crown_holder = ?, discord_name = ?, playcount = ? WHERE alias = ? OR alias2 = ?", (lfmname_dict[crown_user], discordname_dict[crown_user], crown_count, util.compactnamefilter(artist,"artist"), util.compactnamefilter(artist,"artist")))
                    conSS.commit()
                else:
                    emoji = util.emoji("thumbs_up")
                    description += f"\nCrown claimed by {discordname_dict[crown_user]} with {crown_count} plays! {emoji}"
                    curSS.execute(f"INSERT INTO crowns_{ctx.guild.id} VALUES (?, ?, ?, ?, ?, ?)", (artist, util.compactnamefilter(artist,"artist"), "", lfmname_dict[crown_user],discordname_dict[crown_user],crown_count))
                    conSS.commit()

        embed = discord.Embed(title=header[:256], description=description[:4096], color=0x800000)
        if wk_type in ["artist", "album", "track"]:
            try:
                genre_tag_list = util.filter_genretags(tags)
                tag_string = f"{self.tagseparator}".join(genre_tag_list)
                if posuser_counter > 0:
                    if posuser_counter == 1:
                        plurals = ""
                    else:
                        plurals = "s"
                    tag_string += f"\n{wk_type} - {posuser_counter} listener{plurals} - {total_plays} plays"
                embed.set_footer(text=tag_string[:2048])
            except:
                pass
            try:
                embed.set_thumbnail(url=thumbnail)
            except:
                pass
        else:
            try:
                if len(artistlist) > 0:
                    artistlist_new = []
                    conSS = sqlite3.connect('databases/scrobblestats.db')
                    curSS = conSS.cursor()

                    if posuser_counter > 0:
                        if posuser_counter == 1:
                            plurals = ""
                        else:
                            plurals = "s"
                        if len(artistlist) == 1:
                            tag_string_add = f"\n{wk_type.split()[0]} - {posuser_counter} listener{plurals} - {total_plays} plays"
                        else:
                            tag_string_add = f"\n{wk_type} - {len(artistlist)} potential artists - {posuser_counter} listener{plurals} - {total_plays} plays"
                    else:
                        tag_string_add = ""

                    for a in artistlist:
                        try:
                            artistresult = curSS.execute("SELECT artist FROM artistinfo WHERE filtername = ? OR filteralias = ?", (util.compactnamefilter(a,"artist"),util.compactnamefilter(a,"artist")))
                            rtuple = artistresult.fetchone()
                            artist_wo = rtuple[0]
                            artistlist_new.append(artist_wo.lower())
                        except:
                            artistlist_new.append(a.lower())

                    tag_string = str("artist matches: " + ", ".join(sorted(artistlist_new)))
                    if len(tag_string) > 2048-len(tag_string_add):
                        tag_string = tag_string[:2045-len(tag_string_add)] + "..."
                    if posuser_counter > 0:
                        tag_string += tag_string_add
                    embed.set_footer(text=tag_string[:2048])
            except Exception as e:
                print("Error:", e)
        await ctx.send(embed=embed)




    async def first_scrobbler(self, ctx, argument, wk_type):
        # under construction : if argument is user mention or id then fetch from their lastfm

        con = sqlite3.connect('databases/npsettings.db')
        cur = con.cursor()
        lfm_list = [[item[0],item[1],str(item[2]).lower().strip()] for item in cur.execute("SELECT id, lfm_name, details FROM lastfm").fetchall()]

        if wk_type == "artist":
            artist, thumbnail, tags = await self.wk_artist_match(ctx, argument)
            header = f"{artist}"

        elif wk_type == "album":
            artist, album, thumbnail, tags = await self.wk_album_match(ctx, argument)
            header = f"{artist} - {album}"

        elif wk_type == "track":
            artist, track, thumbnail, tags = await self.wk_track_match(ctx, argument)
            header = f"{artist} - {track}"

        else:
            raise ValueError("unknown WK type")

        #conFM = sqlite3.connect('databases/scrobbledata.db')
        #curFM = conFM.cursor()

        conFM2 = sqlite3.connect('databases/scrobbledata_releasewise.db')
        curFM2 = conFM2.cursor()

        conFM3 = sqlite3.connect('databases/scrobbledata_trackwise.db')
        curFM3 = conFM3.cursor()

        # ignore: inactive, wk_banned and scrobble_banned
        # proceed with: NULL, "", crown_banned

        now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())

        discordname_dict = {}
        lfmname_dict = {}
        time_list = []

        server_member_ids = [x.id for x in ctx.guild.members]

        # FILTER BY USER STATUS

        for useritem in lfm_list:
            try:
                user_id = int(useritem[0])
            except Exception as e:
                print("Error:", e)
                continue

            lfm_name = useritem[1]
            status = useritem[2]

            if type(status) == str and (status.startswith(("wk_banned", "scrobble_banned")) or (status.endswith("inactive") and str(ctx.guild.id) == str(os.getenv("guild_id")))):
                continue

            if user_id not in server_member_ids:
                continue

            # check if lfm_name was already added
            if lfm_name in lfmname_dict.keys():
                continue

            lfmname_dict[user_id] = lfm_name

            # GET FIRST TIMESTAMP

            try:
                if wk_type == "artist":
                    result = curFM2.execute(f"SELECT MIN(first_time) FROM [{lfm_name}] WHERE artist_name = ?", (util.compactnamefilter(artist,"artist"),))

                elif wk_type == "album":
                    result = curFM2.execute(f"SELECT first_time FROM [{lfm_name}] WHERE artist_name = ? AND album_name = ?", (util.compactnamefilter(artist,"artist"),util.compactnamefilter(album,"album")))

                elif wk_type == "track":
                    result = curFM3.execute(f"SELECT first_time FROM [{lfm_name}] WHERE artist_name = ? AND track_name = ?", (util.compactnamefilter(artist,"artist"),util.compactnamefilter(track,"track")))

                try:
                    rtuple = result.fetchone()
                    first = int(rtuple[0])

                    if first < 1000000000 or first >= util.year9999():
                        first = None
                except:
                    first = None
                    
            except Exception as e:
                if str(e).startswith("no such table"):
                    pass
                else:
                    print("Error:", e)
                first = None

            if first is None:
                continue
            else:
                time_list.append([user_id, first])

        # FETCH SERVER NAMES

        for member in ctx.guild.members:
            if member.id in lfmname_dict:
                discordname_dict[member.id] = str(member.name)


        # SORT

        time_list.sort(key=lambda x: x[1])

        i = 0
        top = 0
        output_string = ""

        for item in time_list:
            i += 1
            user_id = int(item[0])
            first = int(item[1])

            #if i > 14 and user_id != ctx.author.id:
            #    continue
            if i > 3:
                continue

            top += 1
            output_string += f"{i}. [{discordname_dict[user_id]}](https://www.last.fm/user/{lfmname_dict[user_id]}) - <t:{first}:D>\n"

        if output_string.strip() == "":
            emoji = util.emoji("disappointed")
            output_string = f"no has listened to this {wk_type} {emoji}"

        # EMBED

        header += f" : First {top} in {ctx.guild.name}"
        embed = discord.Embed(title=header[:256], description=output_string[:4096], color=0x800000)
        try:
            embed.set_footer(text=f"{wk_type} - first scrobblers - {i} listeners")
        except:
            pass
        try:
            embed.set_thumbnail(url=thumbnail)
        except:
            pass
        await ctx.send(embed=embed)



    async def artist_detailplays(self, ctx, argument, wk_type):

        # GET USER
        user_id = str(ctx.author.id)

        # under construction: fetch other user

        con = sqlite3.connect('databases/npsettings.db')
        cur = con.cursor()
        lfm_list = [item[0] for item in cur.execute("SELECT lfm_name FROM lastfm WHERE id = ?", (str(user_id),)).fetchall()]
        lfm_name = lfm_list[0].strip()

        artist, thumbnail, tags = await self.wk_artist_match(ctx, argument)
        compact_artist = util.compactnamefilter(artist,"artist")
        artist_aliases_compact = [compact_artist]

        # LOAD ALL SCROBBLES
        conFM = sqlite3.connect('databases/scrobbledata.db')
        curFM = conFM.cursor()

        now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())

        if wk_type == "album":
            conFM2 = sqlite3.connect('databases/scrobbledata_releasewise.db')
            curFM2 = conFM2.cursor()
            result = [[item[0],item[1]] for item in curFM2.execute(f"SELECT album_name, count FROM [{lfm_name}] WHERE artist_name = ? ORDER BY count DESC", (compact_artist,)).fetchall()]

            #under construction: fetch album name from scrobblemeta.db instead

            all_albums = [[item[0],item[1]] for item in curFM.execute(f"SELECT DISTINCT artist_name, album_name FROM [{lfm_name}]").fetchall()]
            filtered_albums = [[util.compactnamefilter(x[1],"album"), x[1]] for x in all_albums if util.compactnamefilter(x[0],"artist") in artist_aliases_compact]
            album_dict = {}
            for key, element in filtered_albums:
                album_dict[key] = element

            result_proper = []
            for item in result:
                album_name = item[0]
                if album_name in album_dict:
                    album_name = util.compactaddendumfilter(album_dict[album_name], "album")
                count = item[1]
                result_proper.append([album_name, count])

        elif wk_type == "track":
            conFM3 = sqlite3.connect('databases/scrobbledata_trackwise.db')
            curFM3 = conFM3.cursor()
            result = [[item[0],item[1]] for item in curFM3.execute(f"SELECT track_name, count FROM [{lfm_name}] WHERE artist_name = ? ORDER BY count DESC", (compact_artist,)).fetchall()]

            all_tracks = [[item[0],item[1]] for item in curFM.execute(f"SELECT DISTINCT artist_name, track_name FROM [{lfm_name}]").fetchall()]
            filtered_tracks = [[util.compactnamefilter(x[1],"track"), x[1]] for x in all_tracks if util.compactnamefilter(x[0],"artist") in artist_aliases_compact]
            track_dict = {}
            for key, element in filtered_tracks:
                track_dict[key] = element

            result_proper = []
            for item in result:
                track_name = item[0]
                if track_name in track_dict:
                    track_name = track_dict[track_name] #util.compactaddendumfilter(track_dict[track_name], "track")
                count = item[1]
                result_proper.append([track_name, count])
        else:
            raise ValueError("unknown WK type")

        ###################### EMBED

        # under construction

        header = f"{artist[:128]} {wk_type} plays"
        header = f"{ctx.author.display_name}"[:253-len(header)] + "'s " + header
        color = ctx.author.color

        contents = [""]
        i = 0 #indexnumber
        k = 0 #pagenumber
        for item in result_proper:
            if item[0].strip() == "":
                continue

            i = i+1
            itemstring = f"`{i}.` **{item[0]}** - *{item[1]} plays*\n"
            
            previous = 0
            for j in range(0,k):
                previous += contents[j].count("\n")

            if len(contents[k]) + len(itemstring) <= 1500 and (i - previous) <= 15:    
                contents[k] = contents[k] + itemstring 
            else:
                k = k+1
                contents.append(itemstring)

        footer = f"{i} {wk_type}s"

        await util.embed_pages(ctx, self.bot, header, contents, color, footer)
        


    async def lastfm_error_handler(self, ctx, e):
        if "'message': '" in str(e):
            try:
                errormessage = str(e).split("'message': '")[1].split("'")[0].strip()
                errorcode = ""
                if "'error': " in str(e):
                    errorcode = "error code: " + str(e).split("'error': ")[1].split("}")[0].strip()
                    if "," in errorcode:
                        errorcode = errorcode.split(",")[0].strip()

                emoji = util.emoji("attention")
                output_string = f"{emoji} **Last.fm error:**\nAPI call got response message:```{errormessage}```{errorcode}"
                embed = discord.Embed(title="", description=output_string[:4096], color=0x800000)
            except Exception as e2:
                print(e2)
                await ctx.send(f"Error: {e}")
        else:
            await ctx.send(f"Error: {e}")
            print(traceback.format_exc())



    async def get_albumcover(self, ctx, artist, album, *track):
        conSM = sqlite3.connect('databases/scrobblemeta.db')
        curSM = conSM.cursor()
        curSM.execute('''CREATE TABLE IF NOT EXISTS albuminfo (artist text, artist_filtername text, album text, album_filtername text, tags text, cover_url text, last_update integer)''')
        albuminfo = [[item[0],item[1],item[2],item[3]] for item in curSM.execute("SELECT artist, album, tags, cover_url FROM albuminfo WHERE artist_filtername = ? AND album_filtername = ?", (util.compactnamefilter(artist,"artist"), util.compactnamefilter(album,"album"))).fetchall()]

        if len(albuminfo) > 0:
            cover_url = albuminfo[0][3]
            if cover_url.strip() != "":
                return cover_url

        # FETCH FROM API

        try:
            if album.strip() != "":
                payload = {
                    'method': 'album.getInfo',
                    'album': album,
                    'artist': artist,
                }
                cooldown = True

                response = await util.lastfm_get(ctx, payload, cooldown)
                if response == "rate limit":
                    print("Error: Rate limit.")
                    return ""

                rjson = response.json()

                artist_name = rjson['album']['artist']
                album_name = rjson['album']['name']
                thumbnail = rjson['album']['image'][-1]['#text']
                tags = []
                try:
                    for tag in rjson['album']['tags']['tag']:
                        try:
                            tagname = tag['name'].lower()
                            tags.append(tagname)
                        except Exception as e:
                            print("Tag error:", e)
                except:
                    pass

            else:
                payload = {
                    'method': 'track.getInfo',
                    'track': track[0],
                    'artist': artist,
                }
                cooldown = True

                response = await util.lastfm_get(ctx, payload, cooldown)
                if response == "rate limit":
                    print("Error: Rate limit.")
                    return ""

                rjson = response.json()
                artist_name = rjson['track']['artist']['name']
                track_name = rjson['track']['name']
                thumbnail = rjson['track']['album']['image'][-1]['#text']

                tags = []
                try:
                    for tag in rjson['track']['toptags']['tag']:
                        try:
                            tagname = tag['name'].lower()
                            tags.append(tagname)
                        except Exception as e:
                            print("Tag error:", e)
                except:
                    pass

            # under construction: insert into scrobblemeta.db

            return thumbnail
        except Exception as e:
            print("Error in get_albumcover():", e)
            return ""



    async def user_plays(self, ctx, argument, wk_type):
        
        # under construction : if argument is user mention or id then fetch from their lastfm
        
        user_id = str(ctx.author.id)

        con = sqlite3.connect('databases/npsettings.db')
        cur = con.cursor()
        lfm_list = [[item[0],str(item[1]).lower().strip()] for item in cur.execute("SELECT lfm_name, details FROM lastfm WHERE id = ?", (user_id,)).fetchall()]

        if len(lfm_list) == 0:
            if user_id == str(ctx.author.id):
                await ctx.reply(f"You haven't set your lastfm account yet.\nUse `{self.prefix}setfm <your username>` to set your account.", mention_author=False)
            else:
                await ctx.reply(f"They haven't set their lastfm account yet.", mention_author=False)
            return

        lfm_name = lfm_list[0][0].strip()

        if wk_type == "artist":
            artist, thumbnail, tags = await self.wk_artist_match(ctx, argument)
            header = f"{artist}"

        elif wk_type == "album":
            try:
                artist, album, thumbnail, tags = await self.wk_album_match(ctx, argument)
                header = f"{artist} - {album}"
            except Exception as e:
                if str(e) == "Could not parse artist and album.":
                    #artistless_albummatch
                    artist = ""
                    thumbnail = ""
                    tags = []
                    album = argument.upper()
                    wk_type = "album without artist"
                    header = f"Album: {album}"
                else:
                    raise ValueError(f"while parsing artist/album - {e}")
                    return

        elif wk_type == "track":
            try:
                artist, track, thumbnail, tags = await self.wk_track_match(ctx, argument)
                header = f"{artist} - {track}"
            except Exception as e:
                if str(e) == "Could not parse artist and track.":
                    #artistless_trackmatch
                    artist = ""
                    thumbnail = ""
                    tags = []
                    track = argument.upper()
                    wk_type = "track without artist"
                    header = f"Track: {track}"
                else:
                    raise ValueError(f"while parsing artist/track - {e}")
                    return
        else:
            raise ValueError("unknown WK type")

        conFM = sqlite3.connect('databases/scrobbledata.db')
        curFM = conFM.cursor()

        conFM2 = sqlite3.connect('databases/scrobbledata_releasewise.db')
        curFM2 = conFM2.cursor()

        conFM3 = sqlite3.connect('databases/scrobbledata_trackwise.db')
        curFM3 = conFM3.cursor()

        now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())
        artistlist = []
        artist_matches = ""

        if wk_type == "artist":
            result = curFM2.execute(f"SELECT SUM(count) FROM [{lfm_name}] WHERE artist_name = ?", (util.compactnamefilter(artist,"artist"),))
            result2 = curFM.execute(f"SELECT COUNT(id) FROM [{lfm_name}] WHERE date_uts > ? AND {util.compact_sql('artist_name')} = {util.compact_sql('?')}", (now - 7*24*60*60, artist))

        elif wk_type == "album":
            result = curFM2.execute(f"SELECT count FROM [{lfm_name}] WHERE artist_name = ? AND album_name = ?", (util.compactnamefilter(artist,"artist"),util.compactnamefilter(album,"album")))
            result2 = curFM.execute(f"SELECT COUNT(id) FROM [{lfm_name}] WHERE date_uts > ? AND {util.compact_sql('artist_name')} = {util.compact_sql('?')} AND {util.compact_sql('album_name')} = {util.compact_sql('?')}", (now - 7*24*60*60, artist, album))

        elif wk_type == "track":
            result = curFM3.execute(f"SELECT count FROM [{lfm_name}] WHERE artist_name = ? AND track_name = ?", (util.compactnamefilter(artist,"artist"),util.compactnamefilter(track,"track")))
            result2 = curFM.execute(f"SELECT COUNT(id) FROM [{lfm_name}] WHERE date_uts > ? AND {util.compact_sql('artist_name')} = {util.compact_sql('?')} AND {util.compact_sql('track_name')} = {util.compact_sql('?')}", (now - 7*24*60*60, artist, track))

        ############ error case feature

        elif wk_type == "album without artist":
            result = curFM2.execute(f"SELECT SUM(count) FROM [{lfm_name}] WHERE album_name = ?", (util.compactnamefilter(album,"album"),))
            result2 = curFM.execute(f"SELECT COUNT(id) FROM [{lfm_name}] WHERE date_uts > ? AND {util.compact_sql('album_name')} = {util.compact_sql('?')}", (now - 7*24*60*60, album))
            try:
                rtuple = result.fetchone()
                count = int(rtuple[0])
            except:
                count = 0
            temp_artist_list = [item[0] for item in curFM2.execute(f"SELECT artist_name FROM [{lfm_name}] WHERE album_name = ?", (util.compactnamefilter(album,"album"),)).fetchall()]  
            for temp_artist in temp_artist_list:
                if temp_artist not in artistlist:
                    artistlist.append(temp_artist)

        elif wk_type == "track without artist":
            result = curFM3.execute(f"SELECT SUM(count) FROM [{lfm_name}] WHERE track_name = ?", (util.compactnamefilter(track,"track"),))
            result2 = curFM.execute(f"SELECT COUNT(id) FROM [{lfm_name}] WHERE date_uts > ? AND {util.compact_sql('track_name')} = {util.compact_sql('?')}", (now - 7*24*60*60, track))
            try:
                rtuple = result.fetchone()
                count = int(rtuple[0])
            except:
                count = 0
            temp_artist_list = [item[0] for item in curFM3.execute(f"SELECT artist_name FROM [{lfm_name}] WHERE track_name = ?", (util.compactnamefilter(track,"track"),)).fetchall()]  
            for temp_artist in temp_artist_list:
                if temp_artist not in artistlist:
                    artistlist.append(temp_artist)

        else:
            result = (None, None)
            print("Error: Unknown WK type")

        ############
        if wk_type in ["artist", "album", "track"]:
            try:
                rtuple = result.fetchone()
                count = int(rtuple[0])
            except Exception as e:
                print(e)
                count = 0
        else:
            pass # artistless aap/atp

        try:
            rtuple2 = result2.fetchone()
            weekcount = int(rtuple2[0])
        except:
            weekcount = 0

        ###################### EMBED

        description = f"**{count}** plays of {header[:256]}\n{weekcount} in the past week"
        try:
            color = ctx.author.color
        except:
            color = 0xFFFFFF

        embed = discord.Embed(title="", description=description[:4096], color=color)
        if wk_type in ["artist", "album", "track"]:
            try:
                embed.set_thumbnail(url=thumbnail)
            except:
                pass
        else:
            try:
                if len(artistlist) > 0:
                    artistlist_new = []
                    conSS = sqlite3.connect('databases/scrobblestats.db')
                    curSS = conSS.cursor()

                    tag_string_add = f"\n{wk_type} - {len(artistlist)} potential artists"

                    for a in artistlist:
                        try:
                            artistresult = curSS.execute("SELECT artist FROM artistinfo WHERE filtername = ? OR filteralias = ?", (util.compactnamefilter(a,"artist"),util.compactnamefilter(a,"artist")))
                            rtuple = artistresult.fetchone()
                            artist_wo = rtuple[0]
                            artistlist_new.append(artist_wo.lower())
                        except:
                            artistlist_new.append(a.lower())
                    tag_string = str("artist matches: " + ", ".join(sorted(artistlist_new)))

                    if len(tag_string) > 2048-len(tag_string_add):
                        tag_string = tag_string[:2045-len(tag_string_add)] + "..."

                    tag_string += tag_string_add
                    embed.set_footer(text=tag_string[:2048])

            except Exception as e:
                print("Error:", e)
        try:
            member = ctx.author
            embed.set_author(name=f"{member.display_name}'s {wk_type.split()[0]} plays" , icon_url=member.avatar)
        except Exception as e:
            print("Error:", e)
        await ctx.send(embed=embed)
        


    ##################################################### COMMANDS #################################################################



    @commands.command(name='u', aliases = ['fmu', 'fmupdate', "scrobbleupdate"])
    @commands.check(ScrobblingCheck.scrobbling_enabled)
    @commands.check(util.is_active)
    async def _scrobble_update(self, ctx: commands.Context, *args):
        """Manually update your scrobbles

        use argument `--force all` to update ALL entries from scratch
        or specify e.g. `--force 2 weeks` to update from a given point some time ago"""

        member = ctx.author

        con = sqlite3.connect('databases/npsettings.db')
        cur = con.cursor()
        lfm_list = [[item[0],item[1],item[2]] for item in cur.execute("SELECT lfm_name, lfm_link, details FROM lastfm WHERE id = ?", (str(member.id),)).fetchall()]

        if len(lfm_list) == 0:
            await ctx.send(f"You haven't set your lastfm user account yet.\nUse `{self.prefix}setfm <your username>` to do that.")
            return

        lfm_name = lfm_list[0][0]
        argument = ' '.join(args)
        status = lfm_list[0][2]

        if type(status) == str and status.startswith("scrobble_banned"):
            await ctx.reply(f"You are unfortunately scrobble banned.")
            return

        # check if update is currently running 
        cooldown_list = util.check_active_scrobbleupdate()
        if len(cooldown_list) > 0:
            print("Skipping scrobble auto-update. Update pipe in use:", cooldown_list)
            usernames = []
            for item in cooldown_list:
                usernames.append(item[1])
            usernamestring = ', '.join(usernames)
            await ctx.send(f"Update pipe is currently in use ({usernamestring}). Please try again later.")
            return

        util.block_scrobbleupdate(ctx)

        async with ctx.typing():
            try:
                message, count = await self.fetch_scrobbles(ctx, lfm_name, argument)

            except Exception as e:
                util.unblock_scrobbleupdate()
                print("Error:", e)
                await ctx.send(f"Error: {e}")
                print(traceback.format_exc())
                return

            loadingbar = util.get_loadingbar(self.loadingbar_width, 100)
            if count == 0:
                new_embed = discord.Embed(title="", description=f"No new scrobbles to add to database.\n\n{loadingbar} 100%", color=0x00A36C)
            else:
                emoji = util.emoji("yay")
                if count == 1:
                    new_embed = discord.Embed(title="", description=f"Done! Updated {count} entry. {emoji}\n\n{loadingbar} 100%", color=0x00A36C)
                else:
                    new_embed = discord.Embed(title="", description=f"Done! Updated {count} entries. {emoji}\n\n{loadingbar} 100%", color=0x00A36C)

        if count >= 200:
            await self.run_scrobbledata_sanitycheck(lfm_name, 0)
        await message.edit(embed=new_embed)
        util.unblock_scrobbleupdate()

    @_scrobble_update.error
    async def scrobble_update_error(self, ctx, error):
        await util.error_handling(ctx, error) 



    @commands.command(name='reloadrwdb', aliases = ["reloadreleasewisedb"])
    @commands.has_permissions(manage_guild=True)
    @commands.check(ScrobblingCheck.scrobbling_enabled)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _fullyreload_releasewise_database(self, ctx: commands.Context, *args):
        """🔒 reload releasewise database for lfm scrobbles

        this command may block all other bot activity

        use with arg `full` to also re-index entries in scrobbledata.db"""

        if len(args) > 0 and args[0].lower() == "full":
            reindex = True
        else:
            reindex = False

        async with ctx.typing():
            await ctx.send("Warning: Bot functionality might be blocked until finished.")

            cooldown_list = util.check_active_scrobbleupdate()
            if len(cooldown_list) > 0:
                print("Skipping scrobble auto-update. Update pipe in use:", cooldown_list)
                usernames = []
                for item in cooldown_list:
                    usernames.append(item[1])
                usernamestring = ', '.join(usernames)
                await ctx.send(f"Update pipe is currently in use ({usernamestring}). Please try again later.")
                return

            util.block_scrobbleupdate("mod action")

            try:
                i = await self.reload_releasewise_database(reindex)
                await ctx.send(f"Done! {i} items were (re)loaded from the scrobble database.")
            except Exception as e:
                util.unblock_scrobbleupdate()
                await ctx.send(f"Error: {e}")

            util.unblock_scrobbleupdate()

    @_fullyreload_releasewise_database.error
    async def fullyreload_releasewise_database_error(self, ctx, error):
        await util.error_handling(ctx, error) 



    @commands.command(name='wk', aliases = ["w", "whoknows", "whoknowsartist"])
    @commands.check(ScrobblingCheck.scrobbling_enabled)
    @commands.check(util.is_active)
    async def _whoknowsartist(self, ctx: commands.Context, *args):
        """List of users with most scrobbles of said artist"""

        try:
            async with ctx.typing():
                argument = ' '.join(args)
                await self.whoknows(ctx, argument, "artist")
        except Exception as e:
            await self.lastfm_error_handler(ctx, e)

    @_whoknowsartist.error
    async def whoknowsartist_error(self, ctx, error):
        await util.error_handling(ctx, error) 



    @commands.command(name='wka', aliases = ["whoknowsalbum", "wa"])
    @commands.check(ScrobblingCheck.scrobbling_enabled)
    @commands.check(util.is_active)
    async def _whoknowsalbum(self, ctx: commands.Context, *args):
        """List of users with most scrobbles of said artist"""

        try:
            async with ctx.typing():
                argument = ' '.join(args)
                await self.whoknows(ctx, argument, "album")
        except Exception as e:
            await self.lastfm_error_handler(ctx, e)

    @_whoknowsalbum.error
    async def whoknowsalbum_error(self, ctx, error):
        await util.error_handling(ctx, error) 



    @commands.command(name='wkt', aliases = ["whoknowstrack", "wt"])
    @commands.check(ScrobblingCheck.scrobbling_enabled)
    @commands.check(util.is_active)
    async def _whoknowstrack(self, ctx: commands.Context, *args):
        """List of users with most scrobbles of said artist"""

        try:
            async with ctx.typing():
                argument = ' '.join(args)
                await self.whoknows(ctx, argument, "track")
        except Exception as e:
            await self.lastfm_error_handler(ctx, e)

    @_whoknowstrack.error
    async def whoknowstrack_error(self, ctx, error):
        await util.error_handling(ctx, error) 



    @commands.command(name='fwk', aliases = ["firstartist", "first", 'fw'])
    @commands.check(ScrobblingCheck.scrobbling_enabled)
    @commands.check(util.is_active)
    async def _firstartist(self, ctx: commands.Context, *args):
        """List of users who scrobbled this artist the earliest"""

        try:
            async with ctx.typing():
                argument = ' '.join(args)
                await self.first_scrobbler(ctx, argument, "artist")
        except Exception as e:
            await self.lastfm_error_handler(ctx, e)

    @_firstartist.error
    async def firstartist_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='fwka', aliases = ['firstalbum', 'fwa'])
    @commands.check(ScrobblingCheck.scrobbling_enabled)
    @commands.check(util.is_active)
    async def _firstalbum(self, ctx: commands.Context, *args):
        """List of users who scrobbled this album the earliest"""

        try:
            async with ctx.typing():
                argument = ' '.join(args)
                await self.first_scrobbler(ctx, argument, "album")
        except Exception as e:
            await self.lastfm_error_handler(ctx, e)

    @_firstalbum.error
    async def firstalbum_error(self, ctx, error):
        await util.error_handling(ctx, error) 



    @commands.command(name='fwkt', aliases = ["firsttrack", 'fwt'])
    @commands.check(ScrobblingCheck.scrobbling_enabled)
    @commands.check(util.is_active)
    async def _firsttrack(self, ctx: commands.Context, *args):
        """List of users who scrobbled this track the earliest"""

        try:
            async with ctx.typing():
                argument = ' '.join(args)
                await self.first_scrobbler(ctx, argument, "track")
        except Exception as e:
            await self.lastfm_error_handler(ctx, e)

    @_firsttrack.error
    async def firsttrack_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='crowns', aliases = ["crown"])
    @commands.check(ScrobblingCheck.scrobbling_enabled)
    @commands.check(util.is_active)
    async def _crowns(self, ctx: commands.Context, *args):
        """Shows crowns of user

        You can also put a user id or mention as first argument to show their crowns.
        """

        # FETCH USER ID
        user_id = str(ctx.author.id)
        color = 0x9d2933

        if len(args) > 0:
            try:
                object_id, rest = await util.fetch_id_from_args("user", "first", args)
                if util.represents_integer(object_id) and len(object_id) > 15:
                    user_id = str(object_id)
            except:
                pass

        # FETCH LASTFM NAME

        conNP = sqlite3.connect('databases/npsettings.db')
        curNP = conNP.cursor()

        try:
            result = curNP.execute("SELECT lfm_name FROM lastfm WHERE id = ?", (user_id,))
            lfm_name = result.fetchone()[0]
        except Exception as e:
            print(e)
            text = f"Error: Could not find lastfm user name of <@{user_id}>."
            embed = discord.Embed(title="", description=text, color=0x000000)
            await ctx.send(embed=embed)
            return

        # FETCH CROWNS

        conSS = sqlite3.connect('databases/scrobblestats.db')
        curSS = conSS.cursor()
        crowns_list = [[item[0],util.forceinteger(item[1])] for item in curSS.execute(f"SELECT artist, playcount FROM crowns_{str(ctx.guild.id)} WHERE crown_holder = ?", (lfm_name,)).fetchall()]
        crowns_list.sort(key=lambda x: x[1], reverse = True)
        num_crowns = len(crowns_list)

        # CREATE STRING LIST

        emoji = util.emoji("crown")
        header = f"{emoji} crowns of {lfm_name} on {ctx.guild.name}"
        footer = f"{num_crowns} crowns in total"

        contents = [""]
        i = 0 #indexnumber
        j = 0 #item on this page
        k = 0 #pagenumber
        for item in crowns_list:
            i += 1
            j += 1
            artist = item[0].strip()[:100]
            playcount = item[1]
            crowninfo = f"`{i}.` {artist} - **{playcount}** plays"

            if j <= 15:    
                contents[k] = contents[k] + "\n" + crowninfo 
            else:
                k = k+1
                j = 0
                contents.append(crowninfo)

        # SEND EMBED MESSAGE

        await util.embed_pages(ctx, self.bot, header[:256], contents, color, footer)

    @_crowns.error
    async def crowns_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='servercrowns', aliases = ["servercrown", "crownleaderboard"])
    @commands.check(ScrobblingCheck.scrobbling_enabled)
    @commands.check(util.is_active)
    async def _servercrowns(self, ctx: commands.Context, *args):
        """Shows leaderboard of crowns per user
        """

        # FETCH LASTFM NAMES

        conNP = sqlite3.connect('databases/npsettings.db')
        curNP = conNP.cursor()
        name_list = [[item[0],item[1]] for item in curNP.execute("SELECT id, lfm_name FROM lastfm WHERE details = ? OR details = ?", ("", None)).fetchall()]
        lfm_dict = {}

        for item in name_list:
            user_id = item[0]
            lfm_name = item[1]

            if user_id in lfm_dict:
                continue

            lfm_dict[user_id] = lfm_name

        servermembers = []
        crowns_list = []
        discord_dict = {}

        for member in ctx.guild.members:
            # is_inactive = await self.check_for_inactivity_role(str(member.id), only)
            if str(member.id) in lfm_dict:
                servermembers.append(str(member.id))
                discord_dict[str(member.id)] = str(member.name)


        # FETCH CROWN NUMBER

        conSS = sqlite3.connect('databases/scrobblestats.db')
        curSS = conSS.cursor()

        for user_id in servermembers:
            try:
                lfm_name = lfm_dict[user_id]
                result = curSS.execute(f"SELECT COUNT(artist) FROM crowns_{str(ctx.guild.id)} WHERE crown_holder = ?", (lfm_name,))
                num_crowns = int(result.fetchone()[0])

                crowns_list.append([user_id, lfm_name, num_crowns])
            except Exception as e:
                print("Error:", e)
                continue

        crowns_list.sort(key=lambda x: x[2], reverse = True)

        # CREATE STRING LIST

        emoji = util.emoji("crown")
        header = f"{emoji} crowns on {ctx.guild.name}"
        crowns_total = 0

        contents = [""]
        i = 0 #indexnumber
        j = 0 #item on this page
        k = 0 #pagenumber
        for item in crowns_list:
            user_id = item[0]
            discord_name = discord_dict[user_id]
            lfm_name = item[1]
            num_crowns = item[2]

            if num_crowns <= 0:
                continue
            i += 1
            j += 1
            crowninfo = f"`{i}.` [{discord_name}](https://www.last.fm/user/{lfm_name}) - **{num_crowns}** crowns"

            crowns_total += num_crowns

            if j <= 15:    
                contents[k] = contents[k] + "\n" + crowninfo 
            else:
                k = k+1
                j = 0
                contents.append(crowninfo)

        footer = f"{crowns_total} crowns in total"
        color = 0x9d2933

        # SEND EMBED MESSAGE

        await util.embed_pages(ctx, self.bot, header[:256], contents, color, footer)

    @_servercrowns.error
    async def servercrowns_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='chart', aliases = ["c"])
    @commands.check(ScrobblingCheck.scrobbling_enabled)
    @commands.check(util.is_active)
    async def _chart(self, ctx: commands.Context, *args):
        """Shows chart of recent music
        
        under construction:
        specify size...
        specify timeframe...
        """

        await ctx.send("Under construction")

    @_chart.error
    async def chart_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='ms', aliases = ["milestone", "scrobble"])
    @commands.check(ScrobblingCheck.scrobbling_enabled)
    @commands.check(util.is_active)
    async def _milestone(self, ctx: commands.Context, *args):
        """Shows scrobble/milestone

        Use without argument to show last milestone.
        Use with index argument `<n>` to get n-th scrobble.
        Use arg `last` to get last scrobble.
        Use arg `rand` to get random scrobble.
        """
        user_id = str(ctx.author.id)
        color = 0x9d2933
        index_int = 0

        if len(args) == 0:
            index_number = "last_ms"
        elif args[0].lower() == "last":
            index_number = "last"
        elif args[0].lower() in ["rand", "rando", "random"]:
            index_number = "random"
        else:
            index_number = args[0]
            if util.represents_integer:
                index_int = int(index_number)
                if index_int < 1:
                    index_int = 1
            else:
                index_number = "last_ms"

        # FETCH LASTFM NAME

        conNP = sqlite3.connect('databases/npsettings.db')
        curNP = conNP.cursor()

        try:
            result = curNP.execute("SELECT lfm_name FROM lastfm WHERE id = ?", (user_id,))
            lfm_name = result.fetchone()[0]
        except Exception as e:
            print(e)
            await ctx.send(f"Error: Could not find your lastfm username. {emoji}\nUse `{self.prefix}setfm` to set your username first, and then use `{self.prefix}u` to load your scrobbles into the bot's database.")
            return

        # FETCH MILESTONE

        conFM = sqlite3.connect('databases/scrobbledata.db')
        curFM = conFM.cursor()

        scrobbles = [[item[0],item[1],item[2],item[3]] for item in curFM.execute(f"SELECT artist_name, album_name, track_name, date_uts FROM [{lfm_name}] ORDER BY date_uts ASC").fetchall()]
        
        if len(scrobbles) == 0:
            await ctx.send("You haven't imported any of your scrobbles.")
            return

        footer = ""
        if index_number == "last_ms":
            milestone_list = [1]
            for x in [1,2,3,4,5,6,7,8,9]:
                for y in [1,2,3,4,5,6,7,8,9]:
                    milestone = (10 ** x) * y
                    milestone_list.append(milestone)
                    if x == 5:
                        milestone += (10 ** (x-1)) * 5
                        milestone_list.append(milestone)
                    if x > 5:
                        for z in range(9):
                            milestone += (10 ** (x-1)) * z
                            milestone_list.append(milestone)
            index_int = 1
            for i in milestone_list:
                if i <= len(scrobbles):
                    index_int = i
                else:
                    break
        elif index_number == "random":
            index_int = random.randint(1, len(scrobbles))

        elif index_number == "last" or index_int > len(scrobbles):
            index_int = len(scrobbles)
            if index_int > len(scrobbles):
                footer = f"{len(scrobbles)}? you don't have that many scrobbles... yet"

        item = scrobbles[index_int - 1]

        artist = item[0]
        album = item[1]
        track = item[2]
        uts = item[3]

        text = f"**{track}**\nby {artist}"
        if album.strip() != "":
            text += f" | {album}"

        text += f"\n\nPlayed at <t:{uts}:f>"

        embed = discord.Embed(title="", description=text, color=ctx.author.color)

        try:
            embed.set_author(name=f"{ctx.author.name}'s scrobble no. {index_int}", icon_url=ctx.author.avatar)
        except Exception as e:
            print("Error:", e)

        try:
            albumart = await self.get_albumcover(ctx, artist, album, track)
            embed.set_thumbnail(url=albumart)
        except Exception as e:
            print("Error:", e)

        if footer.strip() != "":
            embed.set_footer(text=footer.strip())

        await ctx.send(embed=embed)

    @_milestone.error
    async def milestone_error(self, ctx, error):
        await util.error_handling(ctx, error) 


    
    @commands.command(name='stats', aliases = ["stat"])
    @commands.check(ScrobblingCheck.scrobbling_enabled)
    @commands.check(util.is_active)
    async def _stats(self, ctx: commands.Context, *args):
        """Shows lastfm stats
        """

        await ctx.send("Under construction")

    @_stats.error
    async def stats_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='streak', aliases = ["str"])
    @commands.check(ScrobblingCheck.scrobbling_enabled)
    @commands.check(util.is_active)
    async def _streak(self, ctx: commands.Context, *args):
        """Shows current lastfm streak
        """

        await ctx.send("Under construction")

    @_streak.error
    async def streak_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='pace', aliases = ["pc"])
    @commands.check(ScrobblingCheck.scrobbling_enabled)
    @commands.check(util.is_active)
    async def _pace(self, ctx: commands.Context, *args):
        """Shows lastfm pace
        """

        await ctx.send("Under construction")

    @_pace.error
    async def pace_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='aa', aliases = ["artistalbums"])
    @commands.check(ScrobblingCheck.scrobbling_enabled)
    @commands.check(util.is_active)
    async def _artistalbums(self, ctx: commands.Context, *args):
        """
        Shows the top albums by plays of a given artist
        """

        try:
            async with ctx.typing():
                argument = ' '.join(args)
                await self.artist_detailplays(ctx, argument, "album")
        except Exception as e:
            await self.lastfm_error_handler(ctx, e)

    @_artistalbums.error
    async def artistalbums_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='at', aliases = ["artisttracks"])
    @commands.check(ScrobblingCheck.scrobbling_enabled)
    @commands.check(util.is_active)
    async def _artisttracks(self, ctx: commands.Context, *args):
        """
        Shows the top tracks by plays of a given artist
        """

        try:
            async with ctx.typing():
                argument = ' '.join(args)
                await self.artist_detailplays(ctx, argument, "track")
        except Exception as e:
            await self.lastfm_error_handler(ctx, e)

    @_artisttracks.error
    async def artisttracks_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='ap', aliases = ["artistplays"])
    @commands.check(ScrobblingCheck.scrobbling_enabled)
    @commands.check(util.is_active)
    async def _artistplays(self, ctx: commands.Context, *args):
        """
        """
        argument = ' '.join(args)
        wk_type = "artist"
        await self.user_plays(ctx, argument, wk_type)

    @_artistplays.error
    async def artistplays_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='aap', aliases = ["albumplays", 'alp'])
    @commands.check(ScrobblingCheck.scrobbling_enabled)
    @commands.check(util.is_active)
    async def _albumplays(self, ctx: commands.Context, *args):
        """
        """
        argument = ' '.join(args)
        wk_type = "album"
        await self.user_plays(ctx, argument, wk_type)

    @_albumplays.error
    async def albumplays_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='atp', aliases = ["trackplays","tp"])
    @commands.check(ScrobblingCheck.scrobbling_enabled)
    @commands.check(util.is_active)
    async def _trackplays(self, ctx: commands.Context, *args):
        """
        """
        argument = ' '.join(args)
        wk_type = "track"
        await self.user_plays(ctx, argument, wk_type)

    @_trackplays.error
    async def trackplays_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='ai', aliases = ["artistinfo"])
    @commands.check(ScrobblingCheck.scrobbling_enabled)
    @commands.check(util.is_active)
    async def _artistinfo(self, ctx: commands.Context, *args):
        """
        """

        await ctx.send("Under construction")

    @_artistinfo.error
    async def artistinfo_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='from', aliases = ["fromcountry"])
    @commands.check(ScrobblingCheck.scrobbling_enabled)
    @commands.check(util.is_active)
    async def _fromcountry(self, ctx: commands.Context, *args):
        """
        """

        await ctx.send("Under construction")

    @_fromcountry.error
    async def fromcountry_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='g', aliases = ["genres"])
    @commands.check(ScrobblingCheck.scrobbling_enabled)
    @commands.check(util.is_active)
    async def _usergenres(self, ctx: commands.Context, *args):
        """
        """

        await ctx.send("Under construction")

    @_usergenres.error
    async def usergenres_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='ga', aliases = ["genreartist", "genreartists"])
    @commands.check(ScrobblingCheck.scrobbling_enabled)
    @commands.check(util.is_active)
    async def _genreartists(self, ctx: commands.Context, *args):
        """
        """

        await ctx.send("Under construction")

    @_genreartists.error
    async def genreartists_error(self, ctx, error):
        await util.error_handling(ctx, error)




    ####################################################### mod commands



    async def check_for_inactivity_role(self, user_id, only):
        try:
            user, color, rest_list = await util.fetch_member_and_color(ctx, str(user_id).strip())
            conB = sqlite3.connect('databases/botsettings.db')
            curB = conB.cursor()

            # FETCH ROLE

            inactivityrole_list = [item[0] for item in curB.execute("SELECT role_id FROM specialroles WHERE name = ?", ("inactivity role",)).fetchall()]        
            if len(inactivityrole_list) == 0 or not util.represents_integer(inactivityrole_list[0]):
                return False
            else:
                if len(inactivityrole_list) > 1:
                    print("Warning: there are multiple inactivity role entries in the database")
                inactivity_role_id = int(inactivityrole_list[0])

            try:
                inactivity_role = ctx.guild.get_role(inactivity_role_id)
            except Exception as e:
                print("Error with inactivity role id:", e)
                return False

            if inactivity_role is None:
                print("Error with inactivity role", e)
                return False

            # CHECK IF USER HAS ROLE

            if inactivity_role in user.roles:
                if only:
                    # check if that's the only role
                    if len(user.roles) <= 2:
                        return True
                    else:
                        return False
                else:
                    return True

            return False

        except Exception as e:
            print("check_for_inactivity_role() error", e)
            return False



    async def remove_all_crowns(self, ctx, bot, user_id):
        await ctx.send("under construction")
        # under construction




    @commands.command(name='crownban', aliases = ["cwban"])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(ScrobblingCheck.scrobbling_enabled)
    @commands.check(util.is_active)
    async def _crownban(self, ctx: commands.Context, *args):
        """🔒 ban user from gaining crowns

        Crownbanned users are not able to participate in the crown game.
        Use command with arg `user id`.

        If you want to also remove existing crowns of that user use command `-crownremove` next.
        """

        user_ids, rest = await util.fetch_id_from_args("user", "multiple", remainder_args)
        user_list = user_ids.split(";")

        if len(user_list) == 0:
            await ctx.send("Command needs user arguments!")
            return

        conNP = sqlite3.connect('databases/npsettings.db')
        curNP = conNP.cursor()
        lfm_list = [[item[0],item[1],item[2]] for item in curNP.execute("SELECT id, lfm_name, details FROM lastfm").fetchall()]

        lfm_ids = [item[0].strip() for item in lfm_list]

        # CHECK USERS

        for user_id in user_list:
            if user_id.strip() not in lfm_ids:
                text = f"user <@{user_id}> not found in database"
                embed = discord.Embed(title="", description=text, color=0x000000)
                await ctx.send(embed=embed)
                continue

            try:
                # CROWN BAN USERS

                only = False
                is_inactive = await self.check_for_inactivity_role(user_id.strip(), only)

                if is_inactive:
                    curNP.execute("UPDATE lastfm SET details = ? WHERE id = ?", ("crown_banned_inactive", user_id.strip()))
                else:
                    curNP.execute("UPDATE lastfm SET details = ? WHERE id = ?", ("crown_banned", user_id.strip()))
                conNP.commit()

                emoji = util.emoji("ban")
                text = f"Crown banned <@{user_id}>. {emoji}"
                embed = discord.Embed(title="", description=text, color=0xff0000)
                await ctx.send(embed=embed)

            except Exception as e:
                text = f"Error while trying to crown ban <@{user_id}>: {e}"
                embed = discord.Embed(title="", description=text, color=0xffff00)
                await ctx.send(embed=embed)
        
        await util.changetimeupdate()

    @_crownban.error
    async def crownban_error(self, ctx, error):
        await util.error_handling(ctx, error) 



    @commands.command(name='crownremove', aliases = ["cwremove"])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(ScrobblingCheck.scrobbling_enabled)
    @commands.check(util.is_active)
    async def _crownremove(self, ctx: commands.Context, *args):
        """🔒 remove crowns from a user

        Remove crowns from user via their last_fm name.

        Use command with argument `all` to remove all crowns on this bot."""

        if len(args) == 0:
            await ctx.send(f"Error: Command needs argument.")
            return

        if len(args) == 1 and args[0].lower() == "all":
            conSS = sqlite3.connect('databases/scrobblestats.db')
            curSS = conSS.cursor()
            successes = 0
            serverlist = []
            for guild in self.bot.guilds:
                try:
                    curSS.execute(f'''CREATE TABLE IF NOT EXISTS crowns_{guild.id} (artist text, alias text, alias2 text, crown_holder text, discord_name text, playcount integer)''')
                    scrobblestats = [item for item in curSS.execute(f"SELECT * FROM crowns_{guild.id}").fetchall()]
                    if len(scrobblestats) == 0:
                        continue

                    curSS.execute(f"DELETE FROM crowns_{guild.id}")
                    conSS.commit()
                    successes += 1
                    serverlist.append(str(guild.name))
                except Exception as e:
                    await ctx.send(f"Error while trying to remove all crowns from {guild.name}: {e}")

            if successes > 0:
                serverstring = ', '.join(serverlist)
                emoji = util.emoji("unleashed")
                await cts.send(f"Successfully removed all crowns from {successes} servers. {emoji}\nServers: {serverstring}")
            else:
                emoji = util.emoji("disappointed")
                await cts.send(f"Couldn't remove any crowns. {emoji}")
            return

        for arg in args:
            lfm_name = arg.replace("\\","")
            try:
                await self.remove_all_crowns(ctx, self.bot, lfm_name)
            except Exception as e:
                await ctx.send(f"Failed to remove user {lfm_name} crowns: {e}\n\nTry again later.")

    @_crownremove.error
    async def crownremove_error(self, ctx, error):
        await util.error_handling(ctx, error) 



    @commands.command(name='crownunban', aliases = ["cwunban"])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(ScrobblingCheck.scrobbling_enabled)
    @commands.check(util.is_active)
    async def _crownunban(self, ctx: commands.Context, *args):
        """🔒 unban user from gaining crowns

        Crownbanned users are not able to participate in the crown game."""

        user_ids, rest = await util.fetch_id_from_args("user", "multiple", remainder_args)
        user_list = user_ids.split(";")

        if len(user_list) == 0:
            await ctx.send("Command needs user arguments!")
            return

        conNP = sqlite3.connect('databases/npsettings.db')
        curNP = conNP.cursor()
        lfm_list = [[item[0],item[1],item[2]] for item in curNP.execute("SELECT id, lfm_name, details FROM lastfm").fetchall()]

        lfm_ids = [item[0].strip() for item in lfm_list]

        for user_id in user_list:
            if user_id.strip() not in lfm_ids:
                text = f"user <@{user_id}> not found in database"
                embed = discord.Embed(title="", description=text, color=0x000000)
                await ctx.send(embed=embed)
                continue
            else:
                status = None
                for item in lfm_list:
                    if item[0].strip() == user_id.strip():
                        status = item[2]
                        break

                if type(status) == str and status.strip().lower() not in ['crown_banned', 'crown_banned_inactive']:
                    text = f"user <@{user_id}> is not crown banned. No action taken."
                    embed = discord.Embed(title="", description=text, color=0x000000)
                    await ctx.send(embed=embed)
                    continue

            try:
                only = False
                is_inactive = await self.check_for_inactivity_role(user_id, only)

                if is_inactive:
                    curNP.execute("UPDATE lastfm SET details = ? WHERE id = ?", ("inactive", user_id.strip()))
                else:
                    curNP.execute("UPDATE lastfm SET details = ? WHERE id = ?", ("", user_id.strip()))
                conNP.commit()

                emoji = util.emoji("thumbs_up")
                text = f"Crown unbanned <@{user_id}>. {emoji}\nIf this user previously had crowns, they would have to reclaim them again."
                embed = discord.Embed(title="", description=text, color=0xff0000)
                await ctx.send(embed=embed)

            except Exception as e:
                text = f"Error while trying to crown unban <@{user_id}>: {e}"
                embed = discord.Embed(title="", description=text, color=0xffff00)
                await ctx.send(embed=embed)
        
        await util.changetimeupdate()

    @_crownunban.error
    async def crownunban_error(self, ctx, error):
        await util.error_handling(ctx, error) 



    @commands.command(name='wkban', aliases = ["whoknowsban"])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(ScrobblingCheck.scrobbling_enabled)
    @commands.check(util.is_active)
    async def _whoknowsban(self, ctx: commands.Context, *args):
        """🔒 ban user from being displayed on whoknows lists

        """

        await ctx.send(f"Under construction.")
        #under construction

        # remove all crowns

    @_whoknowsban.error
    async def whoknowsban_error(self, ctx, error):
        await util.error_handling(ctx, error) 



    @commands.command(name='wkunban', aliases = ["whoknowsunban"])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(ScrobblingCheck.scrobbling_enabled)
    @commands.check(util.is_active)
    async def _whoknowsunban(self, ctx: commands.Context, *args):
        """🔒 ban user from being displayed on whoknows lists

        """

        await ctx.send(f"Under construction.")
        #under construction

    @_whoknowsunban.error
    async def whoknowsunban_error(self, ctx, error):
        await util.error_handling(ctx, error) 



    @commands.command(name='scban', aliases = ["scrobbleban"])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(ScrobblingCheck.scrobbling_enabled)
    @commands.check(util.is_active)
    async def _scrobbleban(self, ctx: commands.Context, *args):
        """🔒 ban user from having their scrobbles saved in local database

        """

        await ctx.send(f"Under construction.")
        #under construction

        # remove all crowns

    @_scrobbleban.error
    async def scrobbleban_error(self, ctx, error):
        await util.error_handling(ctx, error) 



    @commands.command(name='scunban', aliases = ["scrobbleunban"])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(ScrobblingCheck.scrobbling_enabled)
    @commands.check(util.is_active)
    async def _scrobbleunban(self, ctx: commands.Context, *args):
        """🔒 unban user from having their scrobbles saved in local database

        """

        await ctx.send(f"Under construction.")
        #under construction

    @_scrobbleunban.error
    async def scrobbleunban_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='crownseed')
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(ScrobblingCheck.scrobbling_enabled)
    @commands.check(util.is_active)
    async def _crownseed(self, ctx: commands.Context, *args):
        """🔒 seeds crowns to server members
        """

        await ctx.send(f"Under construction.")
                
    @_crownseed.error
    async def crownseed_error(self, ctx, error):
        await util.error_handling(ctx, error)



    #@commands.command(name='scrobblefilter')
    #@commands.has_permissions(manage_guild=True)
    #@commands.check(util.is_main_server)
    #@commands.check(ScrobblingCheck.scrobbling_enabled)
    #@commands.check(util.is_active)
    #async def _scrobblefilter(self, ctx: commands.Context, *args):
    #    """🔒 filters out double scrobbles and re-indexes entries

    #    command has some issues. for one, spotify caches plays and sends them in bulks, so if people genuinely listen to the same track repeatedly it might show as double scrobble regardless.
    #    """

    #    lfm_name = ' '.join(args)
    #    len_before, len_after, sus = await self.run_scrobbledata_sanitycheck(lfm_name, 0)

    #    text = f"Filtered and re-indexed scrobbles of {lfm_name}."
    #    if (len_before != len_after):
    #        text += f"\nCount was reduced from {len_before} to {len_after}. (Diff: {len_before - len_after})"
    #    else:
    #        text += f"\nCount remains unchanged. (Diff: 0)"

    #    if sus > 0:
    #        emoji = util.emoji("think")
    #        text += f"\n\n(Furthermore, {sus} many scrobbles that happened at the same second. So many Napalm Death type cases? {emoji})"
    #    await ctx.send(text)

    #@_scrobblefilter.error
    #async def scrobblefilter_error(self, ctx, error):
    #    await util.error_handling(ctx, error)



async def setup(bot: commands.bot) -> None:
    await bot.add_cog(
        Music_Scrobbling(bot),
        guilds = [discord.Object(id = int(os.getenv("guild_id")))])