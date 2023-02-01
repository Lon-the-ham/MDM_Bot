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



    @commands.command(name='convert', aliases = ['con','conv'])
    async def _convert(self, ctx, *args):
        """Converts units

        -con <number>F: Fahrenheit to Celsius
        -con <number>C: Celsius to Fahrenheit
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

        if len(args) > 0:
            #arg = args[0]
            #l = len(arg)
            #unit_one = arg[l-1:]
            #value_one = arg[:l-1]
            arg = ''.join(args)
            try:
                VaU_unfiltered = separate_number_chars(arg)
                VaU = [x for x in VaU_unfiltered if x]
                value_one = VaU[0]
                unit_one = VaU[1]
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
                        await ctx.send(f'Liters to Gallons ounces\n```{value_to_convert}l is about {converted_value}gal (US).\n(...or {converted_valueUK}gal (UK))```')
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

                else:
                    await ctx.send(f'Error: Unsupported unit.')
        else:
            await ctx.send(f'Missing argument for conversion.')
    @_convert.error
    async def convert_error(self, ctx, error, *args):
        await ctx.send(f'Some error ocurred <:seenoslowpoke:975062347871842324>\nCheck whether you do not use quotation marks or other characters that break discord... <:woozybread:976283266413908049>') 


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(
        Utility(bot),
        guilds = [discord.Object(id = 413011798552477716)])