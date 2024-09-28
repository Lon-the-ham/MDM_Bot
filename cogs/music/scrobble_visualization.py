import discord
from discord.ext import commands
import datetime
from other.utils.utils import Utils as util
import os
import sys
import asyncio
import sqlite3
import functools
import typing
import traceback

import pandas as pd 

try:
    import bar_chart_race as bcr
    barchartrace_enabled = True
except:
    print("Not importing bar chart race library")
    barchartrace_enabled = False




class ScrobbleVisualsCheck():
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

    def is_barchartrace_enabled(*ctx):
        if barchartrace_enabled:
            return True
        else:
            return False

    ### CHECK BLOCK UNBLOCK

    def check_active_gfx_generation(service):
        conC = sqlite3.connect('databases/cooldowns.db')
        curC = conC.cursor()
        cooldown_list = [[item[0],item[1],item[2],item[3]] for item in curC.execute("SELECT service, userid, username, time_stamp FROM gfx_generation WHERE service = ?", (str(service),)).fetchall()]
        return cooldown_list

    def block_gfx_generation(ctx, service):
        now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())

        if ctx is None:
            userid = "?"
            username = "?"
        else:
            userid = ctx.author.id
            username = ctx.author.name

        conC = sqlite3.connect('databases/cooldowns.db')
        curC = conC.cursor()
        curC.execute("INSERT INTO gfx_generation VALUES (?, ?, ?, ?)", (str(service), str(userid), str(username), str(now)))
        conC.commit()

    def unblock_gfx_generation(service):
        conC = sqlite3.connect('databases/cooldowns.db')
        curC = conC.cursor()
        curC.execute("DELETE FROM gfx_generation WHERE service = ?", (str(service),))
        conC.commit()



class Music_Scrobbling_Visuals(commands.Cog):
    def __init__(self, bot: commands.bot) -> None:
        self.bot = bot
        self.prefix = os.getenv("prefix")
        self.tagseparator = " ‧ "
        self.loadingbar_width = 16



    def to_thread(func: typing.Callable) -> typing.Coroutine:
        """wrapper for blocking functions"""
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await asyncio.to_thread(func, *args, **kwargs)
        return wrapper



    ###################################################################################



    def get_timecut_seconds(self, now, arg):
        if arg in ["weekly", "week", "w"]:
            result = now - 7 * 24 * 3600
        elif arg in ["monthly", "month", "m"]:
            result = now - 30 * 24 * 3600
        elif arg in ["quarterly", "quarter", "q"]:
            result = now - 90 * 24 * 3600
        elif arg in ["semester", "semi", "halfyearly", "halfyear", "half", "h"]:
            result = now - 180 * 24 * 3600
        elif arg in ["yearly", "year", "y"]:
            result = now - 365 * 24 * 3600
        elif arg in ["all", "a", "alltime"]:
            result = 0
        else:
            result = -1

        return result



    async def parse_barchartrace_args(self, args):
        now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())

        arg_dict = {
            "timecut": 0,
            "top": 10,
            "steps": 60,    
            "scope": "user",
        }

        arguments = []
        args_intermediate = ' '.join(args).replace(";",",").split(",")
        for arg in args_intermediate:
            arguments.append(''.join([x for x in arg.lower() if x.isalnum()]).strip())

            arg_strip = arg.strip()
            if arg_strip.startswith("<@") and arg_strip.endswith(">") and len(arg_strip) >= 19:
                if util.represents_integer(arg_strip[2:-1]):
                    arg_dict["scope"] = arg_strip[2:-1]

        min_bars = 1
        max_bars = 50
        min_steps = 7
        max_steps = 500

        for arg in arguments:
            if arg.startswith("bars") and len(arg) > 4:
                val = util.forceinteger(arg[4:])
                if val >= min_bars and val <= max_bars:
                    arg_dict["top"] = val
                elif arg[4:] == "max":
                    arg_dict["top"] = max_bars
                elif arg[4:] == "min":
                    arg_dict["top"] = min_bars

            elif arg.startswith(("top", "bar")) and len(arg) > 3:
                val = util.forceinteger(arg[3:])
                if val >= min_bars and val <= max_bars:
                    arg_dict["top"] = val
                elif arg[3:] == "max":
                    arg_dict["top"] = max_bars
                elif arg[3:] == "min":
                    arg_dict["top"] = min_bars

            elif arg.startswith("points") and len(arg) > 6:
                val = util.forceinteger(arg[6:])
                if val >= min_steps and val <= max_steps:
                    arg_dict["steps"] = val
                elif arg[6:] == "max":
                    arg_dict["steps"] = max_bars
                elif arg[6:] == "min":
                    arg_dict["steps"] = min_bars

            elif arg.startswith(("steps", "point")) and len(arg) > 5:
                val = util.forceinteger(arg[5:])
                if val >= min_steps and val <= max_steps:
                    arg_dict["steps"] = val
                elif arg[5:] == "max":
                    arg_dict["steps"] = max_bars
                elif arg[5:] == "min":
                    arg_dict["steps"] = min_bars

            elif arg.startswith("step") and len(arg) > 4:
                val = util.forceinteger(arg[4:])
                if val >= min_steps and val <= max_steps:
                    arg_dict["steps"] = val
                elif arg[4:] == "max":
                    arg_dict["steps"] = max_bars
                elif arg[4:] == "min":
                    arg_dict["steps"] = min_bars

            elif arg.startswith("scope") and len(arg) > 5:
                val = arg[5:]
                if val in ["server", "guild"]:
                    arg_dict["scope"] = "server"
                else:
                    val2 = util.forceinteger(util.alphanum(val))
                    if val2 > 9999999999999999:
                        arg_dict["scope"] = str(val2)

            elif arg.startswith("time") and len(arg) > 4:
                val = util.forceinteger(arg[4:])
                if val > 0 and val <= now - 24*60*60:
                    arg_dict["timecut"] = val
                else:
                    val2 = arg[4:]
                    possible_timecut = self.get_timecut_seconds(now, val2)
                    if possible_timecut >= 0:
                        arg_dict["timecut"] = possible_timecut

        # parse time argument

        try:
            for arg in arguments:
                possible_timecut = self.get_timecut_seconds(now, arg)
                if possible_timecut >= 0:
                    arg_dict["timecut"] = possible_timecut
        except:
            arg_dict["timecut"] = 0

        return arg_dict



    @to_thread
    def get_scrobble_dataframe(self, ctx, arg_dict, efficiency_filter):

        conFM = sqlite3.connect('databases/scrobbledata.db')
        curFM = conFM.cursor()

        now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())
        user_id = str(ctx.author.id)

        # check arguments

        n = arg_dict["steps"]
        top = arg_dict["top"]
        timecut = arg_dict["timecut"]
        scope = arg_dict["scope"]

        # decide whether to fetch userdata or serverdata

        conNP = sqlite3.connect('databases/npsettings.db')
        curNP = conNP.cursor()

        if scope == "server":
            # fetch entire server (minus scrobble banned/inactive users)

            output_name = "server"
            scrobbles = []

            server_creation_utc = util.get_server_created_utc(ctx)
            if timecut < server_creation_utc:
                timecut = server_creation_utc

            userid_list = [str(u.id) for u in ctx.guild.members]
            lfm_list = [[item[0],str(item[1]).lower().strip(), item[2]] for item in curNP.execute("SELECT id, lfm_name, details FROM lastfm").fetchall()]
            
            for lfm_entry in lfm_list:
                user_id = lfm_entry[0]
                lfm_name = lfm_entry[1]
                scrobble_restriction = lfm_entry[2]

                if user_id not in userid_list:
                    continue
                if scrobble_restriction.startswith(("scrobble_banned", "wk_banned", "crown_banned")) or scrobble_restriction.endswith("inactive"):
                    continue

                scrobbles += [[item[0], item[1]] for item in curFM.execute(f"SELECT artist_name, date_uts FROM [{lfm_name}] WHERE date_uts > ?", (timecut,)).fetchall()]

            #scrobbles.sort(key=lambda x: x[1])

        else: 
            different_user = False
            if scope != "user":
                different_user = True
                user_id = scope

            # check user data
            lfm_list = [[item[0],str(item[1]).lower().strip()] for item in curNP.execute("SELECT lfm_name, details FROM lastfm WHERE id = ?", (str(user_id),)).fetchall()]

            if len(lfm_list) == 0:
                if different_user:
                    raise ValueError(f"Could not find user with ID `{user_id}`.")
                else:
                    raise ValueError(f"You haven't set your lastfm account yet.\nUse `{self.prefix}setfm <your username>` to set your account.")

            lfm_name = lfm_list[-1][0]
            lfm_status = lfm_list[-1][1]
            output_name = lfm_name

            if lfm_status.startswith("scrobble_banned"):
                raise ValueError(f"Unfortunately you cannot use this command. ~~Skill issue~~")

            # fetch scrobble info

            scrobbles = [[item[0], item[1]] for item in curFM.execute(f"SELECT artist_name, date_uts FROM [{lfm_name}] WHERE date_uts > ? ORDER BY date_uts ASC", (timecut,)).fetchall()]
            

        artist_name_dict = {}
        artist_scrobble_dict = {}
        zero_timestamp_detected = False
        smallest_utc = now

        for scrobble in scrobbles:
            utc_time = util.forceinteger(scrobble[1])

            if utc_time < 1:
                continue
            elif utc_time < 10000000:
                utc_time = 0
                zero_timestamp_detected = True
            else:
                if utc_time < smallest_utc:
                    smallest_utc = utc_time

            artist_name_full = scrobble[0]
            artist_compact   = util.compactnamefilter(artist_name_full, "artist")

            if artist_compact not in artist_name_dict:
                artist_name_dict[artist_compact]        = artist_name_full
                artist_scrobble_dict[artist_compact]    = [utc_time]
            else:
                artist_scrobble_dict[artist_compact].append(utc_time)

        # set datapoints

        point_span = (now - smallest_utc) / n
        timestamp_points = []

        for i in range(n):
            timepoint = smallest_utc + round(i * point_span)
            timestamp_points.append(timepoint)
        timestamp_points.append(now)

        timestamp_points_converted = []

        for t in timestamp_points:
            dt_object = datetime.datetime.fromtimestamp(t)
            date_string = dt_object.strftime("%Y-%m-%d")
            timestamp_points_converted.append(date_string)
            
        # create tables (for every artist cumulated scrobbles per day)

        data = {}

        for artist, scrob_times in artist_scrobble_dict.items():
            column = []
            for timepoint in timestamp_points:
                scrob_count = sum(i <= timepoint for i in scrob_times)
                column.append(scrob_count)

            artist_full = artist_name_dict[artist]
            data[artist_full] = column

        print(f"full data: {len(data)} artists")

        if efficiency_filter:
            # remove irrelevant entries

            top = min(top, len(artist_name_dict))
            relevant_names = []

            for k in range(len(timestamp_points)):
                numbers = []
                temp = {}
                for artist in data.keys():
                    val = data[artist][k]
                    temp[artist] = val
                    numbers.append(val)

                numbers.sort(reverse=True)
                threshold = numbers[top-1]

                tempcount = 0
                for artist, scrobs in temp.items():
                    if scrobs >= max(threshold, 1) and tempcount < top:
                        tempcount += 1
                        if artist not in relevant_names:
                            relevant_names.append(artist)

            data_filtered = {}

            for artist, scrob_count_list in data.items():
                if artist in relevant_names:
                    #transform
                    artist2 = str(util.diacritic_translation(artist).encode('utf-8'))
                    if artist2.startswith(("b'", 'b"')):
                        artist2 = artist2[2:]
                    if artist2.endswith(("'", '"')):
                        artist2 = artist2[:-1]
                    #add
                    data_filtered[artist2] = scrob_count_list

            print(f"filtered data: {len(data_filtered)} artists")

            df = pd.DataFrame(data_filtered, index = [timestamp_points_converted])

        else:
            df = pd.DataFrame(data, index = [timestamp_points_converted])

        return df, output_name



    @to_thread
    def create_barchart_vid(self, df, user, user_id, arg_dict, now):
        n = arg_dict["steps"]
        top = arg_dict["top"]
        timecut = arg_dict["timecut"]

        bcr.bar_chart_race( df=df, 
                            filename=f'temp/{user_id}_{now}.mp4', 
                            n_bars=top, 
                            steps_per_period=10,
                            filter_column_colors=True,
                            period_length=500,
                            figsize=(6, 3.5),
                            dpi=100,
                            title=f"Scrobbles of {user}",
                            title_size='smaller',
                            #shared_fontdict={'family': ['DejaVu Sans', 'Hiragino Sans']}
                            )



    @commands.command(name='racechart', aliases = ["rc", "barchartrace", "bcr"])
    @commands.check(ScrobbleVisualsCheck.scrobbling_enabled)
    @commands.check(ScrobbleVisualsCheck.is_barchartrace_enabled)
    @commands.check(util.is_active)
    async def _scrobble_racechart_video(self, ctx: commands.Context, *args):
        """Create a race-chart of your scrobbles

        You can provide a time argument, bar number argument and a step number argument. These arguments have to preceded by its name, and separated by a comma or semicolon.
        Use e.g. 
        `<prefix>rce time: year, bars: 10, steps: 60`
        or
        `<prefix>rce quarter, bars: 10`
        """

        # check if pipe is blocked
        in_use_list = ScrobbleVisualsCheck.check_active_gfx_generation("bar_chart_race")

        if len(in_use_list) > 0:
            in_use_string = ', '.join([x[2] for x in in_use_list])
            await ctx.reply(f"Error: The bar chart race functionality is currently in use ({in_use_string}). Please wait a moment!", mention_author=False)
            return

        ScrobbleVisualsCheck.block_gfx_generation(ctx, "bar_chart_race")
        
        now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())

        try:
            await util.cooldown(ctx, "bar_chart_race")
        except Exception as e:
            await ctx.reply("Bar Chart Race cooldown. Please wait a few seconds.", mention_author=False)
            return

        async with ctx.typing():
            efficiency_filter = True
            user_id = str(ctx.author.id)
            user = ctx.author.name

            arg_dict = await self.parse_barchartrace_args(args)
            n = arg_dict["steps"]
            top = arg_dict["top"]
            timecut = arg_dict["timecut"]
            scope = arg_dict["scope"]
            if timecut <= 1000000000:
                timestring = "`all time`"
            else:
                timestring = f"<t:{timecut}:R>"

            title = "bar chart race"
            text0 = f"Settings:\nbars = `{top}`, steps = `{n}`, from = {timestring}"
            if scope != "user":
                text0 += f"\nscope: `@{scope}`"
            emoji = util.emoji("load")
            text1 = f"\nCreating dataframe... {emoji}"
            embed1 = discord.Embed(title=title, description=text0+text1, color=0x000000)
            loading_message = await ctx.reply(embed=embed1, mention_author=False)

            try:
                df, lfm_name = await self.get_scrobble_dataframe(ctx, arg_dict, efficiency_filter)
            except Exception as e:
                await ctx.reply("Error: " + str(e), mention_author=False)
                raise ValueError(e)

            text2  = f"\nCreated dataframe. ✅\nCreating video... {emoji}"
            embed2 = discord.Embed(title=title, description=text0+text2, color=0x000000)
            await loading_message.edit(embed=embed2)

            try:
                await self.create_barchart_vid(df, lfm_name, user_id, arg_dict, now)

                text3  = f"\nCreated dataframe. ✅\nCreated video. ✅"
                embed3 = discord.Embed(title=title, description=text0+text3, color=0x000000)
                await loading_message.edit(embed=embed3)

                try:
                    await ctx.reply("Here's your scrobble bar chart race!", file=discord.File(rf"temp/{user_id}_{now}.mp4"), mention_author=False)
                except Exception as e:
                    await ctx.reply("Sending race chart video failed.. :(\nMaybe its too large?", mention_author=False)

                os.remove(f"temp/{user_id}_{now}.mp4")

            except:
                text4  = f"\nCreated dataframe. ✅\nCreating video failed. ❌"
                embed4 = discord.Embed(title=title, description=text0+text4, color=0x000000)
                await loading_message.edit(embed=embed4)
                await ctx.reply("Converting the dataframe to a bar chart race video failed... :(", mention_author=False)

        ScrobbleVisualsCheck.unblock_gfx_generation("bar_chart_race")
        print("BarChartRace creation finished.")

    @_scrobble_racechart_video.error
    async def scrobble_racechart_video_error(self, ctx, error):
        try:
            ScrobbleVisualsCheck.unblock_gfx_generation("bar_chart_race")
        except Exception as e:
            print("Error in error handler:", e)
        await util.error_handling(ctx, error)




    @commands.command(name='racechartexport', aliases = ["rce", "rcexport", "bcre"])
    @commands.check(ScrobbleVisualsCheck.scrobbling_enabled)
    @commands.check(util.is_active)
    async def _scrobble_racechart_export(self, ctx: commands.Context, *args):
        """Make a dataframe of your scrobbles in .csv format

        You can provide a time argument, bar number argument, a step number argument and a scope argument. The number arguments have to preceded by their name, all arguments have to be separated by a comma or semicolon.
        Use e.g. 
        `<prefix>rce time: year, bars: 10, steps: 60, scope: server`
        or leave some out like
        `<prefix>rce quarter, bars: 10`

        The number of bars need to be an integer between 1 and 50. The number of steps needs to be an integer between 7 and 500. The scope needs to be either `server` or a user ID/mention. The time argument needs to be `week`, `month`, `quarter`, `half`, `year` or `all`.

        This csv file will be comma-delimited.

        """

        # check if pipe is blocked
        in_use_list = ScrobbleVisualsCheck.check_active_gfx_generation("bar_chart_race")

        if len(in_use_list) > 0:
            in_use_string = ', '.join([x[2] for x in in_use_list])
            await ctx.reply(f"Error: The bar chart race functionality is currently in use ({in_use_string}). Please wait a moment!", mention_author=False)
            return

        ScrobbleVisualsCheck.block_gfx_generation(ctx, "bar_chart_race")

        now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())

        try:
            await util.cooldown(ctx, "bar_chart_race")
        except Exception as e:
            await ctx.reply("Bar Chart Race cooldown. Please wait a few seconds.", mention_author=False)
            return

        async with ctx.typing():
            efficiency_filter = False
            user_id = str(ctx.author.id)
            user = ctx.author.name

            arg_dict = await self.parse_barchartrace_args(args)

            try:
                df, lfm_name = await self.get_scrobble_dataframe(ctx, arg_dict, efficiency_filter)
            except Exception as e:
                await ctx.reply("Error: " + str(e), mention_author=False)
                raise ValueError(e)

            file_name = f"temp/{user_id}_{now}.csv"

            try:
                df.to_csv(file_name, sep=',', encoding='utf-8')

                try:
                    await ctx.send(f"Here's your comma-separated `.csv` file with the scrobble data!", file=discord.File(rf"temp/{user_id}_{now}.csv"))
                except:
                    await ctx.send("Sending the file failed.. :(\nMaybe its too large?")

                os.remove(f"temp/{user_id}_{now}.csv")

            except:
                await ctx.send("Converting the dataframe to `CSV` failed... :(")

        ScrobbleVisualsCheck.unblock_gfx_generation("bar_chart_race")
        print("Dataframe-Export finished.")

    @_scrobble_racechart_export.error
    async def scrobble_racechart_export_error(self, ctx, error):
        try:
            ScrobbleVisualsCheck.unblock_gfx_generation("bar_chart_race")
        except Exception as e:
            print("Error in error handler:", e)
        await util.error_handling(ctx, error)



    



async def setup(bot: commands.bot) -> None:
    await bot.add_cog(
        Music_Scrobbling_Visuals(bot),
        guilds = [discord.Object(id = int(os.getenv("guild_id")))])
