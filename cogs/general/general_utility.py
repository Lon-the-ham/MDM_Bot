import discord
from discord.ext import commands
import datetime
import pytz
from other.utils.utils import Utils as util
import os
import asyncio
import random
import re
from collections import OrderedDict
import sqlite3
import math
import requests
from emoji import UNICODE_EMOJI
from langdetect import detect

import traceback

try:
    from googletrans import Translator
    googletrans_enabled = True
except:
    print("Not importing Google Translator library")
    googletrans_enabled = False

try:
    import asyncpraw
    try:
        import asyncprawcore
        reddit_enabled = True
    except:
        print("Not importing AsyncPrawCore (Reddit) library")
        reddit_enabled = False
except:
    print("Not importing AsyncPraw (Reddit) library")
    reddit_enabled = False

try:
    from openai import OpenAI
    gpt_enabled = True
except:
    print("Not importing OpenAI library")
    gpt_enabled = False



class GU_Check():
    def is_googletrans_enabled(*ctx):
        if googletrans_enabled:
            return True
        else:
            return False
            #raise ValueError("GoogleTranslate module was not imported.")

    def is_reddit_enabled(*ctx):
        if reddit_enabled:
            return True
        else:
            return False
            #raise ValueError("AsyncPraw module (for Reddit) was not imported.")

    def is_gpt_enabled(*ctx):
        if gpt_enabled:
            return True
        else:
            return False
            #raise ValueError("OpenAI module was not imported.")


class General_Utility(commands.Cog):
    def __init__(self, bot: commands.bot) -> None:
        self.bot = bot
        self.prefix = os.getenv("prefix")



    @commands.command(name='test')
    @commands.check(util.is_active)
    async def _test(self, ctx):
        """check availability

        The bot will reply with a message if online and active.
        """    
        await ctx.send(f'`I am online!`')
        
    @_test.error
    async def test_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='version', aliases = ["v"])
    @commands.check(util.is_active)
    async def _botversion(self, ctx):
        """shows version of the bot
        """    
        version = util.get_version()
        await ctx.send(f"MDM Bot {version}")
    @_botversion.error
    async def botversion_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='say', aliases = ['msg'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _say(self, ctx: commands.Context, *args):
        """🔒 Messages given text

        Write `<prefix>say <channel name> <message>` to send an embedded message to this channel.
        Use `<prefix>say <channel name> [<header>] <message>` to give it a title as well.
        """
        if len(args) <= 1:
            message = "Not enough arguments :("
            embed = discord.Embed(title="error", description=message, color=0x990000)
            await ctx.send(embed=embed)
            return

        channel_found = False
        for channel in ctx.guild.text_channels:
            if f"<#{channel.id}>" == args[0].lower():
                the_channel = channel
                channel_found = True
                break 
        else:
            for channel in ctx.guild.text_channels:
                if str(channel.id) == args[0].lower():
                    the_channel = channel
                    channel_found = True
                    break 
            else:
                for channel in ctx.guild.text_channels:
                    if str(channel.name).lower() == args[0].lower():
                        the_channel = channel
                        channel_found = True
                        break 

        if not channel_found:
            message = "Text channel seems not to exist :("
            embed = discord.Embed(title="error", description=message, color=0x990000)
            await ctx.send(embed=embed)
            return

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

    @_say.error
    async def say_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='react', aliases = ['reaction', 'reactions'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _react(self, ctx: commands.Context, *args):
        """🔒 Add reactions

        Write <prefix>react <channel> <message id> <reactions> to add reactions to a message.
        """
        if len(args) <= 2:
            message = "Not enough arguments :("
            embed = discord.Embed(title="error", description=message, color=0x990000)
            await ctx.send(embed=embed)
            return
        
        channel_found = False
        for channel in ctx.guild.text_channels:
            if f"<#{channel.id}>" == args[0].lower():
                the_channel = channel
                channel_found = True
                break 
        else:
            for channel in ctx.guild.text_channels:
                if str(channel.id) == args[0].lower():
                    the_channel = channel
                    channel_found = True
                    break 
            else:
                for channel in ctx.guild.text_channels:
                    if str(channel.name).lower() == args[0].lower():
                        the_channel = channel
                        channel_found = True
                        break 

        if not channel_found:
            message = "Channel not found :("
            embed = discord.Embed(title="error", description=message, color=0x990000)
            await ctx.send(embed=embed)
            return 

        msg_found = False
        message_id = args[1]
        try:
            msg = await channel.fetch_message(message_id)
            msg_found = True 
            print(msg.content)
        except Exception as e:
            print(e)

        if not msg_found:
            message = "Message seems to not exist :("
            embed = discord.Embed(title="error", description=message, color=0x990000)
            await ctx.send(embed=embed)
            return 

        reaction_list = args[2:]
        for reaction in reaction_list:
            try:
                await msg.add_reaction(str(reaction))
            except Exception as e:
                for emoji in self.bot.emojis:
                    if f":{emoji.name}:" == reaction:
                        try:
                            await msg.add_reaction(str(reaction))
                            break
                        except:
                            print(f"Could not send reaction: {reaction}")
    @_react.error
    async def react_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='quickpoll', aliases = ['qp'])
    @commands.check(util.is_active)
    async def _qp(self, ctx: commands.Context, *args):
        """Quickpoll

        Default adds 2 reacts: yes/no. 
        With `<prefix>qp <question> options: <list of things seperated by commas>` you can create an embed with up to 20 options.

        (🔒 By making the 1st argument a #channel mention you can send it over to that channel.)
        """
        if len(args) < 1:
            await ctx.send("What do you want to poll?")
            return 

        channel = ctx.channel
        otherchannel = False
        is_main_server = util.is_main_server(ctx)
        if is_main_server:
            try:
                member_id = ctx.message.author.id
                member = ctx.guild.get_member(member_id)
                if ("manage_guild",True) in member.guild_permissions:
                    if args[0].startswith("<#") and args[0].endswith(">"):
                        channel_id = args[0].replace("<#","").replace(">","")
                        try:
                            channel = self.bot.get_channel(int(channel_id))
                            otherchannel = True
                        except:
                            channel = ctx.channel
                            otherchannel = True
            except Exception as e:
                print(e)
                otherchannel = False

        optionslisted = False
        for arg in args:
            if ("options:" in arg) or ("Options:" in arg):
                optionslisted = True

        if not optionslisted:
            if otherchannel:
                msgtext = "Quick poll: " + " ".join(args[1:])
                message = await channel.send(msgtext)
                await message.add_reaction('✅')
                await message.add_reaction('🚫')
                return

            await ctx.message.add_reaction('✅')
            await ctx.message.add_reaction('🚫')
            return

        wholetext = " ".join(args).replace("Options:", "options:")
        msgtext = wholetext.split("options:")[0]
        listingstext = wholetext.split("options:")[1]

        listings = listingstext.split(",")
        emojilist = ["🍎", "🍊", "🍋", "🍉", "🍇", "🫐", "🍑", "🍍", "🥥", "🥝", "🌽", "🥐", "🥨", "🥞", "🍕", "🍜", "🌮", "🍙", "🍮", "🥜"]

        optionstext = ""
        if len(listings) > 20:
            emoji = util.emoji("sob")
            await ctx.send(f'Error: Too many options. I can only do 20... {emoji}')
            return

        for i in range(len(listings)):
            optionstext = optionstext + emojilist[i] + " " + listings[i] + "\n"

        finalmessagetext = msgtext + "\n" + optionstext
        embed = discord.Embed(title="Quick poll:", description=finalmessagetext, color=0xFFBF00)
        embed.set_thumbnail(url="https://i.imgur.com/wFnxsyI.png")
        message = await channel.send(embed=embed)

        for i in range(len(listings)):
            await message.add_reaction(emojilist[i])

    @_qp.error
    async def qp_error(self, ctx, error):
        await util.error_handling(ctx, error)


    


    ############################# ROLL #######################################################################################################################



    @commands.command(name='roll', aliases = ['rng', 'die', 'random', 'dice', 'choose'])
    @commands.check(util.is_active)
    async def _dice(self, ctx: commands.Context, *args):
        """RNG command

        Gives out random number or choice depending on the argument.

        Argument can be either one integer n > 1 -> gives out random integer between 1 and n.
        or
        Argument can be a set of options to choose from separated by semicolons -> chooses one of those options.
        or
        Argument can be `bl`, `blc` or `blx` (optionally with category name behind (no spaces)) -> chooses random item from your backlog.
        or
        Argument can be multiple die rolls with syntax `<n>D<x>` to roll `n`-many `x`-sided dice, e.g. `-roll 8D20`.
        In the last case you can add modifiers:
        e.g. `<prefix>roll 8D20d3` to drop the 3 lowest die rolls
        e.g. `<prefix>roll 8D20k3` to keep the 3 highest die rolls
        e.g. `<prefix>roll 8D20dh3` to drop the 3 highest die rolls
        e.g. `<prefix>roll 8D20kl3` to keep the 3 highest die rolls
        You can also use +/- for bonus/malus or string together multiple dice rolls with + as well (or - if you want to subtract the dice roll).

        (when no argument is given, the command gives out a random number between 1 and 6)
        """
        if len(args) == 0:
            r = random.randint(1, 6)
            await ctx.send(f'🎲 D6 roll: {r}')
            return
            
        ctext = ' '.join(args)

        # CHOOSE FROM OPTIONS

        if ';' in ctext or ',' in ctext:
            if ';' in ctext:
                options = ctext.split(';')
                while "" in options:
                    options.remove("")
                n = len(options)
                if n > 1:
                    r = random.randint(1, n)
                    await ctx.send(f'🎲 D{n} roll: {options[r-1]}')
                else:
                    emoji = util.emoji("disappointed")
                    await ctx.send(f'Error: There are not enough options to choose from {emoji}')
                return
            
            elif ',' in ctext:
                options = ctext.split(',')
                while "" in options:
                    options.remove("")
                n = len(options)
                if n > 1:
                    r = random.randint(1, n)
                    await ctx.send(f'🎲 D{n} roll: {options[r-1]}')
                else:
                    emoji = util.emoji("disappointed")
                    await ctx.send(f'Error: There are not enough options to choose from {emoji}')
                return

        # ONE ARG ROLLS
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
                return

            if args[0].lower() in ['bl','backlog','memo']:
                user, color, rest_list = await util.fetch_member_and_color(ctx, args)
                cat_list = []
                cat_type = "all"
                await util.backlog_roll(ctx, user, cat_type, cat_list)
                return
            
            if args[0].lower() in ['blc','backlogcat','backlogcategory']:
                user, color, rest_list = await util.fetch_member_and_color(ctx, args)
                cat_list = ["default"]
                cat_type = "blc"
                await util.backlog_roll(ctx, user, cat_type, cat_list)
                return

            if args[0].lower() in ['blx','backlogwithout']:
                user, color, rest_list = await util.fetch_member_and_color(ctx, args)
                cat_list = ["default"]
                cat_type = "blx"
                await util.backlog_roll(ctx, user, cat_type, cat_list)
                return

        if len(args) >= 2 and args[0].lower() in ['bl','backlog','memo','blc','backlogcat','backlogcategory','blx','backlogwithout']:
            commandarg = args[0].lower()
            user, color, rest_list = await util.fetch_member_and_color(ctx, args[1:])
            cat_list = []

            if commandarg in ["blx","backlogwithout"]:
                cat_type = "blx"
                for arg in rest_list[1:]:
                    arg2 = util.cleantext2(arg.lower())
                    if arg2 == "":
                        arg2 = "default"
                    cat_list.append(arg2)
            else:
                cat_type = "blc"
                for arg in rest_list:
                    arg2 = util.cleantext2(arg.lower())
                    if arg2 == "":
                        arg2 = "default"
                    cat_list.append(arg2)

            await util.backlog_roll(ctx, user, cat_type, cat_list)
            return

        if len(args) >= 1 and "d" in args[0].lower():
            try:
                diceroll_batch = []
                argumentstring = ''.join(args).lower()

                for char in argumentstring:
                    if char not in ["d","k","l","h","+","-","0","1","2","3","4","5","6","7","8","9"]:
                        # under construction: add explosion e or !
                        # under construction minimum/maximum?
                        # under construction: number successes > <
                        raise ValueError("syntax error - inavlid characters")
                        return

                argumentstring2 = argumentstring.replace("+","?+").replace("-","?-")
                arguments = argumentstring2.split("?")

                i = -1
                for arg in arguments:
                    if "d" in arg:
                        i += 1
                        # handle dice
                        factor = 1
                        # parse number of dice
                        num_of_dice_str = arg.split("d",1)[0]
                        if num_of_dice_str.strip() in ["", "+", "-"]:
                            num_of_dice = 1
                            if num_of_dice_str.strip() in ["-"]:
                                factor = -1
                        else:
                            num_of_dice = int(num_of_dice_str)
                            if num_of_dice < -9999:
                                raise ValueError("number of dice too far in the negative")
                            elif num_of_dice > 9999:
                                raise ValueError("number of dice too large")
                            if num_of_dice == 0:
                                continue
                            if num_of_dice < 0:
                                num_of_dice = -num_of_dice
                                factor = -1
                        rest = arg.split("d",1)[1]
                        extra = False
                        bonus = 0

                        if "dh" in rest:
                            die_size = int(rest.split("dh")[0])
                            num = int(rest.split("dh")[1])
                            extra = True
                            reverse = False
                            keep_factor = -1

                        elif "kl" in rest:
                            die_size = int(rest.split("kl")[0])
                            num = int(rest.split("kl")[1])
                            extra = True
                            reverse = False
                            keep_factor = 1

                        elif "dl" in rest:
                            die_size = int(rest.split("dl")[0])
                            num = int(rest.split("dl")[1])
                            extra = True
                            reverse = True
                            keep_factor = -1

                        elif "kh" in rest:
                            die_size = int(rest.split("kh")[0])
                            num = int(rest.split("kh")[1])
                            extra = True
                            reverse = True
                            keep_factor = 1

                        elif "d" in rest:
                            die_size = int(rest.split("d")[0])
                            num = int(rest.split("d")[1])
                            extra = True
                            reverse = True
                            keep_factor = -1

                        elif "k" in rest:
                            die_size = int(rest.split("k")[0])
                            num = int(rest.split("k")[1])
                            extra = True
                            reverse = True
                            keep_factor = 1

                        else:
                            die_size = int(rest)

                        n = num_of_dice
                        dice_rolls = []
                        while n >= 1:
                            r = random.randint(1, die_size)
                            dice_rolls.append(r)
                            n = n - 1
                        #total = sum(dice_rolls)

                        if extra:
                            if num > 0 and num < num_of_dice:
                                dice_rolls.sort(reverse=reverse)
                                filtered_rolls = dice_rolls[:(keep_factor * num)]
                                filtered_sum = sum(filtered_rolls) * factor
                                dropped_rolls = dice_rolls[(keep_factor * num):]
                            else:
                                raise ValueError("modifiers to drop/keep cannot be equal or larger than the number of dice")
                        else:
                            filtered_rolls = dice_rolls
                            filtered_sum = sum(filtered_rolls) * factor
                            dropped_rolls = []

                        diceroll_batch.append([filtered_sum, sorted(filtered_rolls, reverse=True), sorted(dropped_rolls, reverse=True), bonus])
                    else:
                        #handle bonus
                        if arg.startswith("+"):
                            diceroll_batch[i][3] += int(arg[1:])
                        elif arg.startswith("-"):
                            diceroll_batch[i][3] -= int(arg[1:])

                if len(diceroll_batch) == 0:
                    raise ValueError("no valid roll found")

                # assemble
                description = argumentstring
                result = ""
                total = 0
                for diceroll in diceroll_batch:
                    sub_total = diceroll[0]
                    filtered = ', '.join([str(x) for x in diceroll[1]])
                    if len(diceroll[2]) > 0:
                        dropped = ", ~~" + ', '.join([str(x) for x in diceroll[2]]) + "~~"
                    else:
                        dropped = ""
                    if diceroll[3] == 0:
                        bonus = ""
                    elif diceroll[3] < 0:
                        bonus = str(diceroll[3])
                    else:
                        bonus = "+" + str(diceroll[3])
                    result += f"{sub_total}{bonus}  ({filtered}{dropped})\n"

                    total += sub_total + diceroll[3]

                if len(diceroll_batch) > 1 or diceroll[3] != 0:
                    s = "\n"
                else:
                    s = ""
                response = f"🎲 `{description} roll`:{s} {result}"[:1950] 
                if len(diceroll_batch) > 1 or diceroll[3] != 0:
                    response +=  f"**Total: {total}**"

                await ctx.send(response.strip())
                return

            except Exception as e:
                await ctx.send(f"Error: {e}")
                print(traceback.format_exc())
                return
       
        await ctx.send(f'Error: Argument can be one of the following things:\nan integer > 1\na list of options separated by semicolons\n`bl` or `blc <category>` or `blx <category>` (with category names separated by commas)\n`n`D`x` to roll `n`-many `x`-sided dice.')
    
    @_dice.error
    async def dice_error(self, ctx, error):
        await util.error_handling(ctx, error)



    ############################# TRANSLATE #################################################################################################################



    def get_languagedict(self, scope):
        languages_name_dict = {
                    "afrikaans": 'af',
                    "albanian": 'sq',
                    "amharic": 'am',
                    'arabic': 'ar',
                    'armenian': 'hy',
                    'azerbaijani': 'az',
                    'basque': 'eu',
                    'belarusian': 'be',
                    'bengali': 'bn',
                    'bosnian': 'bs',
                    'bulgarian': 'bg',
                    'catalan': 'ca',
                    'cebuano': 'ceb',
                    'chichewa': 'ny',
                    'chinese': 'zh-cn',
                    'simpchinese': 'zh-cn',
                    'tradchinese': 'zh-tw',
                    'taiwanese': 'zh-tw',
                    'corsican': 'co',
                    'croatian': 'hr',
                    'czech': 'cs',
                    'danish': 'da',
                    'dutch': 'nl',
                    'english': 'en',
                    'esperanto': 'eo',
                    'estonian': 'et',
                    'filipino': 'tl',
                    'finnish': 'fi',
                    'french': 'fr',
                    'frisian': 'fy',
                    'galician': 'gl',
                    'georgian': 'ka',
                    'german': 'de',
                    'greek': 'el',
                    'gujarati': 'gu',
                    'haitian creole': 'ht',
                    'hausa': 'ha',
                    'hawaiian': 'haw',
                    'hebrew2': 'iw',
                    'hebrew': 'he',
                    'hindi': 'hi',
                    'hmong': 'hmn',
                    'hungarian': 'hu',
                    'icelandic': 'is',
                    'igbo': 'ig',
                    'indonesian': 'id',
                    'irish': 'ga',
                    'italian': 'it',
                    'japanese': 'ja',
                    'javanese': 'jw',
                    'kannada': 'kn',
                    'kazakh': 'kk',
                    'khmer': 'km',
                    'korean': 'ko',
                    'kurdish': 'ku',
                    'kurmanji': 'ku',
                    'kyrgyz': 'ky',
                    'lao': 'lo',
                    'latin': 'la',
                    'latvian': 'lv',
                    'lithuanian': 'lt',
                    'luxembourgish': 'lb',
                    'macedonian': 'mk',
                    'malagasy': 'mg',
                    'malay': 'ms',
                    'malayalam': 'ml',
                    'maltese': 'mt',
                    'maori': 'mi',
                    'marathi': 'mr',
                    'mongolian': 'mn',
                    'myanmar': 'my',
                    'burmese': 'my',
                    'nepali': 'ne',
                    'norwegian': 'no',
                    'odia': 'or',
                    'pashto': 'ps',
                    'persian': 'fa',
                    'polish': 'pl',
                    'portuguese': 'pt',
                    'punjabi': 'pa',
                    'romanian': 'ro',
                    'russian': 'ru',
                    'samoan': 'sm',
                    'scots gaelic': 'gd',
                    'serbian': 'sr',
                    'sesotho': 'st',
                    'shona': 'sn',
                    'sindhi': 'sd',
                    'sinhala': 'si',
                    'slovak': 'sk',
                    'slovenian': 'sl',
                    'somali': 'so',
                    'spanish': 'es',
                    'sundanese': 'su',
                    'swahili': 'sw',
                    'swedish': 'sv',
                    'tajik': 'tg',
                    'tamil': 'ta',
                    'telugu': 'te',
                    'thai': 'th',
                    'turkish': 'tr',
                    'ukrainian': 'uk',
                    'urdu': 'ur',
                    'uyghur': 'ug',
                    'uzbek': 'uz',
                    'vietnamese': 'vi',
                    'welsh': 'cy',
                    'xhosa': 'xh',
                    'yiddish': 'yi',
                    'yoruba': 'yo',
                    'zulu': 'zu',
                    }

        languages_flag_dict = {
                        "🇮🇳": 'hi',
                        "🇦🇷": 'es',
                        "🇦🇺": 'en',
                        "🇧🇩": 'bn',
                        "🇧🇷": 'pt',
                        "🇨🇦": 'en',
                        "🇨🇳": 'zh-cn',
                        "🇨🇿": 'cs',
                        "🇭🇷": 'hr',
                        "🇵🇱": 'pl',
                        "🇷🇴": 'ro',
                        "🇷🇺": 'ru',
                        "🇸🇰": 'sk',
                        "🇹🇷": 'tr',
                        "🇬🇧": 'en',
                        "🇺🇸": 'en',
                        "🇫🇷": 'fr',
                        "🇩🇪": 'de',
                        "🇪🇸": 'es',
                        "🇳🇱": 'nl',
                        "🇮🇹": 'it',
                        "🇬🇦": 'ga',
                        "🇵🇹": 'pt',
                        "🇳🇵": 'ne',
                        "🇸🇷": 'sr',
                        "🇺🇦": 'uk',
                        "🇻🇳": 'vi',
                        "🇮🇩": 'id',
                        "🇵🇭": 'tl',
                        "🇯🇵": 'ja',
                        "🇭🇺": 'hu',
                        "🇮🇸": 'is',
                        "🇫🇮": 'fi',
                        "🇧🇼": 'et',
                        "🇧🇬": 'bg',
                        "🇮🇱": 'he',
                        "🇰🇷": 'ko',
                        "🇱🇻": 'lv',
                        "🇱🇧": 'lb',
                        "🇺🇿": 'uz',
                        "🇸🇦": 'ar',
                        "🇿🇦": 'af'
                        }

        languages_extra_dict = {
                        "ch": 'zh-cn',
                        "zh": 'zh-cn',
                        "jp": 'ja',
                        "gr": 'el',
                        }           

        languagedict = {}   

        if scope in ["name", "names", "all"]:
            languagedict.update(languages_name_dict)

        if scope in ["flag", "flags", "all"]:
            languagedict.update(languages_flag_dict)

        if scope in ["all"]:
            languagedict.update(languages_extra_dict)

        return languagedict



    async def google_translate(self, ctx, args, extra_info):
        async with ctx.typing():
            languagedict = self.get_languagedict("all")
            if len(args) == 0:
                await ctx.send(f'No arguments provided. First argument needs to be language code, everything after will be translated.')
                return
            
            givenLanguage = args[0]

            if givenLanguage.lower() in ["languages", "language"]:
                languagesList = languagedict.values()
                filteredList = sorted(list(dict.fromkeys(languagesList)))
                languagestring = ', '.join(filteredList)
                await ctx.send(f'`Supported languages:` {languagestring}')
                return

            if givenLanguage in languagedict.values():
                targetLanguage = givenLanguage
            elif givenLanguage in languagedict:
                targetLanguage = languagedict[givenLanguage]
            else:
                if givenLanguage.lower() in languagedict.values():
                    targetLanguage = givenLanguage.lower()
                elif givenLanguage.lower() in languagedict:
                    targetLanguage = languagedict[givenLanguage.lower()]
                else:
                    targetLanguage = "error"

            print(f"Target Language: {targetLanguage}")

            if targetLanguage == "error":
                await ctx.send(f'Language {givenLanguage} is not supported. Use `{self.prefix}language details` to get list of supported languages.')
                return

            if len(args) == 1:
                emoji = util.emoji("think")
                await ctx.send(f'{emoji}')
                return

            try:
                msgToTranslate = ' '.join(args[1:])
                print(f"To translate: {msgToTranslate}")
                GTranslator = Translator()
                detection = GTranslator.detect(msgToTranslate)
                msgTranslated = GTranslator.translate(msgToTranslate, dest=targetLanguage).text

                if extra_info:
                    responsetext = f"`[Lang.: {detection.lang}, Conf.={detection.confidence}]`\n"
                    responsetext += f'`Google Translation result:` {msgTranslated}'
                else:
                    responsetext = f'`Translation result:` {msgTranslated}'

                await ctx.reply(responsetext[:2000], mention_author=False)
            except Exception as e:
                if str(e).strip() == "'NoneType' object has no attribute 'group'":
                    await ctx.send(f'`An error ocurred:` Probably wrong googletranslate package.\nHost should try```pip uninstall googletrans```and then```pip install googletrans==3.1.0a0```in console.')
                else:
                    await ctx.send(f'`An error ocurred:` {e}')



    async def libre_get(self, mirror, language, query):
        url = f"https://{mirror}/translate"

        payload = {
            'q': query,
            'source': 'auto',
            'target': language,
            'format': 'text',
            #'api_key': ""
        }

        response = requests.post(url, data=payload, timeout=4)
        rjson = response.json()

        return rjson



    async def libre_translate(self, ctx, args, extra_info):
        """https://github.com/LibreTranslate/LibreTranslate?tab=readme-ov-file#mirrors"""

        if len(args) < 2:
            await ctx.send("Command needs target language and words to translate as arguments.")

        async with ctx.typing():
            language = args[0]
            query = ' '.join(args[1:])

            conB = sqlite3.connect(f'databases/botsettings.db')
            curB = conB.cursor()
            mirror_list = [item[0] for item in curB.execute("SELECT url FROM mirrors WHERE service = ? ORDER BY priority", ("libre translate",)).fetchall()]

            new_mirror_list = []
            i = 0

            # fetch from mirrors

            for mirror in mirror_list:
                try:
                    rjson = await self.libre_get(mirror, language, query)

                    translated_text = rjson['translatedText']
                    new_mirror_list.append([mirror, 1])
                    print("Translation mirror:", mirror)
                    break

                except Exception as e:
                    print("Error:", e)
                    try:
                        print(rjson)
                    except:
                        pass
                    i += 1
                    new_mirror_list.append([mirror, len(mirror_list) + 1 - i])
                    continue
            else:
                emoji = util.emoji("disappointed")
                await ctx.send(f"None of the mirrors seem to work {emoji}\nMods can try to fix it via `{self.prefix}update`.")
                return

            # reorder

            try:
                new_mirror_urls = [x[0] for x in new_mirror_list]
                for mirror in reversed(mirror_list):
                    if mirror in new_mirror_urls:
                        pass
                    else:
                        i += 1
                        new_mirror_list.append([mirror, len(mirror_list) + 1 - i])

                for item in new_mirror_list:
                    url = item[0]
                    prio = item[1]
                    curB.execute("UPDATE mirrors SET priority = ? WHERE url = ?", (prio, url))
                conB.commit()
            except Exception as e:
                print("Warning:", e)

            # send

            try:
                try:
                    original_language = rjson['detectedLanguage']['language']
                except:
                    original_language = "?"

                try:
                    confidence = rjson['detectedLanguage']['confidence']
                except:
                    confidence = "?"

                if extra_info:
                    responsetext = f"`[Lang.: {original_language}, Conf.={confidence/100}]`\n"
                    responsetext += f'`Libre Translation result:` {translated_text}'
                else:
                    responsetext = f'`Translation result:` {translated_text}'

                await ctx.reply(responsetext[:2000], mention_author=False)

            except Exception as e:
                await ctx.send(f"Error: {e}\n```{rjson}```Mayhaps let mods refresh libre translate mirrors via `{self.prefix}update`.")



    @commands.group(name="translate", aliases = ["tr"], pass_context=True, invoke_without_command=True)
    #@commands.check(GU_Check.is_googletrans_enabled)
    @commands.check(util.is_active)
    async def _translate(self, ctx, *args):
        """translate

        Translates a word or sentence, first argument must be the destination language code.

        If GoogleTranslate is enabled, you can use `-languages` to see which languages are supported.
        If not the command will use LibreTranslate instead.
        """
        if len(args) < 2:
            await ctx.send(f'Needs arguments. First argument needs to be language code, everything after will be translated.')
            return

        extra_info = False

        try:
            if GU_Check.is_googletrans_enabled():
                await self.google_translate(ctx, args, extra_info)
            else:
                raise ValueError("GoogleTranslate not imported")
        except:
            await self.libre_translate(ctx, args, extra_info)
        
    @_translate.error
    async def translate_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.group(name="trx", aliases = ["translatex"], pass_context=True, invoke_without_command=True)
    #@commands.check(GU_Check.is_googletrans_enabled)
    @commands.check(util.is_active)
    async def _translate_x(self, ctx, *args):
        """translate (with detection info)

        Translates a word or sentence, first argument must be the destination language code.
        
        If GoogleTranslate is enabled, you can use `-languages` to see which languages are supported.
        If not the command will use LibreTranslate instead.
        """
        if len(args) < 2:
            await ctx.send(f'Needs arguments. First argument needs to be language code, everything after will be translated.')
            return
        extra_info = True
        
        try:
            if GU_Check.is_googletrans_enabled():
                await self.google_translate(ctx, args, extra_info)
            else:
                raise ValueError("GoogleTranslate not imported")
        except:
            await self.libre_translate(ctx, args, extra_info)
        
    @_translate.error
    async def translate_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name="ltr", aliases = ["libretranslate", "ltranslate"])
    @commands.check(GU_Check.is_googletrans_enabled)
    @commands.check(util.is_active)
    async def _libretranslate(self, ctx, *args):
        """Translates using LibreTranslate
        """
        if len(args) < 2:
            await ctx.send(f'Needs arguments. First argument needs to be language code, everything after will be translated.')
            return

        extra_info = False

        await self.libre_translate(ctx, args, extra_info)
        
    @_libretranslate.error
    async def libretranslate_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name="ltrx", aliases = ["libretranslatex", "ltranslatex"])
    @commands.check(GU_Check.is_googletrans_enabled)
    @commands.check(util.is_active)
    async def _libretranslatex(self, ctx, *args):
        """Translates using LibreTranslate (with detection info)
        """
        if len(args) < 2:
            await ctx.send(f'Needs arguments. First argument needs to be language code, everything after will be translated.')
            return

        extra_info = True

        await self.libre_translate(ctx, args, extra_info)
        
    @_libretranslatex.error
    async def libretranslatex_error(self, ctx, error):
        await util.error_handling(ctx, error)



    async def show_language_list(self, ctx, args):
        short = True
        for arg in args:
            if arg.lower() in ["detail", "details", "detailed"]:
                short = False

        languagedict = self.get_languagedict("all")
        languagesList = languagedict.values()
        filteredList = sorted(list(dict.fromkeys(languagesList)))

        if short:
            languagestring = ', '.join(filteredList)
            await ctx.send(f'`Supported languages:` {languagestring}')
            return

        language_names_dict = self.get_languagedict("name")
        language_reverse_dict = {v: k for k, v in language_names_dict.items()}

        response_text = "**Supported languages:** "

        for lang in filteredList:
            if lang in language_reverse_dict:
                response_text += f"`{lang}`: {language_reverse_dict[lang]}, "
            else:
                response_text += f"`{lang}`: ?, "

        if response_text.endswith(", "):
            response_text = response_text[:-2]

        await ctx.send(response_text[:2000])


    
    @commands.command(name='languages', aliases = ['language'])
    @commands.check(GU_Check.is_googletrans_enabled)
    @commands.check(util.is_active)
    async def _translate_languages(self, ctx, *args):
        """list of supported translation languages

        Use with arg `detailed` to get language names alongside language abbreviations."""
        await self.show_language_list(ctx, args)
    @_translate_languages.error
    async def translate_languages_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_translate.command(name="languages", aliases = ['language'], pass_context=True)
    @commands.check(GU_Check.is_googletrans_enabled)
    @commands.check(util.is_active)
    async def _translate_languages_subcommand(self, ctx, *args):
        """list of supported translation languages
        Use with arg `detailed` to get language names alongside language abbreviations."""
        await self.show_language_list(ctx, args)
    @_translate_languages_subcommand.error
    async def translate_languages_subcommand_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_translate_x.command(name="languages", aliases = ['language'], pass_context=True)
    @commands.check(GU_Check.is_googletrans_enabled)
    @commands.check(util.is_active)
    async def _translatex_languages_subcommand(self, ctx, *args):
        """list of supported translation languages
        Use with arg `detailed` to get language names alongside language abbreviations."""
        await self.show_language_list(ctx, args)
    @_translatex_languages_subcommand.error
    async def translatex_languages_subcommand_error(self, ctx, error):
        await util.error_handling(ctx, error)





    ############################# UNIT CONVERSION #################################################################################################################



    @commands.command(name='convert', aliases = ['con','conv'])
    @commands.check(util.is_active)
    async def _convert(self, ctx, *args):
        """Converts units
        
        For example:
        `<prefix>con <number>F`: Fahrenheit to Celsius
        `<prefix>con <number>C`: Celsius to Fahrenheit

        currently supported are temperature `(C,F)`, length/distances `(km,m,cm,mi,yd,ft,in also 5'11 notation)`, speed `(kmh,mph)`, weight/mass `(lbs,oz,kg,g)`, volume `(gal,ukgal,fl oz,cup,l,cl,ml)`, area `(acre,sqm)`, time `(years,months,weeks,days,hours,minutes,seconds)`
        and 
        also currencies, for which you can use "to"
        `<prefix>con <number> USD to EUR CHF`
        if you leave the "to" out it will give out USD, EUR, GPB, JPY per default
        """

        ##### INTERNAL FUNCTIONS #####

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

        EUR_LIST = ["€","EURO","EUROS"]
        JPY_LIST = ["円","¥","YEN","YENS", "EN", "えん", "エン"]
        USD_LIST = ["$","DOLLAR","DOLLARS","USDOLLAR","USDOLLARS"]
        GBP_LIST = ["£","POUND","POUNDS","QUID","QUIDS"]
        other_currency_symbols = EUR_LIST + JPY_LIST + USD_LIST + GBP_LIST
        def currency_symbol_converter(s):
            if s in other_currency_symbols:
                if s in EUR_LIST:
                    return "EUR"
                elif s in JPY_LIST:
                    return "JPY"
                elif s in USD_LIST:
                    return "USD"
                elif s in GBP_LIST:
                    return "GBP"
                else:
                    return "ERROR"
            else:
                return s.upper()

        #### START CONVERT COMMAND ####

        if len(args) == 0:
            await ctx.send(f'Missing argument for conversion.')
            return

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
        argument_string = ''.join(from_arguments).replace(",","")
        derpy = util.emoji("derpy")
        think = util.emoji("think")
        try:
            VaU_unfiltered = separate_number_chars(argument_string) # Value & Unit
            VaU = [x for x in VaU_unfiltered if x]
            value_one = VaU[0]
            unit_one = VaU[1]
            if is_number(value_one) == False and is_number(unit_one) == True:
                value_one = VaU[1]
                unit_one = VaU[0]
        except Exception as e:
            print(e)
            await ctx.send(f'Error: Parsing value and unit crashed. {derpy}')
            return

        ################### go through different units ###########################################################################

        # TEMPERATURE ############################################################################################################
        if unit_one.lower() in ["f","fahrenheit", "°f"] and is_number(value_one):
            try:
                value_to_convert = float(value_one)
                converted_value = round((value_to_convert-32) * 5/9,1)
                await ctx.send(f'Fahrenheit to Celsius\n```{"{:,}".format(value_to_convert)}F is about {"{:,}".format(converted_value)}C.```')
            except:
                await ctx.send(f'Error: Fahrenheit to Celsius computation crashed. {derpy}')
        elif unit_one.lower() in ["c","celsius", "°c"] and is_number(value_one):
            try:
                value_to_convert = float(value_one)
                converted_value = round(value_to_convert * 9/5 + 32,1)
                await ctx.send(f'Celsius to Fahrenheit\n```{"{:,}".format(value_to_convert)}C is about {"{:,}".format(converted_value)}F.```')
            except:
                await ctx.send(f'Error: Celsius to Fahrenheit computation crashed. {derpy}')

        # LENGTH/DISTANCE #########################################################################################################
        elif  unit_one.lower() in ["mi","miles", "mile"] and is_number(value_one):
            try:
                value_to_convert = float(value_one)
                converted_value = round((value_to_convert) * 1.609344,1)
                await ctx.send(f'Miles to Kilometers\n```{"{:,}".format(value_to_convert)}mi is about {"{:,}".format(converted_value)}km.```')
            except:
                await ctx.send(f'Error: Miles to Kilometers computation crashed. {derpy}')
        elif  unit_one.lower() in ["km","kilometer", "kilometers", "kilometre", "kilometres"] and is_number(value_one):
            try:
                value_to_convert = float(value_one)
                converted_value = round((value_to_convert)/1.609344,1)
                await ctx.send(f'Kilometers to Miles\n```{"{:,}".format(value_to_convert)}km is about {"{:,}".format(converted_value)}mi.```')
            except:
                await ctx.send(f'Error: Kilometers to Miles computation crashed. {derpy}')

        elif  unit_one.lower() in ["ft","feet", "foot", "'"] and is_number(value_one):
            try:
                value_to_convert = float(value_one)
                converted_value = round((value_to_convert) * 0.3048,2)
                if len(VaU) > 2:
                    value_two = VaU[2]
                    if is_number(value_two):
                        converted_value2 = round((100 * converted_value + (float(value_two) * 2.54))/100,2)
                        if value_to_convert == math.floor(value_to_convert) and float(value_two) == math.floor(float(value_two)):
                            await ctx.send(f'Feet to Meters\n```{"{:,}".format(math.floor(value_to_convert))}ft {math.floor(float(value_two))}inch is about {"{:,}".format(converted_value2)}m.```')
                        else:
                            await ctx.send(f'Feet to Meters\n```{"{:,}".format(value_to_convert)}ft {float(value_two)}inch is about {"{:,}".format(converted_value2)}m.```')
                    else:
                        await ctx.send(f'Error: Second value is faulty. {think}')
                        await ctx.send(f'Feet to Meters\n```{"{:,}".format(value_to_convert)}ft is about {"{:,}".format(converted_value)}m.```')
                else:
                    await ctx.send(f'Feet to Meters\n```{"{:,}".format(value_to_convert)}ft is about {"{:,}".format(converted_value)}m.```')
            except Exception as e:
                print(e)
                await ctx.send(f'Error: Feet to Meters computation crashed. {derpy}')

        elif  unit_one.lower() in ["m","meter", "meters", "metre", "metres"] and is_number(value_one):
            try:
                value_to_convert = float(value_one)
                converted_value = round((100 * value_to_convert)/2.54,1)
                if converted_value >= 12 * 9:
                    conv_yard = round(((100 * value_to_convert)/2.54)/(12*3),1)
                    await ctx.send(f'Meters to Yards\n```{"{:,}".format(value_to_convert)}m is about {"{:,}".format(conv_yard)}yards.```')
                elif converted_value >= 12:
                    conv_feet = converted_value // 12
                    conv_inch = round(converted_value - (conv_feet * 12),1)
                    await ctx.send(f'Meters to Feet/Inch\n```{"{:,}".format(value_to_convert)}m is about {conv_feet}ft {conv_inch}inch. \n({"{:,}".format(converted_value)} inch)```')
                else:
                    await ctx.send(f'Meters to Inch\n```{"{:,}".format(value_to_convert)}m is about {"{:,}".format(converted_value)}inch.```')
            except:
                await ctx.send(f'Error: Meters to Feet/Inch computation crashed. {derpy}')
        elif unit_one.lower() in ["yd","yard","yards"] and is_number(value_one):
            try:
                value_to_convert = float(value_one)
                converted_value = round((value_to_convert) * 0.9144,1)
                await ctx.send(f'Yards to Meter\n```{"{:,}".format(value_to_convert)}yd is about {"{:,}".format(converted_value)}m.```')
            except:
                await ctx.send(f'Error: Yards to Meter computation crashed. {derpy}')

        elif  unit_one.lower() in ["in","inch","zoll","inches","inchs"] and is_number(value_one):
            try:
                value_to_convert = float(value_one)
                converted_value = round((value_to_convert) * 2.54,1)
                await ctx.send(f'Inch to Centimeters\n```{"{:,}".format(value_to_convert)}inch is about {"{:,}".format(converted_value)}cm.```')
            except:
                await ctx.send(f'Error: Inch to Centimeters computation crashed. {derpy}')
        elif  unit_one.lower() in ["cm", "centimeters", "centimetres", "centimeter", "centimetre"] and is_number(value_one):
            try:
                value_to_convert = float(value_one)
                converted_value = round((value_to_convert)/2.54,1)
                if converted_value >= 12:
                    conv_feet = converted_value // 12
                    conv_inch = round(converted_value - (conv_feet * 12),1)
                    await ctx.send(f'Centimeters to Feet/Inch\n```{"{:,}".format(value_to_convert)}cm is about {conv_feet}ft {conv_inch}inch. \n({"{:,}".format(converted_value)} inch)```')
                else:
                    await ctx.send(f'Centimeters to Inch\n```{"{:,}".format(value_to_convert)}cm is about {"{:,}".format(converted_value)}inch.```')
            except:
                await ctx.send(f'Error: Inches to Centimeters computation crashed. {derpy}')

        # SPEED ###################################################################################################################
        elif  unit_one.lower() in ["mph","milesperhour","miph","mileperhour"] and is_number(value_one):
            try:
                value_to_convert = float(value_one)
                converted_value = round((value_to_convert) * 1.609344,1)
                await ctx.send(f'Miles per hour to Kilometers per hour\n```{"{:,}".format(value_to_convert)}mph is about {"{:,}".format(converted_value)}km/h.```')
            except:
                await ctx.send(f'Error: Mph to km/h computation crashed. {derpy}')
        elif  unit_one.lower() in ["kmh","km/h","kmph","kilometersperhour","kilometerperhour"] and is_number(value_one):
            try:
                value_to_convert = float(value_one)
                converted_value = round((value_to_convert) / 1.609344,1)
                await ctx.send(f'Kilometers per hour to Miles per hour\n```{"{:,}".format(value_to_convert)}km/h is about {"{:,}".format(converted_value)}mph.```')
            except:
                await ctx.send(f'Error: Km/h to mph computation crashed. {derpy}')

        # WEIGHT/MASS #############################################################################################################
        elif unit_one.lower() in ["lbs", "pound", "pounds", "lb", "pds", "pd", "libra", "libras"] and is_number(value_one):
            try:
                value_to_convert = float(value_one)
                converted_value = round((value_to_convert) * 0.45359237,2)
                await ctx.send(f'Pounds to Kilograms\n```{"{:,}".format(value_to_convert)}lbs is about {"{:,}".format(converted_value)}kg.```')
            except:
                await ctx.send(f'Error: Pounds to Kilograms computation crashed. {derpy}')
        elif unit_one.lower() in ["kg", "kilogram", "kgs", "kilograms", "kilogramms", "kilogramm"] and is_number(value_one):
            try:
                value_to_convert = float(value_one)
                converted_value = round((value_to_convert) * 2.20462262185,1)
                await ctx.send(f'Kilograms to Pounds\n```{"{:,}".format(value_to_convert)}kg is about {"{:,}".format(converted_value)}lbs.```')
            except:
                await ctx.send(f'Error: Kilograms to Pounds computation crashed. {derpy}')

        elif unit_one.lower() in ["oz", "ounce", "ounces"] and is_number(value_one):
            try:
                value_to_convert = float(value_one)
                converted_value = round((value_to_convert) * 28.34952,1)
                await ctx.send(f'Ounces to Grams\n```{"{:,}".format(value_to_convert)}oz is about {"{:,}".format(converted_value)}g.```\n(for volume/fluid ounces use "foz")')
            except:
                await ctx.send(f'Error: Ounces to Grams computation crashed. {derpy}')
        elif unit_one.lower() in ["g", "gram", "grams", "gramm", "gramms"] and is_number(value_one):
            try:
                value_to_convert = float(value_one)
                converted_value = round((value_to_convert) * 0.03527396195,2)
                await ctx.send(f'Grams to Ounces\n```{"{:,}".format(value_to_convert)}g is about {"{:,}".format(converted_value)}oz.```')
            except:
                await ctx.send(f'Error: Grams to Ounces computation crashed. {derpy}')

        # VOLUME ##################################################################################################################
        elif unit_one.lower() in ["foz", "ozf", "floz", "ozfl", "fluidounce", "fluidounces", "loz", "voz", "liquidounce", "luiquidounces", "volumeounce", "volumeounces"] and is_number(value_one):
            try:
                value_to_convert = float(value_one)
                converted_value = round((value_to_convert) * 29.5735296875,1)
                await ctx.send(f'Fluid ounces to Milliliters\n```{"{:,}".format(value_to_convert)}oz (fluid) is about {"{:,}".format(converted_value)}ml.```')
            except:
                await ctx.send(f'Error: Fluid ounces to Milliliters computation crashed. {derpy}')
        elif unit_one.lower() in ["ml", "milliliter", "milliliters", "millilitre", "millilitres", "mililiter", "mililiters", "mililitre", "mililitres"] and is_number(value_one):
            try:
                value_to_convert = float(value_one)
                converted_value = round((value_to_convert) * 0.03381402,2)
                await ctx.send(f'Milliliters to Fluid ounces\n```{"{:,}".format(value_to_convert)}ml is about {"{:,}".format(converted_value)}oz (fluid).```')
            except:
                await ctx.send(f'Error: Milliliters to Fluid ounces computation crashed. {derpy}')
        elif unit_one.lower() in ["cl", "centiliter", "centiliters", "centilitre", "centilitres"] and is_number(value_one):
            try:
                value_to_convert = float(value_one)
                converted_value = round((value_to_convert) * 0.3381402,2)
                await ctx.send(f'Centiliters to Fluid ounces\n```{"{:,}".format(value_to_convert)}cl is about {"{:,}".format(converted_value)}oz (fluid).```')
            except:
                await ctx.send(f'Error: Centiliters to Fluid ounces computation crashed. {derpy}')

        elif unit_one.lower() in ["l", "liter", "liters", "litre", "litres"] and is_number(value_one):
            try:
                value_to_convert = float(value_one)
                converted_value = round((value_to_convert) * 0.2641720524,1)
                converted_valueUK = round((value_to_convert) * 0.21996923465436,1)
                await ctx.send(f'Liters to Gallons\n```{"{:,}".format(value_to_convert)}l is about {"{:,}".format(converted_value)}gal (US).\n(...or {"{:,}".format(converted_valueUK)}gal (UK))```')
            except:
                await ctx.send(f'Error: Liters to Gallons computation crashed. {derpy}')
        elif unit_one.lower() in ["gal", "gallon", "gallons", "galon", "galons", "galus", "usgal", "usgallon", "usgallons", "gallonus", "gallonsus"] and is_number(value_one):
            try:
                value_to_convert = float(value_one)
                converted_value = round((value_to_convert) * 3.785411784,1)
                converted_valueUK = round((value_to_convert) * 0.8326741881485,1)
                await ctx.send(f'US Gallons to Liters\n```{"{:,}".format(value_to_convert)}gal (US) is about {"{:,}".format(converted_value)}l.\n(...or {"{:,}".format(converted_valueUK)}gal (UK))```(for UK Gallons use "ukgal")')
            except:
                await ctx.send(f'Error: US Gallons to Liters computation crashed. {derpy}')
        elif unit_one.lower() in ["ukgal", "ukgallon", "ukgallons", "ukgalon", "ukgalons", "galuk", "gallonuk", "gallonsuk"] and is_number(value_one):
            try:
                value_to_convert = float(value_one)
                converted_value = round((value_to_convert) * 4.5460902819948,1)
                converted_valueUS = round((value_to_convert) * 1.2009499204287,1)
                await ctx.send(f'UK Gallons to Liters\n```{"{:,}".format(value_to_convert)}gal (UK) is about {"{:,}".format(converted_value)}l.\n(...or {"{:,}".format(converted_valueUS)}gal (US))```')
            except:
                await ctx.send(f'Error: UK Gallons to Liters computation crashed. {derpy}')

        elif unit_one.lower() in ["cup", "cups", "uscup", "uscups", "cupus", "cupsus"] and is_number(value_one):
            try:
                value_to_convert = float(value_one)
                converted_value_pre = round((value_to_convert) * 236.5882365,1)
                if converted_value_pre > 1000:
                    converted_value_l = round((converted_value_pre)/1000,3)
                    await ctx.send(f'Cups (US) to Liters\n```{"{:,}".format(value_to_convert)}cup is about {"{:,}".format(converted_value_l)}l.```')
                else:
                    converted_value_ml = int(round((converted_value_pre),0))
                    await ctx.send(f'Cups (US) to Liters\n```{"{:,}".format(value_to_convert)}cup is about {"{:,}".format(converted_value_ml)}ml.```')
            except:
                await ctx.send(f'Error: Cups (US) to Liters computation crashed. {derpy}')

        # AREA ####################################################################################################################
        elif unit_one.lower() in ["acre", "a", "acres", "acer", "acers"] and is_number(value_one):
            try:
                value_to_convert = float(value_one)
                converted_value = round((value_to_convert) * 4046.8564224,1)
                await ctx.send(f'Acres to square meters ounces\n```{"{:,}".format(value_to_convert)}acres is about {"{:,}".format(converted_value)}m².```')
            except:
                await ctx.send(f'Error: Acres to square meters computation crashed. {derpy}')

        elif unit_one.lower() in ["sqm", "m²", "sqrm", "squaremeter", "squaremeters", "squaremetre", "squaremetres"] and is_number(value_one):
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
                await ctx.send(f'Acres to square meters ounces\n```{"{:,}".format(value_to_convert)}acres is about {"{:,}".format(converted_value)}m².```')
            except:
                await ctx.send(f'Error: Acres to square meters computation crashed. {derpy}')

        
        # CURRENCY - ONE IF-THEN-ELSE LEVEL HIGHER (to not load DB if not needed) #################################################
        else:
            crypto_currencies = ["BTC","BITCOIN", "ETH", "ETHER", "ETHEREUM", "USDT", "TETHER", "BNB", "USDC", "USDCOIN", "XRP", "BUSD", "BINANCEUSD", "BINANCE", "ADA", "CARDANO"]
            
            # CRYPTO CURRENCY
            if unit_one.upper() in crypto_currencies:
                emoji = util.emoji("pain")
                await ctx.send(f'Ugh crypto... {emoji}\nNot supported, sorry.')

            else:
                # ACTUAL CURRENCY
                try:
                    con = sqlite3.connect('databases/exchangerate.db')
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
                    print("error: fetching data from currency DB failed")

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
                        currency_from = currency_symbol_converter(unit_one.upper())
                        for currency in data:
                            currency_code = currency[0]
                            if currency_from == currency_code:
                                currency_value = currency[1]
                                currency_name = currency[2]
                                currency_country = currency[3]
                                last_updated = currency[4]
                                break

                        message = f"{currency_name} currency conversion\n"
                        message += "```\n"
                        message += f"{'{:,}'.format(value_to_convert)} {currency_code} are about...\n"

                        #these currencies do not get rounded to 1/100 but to 1
                        largenominalcurrencies = ["JPY", "TRY"]

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
                                    print(conversion)
                                    message += f"    {'{:,}'.format(conversion)} {convert_code}\n"
                            message += "```" + f"as per {last_updated}"
                            await ctx.send(message)
                        else:
                            # convert multiple
                            error = ""
                            valid_conversion_currency_found = False
                            for arg in to_arguments:
                                arg2 = arg.upper().replace(",","").replace(";","")
                                if arg2 in currencies:
                                    convert_to = currency_symbol_converter(arg2)
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
                                elif arg2 in crypto_currencies:
                                    emoji = util.emoji("welp")
                                    error += f" ...{arg2.upper()} is not supported {emoji}\n"
                                else:
                                    emoji = util.emoji("cover_eyes2")
                                    error += f" ...{arg2.upper()} I do not know {emoji}\n"
                            
                            if valid_conversion_currency_found:
                                message += "```" + f"as per {last_updated}\n\n" + error
                            else:
                                message = f"{currency_name} currency conversion\n"
                                message += "none of the given exchange currencies were recognised... :("
                            await ctx.send(message[:4096])
                    except Exception as e:
                        emoji = util.emoji("derpy_playful")
                        await ctx.send(f'Error: Currency conversion crashed. {emoji}\n{e}')
            
                else:
                    # CONVERT TIME
                    
                    if unit_one.lower() in ["year", "years", "month", "months", "week", "weeks", "day", "days", "hour", "hours", "minute", "minutes", "second", "seconds", "y", "mon", "w", "d", "h", "hr", "hrs", "min", "sec", "s"] and is_number(value_one):
                        # time converter
                        total_seconds = 0 
                        val_unit_list = []
                        valuniterrors = []
                        k = 0
                        l = 0
                        for arg in args: 
                            if (k % 2) == 0:
                                val_unit_list.append([arg])
                            else:
                                val_unit_list[l].append(arg)
                                l += 1
                            k += 1

                        print(val_unit_list)
                        for val_unit in val_unit_list:
                            try:
                                val_str = val_unit[0]
                                unit = val_unit[1].lower().replace("`","'")
                                val = float(val_str)
                                value_is_number = True
                            except:
                                print("value not a number or unit not provided")
                                value_is_number = False

                            if value_is_number:
                                if unit in ["year", "years", "y"]:
                                    total_seconds += val * 365 * 24 * 60 * 60
                                    # leap year
                                    if val >= 4:
                                        total_seconds += (val // 4) * 24 * 60 * 60
                                    if val <= -4:
                                        total_seconds += math.ceil(val / 4) * 24 * 60 * 60

                                elif unit in ["month", "months", "mon"]:
                                    total_seconds += val * 30 * 24 * 60 * 60
                                    if val >= 6 and val < 12:
                                        total_seconds += (val / 12) * 2 * 24 * 60 * 60
                                    elif val >= 12:
                                        total_seconds += (val / 12) * 5 * 24 * 60 * 60
                                    if val <= -6 and val > -12:
                                        total_seconds += (val / 12) * 2 * 24 * 60 * 60
                                    elif val <= -12:
                                        total_seconds += (val / 12) * 5 * 24 * 60 * 60
                                    # leap year
                                    if val >= 48:
                                        total_seconds += math.floor(val / 48) * 24 * 60 * 60
                                    if val <= -48:
                                        total_seconds += math.ceil(val / 48) * 24 * 60 * 60

                                elif unit in ["week", "weeks", "w"]:
                                    total_seconds += val * 7 * 24 * 60 * 60

                                elif unit in ["day", "days", "d"]:
                                    total_seconds += val * 24 * 60 * 60

                                elif unit in ["hour", "hours", "h", "hr", "hrs"]:
                                    total_seconds += val * 60 * 60

                                elif unit in ["minute", "minutes", "min"]:
                                    total_seconds += val * 60

                                elif unit in ["second", "seconds", "sec", "s"]:
                                    total_seconds += val

                                else:
                                    valunit_string = ' '.join(val_unit)
                                    valuniterrors.append(valunit_string)
                            else:
                                valunit_string = ' '.join(val_unit)
                                valuniterrors.append(valunit_string)
                        
                        if len(valuniterrors) == 0:
                            time_to_convert = ' '.join(args).lower()[:1000]
                            converted_time = f"{'{:,}'.format(int(total_seconds))} sec"
                            if total_seconds > 60:
                                minutes = int(total_seconds//60)
                                seconds = int(total_seconds - (minutes * 60))
                                converted_time += f"\n\n  or {'{:,}'.format(minutes)}min {seconds}sec"
                            if total_seconds > 3600:
                                hours = int(total_seconds//3600)
                                minutes = int((total_seconds - (hours * 3600))//60)
                                seconds = int(total_seconds - (hours * 3600 + minutes * 60))
                                converted_time += f"\n\n  or {'{:,}'.format(hours)}h {minutes}min {seconds}s"
                            if total_seconds > 24 * 3600:
                                days = int(total_seconds//(24*3600))
                                hours = int((total_seconds - (days * 24*3600))//3600)
                                minutes = int((total_seconds - ((days * 24*3600) + (hours * 3600)))//60)
                                seconds = int(total_seconds - (days * 24*3600 + hours * 3600 + minutes * 60))
                                if seconds > 30:
                                    minutes += 1
                                converted_time += f"\n\n  or {'{:,}'.format(days)}days {hours}h {minutes}min"
                            if total_seconds > 365 * 24 * 3600:
                                if total_seconds > (4 * 365 + 1) * 24 * 3600:
                                    years = round((total_seconds/(365 * 24 * 3600)),1)
                                else:
                                    years = round((4*total_seconds/((4 * 365 + 1) * 24 * 3600)),1)
                                converted_time += f"\n\n  or {'{:,}'.format(years)}years"
                            await ctx.send(f'Time conversion:\n```{time_to_convert} is about {converted_time}```')
                        else:
                            valuniterrors_string = ', '.join(valuniterrors)
                            await ctx.send(f"Error: Could not parse `{valuniterrors_string}` value/unit tuple(s)...")

                    else:
                        # WHEN NOTHING MATCHES
                        await ctx.send(f'Error: Unsupported unit. {think}')

    @_convert.error
    async def convert_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='currencies', aliases = ['supportedcurrencies'])
    @commands.check(util.is_active)
    async def _supportedcurrencies(self, ctx, *args):
        """Shows the supported currencies for exchangerate conversion"""
        conER = sqlite3.connect('databases/exchangerate.db')
        curER = conER.cursor()
        curER.execute('''CREATE TABLE IF NOT EXISTS USDexchangerate (code text, value text, currency text, country text, last_updated text, time_stamp text)''')
        known_currencies = [[item[0],item[1]] for item in curER.execute("SELECT code, value FROM USDexchangerate").fetchall()]

        if len(known_currencies) == 0:
            await ctx.send(f"Currency database is empty atm. Ask mods to use {self.prefix}update.")
            return
        currency_list = []
        for item in known_currencies:
            c_code = item[0]
            c_value = item [1]
            if (not c_code is None or c_code == "") and (not c_value is None or c_value == "") and (util.represents_float(c_value)):
                currency_list.append(c_code)

        currency_list.sort()
        embed=discord.Embed(title="Supported currencies", description=', '.join(currency_list), color=0x000000)
        embed.set_footer(text=f"Use e.g. '{self.prefix}con 100 USD to JPY' to convert currencies.")
        await ctx.send(embed=embed)
    @_supportedcurrencies.error
    async def supportedcurrencies_error(self, ctx, error):
        await util.error_handling(ctx, error)



    #####################################################################################################################
    #####################################################################################################################
    #####################################################################################################################
    #####################################################################################################################
    #####################################################################################################################
    #####################################################################################################################
    #####################################################################################################################
    #####################################################################################################################
    #####################################################################################################################
    #####################################################################################################################
    #####################################################################################################################
    #####################################################################################################################

    #################################################### TIME STUFF #####################################################



    async def reminder_counter(self):
        con = sqlite3.connect(f'databases/timetables.db')
        cur = con.cursor()
        try:
            zcounter_list = [item[0] for item in cur.execute("SELECT num FROM zcounter").fetchall()]
            if len(zcounter_list) == 0:
                cur.execute("INSERT INTO zcounter VALUES (?)", ("101",))
                con.commit()
                reminder_id = str(101)
            else: 
                reminder_id = str(int(zcounter_list[0])+1)
                cur.execute("UPDATE zcounter SET num = ?", (reminder_id,))
                con.commit()
        except Exception as e:
            print(e)
            raise ValueError(f"Error while creating reminder ID: {e}")

        return reminder_id
        


    @commands.group(name="remind", aliases = ["remindme"], pass_context=True, invoke_without_command=True)
    @commands.check(util.is_active)
    async def _remind(self, ctx, *args):
        """Sets a reminder

        First needs to specify a time, which can be either given by `in` and a time period
        i.e. 
        > `-remind in 5 hours blablabla`
        or an `at` and a given time in the future in UNIX timestamp format
        i.e. 
        > `-remind at 2023668360 blablabla`
        the rest is considered part of the reminder content.

        has subcommand:
        🔒`recurring`
        """

        user_perms = [p for p in ctx.author.guild_permissions]
        
        if ('manage_guild', True) not in user_perms:
            conB = sqlite3.connect(f'databases/botsettings.db')
            curB = conB.cursor()
            custom_reminders_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("reminder functionality",)).fetchall()]
            if len(custom_reminders_list) == 0:
                curB.execute("INSERT INTO serversettings VALUES (?, ?, ?, ?)", ("reminder functionality", "on", "", ""))
                conB.commit()
                enabled = "on"
            else:
                enabled = custom_reminders_list[0].lower().strip()

            if enabled == "off":
                await ctx.send("Reminder functionality has been disabled. Creating new reminders is a mod privilege as of now.")
                return

        if len(args) == 0:
            await ctx.send("Command needs arguments")
            return

        # CLEAN UP INPUT

        arguments = []
        for arg in args:
            arguments.append(util.cleantext(arg))

        argument_string = await util.remove_role_mentions_from_string(' '.join(arguments), ctx)
        arguments = argument_string.split()

        # TRY TO FIRST PARSE INDICATORS WHETHER TIME PERIOD OR UNIX TIME STAMP IS PROVIDED

        userid = str(ctx.author.id)
        if arguments[0].lower() == "me":
            arguments.pop(0)

        elif len(arguments[0]) > 14 and arguments[0].startswith("<@") and arguments[0].endswith(">"):
            # discord user ids have 18 digits apparently
            userid = arguments[0][2:-1]
            arguments.pop(0)

        if arguments[0].lower() == "in":
            time_type = "in"
            arguments.pop(0)
        elif arguments[0].lower() == "at":
            time_type = "at"
            arguments.pop(0)
        else:
            time_type = "undecided"

        if len(arguments) < 2:
            await ctx.send("Not enough arguments")
            return

        now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())
        time_units = ["min", "minute", "minutes", "h", "hr", "hrs", "hour", "hours", "d", "day", "days", "week", "weeks", "fortnight", "fortnights", "moon", "moons", "naive_month", "month", "months", "naive_year", "year", "years"]

        if time_type == "undecided":
            if util.represents_integer(arguments[0]):
                if int(arguments[0]) > now and arguments[1] not in time_units:
                    time_type = "at"
                else:
                    time_type = "in"
            elif arguments[0].startswith("<t:") and arguments[0].endswith((':d>',':D>',':t>',':T>',':f>',':F>',':R>',':r>')) and util.represents_integer(arguments[0][3:-3]):
                time_type = "at"
                arguments = (arguments[0][3:-3],) + arguments[1:]
            else:
                await ctx.send(f"Error (possibly in snytax): Use e.g. `{self.prefix}remind in 5 hours` or `{self.prefix}remind at <UNIX timestamp>`.")
                return

        # GET REMINDER COUNTER

        con = sqlite3.connect(f'databases/timetables.db')
        cur = con.cursor()

        reminder_id = await self.reminder_counter()

        # HANDLE THE 2 DIFFERENT CASES

        if time_type == "at":
            if not util.represents_integer(arguments[0]):
                await ctx.send("Error with `at` reminder: invalid UNIX timestamp")
                return

            utc_timestamp = int(arguments[0])
            arguments.pop(0)

            if utc_timestamp < now:
                await ctx.send("Error with `at` reminder: UNIX timestamp needs to be in the future.")
                return

            if utc_timestamp < now + 60:
                await ctx.send("Error with `at` reminder: UNIX timestamp needs to be farther in the future.")
                return

            if arguments[0].lower() in ["to", "about"]:
                arguments.pop(0)

            if len(arguments) == 0:
                remindertext = "*vaguely gestures*"
            else:
                remindertext = ' '.join(arguments)

            cur.execute("INSERT INTO reminders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (reminder_id, str(ctx.author.name), userid, str(utc_timestamp), remindertext, str(ctx.channel.id), str(ctx.channel.name), str(ctx.message.id), str(now)))
            con.commit()
            await util.changetimeupdate()
            seconds_until = utc_timestamp - now
            readable_time = util.seconds_to_readabletime(seconds_until, False, now)
            await ctx.reply(f"Alrighty. Will remind you in {readable_time} or so.\n(ID: {reminder_id})", mention_author=False)

        else:
            try:
                now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())
                timeseconds, timetext, rest = await util.timeparse(' '.join(arguments), now)
            except Exception as e:
                await ctx.send(f"Error while trying to fetch time: {e}")
                return

            if timeseconds == "infinity":
                await ctx.send(f"Error with the given amount of time.")
                return

            if int(timeseconds) < 0:
                await ctx.send(f"Error: Given time is negative.")
                return
            elif int(timeseconds) < 60:
                await ctx.send(f"Time is too short for me to act.")
                return
            #if rest.strip() in ["", "to", "about"]:
            #    await ctx.send("What should the reminder be about?")
            #    return

            utc_timestamp = now + int(timeseconds)
            remindertext = rest

            cur.execute("INSERT INTO reminders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (reminder_id, str(ctx.author.name), userid, str(utc_timestamp), remindertext, str(ctx.channel.id), str(ctx.channel.name), str(ctx.message.id), str(now)))
            con.commit()
            await util.changetimeupdate()
            seconds_until = utc_timestamp - now
            readable_time = util.seconds_to_readabletime(seconds_until, False, now)
            await ctx.reply(f"Alrighty. Will remind you in {readable_time} or so.\n(ID: {reminder_id} | <t:{utc_timestamp}:f>)", mention_author=False)
    @_remind.error
    async def remind_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_remind.command(name="recurring", aliases = ["repeating", "recurringly", "repeatingly", "repeatedly"], pass_context=True)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _remind_recurring(self, ctx, *args):
        """🔒set a recurring reminder
    
        Arguments need to be separated with double-semicolons.
        mandatory:
        1st arg: given point in time (UNIX timestamp format),
        2nd arg: `weekly`, `monthly`, `yearly` or `fortnightly` (14 days) or another time period specified with `every` and an amount of days,
        optional:
        3rd arg: channel id,
        4th arg: embed title,
        5th arg: embed text,
        6th arg: title url,
        7th arg: thumbnail url
        8th arg: comma-separated list of user IDs
        9th arg: emoji
        
        i.e. `<prefix>remind recurring <unix timestamp> ;; <interval time> ;; <channel id> ;; <title> ;; <text> ;; <title link> ;; <thumbnail url> ;; <ping list>`
        
        You do not have to provide all arguments, but you need to still separate empty arguments with a double-semicolon
        e.g. `<prefix>remind recurring 2023668360 ;; weekly ;; ;; ;; hey this is a weekly reminder ;; ;; ;; ;;`.
        You can leave out double-semicolons at the end, where only empty arguments follow
        e.g. `<prefix>remind recurring 2023668360 ;; every 30 days `.
        """

        if len(args) == 0:
            await ctx.send("Command needs arguments")
            return

        aux_args = []
        for arg in args:
            aux_args.append(util.cleantext(arg.lower()))
        arg_string = ' '.join(aux_args)

        arguments = []
        for arg in arg_string.split(";;"):
            arguments.append(arg.strip())
        if len(arguments) < 2:
            await ctx.send(f"Too few arguments. Make sure to separate them with double-semicolons. See `{self.prefix}help remind recurring` for more info.")
            return
        arguments += ["","","","","","",""]

        # PARSE INPUT

        i = 0
        try:
            i += 1
            unix_timestamp = int(arguments[0])
            i += 1
            time_interval = arguments[1]

            i += 1
            if arguments[2] == "":
                channel_id = ctx.channel.id
            else:
                channel_id = int(arguments[2])
            channel = self.bot.get_channel(channel_id)
            if channel is None:
                raise ValueError(f"channel id seems to be invalid")
            else:
                channel_name = channel.name

            i += 1
            if arguments[3] == "":
                title = "Reminder!"
            else:
                title = arguments[3]

            i += 1
            if arguments[4] == "":
                description = "⏰" 
            else:
                description = arguments[4]

            i += 1
            if arguments[5] == "":
                title_url = "https://hammertime.cyou/"
            else:
                title_url = arguments[5]

            i += 1
            if arguments[6] == "":
                thumbnail_url = ""
            else:
                thumbnail_url = arguments[6]

            i += 1
            if arguments[7] == "":
                ping_list = ""
            else:
                id_list = arguments[7].split(",")
                clean_id_list = []
                for userid in id_list:
                    if util.represents_integer(userid):
                        clean_id_list.append(userid.strip())
                ping_list = ','.join(clean_id_list)

            i += 1
            emoji = arguments[8]
            #if argument[8] in self.bot.emojis or argument[8] in UNICODE_EMOJI['en']:
            #    emoji = argument[8]
            #else:
            #    emoji = util.emoji(argument[8])
        except Exception as e:
            await ctx.send(f"Error with provided arguments (arg {i}):```{e}```")
            return

        # HANDLE DATABASE STUFF

        con = sqlite3.connect(f'databases/timetables.db')
        cur = con.cursor()

        reminder_id = await self.reminder_counter()
        reminder_id = "R" + reminder_id

        cur.execute("INSERT INTO recurring VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (reminder_id, str(ctx.author.name), str(ctx.author.id), ping_list, time_interval, str(unix_timestamp), title, description, title_url, str(channel_id), channel_name, thumbnail_url, emoji))
        con.commit()
        await util.changetimeupdate()

        await ctx.send(f"Successfully added a recurring reminder with ID {reminder_id}!")

        # GIVE PREVIEW

        try:
            adapted_link = util.adapt_link(title_url)
        except Exception as e:
            print(e)
            adapted_link = title_url

        try:
            if adapted_link == "":
                embed=discord.Embed(title=title, description=description, color=0xf8de7e)
            else:
                embed=discord.Embed(title=title, url=adapted_link, description=description, color=0xf8de7e)
            if thumbnail_url != "":
                embed.set_thumbnail(url=thumbnail_url)
            embed.set_footer(text=f"This is a preview.")
            await channel.send(embed=embed)

            text = "**Additional info:**\n"
            text += f"{time_interval} reminder, next time set for <t:{unix_timestamp}:R>\n"
            text += "users who will be pinged: "
            if ping_list.strip() != "":
                text += ', '.join([f"<@{x.strip()}>" for x in ping_list.split(",")])
            else:
                text += "none"
            text += " " + emoji
            embed2=discord.Embed(title="", description=text[:4096], color=0x000000)
            await channel.send(embed=embed2)
        except Exception as e:
            print("Error while trying to send preview:",e)
    @_remind_recurring.error
    async def remind_recurring_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.group(name="reminders", aliases = ["reminder"], pass_context=True, invoke_without_command=True)
    @commands.check(util.is_active)
    async def _reminders(self, ctx):
        """Show the reminders you have in this channel

        has subcommands
        ```
        all
        remove
        🔒recurring
        ```
        """

        user_id = str(ctx.message.author.id)
        channel_id = str(ctx.channel.id)

        con = sqlite3.connect(f'databases/timetables.db')
        cur = con.cursor()
        reminder_list = [[item[0],item[1],item[2]] for item in cur.execute("SELECT reminder_id, utc_timestamp, remindertext FROM reminders WHERE userid = ? AND channel = ? ORDER BY reminder_id", (user_id, channel_id)).fetchall()]
        text = f"⏰ <@{user_id}>'s reminders in <#{channel_id}>:\n"
        if len(reminder_list) == 0:
            text += "_none_"
        else:
            for item in reminder_list:
                reminder_id = item[0]
                utc_timestamp = item[1]
                if len(item[2]) > 50:
                    remindertext = util.cleantext2(item[2][:47]) + "..."
                else:
                    remindertext = util.cleantext2(item[2])
                text += f"`{reminder_id}.` ~<t:{utc_timestamp}:f> : {remindertext}\n"
        embed=discord.Embed(title="", description=text[:4096], color=0x000000)

        # CHECK IF REMINDER FUNCTIONALITY IS ENABLED
        try:
            conB = sqlite3.connect(f'databases/botsettings.db')
            curB = conB.cursor()
            custom_reminders_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("reminder functionality",)).fetchall()]
            if len(custom_reminders_list) == 0:
                curB.execute("INSERT INTO serversettings VALUES (?, ?, ?, ?)", ("reminder functionality", "on", "", ""))
                conB.commit()
                enabled = "on"
            else:
                enabled = custom_reminders_list[0].lower().strip()

            if enabled != "on":
                embed.set_footer(text=f"Note: Reminder setting is turned off. Non-mods cannot create new reminders at the moment.")
        except Exception as e:
            print("Error while trying to fetch reminder functionality setting:", e)

        await ctx.send(embed=embed)
    @_reminders.error
    async def reminders_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_reminders.command(name="remove", aliases = ["delete"], pass_context=True)
    @commands.check(util.is_active)
    async def _reminders_remove(self, ctx, *args):
        """Remove reminder given by id number
        """
        user_id = str(ctx.message.author.id)

        # PARSE ARGUMENTS

        arguments = []
        recurring_arguments = []
        for arg in args:
            if arg.upper().startswith("R"):
                argnum = "R"
            else:
                argnum = ""
            try:
                num = str(int(''.join([x for x in arg if x in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]])))

                if argnum == "R":
                    argnum += num
                    recurring_arguments.append(argnum)
                else:
                    arguments.append(num)
            except Exception as e:
                print("Error in reminders.remove(). Could not parse provided reminder id:", e)

        user_perms = [p for p in ctx.author.guild_permissions]

        if (len(arguments) == 0) and ((len(recurring_arguments) == 0) or (('manage_guild', True) not in user_perms)):
            await ctx.send(f"Please provide valid arguments.")
            return

        # CHECK REMINDER IN DATABASE

        con = sqlite3.connect(f'databases/timetables.db')
        cur = con.cursor()
        reminder_list = [[item[0],item[1],item[2],item[3]] for item in cur.execute("SELECT reminder_id, utc_timestamp, remindertext, channel FROM reminders WHERE userid = ? ORDER BY reminder_id", (user_id,)).fetchall()]

        reminders_to_remove = []
        recurring_reminders_to_remove = []
        for item in reminder_list:
            reminder_id = item[0]
            if reminder_id in arguments:
                reminders_to_remove.append(item)

        if ('manage_guild', True) in user_perms:
            recurring_reminders_to_remove = []
            recurring_reminder_list = [[item[0],item[1],item[2],item[3]] for item in cur.execute("SELECT reminder_id, next_time, remindertext, channel FROM recurring ORDER BY reminder_id").fetchall()]

            for item in recurring_reminder_list:
                recurring_reminder_id = item[0]
                if recurring_reminder_id in recurring_arguments:
                    recurring_reminders_to_remove.append(item)

        if len(reminders_to_remove) == 0 and len(recurring_reminders_to_remove) == 0:
            await ctx.send(f"You cannot remove any of these reminders.")
            return

        # REMOVE REMINDERS (REGULAR)

        text_removed = ""
        if len(reminders_to_remove) > 0:
            text_removed += "**Removed reminder(s):**\n"

            for item in reminders_to_remove:
                reminder_id = item[0]
                utc_timestamp = item[1]
                if len(item[2]) > 50:
                    remindertext = util.cleantext2(item[2][:47]) + "..."
                else:
                    remindertext = util.cleantext2(item[2])
                channel_id = item[3]
                cur.execute("DELETE FROM reminders WHERE userid = ? AND reminder_id = ?", (user_id, reminder_id))
                con.commit()
                text_removed += f"`{reminder_id}.` <t:{utc_timestamp}:f> in <#{channel_id}> : {remindertext}\n"

        # REMOVE REMINDERS (RECURRING)

        if len(recurring_reminders_to_remove) > 0:
            text_removed += "\n**Removed recurring reminder(s):**\n"

            for item in recurring_reminders_to_remove:
                reminder_id = item[0]
                utc_timestamp = item[1]
                if len(item[2]) > 50:
                    remindertext = util.cleantext2(item[2][:47]) + "..."
                else:
                    remindertext = util.cleantext2(item[2])
                channel_id = item[3]
                cur.execute("DELETE FROM recurring WHERE reminder_id = ?", (reminder_id,))
                con.commit()
                text_removed += f"`{reminder_id}.` <t:{utc_timestamp}:f> in <#{channel_id}> : {remindertext}\n"

        await util.changetimeupdate()
        embed=discord.Embed(title="", description=text_removed[:4096], color=0x000000)
        await ctx.send(embed=embed)
    @_reminders_remove.error
    async def reminders_remove_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_reminders.command(name="all", aliases = ["allchannels", "every", "everywhere"], pass_context=True)
    @commands.check(util.is_active)
    async def _reminders_allchannels(self, ctx, *args):
        """Show your reminders in ALL channels of this server
        """
        
        user_id = str(ctx.message.author.id)

        con = sqlite3.connect(f'databases/timetables.db')
        cur = con.cursor()
        reminder_list = [[item[0],item[1],item[2],item[3]] for item in cur.execute("SELECT reminder_id, utc_timestamp, remindertext, channel FROM reminders WHERE userid = ? ORDER BY reminder_id", (user_id,)).fetchall()]
        text = f"⏰ All of <@{user_id}>'s reminders:\n"
        if len(reminder_list) == 0:
            text += "_none_"
        else:
            for item in reminder_list:
                reminder_id = item[0]
                utc_timestamp = item[1]
                if len(item[2]) > 50:
                    remindertext = util.cleantext2(item[2][:47]) + "..."
                else:
                    remindertext = util.cleantext2(item[2])
                channel_id = item[3]
                text += f"`{reminder_id}.` ~<t:{utc_timestamp}:f> in <#{channel_id}>: {remindertext}\n"
        embed=discord.Embed(title="", description=text[:4096], color=0x000000)

        # CHECK IF REMINDER FUNCTIONALITY IS ENABLED
        try:
            conB = sqlite3.connect(f'databases/botsettings.db')
            curB = conB.cursor()
            custom_reminders_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("reminder functionality",)).fetchall()]
            if len(custom_reminders_list) == 0:
                curB.execute("INSERT INTO serversettings VALUES (?, ?, ?, ?)", ("reminder functionality", "on", "", ""))
                conB.commit()
                enabled = "on"
            else:
                enabled = custom_reminders_list[0].lower().strip()

            if enabled != "on":
                embed.set_footer(text=f"Note: Reminder setting is turned off. Non-mods cannot create new reminders at the moment.")
        except Exception as e:
            print("Error while trying to fetch reminder functionality setting:", e)

        await ctx.send(embed=embed)
    @_reminders_allchannels.error
    async def reminders_allchannels_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_reminders.command(name="recurring", aliases = ["allrecurring"], pass_context=True)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _reminders_recurring(self, ctx, *args):
        """🔒Show all recurring reminders on this server
        """

        con = sqlite3.connect(f'databases/timetables.db')
        cur = con.cursor()
        reminder_list = [[item[0],item[1],item[2],item[3],item[4],item[5]] for item in cur.execute("SELECT reminder_id, next_time, remindertext, channel, interval, remindertitle FROM recurring ORDER BY reminder_id").fetchall()]
        text = f"♻️⏰ All recurring reminders:\n"
        if len(reminder_list) == 0:
            text += "_none_"
        else:
            for item in reminder_list:
                reminder_id = item[0]
                utc_timestamp = item[1]
                if len(item[2]) > 50:
                    remindertext = util.cleantext2(item[2][:47]) + "..."
                else:
                    remindertext = util.cleantext2(item[2])
                channel_id = item[3]
                interval = item[4]
                if len(item[5]) > 50:
                    title = util.cleantext2(item[5][:47]) + "..."
                else:
                    title = util.cleantext2(item[5])
                text += f"`{reminder_id}.` ~<t:{utc_timestamp}:f> {interval} in <#{channel_id}>: [**{title}**] {remindertext}\n"

        embed=discord.Embed(title="", description=text, color=0x000000)
        await ctx.send(embed=embed)
    @_reminders_recurring.error
    async def reminders_recurring_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name="schedule", aliases = ["scheduling"])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_active)
    @commands.check(util.is_main_server)
    async def _schedule(self, ctx, *args):
        """🔒 Schedule a message
        """
        await ctx.send("Under construction.")

    @_schedule.error
    async def schedule_error(self, ctx, error):
        await util.error_handling(ctx, error)
        


    @commands.command(name="selfmute", aliases = ["selftimeout"])
    @commands.check(util.is_active)
    @commands.check(util.is_main_server)
    async def _selfmute(self, ctx, *args):
        """Mutes you for given amount of time

        i.e. `<prefix>selfmute 2 hours`
        """
        # PRE CHECK

        try:
            con = sqlite3.connect(f'databases/botsettings.db')
            cur = con.cursor()
            timeout_list = [item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("timeout system",)).fetchall()]
            if len(timeout_list) == 0:
                await ctx.send("Error: No timeout system entry in database.")
                return 
            else:
                timeout = timeout_list[0]
        except Exception as e:
            print(e)
            await ctx.send("Error with timeout system in database.")
            return

        if timeout == "off":
            await ctx.send(f"Timeout system is not enabled.\nAsk mods to enable it. `{self.prefix}help set timeout` for more info.")
            return

        if len(args) < 1:
            await ctx.send("Error: Missing time argument.")
            return

        # MEMBER

        the_member = ctx.author
        user_id = str(the_member.id)
        user_perms = [p for p in the_member.guild_permissions]
        
        if ('manage_guild', True) in user_perms:
            emoji = util.emoji("shy")
            await ctx.send(f"I- I don't want to mute you. {emoji}")
            return

        # FETCH TIME

        try:
            argument_string = ' '.join(args)
            now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())
            timeseconds, timetext, reason = await util.timeparse(argument_string, now)
        except Exception as e:
            await ctx.send(f"Error while trying to fetch time: {e}")
            return

        if timeseconds == "infinity":
            emoji = util.emoji("cover_eyes")
            await ctx.send(f"Could not properly parse time. {emoji}")
            return
        else:
            if int(timeseconds) < 0:
                await ctx.send(f"Error: Given time is negative.")
                return
            elif int(timeseconds) < 60:
                await ctx.send(f"Timeout time is too short for me to act.")
                return


        # FETCH TIMEOUT ROLE

        try:
            con = sqlite3.connect(f'databases/botsettings.db')
            cur = con.cursor()
            timeoutrole_id = int([item[0] for item in cur.execute("SELECT role_id FROM specialroles WHERE name = ?", ("timeout role",)).fetchall()][0])
        except Exception as e:
            print(e)
            await ctx.send(f"Error: Missing Timeout role in database.")
            return

        for role in ctx.guild.roles:
            if role.id == timeoutrole_id:
                timeout_role = role
                break 
        else:
            await ctx.send(f"Error: Could not find Timeout role.")
            return

        # SAVE MEMBERs ROLES (FOR LATER UNMUTE)

        member_role_ids = []
        member_roles = []
        for role in the_member.roles:
            if role.id != ctx.guild.id: #ignore @everyone role
                member_role_ids.append(role.id)
                member_roles.append(role)

        role_id_liststr = str(member_role_ids)
        username = str(the_member.name)

        if timeout_role.id in member_role_ids: # check if user already has timeout role
            emoji = util.emoji("think")
            await ctx.send(f"User already muted. {emoji}")
            return

        utc_now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds()) 
        utc_timestamp = str(utc_now + int(timeseconds))

        con = sqlite3.connect(f'databases/timetables.db')
        cur = con.cursor()
        cur.execute("INSERT INTO timeout VALUES (?, ?, ?, ?)", (username, user_id, utc_timestamp, role_id_liststr))
        con.commit()
        await util.changetimeupdate()


        # TIMEOUT MEMBER

        try:
            await the_member.edit(roles=[timeout_role])
        except Exception as e:
            print(e)
            try:
                for r in member_roles:
                    if r.id != ctx.guild.id: #ignore @everyone role
                        try:
                            await the_member.remove_roles(r)
                        except:
                            print(f"Error with: {r}, {r.id}")
                await the_member.add_roles(timeout_role)
            except Exception as e:
                print(e)
                await ctx.send(f"Error while trying to change roles.")
                return
        muteemoji = util.emoji("mute")

        # RESPONSE

        description = f"Muted <@{user_id}> for {timetext}. {muteemoji}"
        header = "Selfmute"
        embed=discord.Embed(title=header, description=description, color=0x4863A0)
        await ctx.send(embed=embed)

        # DM THE USER
        #if True:
        #    try:
        #        user = await self.bot.fetch_user(int(user_id))
        #        if timeseconds == "infinity":
        #            timespec = ""
        #        else:
        #            timespec = f" for {timetext}"
        #        message = f"You have been muted in {ctx.guild.name}{timespec}."
        #        embed=discord.Embed(title="", description=message, color=0x4863A0)
        #        await user.send(embed=embed)
        #        print("Successfully notified user.")
        #    except Exception as e:
        #        print("Error while trying to DM muted user:", e)

    @_selfmute.error
    async def selfmute_error(self, ctx, error):
        await util.error_handling(ctx, error)




    ####################################### calendar functionality #############################################


    async def show_calendar(self, ctx):
        await ctx.send("⚠️ under construction")



    @commands.group(name="calendar", aliases = ["kalender", "showcalendar"], pass_context=True, invoke_without_command=True)
    @commands.check(util.is_active)
    async def _calendar(self, ctx):
        """Calendar functionality 

        Has subcommands:
        ```
        🔒add 
        🔒remove 
        show
        ```
        """

        # show calendar help
        await ctx.send("⚠️ under construction")
    @_calendar.error
    async def calendar_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_calendar.command(name="show", aliases = ["display"], pass_context=True)
    @commands.check(util.is_active)
    async def _calendar_display(self, ctx, *args):
        """Show calendar

        you can give days, months or weeks as argument or `next`, i.e.
        `<prefix>calendar show 31/01` (next January 31st)
        or
        `<prefix>calendar show 12` (show December)
        or
        `<prefix>calendar show week 28` (show 28th calender week)
        or
        `<prefix>calendar show next` (show next few calendar entries)
        """

        await self.show_calendar(ctx)
    @_calendar_display.error
    async def calendar_display_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_calendar.command(name="add", aliases = ["insert"], pass_context=True)
    @commands.check(util.is_active)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _calendar_add(self, ctx, *args):
        """🔒 Add item to calendar
        
        Arg 1: <date> in YYYY-MM-DD or DD-MM-YYYY format (slashes or dots work as well)
        Arg 2: <emoji>
        Arg 3: <item name/content>

        Optional: add argument `!recurring` or `!yearly` to make it a recurring entry every year or `!monthly` to make it recurring every month.
        Optional: add argument `!ping` to make it ping you. Per default the calendar notifications are sent to the bot spam channel at about 1pm UTC. You can specify a different UTC hour via e.g. `!ping:15` for 3pm UTC
        """
        await ctx.send("⚠️ under construction")
    @_calendar_add.error
    async def calendar_add_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_calendar.command(name="remove", aliases = ["delete"], pass_context=True)
    @commands.check(util.is_active)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _calendar_remove(self, ctx, *args):
        """🔒 Remove item from calendar

        Arg 1: date in YYYY-MM-DD or DD-MM-YYYY format (slashes or dots work as well)
        Arg 2: item index
        """
        await ctx.send("⚠️ under construction")
    @_calendar_remove.error
    async def calendar_remove_error(self, ctx, error):
        await util.error_handling(ctx, error)


    


    ############################################################################################################################
    ############################################################################################################################
    ############################################################################################################################
    ############################################################################################################################
    ############################################################################################################################
    ############################################################################################################################
    ############################################################################################################################
    ############################################################################################################################
    ############################################################################################################################
    ############################################################################################################################
    ############################################################################################################################
    ############################################################################################################################
    ############################################################################################################################
    ############################################################################################################################
    ############################################################################################################################



    ############################# QUOTES #######################################################################################



    @commands.group(name="quote", aliases = ["q"], pass_context=True, invoke_without_command=True)
    @commands.check(util.is_active)
    async def _quote(self, ctx, *args):
        """Show quote
        """
        await ctx.send("⚠️ under construction")
    @_quote.error
    async def quote_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_quote.command(name="add", pass_context=True)
    @commands.check(util.is_active)
    async def _quote_add(self, ctx, *args):
        """Add quote"""
        
        await ctx.send("⚠️ under construction")

    @_quote_add.error
    async def quote_add_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_quote.command(name="remove", pass_context=True)
    @commands.check(util.is_active)
    async def _quote_remove(self, ctx, *args):
        """Remove quote"""
        
        await ctx.send("⚠️ under construction")
        
    @_quote_remove.error
    async def quote_remove_error(self, ctx, error):
        await util.error_handling(ctx, error)



    ############################# GEODATA #######################################################################################



    async def get_geodata(self, ctx, args):
        # INITIALISE API DATA
        try:
            API_KEY = os.getenv("openweathermap_key")
            if API_KEY is None:
                raise ValueError("No OpenWeatherMap API Key")
        except:
            emoji = util.emoji("disappointed")
            raise ValueError(f"No API key provided. {emoji}\n||(Ask mods to create a free OpenWeatherMap account and get an API key.)||")
            return

        try: # cooldown to not trigger actual rate limits or IP blocks
            await util.cooldown(ctx, "openweathermap")
        except Exception as e:
            await util.cooldown_exception(ctx, e, "openweathermap")
            return

        try:
            version = util.get_version().replace("version","v").replace(" ","").strip()
        except:
            version = "v_X"
        USER_AGENT = f'MDM_Bot_{version}'
        headers = {'user-agent': USER_AGENT}

        # PARSE ARGUMENTS

        city_string = "" # sometimes the returned city name is very specific and lacks the city name, for this case we save the city name here

        if len(args) == 0:
            conU = sqlite3.connect('databases/userdata.db')
            curU = conU.cursor()
            loc_list = [[item[0],item[1],item[2]] for item in curU.execute("SELECT longitude, latitude, city FROM location WHERE user_id = ?", (str(ctx.author.id),)).fetchall()]
            if len(loc_list) == 0:
                raise ValueError(f"No location was set.\nUse `{self.prefix}we set <city>, <country>` to set location.")
                return

            longitude = loc_list[0][0]
            latitude = loc_list[0][1]
            city_string = loc_list[0][2]

        else:
            # GET WEATHER DIRECTLY VIA ZIP CODE
            pre_parse = re.split(r",| |;", ' '.join(args))
            if util.represents_integer(pre_parse[0]):
                zip_code = str(int(pre_parse[0]))
                arguments = re.split(r",|;", ' '.join(args))
                try:
                    country = util.isocode(arguments[1].strip())
                except:
                    country = "US"

                location = f"{zip_code.strip()},{country.lower().strip()}"
                print(f"ZIP: {zip_code}\ncountry: {country}")
                payload = {
                    'zip': location,
                    'appid': API_KEY,
                    'format': 'json'
                }
                # GET WEATHER DATA
                url = 'https://api.openweathermap.org/data/2.5/weather'
                response = requests.get(url, headers=headers, params=payload)
                rjson = response.json()
                print(rjson)
                try:
                    longitude = rjson['coord']['lon']
                    latitude =  rjson['coord']['lat']
                except:
                    longitude = ""
                    latitude = ""
                return rjson, city_string, longitude, latitude

            else:
                # GET COORDINATES FIRST BY CITY/COUNTRY NAME
                arguments = re.split(r",|;", ' '.join(args))
                if len(arguments) >= 3:
                    city = arguments[0].strip()
                    country = util.isocode(arguments[2])
                    if country == "US":
                        state = util.us_state_code(arguments[1].strip())
                    else:
                        state = arguments[1].strip()
                    location = f"{city},{state},{country}"

                elif len(arguments) == 2:
                    city = arguments[0].strip()
                    country = util.isocode(arguments[1].strip())
                    state = ""

                    if country == "ERROR":
                        state = util.us_state_code(arguments[1].strip())
                        if len(state) == 2:
                            country = "US"
                            location = f"{city},{state},{country}"
                        else:
                            location = f"{city},{arguments[1].strip().lower()}"
                    else:
                        location = f"{city},{country}"

                else:
                    city = arguments[0].strip()
                    country = ""
                    state = ""
                    location = city
                print(f"country: {country}\nstate: {state}\ncity: {city}")

                # GET GEO COORDINATES
                url = 'http://api.openweathermap.org/geo/1.0/direct'
                payload = {
                        'q': location,
                        'limit': '10',
                        'appid': API_KEY,
                        'format': 'json'
                    }
                response = requests.get(url, headers=headers, params=payload)
                rjson = response.json()

                # SECOND TRY
                if len(rjson) == 0 and state == "":
                    await asyncio.sleep(1)
                    if country != "":
                        payload = {
                                'q': f"{city},{country},US",
                                'limit': '10',
                                'appid': API_KEY,
                                'format': 'json'
                        }
                    else:
                        city_list = city.split()
                        if len(city_list) == 1:
                            if len(city.strip()) > 2:
                                city_list = [city.strip()[:-2].strip(), city.strip()[-2:]]
                            else:
                                emoji = util.emoji("sad")
                                raise ValueError(f"No such location found. {emoji}")
                        city = ' '.join(city_list[:-1])
                        state = util.us_state_code(city_list[-1])
                        if len(state) == 2:
                            location = f"{city},{state},US"
                        else:
                            country = util.isocode(city_list[-1])
                            if country != "ERROR":
                                location = f"{city},{country}"
                            else:
                                location = f"{city},{city_list[-1]}"
                        payload = {
                                'q': location,
                                'limit': '10',
                                'appid': API_KEY,
                                'format': 'json'
                        }
                    response = requests.get(url, headers=headers, params=payload)
                    rjson = response.json()

                if len(rjson) == 0:
                    emoji = util.emoji("disappointed")
                    raise ValueError(f"No such location found. {emoji}")
                    return

                city_string = city.title()
                city_check = {}

                # CALCULATE SOME SORT OF PLAUSIBILITY
                i = 0
                for r in rjson:
                    city_check[i] = 0

                    local_names = []
                    try:
                        for x in r['local_names']:
                            local_names.append(r['local_names'][x].lower().replace(" ","").replace("-",""))
                    except:
                        pass

                    try:
                        if city.lower().replace(" ","").replace("-","") == r['name'].replace(" ","").replace("-",""):
                            city_check[i] += 24
                        elif city.lower().replace(" ","").replace("-","") in local_names:
                            city_check[i] += 20
                        elif util.alphanum(city,"lower") in util.alphanum(r['name'],"lower"):
                            city_check[i] += 16
                        else:
                            for ln in local_names:
                                if util.alphanum(city,"lower") in util.alphanum(ln,"lower"):
                                    city_check[i] += 8
                                    break
                    except:
                        pass
                    try:
                        if country.lower().replace(" ","").replace("-","") == r['country'].replace(" ","").replace("-",""):
                            city_check[i] += 10
                        elif util.alphanum(country,"lower") in util.alphanum(r['country'],"lower"):
                            city_check[i] += 6
                    except:
                        pass
                    try:
                        if state.lower().replace(" ","").replace("-","") == r['state'].replace(" ","").replace("-",""):
                            city_check[i] += 5
                        elif util.alphanum(state,"lower") in util.alphanum(r['state'],"lower"):
                            city_check[i] += 3
                    except:
                        pass
                    i += 1

                index_with_highest_plausibility = 0
                for j in city_check:
                    if city_check[j] > city_check[index_with_highest_plausibility]:
                        index_with_highest_plausibility = j

                latitude = rjson[index_with_highest_plausibility]['lat']
                longitude = rjson[index_with_highest_plausibility]['lon']
                try:
                    city_string = rjson[index_with_highest_plausibility]['name']
                except Exception as e:
                    print("Error during weather command while trying to fetch city name from json response:", e)

        # GET WEATHER DATA
        url = 'https://api.openweathermap.org/data/2.5/weather'
        payload = {
                'lat': latitude,
                'lon': longitude,
                'appid': API_KEY,
            }
        payload['format'] = 'json'
        response = requests.get(url, headers=headers, params=payload)
        rjson = response.json()
        try:
            error_code = rjson['cod']
            msg = rjson['message']
            if error_code == '404' or msg == 'city not found':
                raise ValueError("Place not found.")
        except:
            pass
        return rjson, city_string, latitude, longitude



    def temperature_string(self, kelvin1, *kelvin2args):
        celsius1 = round(kelvin1-273.15,1)
        fahrenheit1 = round((kelvin1-273.15) * 9/5 + 32,1)

        if len(kelvin2args) == 0:
            temperature = f"{celsius1}°C ({fahrenheit1}°F)"
        else:
            kelvin2 = float(kelvin2args[0])
            celsius2 = round(kelvin2-273.15,1)
            fahrenheit2 = round((kelvin2-273.15) * 9/5 + 32,1)
            temperature = f"{celsius1}°C - {celsius2}°C ({fahrenheit1}°F - {fahrenheit2}°F)"
        return temperature



    def wind_direction(self, deg):
        direction_dict = OrderedDict()
        direction_dict[0]     = "N"
        direction_dict[22.5]  = "NNE"
        direction_dict[45]    = "NE"
        direction_dict[67.5]  = "ENE"
        direction_dict[90]    = "E"
        direction_dict[112.5] = "ESE"
        direction_dict[135]   = "SE"
        direction_dict[157.5] = "SSE"
        direction_dict[180]   = "S"
        direction_dict[202.5] = "SSW"
        direction_dict[225]   = "SW"
        direction_dict[247.5] = "WSW"
        direction_dict[270]   = "W"
        direction_dict[292.5] = "WNW"
        direction_dict[315]   = "NW"
        direction_dict[337.5] = "NNW"
        direction_dict[360]   = "N"
        direction = "?"
        for d in direction_dict:
            if deg > d - 11.25:
                direction = direction_dict[d]
            else:
                break
        return direction



    def speed_string(self, x):
        """convert x from m/s"""
        kmh = int(round(3.6 * x, 0))
        mph = int(round(2.236936 * x, 0))
        speed = f"{kmh}km/h ({mph}mp/h)"
        return speed



    def weatheremoji(self, s): # also adds a gap
        emoji_dict = {
                # CLEAR
                "clear sky": " ☀️",
                # CLOUDS
                "few clouds": " 🌤️",
                "scattered clouds": " ⛅",
                "broken clouds": " 🌥️",
                "overcast clouds": " ☁️",
                # RAIN
                "shower rain": " 🌧️",
                "rain": " 🌧️",
                "light intensity drizzle": " 🌦️",
                "drizzle": " 🌦️",
                "heavy intensity drizzle": " 🌦️",
                "light intensity drizzle rain": " 🌦️",
                "drizzle rain": " 🌦️",
                "heavy intensity drizzle rain": " 🌦️",
                "shower rain and drizzle": " 🌦️",
                "heavy shower rain and drizzle": " 🌦️",
                "shower drizzle": " 🌦️",
                "light rain": " 🌧️",
                "moderate rain": " 🌧️",
                "heavy intensity rain": " 🌧️",
                "very heavy rain": " 🌧️",
                "extreme rain": " 🌧️",
                "freezing rain": " 🌧️",
                "light intensity shower rain": " 🌧️",
                "shower rain": " 🌧️",
                "heavy intensity shower rain": " 🌧️",
                "ragged shower rain": " 🌧️",
                # THUNDER
                "thunderstorm ": " 🌩️",
                "thunderstorm with light rain": " ⛈️",
                "thunderstorm with rain": " ⛈️",
                "thunderstorm with heavy rain": " ⛈️",
                "light thunderstorm": " 🌩️",
                "heavy thunderstorm": " 🌩️",
                "ragged thunderstorm": " 🌩️",
                "thunderstorm with light drizzle": " ⛈️",
                "thunderstorm with drizzle": " ⛈️",
                "thunderstorm with heavy drizzle": " ⛈️",
                "": "",
                # SNOW
                "snow": " ❄️",
                "light snow": " ❄️",
                "heavy snow": " ❄️",
                "sleet": " 🌨️",
                "light shower sleet": " 🌨️",
                "shower sleet": " 🌨️",
                "light rain and snow": " 🌨️",
                "rain and snow": " 🌨️",
                "light shower snow": " 🌨️",
                "shower snow": " 🌨️",
                "heavy shower snow": " 🌨️",
                # ATMOSPHERE
                "mist": " 🌫️",
                "smoke": " 🌫️",
                "haze": " 🌫️",
                "sand/dust whirls": " 🌫️",
                "fog": " 🌫️",
                "sand": " 🌫️",
                "dust": " 🌫️",
                "volcanic ash": " 🌋",
                "squalls": " 💨",
                "tornado": " 🌪️",
            }

        if s.lower().strip() in emoji_dict:
            return emoji_dict[s.lower().strip()]
        else:
            return ""



    async def get_forecast(self, ctx, latitude, longitude):
        # INITIALISE API DATA
        try:
            API_KEY = os.getenv("openweathermap_key")
            if API_KEY is None:
                raise ValueError("No OpenWeatherMap API Key")
        except Exception as e:
            print("Error while fetching OpenWeatherMap API Key", e)
            return ""

        try:
            version = util.get_version().replace("version","v").replace(" ","").strip()
        except:
            version = "v_X"
        USER_AGENT = f'MDM_Bot_{version}'
        headers = {'user-agent': USER_AGENT}

        string = ""

        # GET WEATHER DATA
        url = 'https://api.openweathermap.org/data/2.5/forecast'
        payload = {
                'lat': latitude,
                'lon': longitude,
                'appid': API_KEY,
            }
        payload['format'] = 'json'
        response = requests.get(url, headers=headers, params=payload)
        rjson = response.json()
        try:
            error_code = rjson['cod']
            msg = rjson['message']
            if error_code == '404' or msg == 'city not found':
                raise ValueError("Place not found.")
        except:
            pass

        try:
            forecast_list = rjson['list']
            string_list = []

            for item in forecast_list:
                try:
                    dt = item['dt']
                    temp = item['main']['temp']
                    humidity = item['main']['humidity']
                    weather_list = item['weather']
                    weather_string = ', '.join([x['description'] + self.weatheremoji(x['description']) for x in weather_list])
                    pop = item['pop'] # probability of precipitation

                    #string_list.append(f"<t:{dt}:t> {weather_string} `{self.temperature_string(temp)}` Precipitation: {round(pop*100)}%\n")
                    string_list.append(f"<t:{dt}:t> {weather_string} `{self.temperature_string(temp)}` 💧{round(pop*100)}%\n")
                except Exception as e:
                    print("Error:", e)

            if len(string_list) > 0:
                string += "\n**Forecast:** \n"
                i = 0
                for forecast in string_list:
                    string += forecast
                    i += 1

                    if i > 7:
                        break

        except Exception as e:
            print("Error while parsing forecast data:", e)

        return string




    @commands.group(name="tz", aliases = ["time","timezone"], pass_context=True, invoke_without_command=True)
    @commands.check(util.is_active)
    async def _timezone_by_location(self, ctx, *args):
        """Show time of given location
        
        Give argument `<city>, <country>` or to be more precise `<city>, <state>, <country>`.
        You can also use `<zip code>, <country>`

        You can also set your location with `-tz set <location>` and remove it with `-tz remove`.
        """

        try:
            rjson, city_name, latitude, longitude = await self.get_geodata(ctx, args)
        except:
            await ctx.send(f"Error: {e}")
            return

        try:
            country = rjson['sys']['country']
            name = rjson['name']
        except Exception as e1:
            try:
                conU = sqlite3.connect('databases/userdata.db')
                curU = conU.cursor()
                loc_list = [[item[0],item[1]] for item in curU.execute("SELECT city, country FROM location WHERE user_id = ?", (str(ctx.author.id),)).fetchall()]
                country = loc_list[0][1]
                name = loc_list[0][0]
            except Exception as e2:
                print(f"Error while trying to fetch country and city:\n>{e1}\n>{e2}")
                await ctx.send("Error: Place not found.")

        offset_sec = int(rjson['timezone'])
        offset_hrs = abs(int(offset_sec/3600))
        offset_xmin = int(round(abs(offset_sec) - 3600*abs(offset_hrs),0)/60)
        offset_string = f"{offset_hrs}:{str(offset_xmin).zfill(2)}"

        if offset_sec >= 0: 
            pm = "+"
        else:
            pm = "-"

        utc_now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())
        datetime_text = datetime.datetime.utcfromtimestamp(utc_now+offset_sec).strftime('%Y-%m-%d %H:%M:%S')

        if city_name != "" and util.alphanum(city_name,"lower") != util.alphanum(name,"lower"):
            name = city_name + f" ({name})"
        await ctx.send(f"{name}, {country} is in timezone UTC{pm}{offset_string}.\nCurrently: `{datetime_text}`")

    @_timezone_by_location.error
    async def timezone_by_location_error(self, ctx, error):
        await util.error_handling(ctx, error)



    async def weather_command(self, ctx, args, forecast):
        try:
            rjson, city_name, latitude, longitude = await self.get_geodata(ctx, args)
        except Exception as e:
            await ctx.send(f"Error: {e}")
            return

        print(rjson)

        forecast_data = ""
        if forecast:
            try:
                forecast_data = await self.get_forecast(ctx, latitude, longitude)
            except Exception as e:
                print("Error while trying to fetch forecast:", e)

        try:
            country = rjson['sys']['country']
            name = rjson['name']
        except Exception as e1:
            try:
                longitude = rjson['coord']['lon']
                latitude =  rjson['coord']['lat']
                country = f"lon: {longitude}, lat: {latitude}"
                name = "unnamed place"
            except Exception as e2:
                print(f"Error while trying to fetch country and city:\n>{e1}\n>{e2}")
                await ctx.send(f"Error: Place not found.\n(If you meant to use the *whoknows* command that'd be `{self.prefix}wk`)")
                return

        # PARSE FROM RESPONSE
        try:
            weather_list = [[x['main'],x['description'],x['icon']] for x in rjson['weather']]
        except:
            try:
                weather_list = [rjson['weather'][0]['main'], rjson['weather'][0]['description'], rjson['weather'][0]['icon']]
            except:
                weather_list = []
        try:
            temperature = self.temperature_string(rjson['main']['temp'])
        except:
            temperature = "?"
        try:
            temperature_feels = self.temperature_string(rjson['main']['feels_like'])
        except:
            temperature_feels = "?"
        try:
            temperature_span = self.temperature_string(rjson['main']['temp_min'], rjson['main']['temp_max'])
        except:
            temperature_span = "?"

        try:
            humidity = rjson['main']['humidity']
        except:
            humidity = "?"
        try:
            pressure = rjson['main']['pressure'] #hPa
        except:
            pressure = "?"
        try:
            wind_speed = rjson['wind']['speed']
        except:
            wind_speed = "?"
        try:
            wind_degree = rjson['wind']['deg']
        except:
            wind_degree = "?"


        # STRING TEMP/WIND DATA

        if len(weather_list) == 0:
            header = "no weather data"
            icon_url = ""
        else:
            icon = weather_list[0][2]
            icon_url = f"http://openweathermap.org/img/wn/{icon}@2x.png"

            descriptions = []
            for weather in weather_list:
                descriptions.append(f"{weather[1]}{self.weatheremoji(weather[1])}")
            header = ', '.join(descriptions)

        if temperature == "?":
            text = ""
        elif temperature_feels == "?":
            text = f"**{temperature}**\n"
        else:
            text = f"**{temperature}** feels like {temperature_feels}\n"

        if temperature_span != "?":
            text += f"[span: {temperature_span}]\n"

        if humidity != "?":
            text += f"Humidity: {humidity}%\n"

        if wind_speed == "?" or wind_degree == "?":
            pass
        else:
            text += f"Wind: {self.wind_direction(wind_degree)} @ {self.speed_string(wind_speed)}\n"

        if forecast_data != "":
            text += forecast_data

        if city_name != "" and util.alphanum(city_name,"lower") != util.alphanum(name,"lower") and f"({name})" not in city_name:
            name = city_name + f" ({name})"

        embed=discord.Embed(title=header, description=text.strip(), color=0xEA6D4A)
        if not forecast:
            embed.set_thumbnail(url=icon_url)
        embed.set_footer(text=f"{name}, {country}")
        await ctx.send(embed=embed)



    @commands.group(name="weather", aliases = ["we","wth", "ww"], pass_context=True, invoke_without_command=True)
    @commands.check(util.is_active)
    async def _weather_by_location(self, ctx, *args):
        """Show weather of given location

        Give argument `<city>` or `<city>, <country>` or `<city>, <state>, <country>`.
        You can also use `<zip code>, <country>`

        You can also set your location with `-we set <location>` and remove it with `-we remove`.
        """
        forecast = False
        await self.weather_command(ctx, args, forecast)

    @_weather_by_location.error
    async def weather_by_location_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name="weatherforecast", aliases = ["wf"], pass_context=True, invoke_without_command=True)
    @commands.check(util.is_active)
    async def _weatherforecast_by_location(self, ctx, *args):
        """Show weather forecast of given location

        Give argument `<city>` or `<city>, <country>` or `<city>, <state>, <country>`.
        You can also use `<zip code>, <country>`

        You can also set your location with `<prefix>we set <location>` and remove it with `<prefix>we remove`.
        """
        forecast = True
        await self.weather_command(ctx, args, forecast)

    @_weatherforecast_by_location.error
    async def weatherforecast_by_location_error(self, ctx, error):
        await util.error_handling(ctx, error)



    async def set_location(self, ctx, args):
        if len(args) == 0:
            raise ValueError("Command needs location argument.")

        # FETCH INFO FROM API

        try:
            rjson, city_name, latitude, longitude = await self.get_geodata(ctx, args)
        except Exception as e:
            await ctx.send(f"Error: {e}")
            return

        try:
            country = rjson['sys']['country']
            city = rjson['name']
            state = ""
            longitude = rjson['coord']['lon']
            latitude =  rjson['coord']['lat']
        except Exception as e:
            print("Error while trying to fetch city name and country:", e)
            raise ValueError("Error 404: Place not found.")
            return

        if city_name != "" and util.alphanum(city_name,"lower") != util.alphanum(city,"lower"):
            city = city_name + f" ({city})"

        # EDIT DATABASE

        conU = sqlite3.connect('databases/userdata.db')
        curU = conU.cursor()
        loc_list = [item[0] for item in curU.execute("SELECT city FROM location WHERE user_id = ?", (str(ctx.author.id),)).fetchall()]

        if len(loc_list) == 0:
            curU.execute("INSERT INTO location VALUES (?, ?, ?, ?, ?, ?, ?)", (str(ctx.author.id), str(ctx.author.name), city, state, country, longitude, latitude))
            conU.commit()
        else:
            curU.execute("UPDATE location SET city = ?, state = ?, country = ?, longitude = ?, latitude = ? WHERE user_id = ?", (city_name, state, country, longitude, latitude, str(ctx.author.id)))
            conU.commit()
        await util.changetimeupdate()

        await ctx.send(f"Set your location to {city}, {country}!\n`lon: {longitude}, lat: {latitude}`")



    async def remove_location(self, ctx, args):
        conU = sqlite3.connect('databases/userdata.db')
        curU = conU.cursor()
        loc_list = [item[0] for item in curU.execute("SELECT city FROM location WHERE user_id = ?", (str(ctx.author.id),)).fetchall()]

        if len(loc_list) == 0:
            emoji = util.emoji("think")
            await ctx.send(f"No location of yours in database. {emoji}")
        else:
            curU.execute("DELETE FROM location WHERE user_id = ?", (str(ctx.author.id),))
            conU.commit()
            await util.changetimeupdate()
            await ctx.send("Deleted your location from database!")
        


    @_weather_by_location.command(name="set", pass_context=True)
    @commands.check(util.is_active)
    async def _set_location_w(self, ctx, *args):
        """Set location for weather and timezone command"""
        try:
            await self.set_location(ctx, args)
        except Exception as e:
            await ctx.send(f"Error: {e}")
    @_set_location_w.error
    async def set_location_w_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_timezone_by_location.command(name="set", pass_context=True)
    @commands.check(util.is_active)
    async def _set_location_t(self, ctx, *args):
        """Set location for weather and timezone command"""
        try:
            await self.set_location(ctx, args)
        except Exception as e:
            await ctx.send(f"Error: {e}")
    @_set_location_t.error
    async def set_location_t_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_weather_by_location.command(name="remove", pass_context=True)
    @commands.check(util.is_active)
    async def _remove_location_w(self, ctx, *args):
        """Remove location for weather and timezone command"""
        try:
            await self.remove_location(ctx, args)
        except Exception as e:
            await ctx.send(f"Error: {e}")
    @_remove_location_w.error
    async def remove_location_w_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_timezone_by_location.command(name="remove", pass_context=True)
    @commands.check(util.is_active)
    async def _remove_location_t(self, ctx, *args):
        """Remove location for weather and timezone command"""
        try:
            await self.remove_location(ctx, args)
        except Exception as e:
            await ctx.send(f"Error: {e}")
    @_remove_location_t.error
    async def remove_location_t_error(self, ctx, error):
        await util.error_handling(ctx, error)



    ################################################################################################################################



    @commands.command(name='img', aliases = ['image'])
    @commands.check(util.is_active)
    async def _imagesearch(self, ctx: commands.Context, *args):
        """Google image search

        (has a 100 day API limit per day)
        """

        # INITIALISE API DATA
        try:
            API_KEY = os.getenv("google_search_key")
            if API_KEY is None:
                emoji = util.emoji("disappointed")
                raise ValueError(f"No API key provided. {emoji}\n||(Ask mods to get an API key + Search Engine ID from developers.google.com)||")

            Search_Engine_ID = os.getenv("google_search_engine_id")
            if Search_Engine_ID is None:
                emoji = util.emoji("disappointed")
                raise ValueError(f"No Search Engine ID provided. {emoji}\n||(Ask mods to get an API key + Search Engine ID from developers.google.com)||")
        except Exception as e:
            await ctx.send(f"Error: {e}")
            return

        try: # cooldown to not trigger actual rate limits or IP blocks
            await util.cooldown(ctx, "googlesearch")
        except Exception as e:
            await util.cooldown_exception(ctx, e, "googlesearch")
            return

        try:
            version = util.get_version().replace("version","v").replace(" ","").strip()
        except:
            version = "v_X"
        USER_AGENT = f'MDM_Bot_{version}'
        headers = {'user-agent': USER_AGENT}

        # PARSE ARGUMENTS

        string = ' '.join(args)

        payload = {
            'key': API_KEY,
            'cx': Search_Engine_ID,
            'hl': 'lang_en',
            'q':  string,
            'safe': 'active',
            'searchType': 'image',
        }

        # GET IMAGE DATA
        url = 'https://customsearch.googleapis.com/customsearch/v1'
        response = requests.get(url, headers=headers, params=payload)
        rjson = response.json()

        bad_urls = [
            "https://cdn.", # does not embed somehow
            "https://lookaside.", # facebook and instagram pictures
            "https://www.tiktok.com", # tiktok
        ]

        try:
            for item in rjson['items']:
                if any([item['link'].startswith(x) for x in bad_urls]): #some links don't work well with discord
                    continue
                await ctx.send(item['link'])
                break
        except:
            #print(rjson)
            try:
                errorcode = rjson['error']['code']
                try:
                    errorreason = rjson['error']['details'][0]['reason']
                except:
                    errorreason = "?"

                if errorreason == 'RATE_LIMIT_EXCEEDED':
                    await ctx.send(f"Error ({errorcode}): Reached API limit.\n(Only 100 queries per day.)")
                else:
                    reason = errorreason.lower().replace("_", " ")
                    await ctx.send(f"Error ({errorcode}): Could not find image.\n(reason: {reason})")
            except Exception as e:
                print("Error while compiling error message lmao:", e)
                await ctx.send("Error: Could not find image.")

    @_imagesearch.error
    async def imagesearch_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='calc', aliases = ['calculate', "wolframalpha", "woa", "query", "tellme", "mirrormirroronthewall"])
    @commands.check(util.is_active)
    async def _calculate(self, ctx: commands.Context, *args):
        """Computation via WolframAlpha

        This command can be used to make simple calculations, but also to query other things that WolframAlpha can handle such as "How far is Tokio from Osaka".
        """
        # INITIALISE API DATA
        try:
            API_KEY = os.getenv("wolframalpha_id")
            if API_KEY is None:
                emoji = util.emoji("disappointed")
                raise ValueError(f"No API key provided. {emoji}\n||(Ask mods to get an API key from https://developer.wolframalpha.com/access)||")
        except Exception as e:
            await ctx.send(f"Error: {e}")
            return

        try: # cooldown to not trigger actual rate limits or IP blocks
            await util.cooldown(ctx, "wolframalpha")
        except Exception as e:
            await util.cooldown_exception(ctx, e, "wolframalpha")
            return

        try:
            version = util.get_version().replace("version","v").replace(" ","").strip()
        except:
            version = "v_X"
        USER_AGENT = f'MDM_Bot_{version}'
        headers = {'user-agent': USER_AGENT}

        # PARSE ARGUMENTS

        string = ' '.join(args)

        if string.strip() == "":
            await ctx.send("Command needs arguments.")
            return

        async with ctx.typing():
            payload = {
                'appid': API_KEY,
                'i': string,
            }

            # GET WOLFRAM ALPHA DATA
            try:
                url = 'http://api.wolframalpha.com/v1/result'
                response = requests.get(url, headers=headers, params=payload)
                text = util.cleantext2(response.text)
                await ctx.send(f"`Result:` {text}")
            except Exception as e:
                print(e)
                await ctx.send(f"`WolframAlpha Error:` {e}")
    @_calculate.error
    async def calculate_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='gpt', aliases = ['chatgpt'])
    @commands.check(GU_Check.is_gpt_enabled)
    @commands.check(util.is_active)
    async def _gpt_query(self, ctx: commands.Context, *args):
        """Query Chat GPT

        Note that this command makes an OpenAI query without any knowledge of previous conversation or information about the user that the bot otherwise has.
        """
        try:
            api_key = os.getenv("openai_secret_key")

            if api_key is None:
                await ctx.send("No API key provided.\n||Ask mods to add Open AI account and API key.||")
                return 
        except:
            await ctx.send("Failed to load OpenAI API key.")
            return 

        if len(args) == 0:
            await ctx.send("Command needs prompt.")
            return

        # THE QUERY
        query = ' '.join(args)

        async with ctx.typing():
            try:
                now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())

                conRA = sqlite3.connect('databases/robotactivity.db')
                curRA = conRA.cursor()

                # check channel restrictions

                #under construction

                # check bot-wide cooldown
                try: # cooldown to not trigger actual rate limits or IP blocks
                    await util.cooldown(ctx, "gpt")
                except Exception as e:
                    await util.cooldown_exception(ctx, e, "gpt")
                    return

                # check user-specific cooldown

                modexempt = False
                modexemption_list = [item[0] for item in curRA.execute("SELECT content FROM gpt_setting WHERE type = ?", ("user cooldown mod exempt",)).fetchall()]

                if len(modexemption_list) > 0:
                    modexemption = modexemption_list[0].lower().strip()
                    if modexemption in ["on"]:
                        modexempt = True
                    if len(modexemption) > 1:
                        print("Warning: multiple mod exemption entries for GPT command found in database")

                if modexempt:
                    for perms in ctx.message.author.guild_permissions:
                        if perms[0] == "manage_guild":
                            if perms[1]:
                                is_mod = True
                            else:
                                is_mod = False
                            break
                    else:
                        print("Error: Something is wrong with permission manage_guild.")
                        is_mod = False

                if not is_mod:
                    cooldown_setting = [item[0] for item in curRA.execute("SELECT content FROM gpt_setting WHERE type = ?", ("user cooldown",)).fetchall()]
                    try:
                        cooldown_int = int(cooldown_setting[0])
                    except Exception as e:
                        print("Format error with given GPT user cooldown setting:", e)
                        cooldown_int = 60

                    usercooldown = [item[0] for item in curRA.execute("SELECT last_time FROM gpt_usercooldown WHERE userid = ?", (str(ctx.author.id),)).fetchall()]

                    if len(usercooldown) == 0:
                        curRA.execute("INSERT INTO gpt_usercooldown VALUES (?, ?, ?, ?)", (str(ctx.author.id), str(ctx.author.name), now, ""))
                        conRA.commit()
                    else:
                        last_time = int(usercooldown[0])

                        if last_time + cooldown_int > now:
                            await ctx.send(f"Command on cooldown, please wait. <t:{(now + (now - (last_time + cooldown_int)))}:R>")
                            return
                        else:
                            curRA.execute("UPDATE gpt_usercooldown SET last_time = ? WHERE userid = ?", (now, str(ctx.author.id)))
                            conRA.commit()

            except Exception as e:
                await ctx.send(f"Error: {e}")
                return

            try:
                # connect
                client = OpenAI(api_key=api_key)
                context = []

                # get initial role
                conRA = sqlite3.connect('databases/robotactivity.db')
                curRA = conRA.cursor()
                gpt_settings_systemrole = [item[0] for item in curRA.execute("SELECT content FROM gpt_setting WHERE type = ?", ("systemrole",)).fetchall()]

                if len(gpt_settings_systemrole) == 0:
                    systemrole = "You are a helpful assistant."
                else:
                    systemrole = gpt_settings_systemrole[0]
                context.append({"role": "system", "content": systemrole})

                try:
                    # get chat context
                    gpt_settings_context = [item[0] for item in curRA.execute("SELECT content FROM gpt_setting WHERE type = ?", ("context",)).fetchall()]
                    if len(gpt_settings_context) > 0 and gpt_settings_context[0].lower().strip() == "enabled":
                        # remove old context
                        now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())
                        curRA.execute("DELETE FROM gpt_context WHERE utc_timestamp < ?", (now - 24*60*60,))
                        conRA.commit()

                        # fetch messages
                        gpt_context_messages = [[item[0],item[1][:1000],item[2]] for item in curRA.execute("SELECT role, content, message_id FROM gpt_context WHERE user_id = ? AND channel_id = ? ORDER BY utc_timestamp ASC", (str(ctx.author.id),str(ctx.channel.id))).fetchall()]

                        # filter out messages
                        gpt_context_messages_copy = []
                        char_count = len(query) + len(systemrole)
                        remove_rest = False
                        for item in reversed(gpt_context_messages):
                            # throw out too long stuff
                            if char_count + len(item[1]) > 2000:
                                remove_rest = True

                            if not remove_rest:
                                char_count += len(item[1])
                                gpt_context_messages_copy.append(item)

                        gpt_context_messages_copy = list(reversed(gpt_context_messages_copy))

                        i = 0
                        for item in gpt_context_messages_copy:
                            i += 1
                            if len(gpt_context_messages_copy) - i > 10:
                                continue

                            role = item[0]
                            msg_text = util.cleantext2(item[1])
                            context.append({"role": role, "content": msg_text})

                        if ctx.message.reference is not None and ctx.message.reference.message_id not in [x[2] for x in gpt_context_messages_copy]:
                            msg = await ctx.fetch_message(ctx.message.reference.message_id)

                            if str(msg.author.id) == str(self.bot.application_id):
                                role = "assistant"
                            else:
                                role = "user"
                            text = util.cleantext2(str(msg.content))
                            context.append({"role": role, "content": text})

                except Exception as e:
                    print("Error while trying to assemble context:", e)

                # append query
                context.append({"role": "user", "content": query})

                completion = client.chat.completions.create(
                  model="gpt-3.5-turbo",
                  messages=context
                )

                await ctx.reply(str(completion.choices[0].message.content), mention_author=False)

                if len(gpt_settings_context) > 0 and gpt_settings_context[0].lower().strip() == "enabled":
                    curRA.execute("INSERT INTO gpt_context VALUES (?, ?, ?, ?, ?, ?, ?)", ("user", str(ctx.author.id), str(ctx.author.name), str(ctx.channel.id), str(ctx.message.id), query, now-1))
                    curRA.execute("INSERT INTO gpt_context VALUES (?, ?, ?, ?, ?, ?, ?)", ("assistant", str(ctx.author.id), str(ctx.author.name), str(ctx.channel.id), str(ctx.message.id), str(completion.choices[0].message.content), now-1))
                    conRA.commit()

            except Exception as e:
                try:
                    error_code = str(e).split(" - {")[0].strip()
                    message = str(e).split("'message': '")[1].split("'")[0].strip()
                    error_type = str(e).split("'type': '")[1].split("'")[0].replace("_", " ").strip()
                    print("ERROR:", message)
                    additional = ""
                    if error_type == "insufficient quota":
                        additional = "API limit reached."

                    await ctx.send(f"Open AI Error: ```{error_code} - {error_type}```{additional}")
                except:
                    await ctx.send(f"Open AI Error: {e}")
            
    @_gpt_query.error
    async def gpt_query_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='gptset', aliases = ['setgpt'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(GU_Check.is_gpt_enabled)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _setgpt(self, ctx: commands.Context, *args):
        """🔒 GPT settings of bot

        Use arg `context` with `on` or `off` to enable/disable context messages.
        Use arg `systemrole` to set "personality" of the AI respodent.

        Use without argument to see settings.
        """
        conRA = sqlite3.connect('databases/robotactivity.db')
        curRA = conRA.cursor()
        
        if len(args) == 0:
            gpt_settings_systemrole = [item[0] for item in curRA.execute("SELECT content FROM gpt_setting WHERE type = ?", ("systemrole",)).fetchall()]
            if len(gpt_settings_systemrole) == 0:
                systemrole = "You are a helpful assistant."
            else:
                systemrole = util.cleantext2(gpt_settings_systemrole[0])

            gpt_settings_context = [item[0] for item in curRA.execute("SELECT content FROM gpt_setting WHERE type = ?", ("context",)).fetchall()]
            if len(gpt_settings_context) > 0 and gpt_settings_context[0].lower().strip() in ["enabled", "on", "enable"]:
                context = "on"
            else:
                context = "off"

            info = f"GPT system role is set to```{systemrole}```Context is set `{context}`."
            await ctx.send(info)

        elif args[0].lower().strip() == "systemrole":
            if len(args) <= 1:
                new_systemrole = "You are a helpful assistant."
            else:
                new_systemrole = ' '.join(args[1:])
            curRA.execute("UPDATE gpt_setting SET content = ? WHERE type = ?", (new_systemrole, "systemrole"))
            conRA.commit()

            await ctx.send(f"GPT system role set to ```{new_systemrole[:1900]}```")

        elif args[0].lower().strip() == "context":
            try:
                switch = args[1].lower().strip()

                if switch in ["on", "enabled", "enable"]:
                    turn = "enabled"
                else:
                    turn = "disabled"

                curRA.execute("UPDATE gpt_setting SET content = ? WHERE type = ?", (turn, "context"))
                conRA.commit()

                await ctx.send(f"GPT: {turn} context")
            except:
                await ctx.send("Error with provided arguments.")

        else:
            await ctx.send("Error: Command needs either argument `context` or `systemrole` or no argument.")

    @_setgpt.error
    async def setgpt_error(self, ctx, error):
        await util.error_handling(ctx, error)



           
    @commands.command(name='wiki', aliases = ['wikipedia'])
    @commands.check(util.is_active)
    async def _wikipedia(self, ctx: commands.Context, *args):
        """Queries wikipedia for information
        """
        
        def url_lang_detect(title):
            try:
                lang = detect(str(title))
                if lang == 'ja':
                    return 'https://ja.wikipedia.org/w/api.php'
                elif lang == 'de':
                    return 'https://de.wikipedia.org/w/api.php'
                elif lang == 'en':
                    return 'https://en.wikipedia.org/w/api.php'
                else:
                    return 'https://en.wikipedia.org/w/api.php'
            except:
                return 'Error detecting language.'
        
        def get_images_from_wikipedia(title):
            # if (title is jap): url is jap/ elif (): url is eng 
            url = url_lang_detect(str(title))
            params = {
                "action": "query",
                "titles": title,
                "prop": "images",
                "format": "json"
            }
            response = requests.get(url, params=params)
            data = response.json()
            print(data)
            pages = data.get("query", {}).get("pages", {})
            images = []
            for page_id, page in pages.items():
                images.append(page.get("images", []))
            return images
        
        def get_image_info(title):
            url = url_lang_detect(str(title))
            params = {
                "action": "query",
                "titles": title,
                "prop": "imageinfo",
                "iiprop": "url",
                "format": "json"
            }
            response = requests.get(url, params=params)
            data = response.json()
            pages = data.get("query", {}).get("pages", {})
            for page_id, page in pages.items():
                image_info = page.get("imageinfo", [{}])[0]
                return image_info.get("url", [])

        def fetch_wikipedia_page(load):
            url = url_lang_detect(load["i"])
            params = {
                "action": "query",
                "titles": load["i"],
                "prop": "imageinfo",
                "iiprop": "url",
                "format": "json"
                #'apikey': API_KEY,  # Include the API key in the request
            }
            response = requests.get(url, params = params)
            response.raise_for_status()  # Raise an exception for HTTP errors
            return response.json()

        def get_wikipedia_info(load, sentences=5):
            url = url_lang_detect(load["i"])
            params = {
                "action": "query",
                "format": "json",
                "titles": load["i"],
                "prop": "extracts",
                "exintro": True,
                "explaintext": True,
                "exsentences": sentences
            }

            response = requests.get(url, params=params)
            data = response.json()
            
            page = next(iter(data['query']['pages'].values()))
            title = page.get('title', 'No title found')
            summary = page.get('extract', 'No summary found')
            
            return title, summary

        ### START OF FUNCTION

        try:
            API_KEY = os.getenv("wikipedia_token")
            if API_KEY is None:
                emoji = util.emoji("disappointed")
                raise ValueError(f"No API key provided. {emoji}\n||(Ask mods to get an API key from https://api.wikimedia.org/wiki/Getting_started_with_Wikimedia_APIs)||")
        except Exception as e:
            await ctx.send(f"Error: {e}")
            return

        try: # cooldown to not trigger actual rate limits or IP blocks
            await util.cooldown(ctx, "wikipedia")
        except Exception as e:
            await util.cooldown_exception(ctx, e, "wikipedia")
            return

        try:
            version = util.get_version().replace("version","v").replace(" ","").strip()
        except:
            version = "v_X"
        USER_AGENT = f'MDM_Bot_{version}'
        headers = {'user-agent': USER_AGENT}

        # PARSE ARGUMENTS

        string = ' '.join(args)
        if string.strip() == "":
            await ctx.send("Command needs arguments.")
            return

        async with ctx.typing():

            payload = {
                        'appid': API_KEY,
                        'i': string,
                        }

            try:
                # Fetch and print a Wikipedia page summary
                page_data = fetch_wikipedia_page(payload)
                pages = page_data.get('query', {}).get('pages', {})
                string_list = []
                title, summary = get_wikipedia_info(payload)
                for page_id, page_info in pages.items():
                    extract = page_info.get('extract', 'No extract found.')
                    string_list.append(extract)

                embed = discord.Embed(
                                title=f"{title}",
                                description=f"{summary}",
                                color=discord.Color.blue()
                            )

                images = get_images_from_wikipedia(string)

                # Save the first image if it exists
                try:
                    if len(images) > 0:
                        image_title = None
                        for i in range(len(images)):
                            if image_title not in [None, ""] and str(image_title).endswith(('.jpg','.jpeg','.png','.gif','.webm','.webp')):
                                break
                            for j in range(len(images[i])):
                                try:
                                    image_title = images[i][j].get("title")  # Get the first image's title
                                    if image_title not in [None, ""] and str(image_title).endswith(('.jpg','.jpeg','.png','.gif','.webm','.webp')):
                                        break
                                except Exception as e:
                                    print("intermediate image fetch error:", e)
                                    continue
                        if image_title:
                            image_url = get_image_info(image_title)
                            if len(image_url) > 0:
                                embed.set_thumbnail(url = image_url) 
                except Exception as e:
                    print("wikipedia - could not add thumbnail:", e)
                await ctx.send(embed=embed)

            except Exception as e:
                print(e)
                if str(e) == "list index out of range":
                    await ctx.send("Wikipedia Error: Page not found")
                else:
                    await ctx.send(f"Wikipedia Error: {e}")

    @_wikipedia.error
    async def wikipedia_error(self, ctx, error):
        await util.error_handling(ctx, error)




async def setup(bot: commands.bot) -> None:
    await bot.add_cog(
        General_Utility(bot),
        guilds = [discord.Object(id = int(os.getenv("guild_id")))])