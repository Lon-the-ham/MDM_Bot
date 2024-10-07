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

try:
    from PIL import Image, ImageDraw, ImageFont
    from io import BytesIO
    from urllib.request import urlopen
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
        return image_charts_enabled

    def is_imagechart_enabled(*ctx):
        return barchartrace_enabled

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




    ######################################################### TOP CHART ########################################################################



    @to_thread
    def create_chart(self, caption_dict, image_dict, chart_name, width, height):
        """takes dictionaries of image_url_names and image_caption_names and makes a collage out of them"""

        #SETTINGS
        try:
            caption_font = "other/resources/Arial Unicode MS.ttf"
        except:
            caption_font = "other/resources/Arimo-Regular.ttf"
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

        font_size = round(img_size / 10)
        font = ImageFont.truetype(caption_font, font_size)

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
                        with BytesIO(urlopen(img_loc).read()) as file:
                            img_cell = Image.open(file)
                            img_cell = img_cell.convert("RGB")
                    else:
                        raise ValueError("Invalid image")
                except Exception as e:
                    img_cell = Image.open(open(f"other/resources/lastfm_default.jpg", 'rb'))

                #resize opened image, so it is no bigger than img_size^2
                img_cell.thumbnail((img_size, img_size))

                img = Image.new('RGB', (img_size, img_size))
                img.paste(img_cell, (0,0))

                #pre-caption (to get text size etc)
                line_number = 1
                caption = caption_dict[img_key]
                if "\n" in caption:
                    caption_lines = caption.split("\n")
                    line_number = len(caption_lines)
                    caption_list = []
                    for cap_line in caption_lines:
                        if len(cap_line) > 20:
                            cap_line2 = cap_line[:17] + "..."
                            caption_list.append(cap_line2)
                        else:
                            caption_list.append(cap_line)
                    caption = '\n'.join(caption_list)  
                else:
                    if len(caption) > 20:
                        caption = caption[:17] + "..."

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



    def parse_topchart_args(self, ctx, args):
        now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())

        arg_dict = {
            "top": 9,
            "height": 3,
            "width": 3,    
            "scope": "user",
        }

        arguments = []
        argsjoin = ' '.join(args)
        if ":" in argsjoin or "user" in argsjoin or "scope" in argsjoin:
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
        max_size = 10

        for arg in arguments:
            if "x" in arg:
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

            elif arg.startswith("top") and len(arg) > 3:
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

            elif arg.startswith("scope") and len(arg) > 5:
                val = arg[5:]
                if val in ["server", "guild"]:
                    arg_dict["scope"] = "server"
                else:
                    val2 = util.forceinteger(util.alphanum(val))
                    if val2 > 9999999999999999:
                        arg_dict["scope"] = str(val2)

            elif arg.startswith("user") and len(arg) > 4:
                val = arg[4:]
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

        if arg_dict["top"] >= 100:
            default_timecut = 0
        elif arg_dict["top"] >= 67:
            default_timecut = now - 180*24*60*60
        elif arg_dict["top"] >= 50:
            default_timecut = now - 90*24*60*60
        elif arg_dict["top"] >= 25:
            default_timecut = now - 30*24*60*60
        else:
            default_timecut = now - 7*24*60*60

        try:
            for arg in arguments:
                possible_timecut = self.get_timecut_seconds(now, arg)
                if possible_timecut >= 0:
                    arg_dict["timecut"] = possible_timecut
        except:
            arg_dict["timecut"] = default_timecut

        if "timecut" not in arg_dict.keys():
            arg_dict["timecut"] = default_timecut

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
            return url, details

        # otherwise get info from lastfm and save data in albuminfo
        url, tags = await util.fetch_update_lastfm_artistalbuminfo(ctx, artist_name, album_name)
        details = ""

        return url, details



    @to_thread
    def get_relevant_chart_dictionaries(self, ctx, arg_dict):
        # extract args
        top = arg_dict["top"]
        width = arg_dict["width"]
        height = arg_dict["height"]
        timecut = arg_dict["timecut"]
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
                    scrobble_list += [[item[0], item[1]] for item in curFM.execute(f"SELECT artist_name, album_name FROM [{lfm_name}] WHERE date_uts > ? ORDER BY date_uts DESC", (timecut,)).fetchall()]

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
                scrobble_list += [[item[0], item[1]] for item in curFM.execute(f"SELECT artist_name, album_name FROM [{lfm_name}] WHERE date_uts > ? ORDER BY date_uts DESC", (timecut,)).fetchall()]

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
                        caption_dict[i] = f"{artist_name}"
                    else:
                        caption_dict[i] = f"{artist_name}\n{album_name}"

                if str(details).lower().strip() == "nsfw":
                    is_nsfw = True

        else:
            print("get cover images...")
            i = 0
            for item in count_list:
                i += 1
                if charttype == "artists":
                    artistcompact = item[0]
                    artist_name = artist_dict[artistcompact]
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
                    artist_name = aa_full[0]
                    album_name = aa_full[1]
                    caption_dict[i] = f"{artist_name}\n{album_name}"

                image_dict[i], details = await self.get_album_cover_url(ctx, artist_name, album_name)
                if str(details).lower().strip() == "nsfw":
                    is_nsfw = True

        return caption_dict, image_dict, user_name, is_nsfw



    async def parse_chart_list_from_api(self, response, charttype, lfm_name, top, check_list):
        caption_image_list = []
        rjson = response.json()
        i = len(check_list)

        if charttype == "artists":
            topartists = rjson['topartists']['artist']

            now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())

            for entry in topartists:
                artist = entry['name']
                mbid = 'mbid'

                image, update_time = await util.get_database_artistimage(artist)
                if image == "" or update_time < now - 30*24*60*60:
                    image = await util.get_spotify_artistimage(artist, lfm_name)

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

        """
        now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())

        async with ctx.typing():
            # PARSE ARGUMENTS

            print("chart command: parse args...")
            arg_dict = self.parse_topchart_args(ctx, args)

            top = arg_dict["top"]
            width = arg_dict["width"]
            height = arg_dict["height"]
            timecut = arg_dict["timecut"]
            scope = arg_dict["scope"]

            charttype = "albums"
            arg_dict["charttype"] = charttype

            if timecut <= 1000000000:
                timestring = "`all time`"
            else:
                timestring = f"<t:{timecut}:R>"

            # GET DATA

            print("chart command: fetch data...")
            try:
                caption_dict, image_dict, lfm_name, is_nsfw = await self.get_chart_data_from_api(ctx, arg_dict)
                fetched_from_api = True
            except Exception as e:
                print("API error while trying to fetch chart data:", e)
                caption_dict, image_dict, lfm_name, is_nsfw = await self.get_chart_data_from_db(ctx, arg_dict)
                fetched_from_api = False

            # MAKE CHART

            print("chart command: create image...")
            if is_nsfw:
                chart_name = f"SPOILER_chart_{ctx.author.id}_{now}"
            else:
                chart_name = f"chart_{ctx.author.id}_{now}"

            await self.create_chart(caption_dict, image_dict, chart_name, width, height)

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



    @commands.command(name='top', aliases = ["topartistchart", "topchart"])
    @commands.check(ScrobbleVisualsCheck.scrobbling_enabled)
    @commands.check(ScrobbleVisualsCheck.is_imagechart_enabled)
    @commands.check(util.is_active)
    async def _topartistchart(self, ctx: commands.Context, *args):
        """Shows chart of recent music
        
        Specify a time argument: week, month, quarter, half, year, alltime
        Specify a size in the format `3x3`, `4x5`, `10x10` etc.
        Ping a user to get their chart.
        """
        now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())

        async with ctx.typing():
            # PARSE ARGUMENTS

            print("top command: parse args...")
            arg_dict = self.parse_topchart_args(ctx, args)

            top = arg_dict["top"]
            width = arg_dict["width"]
            height = arg_dict["height"]
            timecut = arg_dict["timecut"]
            scope = arg_dict["scope"]

            charttype = "artists"
            arg_dict["charttype"] = charttype

            if timecut <= 1000000000:
                timestring = "`all time`"
            else:
                timestring = f"<t:{timecut}:R>"

            # GET DATA

            print("top command: fetch data...")
            try:
                caption_dict, image_dict, lfm_name, is_nsfw = await self.get_chart_data_from_api(ctx, arg_dict)
                fetched_from_api = True
            except Exception as e:
                print("API error while trying to fetch chart data:", e)
                caption_dict, image_dict, lfm_name, is_nsfw = await self.get_chart_data_from_db(ctx, arg_dict)
                fetched_from_api = False

            # MAKE CHART

            print("top command: create image...")
            if is_nsfw:
                chart_name = f"SPOILER_chart_{ctx.author.id}_{now}"
            else:
                chart_name = f"chart_{ctx.author.id}_{now}"

            await self.create_chart(caption_dict, image_dict, chart_name, width, height)

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



    



async def setup(bot: commands.bot) -> None:
    await bot.add_cog(
        Music_Scrobbling_Visuals(bot),
        guilds = [discord.Object(id = int(os.getenv("guild_id")))])
