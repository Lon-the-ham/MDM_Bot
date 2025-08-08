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

try:
    import pandas as pd 
    import bar_chart_race as bcr
    barchartrace_enabled = True
except:
    print("Not importing bar chart race library")
    barchartrace_enabled = False

try:
    from PIL import Image, ImageDraw, ImageFont
    from io import BytesIO
    import urllib.request
    #from urllib.request import urlopen
    image_charts_enabled = True
except:
    image_charts_enabled = False




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
            raise commands.CheckFailure("This functionality is turned off.")

    def is_imagechart_enabled(*ctx):
        if image_charts_enabled:
            return True
        else:
            raise commands.CheckFailure("This functionality is turned off.")



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



################################################################################################################################################################



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



    ##################################### BAR CHART RACE ##############################################



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

        # set default values

        default_timecut = 0
        default_timeend = now + 1
        default_top = 10
        default_scope = "user"

        # initialise args

        arg_dict = {}

        arguments = []
        args_intermediate = ' '.join(args).replace(";",",").split(",")
        for arg in args_intermediate:
            arguments.append(''.join([x for x in arg.lower() if x.isalnum()]).strip())

            if "scope" not in arg_dict:
                arg_strip = arg.strip()
                if arg_strip.startswith("<@") and arg_strip.endswith(">") and len(arg_strip) >= 19:
                    if util.represents_integer(arg_strip[2:-1]):
                        arg_dict["scope"] = arg_strip[2:-1]

        min_bars = 1
        max_bars = 50
        min_steps = 7
        max_steps = 200

        for arg in arguments:
            if arg.startswith("bars") and len(arg) > 4 and "top" not in arg_dict:
                val = util.forceinteger(arg[4:])
                if val >= min_bars and val <= max_bars:
                    arg_dict["top"] = val
                elif arg[4:] == "max" or val > max_bars:
                    arg_dict["top"] = max_bars
                elif arg[4:] == "min" or (val < min_bars and val > 0):
                    arg_dict["top"] = min_bars

            elif arg.startswith(("top", "bar")) and len(arg) > 3 and "top" not in arg_dict:
                val = util.forceinteger(arg[3:])
                if val >= min_bars and val <= max_bars:
                    arg_dict["top"] = val
                elif arg[3:] == "max" or val > max_bars:
                    arg_dict["top"] = max_bars
                elif arg[3:] == "min" or (val < min_bars and val > 0):
                    arg_dict["top"] = min_bars

            elif arg.startswith("points") and len(arg) > 6 and "steps" not in arg_dict:
                val = util.forceinteger(arg[6:])
                if val >= min_steps and val <= max_steps:
                    arg_dict["steps"] = val
                elif arg[6:] == "max" or val > max_steps:
                    arg_dict["steps"] = max_steps
                elif arg[6:] == "min" or (val < min_steps and val > 0):
                    arg_dict["steps"] = min_steps

            elif arg.startswith(("steps", "point")) and len(arg) > 5 and "steps" not in arg_dict:
                val = util.forceinteger(arg[5:])
                if val >= min_steps and val <= max_steps:
                    arg_dict["steps"] = val
                elif arg[5:] == "max" or val > max_steps:
                    arg_dict["steps"] = max_steps
                elif arg[5:] == "min" or (val < min_steps and val > 0):
                    arg_dict["steps"] = min_steps

            elif arg.startswith("step") and len(arg) > 4 and "steps" not in arg_dict:
                val = util.forceinteger(arg[4:])
                if val >= min_steps and val <= max_steps:
                    arg_dict["steps"] = val
                elif arg[4:] == "max" or val > max_steps:
                    arg_dict["steps"] = max_steps
                elif arg[4:] == "min" or (val < min_steps and val > 0):
                    arg_dict["steps"] = min_steps

            elif arg.startswith("scope") and len(arg) > 5 and "scope" not in arg_dict:
                val = arg[5:]
                if val in ["server", "guild"]:
                    arg_dict["scope"] = "server"
                else:
                    val2 = util.forceinteger(util.alphanum(val))
                    if val2 > 9999999999999999:
                        arg_dict["scope"] = str(val2)

            elif arg.startswith("user") and len(arg) > 4 and "scope" not in arg_dict:
                val = arg[4:]
                if val in ["server", "guild"]:
                    arg_dict["scope"] = "server"
                else:
                    val2 = util.forceinteger(util.alphanum(val))
                    if val2 > 9999999999999999:
                        arg_dict["scope"] = str(val2)

            elif arg.startswith(("time", "from")) and len(arg) > 4 and "timecut" not in arg_dict:
                val = util.forceinteger(arg[4:])
                if val > 0 and val <= now - 24*60*60:
                    if val > 9999 or val < 1970:
                        arg_dict["timecut"] = val
                    else:
                        try:
                            arg_dict["timecut"] = int((datetime.datetime(val, 1, 1) - datetime.datetime(1970, 1, 1)).total_seconds())
                            arg_dict["timeend"] = int((datetime.datetime(val+1, 1, 1) - datetime.datetime(1970, 1, 1)).total_seconds())
                            arg_dict["timedisplay"] = str(val)
                        except Exception as e:
                            print("Error:", e)
                else:
                    val2 = arg[4:]
                    possible_timecut = self.get_timecut_seconds(now, val2)
                    if possible_timecut >= 0:
                        arg_dict["timecut"] = possible_timecut
                    else:
                        timeseconds, timetext, rest = await util.timeparse(arg[4:])
                        timesec_int = util.forceinteger(timeseconds)
                        if timesec_int >= 24*60*60:
                            arg_dict["timecut"] = max(now - timesec_int, 0)

        # parse time argument

        if "timecut" not in arg_dict:
            try:
                for arg in arguments:
                    possible_timecut = self.get_timecut_seconds(now, arg)
                    if possible_timecut >= 0:
                        arg_dict["timecut"] = possible_timecut
            except:
                arg_dict["timecut"] = default_timecut

        # set default step count

        if "scope" not in arg_dict:
            arg_dict["scope"] = default_scope

        if "top" not in arg_dict:
            arg_dict["top"] = default_top

        if "timecut" not in arg_dict:
            arg_dict["timecut"] = default_timecut

        if "timeend" not in arg_dict:
            arg_dict["timeend"] = default_timeend

        if "timedisplay" not in arg_dict:
            arg_dict["timedisplay"] = ""

        if "steps" not in arg_dict:
            if arg_dict["timecut"] > 1000000000:
                months_covered = round((arg_dict["timeend"] - arg_dict["timecut"]) / (60*60*24*28))
                arg_dict["steps"] = min(max(months_covered, min_steps), max_steps)
            else:
                arg_dict["steps"] = 60

        return arg_dict



    @to_thread
    def get_scrobble_dataframe(self, ctx, arg_dict, efficiency_filter):

        conFM = sqlite3.connect('databases/scrobbledata.db')
        curFM = conFM.cursor()

        now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())
        user_id = str(ctx.author.id)

        # check arguments

        print(arg_dict)

        n = arg_dict["steps"]
        top = arg_dict["top"]
        timecut = arg_dict["timecut"]
        timeend = arg_dict["timeend"]
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

                scrobbles += [[item[0], item[1]] for item in curFM.execute(f"SELECT artist_name, date_uts FROM [{lfm_name}] WHERE date_uts > ? AND date_uts < ?", (timecut, timeend)).fetchall()]

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
                    raise ValueError(f"You haven't set your lastfm account yet.\nUse `{self.prefix}setfm <your username>` to set your account and then `{self.prefix}u` to import your scrobbles.")

            lfm_name = lfm_list[-1][0]
            lfm_status = lfm_list[-1][1]
            output_name = lfm_name

            if lfm_status.startswith("scrobble_banned"):
                raise ValueError(f"Unfortunately you cannot use this command. ~~Skill issue~~")

            # fetch scrobble info

            scrobbles = [[item[0], item[1]] for item in curFM.execute(f"SELECT artist_name, date_uts FROM [{lfm_name}] WHERE date_uts > ? AND date_uts < ? ORDER BY date_uts ASC", (timecut, timeend)).fetchall()]
            

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

        point_span = (timeend - smallest_utc) / n
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
                    if len(artist2) > 30:
                        artist2 = artist2[:27] + "..."
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
        timeend = arg_dict["timeend"]

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
        `<prefix>bcr time: year, bars: 10, steps: 60`
        or
        `<prefix>bcr quarter, bars: 10`
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
            ScrobbleVisualsCheck.unblock_gfx_generation("bar_chart_race")
            return

        async with ctx.typing():
            efficiency_filter = True
            user_id = str(ctx.author.id)
            user = ctx.author.name

            arg_dict = await self.parse_barchartrace_args(args)
            n = arg_dict["steps"]
            top = arg_dict["top"]
            timecut = arg_dict["timecut"]
            timeend = arg_dict["timeend"]
            timedisplay = arg_dict["timedisplay"]
            scope = arg_dict["scope"]
            if timedisplay == "":
                if timecut <= 1000000000:
                    timestring = "`all time`"
                else:
                    timestring = f"<t:{timecut}:R>"
            else:
                timestring = f"`{timedisplay}`"

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




    ######################################################### TOP CHART ########################################################################



    @to_thread
    def create_chart(self, caption_dict, image_dict, chart_name, width, height, font_factor):
        """takes dictionaries of image_url_names and image_caption_names and makes a collage out of them"""

        #SETTINGS
        caption_font = "other/resources/arial-unicode-ms.ttf"

        fontColor = 0xFFFFFF
        TINT_COLOR = (0, 0, 0)  # Black
        TRANSPARENCY = .6  # Degree of transparency, 0-100%
        OPACITY = int(255 * TRANSPARENCY)

        #determine grid
        if width == 0 or width == None or height == 0 or height == None:
            grid_size = 1
            for q in range(2,11):
                if len(image_dict) >= q*q:
                    grid_size = q
            width = grid_size
            height = grid.size

        grid_size = max(width, height)

        #creates a new empty image, RGB mode, and size ~1200 by 1200.
        img_size = min(round(1200 / grid_size), 300)
        collage_img = Image.new('RGB', (img_size * width, img_size * height))

        font_size = round((img_size / 10) * (font_factor / 100))

        try:
            font = ImageFont.truetype(caption_font, font_size)
        except:
            font = ImageFont.truetype("arial.ttf", font_size)

        try:
            version = Utils.get_version().replace("version","v").replace(" ","").strip()
        except:
            version = "v_X"
        try:
            APP_NAME = "_" + os.getenv("lfm_app_name")
        except:
            APP_NAME = ""
        try:
            REGISTERED_TO = "_by:" + os.getenv("lfm_registered_to")
        except:
            REGISTERED_TO = ""
        USER_AGENT = f'MDM_Bot_{version}{APP_NAME}{REGISTERED_TO}_function:NowPlaying'

        x = 0
        y = 0
        for img_key in image_dict.keys():
            try:
                #opens an image:
                try:
                    img_loc = image_dict[img_key]
                    if img_loc.startswith("temp/"):
                        img_cell = Image.open(open(f"temp/{img_key}.jpg", 'rb'))
                    elif img_loc.startswith("http"):
                        hdr = { 'User-Agent' : USER_AGENT }
                        req = urllib.request.Request(img_loc, headers=hdr)
                        with BytesIO(urllib.request.urlopen(req).read()) as file:
                            img_cell = Image.open(file)
                            img_cell = img_cell.convert("RGB")
                    else:
                        raise ValueError("Invalid image")
                except Exception as e:
                    if image_dict[img_key] != "":
                        print(f"Error with {image_dict[img_key]}:", e)
                    img_cell = Image.open(open(f"other/resources/lastfm_default.jpg", 'rb'))

                #resize opened image, so it is no bigger than img_size^2
                img_cell.thumbnail((img_size, img_size))
                w, h = img_cell.size 
                if (max(w,h) < img_size):
                    if w > h:
                        img_cell = img_cell.resize((img_size, int(img_size * (h/w))))
                    else:
                        img_cell = img_cell.resize((int(img_size * (w/h)), img_size))
                w, h = img_cell.size 

                x0 = int((img_size - w) / 2)
                y0 = int((img_size - h) / 2)
                img = Image.new('RGB', (img_size, img_size))
                img.paste(img_cell, (x0,y0))

                #pre-caption (to get text size etc)
                line_number = 1
                caption = caption_dict[img_key]
                if "\n" in caption:
                    caption_lines = caption.split("\n")
                    line_number = len(caption_lines)
                    caption_list = []
                    for cap_line in caption_lines:
                        if len(cap_line) > 60:
                            cap_line2 = cap_line[:57] + "..."
                            caption_list.append(cap_line2)
                        else:
                            caption_list.append(cap_line)
                    caption = '\n'.join(caption_list)  
                else:
                    if len(caption) > 60:
                        caption = caption[:57] + "..."

                drawC = ImageDraw.Draw(img)
                _, _, w, h = drawC.textbbox((0,0), text="Ff Gg Jj Pp Qq Yy Zz", font=font)

                #Make semi-transparent overlay
                img = img.convert("RGBA")
                drawO = ImageDraw.Draw(img)
                overlay = Image.new('RGBA', img.size, TINT_COLOR+(0,))
                drawO = ImageDraw.Draw(overlay)  # Create a context for drawing things on it.
                drawO.rectangle(((0, img_size - h*line_number*1.1), (img_size, img_size)), fill=TINT_COLOR+(OPACITY,))

                #Alpha composite these two images together to obtain the desired result.
                img = Image.alpha_composite(img, overlay)
                img = img.convert("RGB") # Remove alpha for saving in jpg format.

                #actual caption
                drawC2 = ImageDraw.Draw(img)

                caption_lines = caption.split("\n")
                i = len(caption_lines)

                for caption_line in caption_lines:
                    _, _, w, _ = drawC2.textbbox((0,0), text=caption_line, font=font)

                    tries = 0
                    while w > img_size:
                        tries += 1
                        if caption_line.endswith("..."):
                            caption_line = caption_line[:-3]
                        caption_line = caption_line[:-1] + "..."
                        _, _, w, _ = drawC2.textbbox((0,0), text=caption_line, font=font)
                        if tries > 57:
                            break

                    drawC2.text(((img_size-w)/2, (img_size-h*i)*0.99), caption_line, font=font, fill=fontColor)
                    i -= 1

                #paste the image at location x,y:
                collage_img.paste(img, (y,x))

                y += img_size
                if y >= img_size * width:
                    y = 0
                    x += img_size

            except Exception as e:
                print("Error:", e)
                if str(e) == "Invalid image":
                    raise ValueError("Invalid image")

        collage_img.save(f"temp/{chart_name}.jpg", "JPEG")



    async def parse_topchart_args(self, ctx, args):
        now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())

        # set defaults 

        default_timecut = now - 7*24*60*60
        default_timeend = now + 1
        default_top = 9
        default_height = 3
        default_width = 3
        default_scope = "user"
        default_source = "api"
        default_font_factor = 100

        # initialise args

        arg_dict = {}

        arguments = []
        argsjoin = ' '.join(args)
        if ": " in argsjoin or "," in argsjoin or ";" in argsjoin or "=" in argsjoin or "user" in argsjoin or "scope" in argsjoin:
            args_intermediate = argsjoin.replace(";",",").split(",")
        else:
            args_intermediate = argsjoin.split()

        for arg in args_intermediate:
            arguments.append(''.join([x for x in arg.lower() if x.isalnum()]).strip())

            arg_strip = arg.strip()
            if arg_strip.startswith("<@") and arg_strip.endswith(">") and len(arg_strip) >= 19:
                if util.represents_integer(arg_strip[2:-1]):
                    arg_dict["scope"] = arg_strip[2:-1]

        min_size = 1
        max_size = 12

        for arg in arguments:
            if ("x" in arg) and ("top" not in arg_dict.keys() or "width" not in arg_dict.keys() or "height" not in arg_dict.keys()):
                if arg.startswith("size"):
                    arg2 = arg[4:]
                else:
                    arg2 = arg
                size_args = arg2.split("x")
                width_str = size_args[0].strip()
                height_str = size_args[1].strip()
                if util.represents_integer(width_str) and util.represents_integer(height_str):
                    width = util.forceinteger(width_str)
                    height = util.forceinteger(height_str)
                    # adjust
                    if width < min_size:
                        width = min_size
                    if width > max_size:
                        width = max_size
                    if height < min_size:
                        height = min_size
                    if height > max_size:
                        height = max_size
                    # set dict parameters
                    arg_dict["top"] = width*height
                    arg_dict["width"] = width
                    arg_dict["height"] = height

            elif arg.startswith("top") and len(arg) > 3 and "top" not in arg_dict.keys():
                val = util.forceinteger(arg[3:])
                found = False
                if val >= min_size*min_size and val <= max_size*max_size:
                    arg_dict["top"] = val
                    found = True
                elif arg[3:] == "max":
                    arg_dict["top"] = max_size*max_size
                    found = True
                elif arg[3:] == "min":
                    arg_dict["top"] = min_size*min_size
                    found = True
                # adjust size
                if found:
                    square_size = math.ceil(math.sqrt(min_size*min_size))
                    arg_dict["width"] = square_size
                    arg_dict["height"] = square_size

            elif arg.startswith("scope") and len(arg) > 5 and "scope" not in arg_dict.keys():
                val = arg[5:]
                if val in ["server", "guild"]:
                    arg_dict["scope"] = "server"
                else:
                    val2 = util.forceinteger(util.alphanum(val))
                    if val2 > 9999999999999999:
                        arg_dict["scope"] = str(val2)

            elif arg.startswith("user") and len(arg) > 4 and "scope" not in arg_dict.keys():
                val = arg[4:]
                if val in ["server", "guild"]:
                    arg_dict["scope"] = "server"
                else:
                    val2 = util.forceinteger(util.alphanum(val))
                    if val2 > 9999999999999999:
                        arg_dict["scope"] = str(val2)

            elif arg.startswith("time") and len(arg) > 4 and "timecut" not in arg_dict.keys():
                val = util.forceinteger(arg[4:])
                if val > 0 and val <= now - 24*60*60:
                    if val > 9999 or val < 1970:
                        arg_dict["timecut"] = val
                    else:
                        try:
                            arg_dict["timecut"] = int((datetime.datetime(val, 1, 1) - datetime.datetime(1970, 1, 1)).total_seconds())
                            arg_dict["timeend"] = int((datetime.datetime(val+1, 1, 1) - datetime.datetime(1970, 1, 1)).total_seconds())
                            arg_dict["timedisplay"] = str(val)
                        except Exception as e:
                            print("Error:", e)
                else:
                    val2 = arg[4:]
                    possible_timecut = self.get_timecut_seconds(now, val2)
                    if possible_timecut >= 0:
                        arg_dict["timecut"] = possible_timecut
                    else:
                        timeseconds, timetext, rest = await util.timeparse(arg[4:])
                        timesec_int = util.forceinteger(timeseconds)
                        if timesec_int >= 24*60*60:
                            arg_dict["timecut"] = max(now - timesec_int, 0)

            elif arg.startswith("font") and len(arg) > 4:
                if arg.startswith("fontsize") and len(arg) > 8:
                    val = util.forceinteger(arg[8:])
                    if val > 0:
                        arg_dict["fontfactor"] = val
                elif arg.startswith("fontfactor") and len(arg) > 10:
                    val = util.forceinteger(arg[10:])
                    if val > 0:
                        arg_dict["fontfactor"] = val
                else:
                    val = util.forceinteger(arg[4:])
                    if val > 0:
                        arg_dict["fontfactor"] = val

            elif arg.startswith("source") and len(arg) > 6 and "source" not in arg_dict.keys():
                val = arg[6:].lower()
                if val in ["loc", "local", "db", "database"]:
                    arg_dict["source"] = "local"
                elif val in ["lastfm", "lfm", "api"]:
                    arg_dict["source"] = "api"

            elif arg.lower() == "local" and "source" not in arg_dict.keys():
                arg_dict["source"] = "local"
            elif arg.lower() == "api" and "source" not in arg_dict.keys():
                arg_dict["source"] = "api"

        # parse time argument
        if "timecut" not in arg_dict.keys():
            try:
                for arg in arguments:
                    possible_timecut = self.get_timecut_seconds(now, arg)
                    if possible_timecut >= 0:
                        arg_dict["timecut"] = possible_timecut
            except:
                arg_dict["timecut"] = default_timecut

        # set missing parameters to default values

        if "timecut" not in arg_dict.keys():
            arg_dict["timecut"] = default_timecut

        if "timeend" not in arg_dict.keys():
            arg_dict["timeend"] = default_timeend

        if "timedisplay" not in arg_dict:
            arg_dict["timedisplay"] = ""

        if "top" not in arg_dict.keys():
            arg_dict["top"] = default_top

        if "height" not in arg_dict.keys():
            arg_dict["height"] = default_height
            
        if "width" not in arg_dict.keys():
            arg_dict["width"] = default_width

        if "scope" not in arg_dict.keys():
            arg_dict["scope"] = default_scope

        if "source" not in arg_dict.keys():
            arg_dict["source"] = default_source

        if "fontfactor" not in arg_dict.keys():
            arg_dict["fontfactor"] = default_font_factor

        return arg_dict



    async def get_album_cover_url(self, ctx, artist_name, album_name):
        # first try compact get from db
        artistcompact = util.compactnamefilter(artist_name, "artist", "alias")
        albumcompact = util.compactnamefilter(album_name, "album")
        conSM = sqlite3.connect('databases/scrobblemeta.db')
        curSM = conSM.cursor()
        artistinfo_list = [[item[0], item[1]] for item in curSM.execute("SELECT cover_url, details FROM albuminfo WHERE artist_filtername = ? AND album_filtername = ?", (artistcompact, albumcompact)).fetchall()]

        if len(artistinfo_list) > 0:
            url = artistinfo_list[-1][0]
            details = str(artistinfo_list[-1][1])
            if url != "" and not url.endswith("/2a96cbd8b46e442fc41c2b86b821562f.png"):
                return url, details

        # otherwise get info from lastfm and save data in albuminfo
        try:
            url, tags = await util.fetch_update_lastfm_artistalbuminfo(ctx, artist_name, album_name)
        except:
            url = ""

        details = ""

        return url, details



    @to_thread
    def get_relevant_chart_dictionaries(self, ctx, arg_dict):
        # extract args
        top = arg_dict["top"]
        width = arg_dict["width"]
        height = arg_dict["height"]
        timecut = arg_dict["timecut"]
        timeend = arg_dict["timeend"]
        scope = arg_dict["scope"]
        charttype = arg_dict["charttype"]

        # connect to databases
        conFM = sqlite3.connect('databases/scrobbledata.db')
        curFM = conFM.cursor()
        conFM2 = sqlite3.connect('databases/scrobbledata_releasewise.db')
        curFM2 = conFM2.cursor()
        conNP = sqlite3.connect('databases/npsettings.db')
        curNP = conNP.cursor()
        conSS = sqlite3.connect('databases/scrobblestats.db')
        curSS = conSS.cursor()

        scrobble_list = []
        aa_scrobble_dict = {}
        artist_scrobble_dict = {}
        artist_dict = {}
        artist_album_dict = {}
        aa_first_found_in = {}

        if scope == "server":
            user_name = ctx.guild.name

            # fetch entire server (minus scrobble banned/inactive users)
            output_name = "server"
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

                if timecut == 0:
                    artist_album_scrobble_list = [[item[0], item[1], item[2]] for item in curFM2.execute(f"SELECT artist_name, album_name, count FROM [{lfm_name}]").fetchall()]

                    for item in artist_album_scrobble_list:
                        artist_compact = item[0]
                        album_compact = item[1]
                        count = util.forceinteger(item[2])
                        aa_tuple = (artist_compact, album_compact)

                        artist_scrobble_dict[artist_compact] = artist_scrobble_dict.get(artist_compact, 0) + count
                        aa_scrobble_dict[aa_tuple] = aa_scrobble_dict.get(aa_tuple, 0) + count

                        if aa_tuple not in aa_first_found_in:
                            aa_first_found_in[aa_tuple] = lfm_name

                else:
                    scrobble_list += [[item[0], item[1]] for item in curFM.execute(f"SELECT artist_name, album_name FROM [{lfm_name}] WHERE date_uts > ? AND date_uts < ? ORDER BY date_uts DESC", (timecut, timeend)).fetchall()]

                    for item in scrobble_list:
                        artist = item[0]
                        album = item[1]
                        artist_compact = util.compactnamefilter(artist, "artist", "alias")
                        album_compact = util.compactnamefilter(album, "album")
                        aa_tuple = (artist_compact, album_compact)

                        artist_scrobble_dict[artist_compact] = artist_scrobble_dict.get(artist_compact, 0) + 1
                        aa_scrobble_dict[aa_tuple] = aa_scrobble_dict.get(aa_tuple, 0) + 1

                        if aa_tuple not in artist_album_dict:
                            artist_album_dict[aa_tuple] = (artist, album)
                        if artist_compact not in artist_dict:
                            artist_dict[artist_compact] = artist
        else:
            if scope == "user":
                user_id = ctx.author.id
            else:
                user_id = scope

            lfm_list = [[item[0],str(item[1]).lower().strip()] for item in curNP.execute("SELECT lfm_name, details FROM lastfm WHERE id = ?", (str(user_id),)).fetchall()]

            if len(lfm_list) == 0:
                raise ValueError("no such user found on this server")
            elif lfm_list[-1][1].startswith("scrobble_banned"):
                raise ValueError("this user is scrobble banned")

            lfm_name = lfm_list[-1][0]
            user_name = lfm_name

            if timecut == 0:
                artist_album_scrobble_list = [[item[0], item[1], item[2]] for item in curFM2.execute(f"SELECT artist_name, album_name, count FROM [{lfm_name}]").fetchall()]

                for item in artist_album_scrobble_list:
                    artist_compact = item[0]
                    album_compact = item[1]
                    count = util.forceinteger(item[2])
                    aa_tuple = (artist_compact, album_compact)

                    artist_scrobble_dict[artist_compact] = artist_scrobble_dict.get(artist_compact, 0) + count
                    aa_scrobble_dict[aa_tuple] = aa_scrobble_dict.get(aa_tuple, 0) + count

            else:
                scrobble_list += [[item[0], item[1]] for item in curFM.execute(f"SELECT artist_name, album_name FROM [{lfm_name}] WHERE date_uts > ? AND date_uts < ? ORDER BY date_uts DESC", (timecut, timeend)).fetchall()]

                for item in scrobble_list:
                    artist = item[0]
                    album = item[1]
                    artist_compact = util.compactnamefilter(artist, "artist", "alias")
                    album_compact = util.compactnamefilter(album, "album")
                    aa_tuple = (artist_compact, album_compact)

                    artist_scrobble_dict[artist_compact] = artist_scrobble_dict.get(artist_compact, 0) + 1
                    aa_scrobble_dict[aa_tuple] = aa_scrobble_dict.get(aa_tuple, 0) + 1

                    if aa_tuple not in artist_album_dict:
                        artist_album_dict[aa_tuple] = (artist, album)
                    if artist_compact not in artist_dict:
                            artist_dict[artist_compact] = artist

        # GET THE TOP ENTRIES
        count_list = []

        if charttype == "artists":
            for artistcompact, count in artist_scrobble_dict.items():
                count_list.append([artistcompact, count])
        else:
            for aa_compact, count in aa_scrobble_dict.items():
                count_list.append([aa_compact, count])

        count_list.sort(key=lambda x: x[1], reverse=True)
        m = min(top, len(count_list))
        count_list = count_list[:m]

        return user_name, count_list, artist_dict, artist_album_dict, aa_scrobble_dict, aa_first_found_in



    async def get_chart_data_from_db(self, ctx, arg_dict):
        top = arg_dict["top"]
        width = arg_dict["width"]
        height = arg_dict["height"]
        timecut = arg_dict["timecut"]
        timeend = arg_dict["timeend"]
        scope = arg_dict["scope"]
        charttype = arg_dict["charttype"]

        caption_dict = {}
        image_dict = {}
        is_nsfw = False

        print("create lists and maps...")
        user_name, count_list, artist_dict, artist_album_dict, aa_scrobble_dict, aa_first_found_in = await self.get_relevant_chart_dictionaries(ctx, arg_dict)

        if len(artist_album_dict) == 0:
            print("get full names and cover images...")
            needs_scrobble_loading = True

            i = 0
            for item in count_list:
                i += 1
                if charttype == "artists":
                    artistcompact = item[0]
                    album_count_list = []
                    for aa_tuple in aa_scrobble_dict.keys():
                        if aa_tuple[0] == artistcompact:
                            count = aa_scrobble_dict[aa_tuple]
                            album_count_list.append([aa_tuple, count])

                    album_count_list.sort(key=lambda x: x[1], reverse=True)
                    aa_compact = album_count_list[0]
                    albumcompact = aa_compact[1]
                else:
                    artistcompact = item[0][0]
                    albumcompact = item[0][1]

                # GET THE FULL NAMES OF THE ARTISTS/ALBUMS
                artist_name, album_name, image_url, details, tagstring, last_updated = await util.get_album_details_from_compact(artistcompact, albumcompact)

                #if image_url is None or image_url == "":
                #    if scope == "server":
                #        lfm_name = aa_first_found_in[artistcompact]
                #    else:
                #        lfm_name = user_name
                #    if needs_scrobble_loading:
                #        conFM = sqlite3.connect('databases/scrobbledata.db')
                #        curFM = conFM.cursor()
                #        check_scrobble_list = [[item[0], item[1]] for item in curFM.execute(f"SELECT artist_name, album_name FROM [{lfm_name}] ORDER BY date_uts DESC").fetchall()]
                #        first_time = False

                #    for item in check_scrobble_list:
                #        check_artist = item[0]
                #        check_album = item[1]
                #        check_artistcompact = util.compactnamefilter(check_artist, "artist", "alias")
                #        check_albumcompact = util.compactnamefilter(check_album, "album")

                #        if check_artistcompact == artistcompact and check_albumcompact == albumcompact:
                #            artist_name = check_artist
                #            album_name = check_album
                #            image_dict[i] = await self.get_album_cover_url(ctx, artist_name, album_name)
                #            break
                #    else:
                #        # empty last fm cover
                #        image_dict[i] = "https://i.imgur.com/ZJKiTyT.jpeg"
                #else:
                #    image_dict[i] = image_url

                if artist_name is None or image_url is None:
                    print("under construction: using placeholder image and names")

                    image_dict[i] = "https://i.imgur.com/ZJKiTyT.jpeg"
                    if charttype == "artists":
                        caption_dict[i] = f"{artistcompact}"
                    else:
                        caption_dict[i] = f"{artistcompact}\n{albumcompact}"
                else:
                    image_dict[i], details = await self.get_album_cover_url(ctx, artist_name, album_name)
                    if charttype == "artists":
                        caption_dict[i] = util.compactaddendumfilter(artist_name, "artist")
                    else:
                        caption_dict[i] = util.compactaddendumfilter(artist_name, "artist") + "\n" + util.compactaddendumfilter(album_name, "album")

                if str(details).lower().strip() == "nsfw":
                    is_nsfw = True

        else:
            print("get cover images...")
            i = 0
            for item in count_list:
                i += 1
                if charttype == "artists":
                    artistcompact = item[0]
                    artist_name = util.compactaddendumfilter(artist_dict[artistcompact], "artist")
                    caption_dict[i] = artist_name

                    album_count_list = []
                    for aa_tuple in aa_scrobble_dict.keys():
                        if aa_tuple[0] == artistcompact:
                            count = aa_scrobble_dict[aa_tuple]
                            album_count_list.append([aa_tuple, count])

                    album_count_list.sort(key=lambda x: x[1], reverse=True)
                    aa_compact = album_count_list[0][0]
                    album_name = artist_album_dict[aa_compact][1]
                else:
                    artistcompact = item[0][0]
                    albumcompact = item[0][1]
                    aa_full = artist_album_dict[(artistcompact, albumcompact)]
                    artist_name = util.compactaddendumfilter(aa_full[0], "artist")
                    album_name = util.compactaddendumfilter(aa_full[1], "album")
                    caption_dict[i] = f"{artist_name}\n{album_name}"

                image_dict[i], details = await self.get_album_cover_url(ctx, artist_name, album_name)
                if str(details).lower().strip() == "nsfw":
                    is_nsfw = True

        return caption_dict, image_dict, user_name, is_nsfw



    async def parse_chart_list_from_api(self, response, charttype, lfm_name, top, check_list):
        now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())

        caption_image_list = []
        rjson = response.json()
        i = len(check_list)

        if charttype == "artists":
            topartists = rjson['topartists']['artist']

            for entry in topartists:
                artist = entry['name']
                mbid = 'mbid'

                image, update_time = await util.get_database_artistimage(artist)
                if image == "" or update_time < now - 30*24*60*60:
                    image = await util.get_spotify_artistimage(artist, lfm_name, image)

                if artist in check_list:
                    pass
                else:
                    check_list.append(artist)
                    caption_image_list.append([artist, "", image])
                    i += 1

                    if i == top:
                        break

        else:
            topalbums = rjson['topalbums']['album']

            for entry in topalbums:
                artist = entry['artist']['name']
                album = entry['name']
                image = entry['image'][-1]['#text']

                image2, last_update = await util.get_database_albumimage(artist, album, image)

                if last_update > now:
                    image = image2

                if (artist, album) in check_list:
                    pass
                else:
                    check_list.append((artist, album))
                    caption_image_list.append([artist, album, image])
                    i += 1

                    if i == top:
                        break

        return caption_image_list, check_list



    async def get_chart_data_from_api(self, ctx, arg_dict):
        now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())

        # extract args
        top = arg_dict["top"]
        width = arg_dict["width"]
        height = arg_dict["height"]
        timecut = arg_dict["timecut"]
        timeend = arg_dict["timeend"]
        scope = arg_dict["scope"]
        charttype = arg_dict["charttype"]
        is_nsfw = False

        if scope == "server":
            raise ValueError("switch to database fetch")

        if scope == "user":
            user_id = ctx.author.id
        else:
            user_id = scope

        conNP = sqlite3.connect('databases/npsettings.db')
        curNP = conNP.cursor()
        lfm_list = [[item[0],str(item[1]).lower().strip()] for item in curNP.execute("SELECT lfm_name, details FROM lastfm WHERE id = ?", (str(user_id),)).fetchall()]
        if len(lfm_list) == 0:
            raise ValueError("no such user found on this server")
        elif lfm_list[-1][1].startswith("scrobble_banned"):
            raise ValueError("this user is scrobble banned")

        lfm_name = lfm_list[-1][0]

        payload = {
                    'user': lfm_name,
                    'limit': 50,
                    'page': 1,
                }

        if (now-timecut) < (24*3600) * 10:
            payload['period'] = "7day"
        elif (now-timecut) < (24*3600) * 33:
            payload['period'] = "1month"
        elif (now-timecut) < (24*3600) * 100:
            payload['period'] = "3month"
        elif (now-timecut) < (24*3600) * 200:
            payload['period'] = "6month "
        elif (now-timecut) < (24*3600) * 400:
            payload['period'] = "12month"
        else:
            payload['period'] = "overall"

        if charttype == "artists":
            payload['method'] = 'user.getTopArtists'
        else:
            payload['method'] = 'user.getTopAlbums'

        cooldown = True
        response = await util.lastfm_get(ctx, payload, cooldown, "lastfm")

        caption_image_list, check_list = await self.parse_chart_list_from_api(response, charttype, lfm_name, top, [])

        while top > len(caption_image_list):
            if payload['page'] > 3:
                break
            try:
                payload['limit'] = 50
                payload['page'] += 1
                cooldown = False
                response = await util.lastfm_get(ctx, payload, cooldown, "lastfm")
                new_caption_image_list, new_check_list = await self.parse_chart_list_from_api(response, charttype, lfm_name, top, check_list)

                caption_image_list += new_caption_image_list
                check_list = new_check_list
            except:
                break

        caption_image_list = caption_image_list[:top]

        caption_dict = {}
        image_dict  = {}
        i = 0

        for item in caption_image_list:
            i += 1
            artist = item[0] 
            album = item[1]
            image = item[2]

            if charttype == "artists":
                caption_dict[i] = artist
            else:
                caption_dict[i] = f"{artist}\n{album}"

            image_dict[i] = image

            if (charttype != "artists") and (not is_nsfw):
                is_nsfw = util.album_is_nsfw(artist, album)

        return caption_dict, image_dict, lfm_name, is_nsfw




    @commands.command(name='chart', aliases = ["c", "albumchart"])
    @commands.check(ScrobbleVisualsCheck.scrobbling_enabled)
    @commands.check(ScrobbleVisualsCheck.is_imagechart_enabled)
    @commands.check(util.is_active)
    async def _topalbumchart(self, ctx: commands.Context, *args):
        """Shows chart of recent music
        
        Specify a time argument: week, month, quarter, half, year, alltime
        Specify a size in the format `3x3`, `4x5`, `10x10` etc.
        Ping a user to get their chart.
        
        Default shows your 3x3 week chart.
        """
        now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())

        async with ctx.typing():
            # PARSE ARGUMENTS

            print("chart command: parse args...")
            arg_dict = await self.parse_topchart_args(ctx, args)

            top = arg_dict["top"]
            width = arg_dict["width"]
            height = arg_dict["height"]
            timecut = arg_dict["timecut"]
            timeend = arg_dict["timeend"]
            timedisplay = arg_dict["timedisplay"]
            scope = arg_dict["scope"]
            source = arg_dict["source"]
            font_factor = arg_dict["fontfactor"]

            charttype = "albums"
            arg_dict["charttype"] = charttype

            if timedisplay == "":
                if timecut <= 1000000000:
                    timestring = "`all time`"
                else:
                    timestring = f"<t:{timecut}:R>"
            else:
                timestring = f"`{timedisplay}`"

            # GET DATA

            print("chart command: fetch data...")
            try:
                if source == "local":
                    raise ValueError("local data inquired")
                caption_dict, image_dict, lfm_name, is_nsfw = await self.get_chart_data_from_api(ctx, arg_dict)
                fetched_from_api = True
            except Exception as e:
                if str(e) != "local data inquired":
                    print("API error while trying to fetch chart data:", e)
                try:
                    caption_dict, image_dict, lfm_name, is_nsfw = await self.get_chart_data_from_db(ctx, arg_dict)
                    fetched_from_api = False
                except Exception as e:
                    if str(e) == "no such user found on this server":
                        await ctx.send(f"To use the album chart command you need to provide your lastfm username via `{self.prefix}setfm` and import your scrobbles first.")
                        return

            # MAKE CHART

            print("chart command: create image...")
            if is_nsfw:
                chart_name = f"SPOILER_chart_{ctx.author.id}_{now}"
            else:
                chart_name = f"chart_{ctx.author.id}_{now}"

            await self.create_chart(caption_dict, image_dict, chart_name, width, height, font_factor)

            # SEND

            if fetched_from_api:
                source = "`[from last.fm api]`"
            else:
                source = "`[from local database]`"

            try:
                await ctx.reply(f"**{lfm_name}'s top {len(image_dict)} album chart from** {timestring} **up to now** {source}", file=discord.File(rf"temp/{chart_name}.jpg"), mention_author=False)
            except Exception as e:
                await ctx.reply(f"Error: {e}", mention_author=False)

        os.remove(f"temp/{chart_name}.jpg")

    @_topalbumchart.error
    async def topalbumchart_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='top', aliases = ["topartistchart", "topchart", "artistchart"])
    @commands.check(ScrobbleVisualsCheck.scrobbling_enabled)
    @commands.check(ScrobbleVisualsCheck.is_imagechart_enabled)
    @commands.check(util.is_active)
    async def _topartistchart(self, ctx: commands.Context, *args):
        """Shows chart of recent music
        
        Specify a time argument: week, month, quarter, half, year, alltime
        Specify a size in the format `3x3`, `4x5`, `10x10` etc.
        Ping a user to get their chart.

        Default shows your 3x3 week chart.
        """
        now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())

        async with ctx.typing():
            # PARSE ARGUMENTS

            print("top command: parse args...")
            arg_dict = await self.parse_topchart_args(ctx, args)

            top = arg_dict["top"]
            width = arg_dict["width"]
            height = arg_dict["height"]
            timecut = arg_dict["timecut"]
            timeend = arg_dict["timeend"]
            scope = arg_dict["scope"]
            source = arg_dict["source"]
            font_factor = arg_dict["fontfactor"]

            charttype = "artists"
            arg_dict["charttype"] = charttype

            if timecut <= 1000000000:
                timestring = "`all time`"
            else:
                timestring = f"<t:{timecut}:R>"

            # GET DATA

            print("top command: fetch data...")
            try:
                if source == "local":
                    raise ValueError("local data inquired")
                caption_dict, image_dict, lfm_name, is_nsfw = await self.get_chart_data_from_api(ctx, arg_dict)
                fetched_from_api = True
            except Exception as e:
                if str(e) != "local data inquired":
                    print("API error while trying to fetch chart data:", e)
                try:
                    caption_dict, image_dict, lfm_name, is_nsfw = await self.get_chart_data_from_db(ctx, arg_dict)
                    fetched_from_api = False
                except Exception as e:
                    if str(e) == "no such user found on this server":
                        await ctx.send(f"To use the top artist chart command you need to provide your lastfm username via `{self.prefix}setfm` and import your scrobbles first.")
                        return

            # MAKE CHART

            print("top command: create image...")
            if is_nsfw:
                chart_name = f"SPOILER_chart_{ctx.author.id}_{now}"
            else:
                chart_name = f"chart_{ctx.author.id}_{now}"

            await self.create_chart(caption_dict, image_dict, chart_name, width, height, font_factor)

            # SEND

            if fetched_from_api:
                source = "`[from last.fm api]`"
            else:
                source = "`[from local database]`"

            try:
                await ctx.reply(f"**{lfm_name}'s top {len(image_dict)} artists chart from** {timestring} **up to now** {source}", file=discord.File(rf"temp/{chart_name}.jpg"), mention_author=False)
            except Exception as e:
                await ctx.reply(f"Error: {e}", mention_author=False)

        os.remove(f"temp/{chart_name}.jpg")

    @_topartistchart.error
    async def topartistchart_error(self, ctx, error):
        await util.error_handling(ctx, error)



    #################################################################################################################################################
    #################################################################################################################################################
    #################################################################################################################################################
    #################################################################################################################################################
    #################################################################################################################################################
    #################################################################################################################################################
    #################################################################################################################################################
    #################################################################################################################################################
    #################################################################################################################################################



    @to_thread
    def create_artist_album_chart(self, ctx, artist_name, artist_image, caption_list, image_list, chart_name, user_name_list, user_playcount_list, server_artist_count, total_listeners, scope, mentioned_users):
        #SETTINGS
        caption_font = "other/resources/arial-unicode-ms.ttf"

        coordinates = {
            -1:(96,43),
            0: (602,43),
            1: (930,43),
            2: (1255,43),
            3: (602,318),
            4: (930,318),
            5: (1255,318),
            6: (602,593),
            7: (930,593),
            8: (1255,593),
            99:  (96, 581),
            100: (96, 627),
            101: (96, 673),
            102: (96, 719),
            103: (96, 765),
            104: (96, 811),
        }

        artist_size = 384
        sidesize = 207
        buffer = 5
        caption_box_width = 288

        font_size = 24
        font_smol_size = 20
        font_big_size = 30
        font_user_size = 22

        fontColor = 0xFFFFFF
        TINT_COLOR = (0, 0, 0)  # Black
        TRANSPARENCY = .6  # Degree of transparency, 0-100%
        OPACITY = int(255 * TRANSPARENCY)

        try:
            font = ImageFont.truetype(caption_font, font_size)
            font_smaller = ImageFont.truetype(caption_font, font_smol_size)
            font_larger = ImageFont.truetype(caption_font, font_big_size)
            font_user = ImageFont.truetype(caption_font, font_user_size)
        except:
            font = ImageFont.truetype("arial.ttf", font_size)
            font_smaller = ImageFont.truetype("arial.ttf", font_smol_size)
            font_larger = ImageFont.truetype("arial.ttf", font_big_size)
            font_user = ImageFont.truetype("arial.ttf", font_user_size)

        # FETCHES BACKGROUND IMAGE

        if scope == "server":
            collage_img = Image.open(open(f"other/resources/artistalbumchart_template.jpg", 'rb'))
        else:
            collage_img = Image.open(open(f"other/resources/artistalbumchart_template2.jpg", 'rb'))

        # SET UP USER AGENT

        try:
            version = Utils.get_version().replace("version","v").replace(" ","").strip()
        except:
            version = "v_X"
        try:
            APP_NAME = "_" + os.getenv("lfm_app_name")
        except:
            APP_NAME = ""
        try:
            REGISTERED_TO = "_by:" + os.getenv("lfm_registered_to")
        except:
            REGISTERED_TO = ""
        USER_AGENT = f'MDM_Bot_{version}{APP_NAME}{REGISTERED_TO}_function:NowPlaying'

        # ADD ARTIST

        #opens an image:
        try:
            if artist_image.startswith("http"):
                hdr = { 'User-Agent' : USER_AGENT }
                req = urllib.request.Request(artist_image, headers=hdr)
                with BytesIO(urllib.request.urlopen(req).read()) as file:
                    img_cell = Image.open(file)
                    img_cell = img_cell.convert("RGB")
            else:
                raise ValueError("Invalid image")
        except Exception as e:
            if artist_image != "":
                print(f"Error with image URL {artist_image}:", e)
            img_cell = Image.open(open(f"other/resources/lastfm_default.jpg", 'rb'))

        #resize opened image, so it is no bigger than artist_size^2
        img_cell.thumbnail((artist_size, artist_size))
        w, h = img_cell.size 
        if (max(w,h) < artist_size):
            if w > h:
                img_cell = img_cell.resize((artist_size, int(artist_size * (h/w))))
            else:
                img_cell = img_cell.resize((int(artist_size * (w/h)), artist_size))
        w, h = img_cell.size 

        x0 = int((artist_size - w) / 2)
        y0 = int((artist_size - h) / 2)
        img = Image.new('RGB', (artist_size, artist_size))
        img.paste(img_cell, (x0,y0))

        #paste the image at location x,y:
        x, y = coordinates[-1]
        collage_img.paste(img, (x,y))

        #add artist name (pre-determine width and height)
        drawC = ImageDraw.Draw(img)
        _, _, w, h = drawC.textbbox((0,0), text="Ff Gg Jj Pp Qq Yy Zz", font=font)

        #actual caption
        drawC2 = ImageDraw.Draw(collage_img)

        if scope == "server":
            caption_lines = [artist_name, f"Top albums on {ctx.guild.name}", f"({server_artist_count} plays total from {total_listeners} listeners)"]
        elif len(mentioned_users) == 1:
            uname = util.convert_lfmname_to_discordname(ctx, mentioned_users[0])
            caption_lines = [artist_name, f"{uname}'s fav albums", f"({server_artist_count} plays total)"]
        else:
            caption_lines = [artist_name, f"{len(mentioned_users)} users' fav albums", f"({server_artist_count} plays total)"]

        k = 0
        for caption_line in caption_lines:
            if (k == 0):
                font_here = font_larger
            else:
                font_here = font

            _, _, w, _ = drawC2.textbbox((0,0), text=caption_line, font=font_here)

            tries = 0
            while w > artist_size:
                tries += 1
                if caption_line.endswith("..."):
                    caption_line = caption_line[:-3]
                caption_line = caption_line[:-1] + "..."
                _, _, w, _ = drawC2.textbbox((0,0), text=caption_line, font=font_here)
                if tries > 10:
                    break

            text_x = x + int((artist_size-w)/2)
            text_y = y + artist_size + 2*(1+k) * buffer + (h * k)
            drawC2.text((text_x, text_y), caption_line, font=font_here, fill=fontColor)
            k += 1

        # ADD ALBUMS (COVER, NAME, PLAYCOUNT)

        for i in range(len(caption_list)):
            caption_orig = caption_list[i]
            img_loc = image_list[i]

            x, y = coordinates[i]
            try:
                #opens an image:
                try:
                    if img_loc.startswith("http"):
                        hdr = { 'User-Agent' : USER_AGENT }
                        req = urllib.request.Request(img_loc, headers=hdr)
                        with BytesIO(urllib.request.urlopen(req).read()) as file:
                            img_cell = Image.open(file)
                            img_cell = img_cell.convert("RGB")
                    else:
                        raise ValueError("Invalid image")
                except Exception as e:
                    if img_loc != "":
                        print(f"Error with image URL {img_loc}:", e)
                    img_cell = Image.open(open(f"other/resources/lastfm_default.jpg", 'rb'))

                #resize opened image, so it is no bigger than sidesize^2
                img_cell.thumbnail((sidesize, sidesize))
                w, h = img_cell.size 
                if (max(w,h) < sidesize):
                    if w > h:
                        img_cell = img_cell.resize((sidesize, int(sidesize * (h/w))))
                    else:
                        img_cell = img_cell.resize((int(sidesize * (w/h)), sidesize))
                w, h = img_cell.size 

                x0 = int((sidesize - w) / 2)
                y0 = int((sidesize - h) / 2)
                img = Image.new('RGB', (sidesize, sidesize))
                img.paste(img_cell, (x0,y0))

                #paste the image at location x,y:
                collage_img.paste(img, (x,y))

                #pre-caption (to get text size etc)
                line_number = 1
                if "\n" in caption_orig:
                    caption_lines = caption_orig.split("\n")
                    line_number = len(caption_lines)
                    caption_linelist = []
                    for cap_line in caption_lines:
                        if len(cap_line) > 30:
                            cap_line2 = cap_line[:17] + "..."
                            caption_linelist.append(cap_line2)
                        else:
                            caption_linelist.append(cap_line)
                    caption = '\n'.join(caption_linelist)  
                else:
                    if len(caption_orig) > 30:
                        caption = caption_orig[:17] + "..."

                # pre-determine width and height
                drawC = ImageDraw.Draw(img)
                _, _, w, h = drawC.textbbox((0,0), text="Ff Gg Jj Pp Qq Yy Zz", font=font)

                #actual caption
                drawC2 = ImageDraw.Draw(collage_img)

                caption_lines = caption.split("\n")
                k = 0
                for caption_line in caption_lines:
                    if (k == 0):
                        font_here = font
                    else:
                        font_here = font_smaller

                    _, _, w, _ = drawC2.textbbox((0,0), text=caption_line, font=font_here)

                    tries = 0
                    while w > caption_box_width:
                        tries += 1
                        if caption_line.endswith("..."):
                            caption_line = caption_line[:-3]
                        caption_line = caption_line[:-1] + "..."
                        _, _, w, _ = drawC2.textbbox((0,0), text=caption_line, font=font_here)
                        if tries > 10:
                            break

                    text_x = x - int((caption_box_width - sidesize)/2) + int((caption_box_width-w)/2)
                    text_y = y + sidesize + buffer + (h * k)
                    drawC2.text((text_x, text_y), caption_line, font=font_here, fill=fontColor)
                    k += 1

            except Exception as e:
                print("Error:", e)
                if str(e) == "Invalid image":
                    raise ValueError("Invalid image")

        # ADD TOP LISTENERS
        if scope == "server" or len(mentioned_users) >= 2:
            if scope == "user":
                num = len(mentioned_users) if len(mentioned_users) < 5 else 5
                minititle = f"{num} top users:"
                x, y = coordinates[99]
                drawC2 = ImageDraw.Draw(collage_img)
                _, _, w, _ = drawC2.textbbox((0,0), text=minititle, font=font_user)
                x_central = x + int((artist_size - w)/2)
                drawC2.text((x_central, y), minititle, font=font_user, fill=fontColor)

                for name in mentioned_users:
                    if name not in user_name_list:
                        user_name_list.append(name)
                        user_playcount_list.append(0)

            for j in range(min(len(user_name_list), 5)):
                x, y = coordinates[100 + j]
                user_name = util.convert_lfmname_to_discordname(ctx, user_name_list[j])
                playcount = user_playcount_list[j]

                if scope == "server" and playcount == 0:
                    break

                drawC2 = ImageDraw.Draw(collage_img)
                _, _, w1, _ = drawC2.textbbox((0,0), text=user_name, font=font_user)
                _, _, w2, _ = drawC2.textbbox((0,0), text=str(playcount), font=font_user)

                tries = 0
                while w1 + w2 + 3 * buffer > artist_size:
                    tries += 1
                    if user_name.endswith("..."):
                        user_name = user_name[:-3]
                    user_name = user_name[:-1] + "..."
                    _, _, w1, _ = drawC2.textbbox((0,0), text=user_name, font=font_user)
                    if tries > 15:
                        break

                text_x = x + buffer
                text_y = y + buffer
                drawC2.text((text_x, text_y), user_name, font=font_user, fill=fontColor)

                text_x = x + artist_size - buffer - w2
                drawC2.text((text_x, text_y), str(playcount), font=font_user, fill=fontColor)

        # SAVE

        collage_img.save(f"temp/{chart_name}.jpg", "JPEG")



    @to_thread
    def get_full_album_name_from_table_and_time(self, lfm_name, last_time, album_compact = ""):
        print(f"INPUT: {lfm_name} {last_time} {album_compact}")
        try:
            conFM = sqlite3.connect('databases/scrobbledata.db')
            curFM = conFM.cursor()
            target_scrobble = curFM.execute(f"SELECT album_name FROM [{lfm_name}] WHERE date_uts = ?", (str(last_time),))

            result_tuple = target_scrobble.fetchone()
            album_name = result_tuple[0]

            if album_compact != "":
                if util.compactnamefilter(album_name, "album") != album_compact:
                    print("Error: Found album doesn't match.")
                    return None

            print("OUTPUT")
            return album_name

        except:
            return None



    @commands.command(name='serverartistchart', aliases = ["sac"])
    @commands.check(ScrobbleVisualsCheck.scrobbling_enabled)
    @commands.check(ScrobbleVisualsCheck.is_imagechart_enabled)
    @commands.check(util.is_active)
    async def _serverartistchart(self, ctx: commands.Context, *args):
        """Chart of artist's top albums on this server
        
        Provide an artist argument, or invoke command without argument to get the server artist chart for the artist you're currently listening to (on last.fm).
        """
        scope = "server"
        await self.artist_top_album_chart(ctx, args, scope)
    @_serverartistchart.error
    async def serverartistchart_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='userartistchart', aliases = ["uac", "myac", "myartistchart", "mac", "artistalbumchart", "aac"])
    @commands.check(ScrobbleVisualsCheck.scrobbling_enabled)
    @commands.check(ScrobbleVisualsCheck.is_imagechart_enabled)
    @commands.check(util.is_active)
    async def _userartistchart(self, ctx: commands.Context, *args):
        """Chart of artist's top albums of user
        
        Provide an artist argument, or invoke command without argument to get the user artist chart for the artist you're currently listening to (on last.fm).

        You can @ user(s) to see a chart made up from their scrobbles.
        """
        scope = "user"
        await self.artist_top_album_chart(ctx, args, scope)
    @_userartistchart.error
    async def userartistchart_error(self, ctx, error):
        await util.error_handling(ctx, error)



    async def artist_top_album_chart(self, ctx, args, scope):
        arguments           = []
        mentioned_user_ids  = []
        mentioned_users     = []

        for arg in (' '.join(args).replace(">", "> ").replace("<@", " <@").split()):
            if (scope == "user" and len(arg) > 19 and arg.strip().startswith("<@") and arg.strip().endswith(">") and util.represents_integer(arg.strip()[2:-1])):
                mentioned_user_ids.append(util.forceinteger(arg[2:-1]))
            elif (scope == "user" and len(arg) > 16 and util.represents_integer(arg.strip())):
                mentioned_user_ids.append(util.forceinteger(arg))
            elif arg.strip() == "":
                pass
            else:
                arguments.append(arg.strip())

        if scope == "user" and len(mentioned_user_ids) == 0:
            mentioned_user_ids.append(ctx.author.id)

        ##################################

        if len(arguments) == 0:
            try:
                artist, album, song, thumbnail, cover, tags = await util.get_last_track(ctx)
                if artist is None or artist.strip() == "":
                    raise ValueError("No current/last track found.")
            except Exception as e:
                print("Error:", e)
                await ctx.send("Command needs an artist argument.")
                return

            artist, thumbnail = await util.get_artist_name_and_image(artist, ctx, album)
        else:
            artist, thumbnail = await util.get_artist_name_and_image(' '.join(arguments), ctx)

        artist_compact = util.compactnamefilter(artist, "artist", "alias")

        conNP = sqlite3.connect('databases/npsettings.db')
        curNP = conNP.cursor()
        conFM2 = sqlite3.connect('databases/scrobbledata_releasewise.db')
        curFM2 = conFM2.cursor()

        lfm_list = [[item[0],item[1],str(item[2]).lower().strip()] for item in curNP.execute("SELECT id, lfm_name, details FROM lastfm").fetchall()]

        server_members = [x.id for x in ctx.guild.members]

        # FETCH SCROBBLE COUNT PER ALBUM
        artist_album_dict = {}
        user_count_list = []

        fetch_album_name_later = {} # save lfm_name and timestamp to be able to retrieve the full album name later

        server_artist_count = 0
        total_listeners = 0

        for useritem in lfm_list:
            try:
                user_id = int(useritem[0])
            except Exception as e:
                print("Error:", e)
                continue

            lfm_name = useritem[1]

            if scope == "server":
                # check user id
                if user_id not in server_members:
                    continue

                # check status
                status = useritem[2]

                if status.startswith(("wk_banned", "scrobble_banned")) or status.endswith("inactive"):
                    continue

            else: #scope == "user"
                if user_id not in mentioned_user_ids:
                    continue

                mentioned_users.append(lfm_name)

            # fetch scrobbles

            try:
                artist_scrobbles = [[item[0],item[1],item[2]] for item in curFM2.execute(f"SELECT album_name, count, last_time FROM [{lfm_name}] WHERE artist_name = ?", (artist_compact,)).fetchall()]
            except Exception as e:
                print(f"Skipping user {lfm_name}:", e)
                continue

            totalcount = 0

            for album_count in artist_scrobbles:
                album_compact = album_count[0]
                count = album_count[1]
                totalcount += count
                artist_album_dict[album_compact] = artist_album_dict.get(album_compact, 0) + count

                if album_compact not in fetch_album_name_later:
                    last_time = util.forceinteger(album_count[2])
                    fetch_album_name_later[album_compact] = (lfm_name, last_time)
            
            user_count_list.append([lfm_name, totalcount])
            server_artist_count += totalcount

            if totalcount > 0:
                total_listeners += 1

        if server_artist_count == 0:
            emoji = util.emoji("disappointed")
            await ctx.reply(f"No one has listened to this artist. {emoji}", mention_author=False)
            return


        # GET TOP 9 ALBUMS

        release_name_dict = {}
        release_image_dict = {}
        album_count_sort_list = []

        for album_compact, count in artist_album_dict.items():
            if album_compact != "":
                album_count_sort_list.append([album_compact, count])

        album_count_sort_list.sort(key=lambda x: x[1], reverse=True)
        album_count_sort_list = album_count_sort_list[:9]

        # FETCH FULL ALBUM NAMES AND ALBUM COVERS

        async with ctx.typing():
            for album_item in album_count_sort_list:
                album_compact = album_item[0]
                count = album_item[1]

                print(f">>Checking: {album_compact}")
                _, album_full, cover_url, _, _, _ = await util.get_album_details_from_compact(artist_compact, album_compact)

                if album_full is None or album_full.strip() == "":
                    lfm_name, last_time = fetch_album_name_later[album_compact]
                    album_full = await self.get_full_album_name_from_table_and_time(lfm_name, last_time, album_compact)

                if album_full is None or album_full.strip() == "":
                    album_full = album_compact
                    print("Note: could not find full album name")

                album_full = util.compactaddendumfilter(album_full)

                if cover_url is None or (cover_url == "" or cover_url.endswith("/2a96cbd8b46e442fc41c2b86b821562f.png")):
                    print("Note: could not find cover image in DB, fetching anew")
                    cover_url, details = await self.get_album_cover_url(ctx, artist, album_full)

                    if cover_url is None or (cover_url == "" or cover_url.endswith("/2a96cbd8b46e442fc41c2b86b821562f.png")):
                        print("Note: could not find cover image via API as well :(")
                        cover_url = ""

                release_name_dict[album_compact] = album_full
                release_image_dict[album_compact] = cover_url

        # IF ARTIST IMAGE WASN'T FOUND TRY AGAIN

        if thumbnail is None or thumbnail == "":
            try:
                top_album = release_name_dict[album_count_sort_list[0][0]]
                _, thumbnail = await util.get_artist_name_and_image(' '.join(args), ctx, top_album)
            except Exception as e:
                print("Error while trying to fetch artist image with more information:", e)

        # FETCH TOP USERS

        user_count_list.sort(key=lambda x: x[1], reverse=True)

        user_name_list = []
        user_playcount_list = []

        for item in user_count_list:
            if item[1] == 0:
                break
            user_name_list.append(item[0])
            user_playcount_list.append(item[1])
        
        # CREATE CHART

        caption_list = []
        image_list = []
        is_nsfw = False

        for album_item in album_count_sort_list:
            album_compact = album_item[0]
            count = album_item[1]
            album_full = release_name_dict[album_compact]

            caption_list.append(f"{album_full}\n{count} plays")
            image_list.append(release_image_dict[album_compact])

            if is_nsfw == False:
                is_nsfw = util.album_is_nsfw(artist, album_compact)

        now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())

        if is_nsfw:
            chart_name = f"SPOILER_{scope}_artist_album_chart_{ctx.author.id}_{now}"
        else:
            chart_name = f"{scope}_artist_album_chart_{ctx.author.id}_{now}"

        async with ctx.typing():
            await self.create_artist_album_chart(ctx, artist, thumbnail, caption_list, image_list, chart_name, user_name_list, user_playcount_list, server_artist_count, total_listeners, scope, mentioned_users)

        try:
            await ctx.reply(file=discord.File(rf"temp/{chart_name}.jpg"), mention_author=False)
        except Exception as e:
            await ctx.reply(f"Error: {e}", mention_author=False)

        os.remove(f"temp/{chart_name}.jpg")

    



async def setup(bot: commands.bot) -> None:
    await bot.add_cog(
        Music_Scrobbling_Visuals(bot),
        guilds = [discord.Object(id = int(os.getenv("guild_id")))])
