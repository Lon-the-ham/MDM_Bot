import discord
from discord.ext import commands
import datetime
import pytz
from other.utils.utils import Utils as util
import os
import random
import sqlite3


class Shenanigans(commands.Cog):
    def __init__(self, bot: commands.bot) -> None:
        self.bot = bot
        self.prefix = os.getenv("prefix")

    def is_inactive(self):
        try:
            activity = util.is_active()
            return not activity
        except:
            return True

    def custom_responses_enabled(self):
        try:
            conB = sqlite3.connect(f'databases/botsettings.db')
            curB = conB.cursor()

            custom_triggerresponse_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("custom responses",)).fetchall()]
            
            if len(custom_triggerresponse_list) == 0 or custom_triggerresponse_list[-1].lower().strip() != 'on':
                return False
            else:
                return True
        except:
            return False



    @commands.command(name='sudo', aliases = ['please', 'pls'])
    @commands.check(util.is_active)
    async def _sudo(self, ctx: commands.Context, *args):
        """sudo do something"""

        conSH = sqlite3.connect('databases/shenanigans.db')
        curSH = conSH.cursor()

        comstring = ' '.join(args).lower()
        possible_outcomes = [[item[0],item[1]] for item in curSH.execute("SELECT response1, response2 FROM sudo WHERE command = ?", (comstring,)).fetchall()]
            
        if len(possible_outcomes) == 0:
            await ctx.send("Sorry. Not in the mood.")
            return

        r = random.randint(0,len(possible_outcomes)-1)

        message1 = await util.customtextparse(possible_outcomes[r][0], str(ctx.author.id))
        message2 = await util.customtextparse(possible_outcomes[r][1], str(ctx.author.id))
        message_sent = False

        if message1.strip() != "":
            await ctx.send(message1)
            message_sent = True

        if message2.strip() != "":
            await ctx.send(message2)
            message_sent = True

        if not message_sent:
            await ctx.send("Mhm yeah, not today.")
            return

    @_sudo.error
    async def sudo_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='inspire', aliases = ['inspiration'])
    @commands.check(util.is_active)
    async def _inspire(self, ctx: commands.Context, *args):
        """quote that may or may not be inspiring"""

        conSH = sqlite3.connect('databases/shenanigans.db')
        curSH = conSH.cursor()

        possible_outcomes = [[item[0],item[1],item[2]] for item in curSH.execute("SELECT quote, author, link FROM inspire").fetchall()]

        if len(possible_outcomes) == 0:
            await ctx.send("Sorry. I am not inspired.")
            return

        r = random.randint(0,len(possible_outcomes)-1)
        
        quote = possible_outcomes[r][0]
        author = possible_outcomes[r][1]
        link = possible_outcomes[r][2]

        if str(link).startswith("https:") or str(link).startswith("www."):
            is_url = True
        else:
            is_url = False

        if quote.strip() == "":
            await ctx.send("Mhm yeah, not today.")
            return

        text = await util.customtextparse(quote, str(ctx.author.id))
        text = "*" + util.cleantext2(text) + "*\n"

        if author.strip() != "":
            text += "-"

            if is_url:
                text += "["

            text += author.strip()

            if is_url:
                text += f"]({link.strip()})"


        if link.strip() != "" and not is_url:
            text += f" ({link})"

        embed=discord.Embed(title="", description=text.strip(), color=0x63c5da)
        await ctx.send(embed=embed)

    @_inspire.error
    async def inspire_error(self, ctx, error):
        await util.error_handling(ctx, error)




    @commands.command(name='mrec', aliases = ['memerec', 'memerecommendation'])
    @commands.check(util.is_active)
    async def _mrec(self, ctx, *args):
        """possibly great recommendation"""

        conSH = sqlite3.connect('databases/shenanigans.db')
        curSH = conSH.cursor()

        comstring = ''.join(args).lower()

        if comstring.strip() != "":
            possible_outcomes = [item[0] for item in curSH.execute("SELECT link FROM mrec WHERE subcommand = ? or alias = ?", (comstring, comstring)).fetchall()]
        else:
            possible_subcommands = [item[0] for item in curSH.execute("SELECT subcommand FROM mrec").fetchall()]
            possible_subcommands = list(dict.fromkeys(possible_subcommands))
            r = random.randint(0,len(possible_subcommands)-1)
            subcommand = possible_subcommands[r]
            possible_outcomes = [item[0] for item in curSH.execute("SELECT link FROM mrec WHERE subcommand = ?", (subcommand,)).fetchall()]

        if len(possible_outcomes) == 0:
            await ctx.send("Sorry. Nothing to recommend.")
            return

        r = random.randint(0,len(possible_outcomes)-1)
        url = possible_outcomes[r]
        emoji = util.emoji("giggle")
        await ctx.send(f'I think you will enjoy this! {emoji}\n{url}')  

    @_mrec.error
    async def mrec_error(self, ctx, error):
        await util.error_handling(ctx, error)



    ###########################################################################################################################################################
    ###########################################################################################################################################################
    ###########################################################################################################################################################

    # commands to fill the database



    @commands.command(name='shenaniganadd', aliases = ['addshenanigans', 'addshenanigan', 'shenanigansadd'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _add_a_shenanigan(self, ctx: commands.Context, *args):
        """🔒 Adds DB entry
        
        First argument needs to specify, which database table something should be added to. The following arguments are the content, separated by double-semicolons.
        
        > `inspire` [3 args](1 mandatory arg: quote; 2 optional args: author, link)
        > `mrec` [3 args](1 mandatory arg: link; 2 optional args: filtername, filteralias)
        > `sudo` [3 args](2 mandatory args: commandname, response 1; 1 optional arg: response 2)

        E.g.
        `<prefix>addshenanigan sudo make me a sandwich;; ok here;; 🥪`

        You can also specify some custom command/reactions:
        > `customtext` [3 args](2 mandatory args: trigger text response text; 1 optional arg: trigger type)
        > `customreact` [3 args](2 mandatory args: trigger text, response reaction(s); 1 optional arg: trigger type)

        The trigger text triggers even without the command prefix (<prefix>), unless you also include the prefix. 
        Response text or response reactions are what the bot will respond with.

        The trigger type needs to be the last argument and is per default 
        `standard`: matches when a users message is equal to the specified text, but case insensitive
        but you can also specify
        `strict`: matches only when the text is EXACTLY the same, including casing
        `include`: matches when the text includes the trigger text, case insensitive

        Note that line breaks in responses are given by `\\n` and prefixes in trigger text can be written as `< prefix >` (without spaces).
        """
        if len(args) < 2:
            await ctx.send("Command needs more arguments.")
            return

        # PARSE ARGUMENTS

        table_raw = args[0].split(";;")[0]
        rest = ' '.join(args).removeprefix(table_raw)

        table = table_raw.strip().lower()
        arguments = []
        for arg in rest.split(";;"):
            if arg.strip() != "":
                arguments.append(util.cleantext(arg.strip()))

        # TABLE SWITCH CASE

        if table in ['inspire', 'inspi', 'inspiring', 'quote']:

            # INTERPRET ARGUMENTS

            if len(arguments) >= 3:
                link = arguments[2]
            else:
                link = ""

            if len(arguments) >= 2:
                author = arguments[1]
                if author.startswith("http"):
                    link = author
                    author = ""
            else:
                author = ""

            if len(arguments) >= 1:
                quote = arguments[0]
            else:
                await ctx.send("Pls provide valid quote arguments.")
                return

            # INSERT INTO DATABASE

            conSH = sqlite3.connect('databases/shenanigans.db')
            curSH = conSH.cursor()
            id_strings = [item[0] for item in curSH.execute("SELECT quote_id FROM inspire").fetchall()]
            max_id = 0
            for ids in id_strings:
                try:
                    id_int = int(ids)
                except:
                    continue

                if max_id < id_int:
                    max_id = id_int
            quote_id = str(max_id + 1)

            curSH.execute("INSERT INTO inspire VALUES (?, ?, ?, ?)", (quote_id, quote, author, link))
            conSH.commit()
            await util.changetimeupdate()
            await ctx.send("Successfully added quote.\n\nPREVIEW:")

            # GIVE PREVIEW

            if str(link).startswith("https:") or str(link).startswith("www."):
                is_url = True
            else:
                is_url = False
            text = await util.customtextparse(quote, str(ctx.author.id))
            text = "*" + util.cleantext2(text) + "*\n"
            if author.strip() != "":
                text += "-"

                if is_url:
                    text += "["

                text += author.strip()

                if is_url:
                    text += f"]({link.strip()})"

            if link.strip() != "" and not is_url:
                text += f" ({link})"

            embed=discord.Embed(title="", description=text.strip(), color=0x63c5da)
            embed.set_footer(text=f"ID: {quote_id}")
            await ctx.send(embed=embed)


        elif table in ['rec', 'mrec', 'recommendation', 'recommendations', 'memerecommendation', 'memerecommendations']:
            # INTERPRET ARGUMENTS

            if len(arguments) >= 3:
                filteralias = arguments[2]
            else:
                filteralias = ""

            if len(arguments) >= 2:
                filtername = arguments[1]
            else:
                filtername = ""

            if len(arguments) >= 1:
                link = arguments[0]
            else:
                await ctx.send("Pls provide valid mrec arguments.")
                return

            # INSERT INTO DATABASE

            conSH = sqlite3.connect('databases/shenanigans.db')
            curSH = conSH.cursor()
            id_strings = [item[0] for item in curSH.execute("SELECT mrec_id FROM mrec").fetchall()]
            max_id = 0
            for ids in id_strings:
                try:
                    id_int = int(ids)
                except:
                    continue

                if max_id < id_int:
                    max_id = id_int
            mrec_id = str(max_id + 1)

            curSH.execute("INSERT INTO mrec VALUES (?, ?, ?, ?)", (mrec_id, filtername, filteralias, link))
            conSH.commit()
            await util.changetimeupdate()
            await ctx.send("Successfully added mrec.\n\nPREVIEW:")

            # GIVE PREVIEW

            emoji = util.emoji("giggle")
            await ctx.send(f'I think you will enjoy this! {emoji}\n{link}\n(ID: {mrec_id})')  


        elif table in ['sudo', 'superuserdo', 'suedough']:
            # INTERPRET ARGUMENTS

            if len(arguments) >= 3:
                response2 = arguments[2]
            else:
                response2 = ""

            if len(arguments) >= 2:
                response1 = arguments[1]
                commandname = arguments[0]
            else:
                await ctx.send("Pls provide valid sudo arguments.")
                return

            # INSERT INTO DATABASE

            conSH = sqlite3.connect('databases/shenanigans.db')
            curSH = conSH.cursor()
            id_strings = [item[0] for item in curSH.execute("SELECT sudo_id FROM sudo").fetchall()]
            max_id = 0
            for ids in id_strings:
                try:
                    id_int = int(ids)
                except:
                    continue

                if max_id < id_int:
                    max_id = id_int
            sudo_id = str(max_id + 1)

            curSH.execute("INSERT INTO sudo VALUES (?, ?, ?, ?)", (sudo_id, commandname, response1, response2))
            conSH.commit()
            await util.changetimeupdate()
            await ctx.send("Successfully added sudo command/response.")

            # GIVE PREVIEW
            text = f"Command: {self.prefix}sudo {commandname}\n"
            if response2 == "":
                text += f"Response: {response1}"
            else:
                text += f"Response 1: {response1}"
                text += f"Response 2: {response2}"
            embed=discord.Embed(title="", description=text.strip(), color=0x000000)
            embed.set_footer(text=f"ID: {sudo_id}")
            await ctx.send(embed=embed)


        elif table in ['custom', 'customresponse', 'customtext', 'customreply', 'customreact', 'customreacts', 'customreaction', 'customreactions']:
            # INTERPRET ARGUMENTS

            if len(arguments) >= 3:
                triggertype = arguments[2].lower().strip()
            else:
                triggertype = "standard"

            if len(arguments) >= 2:
                response = arguments[1]
                trigger = arguments[0]
            else:
                await ctx.send("Pls provide valid custom trigger and response.")
                return

            if triggertype not in ['standard', 'strict', 'include']:
                if triggertype in ['exact', 'precise', 'precisely']:
                    triggertype = 'strict'
                elif triggertype in ['includes', 'including']:
                    triggertype = 'include'
                else:
                    await ctx.send(f"Given trigger type `{triggertype}` not recognised... changing it to `standard`.")
                    triggertype = 'standard'


            # INSERT INTO DATABASE

            conSH = sqlite3.connect('databases/shenanigans.db')
            curSH = conSH.cursor()
            id_strings = [item[0] for item in curSH.execute("SELECT custom_id FROM custom").fetchall()]
            max_id = 0
            for ids in id_strings:
                try:
                    id_int = int(ids)
                except:
                    continue

                if max_id < id_int:
                    max_id = id_int
            custom_id = str(max_id + 1)

            if table in ['custom', 'customresponse', 'customtext', 'customreply']:
                responsetype = 'text'
            else:
                responsetype = 'reaction'

            curSH.execute("INSERT INTO custom VALUES (?, ?, ?, ?, ?)", (custom_id, trigger, triggertype, response, responsetype))
            conSH.commit()
            await util.changetimeupdate()
            await ctx.send("Successfully added custom command/response.")

            # GIVE PREVIEW
            trigger_edit = trigger.replace("<prefix>", self.prefix).strip()
            response_edit = response.replace("\\n", "\n").strip()

            text = f"Trigger text ({triggertype}): {trigger_edit}\n"
            text += f"Response ({responsetype}): {response_edit}"
            embed=discord.Embed(title="", description=text.strip(), color=0x000000)
            embed.set_footer(text=f"ID: {custom_id}")
            await ctx.send(embed=embed)


        else:
            await ctx.send("Pls provide valid table name.")

    @_add_a_shenanigan.error
    async def add_a_shenanigan_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='shenaniganremove', aliases = ['removeshenanigans', 'shenanigansremove', 'removeshenanigan', 'deleteshenanigan', 'deleteshenanigans', 'shenanigandelete', 'shenanigansdelete'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _remove_a_shenanigan(self, ctx: commands.Context, *args):
        """🔒 Removes DB entry
        
        First argument needs to specify, which database table something should be removed from.
        > `inspire` 
        > `mrec` 
        > `sudo` 
        > `custom`
        Second argument needs to be the id.

        E.g.
        `<prefix>removeshenanigan sudo 12`
        """
        if len(args) < 2:
            await ctx.send("Command needs more arguments.")
            return

        table = args[0].lower()
        entry_id = util.cleantext(args[1])

        conSH = sqlite3.connect('databases/shenanigans.db')
        curSH = conSH.cursor()

        if table in ['inspire', 'inspi', 'inspiring', 'quote']:
            matches = [[util.cleantext(item[0]),util.cleantext(item[1]),util.cleantext(item[2])] for item in curSH.execute("SELECT quote, author, link FROM inspire WHERE quote_id = ?", (entry_id,)).fetchall()]
            if len(matches) == 0:
                await ctx.send(f"No such inspiring quote with ID {entry_id}.")
                return

            curSH.execute("DELETE FROM inspire WHERE quote_id = ?", (entry_id,))
            conSH.commit()
            await util.changetimeupdate()
            await ctx.send(f"Removed entry:\n```Quote: {matches[0][0]}\nAuthor: {matches[0][1]}\nLink: {matches[0][2]}```")


        elif table in ['rec', 'mrec', 'recommendation', 'recommendations', 'memerecommendation', 'memerecommendations']:
            matches = [[util.cleantext(item[0]),util.cleantext(item[1]),util.cleantext(item[2])] for item in curSH.execute("SELECT subcommand, alias, link FROM mrec WHERE mrec_id = ?", (entry_id,)).fetchall()]
            if len(matches) == 0:
                await ctx.send(f"No such mrec with ID {entry_id}.")
                return

            curSH.execute("DELETE FROM mrec WHERE mrec_id = ?", (entry_id,))
            conSH.commit()
            await util.changetimeupdate()
            await ctx.send(f"Removed entry:\n```Filter/Subcommand: {matches[0][0]}\nFilteralias: {matches[0][1]}\nLink: {matches[0][2]}```")


        elif table in ['sudo', 'superuserdo', 'suedough']:
            matches = [[util.cleantext(item[0]),util.cleantext(item[1]),util.cleantext(item[2])] for item in curSH.execute("SELECT command, response1, response2 FROM sudo WHERE sudo_id = ?", (entry_id,)).fetchall()]
            if len(matches) == 0:
                await ctx.send(f"No such sudo command/response with ID {entry_id}.")
                return

            curSH.execute("DELETE FROM sudo WHERE sudo_id = ?", (entry_id,))
            conSH.commit()
            await util.changetimeupdate()
            await ctx.send(f"Removed entry:\n```Command: {matches[0][0]}\nResponse 1: {matches[0][1]}\nResponse 2: {matches[0][2]}```")


        elif table in ['custom', 'customresponse', 'customtext', 'customreply', 'customreact', 'customreacts', 'customreaction', 'customreactions']:
            matches = [[util.cleantext(item[0]),util.cleantext(item[1]),util.cleantext(item[2]),util.cleantext(item[3])] for item in curSH.execute("SELECT trigger_text, trigger_type, response, response_type FROM custom WHERE custom_id = ?", (entry_id,)).fetchall()]
            if len(matches) == 0:
                await ctx.send(f"No such custom trigger/response with ID {entry_id}.")
                return

            curSH.execute("DELETE FROM custom WHERE custom_id = ?", (entry_id,))
            conSH.commit()
            await util.changetimeupdate()
            await ctx.send(f"Removed entry:\n```Trigger ({matches[0][1]}): {matches[0][0]}\nResponse ({matches[0][3]}): {matches[0][2]}```")


        else:
            await ctx.send("Pls provide valid table name.")

    @_remove_a_shenanigan.error
    async def remove_a_shenanigan_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='shenaniganshow', aliases = ['showshenanigan', 'showshenanigans', 'shenanigansshow'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _show_shenanigans(self, ctx: commands.Context, *args):
        """🔒 Shows DB entries
        
        First argument needs to specify the database table:
        > `inspire` 
        > `mrec` 
        > `sudo` 
        > `custom`
        """
        if len(args) == 0:
            await ctx.send("Command needs an argument, either: `inspire`, `mrec`, `sudo` or `custom`")
            return

        table = args[0].lower()
        conSH = sqlite3.connect('databases/shenanigans.db')
        curSH = conSH.cursor()

        is_custom = False


        if table in ['inspire', 'inspi', 'inspiring', 'quote']:
            item_list = [[util.forceinteger(item[0]),util.cleantext(item[1]),util.cleantext(item[2]),"<"+util.cleantext(item[3]).strip()+">"] for item in curSH.execute("SELECT quote_id, quote, author, link FROM inspire").fetchall()]
            item_list.sort(key=lambda x: x[0])
            header = "Inspiring quotes IDs"


        elif table in ['rec', 'mrec', 'recommendation', 'recommendations', 'memerecommendation', 'memerecommendations']:
            item_list = [[util.forceinteger(item[0]),util.cleantext(item[1]),util.cleantext(item[2]),"<"+util.cleantext(item[3]).strip()+">"] for item in curSH.execute("SELECT mrec_id, subcommand, alias, link FROM mrec").fetchall()]
            item_list.sort(key=lambda x: x[2])
            item_list.sort(key=lambda x: x[1])
            item_list.sort(key=lambda x: x[0])
            header = "Mrec IDs"


        elif table in ['sudo', 'superuserdo', 'suedough']:
            item_list = [[util.forceinteger(item[0]),util.cleantext(item[1]),util.cleantext(item[2]),util.cleantext(item[3])] for item in curSH.execute("SELECT sudo_id, command, response1, response2 FROM sudo").fetchall()]
            item_list.sort(key=lambda x: x[1])
            item_list.sort(key=lambda x: x[0])
            header = "Sudo command/response IDs"


        elif table in ['custom', 'customresponse', 'customtext', 'customreply', 'customreact', 'customreacts', 'customreaction', 'customreactions']:
            if table in ['custom', 'customresponse']:
                item_list = [[util.forceinteger(item[0]),util.cleantext(item[1].replace("<prefix>", self.prefix)),util.cleantext(item[2]),util.cleantext(item[3]),util.cleantext(item[4])] for item in curSH.execute("SELECT custom_id, trigger_text, trigger_type, response, response_type FROM custom").fetchall()]
            elif table in ['customtext', 'customreply']:
                item_list = [[util.forceinteger(item[0]),util.cleantext(item[1].replace("<prefix>", self.prefix)),util.cleantext(item[2]),util.cleantext(item[3]),util.cleantext(item[4])] for item in curSH.execute("SELECT custom_id, trigger_text, trigger_type, response, response_type FROM custom WHERE response_type = ?", ("text",)).fetchall()]
            else:
                item_list = [[util.forceinteger(item[0]),util.cleantext(item[1].replace("<prefix>", self.prefix)),util.cleantext(item[2]),util.cleantext(item[3]),util.cleantext(item[4])] for item in curSH.execute("SELECT custom_id, trigger_text, trigger_type, response, response_type FROM custom WHERE response_type = ?", ("reaction",)).fetchall()]
            item_list.sort(key=lambda x: x[4])
            item_list.sort(key=lambda x: x[2])
            item_list.sort(key=lambda x: x[1])
            item_list.sort(key=lambda x: x[0])
            header = "Custom trigger/response IDs"
            is_custom = True

        else:
            await ctx.send("Pls provide valid table name.")
            return


        text_list = []

        if is_custom:
            for item in item_list:
                text_list.append(f"`{item[0]}.` `[{item[2][:20]}/{item[4][:20]}]` {item[1][:50]} `--->` {item[3][:50]}")

        else:
            for item in item_list:
                text_list.append(f"`{item[0]}.` {item[1][:50]}; {item[2][:50]}; {item[3][:50]}")
                
        color = 0xFFFFFF
        await util.multi_embed_message(ctx, header, text_list, color, "", None)

    @_show_shenanigans.error
    async def show_shenanigans_error(self, ctx, error):
        await util.error_handling(ctx, error)




    ###########################################################################################################################################################
    ###########################################################################################################################################################
    ###########################################################################################################################################################

    ###########################################################################################################################################################
    ###########################################################################################################################################################
    ###########################################################################################################################################################

    ###########################################################################################################################################################
    ###########################################################################################################################################################
    ###########################################################################################################################################################

    # RESPONSE EVENT

    @commands.Cog.listener()
    async def on_message(self, message):
        if self.is_inactive():
            return
        if message.author.bot:
            return
        if not self.custom_responses_enabled():
            return

        conSH = sqlite3.connect('databases/shenanigans.db')
        curSH = conSH.cursor()
        curSH.execute('''CREATE TABLE IF NOT EXISTS custom (custom_id text, trigger_text text, trigger_type text, response text, response_type text)''')

        item_list = [[item[0],item[1],item[2],item[3]] for item in curSH.execute("SELECT trigger_text, trigger_type, response, response_type FROM custom").fetchall()]

        msg = message.content.replace("<prefix>", self.prefix).strip()
        msg_lower = message.content.lower().strip()

        for item in item_list:
            trigger_response = False
            trigger_text = item[0].replace("<prefix>", self.prefix).strip()
            trigger_type = item[1]

            if trigger_type == "strict":
                if msg == trigger_text:
                    trigger_response = True
            else:
                trigger_text_lower = trigger_text.lower()

                if trigger_type == "include":
                    if trigger_text_lower in msg_lower:
                        trigger_response = True
                else:
                    if msg_lower == trigger_text_lower:
                        trigger_response = True

            if not trigger_response:
                continue

            response  = item[2]
            response_type = item[3]

            if response_type == 'text':
                response_edit = response.replace("\\n","\n")

                await message.reply(response_edit, mention_author=False)

            else:
                for arg in response.replace(",", " ").replace(";", " ").split():
                    try:
                        await message.add_reaction(arg)
                    except:
                        print(f"Error with response reaction: {arg}")
            


async def setup(bot: commands.bot) -> None:
    await bot.add_cog(
        Shenanigans(bot),
        guilds = [discord.Object(id = int(os.getenv("guild_id")))])