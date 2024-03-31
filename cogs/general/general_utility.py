import discord
from discord.ext import commands
import datetime
import pytz
from other.utils.utils import Utils as util
import os
import random
from googletrans import Translator
import re
import sqlite3
import math


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



    @commands.command(name='say', aliases = ['msg'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _say(self, ctx: commands.Context, *args):
        """🔒 Messages given text

        Write `-say <channel name> <message>` to send an embedded message to this channel.
        Use `-say <channel name> [<header>] <message>` to give it a title as well.
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

        Write -react <channel> <message id> <reactions> to add reactions to a message.
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
        With `-qp <question> options: <list of things seperated by commas>` you can create an embed with up to 20 options.

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
        """random number

        argument must be either one integer n > 1 (gives out random integer between 1 and n)
        or
        argument must be a set of options to choose from separated by semicolons
        or
        argument must be bl (optionally with category name behind (no spaces))

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

            dice = args[0].lower()
            if "d" in dice:
                number_and_sides = dice.split("d",1)
                try:
                    if number_and_sides[0] == "":
                        num_of_dice = 1
                    else:
                        num_of_dice = int(number_and_sides[0])
                    dice_size = int(number_and_sides[1])
                except:
                    await ctx.send(f'Error: If you want to use a multiple dice command with `n`-many `x`-sided dice, then use {self.prefix}roll `n`d`x`.\nFor example -roll 6d20')
                    return

                if num_of_dice < 1:
                    await ctx.send(f'Error: Number of dice must be at least 1.')
                    return
                if dice_size < 2:
                    await ctx.send(f'Error: Dice/coins must be at least 2-sided.')
                    return
                if dice_size > 999:
                    emoji = util.emoji("umm")
                    await ctx.send(f'Error: Lmao how large do you want your dice to be. {emoji}\nI can offer a D999 at most...')
                    return
                if num_of_dice > 100:
                    emoji = util.emoji("cry2")
                    await ctx.send(f"Error: I'm sorry, but I only have 100 of these dice {emoji}")
                    return

                n = num_of_dice
                dice_rolls = []
                while n >= 1:
                    r = random.randint(1, dice_size)
                    dice_rolls.append(r)
                    n = n - 1
                total = sum(dice_rolls)

                await ctx.send(f"🎲 {num_of_dice}x D{dice_size} roll: {total} ({str(dice_rolls)[1:len(str(dice_rolls))-1]})")
                return

            await ctx.send(f'Error: Argument should be either an integer > 1, a list of options separated by semicolons, `bl` or `blc categoryname`.')
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

        await ctx.send(f'Error: Argument must be either an integer > 1, a list of options separated by semicolons, `bl`, `blc <categoryname>`, `blx <categoryname>` or `xDy` (where x and y are integers > 1).')              

    @_dice.error
    async def dice_error(self, ctx, error):
        await util.error_handling(ctx, error)



    ############################# TRANSLATE #################################################################################################################



    @commands.command(name='translate', aliases = ['tr','trans', 'googletranslate', 'googletrans', 'translation'])
    @commands.check(util.is_active)
    async def _translate(self, ctx, *args):
        """translate

        Translates a word or sentence, first argument must be the destination language code.
        Use `-tr languages` to see which languages are supported.
        """
        async with ctx.typing():
            languagedict = {
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
                        "🇿🇦": 'af',
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
                        "ch": 'zh-cn',
                        "zh": 'zh-cn',
                        "jp": 'ja'
                        }
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
                await ctx.send(f'Language {givenLanguage} is not supported.')
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
                await ctx.send(f'`[Lang.: {detection.lang}, Conf.={detection.confidence}]`\n`Translation result:` {msgTranslated}\n'[:2000])
            except Exception as e:
                await ctx.send(f'`An error ocurred:` {e}')
    @_translate.error
    async def translate_error(self, ctx, error):
        await util.error_handling(ctx, error)


    # under construction: add -languages command



    ############################# UNIT CONVERSION #################################################################################################################



    @commands.command(name='convert', aliases = ['con','conv'])
    @commands.check(util.is_active)
    async def _convert(self, ctx, *args):
        """Converts units
        
        For example:
        `-con <number>F`: Fahrenheit to Celsius
        `-con <number>C`: Celsius to Fahrenheit

        currently supported are temperature `(C,F)`, length/distances `(km,m,cm,mi,yd,ft,in also 5'11 notation)`, speed `(kmh,mph)`, weight/mass `(lbs,oz,kg,g)`, volume `(gal,ukgal,fl oz,cup,l,cl,ml)`, area `(acre,sqm)`, time `(years,months,weeks,days,hours,minutes,seconds)`
        and 
        also currencies, for which you can use "to"
        `-con <number> USD to EUR CHF`
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
                await ctx.send(f'Grams to Ounces\n```{"{:,}".format(value_to_convert)}oz is about {"{:,}".format(converted_value)}g.```')
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
        i.e. `-remind in 5 hours blablabla`
        or a given time in the future in UNIX timestamp format
        i.e. `-remind at 2023668360 blablabla`
        the rest is considered part of the reminder content.

        has subcommand
        ```
        🔒recurring
        ```
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

        # TRY TO FIRST PARSE INDICATORS WHETHER TIME PERIOD OR UNIX TIME STAMP IS PROVIDED

        arguments = []
        for arg in args:
            arguments.append(util.cleantext(arg))

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
                await ctx.send("What should the reminder be about?")
                return

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
            if rest.strip() in ["", "to", "about"]:
                await ctx.send("What should the reminder be about?")
                return

            utc_timestamp = now + int(timeseconds)
            remindertext = rest

            cur.execute("INSERT INTO reminders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (reminder_id, str(ctx.author.name), userid, str(utc_timestamp), remindertext, str(ctx.channel.id), str(ctx.channel.name), str(ctx.message.id), str(now)))
            con.commit()
            await util.changetimeupdate()
            seconds_until = utc_timestamp - now
            readable_time = util.seconds_to_readabletime(seconds_until, False, now)
            await ctx.reply(f"Alrighty. Will remind you in {readable_time} or so.\n(ID: {reminder_id})", mention_author=False)
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
        
        i.e. `-remind recurring <unix timestamp> ;; <interval time> ;; <channel id> ;; <title> ;; <text> ;; <title link> ;; <thumbnail url> ;; <ping list>`
        
        You do not have to provide all arguments, but you need to still separate empty arguments with a double-semicolon
        e.g. `-remind recurring 2023668360 ;; weekly ;; ;; ;; hey this is a weekly reminder ;; ;; ;; ;;`.
        You can leave out double-semicolons at the end, where only empty arguments follow
        e.g. `-remind recurring 2023668360 ;; every 30 days `.
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
        


    @commands.command(name="selfmute", aliases = ["selftimeout"])
    @commands.check(util.is_active)
    @commands.check(util.is_main_server)
    async def _selfmute(self, ctx, *args):
        """Mutes you for given amount of time

        i.e. `-selfmute 2 hours`
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



    @commands.group(name="calendar", aliases = ["c", "kalender", "showcalendar"], pass_context=True, invoke_without_command=True)
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
        `-calendar show 31/01` (next January 31st)
        or
        `calendar show 12` (show December)
        or
        `calendar show week 28` (show 28th calender week)
        or
        `calendar show next` (show next few calendar entries)
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



    @commands.command(name="quote", aliases = ["q"])
    @commands.check(util.is_active)
    async def _quote(self, ctx, *args):
        """Show quote
        """
        await ctx.send("⚠️ under construction")
    @_quote.error
    async def quote_error(self, ctx, error):
        await util.error_handling(ctx, error)


    ############################# GEODATA #######################################################################################



    @commands.command(name="time", aliases = ["t"])
    @commands.check(util.is_active)
    async def _timezone_by_location(self, ctx, *args):
        """Show time of given location
        """
        await ctx.send("⚠️ under construction")
    @_timezone_by_location.error
    async def timezone_by_location_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name="weather", aliases = ["w"])
    @commands.check(util.is_active)
    async def _weather_by_location(self, ctx, *args):
        """Show weather of given location
        """
        await ctx.send("⚠️ under construction")
    @_weather_by_location.error
    async def weather_by_location_error(self, ctx, error):
        await util.error_handling(ctx, error)





async def setup(bot: commands.bot) -> None:
    await bot.add_cog(
        General_Utility(bot),
        guilds = [discord.Object(id = int(os.getenv("guild_id")))])