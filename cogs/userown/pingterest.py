import discord
from discord.ext import commands
import datetime
import pytz
from other.utils.utils import Utils as util
import os
import sqlite3



########### AUXILIARY CLASS



class PICheck():
    def pingterests_enabled(ctx):
        conB = sqlite3.connect(f'databases/botsettings.db')
        curB = conB.cursor()
        pingterest_func_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("pingable interests functionality",)).fetchall()]
        if len(pingterest_func_list) == 0:
            raise commands.CheckFailure("Error: PingableInterest setting missing in database.")
            return False
        else:
            pingterest_func = pingterest_func_list[0]
            if pingterest_func == "on":
                return True
            else:
                raise commands.CheckFailure("PingableInterest feature is disabled.")
                return False



########### PINGABLE INTEREST CLASS



class Pingable_Interests(commands.Cog):
    def __init__(self, bot: commands.bot) -> None:
        self.bot = bot
        self.prefix = os.getenv("prefix")



    ##### COMMANDS 


    
    @commands.command(name='pingterest', aliases=['pingableinterest', 'createpi', 'newpi', 'pi'])
    @commands.check(PICheck.pingterests_enabled)
    @commands.check(util.is_active)
    async def _pingterest(self, ctx, *args):
        """*(New) PI + message

        Creates a message with the pingterest to be able to join via react, but also makes an entry in the db for said interest, so that members can join it via -joinpi."""
        

        pi_name = " ".join(args).lower()[:60]

        if pi_name == "":
            emoji = util.emoji("attention")
            await ctx.send(f"No name for pingterest given! {emoji}")
            return

        unallowedchars = [",",":","`","´","'",'"',"‘","’","“","”",";"]
        for char in unallowedchars:
            if char in pi_name:
                await ctx.send(f"Pingterest name cannot have quotes, commas or colons!") 
                return

        conP = sqlite3.connect('databases/pingterest.db')
        curP = conP.cursor()
        pi_list = [[item[0], item[1], item[2], item[3]] for item in curP.execute("SELECT pingterest, userid, username, details FROM pingterests WHERE pingterest = ?", (pi_name,)).fetchall()]
        if len(pi_list) == 0:
            curP.execute("INSERT INTO pingterests VALUES (?, ?, ?, ?)", (pi_name, "", "", "template"))
            conP.commit()
            await util.changetimeupdate()

        pi_title = f"Pingterest: {pi_name}"
        pi_desc = f"Interested in `{pi_name}` and getting pinged? \nReact with ✅ to join this pingable interest. React with 🚫 to leave it."
        pi_desc += f"\n\nYou can always use `{self.prefix}joinpi <pingterest name>` or `{self.prefix}leavepi <pingterest name>` to join or leave later. Check with `{self.prefix}listmypi` to get a list of all the pingterests you joined."

        embed = discord.Embed(title=pi_title, description=pi_desc, color=0x000080)
        message = await ctx.send(embed=embed)
        await message.add_reaction('✅')
        await message.add_reaction('🚫')
            
    @_pingterest.error
    async def pingterest_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='joinpi', aliases=['joinpingterest'])
    @commands.check(PICheck.pingterests_enabled)
    @commands.check(util.is_active)
    async def _joinpi(self, ctx, *args):
        """join pingable interest"""
        user = ctx.message.author
        pi_name = " ".join(args).lower()[:60]

        if pi_name == "":
            emoji = util.emoji("attention")
            await ctx.send(f"No name for pingterest given! {emoji}")
            return

        conP = sqlite3.connect('databases/pingterest.db')
        curP = conP.cursor()

        pi_list = [[item[0], item[1], item[2], item[3]] for item in curP.execute("SELECT pingterest, userid, username, details FROM pingterests WHERE pingterest = ? AND details = ?", (pi_name, "template")).fetchall()]

        if len(pi_list) == 0:
            emoji = util.emoji("attention")
            await ctx.send(f"This pingterest does not exist! {emoji}")
            return

        pi_user = [[item[0], item[1], item[2], item[3]] for item in curP.execute("SELECT pingterest, userid, username, details FROM pingterests WHERE pingterest = ? AND userid = ?", (pi_name, str(user.id))).fetchall()]
        if len(pi_user) == 0:
            curP.execute("INSERT INTO pingterests VALUES (?, ?, ?, ?)", (pi_name, str(user.id), str(user.name), ""))
            conP.commit()
            await util.changetimeupdate()
            emoji = util.emoji("excited")
            await ctx.send(f"You successfully joined this pingterest! {emoji}")
        else:
            emoji = util.emoji("ohh")
            await ctx.send(f"You already joined this pingterest! {emoji}")
    @_joinpi.error
    async def joinpi_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='leavepi', aliases=['leavepingterest'])
    @commands.check(PICheck.pingterests_enabled)
    @commands.check(util.is_active)
    async def _leavepi(self, ctx, *args):
        """leave pingable interest"""
        user = ctx.message.author
        pi_name = " ".join(args).lower()[:60]

        if pi_name == "":
            emoji = util.emoji("attention")
            await ctx.send(f"No name for pingterest given! {emoji}")
            return

        conP = sqlite3.connect('databases/pingterest.db')
        curP = conP.cursor()

        pi_list = [[item[0], item[1], item[2], item[3]] for item in curP.execute("SELECT pingterest, userid, username, details FROM pingterests WHERE pingterest = ? AND details = ?", (pi_name, "template")).fetchall()]

        if len(pi_list) == 0:
            emoji = util.emoji("attention")
            await ctx.send(f"This pingterest does not exist! {emoji}")
            return

        pi_user = [[item[0], item[1], item[2], item[3]] for item in curP.execute("SELECT pingterest, userid, username, details FROM pingterests WHERE pingterest = ? AND userid = ?", (pi_name, str(user.id))).fetchall()]
        if len(pi_user) != 0:
            curP.execute("DELETE FROM pingterests WHERE pingterest = ? AND userid = ?", (pi_name, str(user.id)))
            conP.commit()
            await util.changetimeupdate()
            emoji = util.emoji("grin")
            await ctx.send(f"You successfully left this pingterest! {emoji}")
        else:
            emoji = util.emoji("ohh")
            await ctx.send(f"You haven't even joined this pingterest! {emoji}")
    @_leavepi.error
    async def leavepi_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='listmypi', aliases=['listmypis', 'listmypingterests', 'listmypingterest'])
    @commands.check(PICheck.pingterests_enabled)
    @commands.check(util.is_active)
    async def _listmypi(self, ctx, *args):
        """lists user's PI
        
        use `-listmypi compact` to not show each pingterest in a separate line
        """
        argument = " ".join(args).lower()
        conP = sqlite3.connect('databases/pingterest.db')
        curP = conP.cursor()
        user = ctx.message.author
        user_pis = [[item[0], item[1], item[2], item[3]] for item in curP.execute("SELECT pingterest, userid, username, details FROM pingterests WHERE userid = ? ORDER BY pingterest", (str(user.id),)).fetchall()]
        
        userpistring = ""
        i = 0
        for pi in user_pis:
            i += 1
            if i == len(user_pis):
                userpistring += str(pi[0])

            elif argument in ["c","cmpct","compact"]:
                userpistring += str(pi[0]) + ", "
            else:
                userpistring += str(pi[0]) + "\n"

        title = f"Pingterests of {util.cleantext2(str(user.name))}:"
        embed = discord.Embed(title=title, description=userpistring[:4096], color=0xFBCEB1)
        await ctx.send(embed=embed)
    @_listmypi.error
    async def listmypi_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='pisubs', aliases=['pisubscribers'])
    @commands.check(PICheck.pingterests_enabled)
    @commands.check(util.is_active)
    async def _pisubscribers(self, ctx, *args):
        """lists subscribers of given pingterest

        use `-pisubs compact` to not display entries one per line"""
        argument = " ".join(args).lower()
        conP = sqlite3.connect('databases/pingterest.db')
        curP = conP.cursor()
        user = ctx.message.author
        pi_name = " ".join(args).lower()[:60]

        if pi_name == "":
            await ctx.send("Command needs an argument :s")
            return
        
        pi_subs = [[item[0], item[1], item[2], item[3]] for item in curP.execute("SELECT pingterest, userid, username, details FROM pingterests WHERE pingterest = ?", (pi_name,)).fetchall()]
        
        pisubsstring = ""
        i = 0 # counts elements of pi_subs
        k = 0 # counts actual people
        for pi in pi_subs:
            i += 1
            if str(pi[1]) == "":
                pass 
            else:
                k += 1
                if i == len(pi_subs):
                    pisubsstring += f"<@{str(pi[1])}>"

                elif argument in ["c","cmpct","compact"]:
                    pisubsstring += f"<@{str(pi[1])}>" + ", "
                else:
                    pisubsstring += f"<@{str(pi[1])}>" + "\n"

        if pisubsstring == "":
            if i == 0:
                pisubsstring = "*pi does not exist*"
                footer = ""
            elif i == 1:
                pisubsstring = "*no subscribers*"
                footer = ""
            else:
                pisubsstring = "*no subscribers*"
                footer = "however multiple empty entries"

        title = f"Subscribers of {pi_name} ({k})"
        embed = discord.Embed(title=title, description=pisubsstring, color=0xFBCEB1)
        if footer != "":
             embed.set_footer(text=footer)
        await ctx.send(embed=embed)
    @_pisubscribers.error
    async def pisubscribers_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='listallpi', aliases=['listpi', 'listpis', 'listallpis', 'listallpingterests', 'listallpingterest'])
    @commands.check(PICheck.pingterests_enabled)
    @commands.check(util.is_active)
    async def _listpi(self, ctx, *args):
        """lists all PI

        use `-listallpi compact` to not display entries one per line"""
        argument = " ".join(args).lower()
        conP = sqlite3.connect('databases/pingterest.db')
        curP = conP.cursor()
        
        all_pis = [[item[0], item[1], item[2], item[3]] for item in curP.execute("SELECT pingterest, userid, username, details FROM pingterests WHERE details = ?", ("template",)).fetchall()]
        
        allpistring = ""
        i = 0
        for pi in all_pis:
            i += 1
            if i == len(all_pis):
                allpistring += str(pi[0])

            elif argument in ["c","cmpct","compact"]:
                allpistring += str(pi[0]) + ", "
            else:
                allpistring += str(pi[0]) + "\n"

        embed = discord.Embed(title="all pingterests:", description=allpistring, color=0xFBCEB1)
        await ctx.send(embed=embed)
    @_listpi.error
    async def listpi_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='clearpi', aliases=['clearpingterest'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(PICheck.pingterests_enabled)
    @commands.check(util.is_active)
    async def _clearpi(self, ctx, *args):
        """🔒 removes given PI"""
        conP = sqlite3.connect('databases/pingterest.db')
        curP = conP.cursor()

        pi_name = " ".join(args).lower()[:60]
        pi_entries = [[item[0], item[1], item[2], item[3]] for item in curP.execute("SELECT pingterest, userid, username, details FROM pingterests WHERE pingterest = ?", (pi_name,)).fetchall()]
        
        if len(pi_entries) == 0:
            emoji = await util.emoji("hmm")
            await ctx.send(f"Such a pingterest does not exist. {emoji}")
            return 

        curP.execute("DELETE FROM pingterests WHERE pingterest = ?", (pi_name,))
        conP.commit()
        await util.changetimeupdate()
        emoji = await util.emoji("smug")
        await ctx.send(f"Successfully deleted this pingterest! {emoji}")
    @_clearpi.error
    async def clearpi_error(self, ctx, error):
        await util.error_handling(ctx, error) 



    @commands.command(name='clearallpi', aliases=['clearallpis', 'clearallpingterest', 'clearallpingterests'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(PICheck.pingterests_enabled)
    @commands.check(util.is_active)
    async def _clearallpi(self, ctx, *args):
        """🔒 removes all PIs"""
        conP = sqlite3.connect('databases/pingterest.db')
        curP = conP.cursor()
        curP.execute('''CREATE TABLE IF NOT EXISTS pingterests (pingterest text, userid text, username text, details text)''')
        curP.execute("DELETE FROM pingterests")
        conP.commit()
        emoji = await util.emoji("unleashed")
        await ctx.send(f"Successfully cleared the entire pingterest database! {emoji}")
    @_clearallpi.error
    async def clearallpi_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='ping', aliases=['pingall'])
    @commands.check(PICheck.pingterests_enabled)
    @commands.check(util.is_active)
    async def _ping(self, ctx, *args):
        """Pings members of PI

        You can use a comma to add a message to the ping, i.e. write `-ping <pinterest name>, <message content>`"""

        conP = sqlite3.connect('databases/pingterest.db')
        curP = conP.cursor()

        argsstring = " ".join(args).lower()

        if "," in argsstring:
            pi_name = " ".join(args).lower().split(",")[0][:60]
            additional_msg = "\n" + " ".join(args).split(",", 1)[-1]
        else:
            pi_name = argsstring[:60]
            additional_msg = ""

        all_pis = [[item[0], item[1], item[2], item[3]] for item in curP.execute("SELECT pingterest, userid, username, details FROM pingterests WHERE pingterest = ? AND details = ?", (pi_name,"")).fetchall()]
        
        if len(all_pis) == 0:
            emoji = await util.emoji("cry")
            await ctx.send(f"No one has said pingterest {emoji}")
            return
        
        wordlist = [f"**New {pi_name} ping!**\n"]
        for pi in all_pis:
            wordlist.append(f"<@{str(pi[1])}>")
        wordlist.append(f'\n\n(If you also wish to be pinged in the future use {self.prefix}joinpi {pi_name}, if you no longer want to be pinged for these events use {self.prefix}leavepi {pi_name})')
        
        await util.multi_message(ctx, wordlist, None)
    @_ping.error
    async def ping_error(self, ctx, error):
        await util.error_handling(ctx, error)



async def setup(bot: commands.bot) -> None:
    await bot.add_cog(
        Pingable_Interests(bot),
        guilds = [discord.Object(id = int(os.getenv("guild_id")))])