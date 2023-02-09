import os
import datetime
import asyncpraw
import discord
from discord.ext import commands
import asyncio
import asyncprawcore
import re
import time
import random
import sqlite3
import subprocess
from emoji import UNICODE_EMOJI
import functools
import itertools
import math
from async_timeout import timeout
import requests




class Memo(commands.Cog):
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


    #backlog
    @commands.command(name='backlogfull', aliases = ["blf", "memo", "blfull"])
    async def _backlogfull(self, ctx, *args):
        """Show backlog

        Shows your memo list / backlog.
        """    
        conbg = sqlite3.connect('cogs/backlog/memobacklog.db')
        curbg = conbg.cursor()
        curbg.execute('''CREATE TABLE IF NOT EXISTS memobacklog (bgid text, userid text, username text, backlog text, details text)''')
        
        user = ctx.message.author
        user_bg_list = [[item[0], item[1], item[2], item[3], item[4]] for item in curbg.execute("SELECT bgid, userid, username, backlog, details FROM memobacklog WHERE userid = ? ORDER BY bgid", (str(user.id),)).fetchall()]

        show_instead_command = True
        if len(args) == 0:
            show_instead_command = True
        elif args[0] in ["add", "del", "delete", "ed", "edit", "deleteall", "clear", "sug", "suggest", "rec", "recommend", "swap", "sw", "rotate", "rt", "shift", "sh", "verbosity", "verbose"]:
            show_instead_command = False
        else:
            show_instead_command = True

        if len(args) >= 1:
            if len(args[0]) > 3:
                pum = args[0] #potential user mention
                if (pum[0] == "<") and (pum[1] == "@") and (">" in pum):
                    start = '<@'
                    end = '>'

                    pum_id = pum[len(start):pum.find(end)]
                    print(pum_id)
                    try:
                        #get user with said id
                        user = await ctx.guild.fetch_member(pum_id)
                        user_bg_list = [[item[0], item[1], item[2], item[3], item[4]] for item in curbg.execute("SELECT bgid, userid, username, backlog, details FROM memobacklog WHERE userid = ? ORDER BY bgid", (pum_id,)).fetchall()]
                        print(f'bl command: different user mention: {pum_id}')
                    except:
                        await ctx.send("Error with user mention. :(")


        if show_instead_command:
            header = "**Backlog/Memo of %s** (%s):\n" % (str(user.display_name), str(len(user_bg_list)))
            bg_msg = [header]
            i = 0 #indexnumber
            k = 0 #messagenumber
            for bg_item in user_bg_list:
                i = i+1
                bg = bg_item[3]
                msgpart = str(i) + '. `' + bg + '`' + '\n'

                if len(bg_msg[k]) + len(msgpart) <= 1900:
                    bg_msg[k] = bg_msg[k] + msgpart 
                else:
                    k = k+1
                    #bg_msg[k] = msgpart
                    bg_msg.append(msgpart)

            for msg in bg_msg:
                await ctx.send(msg)
        else:
            await ctx.send("in construction")


    #backlog with pages
    @commands.command(name='backlog', aliases = ["bl", "blp", "backlogpages"])
    async def _backlogpages(self, ctx, *args):
        """Show backlog

        Shows your memo list / backlog.
        """    
        conbg = sqlite3.connect('cogs/backlog/memobacklog.db')
        curbg = conbg.cursor()
        curbg.execute('''CREATE TABLE IF NOT EXISTS memobacklog (bgid text, userid text, username text, backlog text, details text)''')
        
        bl_user = ctx.message.author
        user_bg_list = [[item[0], item[1], item[2], item[3], item[4]] for item in curbg.execute("SELECT bgid, userid, username, backlog, details FROM memobacklog WHERE userid = ? ORDER BY bgid", (str(bl_user.id),)).fetchall()]
        try:
            hexcolor = bl_user.color 
        except:
            hexcolor = 0xffffff

        if len(args) >= 1:
            if len(args[0]) > 3:
                pum = args[0] #potential user mention
                if (pum[0] == "<") and (pum[1] == "@") and (">" in pum):
                    start = '<@'
                    end = '>'

                    pum_id = pum[len(start):pum.find(end)]
                    print(pum_id)
                    try:
                        #get user with said id
                        bl_user = await ctx.guild.fetch_member(pum_id)
                        user_bg_list = [[item[0], item[1], item[2], item[3], item[4]] for item in curbg.execute("SELECT bgid, userid, username, backlog, details FROM memobacklog WHERE userid = ? ORDER BY bgid", (pum_id,)).fetchall()]
                        print(f'bl command: different user mention: {pum_id}, {bl_user.display_name}')
                    except:
                        await ctx.send("Error with user mention. :(")     

                    try:
                        hexcolor = bl_user.color 
                    except:
                        hexcolor = 0x000000                   

        #if len(user_bg_list) > 0:
        #    pages = math.ceil(len(user_bg_list)/15)
        #else:
        #    pages = 1 
        cur_page = 1

        contents = [""]
        i = 0 #indexnumber
        k = 0 #pagenumber
        for bg_item in user_bg_list:
            i = i+1
            bg = bg_item[3]
            msgpart = str(i) + '. `' + bg + '`' + '\n'

            if len(contents[k]) + len(msgpart) <= 1500 and (i - k*15) <= 15:
                contents[k] = contents[k] + msgpart 
            else:
                k = k+1
                #contents[k] = msgpart
                contents.append(msgpart)

        pages = len(contents)
        

        header = "**Backlog/Memo of %s** (%s):\n" % (str(bl_user.display_name), str(len(user_bg_list)))
        embed=discord.Embed(title=header, description=(f"{contents[cur_page-1]}"), color=hexcolor)
        #embed.set_author(name=ctx.author.display_name,icon_url=ctx.author.avatar_url)
        embed.set_footer(text=f"Page {cur_page}/{pages}")
        message = await ctx.send(embed=embed)
        # getting the message object for editing and reacting

        if pages > 1:
            if pages > 2:
                await message.add_reaction("⏮️")

            await message.add_reaction("◀️")
            await message.add_reaction("▶️")

            if pages > 2:
                await message.add_reaction("⏭️")

            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["◀️", "▶️", "⏮️", "⏭️"]
                # This makes sure nobody except the command sender can interact with the "menu"

            while True:
                try:
                    reaction, user = await self.bot.wait_for("reaction_add", timeout=60, check=check)
                    # waiting for a reaction to be added - times out after x seconds, 60 in this
                    # example

                    header = "**Backlog/Memo of %s** (%s):\n" % (str(bl_user.display_name), str(len(user_bg_list)))

                    if str(reaction.emoji) == "▶️" and cur_page != pages:
                        cur_page += 1
                        new_embed=discord.Embed(title=header, description=(f"{contents[cur_page-1]}"), color=hexcolor)
                        #new_embed.set_author(name=ctx.author.display_name,icon_url=ctx.author.avatar_url)
                        new_embed.set_footer(text=f"Page {cur_page}/{pages}")
                        await message.edit(embed=new_embed)
                        await message.remove_reaction(reaction, user)

                    elif str(reaction.emoji) == "◀️" and cur_page > 1:
                        cur_page -= 1
                        new_embed=discord.Embed(title=header, description=(f"{contents[cur_page-1]}"), color=hexcolor)
                        #new_embed.set_author(name=ctx.author.display_name,icon_url=ctx.author.avatar_url)
                        new_embed.set_footer(text=f"Page {cur_page}/{pages}")
                        await message.edit(embed=new_embed)
                        await message.remove_reaction(reaction, user)

                    elif str(reaction.emoji) == "⏮️" and cur_page > 1:
                        cur_page = 1 #back to first page
                        new_embed=discord.Embed(title=header, description=(f"{contents[cur_page-1]}"), color=hexcolor)
                        #new_embed.set_author(name=ctx.author.display_name,icon_url=ctx.author.avatar_url)
                        new_embed.set_footer(text=f"Page {cur_page}/{pages}")
                        await message.edit(embed=new_embed)
                        await message.remove_reaction(reaction, user)

                    elif str(reaction.emoji) == "⏭️" and cur_page != pages:
                        cur_page = pages #to last page
                        new_embed=discord.Embed(title=header, description=(f"{contents[cur_page-1]}"), color=hexcolor)
                        #new_embed.set_author(name=ctx.author.display_name,icon_url=ctx.author.avatar_url)
                        new_embed.set_footer(text=f"Page {cur_page}/{pages}")
                        await message.edit(embed=new_embed)
                        await message.remove_reaction(reaction, user)

                    else:
                        await message.remove_reaction(reaction, user)
                        # removes reactions if the user tries to go forward on the last page or
                        # backwards on the first page
                except asyncio.TimeoutError:
                    #await message.delete()
                    new_embed=discord.Embed(title=header, description=(f"{contents[cur_page-1]}"), color=hexcolor)
                    #new_embed.set_author(name=ctx.author.display_name,icon_url=ctx.author.avatar_url)
                    new_embed.set_footer(text=f"Page {cur_page}/{pages}")
                    await message.edit(embed=new_embed)

                    print("▶️ remove bot reactions ◀️")
                    guild = ctx.guild
                    mdmbot = ctx.guild.get_member(958105284759400559)
                    await message.remove_reaction("⏭️", mdmbot)
                    await message.remove_reaction("▶️", mdmbot)
                    await message.remove_reaction("◀️", mdmbot)
                    await message.remove_reaction("⏮️", mdmbot)
                    break
                    # ending 




    #add to backlog
    @commands.command(name='add')
    async def _add(self, ctx, *args):
        """Add to backlog

        Adds an item to the bottom of your memo/backlog. You can add multiple entries seperated by a semi-colon ;
        
        You can specify a category for the items by writing -add [<categoryname>]. The categoryname needs to be the first argument and within brackets, no spaces or semicolons!
        """
        conbg = sqlite3.connect('cogs/backlog/memobacklog.db')
        curbg = conbg.cursor()
        curbg.execute('''CREATE TABLE IF NOT EXISTS memobacklog (bgid text, userid text, username text, backlog text, details text)''')
        
        user = ctx.message.author


        # category 
        has_category = False
        category = ""
        args_without_category = []
        for arg in args:
            args_without_category.append(arg)
        if len(args) > 0:
            first_arg = args[0]
            if len(first_arg) >= 2:
                if first_arg[0] == "[" and first_arg[-1] == "]":
                    if len(first_arg) > 2:
                        has_category = True 
                        category = first_arg[1:len(first_arg)-1]
                        if category.lower() == "default":
                            category = ""
                    else:
                        pass 

                    args_without_category = args_without_category[1:]


        args2 = []
        for arg in args_without_category:
            args2.append(arg.replace("´", "'").replace("`", "'").replace("’", "'"))
        arguments = ' '.join(args2).split(";")

        i = 0
        for arg in arguments:
            i = i+1

            bg = arg.strip()
            if bg == "-" or bg == "":
               bg = "--------------------------------"

            if len(bg) > 300:
                bg = bg[:297] + "..."

            now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())
            mmid = str(now) + "_" + str(user.id) + "_" + str(i).zfill(4)

            # sanity check begin
            bg_id_list = [item[0] for item in curbg.execute("SELECT bgid, userid, username, backlog, details FROM memobacklog WHERE userid = ? ORDER BY bgid", (str(user.id),)).fetchall()]
            while mmid in bg_id_list:
                mmid = mmid + "x"
            # sanity check end

            curbg.execute("INSERT INTO memobacklog VALUES (?, ?, ?, ?, ?)", (mmid, str(user.id), str(user.name), bg, category))
            conbg.commit()
        if len(bg_id_list) + i >= 10000:
            await ctx.send(f'Your backlog reached a critical size and some commands will cause problems. \n Oi tech support, <@586358910148018189>, have a look into this mess.')
        if i == 1:
            await ctx.send(f'`added 1 new entry into your backlog!`')
        else:
            await ctx.send(f'`added {i} new entries into your backlog!`')
    @_add.error
    async def add_error(self, ctx, error, *args):
        await ctx.send(f'Some error ocurred <:seenoslowpoke:975062347871842324>\nCheck whether you do not use quotation marks or other characters that break discord... <:woozybread:976283266413908049>') 



    #remove from backlog
    @commands.command(name='del', aliases = ['delete'])
    async def _del(self, ctx, *args):
        """Delete from backlog

        Deletes an item of your memo/backlog at a given index number.
        """
        conbg = sqlite3.connect('cogs/backlog/memobacklog.db')
        curbg = conbg.cursor()
        curbg.execute('''CREATE TABLE IF NOT EXISTS memobacklog (bgid text, userid text, username text, backlog text, details text)''')
        
        user = ctx.message.author
        user_bg_list = [[item[0], item[1], item[2], item[3], item[4]] for item in curbg.execute("SELECT bgid, userid, username, backlog, details FROM memobacklog WHERE userid = ? ORDER BY bgid", (str(user.id),)).fetchall()]


        #bulk delete
        if len(args) > 1:
            if "to" == args[1]:
                if len(args) == 3:
                    try:
                        start = int(args[0])
                        end = int(args[2])
                        print(start)
                        print(end)
                    except:
                        start = 1
                        end = 0
                        print("found 'to' in delete command, but something went wrong")
                    if start > end:
                        await ctx.send(f'`Argument error.` <:thvnk:957075985721864263>') 
                        args = ()
                    else:
                        if end > len(user_bg_list):
                            end = len(user_bg_list)
                            await ctx.send(f'`End marker larger than backlog size. Corrected marker.`') 
                        args = range(start, end+1, 1)
                else:
                    await ctx.send(f'`Argument error. 🤖`')
                    args = ()

        ###

        n = 0 #number of valid arguments
        for arg in args:
            try:
                i = int(arg)
                if i == 0:
                    #ctx.send(f'Argument must be a non-zero integer!')
                    print('Argument must be a non-zero integer!')
            except:
                i = 0
                #await ctx.send(f'Argument must be an integer!')
                print('Argument must be an integer!')
                break

            if i > 0:
                if i <= len(user_bg_list):
                    n = n+1
                    entry = user_bg_list[i-1]
                    entry_id = entry[0] 

                    curbg.execute("DELETE FROM memobacklog WHERE bgid = ?", (str(entry_id),))
                    conbg.commit()
                    print('deleted entry')
                else:
                    #await ctx.send(f'You do not have that many entries in your backlog.')
                    print('You do not have that many entries in your backlog.')

            elif i < 0:
                #await ctx.send(f'I cannot deal with negative numbers. Yet. <:smug:955227749415550996>')
                print('I cannot deal with negative numbers. Yet.')

        if n == 0:
            await ctx.send(f'`something went wrong :(`')  
        elif n == 1:
            try:
                entry_name = str(entry[3])
            except:
                entry_name = "1 entry"

            await ctx.send(f'`deleted {entry_name} from your backlog!`') 
        else:
            await ctx.send(f'`deleted {n} entries from your backlog!`')


    #edit backlog
    @commands.command(name='edit', aliases = ['ed'])
    async def _edit(self, ctx, *args):
        """Edit backlog

        Edits an item of your memo/backlog at a given index number.
        """
        conbg = sqlite3.connect('cogs/backlog/memobacklog.db')
        curbg = conbg.cursor()
        curbg.execute('''CREATE TABLE IF NOT EXISTS memobacklog (bgid text, userid text, username text, backlog text, details text)''')
        
        user = ctx.message.author
        user_bg_list = [[item[0], item[1], item[2], item[3], item[4]] for item in curbg.execute("SELECT bgid, userid, username, backlog, details FROM memobacklog WHERE userid = ? ORDER BY bgid", (str(user.id),)).fetchall()]

        args2 = []
        for arg in args:
            args2.append(arg.replace("´", "'").replace("`", "'"))

        if len(args2) == 0:
            await ctx.send(f'missing index argument')
        else:
            try:
                i = int(args2[0])
                if i == 0:
                    ctx.send(f'Argument must be a non-zero integer!')
                    print('index must be a non-zero integer!')
            except:
                i = 0
                await ctx.send(f'Argument must be an integer!')
                print('index must be an integer!')

            if i > 0:
                if i <= len(user_bg_list):
                    entry = user_bg_list[i-1]
                    entry_id = entry[0] 

                    oldbacklog = entry[3]
                    newbacklog = ' '.join(args2[1:]).strip()

                    if newbacklog == "-" or newbacklog == "":
                        newbacklog = "--------------------------------"

                    if len(newbacklog) > 300:
                        newbacklog = newbacklog[:297] + "..."

                    curbg.execute("UPDATE memobacklog SET backlog = ? WHERE bgid = ?", (newbacklog, entry_id))
                    conbg.commit()
                    print('Updated entry')
                    await ctx.send(f'Updated `{oldbacklog}` to `{newbacklog}`. <:kowalskinotes:975580577963057202>!')
                else:
                    await ctx.send(f'You do not have that many entries in your backlog.')
                    print('You do not have that many entries in your backlog.')

            elif i < 0:
                await ctx.send(f'I cannot deal with negative numbers. Yet. <:smug:955227749415550996>')
                print('I cannot deal with negative numbers. Yet.')
    @_edit.error
    async def edit_error(self, ctx, error, *args):
        await ctx.send(f'Some error ocurred <:seenoslowpoke:975062347871842324>\nCheck whether you do not use quotation marks or other characters that break discord... <:woozybread:976283266413908049>') 



    #clear backlog
    @commands.command(name='clearall', aliases = ['deleteall'])
    async def _clear(self, ctx, *args):
        """Clear backlog

        Deletes entire backlog.
        """
        conbg = sqlite3.connect('cogs/backlog/memobacklog.db')
        curbg = conbg.cursor()
        curbg.execute('''CREATE TABLE IF NOT EXISTS memobacklog (bgid text, userid text, username text, backlog text, details text)''')
        
        user = ctx.message.author
        user_bg_list = [[item[0], item[1], item[2], item[3], item[4]] for item in curbg.execute("SELECT bgid, userid, username, backlog, details FROM memobacklog WHERE userid = ? ORDER BY bgid", (str(user.id),)).fetchall()]
        try:
            hexcolor = user.color 
        except:
            hexcolor = 0x000000 


        ## create securtiy confirmation

        header = "**Complete deletion of Backlog/Memo of %s** (%s):\n" % (str(user.display_name), str(len(user_bg_list)))
        conf_text = f"Are you sure you want to clear all entries from your backlog/memo? <:attention:961365426091229234>\n{str(len(user_bg_list))} items in total\n\n ✅ Yes, delete everything.\n ⛔ No, stop. Don't delete my backlog."
        embed=discord.Embed(title=header, description=conf_text, color=hexcolor)
        #embed.set_author(name=ctx.author.display_name,icon_url=ctx.author.avatar_url)
        embed.set_footer(text=f"status: pending")
        message = await ctx.send(embed=embed)
        # getting the message object for editing and reacting

        await message.add_reaction("✅")
        await message.add_reaction("⛔")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅","⛔"]
            # This makes sure nobody except the command sender can interact with the "menu"

        decision_made = False
        try:
            guild = ctx.guild
            mdmbot = ctx.guild.get_member(958105284759400559)
        except:
            print("could not find mdm bot member object")

        while True:
            try:
                reaction, user = await bot.wait_for("reaction_add", timeout=60, check=check)
                # waiting for a reaction to be added - times out after x seconds, 60 in this
                # example

                header = "**Backlog/Memo of %s**:\n" % (str(user.display_name))

                if str(reaction.emoji) == "✅" and decision_made == False:
                    new_embed=discord.Embed(title=header, description=conf_text, color=hexcolor)
                    #new_embed.set_author(name=ctx.author.display_name,icon_url=ctx.author.avatar_url)
                    new_embed.set_footer(text=f"status: approved")
                    await message.edit(embed=new_embed)
                    decision_made = True

                    curbg.execute("DELETE FROM memobacklog WHERE userid = ?", (str(user.id),))
                    conbg.commit()
                    await ctx.send(f'Cleared entire backlog. <:hellmo:954376033921040425>')
                    print('approved: backlog cleared')
                    await message.remove_reaction("✅", mdmbot)
                    await message.remove_reaction("⛔", mdmbot)

                elif str(reaction.emoji) == "⛔" and decision_made == False:
                    new_embed=discord.Embed(title=header, description=conf_text, color=hexcolor)
                    #new_embed.set_author(name=ctx.author.display_name,icon_url=ctx.author.avatar_url)
                    new_embed.set_footer(text=f"status: denied")
                    await message.edit(embed=new_embed)
                    decision_made = True
                    print('denied: backlog not cleared')
                    await message.remove_reaction("✅", mdmbot)
                    await message.remove_reaction("⛔", mdmbot)

                else:
                    await message.remove_reaction(reaction, user)
                    # removes reactions if the user tries to go forward on the last page or
                    # backwards on the first page
            except asyncio.TimeoutError:
                #await message.delete()
                if decision_made == False:
                    new_embed=discord.Embed(title=header, description=conf_text, color=hexcolor)
                    #new_embed.set_author(name=ctx.author.display_name,icon_url=ctx.author.avatar_url)
                    new_embed.set_footer(text=f"staus: timeouted (auto-denied)")
                    await message.edit(embed=new_embed)
                    print('timeouted: backlog not cleared')
                    await message.remove_reaction("✅", mdmbot)
                    await message.remove_reaction("⛔", mdmbot)

                print("timeout")
                break
                # ending 
        


    #suggest
    @commands.command(name='suggest', aliases = ['sug', 'rec', 'recommend'])
    @commands.check(is_valid_server)
    async def _suggest(self, ctx, *args):
        """Recommend

        Makes a recommendation message. Reacting with 📝 adds it to the reacting users backlog. 
        Everything after a ; symbol will not get added to the backlog, so use it for extra info.
        """
        the_channel = ctx.channel
        conbg = sqlite3.connect('cogs/backlog/memobacklog.db')
        curbg = conbg.cursor()
        curbg.execute('''CREATE TABLE IF NOT EXISTS memobacklog (bgid text, userid text, username text, backlog text, details text)''')

        args2 = []
        for arg in args:
            is_mention = False
            if len(arg) > 3:
                if arg[0] == "<" and arg[1] == "@" and arg[-1] == ">":
                    is_mention = True 
            if is_mention:
                print("@mention detected")
            else:
                args2.append(arg)

        given_string = " ".join(args2).split(";")
        bl_entry = given_string[0].strip()
        msg = "**%s**" % bl_entry[:300]

        if len(given_string) >= 1:
            additionalinfo = ";".join(given_string[1:]).strip()
            msg = "**%s**\n%s" % (bl_entry[:300], additionalinfo[:1500])

        embed = discord.Embed(title="Recommendation", description=msg, color=0x30D5C8)
        footer = "React with 📝 to add it to your backlog."
        icon = "https://i.imgur.com/8IsAjV6.png"
        extra = ""
        embed.set_footer(text = footer)
        embed.set_thumbnail(url=icon)
        message = await the_channel.send(embed=embed)
        # add reactions to them
        await message.add_reaction("📝")

        #def check(reaction, user):
        #    return str(reaction.emoji) in ["📝"]

        #while True:
        #    try:
        #        reaction, user = await self.bot.wait_for("reaction_add", timeout=600, check=check)
                # waiting for a reaction to be added - times out after x seconds, 600 here

        #        if str(reaction.emoji) == "📝":
                    #print(user.id)
                    #print(user.display_name)
            
        #            bl_entry = str(embed.description).split("\n")[0].replace("*", " ").strip()
        #            now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())
        #            mmid = str(now) + "_" + str(user.id) + "_0rec"
        #            print("adding entry to backlog")
        #            curbg.execute("INSERT INTO memobacklog VALUES (?, ?, ?, ?, ?)", (mmid, str(user.id), str(user.name), bl_entry, ""))
        #            conbg.commit()

        #            extra = extra + "\n-added to " + str(user.display_name) + "'s backlog"
        #            embed = discord.Embed(title="Recommendation", description=msg, color=0x30D5C8)
        #            embed.set_footer(text = footer + extra)
        #            embed.set_thumbnail(url=icon)
        #            await message.edit(embed=embed)

        #    except asyncio.TimeoutError:
        #        embed = discord.Embed(title="Recommendation", description=msg, color=0x30D5C8)
        #        bl_entry = str(embed.description).split("\n")[0].replace("*", " ").strip()
        #        altf = "Timeouted: Reactions no longer auto-add to your backlog, but you can still use -add %s to add this entry manually.\n" % (bl_entry)
        #        embed.set_footer(text = altf + extra)
        #        embed.set_thumbnail(url=icon)
        #        await message.edit(embed=embed)
        #        break

    @_suggest.error
    async def suggest_error(self, ctx, error, *args):
        await ctx.send(f'Some error ocurred <:seenoslowpoke:975062347871842324>\nCheck whether you do not use quotation marks or other characters that break discord... <:woozybread:976283266413908049>') 



    #swap
    @commands.command(name='swap', aliases = ['sw', 'rotate', 'rt'])
    async def _swap(self, ctx, *args):
        """Swap entries

        Swaps entries in your backlog. Use -swap <index number> <index number> to swap 2 entries.
        If you put more than 2 index numbers the entries will rotate in the given order.
        """
        if len(args) < 2:
            await ctx.send(f'you need at least 2 arguments!')
        else:
            conbg = sqlite3.connect('cogs/backlog/memobacklog.db')
            curbg = conbg.cursor()
            curbg.execute('''CREATE TABLE IF NOT EXISTS memobacklog (bgid text, userid text, username text, backlog text, details text)''')
            
            user = ctx.message.author
            user_bg_list = [[item[0], item[1], item[2], item[3], item[4]] for item in curbg.execute("SELECT bgid, userid, username, backlog, details FROM memobacklog WHERE userid = ? ORDER BY bgid", (str(user.id),)).fetchall()]
            L = len(user_bg_list) 

            if L < 2:
                await ctx.send(f'You do not have enough list items to perform a swap.')
            else:
                indices = []
                all_valid_ints = True
                try:
                    for arg in args:
                        i = int(arg)
                        if i >= 1 and i <= L:
                            indices.append(i)
                        else:
                            all_valid_ints = False
                except:
                    all_valid_ints = False

                if all_valid_ints:
                    indices.append(indices[0])
                    for k in list(range(len(indices)-1)):
                        i = indices[k]
                        j = indices[k+1]
                        newbacklog = user_bg_list[i-1][3]
                        newcategory = user_bg_list[i-1][4]
                        entry_id = user_bg_list[j-1][0]
                        curbg.execute("UPDATE memobacklog SET backlog = ?, details = ? WHERE bgid = ?", (newbacklog, newcategory, entry_id))
                        conbg.commit()
                    await ctx.send(f'Swapped/rotated entries!')
                else:
                    await ctx.send(f'Error: arguments need to be integers between 1 and {L}')


    #shift
    @commands.command(name='shift', aliases = ['sh'])
    async def _shift(self, ctx, *args):
        """Shift entries

        Shifts entries in your backlog. Use "-shift <index 1> to <index 2>" to shift entry <i1> to position <i2>. You can also write "-shift <index 1> to top" or "-shift <index 1> to bottom", or shift multiple entries with e.g.
        "-shift <i1> <i2> <i3> to <i4>"

        Detail:
        Note that every 'unshifted' item with an index < <i4> remains above the shifted items, while every 'unshifted' item with an index ≥ <i4> will end up below. If however <i4> is the largest index in your backlog or if you use 'bottom', then all 'unshifted' entries will be places above.
        """
        conbg = sqlite3.connect('cogs/backlog/memobacklog.db')
        curbg = conbg.cursor()
        curbg.execute('''CREATE TABLE IF NOT EXISTS memobacklog (bgid text, userid text, username text, backlog text, details text)''')
        
        user = ctx.message.author
        user_bg_list = [[item[0], item[1], item[2], item[3], item[4]] for item in curbg.execute("SELECT bgid, userid, username, backlog, details FROM memobacklog WHERE userid = ? ORDER BY bgid", (str(user.id),)).fetchall()]

        if len(user_bg_list) >= 10000:
            await ctx.send(f'`Error: IDing process not robust for backlogs with 10,000 or more entries.`\n`Interrupted process.`')
            await ctx.send(f'Please clear some of your backlog ffs')
            await ctx.send(f'smh my head')
        else:
            if "to" in args:
                s = args.index("to")

                if s > 0:
                    if s < len(args)-1:
                        if args[-1].lower() == "top":
                            args = args[:-1] + ("1",)
                        elif args[-1].lower() == "bot" or args[-1].lower() == "bottom":
                            args = args[:-1] + (str(len(user_bg_list)),)

                        indices = args[:s]
                        target = args[s+1:]
                        print(indices)
                        print(target)
                        all_indices_valid = True
                        for arg in indices+target:
                            try:
                                x = int(arg)
                            except:
                                x = -1
                            if x < 1 or x > len(user_bg_list):
                                all_indices_valid = False 
                        if all_indices_valid:
                            if len(target) == 1:
                                t = int(target[0])
                                if len(indices) == len(set(indices)):
                                    # actual shift code

                                    bulk_size = len(indices)
                                    bulk = []
                                    for k in list(range(len(indices))):
                                        i = int(indices[int(k)])
                                        bulk.append(user_bg_list[i-1])

                                    if t == len(user_bg_list):
                                        t = len(user_bg_list) + 1

                                    pre_b_items = []
                                    post_b_items = []
                                    for j in list(range(len(user_bg_list))): #indices minus 1
                                        if str(j+1) in indices:
                                            print(f'skip {j+1}')
                                        else:
                                            if j+1 < t:
                                                pre_b_items.append(user_bg_list[j])
                                            else:
                                                post_b_items.append(user_bg_list[j])

                                    newly_ordered_bg_list = pre_b_items + bulk + post_b_items
                                    #print(newly_ordered_bg_list)

                                    for l in list(range(len(user_bg_list))):
                                        newbacklog = newly_ordered_bg_list[l][3]
                                        newcategory = newly_ordered_bg_list[l][4]
                                        entry_id = user_bg_list[l][0]
                                        curbg.execute("UPDATE memobacklog SET backlog = ?, details = ? WHERE bgid = ?", (newbacklog, newcategory, entry_id))
                                        conbg.commit() 

                                    await ctx.send(f'`Shifted {bulk_size} list item(s)!`')                                   

                                else:
                                    await ctx.send(f'Error: there are duplicate indices <:attention:961365426091229234>')
                            else:
                                await ctx.send(f'Error: too many target arguments <:attention:961365426091229234>')
                        else:
                            await ctx.send(f'Error: some indices seem to be invalid <:attention:961365426091229234>')
                    else:
                        await ctx.send(f'Error: there seems to be no target index <:attention:961365426091229234>')
                else:
                    await ctx.send(f'Error: there seem to be no indices to shift <:attention:961365426091229234>')
            else:
                await ctx.send(f'Error: missing to-separator <:attention:961365426091229234>')

    
    #insert into backlog
    @commands.command(name='insert', aliases = ['ins', 'in'])
    async def _insert(self, ctx, *args):
        """Insert at index

        Adds an item to a given index of your memo/backlog. You can add multiple entries seperated by a semi-colon ;
        """
        conbg = sqlite3.connect('cogs/backlog/memobacklog.db')
        curbg = conbg.cursor()
        curbg.execute('''CREATE TABLE IF NOT EXISTS memobacklog (bgid text, userid text, username text, backlog text, details text)''')
        
        user = ctx.message.author
        user_bg_list = [[item[0], item[1], item[2], item[3], item[4]] for item in curbg.execute("SELECT bgid, userid, username, backlog, details FROM memobacklog WHERE userid = ? ORDER BY bgid", (str(user.id),)).fetchall()]

        # category 
        has_category = False
        category = ""
        args_wc = []
        for arg in args:
            args_wc.append(arg)
        if len(args) > 0:
            first_arg = args[0]
            if len(first_arg) >= 2:
                if first_arg[0] == "[" and first_arg[-1] == "]":
                    if len(first_arg) > 2:
                        has_category = True 
                        category = first_arg[1:len(first_arg)-1]
                        if category.lower() == "default":
                            category = ""
                    else:
                        pass 
                    args_wc = args_wc[1:]
                    print("ins: found category argument")


        args2 = []
        if len(args_wc) > 1:
            try:
                index = int(args_wc[0])
                index_valid = True
            except:
                index = 1
                index_valid = False

            if index_valid:
                for arg in args_wc:
                    args2.append(arg.replace("´", "'").replace("`", "'"))
                arguments = ' '.join(args2[1:]).split(";")

                #delete items with higher index
                for k in list(range(len(user_bg_list))):
                    if k+1 < index:
                        pass 
                    else:
                        entry = user_bg_list[k]
                        entry_id = entry[0] 
                        curbg.execute("DELETE FROM memobacklog WHERE bgid = ?", (str(entry_id),))
                        conbg.commit()

                #add new items
                i = 0
                for arg in arguments:
                    i = i+1
                    bg = arg.strip()
                    if bg == "-" or bg == "":
                        bg = "------------------------------------"
                    if len(bg) > 300:
                        bg = bg[:297] + "..."
                    now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())
                    mmid = str(now) + "_" + str(user.id) + "_" + str(i).zfill(4)
                    curbg.execute("INSERT INTO memobacklog VALUES (?, ?, ?, ?, ?)", (mmid, str(user.id), str(user.name), bg, category))
                    conbg.commit()

                #readd old items
                for k in list(range(len(user_bg_list))):
                    if k+1 < index:
                        pass 
                    else:
                        entry = user_bg_list[k]
                        entry_bg = entry[3] 
                        old_cat = entry[4]
                        now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())
                        mmid = str(now) + "_" + str(user.id) + "_re_" + str(k+1).zfill(4)
                        curbg.execute("INSERT INTO memobacklog VALUES (?, ?, ?, ?, ?)", (mmid, str(user.id), str(user.name), entry_bg, old_cat))
                        conbg.commit()

                if len(user_bg_list) + i >= 10000:
                    await ctx.send(f'Your backlog reached a critical size and some commands will cause problems. \n Oi tech support, <@586358910148018189>, have a look into this mess.')

                if i == 1:
                    await ctx.send(f'`Inserted 1 new entry into your backlog!`')
                else:
                    await ctx.send(f'`Inserted {i} new entries into your backlog!`')
            else:
                await ctx.send(f'`Error with index argument!`')
        else:
            await ctx.send(f'`Too few arguments!`')
    @_insert.error
    async def insert_error(self, ctx, error, *args):
        await ctx.send(f'Some error ocurred <:seenoslowpoke:975062347871842324>\nCheck whether you do not use quotation marks or other characters that break discord... <:woozybread:976283266413908049>') 


    #
    #backlog with categories
    @commands.command(name='backlogcat', aliases = ["blc", "backlogcategory"])
    async def _backlogcategories(self, ctx, *args):
        """Show backlog

        Shows your memo list / backlog filtered by a given category.
        Use -blc <categoryname>
        or
        -blc <@user mention> <categoryname>
        for other users backlog.
        Note that categories cannot have spaces.
        """    
        conbg = sqlite3.connect('cogs/backlog/memobacklog.db')
        curbg = conbg.cursor()
        curbg.execute('''CREATE TABLE IF NOT EXISTS memobacklog (bgid text, userid text, username text, backlog text, details text)''')
        
        bl_user = ctx.message.author
        user_bg_list = [[item[0], item[1], item[2], item[3], item[4]] for item in curbg.execute("SELECT bgid, userid, username, backlog, details FROM memobacklog WHERE userid = ? ORDER BY bgid", (str(bl_user.id),)).fetchall()]

        try:
            hexcolor = bl_user.color 
        except:
            hexcolor = 0xffffff

        if len(args) == 0:
            category = ""
        else:
            category = args[0]
            if category.lower() == "default":
                category = ""

        if len(args) >= 1:
            if len(args[0]) > 3:
                pum = args[0] #potential user mention
                if (pum[0] == "<") and (pum[1] == "@") and (">" in pum):
                    start = '<@'
                    end = '>'

                    pum_id = pum[len(start):pum.find(end)]
                    print(pum_id)

                    if len(args) == 1:
                        category = ""
                    else:
                        category = args[1]
                        if category.lower() == "default":
                            category = ""
                    try:
                        #get user with said id
                        bl_user = await ctx.guild.fetch_member(pum_id)
                        user_bg_list = [[item[0], item[1], item[2], item[3], item[4]] for item in curbg.execute("SELECT bgid, userid, username, backlog, details FROM memobacklog WHERE userid = ? ORDER BY bgid", (pum_id,)).fetchall()]
                        print(f'bl command: different user mention: {pum_id}')
                    except:
                        await ctx.send("Error with user mention. :(")     

                    try:
                        hexcolor = user.color 
                    except:
                        hexcolor = 0x000000      

        user_bg_list_indexed = []
        for j in range(1, len(user_bg_list)+1):
            item = user_bg_list[j-1]
            indexed_item = item + [str(j)]
            if item[4].lower() == category.lower():
                user_bg_list_indexed.append(indexed_item)             

        cur_page = 1

        contents = [""]
        i = 0 #indexnumber
        k = 0 #pagenumber
        for bg_item in user_bg_list_indexed:
            i = i+1
            bg = bg_item[3]
            index = str(bg_item[5])
            msgpart = index + '. `' + bg + '`' + '\n'

            if len(contents[k]) + len(msgpart) <= 1500 and (i - k*15) <= 15:
                contents[k] = contents[k] + msgpart 
            else:
                k = k+1
                #contents[k] = msgpart
                contents.append(msgpart)

        pages = len(contents)
        
        if category == "":
            headercat = "default"
        else:
            headercat = category

        header = "**Backlog [%s] of %s** (%s/%s):\n" % (headercat, str(bl_user.display_name), str(len(user_bg_list_indexed)), str(len(user_bg_list)))
        embed=discord.Embed(title=header, description=(f"{contents[cur_page-1]}"), color=hexcolor)
        #embed.set_author(name=ctx.author.display_name,icon_url=ctx.author.avatar_url)
        embed.set_footer(text=f"Page {cur_page}/{pages}")
        message = await ctx.send(embed=embed)
        # getting the message object for editing and reacting

        if pages > 1:
            if pages > 2:
                await message.add_reaction("⏮️")

            await message.add_reaction("◀️")
            await message.add_reaction("▶️")

            if pages > 2:
                await message.add_reaction("⏭️")

            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["◀️", "▶️", "⏮️", "⏭️"]
                # This makes sure nobody except the command sender can interact with the "menu"

            while True:
                try:
                    reaction, user = await self.bot.wait_for("reaction_add", timeout=60, check=check)
                    # waiting for a reaction to be added - times out after x seconds, 60 in this
                    # example

                    if str(reaction.emoji) == "▶️" and cur_page != pages:
                        cur_page += 1
                        new_embed=discord.Embed(title=header, description=(f"{contents[cur_page-1]}"), color=hexcolor)
                        #new_embed.set_author(name=ctx.author.display_name,icon_url=ctx.author.avatar_url)
                        new_embed.set_footer(text=f"Page {cur_page}/{pages}")
                        await message.edit(embed=new_embed)
                        await message.remove_reaction(reaction, user)

                    elif str(reaction.emoji) == "◀️" and cur_page > 1:
                        cur_page -= 1
                        new_embed=discord.Embed(title=header, description=(f"{contents[cur_page-1]}"), color=hexcolor)
                        #new_embed.set_author(name=ctx.author.display_name,icon_url=ctx.author.avatar_url)
                        new_embed.set_footer(text=f"Page {cur_page}/{pages}")
                        await message.edit(embed=new_embed)
                        await message.remove_reaction(reaction, user)

                    elif str(reaction.emoji) == "⏮️" and cur_page > 1:
                        cur_page = 1 #back to first page
                        new_embed=discord.Embed(title=header, description=(f"{contents[cur_page-1]}"), color=hexcolor)
                        #new_embed.set_author(name=ctx.author.display_name,icon_url=ctx.author.avatar_url)
                        new_embed.set_footer(text=f"Page {cur_page}/{pages}")
                        await message.edit(embed=new_embed)
                        await message.remove_reaction(reaction, user)

                    elif str(reaction.emoji) == "⏭️" and cur_page != pages:
                        cur_page = pages #to last page
                        new_embed=discord.Embed(title=header, description=(f"{contents[cur_page-1]}"), color=hexcolor)
                        #new_embed.set_author(name=ctx.author.display_name,icon_url=ctx.author.avatar_url)
                        new_embed.set_footer(text=f"Page {cur_page}/{pages}")
                        await message.edit(embed=new_embed)
                        await message.remove_reaction(reaction, user)

                    else:
                        await message.remove_reaction(reaction, user)
                        # removes reactions if the user tries to go forward on the last page or
                        # backwards on the first page
                except asyncio.TimeoutError:
                    #await message.delete()
                    new_embed=discord.Embed(title=header, description=(f"{contents[cur_page-1]}"), color=hexcolor)
                    #new_embed.set_author(name=ctx.author.display_name,icon_url=ctx.author.avatar_url)
                    new_embed.set_footer(text=f"Page {cur_page}/{pages}")
                    await message.edit(embed=new_embed)

                    print("▶️ remove bot reactions ◀️")
                    guild = ctx.guild
                    mdmbot = ctx.guild.get_member(958105284759400559)
                    await message.remove_reaction("⏭️", mdmbot)
                    await message.remove_reaction("▶️", mdmbot)
                    await message.remove_reaction("◀️", mdmbot)
                    await message.remove_reaction("⏮️", mdmbot)
                    break
                    # ending 

    @commands.command(name='catedit', aliases = ["cat", "categoryedit", "editcat", "editcategory"])
    async def _blcategoryedit(self, ctx, *args):
        """Edit categories

        write -cat <n1> <n2> .... <nk> <categoryname>
        you can also use -cat <n1> to <n2> <categoryname>
        """    
        conbg = sqlite3.connect('cogs/backlog/memobacklog.db')
        curbg = conbg.cursor()
        curbg.execute('''CREATE TABLE IF NOT EXISTS memobacklog (bgid text, userid text, username text, backlog text, details text)''')
        
        user = ctx.message.author
        user_bg_list = [[item[0], item[1], item[2], item[3], item[4]] for item in curbg.execute("SELECT bgid, userid, username, backlog, details FROM memobacklog WHERE userid = ? ORDER BY bgid", (str(user.id),)).fetchall()]
        
        if len(args) > 1:
            category = args[-1].replace("[","").replace("]","")

            if "to" == args[1]:
                arguments_valid = False
                if len(args) == 4:
                    try:
                        start = int(args[0])
                        end = int(args[2])
                        print(start)
                        print(end)
                    except:
                        start = 1
                        end = 0
                        print("found 'to' in cat-edit command, but something went wrong")
                    if start > end:
                        #await ctx.send(f'`Argument error.` <:thvnk:957075985721864263>') 
                        args2 = []
                    else:
                        if end > len(user_bg_list):
                            end = len(user_bg_list)
                            await ctx.send(f'`End marker larger than backlog size. Corrected marker.`') 
                        args2 = range(start, end+1, 1)
                        arguments_valid = True
                else:
                    await ctx.send(f'`Argument error. 🤖`')
                    args2 = []
            else:
                arguments_valid = True
                args2 = []
                for i in range(0, len(args)-1):
                    try:
                        x = int(args[i])
                        if x <= 0 or x > len(user_bg_list):
                            #ctx.send(f'Argument must be a non-zero integer!')
                            print('Argument must be a non-zero integer!')
                            arguments_valid = False
                        else:
                            args2.append(x)
                    except:
                        #await ctx.send(f'Argument must be an integer!')
                        print('Argument must be an integer!')
                        arguments_valid = False
            ###

            cat = category
            if category == "default":
                category = ""
                cat = "default"

            if arguments_valid:
                for arg in args2:
                    i = int(arg)
                    entry = user_bg_list[i-1]
                    entry_id = entry[0]

                    curbg.execute("UPDATE memobacklog SET details = ? WHERE bgid = ?", (category, entry_id))
                    conbg.commit()

                if len(args2) == 0:
                    await ctx.send(f'`something went wrong :(`')  
                elif len(args2) == 1:
                    try:
                        entry_name = str(entry[3])
                    except:
                        entry_name = "1 entry"

                    await ctx.send(f'`Changed category of {entry_name} to {cat}!`') 
                else:
                    await ctx.send(f'`Changed category of {len(args2)} entries to {cat}!`')
            else:
                await ctx.send(f'`Error: Something about the index arguments seems to be wrong.`')
        else:
            await ctx.send(f'`Error: This command needs at least 2 arguments.`')

    @commands.command(name='showcats', aliases = ["sc", "showc", "showcat", "catlist", "catslist"])
    async def _showcategories(self, ctx, *args):
        """Show categories

        """    
        conbg = sqlite3.connect('cogs/backlog/memobacklog.db')
        curbg = conbg.cursor()
        curbg.execute('''CREATE TABLE IF NOT EXISTS memobacklog (bgid text, userid text, username text, backlog text, details text)''')
        
        user = ctx.message.author
        user_bg_list = [[item[0], item[1], item[2], item[3], item[4]] for item in curbg.execute("SELECT bgid, userid, username, backlog, details FROM memobacklog WHERE userid = ? ORDER BY bgid", (str(user.id),)).fetchall()]
        
        try:
            hexcolor = user.color 
        except:
            hexcolor = 0xffffff

        if len(args) >= 1:
            if len(args[0]) > 3:
                pum = args[0] #potential user mention
                if (pum[0] == "<") and (pum[1] == "@") and (">" in pum):
                    start = '<@'
                    end = '>'

                    pum_id = pum[len(start):pum.find(end)]
                    print(pum_id)
                    try:
                        #get user with said id
                        user = await ctx.guild.fetch_member(pum_id)
                        user_bg_list = [[item[0], item[1], item[2], item[3], item[4]] for item in curbg.execute("SELECT bgid, userid, username, backlog, details FROM memobacklog WHERE userid = ? ORDER BY bgid", (pum_id,)).fetchall()]
                        print(f'bl command: different user mention: {pum_id}')
                    except:
                        await ctx.send("Error with user mention. :(")     

                    try:
                        hexcolor = user.color 
                    except:
                        hexcolor = 0x000000

        cat_dict = {}
        for entry in user_bg_list:
            cat = entry[4].lower()
            if cat in cat_dict.keys():
                prev = cat_dict[cat]
                cat_dict[cat] = str(int(prev)+1)
            else:
                cat_dict[cat] = "1"

        cat_list = ""
        for cat in cat_dict.keys():
            if cat == "":
                category = "default"
            else:
                category = cat
            cat_list = cat_list + "\n" + category + "   (" + cat_dict[cat] + ")"

        header = "**Backlog categories of %s** (%s):\n" % (str(user.display_name), str(len(cat_dict)))
        embed=discord.Embed(title=header, description=(cat_list), color=hexcolor)
        embed.set_footer(text=f"with {str(len(user_bg_list))} items in total")
        message = await ctx.send(embed=embed)


    @commands.command(name='catrename', aliases = ["categoryrename", "catre"])
    async def _categoryrename(self, ctx, *args):
        """Rename category

        first argument: old category name
        second argument: new category name

        """ 
        await ctx.send("under construction <a:mabeltyping:976601600476991509>")


    @commands.command(name='batchrec', aliases = ["batchsuggest"])
    @commands.check(is_valid_server)
    async def _batchsuggest(self, ctx, *args):
        """Recommendation

        under construction

        """ 
        await ctx.send("under construction <a:mabeltyping:976601600476991509>")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(
        Memo(bot),
        guilds = [discord.Object(id = 413011798552477716)])