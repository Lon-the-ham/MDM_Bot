import os
import datetime
import discord
from discord.ext import commands
import asyncio
import re
import time
import random
import sqlite3
from emoji import UNICODE_EMOJI
import functools
import itertools
import math
from async_timeout import timeout
import requests
from discord import app_commands


class Utility(commands.Cog):
    def __init__(self, bot: commands.Bot):
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

    #commands
    @commands.command(name='test')
    async def _test(self, ctx):
        """.

        The bot will reply with a message if online.
        """    
        await ctx.send(f'`I am online!`')


    @commands.command(name='restart', aliases = ['reboot'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(is_valid_server)
    async def _restart(self, ctx: commands.Context, *args):
        """*Restarts bot
        """
        #print('Will restart MDM Bot and Scylla & Charybdis Bot!')
        #await ctx.send('Will restart MDM Bot and Scylla & Charybdis Bot!')
        #subprocess.call(['sh', '/home/pi/bots/mdm/scylla/other/restart_multi_discord.sh'])
        await ctx.send('..in construction.. <:attention:961365426091229234>')


    @commands.command(name='status', aliases = ['setstat', 'setstatus'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(is_valid_server)
    async def _status(self, ctx: commands.Context, *args):
        """*Sets status

        first argument needs to be either:
        p (playing)
        s (streaming)
        w (watching)
        l (listening)

        n (none)
        """
        if len(args) >= 1:
            stat_type = args[0].lower()

            if len(args) >= 2:
                stat_name = ' '.join(args[1:])
            else:
                stat_name = ""

            if stat_type in ['p', 'playing', 'play']:
                # Setting `Playing ` status
                await self.bot.change_presence(activity=discord.Game(name=stat_name))
                await ctx.send(f'Changed status to:\nplaying {stat_name}')

            elif stat_type in ['s', 'streaming', 'stream']:                
                # Setting `Streaming ` status
                my_twitch_url = "https://www.twitch.tv/mdmbot/home"
                await self.bot.change_presence(activity=discord.Streaming(name=stat_name, url=my_twitch_url))
                await ctx.send(f'Changed status to:\nstreaming {stat_name}')

            elif stat_type in ['l', 'listening', 'listen']:
                # Setting `Listening ` status
                await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=stat_name))
                await ctx.send(f'Changed status to:\nlistening to {stat_name}')

            elif stat_type in ['w', 'watching', 'watch']:
                # Setting `Watching ` status
                await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=stat_name))
                await ctx.send(f'Changed status to:\nwatching {stat_name}')

            elif stat_type in ['n', 'none', 'reset', 'delete', 'remove']:
                await self.bot.change_presence(activity=None)
                await ctx.send(f'Removed status.')
            else:
                await ctx.send('did not recognise status type')
        else:
            ctx.send('no arguments given :(')
    @_status.error
    async def status_error(ctx, error, *args):
        if isinstance(error, commands.MissingPermissions):
            #print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
            await ctx.send(f'Sorry, you do not have permissions to do this!')
        elif isinstance(error, commands.BadArgument):
            #print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
            await ctx.send('Something went wrong... something something bad argument <:seenoslowpoke:975062347871842324>')
        else:
            #print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
            await ctx.send(f'Something seems to be wrong with your input <:pikathink:956603401028911124>')


 


    @commands.command(name='say', aliases = ['msg'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(is_valid_server)
    async def _say(self, ctx: commands.Context, *args):
        """*Messages given text

        Write -say <channel name> <message> to send an embedded message to this channel.
        """
        if len(args) <= 1:
            message = "Not enough arguments :("
            embed = discord.Embed(title="error", description=message, color=0x990000)
            await ctx.send(embed=embed)
        else:
            channel_found = False
            for channel in ctx.guild.text_channels:
                if str(channel.name).lower() == args[0].lower():
                    the_channel = channel
                    channel_found = True
                    break 

            if channel_found:
                message_string = ' '.join(args[1:]).replace('\\n', '\n')
                print("say-command for channel %s" % str(the_channel.name))

                if message_string[0] in ['[']:
                    print("building header")
                    message_parts = message_string[1:].split(']',1)
                    message_header = message_parts[0]
                    message_body = message_parts[1]
                else:
                    print("no header")
                    message_header = ""
                    message_body = message_string

                embed = discord.Embed(title=message_header, description=message_body, color=0x990000)
                await the_channel.send(embed=embed)
            else:
                message = "Text channel seems not to exist :("
                embed = discord.Embed(title="error", description=message, color=0x990000)
                await ctx.send(embed=embed)
    @_say.error
    async def say_error(ctx, error, *args):
        if isinstance(error, commands.MissingPermissions):
            #print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
            await ctx.send(f'Sorry, you do not have permissions to do this!')
        elif isinstance(error, commands.BadArgument):
            #print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
            await ctx.send('Something went wrong... something something bad argument <:seenoslowpoke:975062347871842324>')
        else:
            #print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
            await ctx.send(f'Something seems to be wrong with your input <:pikathink:956603401028911124>')


    @commands.command(name='react', aliases = ['reaction', 'reactions'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(is_valid_server)
    async def _react(self, ctx: commands.Context, *args):
        """*Add reactions

        Write -react <channel> <message id> <reactions> to add reactions to a message.
        """
        if len(args) <= 2:
            message = "Not enough arguments :("
            embed = discord.Embed(title="error", description=message, color=0x990000)
            await ctx.send(embed=embed)
        else:
            channel_found = False
            for channel in ctx.guild.text_channels:
                if str(channel.name).lower() == args[0].lower():
                    the_channel = channel
                    channel_found = True
                    break 

            if channel_found:
                msg_found = False
                message_id = args[1]
                try:
                    msg = await channel.fetch_message(message_id)
                    msg_found = True 
                    print(msg.content)
                except Exception as e:
                    print(e)

                if msg_found:
                    reaction_list = args[2:] #' '.join(args[2:]).replace(":", " ").split(" ")

                    print(reaction_list)
                    
                    for reaction in reaction_list:
                        try:
                            #emoji1 = discord.utils.get(ctx.guild.emojis, name = reaction) 
                            await msg.add_reaction(str(reaction))
                        except Exception as e:
                            print(e)
                            notif = "Could not send %s" % reaction
                            await ctx.send(notif)
                    
                else:
                    message = "Message seems to not exist :("
                    embed = discord.Embed(title="error", description=message, color=0x990000)
                    await ctx.send(embed=embed)
            else:
                message = "Channel not found :("
                embed = discord.Embed(title="error", description=message, color=0x990000)
                await ctx.send(embed=embed)
                ####
    @_say.error
    async def say_error(ctx, error, *args):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f'Sorry, you do not have permissions to do this!')


    @commands.command(name='qp', aliases = ['quickpoll'])
    async def _qp(self, ctx: commands.Context, *args):
        """quickpoll

        Default makes a message with 2 reacts: yes/no. with -qp <question> option: <list of things seperated by commas> you can do a different kind of poll.
        """
        optionslisted = False

        for arg in args:
            if ("options:" in arg) or ("Options:" in arg):
                optionslisted = True


        if optionslisted:
            wholetext = " ".join(args).replace("Options:", "options:")
            msgtext = wholetext.split("options:")[0]
            listingstext = wholetext.split("options:")[1]

            listings = listingstext.split(",")
            emojilist = ["🍎", "🍊", "🍋", "🍉", "🍇", "🫐", "🍑", "🍍", "🥥", "🥝", "🌽", "🥐", "🥨", "🥞", "🍕", "🍜", "🌮", "🍙", "🍮", "🥜"]

            optionstext = ""
            if len(listings) <= 20:
                for i in range(len(listings)):
                    optionstext = optionstext + emojilist[i] + " " + listings[i] + "\n"

                finalmessagetext = msgtext + "\n" + optionstext
                embed = discord.Embed(title="Quick poll:", description=finalmessagetext, color=0xFFBF00)
                embed.set_thumbnail(url="https://i.imgur.com/wFnxsyI.png")
                message = await ctx.send(embed=embed)

                for i in range(len(listings)):
                    await message.add_reaction(emojilist[i])
            else:
                await ctx.send(f'Error: Too many options. I can only do 20... <:pikacry:959405314220888104>')
        else:
            msgtext = "Quick poll: " + " ".join(args)
            message = await ctx.send(msgtext)
            await message.add_reaction('✅')
            await message.add_reaction('🚫')
    @_qp.error
    async def qp_error(self, ctx, error, *args):
        await ctx.send(f'Some error ocurred <:seenoslowpoke:975062347871842324>\nCheck whether you do not use quotation marks or other characters that break discord... <:woozybread:976283266413908049>') 



    @commands.command(name='roll', aliases = ['rng', 'die', 'random', 'dice', 'choose'])
    async def _dice(self, ctx: commands.Context, *args):
        """random number

        argument must be either one integer n > 1 (gives out random integer between 1 and n)
        or
        argument must be a set of options to choose from separated by semicolons
        or
        argument must be bl (optionally with category name behind (no spaces))

        (when no argument is given, the command gives out a random number between 1 and 6)
        """
        if len(args) > 0:
            ctext = ' '.join(args)
            if ';' in ctext or ',' in ctext:
                #ctext = ' '.join(args)
                if ';' in ctext:
                    options = ctext.split(';')
                    while "" in options:
                        options.remove("")
                    n = len(options)
                    if n > 1:
                        r = random.randint(1, n)
                        await ctx.send(f'🎲 D{n} roll: {options[r-1]}')
                    else:
                        await ctx.send(f'Error: There are not enough options to choose from <:piplupdisappointed:975461498702921778>')
                elif ',' in ctext:
                    options = ctext.split(',')
                    while "" in options:
                        options.remove("")
                    n = len(options)
                    if n > 1:
                        r = random.randint(1, n)
                        await ctx.send(f'🎲 D{n} roll: {options[r-1]}')
                    else:
                        await ctx.send(f'Error: There are not enough options to choose from <:piplupdisappointed:975461498702921778>')
                else:
                    # this should never trigger
                    await ctx.send(f'Error <:mildpanictiger:1066005100591579176> \noi <@586358910148018189> have a look at this mess')
            else:
                if len(args) == 1:
                    try:
                        n = int(args[0])
                        arg_is_integer = True
                    except:
                        n = 0 
                        arg_is_integer = False

                    if arg_is_integer:
                        if n > 1:
                            r = random.randint(1, n)
                            await ctx.send(f'🎲 D{n} roll: {r}')
                        else:
                            await ctx.send(f'Error: Argument should be an integer > 1.')

                    elif args[0].lower() in ['bl','backlog','memo']:
                        try:
                            conbg = sqlite3.connect('cogs/backlog/memobacklog.db')
                            curbg = conbg.cursor()
                            curbg.execute('''CREATE TABLE IF NOT EXISTS memobacklog (bgid text, userid text, username text, backlog text, details text)''')
                            
                            user = ctx.message.author
                            user_bg_list = [[item[0], item[1], item[2], item[3], item[4]] for item in curbg.execute("SELECT bgid, userid, username, backlog, details FROM memobacklog WHERE userid = ? ORDER BY bgid", (str(user.id),)).fetchall()]
                        
                            n = len(user_bg_list)
                            if n > 0:
                                r = random.randint(1, n)
                                rand_item = user_bg_list[r-1]
                                rand_bg_entry = rand_item[3]
                                await ctx.send(f'🎲 D{n}-bl roll says listen to: `{rand_bg_entry[:300]}`\n(index: {r})')
                            else:
                                await ctx.send(f'Seems like there is nothing in your backlog <:pikathink:956603401028911124>')
                        except Exception as e:
                            print(e)
                            await ctx.send(f'Some error ocurred <:mildpanictiger:1066005100591579176> \noi <@586358910148018189> have a look at this mess:```{e}```')
                    
                    elif args[0].lower() in ['blc','backlogcat','backlogcategory']:
                        try:
                            conbg = sqlite3.connect('cogs/backlog/memobacklog.db')
                            curbg = conbg.cursor()
                            curbg.execute('''CREATE TABLE IF NOT EXISTS memobacklog (bgid text, userid text, username text, backlog text, details text)''')
                            
                            user = ctx.message.author
                            user_bg_list = [[item[0], item[1], item[2], item[3], item[4]] for item in curbg.execute("SELECT bgid, userid, username, backlog, details FROM memobacklog WHERE userid = ? AND (LOWER(details) = ? OR details = ?) ORDER BY bgid", (str(user.id), 'default', '')).fetchall()]
                        
                            n = len(user_bg_list)
                            if n > 0:
                                r = random.randint(1, n)
                                rand_item = user_bg_list[r-1]
                                rand_bg_entry = rand_item[3]

                                full_bl_list = [item[3] for item in curbg.execute("SELECT bgid, userid, username, backlog, details FROM memobacklog WHERE userid = ? ORDER BY bgid", (str(user.id),)).fetchall()]
                                if rand_bg_entry in full_bl_list:
                                    index = str(full_bl_list.index(rand_bg_entry) + 1)
                                else:
                                    index = 'ERROR'
                                await ctx.send(f'🎲 D{n}-bl roll says listen to: `{rand_bg_entry[:300]}`\n(index: {index})')
                            else:
                                await ctx.send(f'Seems like there is nothing with category "default" in your backlog <:pikathink:956603401028911124>')
                        except Exception as e:
                            print(e)
                            await ctx.send(f'Some error ocurred <:mildpanictiger:1066005100591579176> \noi <@586358910148018189> have a look at this mess:```{e}```')
                    else:
                        multidicecommand = False 

                        dice = args[0].lower()
                        if "d" in dice:
                            number_and_sides = dice.split("d",1)
                            try:
                                num_of_dice = int(number_and_sides[0])
                                dice_size = int(number_and_sides[1])
                                multidicecommand = True
                            except:
                                ctx.send(f'Error: If you want to use a multiple dice command with `n`-many `x`-sided dice, then use -roll `n`d`x`.\nFor example -roll 6d20')

                        if multidicecommand:
                            if num_of_dice < 1:
                                await ctx.send(f'Error: Number of dice must be at least 1.')
                            elif dice_size < 2:
                                await ctx.send(f'Error: Dice/coins must be at least 2-sided.')
                            elif dice_size > 256:
                                await ctx.send(f'Error: Lmao how large do you want your dice to be. <:hamUmm:1017442919428395098>\nI can offer a D256 at most...')
                            elif num_of_dice > 24:
                                await ctx.send(f"Error: I'm sorry, but I only have 24 of these dice <a:catcrying:1017801138415874158>")
                            else:
                                n = num_of_dice
                                dice_rolls = []
                                while n >= 1:
                                    r = random.randint(1, dice_size)
                                    dice_rolls.append(r)
                                    n = n - 1
                                total = sum(dice_rolls)

                                await ctx.send(f"🎲 {num_of_dice}x D{dice_size} roll: {total} ({str(dice_rolls)[1:len(str(dice_rolls))-1]})")

                        else:
                            await ctx.send(f'Error: Argument must be either an integer > 1, a list of options separated by semicolons, `bl` or `blc categoryname`.')
                
                elif len(args) == 2 and args[0].lower() in ['bl','backlog','memo','blc','backlogcat','backlogcategory']:
                    cat = args[1]
                    L = len(cat)
                    print(f'cat input: {cat}')
                    if L > 2:
                        if cat[0] == '[' and cat[L-1] == ']':
                            cat = cat[1:L-1]
                            print(f'reduced cat to: {cat}')
                    try:
                        conbg = sqlite3.connect('cogs/backlog/memobacklog.db')
                        curbg = conbg.cursor()
                        curbg.execute('''CREATE TABLE IF NOT EXISTS memobacklog (bgid text, userid text, username text, backlog text, details text)''')
                        
                        user = ctx.message.author
                        if cat.lower() in ["", "default"]:
                            user_bg_list = [[item[0], item[1], item[2], item[3], item[4]] for item in curbg.execute("SELECT bgid, userid, username, backlog, details FROM memobacklog WHERE userid = ? AND (LOWER(details) = ? OR details = ?) ORDER BY bgid", (str(user.id), 'default', '')).fetchall()]
                        else:
                            user_bg_list = [[item[0], item[1], item[2], item[3], item[4]] for item in curbg.execute("SELECT bgid, userid, username, backlog, details FROM memobacklog WHERE userid = ? AND LOWER(details) = LOWER(?) ORDER BY bgid", (str(user.id),cat)).fetchall()]
                    
                        n = len(user_bg_list)
                        if n > 0:
                            r = random.randint(1, n)
                            rand_item = user_bg_list[r-1]
                            rand_bg_entry = rand_item[3]

                            full_bl_list = [item[3] for item in curbg.execute("SELECT bgid, userid, username, backlog, details FROM memobacklog WHERE userid = ? ORDER BY bgid", (str(user.id),)).fetchall()]
                            if rand_bg_entry in full_bl_list:
                                index = str(full_bl_list.index(rand_bg_entry) + 1)
                            else:
                                index = 'ERROR'

                            await ctx.send(f'🎲 D{n}-bl roll says listen to: `{rand_bg_entry[:300]}`\n(index: {index})')
                        else:
                            await ctx.send(f'Seems like there is nothing with category "{cat}" in your backlog <:pikathink:956603401028911124>')
                    except Exception as e:
                        print(e)
                        await ctx.send(f'Some error ocurred <:mildpanictiger:1066005100591579176> \noi <@586358910148018189> have a look at this mess:```{e}```')
                else:
                    await ctx.send(f'Argument must be either an integer > 1, a list of options separated by semicolons, `bl` or `blc categoryname`. <:gengarfeels:752263420820062224>')               
        else:
            r = random.randint(1, 6)
            await ctx.send(f'🎲 D6 roll: {r}')
    @_dice.error
    async def dice_error(self, ctx, error, *args):
        await ctx.send(f'Some error ocurred <:seenoslowpoke:975062347871842324>\nCheck whether you do not use quotation marks or other characters that break discord... <:woozybread:976283266413908049>')         



    @commands.command(name='convert', aliases = ['con','conv'])
    async def _convert(self, ctx, *args):
        """Converts units

        -con <number>F: Fahrenheit to Celsius
        -con <number>C: Celsius to Fahrenheit

        currently supported are temperature (C,F), length/distances (km,m,cm,mi,yd,ft,in also 5'11" notation), speed (kmh,mph), weight/mass (lbs,oz,kg,g), volume (gal,ukgal,fl oz,cup,l,cl,ml), area (acre,sqm)
        and 
        also currencies, for which you can use "to"
        -con <number> USD to EUR CHF 
        if you leave the "to" out it will give out USD, EUR, GPB, JPY
        """
        def is_number(s):
            try:
                float(s)
                return True
            except ValueError:
                return False

        def separate_number_chars(s):
            res = re.split('([-+]?\d+\.\d+)|([-+]?\d+)', s.strip())
            res_f = [r.strip() for r in res if r is not None and r.strip() != '']
            return res_f

        def alphanumonly(s):
            result = "".join(e for e in s if e.isalnum())
            return result

        other_currency_symbols = ["€","円","¥","$","£","EURO","EUROS","DOLLAR","DOLLARS","USDOLLAR","USDOLLARS","YEN","YENS","POUND","POUNDS","QUID","QUIDS"]
        def currency_symbol_converter(s):
            if s in other_currency_symbols:
                if s in ["€","EURO","EUROS"]:
                    return "EUR"
                elif s in ["円","¥","YEN","YENS"]:
                    return "JPY"
                elif s in ["$","DOLLAR","DOLLARS","USDOLLAR","USDOLLARS"]:
                    return "USD"
                elif s in ["£","POUND","POUNDS","QUID","QUIDS"]:
                    return "GBP"
                else:
                    return "ERROR"
            else:
                return s.upper()

        if len(args) > 0:
            #arg = args[0]
            #l = len(arg)
            #unit_one = arg[l-1:]
            #value_one = arg[:l-1]
   

            #divide in from_convert and to_convert
            from_arguments = []
            to_arguments = []
            found_to_separator = False
            for arg in args:
                if arg.lower() == "to":
                    found_to_separator = True
                elif found_to_separator:
                    to_arguments.append(arg)
                else:
                    from_arguments.append(arg)

            #parse from_convert
            argument_string = ''.join(from_arguments)
            try:
                VaU_unfiltered = separate_number_chars(argument_string)
                VaU = [x for x in VaU_unfiltered if x]
                value_one = VaU[0]
                unit_one = VaU[1]
                if is_number(value_one) == False and is_number(unit_one) == True:
                    value_one = VaU[1]
                    unit_one = VaU[0]
                parsing_worked = True
            except:
                parsing_worked = False
                await ctx.send(f'Error: Parsing value and unit crashed. <:derpy:955227738690687048>')

            if parsing_worked:

                # TEMPERATURE
                if unit_one.lower() in ["f","fahrenheit", "°f"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        converted_value = round((value_to_convert-32) * 5/9,1)
                        await ctx.send(f'Fahrenheit to Celsius\n```{value_to_convert}F is about {converted_value}C.```')
                    except:
                        await ctx.send(f'Error: Fahrenheit to Celsius computation crashed. <:derpy:955227738690687048>')
                elif unit_one.lower() in ["c","celsius", "°c"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        converted_value = round(value_to_convert * 9/5 + 32,1)
                        await ctx.send(f'Celsius to Fahrenheit\n```{value_to_convert}C is about {converted_value}F.```')
                    except:
                        await ctx.send(f'Error: Celsius to Fahrenheit computation crashed. <:derpy:955227738690687048>')

                # LENGTH/DISTANCE
                elif  unit_one.lower() in ["mi","miles", "mile"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        converted_value = round((value_to_convert) * 1.609344,1)
                        await ctx.send(f'Miles to Kilometers\n```{value_to_convert}mi is about {converted_value}km.```')
                    except:
                        await ctx.send(f'Error: Miles to Kilometers computation crashed. <:derpy:955227738690687048>')
                elif  unit_one.lower() in ["km","kilometer", "kilometers", "kilometre", "kilometres"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        converted_value = round((value_to_convert)/1.609344,1)
                        await ctx.send(f'Kilometers to Miles\n```{value_to_convert}km is about {converted_value}mi.```')
                    except:
                        await ctx.send(f'Error: Kilometers to Miles computation crashed. <:derpy:955227738690687048>')

                elif  unit_one.lower() in ["ft","feet", "foot", "'"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        converted_value = round((value_to_convert) * 0.3048,2)
                        if len(VaU) > 2:
                            value_two = VaU[2]
                            if is_number(value_two):
                                converted_value2 = round((100 * converted_value + (float(value_two) * 2.54))/100,2)
                                if value_to_convert == math.floor(value_to_convert) and float(value_two) == math.floor(float(value_two)):
                                    await ctx.send(f'Feet to Meters\n```{math.floor(value_to_convert)}ft {math.floor(float(value_two))}inch is about {converted_value2:.2f}m.```')
                                else:
                                    await ctx.send(f'Feet to Meters\n```{value_to_convert}ft {float(value_two)}inch is about {converted_value2:.2f}m.```')
                            else:
                                await ctx.send(f'Error: Second value is faulty. <:pikathink:956603401028911124>')
                                await ctx.send(f'Feet to Meters\n```{value_to_convert}ft is about {converted_value}m.```')
                        else:
                            await ctx.send(f'Feet to Meters\n```{value_to_convert}ft is about {converted_value}m.```')
                    except Exception as e:
                        print(e)
                        await ctx.send(f'Error: Feet to Meters computation crashed. <:derpy:955227738690687048>')
                        channel = bot.get_channel(416384984597790750)
                        await channel.send(f'Error message:\n{e}')
                elif  unit_one.lower() in ["m","meter", "meters", "metre", "metres"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        #converted_value = round((value_to_convert)/0.3048,1)
                        #await ctx.send(f'Meters to Feet\n```{value_to_convert}m is about {converted_value}ft.```')
                        converted_value = round((100 * value_to_convert)/2.54,1)
                        if converted_value >= 12 * 9:
                            conv_yard = round(((100 * value_to_convert)/2.54)/(12*3),1)
                            await ctx.send(f'Meters to Yards\n```{value_to_convert}m is about {conv_yard}yards.```')
                        elif converted_value >= 12:
                            conv_feet = converted_value // 12
                            conv_inch = round(converted_value - (conv_feet * 12),1)
                            await ctx.send(f'Meters to Feet/Inch\n```{value_to_convert}m is about {conv_feet}ft {conv_inch}inch. \n({converted_value} inch)```')
                        else:
                            await ctx.send(f'Meters to Inch\n```{value_to_convert}m is about {converted_value}inch.```')
                    except:
                        await ctx.send(f'Error: Meters to Feet/Inch computation crashed. <:derpy:955227738690687048>')
                elif unit_one.lower() in ["yd","yard","yards"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        converted_value = round((value_to_convert) * 0.9144,1)
                        await ctx.send(f'Yards to Meter\n```{value_to_convert}yd is about {converted_value}m.```')
                    except:
                        await ctx.send(f'Error: Yards to Meter computation crashed. <:derpy:955227738690687048>')

                elif  unit_one.lower() in ["in","inch","zoll","inches","inchs"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        converted_value = round((value_to_convert) * 2.54,1)
                        await ctx.send(f'Inch to Centimeters\n```{value_to_convert}inch is about {converted_value}cm.```')
                    except:
                        await ctx.send(f'Error: Inch to Centimeters computation crashed. <:derpy:955227738690687048>')
                elif  unit_one.lower() in ["cm", "centimeters", "centimetres", "centimeter", "centimetre"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        converted_value = round((value_to_convert)/2.54,1)
                        if converted_value >= 12:
                            conv_feet = converted_value // 12
                            conv_inch = round(converted_value - (conv_feet * 12),1)
                            await ctx.send(f'Centimeters to Feet/Inch\n```{value_to_convert}cm is about {conv_feet}ft {conv_inch}inch. \n({converted_value} inch)```')
                        else:
                            await ctx.send(f'Centimeters to Inch\n```{value_to_convert}cm is about {converted_value}inch.```')
                    except:
                        await ctx.send(f'Error: Inches to Centimeters computation crashed. <:derpy:955227738690687048>')

                # SPEED
                elif  unit_one.lower() in ["mph","milesperhour","miph","mileperhour"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        converted_value = round((value_to_convert) * 1.609344,1)
                        await ctx.send(f'Miles per hour to Kilometers per hour\n```{value_to_convert}mph is about {converted_value}km/h.```')
                    except:
                        await ctx.send(f'Error: Mph to km/h computation crashed. <:derpy:955227738690687048>')
                elif  unit_one.lower() in ["kmh","km/h","kmph","kilometersperhour","kilometerperhour"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        converted_value = round((value_to_convert) / 1.609344,1)
                        await ctx.send(f'Kilometers per hour to Miles per hour\n```{value_to_convert}km/h is about {converted_value}mph.```')
                    except:
                        await ctx.send(f'Error: Km/h to mph computation crashed. <:derpy:955227738690687048>')

                # WEIGHT/MASS
                elif unit_one.lower() in ["lbs", "pound", "pounds", "lb", "pds", "pd", "libra", "libras"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        converted_value = round((value_to_convert) * 0.45359237,2)
                        await ctx.send(f'Pounds to Kilograms\n```{value_to_convert}lbs is about {converted_value}kg.```')
                    except:
                        await ctx.send(f'Error: Pounds to Kilograms computation crashed. <:derpy:955227738690687048>')
                elif unit_one.lower() in ["kg", "kilogram", "kgs", "kilograms", "kilogramms", "kilogramm"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        converted_value = round((value_to_convert) * 2.20462262185,1)
                        await ctx.send(f'Pounds to Kilograms\n```{value_to_convert}kg is about {converted_value}lbs.```')
                    except:
                        await ctx.send(f'Error: Pounds to Kilograms computation crashed. <:derpy:955227738690687048>')

                elif unit_one.lower() in ["oz", "ounce", "ounces"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        converted_value = round((value_to_convert) * 28.34952,1)
                        await ctx.send(f'Ounces to Grams\n```{value_to_convert}oz is about {converted_value}g.```\n(for volume/fluid ounces use "foz")')
                    except:
                        await ctx.send(f'Error: Ounces to Grams computation crashed. <:derpy:955227738690687048>')
                elif unit_one.lower() in ["g", "gram", "grams", "gramm", "gramms"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        converted_value = round((value_to_convert) * 0.03527396195,2)
                        await ctx.send(f'Grams to Ounces\n```{value_to_convert}oz is about {converted_value}g.```')
                    except:
                        await ctx.send(f'Error: Grams to Ounces computation crashed. <:derpy:955227738690687048>')

                # VOLUME
                elif unit_one.lower() in ["foz", "ozf", "floz", "ozfl", "fluidounce", "fluidounces", "loz", "voz", "liquidounce", "luiquidounces", "volumeounce", "volumeounces"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        converted_value = round((value_to_convert) * 29.5735296875,1)
                        await ctx.send(f'Fluid ounces to Milliliters\n```{value_to_convert}oz (fluid) is about {converted_value}ml.```')
                    except:
                        await ctx.send(f'Error: Fluid ounces to Milliliters computation crashed. <:derpy:955227738690687048>')
                elif unit_one.lower() in ["ml", "milliliter", "milliliters", "millilitre", "millilitres", "mililiter", "mililiters", "mililitre", "mililitres"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        converted_value = round((value_to_convert) * 0.03381402,2)
                        await ctx.send(f'Milliliters to Fluid ounces\n```{value_to_convert}ml is about {converted_value}oz (fluid).```')
                    except:
                        await ctx.send(f'Error: Milliliters to Fluid ounces computation crashed. <:derpy:955227738690687048>')
                elif unit_one.lower() in ["cl", "centiliter", "centiliters", "centilitre", "centilitres"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        converted_value = round((value_to_convert) * 0.3381402,2)
                        await ctx.send(f'Centiliters to Fluid ounces\n```{value_to_convert}cl is about {converted_value}oz (fluid).```')
                    except:
                        await ctx.send(f'Error: Centiliters to Fluid ounces computation crashed. <:derpy:955227738690687048>')

                elif unit_one.lower() in ["l", "liter", "liters", "litre", "litres"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        converted_value = round((value_to_convert) * 0.2641720524,1)
                        converted_valueUK = round((value_to_convert) * 0.21996923465436,1)
                        await ctx.send(f'Liters to Gallons\n```{value_to_convert}l is about {converted_value}gal (US).\n(...or {converted_valueUK}gal (UK))```')
                    except:
                        await ctx.send(f'Error: Liters to Gallons computation crashed. <:derpy:955227738690687048>')
                elif unit_one.lower() in ["gal", "gallon", "gallons", "galon", "galons", "galus", "usgal", "usgallon", "usgallons", "gallonus", "gallonsus"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        converted_value = round((value_to_convert) * 3.785411784,1)
                        converted_valueUK = round((value_to_convert) * 0.8326741881485,1)
                        await ctx.send(f'US Gallons to Liters\n```{value_to_convert}gal (US) is about {converted_value}l.\n(...or {converted_valueUK}gal (UK))```(for UK Gallons use "ukgal")')
                    except:
                        await ctx.send(f'Error: US Gallons to Liters computation crashed. <:derpy:955227738690687048>')
                elif unit_one.lower() in ["ukgal", "ukgallon", "ukgallons", "ukgalon", "ukgalons", "galuk", "gallonuk", "gallonsuk"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        converted_value = round((value_to_convert) * 4.5460902819948,1)
                        converted_valueUS = round((value_to_convert) * 1.2009499204287,1)
                        await ctx.send(f'UK Gallons to Liters\n```{value_to_convert}gal (UK) is about {converted_value}l.\n(...or {converted_valueUS}gal (US))```')
                    except:
                        await ctx.send(f'Error: UK Gallons to Liters computation crashed. <:derpy:955227738690687048>')

                elif unit_one.lower() in ["cup", "cups", "uscup", "uscups", "cupus", "cupsus"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        converted_value_pre = round((value_to_convert) * 236.5882365,1)
                        if converted_value_pre > 1000:
                            converted_value_l = round((converted_value_pre)/1000,3)
                            await ctx.send(f'Cups (US) to Liters\n```{value_to_convert}cup is about {converted_value_l}l.```')
                        else:
                            converted_value_ml = int(round((converted_value_pre),0))
                            await ctx.send(f'Cups (US) to Liters\n```{value_to_convert}cup is about {converted_value_ml}ml.```')
                    except:
                        await ctx.send(f'Error: Cups (US) to Liters computation crashed. <:derpy:955227738690687048>')

                # AREA
                elif unit_one.lower() in ["acre", "a", "acres", "acer", "acers"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        converted_value = round((value_to_convert) * 4046.8564224,1)
                        await ctx.send(f'Acres to square meters ounces\n```{value_to_convert}acres is about {converted_value}m².```')
                    except:
                        await ctx.send(f'Error: Acres to square meters computation crashed. <:derpy:955227738690687048>')

                elif unit_one.lower() in ["sqm", "m²", "squaremeter", "squaremeters", "squaremetre", "squaremetres"] and is_number(value_one):
                    try:
                        value_to_convert = float(value_one)
                        if value_to_convert > 4046:
                            converted_value = round((value_to_convert) / 4046.8564224,1)
                        elif value_to_convert < 10:
                            converted_value = round((value_to_convert) / 4046.8564224,4)
                        elif value_to_convert < 81:
                            converted_value = round((value_to_convert) / 4046.8564224,3)
                        else:
                            converted_value = round((value_to_convert) / 4046.8564224,2)
                        await ctx.send(f'Acres to square meters ounces\n```{value_to_convert}acres is about {converted_value}m².```')
                    except:
                        await ctx.send(f'Error: Acres to square meters computation crashed. <:derpy:955227738690687048>')

                
                # CURRENCY - ONE IF-THEN-ELSE LEVEL HIGHER (to not load DB if not needed)
                else:

                    crypto_currencies = ["BTC","BITCOIN", "ETH", "ETHER", "ETHEREUM", "USDT", "TETHER", "BNB", "USDC", "USDCOIN", "XRP", "BUSD", "BINANCEUSD", "BINANCE", "ADA", "CARDANO"]
                    
                    # CRYPTO CURRENCY
                    if unit_one.upper() in crypto_currencies:
                        await ctx.send(f'Ugh crypto... <:hidethepainharold:976988848414404638>\nNot supported, sorry.')


                    else:
                        # ACTUAL CURRENCY
                        try:
                            con = sqlite3.connect('cogs/utility/currency/exchangerate.db')
                            cur = con.cursor()
                            cur.execute('''CREATE TABLE IF NOT EXISTS USDexchangerate (code text, value text, currency text, country text, last_updated text, time_stamp text)''')
                            data = [[item[0],item[1],item[2],item[3],item[4]] for item in cur.execute("SELECT code, value, currency, country, last_updated FROM USDexchangerate").fetchall()]
                            
                            currency_codes = []
                            currency_names = []
                            for item in data:
                                if item[0] != "":
                                    currency_codes.append(item[0])
                                if item[2] != "":
                                    currency_names.append(alphanumonly(item[2]).upper())

                            currencies = currency_codes + currency_names
                            #loaded_database = True
                        except:
                            currency_codes = ['AED','AFN','ALL','AMD','ANG','AOA','ARS','AUD','AWG','AZN','BAM','BBD','BDT','BGN','BHD','BIF','BMD','BND','BOB','BRL','BSD','BTN','BWP','BYN','BZD','CAD','CDF','CHF','CLP','CNY','COP','CRC','CUP','CVE','CZK','DJF','DKK','DOP','DZD','EGP','ERN','ETB','EUR','FJD','FKP','FOK','GBP','GEL','GGP','GHS','GIP','GMD','GNF','GTQ','GYD','HKD','HNL','HRK','HTG','HUF','IDR','ILS','IMP','INR','IQD','IRR','ISK','JEP','JMD','JOD','JPY','KES','KGS','KHR','KID','KMF','KRW','KWD','KYD','KZT','LAK','LBP','LKR','LRD','LSL','LYD','MAD','MDL','MGA','MKD','MMK','MNT','MOP','MRU','MUR','MVR','MWK','MXN','MYR','MZN','NAD','NGN','NIO','NOK','NPR','NZD','OMR','PAB','PEN','PGK','PHP','PKR','PLN','PYG','QAR','RON','RSD','RUB','RWF','SAR','SBD','SCR','SDG','SEK','SGD','SHP','SLE','SOS','SRD','SSP','STN','SYP','SZL','THB','TJS','TMT','TND','TOP','TRY','TTD','TVD','TWD','TZS','UAH','UGX','USD','UYU','UZS','VES','VND','VUV','WST','XAF','XCD','XDR','XOF','XPF','YER','ZAR','ZMW','ZWL']
                            currency_names = []
                            currencies = currency_codes
                            #loaded_database = False
                            print("error: fetching data from currency DB failed")
                            #await ctx.send(f'Error while loading currency exchange database. <:piplupdisappointed:975461498702921778>')

                        currencies += other_currency_symbols #defined at the beginning
                     
                        
                        # ACTUAL CURRENCY
                        input_unit = unit_one.upper()
                        if input_unit in currencies:
                            # if the currency is spelled out in full convert it to code first
                            try:
                                input_unit_alphanum = alphanumonly(input_unit)
                                if input_unit_alphanum in currency_names:
                                    for item in data:
                                        item_currency_name = alphanumonly(item[2]).upper()
                                        if item_currency_name == input_unit_alphanum and item_currency_name != "":
                                            unit_one = item[0]
                                            break
                            except:
                                print("error in converting currency name to its code")

                            # start conversion
                            try:
                                value_to_convert = float(value_one)
                                currency_from = currency_symbol_converter(unit_one)
                                #con = sqlite3.connect('cogs/utility/currency/exchangerate.db')
                                #cur = con.cursor()
                                #cur.execute('''CREATE TABLE IF NOT EXISTS USDexchangerate (code text, value text, currency text, country text, last_updated text, time_stamp text)''')
                                #data = [[item[0],item[1],item[2],item[3],item[4]] for item in cur.execute("SELECT code, value, currency, country, last_updated FROM USDexchangerate").fetchall()]

                                for currency in data:
                                    currency_code = currency[0]
                                    if currency_from == currency_code:
                                        currency_value = currency[1]
                                        currency_name = currency[2]
                                        currency_country = currency[3]
                                        last_updated = currency[4]
                                        break

                                print(currency_code)
                                print(currency_value)
                                print(currency_name)
                                print(currency_country)
                                print(last_updated)
                                message = f"{currency_name} currency conversion\n"
                                message += "```\n"
                                message += f"{value_one} {currency_code} are about...\n"

                                #these currencies do not get rounded to 1/100 but to 1
                                largenominalcurrencies = ["JPY"] 

                                if len(to_arguments) == 0:
                                    # just convert to USD, EUR, GBP and JPY
                                    for convert_to in ["USD", "EUR", "GBP", "JPY"]:
                                        if currency_code == convert_to:
                                            pass
                                        else:
                                            for currency in data:
                                                convert_code = currency[0]
                                                if convert_code == convert_to:
                                                    convert_value = currency[1]
                                                    break
                                            print(convert_code)
                                            if convert_to in largenominalcurrencies:
                                                #n = 0
                                                conversion = int(round(float(value_one)*float(convert_value)/float(currency_value),0))
                                            else:
                                                #n = 2
                                                conversion = round(float(value_one)*float(convert_value)/float(currency_value),2)
                                            #conversion = round(float(value_one)*float(convert_value)/float(currency_value),n)
                                            print(conversion)
                                            message += f"    {conversion} {convert_code}\n"
                                    message += "```" + f"as per {last_updated}"
                                    await ctx.send(message)
                                else:
                                    # convert multiple
                                    error = ""
                                    valid_conversion_currency_found = False
                                    for arg in to_arguments:
                                        if arg.upper() in currencies:
                                            convert_to = currency_symbol_converter(arg)
                                            for currency in data:
                                                convert_code = currency[0]
                                                if convert_code == convert_to:
                                                    convert_value = currency[1]
                                                    break
                                            print(convert_code)
                                            if convert_to in largenominalcurrencies:
                                                #n = 0
                                                conversion = int(round(float(value_one)*float(convert_value)/float(currency_value),0))
                                            else:
                                                #n = 2
                                                conversion = round(float(value_one)*float(convert_value)/float(currency_value),2)
                                            #conversion = round(float(value_one)*float(convert_value)/float(currency_value),n)
                                            print(conversion)
                                            message += f"    {conversion} {convert_code}\n"
                                            valid_conversion_currency_found = True
                                        elif arg.upper() in crypto_currencies:
                                            error += f" ...{arg.upper()} is not supported <:batwelp:1019018908570746880>\n"
                                        else:
                                            error += f" ...{arg.upper()} I do not know <:seenootter:1017786849084854393>\n"
                                    
                                    if valid_conversion_currency_found:
                                        message += "```" + f"as per {last_updated}\n\n" + error
                                    else:
                                        message = f"{currency_name} currency conversion\n"
                                        message += "none of the given exchange currencies were recognised... :("
                                    await ctx.send(message[:4096])
                            except Exception as e:
                                await ctx.send(f'Error: Currency conversion crashed. <:charmanderpy:1014855943177113673>\n{e}')
                    
                        else:
                            await ctx.send(f'Error: Unsupported unit. <:pikathink:956603401028911124>')
        else:
            await ctx.send(f'Missing argument for conversion.')
    @_convert.error
    async def convert_error(self, ctx, error, *args):
        await ctx.send(f'Some error ocurred <:seenoslowpoke:975062347871842324>\nCheck whether you do not use quotation marks or other characters that break discord... <:woozybread:976283266413908049>') 
























async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(
        Utility(bot),
        guilds = [discord.Object(id = 413011798552477716)])