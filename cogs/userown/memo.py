import os
import sys
import datetime
import asyncpraw
import discord
from discord.ext import commands
import asyncio
import asyncprawcore
import re
import csv
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
from other.utils.utils import Utils as util



class MemoCheck():

    def backlog_enabled(ctx):
        conM = sqlite3.connect(f'databases/botsettings.db')
        curM = conM.cursor()
        memo_func_list = [item[0] for item in curM.execute("SELECT value FROM serversettings WHERE name = ?", ("backlog functionality",)).fetchall()]

        if len(memo_func_list) < 1:
            raise commands.CheckFailure("This functionality is turned off.")
            return False
        else:
            memo_func = memo_func_list[0].lower()
            if memo_func == "on":
                return True
            else:
                raise commands.CheckFailure("This functionality is turned off.")
                return False



class Memo(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.prefix = os.getenv("prefix")


    ########################################### FUNCTIONS ######################################################


    async def backlog(self, ctx, args):
        user, color, rest = await util.fetch_member_and_color(ctx, args)
        con = sqlite3.connect('databases/memobacklog.db')
        cur = con.cursor()

        catdisplay_list = ["catdisplay", "displaycat", "categorydisplay", "catsdisplay", "displaycats", "categoriesdisplay"]
        argument = util.cleantext2(''.join(args)).lower()
        display_cats = False
        for keyword in catdisplay_list:
            if keyword in argument:
                display_cats = True

        user_bl_list = [[item[0], item[1], item[2], item[3], item[4]] for item in cur.execute("SELECT bgid, userid, username, backlog, details FROM memobacklog WHERE userid = ? ORDER BY bgid", (str(user.id),)).fetchall()]

        name = util.cleantext2(user.display_name)
        header = f"**Backlog/Memo of {name}** ({len(user_bl_list)})"

        contents = [""]
        i = 0 #indexnumber
        k = 0 #pagenumber
        for bl_item in user_bl_list:
            i = i+1
            bl = bl_item[3]
            if len(bl) > 300:
                bl = bl_item[3][:297] + "..."
            if display_cats:
                cat = bl_item[4]
                msgpart = f"`{str(i)}`.  {bl} `[{cat}]`\n"
            else:
                msgpart = f"`{str(i)}`.  {bl}\n"
            
            previous = 0
            for j in range(0,k):
                previous += contents[j].count("\n")

            if len(contents[k]) + len(msgpart) <= 1500 and (i - previous) <= 15:    
                contents[k] = contents[k] + msgpart 
            else:
                k = k+1
                contents.append(msgpart)

        await util.embed_pages(ctx, self.bot, header, contents, color, None)



    async def backlog_index(self, ctx, args):
        user, color, rest_list = await util.fetch_member_and_color(ctx, args)
        con = sqlite3.connect('databases/memobacklog.db')
        cur = con.cursor()

        user_bl_list = [[item[0], item[1], item[2], item[3], item[4]] for item in cur.execute("SELECT bgid, userid, username, backlog, details FROM memobacklog WHERE userid = ? ORDER BY bgid", (str(user.id),)).fetchall()]

        name = util.cleantext2(user.display_name)
        indices = await util.get_all_integers(rest_list)
        indices_valid = [] # list of strings
        for i in indices:
            if i > 0 and i <= len(user_bl_list):
                indices_valid.append(str(i))
        indices_str = ', '.join(indices_valid)

        if len(indices_valid) == 0:
            if len(rest_list) > 1:
                await ctx.send("None of the provided indices are valid.")
            elif len(rest_list) == 1:
                await ctx.send("Provided index not valid.")
            else:
                await ctx.send("No index provided.")
            return

        elif len(indices_valid) == 1:
            header = f"**Memo of {name} at index: {indices_str}**"
        else:
            header = f"**Memo of {name} at indices: {indices_str}**"
            if len(header) > 256:
                n = len(f"**Memo of {name} at indices: **")
                header = len(f"**Memo of {name} at indices: {indices_str[:253-n]}...**")

        contents = []
        i = 0 #indexnumber
        for bl_item in user_bl_list:
            i = i+1
            if str(i) in indices_valid:
                bl = bl_item[3][:4000]
                cat = bl_item[4][:30].lower()
                if cat == "":
                    cat = "default"
                contents.append(f"`{str(i)}`.  {bl}\n`[category: {cat}]`")

        await util.embed_pages(ctx, self.bot, header, contents, color, None)



    async def backlog_add(self, ctx, args):
        now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())
        con = sqlite3.connect('databases/memobacklog.db')
        cur = con.cursor()
        user = ctx.message.author

        arguments = []
        for arg in args:
            arguments.append(util.cleantext2(arg))

        category = ""
        item_list = ' '.join(arguments).split(";")

        i = 0
        for item in item_list:
            # separate for bl item and category
            if item.strip().startswith("[") and  "]" in item:
                cat_item_split = item.strip().split("]",1)

                item = cat_item_split[1].strip()
                category = cat_item_split[0].strip().replace("[","").replace("]","").replace(" ","_")[:30]
                if category.lower() == "default":
                    category = ""
                if not util.valid_memo_category(category):
                    print(f"category {category} not valid, setting to default")
                    category = ""

            if item in ["", "-"]:
                item = "--------------------------"

            # add item to database
            i += 1

            mmid = str(now) + "_" + str(user.id) + "_" + str(i).zfill(4)

            # sanity check: if the exact backlog id already exists add an "x"
            bl_id_list = [item[0] for item in cur.execute("SELECT bgid, userid, username, backlog, details FROM memobacklog WHERE userid = ? ORDER BY bgid", (str(user.id),)).fetchall()]
            while mmid in bl_id_list:
                mmid = mmid + "x"

            cur.execute("INSERT INTO memobacklog VALUES (?, ?, ?, ?, ?)", (mmid, str(user.id), str(user.name), item, category))
            con.commit()

        await util.changetimeupdate()
        
        emoji = util.emoji("yay")
        if len(item_list) == 0:
            msg = f"Error: No item added to backlog."
        elif len(item_list) == 1:
            if len(item) > 1920:
                msg = f"Added `{item[:1917]}...` to backlog. {emoji}"
            else:
                msg = f"Added `{item}` to backlog. {emoji}"
        else:
            msg = f"Added `{i}` entries to backlog. {emoji}"
        await ctx.send(msg)



    async def backlog_delete(self, ctx, args):
        con = sqlite3.connect('databases/memobacklog.db')
        cur = con.cursor()
        user = ctx.message.author
        user_bl_list = [[item[0], item[1], item[2], item[3], item[4]] for item in cur.execute("SELECT bgid, userid, username, backlog, details FROM memobacklog WHERE userid = ? ORDER BY bgid", (str(user.id),)).fetchall()]

        if len(user_bl_list) == 0:
            await ctx.send("You don't have any items in your backlog/memo to delete!")
            return

        if len(args) == 0:
            await ctx.send("Command needs argument")
            return

        # 3 CASES: (LAST/TO/NORMAL)

        if args[0].lower() in ["last", "bottom"]: # CASE 1: delete from last item
            backlog_length = len(user_bl_list)

            deletion_number = 1
            if len(args) > 1:
                emoji = util.emoji("think_sceptic")
                try:
                    deletion_number = int(args[1])
                except:
                    deletion_number = 1 
                    await ctx.send(f'Argument error, must be integer. Only deleting last entry. {emoji}')
                if deletion_number < 1:
                    deletion_number = 1 
                    await ctx.send(f'Argument error, cannot be lower than 1. Only deleting last entry. {emoji}')
            
            if deletion_number >= backlog_length:
                emoji1 = util.emoji("shaking") 
                emoji2 = util.emoji("attention")
                await ctx.send(f"{emoji1} Are you sure you want to delete your entire backlog? {emoji2}\nI'm guessing this was unintentional... please use `-clearall` if it wasn't.")
                return 

            count = 0
            for i in range(backlog_length+1-deletion_number,backlog_length+1):
                entry = user_bl_list[i-1]
                entry_id = entry[0] 

                cur.execute("DELETE FROM memobacklog WHERE bgid = ?", (str(entry_id),))
                con.commit()
                count += 1

            if count == 0:
                #this should not happen
                await ctx.send(f'`something went wrong :(`')  
            elif count == 1:
                try:
                    entry_name = str(entry[3])
                except:
                    entry_name = "1 entry"

                await ctx.send(f'Deleted `{entry_name}` from your backlog!') 
            else:
                await ctx.send(f'Deleted `{count}` entries from your backlog!')

        else: # CASE 2 & 3
            
            if len(args) > 1: # CAST 2: TO
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
                            emoji = util.emoji("think_sceptic")
                            await ctx.send(f'Argument error. {emoji}') 
                            args = ()
                        else:
                            if end > len(user_bl_list):
                                end = len(user_bl_list)
                                await ctx.send(f'End marker larger than backlog size. Corrected marker.') 
                            args = range(start, end+1, 1)
                    else:
                        emoji = util.emoji("bot")
                        await ctx.send(f'Argument error. {emoji}\nDelete command with `to` arg needs exactly 3 arguments, e.g. `{self.prefix}del 4 to 9`.')
                        args = ()

            ### CASE 3
            n = 0 #number of valid arguments
            for arg in args:
                try:
                    i = int(arg)
                    if i == 0:
                        print('Error: Argument must be a non-zero integer!')
                except:
                    i = 0
                    print('Error: Argument must be an integer!')
                    break

                if i > 0:
                    if i <= len(user_bl_list):
                        n += 1
                        entry = user_bl_list[i-1]
                        entry_id = entry[0] 

                        cur.execute("DELETE FROM memobacklog WHERE bgid = ?", (str(entry_id),))
                        con.commit()
                        await util.changetimeupdate()
                    else:
                        print('error: index larger than backlog size')

                elif i < 0:
                    print('error: negative index')

            if n == 0:
                await ctx.send(f'Something went wrong :(')  
            elif n == 1:
                try:
                    entry_name = str(entry[3])
                except:
                    entry_name = "1 entry"

                await ctx.send(f'Deleted `{entry_name}` from your backlog!') 
            else:
                await ctx.send(f'Deleted `{n}` entries from your backlog!')



    async def backlog_edit(self, ctx, args):
        con = sqlite3.connect('databases/memobacklog.db')
        cur = con.cursor()
        user = ctx.message.author
        user_bl_list = [[item[0], item[1], item[2], item[3], item[4]] for item in cur.execute("SELECT bgid, userid, username, backlog, details FROM memobacklog WHERE userid = ? ORDER BY bgid", (str(user.id),)).fetchall()]

        if len(user_bl_list) == 0:
            await ctx.send("You don't have any items in your backlog/memo to delete!")
            return

        args2 = []
        for arg in args:
            args2.append(util.cleantext2(arg))

        if len(args2) == 0:
            await ctx.send(f'Missing argument')
            return

        if len(args2) == 1:
            args2.append("")

        if args2[0].lower() == "last":
            i = len(user_bl_list)
        else:
            try:
                i = int(args2[0])
                if i <= 0:
                    await ctx.send(f'Argument must be a positive integer!')
                    return
            except:
                i = 0
                await ctx.send(f'Argument must be an integer!')
                return

        if i > len(user_bl_list):
            await ctx.send(f'You do not have that many entries in your backlog.')
            return

        entry = user_bl_list[i-1]
        entry_id = entry[0] 

        oldbacklog = entry[3]
        newbacklog = ' '.join(args2[1:]).strip()

        if newbacklog == "-" or newbacklog == "":
            newbacklog = "--------------------------"

        if len(newbacklog) > 4000:
            newbacklog = newbacklog[:3997] + "..."

        cur.execute("UPDATE memobacklog SET backlog = ? WHERE bgid = ?", (newbacklog, entry_id))
        con.commit()
        await util.changetimeupdate()
        emoji = util.emoji("note")
        await ctx.send(f'Updated `{oldbacklog}` ➡️ `{newbacklog}` {emoji}!')



    async def backlog_clearall(self, ctx):
        con = sqlite3.connect('databases/memobacklog.db')
        cur = con.cursor()
        user = ctx.message.author
        user_bl_list = [[item[0], item[1], item[2], item[3], item[4]] for item in cur.execute("SELECT bgid, userid, username, backlog, details FROM memobacklog WHERE userid = ? ORDER BY bgid", (str(user.id),)).fetchall()]
        color = user.color 
        name = util.cleantext2(user.display_name)

        header = f"**Complete deletion of Backlog/Memo of {name}** ({len(user_bl_list)})"
        emoji = util.emoji("attention")
        text = f"Are you sure you want to clear all entries from your backlog/memo? {emoji}\n{str(len(user_bl_list))} items in total\n\n ✅ Yes, delete everything.\n ⛔ No, stop. Don't delete my backlog."

        response = await util.are_you_sure_embed(ctx, self.bot, header, text, color)

        if response.lower() != "true":
            await ctx.send("cancelled action")
            return

        cur.execute("DELETE FROM memobacklog WHERE userid = ?", (str(user.id),))
        con.commit()
        await util.changetimeupdate()
        emoji = util.emoji("unleashed")
        await ctx.send(f'Cleared entire backlog. {emoji}')



    async def backlog_suggest(self, ctx, args):
        con = sqlite3.connect('databases/memobacklog.db')
        cur = con.cursor()

        args2 = []
        for arg in args:
            is_mention = False
            if len(arg) > 3:
                if arg[0] == "<" and arg[1] == "@" and arg[-1] == ">":
                    is_mention = True 
            if not is_mention:
                args2.append(util.cleantext2(arg).replace("▪️"," "))

        given_string = " ".join(args2).split("|")
        bl_entries = given_string[0].strip().replace(";"," ;\n")

        msg = "**%s**" % bl_entries[:2000]
        if len(bl_entries) > 2000:
            msg += " [...]"

        msg += "\n▪️"

        if len(given_string) >= 1:
            additionalinfo = "|".join(given_string[1:]).strip()
            msg += f"\n{additionalinfo[:1500]}"
            if len(additionalinfo) > 1500:
                msg += " [...]"

        embed = discord.Embed(title="Recommendation", description=msg, color=0x30D5C8)
        footer = "React with 📝 to add it to your backlog."
        icon = "https://i.imgur.com/8IsAjV6.png"
        extra = ""
        embed.set_footer(text = footer)
        embed.set_thumbnail(url=icon)
        message = await the_channel.send(embed=embed)
        await message.add_reaction("📝")



    async def backlog_swap(self, ctx, args):
        if len(args) < 2:
            await ctx.send(f'Command needs at least 2 index arguments!')
            return 

        con = sqlite3.connect('databases/memobacklog.db')
        cur = con.cursor()
        user = ctx.message.author
        user_bl_list = [[item[0], item[1], item[2], item[3], item[4]] for item in cur.execute("SELECT bgid, userid, username, backlog, details FROM memobacklog WHERE userid = ? ORDER BY bgid", (str(user.id),)).fetchall()]
        L = len(user_bl_list) 

        if L < 2:
            await ctx.send(f'You do not have enough list items to perform a swap.')
            return

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
                newbacklog = user_bl_list[i-1][3]
                newcategory = user_bl_list[i-1][4]
                entry_id = user_bl_list[j-1][0]
                cur.execute("UPDATE memobacklog SET backlog = ?, details = ? WHERE bgid = ?", (newbacklog, newcategory, entry_id))
                con.commit()
                await util.changetimeupdate()
            await ctx.send(f'Swapped/rotated entries!')
        else:
            await ctx.send(f'Error: Arguments need to be integers between 1 and {L}')



    async def backlog_shift(self, ctx, args):
        con = sqlite3.connect('databases/memobacklog.db')
        cur = con.cursor()
        user = ctx.message.author

        user_bl_list = [[item[0], item[1], item[2], item[3], item[4]] for item in cur.execute("SELECT bgid, userid, username, backlog, details FROM memobacklog WHERE userid = ? ORDER BY bgid", (str(user.id),)).fetchall()]
        L = len(user_bl_list)

        # MAKE BASIC CHECKS FIRST

        if L >= 10000:
            await ctx.send(f'Error: IDing process not robust for backlogs with 10,000 or more entries.\nCancelled action.')
            await ctx.send(f'Please clear some of your backlog ffs')
            await ctx.send(f'smh my head')
            return 

        if L < 2:
            await ctx.send(f'Backlog too small for that.')
            return 

        if len(args) < 3:
            await ctx.send(f'Error: Command needs at least 1 item index and exactly 1 target index, separated by a `to`.\ne.g. `{self.prefix}shift 14 15 16 to 1`')
            return

        args2 = []
        for arg in args:
            arg2 = util.cleantext2(arg).lower()
            if arg2 != "":
                args2.append(arg2)

        itemindices = args2[:-2]
        separator = args2[-2]
        target = args2[-1]

        # CHECK ARGUMENTS ON VALIDITY
        
        if separator != "to":
            await ctx.send(f'Error: 2nd last arg needs to be `to`.')
            return

        if target == "top":
            target = "1"
        elif target == "bottom":
            target = str(L)
        
        try:
            t = int(target)
        except:
            await ctx.send(f'Error: Target index invalid (needs to be `top`, `bottom` or an integer between 1 and {L}).')
            return

        if len(itemindices) == 2 and itemindices[0] == "last" and util.represents_integer(itemindices[1]):
            itemindices = []
            try:
                last_n = int(itemindices[1])
            except:
                await ctx.send(f'Error with item indices.')
                return

            for i in range(last_n):
                itemindices.append(str(L-i))

        all_indices_integers = True
        valid_indices = []
        for i in itemindices:
            try:
                x = int(i)
                if x > 0 and x <= L:
                    valid_indices.append(x)
            except:
                all_indices_integers = False

        if not all_indices_integers:
            await ctx.send(f'Error: The item indices need to be all integers or `last x` (where x is an integer).')
            return

        valid_indices = list(dict.fromkeys(valid_indices))

        if len(valid_indices) == 0:
            await ctx.send(f'Error: No valid item indices.')
            return

        # SORT ITEMS

        bulk_size = len(itemindices)
        bulk = [] # bulk to shift
        for k in list(range(len(itemindices))):
            i = int(itemindices[int(k)])
            bulk.append(user_bl_list[i-1])

        if t == L:
            t = L + 1

        pre_b_items = []
        post_b_items = []
        for j in list(range(L)): #itemindices minus 1
            if str(j+1) not in itemindices: # not part of the bulk that's to be shifted
                if j+1 < t:
                    pre_b_items.append(user_bl_list[j])
                else:
                    post_b_items.append(user_bl_list[j])

        newly_ordered_bl_list = pre_b_items + bulk + post_b_items

        for l in list(range(L)):
            newbacklog = newly_ordered_bl_list[l][3]
            newcategory = newly_ordered_bl_list[l][4]
            entry_id = user_bl_list[l][0]
            cur.execute("UPDATE memobacklog SET backlog = ?, details = ? WHERE bgid = ?", (newbacklog, newcategory, entry_id))
            con.commit() 
        await util.changetimeupdate()
        await ctx.send(f'`Shifted {bulk_size} list item(s)!`')      



    async def backlog_insert(self, ctx, args):
        con = sqlite3.connect('databases/memobacklog.db')
        cur = con.cursor()
        user = ctx.message.author
        user_bl_list = [[item[0], item[1], item[2], item[3], item[4]] for item in cur.execute("SELECT bgid, userid, username, backlog, details FROM memobacklog WHERE userid = ? ORDER BY bgid", (str(user.id),)).fetchall()]
        L = len(user_bl_list)

        if len(args) < 1:
            await ctx.send(f'Error: Command needs arguments.') 
            return

        try:
            if args[0].lower() in ["bottom", "end", "last"]:
                index = L
            elif args[0].lower() in ["top", "start", "first"]:
                index = 1
            else:
                index = int(args[0])
            if index < 1 or index > L:
                await ctx.send(f'Error: 1st argument needs to be an integer between 1 and {L}.') 
                return
        except:
            await ctx.send(f'Error: 1st argument needs to be an integer.') 
            return

        # filter for bad chars and then divide by semicolons
        args2 = []
        for arg in args[1:]:
            args2.append(util.cleantext2(arg))
        arguments = ' '.join(args2).split(";")

        if len(arguments) >= 1:
            # separate for bl item and category
            items_and_categories = []
            bl_cat = ""
            for arg in arguments:
                arg0 = arg.strip()    
                if len(arg0) >= 2 and arg0[0] == "[" and "]" in arg0:
                    arg_split = arg0[1:].split("]",1)
                    bl_cat = arg_split[0].strip().replace(" ","_").replace("[","").replace("]","")
                    if bl_cat.lower() == "default":
                        bl_cat = ""
                    if not util.valid_memo_category(bl_cat):
                        print(f"category {bl_cat} not valid, setting to default")
                        bl_cat = ""
                    bl_item = arg_split[1].strip()
                else:
                    bl_item = arg
                items_and_categories.append([bl_item, bl_cat])
        else:
            items_and_categories = [["-",""]]

        #delete items with higher index
        for k in list(range(len(user_bl_list))):
            if k+1 < index:
                pass 
            else:
                entry = user_bl_list[k]
                entry_id = entry[0] 
                cur.execute("DELETE FROM memobacklog WHERE bgid = ?", (str(entry_id),))
                con.commit()

        #add new items
        i = 0
        for arg in items_and_categories:
            i = i+1
            bg = arg[0].strip()
            category = arg[1].strip()
            if bg == "-" or bg == "":
                bg = "--------------------------"
            if len(bg) > 4000:
                bg = bg[:3997] + "..."
            if len(category) > 30:
                category = category[:30]
            now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())
            mmid = str(now) + "_" + str(user.id) + "_" + str(i).zfill(4)
            cur.execute("INSERT INTO memobacklog VALUES (?, ?, ?, ?, ?)", (mmid, str(user.id), str(user.name), bg, category))
            con.commit()

        #readd old items
        for k in list(range(len(user_bl_list))):
            if k+1 < index:
                pass 
            else:
                entry = user_bl_list[k]
                entry_bg = entry[3] 
                old_cat = entry[4]
                now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())
                mmid = str(now) + "_" + str(user.id) + "_re_" + str(k+1).zfill(4)
                cur.execute("INSERT INTO memobacklog VALUES (?, ?, ?, ?, ?)", (mmid, str(user.id), str(user.name), entry_bg, old_cat))
                con.commit()
        await util.changetimeupdate()

        if i == 1:
            await ctx.send(f'Inserted `1` new entry into your backlog!')
        else:
            await ctx.send(f'Inserted `{i}` new entries into your backlog!')



    async def backlog_catedit(self, ctx, args):
        con = sqlite3.connect('databases/memobacklog.db')
        cur = con.cursor()
        user = ctx.message.author
        user_bl_list = [[item[0], item[1], item[2], item[3], item[4]] for item in cur.execute("SELECT bgid, userid, username, backlog, details FROM memobacklog WHERE userid = ? ORDER BY bgid", (str(user.id),)).fetchall()]

        if len(args) < 1:
            await ctx.send(f'Error: Command needs arguments.')
            return

        if len(args) == 1:
            index_args = [args[0]]
            category = ""
        else:
            index_args = []
            category_args = []
            reached_index_part = False

            # go backwards until first integer appears
            catlength = 0
            for arg in args[::-1]:
                arg2 = util.cleantext2(arg)
                if util.represents_integer(arg2) or arg2.lower() == "last":
                    reached_index_part = True
                
                if reached_index_part:
                    index_args.append(arg2) 
                else:
                    category_args.append(arg2)
                    catlength += 1

            index_args = index_args[::-1]
            if catlength == 0:
                category = ""
            else:
                category = '_'.join(category_args[::-1]).replace("[","").replace("]","").replace(" ","_")[:30]

        if len(index_args) == 0:
            await ctx.send(f'Error: Needs index arguments.')
            return

        if len(index_args) > 1 and index_args[1].lower() == "to":
            arguments_valid = False
            if len(index_args) != 3:
                emoji = util.emoji("bot")
                await ctx.send(f'Argument error {emoji}.')
                return
            try:
                start = int(index_args[0])
                end = int(index_args[2])
            except:
                await ctx.send(f'Error while trying to interpret the numbers around `to`-argument.')
                return

            if start > end:
                await ctx.send(f'Error with the start and end marker.')
                return

            if end > len(user_bl_list):
                end = len(user_bl_list)
                await ctx.send(f'End marker larger than backlog size. Corrected marker.') 
            args2 = range(start, end+1, 1)

        elif index_args[0].lower() == "last":
            if not len(index_args) in [1,2]:
                await ctx.send(f'Argument error.\nUse `{self.prefix}catedit last (optional integer) <category name>`') 
                return 

            if len(index_args) == 1:
                num = len(user_bl_list)
                args2 = [num]
            else:
                # first check if 2nd arg is integer
                try:
                    num = int(args[1])
                except:
                    await ctx.send(f'Invalid integer argument.') 
                    return
                
                # next check if integer is between 1 and bl-length
                bl_length = len(user_bl_list)
                
                if num < 1: 
                    await ctx.send(f"Integer must be at least 1.")
                    return
                elif num >= bl_length:
                    num = bl_length
                    await ctx.send(f"This will change category of ENTIRE backlog, but ok...")

                # at last put together list with the last n indices
                args2 = []
                for x in range(bl_length+1-num, bl_length+1):
                    args2.append(x)

        else:
            args2 = []
            for i in range(0, len(index_args)):
                try:
                    x = int(index_args[i])
                    if x <= 0 or x > len(user_bl_list):
                        await ctx.send(f'Argument must be a non-zero integer!')
                        return

                    args2.append(x)
                except:
                    await ctx.send(f'Arguments must be integer!')
                    return

        cat = category
        if category.lower() in ["default", ""]:
            category = ""
            cat = "default"
        if not util.valid_memo_category(category):
            await ctx.send(f"`{category}` is not a valid category.")
            return

        for arg in args2:
            i = int(arg)
            entry = user_bl_list[i-1]
            entry_id = entry[0]
            cur.execute("UPDATE memobacklog SET details = ? WHERE bgid = ?", (category[:30], entry_id))
            con.commit()
        await util.changetimeupdate()

        if len(args2) == 0:
            await ctx.send(f'Something went wrong :(')  
        elif len(args2) == 1:
            try:
                entry_name = str(entry[3])
            except:
                entry_name = "1 entry"

            await ctx.send(f'Changed category of {entry_name} to {cat}!') 
        else:
            await ctx.send(f'Changed category of {len(args2)} entries to {cat}!')



    async def backlog_catrename(self, ctx, args):
        con = sqlite3.connect('databases/memobacklog.db')
        cur = con.cursor()
        user = ctx.message.author
        user_bl_list = [[item[0], item[1], item[2], item[3], item[4]] for item in cur.execute("SELECT bgid, userid, username, backlog, details FROM memobacklog WHERE userid = ? ORDER BY bgid", (str(user.id),)).fetchall()]

        if len(args) < 2:
            await ctx.send(f'`Error: Command needs 2 category arguments.`')
        
        category_pre = args[0]

        if len(args) == 2:
            category_post = args[1][:30]
        else:
            category_post = '_'.join(args[1:])[:30]

        if category_pre.lower() == category_post.lower():
            emoji = util.emoji("hmm")
            await ctx.send(f"Aren't those categories kinda the same...? {emoji}")
            return

        if category_pre.lower() == "default":
            category_pre = ""
            category_pre_list = ["", "default"]
        else:
            category_pre_list = [category_pre.lower()]
        if category_post.lower() == "default":
            category_post = ""

        i = 0
        for item in user_bl_list:
            if item[4].lower() in category_pre_list:
                cur.execute("UPDATE memobacklog SET details = ? WHERE bgid = ?", (category_post, item[0]))
                con.commit()
                i += 1

        if i == 0:
            emoji = util.emoji("think_sceptic")
            await ctx.send(f'There is no item in your backlog with category {args[0].lower()[:100]} {emoji}')
        else:
            emoji = util.emoji("nice")
            await ctx.send(f'Changed category {args[0].lower()} to {args[1].lower()[:30]} {emoji}')



    async def clear_category(self, ctx, args):
        con = sqlite3.connect('databases/memobacklog.db')
        cur = con.cursor()
        user = ctx.message.author
        user_bl_list = [[item[0], item[1], item[2], item[3], item[4]] for item in cur.execute("SELECT bgid, userid, username, backlog, details FROM memobacklog WHERE userid = ? ORDER BY bgid", (str(user.id),)).fetchall()]
        color = user.color 
        name = util.cleantext2(user.display_name)

        if ' '.join(args).lower() == "all":
            cats_to_delete = ["ALL"]
            items_to_delete = user_bl_list

        else:
            cats_to_delete = []
            for arg in args:
                arg2 = util.cleantext2(arg.lower())
                if arg2 != "":
                    cats_to_delete.append(arg2)
                if arg2 == "default":
                    cats_to_delete.append("")

            items_to_delete = []
            for item in user_bl_list:
                if item[4].lower() in cats_to_delete:
                    items_to_delete.append(item)

        header = f"**Deletion of categories {','.join(cats_to_delete)} from {name}'s memo** ({len(items_to_delete)}/{len(user_bl_list)})"[:256]
        emoji = util.emoji("attention")
        text = f"Are you sure you want to clear these entries from your backlog/memo? {emoji}\n{str(len(items_to_delete))} items in total\n\n ✅ Yes, delete these.\n ⛔ No, stop. Don't delete that."

        response = await util.are_you_sure_embed(ctx, self.bot, header, text, color)

        if response.lower() != "true":
            await ctx.send("cancelled action")
            return

        for item in items_to_delete:
            item_id = item[0]
            cur.execute("DELETE FROM memobacklog WHERE userid = ? AND bgid = ?", (str(user.id),item_id))
        con.commit()
        await util.changetimeupdate()
        emoji = util.emoji("unleashed")
        cats_string = ', '.join(cats_to_delete)
        await ctx.send(f'Cleared categories {cats_string}. {emoji}\n({len(items_to_delete)} items)')



    async def backlog_search(self, ctx, args):
        display_cats = True #
        user, color, rest_list = await util.fetch_member_and_color(ctx, args)
        con = sqlite3.connect('databases/memobacklog.db')
        cur = con.cursor()
        user_bl_list = [[item[0], item[1], item[2], item[3], item[4]] for item in cur.execute("SELECT bgid, userid, username, backlog, details FROM memobacklog WHERE userid = ? ORDER BY bgid", (str(user.id),)).fetchall()]
        
        # fetch categories and potentially mention of other user
        searchterms = []
        other_user = False
        for arg in rest_list:
            term = ''.join(e for e in arg.lower() if e.isalnum())
            searchterms.append(term)
                    
        if len(searchterms) == 0:
            await ctx.send(f'Use command `{self.prefix}search` with searchterms to get a list of fitting items from your backlog.')
            return 

        # filter backlog for these searchterms
        user_bl_list_indexed = []
        for j in range(1, len(user_bl_list)+1):
            item = user_bl_list[j-1]
            indexed_item = item + [str(j)]

            add_item = True
            alphanum_filtered_item = ''.join(e for e in item[3].lower() if e.isalnum())

            for term in searchterms:
                if term in alphanum_filtered_item:
                    pass
                else:
                    add_item = False

            if add_item:
                user_bl_list_indexed.append(indexed_item)

        headerterms = ",".join(searchterms)
        header = f"**Backlog search [{headerterms}] of {util.cleantext2(str(user.display_name))}** ({str(len(user_bl_list_indexed))}/{str(len(user_bl_list))})"[:256]

        # prepare message sites
        cur_page = 1
        contents = [""]
        i = 0 #indexnumber
        k = 0 #pagenumber
        for bl_item in user_bl_list_indexed:
            i = i+1
            bl = bl_item[3]
            itemindex = bl_item[5]
            if len(bl) > 300:
                bl = bl_item[3][:297] + "..."
            if display_cats:
                cat = bl_item[4]
                msgpart = f"`{str(itemindex)}`.  {bl} `[{cat}]`\n"
            else:
                msgpart = f"`{str(itemindex)}`.  {bl}\n"
            
            previous = 0
            for j in range(0,k):
                previous += contents[j].count("\n")

            if len(contents[k]) + len(msgpart) <= 1500 and (i - previous) <= 15:    
                contents[k] = contents[k] + msgpart 
            else:
                k = k+1
                contents.append(msgpart)

        await util.embed_pages(ctx, self.bot, header, contents, color, None)



    async def backlog_showcats(self, ctx, args):
        user, color, rest_list = await util.fetch_member_and_color(ctx, args)
        con = sqlite3.connect('databases/memobacklog.db')
        cur = con.cursor()
        user_bl_list = [[item[0], item[1], item[2], item[3], item[4]] for item in cur.execute("SELECT bgid, userid, username, backlog, details FROM memobacklog WHERE userid = ? ORDER BY bgid", (str(user.id),)).fetchall()]
        argument = ' '.join(rest_list).strip().lower()

        cat_dict = {}
        for entry in user_bl_list:
            cat = entry[4].lower()
            if cat in cat_dict.keys():
                prev = cat_dict[cat]
                cat_dict[cat] = str(int(prev)+1)
            else:
                cat_dict[cat] = "1"

        cat_list = []
        if argument in ["reversed"]:
            for cat in reversed(sorted(cat_dict.keys())):
                if cat == "":
                    category = "default"
                else:
                    category = cat
                cat_list.append(category + "   (" + cat_dict[cat] + ")")
        else:
            for cat in sorted(cat_dict.keys()):
                if cat == "":
                    category = "default"
                else:
                    category = cat
                cat_list.append(category + "   (" + cat_dict[cat] + ")")

        contents = [""]
        i = 0 #indexnumber
        k = 0 #pagenumber
        for cat in cat_list:
            i += 1
            previous = 0
            for j in range(0,k):
                previous += contents[j].count("\n")

            if len(contents[k]) + len(cat) <= 1000 and (i - previous) <= 20:    
                contents[k] = contents[k] + "\n" + cat 
            else:
                k = k+1
                contents.append(cat)

        header = f"**Backlog categories of {util.cleantext2(str(user.display_name))}** ({str(len(cat_dict))})"[:256]
        footer = f"with {str(len(user_bl_list))} items in total"
        
        await util.embed_pages(ctx, self.bot, header[:256], contents, color, footer)
        #await util.multi_embed_message(ctx, header, cat_list, color, footer, None)



    async def backlog_categories(self, ctx, args):
        user, color, rest_list = await util.fetch_member_and_color(ctx, args)
        con = sqlite3.connect('databases/memobacklog.db')
        cur = con.cursor()
        user_bl_list = [[item[0], item[1], item[2], item[3], item[4]] for item in cur.execute("SELECT bgid, userid, username, backlog, details FROM memobacklog WHERE userid = ? ORDER BY bgid", (str(user.id),)).fetchall()]

        name = util.cleantext2(user.display_name)

        if len(rest_list) == 0:
            args2 = ["default"]
            header = f"**Backlog [default] of {name}** "
        elif len(rest_list) == 1:
            arg2 = util.cleantext2(rest_list[0].lower())
            if arg2 == "":
                arg2 = "default"
            args2 = [arg2]
            header = f"**Backlog [{arg2}] of {name}** "
        else:
            args2 = []
            for arg in rest_list:
                arg2 = util.cleantext2(arg.lower())
                if arg2 == "":
                    arg2 = "default"
                args2.append(arg2)
            header = f"**Backlog [{'/'.join(args2)}] of {name}** "

        contents = [""]
        i = 0 #indexnumber
        k = 0 #pagenumber
        catitem_counter = 0
        for bl_item in user_bl_list:
            i = i+1
            cat = bl_item[4]
            if cat.strip() == "":
                cat = "default"

            if cat.lower() in args2:
                catitem_counter += 1

                bl = bl_item[3]
                if len(bl) > 300:
                    bl = bl_item[3][:297] + "..."
                msgpart = f"`{str(i)}`.  {bl}\n"
                
                previous = 0
                for j in range(0,k):
                    previous += contents[j].count("\n")

                if len(contents[k]) + len(msgpart) <= 1500 and (catitem_counter - previous) <= 15:    
                    contents[k] = contents[k] + msgpart 
                else:
                    k = k+1
                    contents.append(msgpart)

        header += f"({catitem_counter}/{len(user_bl_list)})"
        await util.embed_pages(ctx, self.bot, header[:256], contents, color, None)



    async def backlog_without(self, ctx, args):
        user, color, rest_list = await util.fetch_member_and_color(ctx, args)
        con = sqlite3.connect('databases/memobacklog.db')
        cur = con.cursor()
        user_bl_list = [[item[0], item[1], item[2], item[3], item[4]] for item in cur.execute("SELECT bgid, userid, username, backlog, details FROM memobacklog WHERE userid = ? ORDER BY bgid", (str(user.id),)).fetchall()]

        name = util.cleantext2(user.display_name)

        if len(rest_list) == 0:
            args2 = ["default"]
            header = f"**Backlog without [default] of {name}** "
        elif len(rest_list) == 1:
            arg2 = util.cleantext2(rest_list[0].lower())
            if arg2 == "":
                arg2 = "default"
            args2 = [arg2]
            header = f"**Backlog without [{arg2}] of {name}** "
        else:
            args2 = []
            for arg in rest_list:
                arg2 = util.cleantext2(rest_list.lower())
                if arg2 == "":
                    arg2 = "default"
                args2.append(arg2)
            header = f"**Backlog without [{'/'.join(args2)}] of {name}** "

        contents = [""]
        i = 0 #indexnumber
        k = 0 #pagenumber
        catitem_counter = 0
        for bl_item in user_bl_list:
            i = i+1
            cat = bl_item[4]
            if cat == "":
                cat = "default"

            if cat.lower() not in args2:
                catitem_counter += 1

                bl = bl_item[3]
                if len(bl) > 300:
                    bl = bl_item[3][:297] + "..."
                msgpart = f"`{str(i)}`.  {bl}\n"
                
                previous = 0
                for j in range(0,k):
                    previous += contents[j].count("\n")

                if len(contents[k]) + len(msgpart) <= 1500 and (catitem_counter - previous) <= 15:    
                    contents[k] = contents[k] + msgpart 
                else:
                    k = k+1
                    contents.append(msgpart)

        header += f"({catitem_counter}/{len(user_bl_list)})"
        await util.embed_pages(ctx, self.bot, header[:256], contents, color, None)



    async def backlog_full(self, ctx):
        user, color, rest = await util.fetch_member_and_color(ctx, args)
        con = sqlite3.connect('databases/memobacklog.db')
        cur = con.cursor()

        catdisplay_list = ["catdisplay", "displaycat", "categorydisplay"]
        argument = util.cleantext2(''.join(rest_list)).lower()
        display_cats = False
        for keyword in catdisplay_list:
            if keyword in argument:
                display_cats = True

        user_bl_list = [[item[0], item[1], item[2], item[3], item[4]] for item in cur.execute("SELECT bgid, userid, username, backlog, details FROM memobacklog WHERE userid = ? ORDER BY bgid", (str(user.id),)).fetchall()]

        name = util.cleantext2(user.display_name)
        header = f"**Full memo of {name}** ({len(user_bl_list)})"

        lines = []
        i = 0 #indexnumber
        k = 0 #pagenumber
        for bl_item in user_bl_list:
            i = i+1
            bl = bl_item[3]
            if len(bl) > 300:
                bl = bl_item[3][:297] + "..."
            if display_cats:
                cat = bl_item[4]
                msgpart = f"`{str(i)}`.  {bl} `[{cat}]`\n"
            else:
                msgpart = f"`{str(i)}`.  {bl}\n"
            lines.append(msgpart)

        await util.multi_embed_message(ctx, header, text_list, color, "", None)






    # import/export functions

    async def add_element_to_backlog(self, user_id, user_name, newcat, newitem, i):
        now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())
        con = sqlite3.connect('databases/memobacklog.db')
        cur = con.cursor()

        compactitem_list = [util.alphanum(item[0],"lower") for item in cur.execute("SELECT backlog FROM memobacklog WHERE userid = ? ORDER BY bgid", (user_id,)).fetchall()]

        if util.alphanum(newitem,"lower") in compactitem_list:
            return False

        mmid = str(now) + "_" + user_id + "_" + str(i).zfill(4) + "_CSVimport"
        # sanity check: if the exact backlog id already exists add an "x"
        bl_id_list = [item[0] for item in cur.execute("SELECT bgid FROM memobacklog WHERE userid = ? ORDER BY bgid", (user_id,)).fetchall()]
        while mmid in bl_id_list:
            mmid = mmid + "x"

        cur.execute("INSERT INTO memobacklog VALUES (?, ?, ?, ?, ?)", (mmid, user_id, user_name, newitem, newcat))
        con.commit()

        await util.changetimeupdate()
        return True



    async def backlog_import(self, ctx, naive=True, overwrite=False, confirmation_skip=False):
        user_id = str(ctx.author.id)
        user_name = str(ctx.author.name)
        the_message = ctx.message
        if not the_message.attachments:
            await ctx.send("No attachment found.")
            return

        split_v1 = str(the_message.attachments).split("filename='")[1]
        filename = str(split_v1).split("' ")[0]


        if filename.endswith(".csv"): # Checks if it is a .csv file
            # SAVE CSV FILE
            await the_message.attachments[0].save(fp=f"temp/memo_import_{user_id}.csv")
            i = 0
            counter = 0
            continuing = True

            # OPEN FILE AND CHECK SIZE
            with open(f"temp/memo_import_{user_id}.csv", newline='') as csvfile:
                reader = csv.reader(csvfile, delimiter=";", quotechar='|')

                row_count = sum(1 for row in reader)
                if row_count > 2000:
                    await ctx.send("Error: File is too large for the backlog functionality.")
                    continuing = False

            # OPEN FILE AND ADD ITEMS
            with open(f"temp/memo_import_{user_id}.csv", newline='') as csvfile:
                reader = csv.reader(csvfile, delimiter=";", quotechar='|')
                # OVERWRITE?
                if overwrite and continuing:
                    if confirmation_skip:
                        response = True
                    else:
                        text = "Are you sure you want to overwrite your backlog?"
                        response = await util.are_you_sure_msg(ctx, self.bot, text)

                    if response == False:
                        continuing = False

                    else:
                        con = sqlite3.connect('databases/memobacklog.db')
                        cur = con.cursor()
                        cur.execute("DELETE FROM memobacklog WHERE userid = ?", (user_id,))
                        con.commit()
                        await ctx.send("cleared old backlog...")
                        await util.changetimeupdate()

                # PARSE AND WRITE INTO BACKLOG
                if continuing:
                    for row in reader:
                        if i == 0 and len(row) >= 2 and row[0] == "CATEGORY" and row[1] in ["ITEM", "A"]:
                            pass

                        else:
                            row_clean = []
                            for cell in row:
                                row_clean.append(util.cleantext2(cell.strip()))

                            i += 1
                            try:
                                if naive:
                                    if len(row_clean) > 1:
                                        cat = row_clean[0].strip().lower()[:30]
                                        item = row_clean[1].strip()
                                    else:
                                        cat = ""
                                        item = row_clean[0].strip()

                                else:
                                    if len(row_clean) > 3 and util.alphanum(row_clean[3]) != "":
                                        extrainfo = f" ({row_clean[3].strip()})"
                                    else:
                                        extrainfo = ""

                                    if len(row_clean) > 2 and util.alphanum(row_clean[2]) != "":
                                        second = f" - {row_clean[2].strip()}"
                                    else:
                                        second = ""

                                    if len(row_clean) > 1:
                                        first = row_clean[1].strip()
                                        cat = row_clean[0].strip().lower().replace(" ", "_")[:30]
                                    else:
                                        cat = ""
                                        first = row_clean[0].strip()

                                    item = f"{first}{second}{extrainfo}"

                                if cat == "default":
                                    cat = ""

                                if not util.valid_memo_category(cat):
                                    print("Import Error: invalid category name, set to default")
                                    cat = ""

                                did_add = await self.add_element_to_backlog(user_id, user_name, cat, item, i)
                                if did_add:
                                    counter += 1

                            except Exception as e:
                                print("Error with row in CSV file.", e)

                    await ctx.send(f"Added {counter} items to your backlog.")

            os.remove(f"{sys.path[0]}/temp/memo_import_{user_id}.csv")

        # TEXT FILE
        elif filename.endswith(".txt"):

            await the_message.attachments[0].save(fp=f"temp/memo_import_{user_id}.txt")
            i = 0
            counter = 0
            continuing = True

            # OPEN FILE AND CHECK SIZE
            with open(f'{sys.path[0]}/temp/memo_import_{user_id}.txt', 'r') as txtfile:
                row_count = sum(1 for line in txtfile)
                if row_count > 2000:
                    await ctx.send("Error: File is too large for the backlog functionality.")
                    continuing = False

            # OPEN FILE AND ADD ITEMS
            with open(f'{sys.path[0]}/temp/memo_import_{user_id}.txt', 'r') as txtfile:
                # OVERWRITE BL?
                if overwrite and continuing:
                    if confirmation_skip:
                        response = True
                    else:
                        text = "Are you sure you want to overwrite your backlog?"
                        response = await util.are_you_sure_msg(ctx, self.bot, text)

                    if response == False:
                        continuing = False

                    else:
                        con = sqlite3.connect('databases/memobacklog.db')
                        cur = con.cursor()
                        cur.execute("DELETE FROM memobacklog WHERE userid = ?", (user_id,))
                        con.commit()
                        await ctx.send("cleared old backlog...")
                        await util.changetimeupdate()

                # PARSE AND WRITE INTO BACKLOG
                if continuing:
                    for line in txtfile:
                        LL = line.split("\t")

                        if i == 0 and len(LL) >= 2 and LL[0] == "CATEGORY" and LL[1] in ["ITEM", "A"]:
                            pass

                        else:
                            i += 1

                            if naive:
                                if len(LL) > 1:
                                    cat = util.cleantext2(LL[0]).strip().lower()[:30]
                                    item = util.cleantext2(LL[1]).strip().lower()
                                else:
                                    cat = ""
                                    item = util.cleantext2(LL[0]).strip().lower()

                            else:
                                if len(LL) > 3 and util.alphanum(LL[3]) != "":
                                    extrainfo = f" ({util.cleantext2(LL[3]).strip()})"
                                else:
                                    extrainfo = ""

                                if len(LL) > 2 and util.alphanum(LL[2]) != "":
                                    second = f" - {util.cleantext2(LL[2]).strip()}"
                                else:
                                    second = ""

                                if len(LL) > 1:
                                    first = util.cleantext2(LL[1]).strip()
                                    cat = util.cleantext2(LL[0]).strip().lower().replace(" ", "_")[:30]
                                else:
                                    cat = ""
                                    first = util.cleantext2(LL[0]).strip()

                                item = f"{first}{second}{extrainfo}"

                            if cat == "default":
                                cat = ""

                            did_add = await self.add_element_to_backlog(user_id, user_name, cat, item, i)
                            if did_add:
                                counter += 1

                    await ctx.send(f"Added {counter} items to your backlog.")

            os.remove(f"{sys.path[0]}/temp/memo_import_{user_id}.txt")
        else:
            await ctx.send("Attachment must be a `.txt` or `.csv` file.\n(Make sure that your .txt file is TAB delimited or your .csv file is semicolon delimited.)")



    async def backlog_export(self, ctx, naive=False, sorting=True, header=True, fileformat="txt"):
        user_id = str(ctx.author.id)
        con = sqlite3.connect('databases/memobacklog.db')
        cur = con.cursor()
        bl_item_list = [[item[0].replace(";",",").lower().strip(),item[1].replace(";",",").strip()] for item in cur.execute("SELECT details, backlog FROM memobacklog WHERE userid = ? ORDER BY bgid", (user_id,)).fetchall()]
        
        if sorting:
            bl_item_list.sort(key=lambda x: x[1])
            bl_item_list.sort(key=lambda x: x[0])

        # IN CASE OF A CSV FILE
        if fileformat == "csv":
            with open(f"temp/memo_import_{user_id}.csv", 'w', newline='') as csvfile:
                writer = csv.writer(csvfile, delimiter=';', quotechar='|', quoting=csv.QUOTE_MINIMAL)

                if header:
                    if naive:
                        writer.writerow(["CATEGORY", "ITEM"])
                    else:
                        writer.writerow(["CATEGORY", "A", "B", "X"])

                for item in bl_item_list:
                    if naive:
                        cat = item[0].replace(";","")
                        entry = item[1].replace(";",",")
                        if cat == "":
                            cat = "default"
                        writer.writerow([cat,entry])
                    else:
                        if " - " in item[1]:
                            first = item[1].split(" - ",1)[0]
                            second = item[1].split(" - ",1)[1]
                            rest_can_be_found = 1
                        else:
                            first = item[1]
                            second = ""
                            rest_can_be_found = 0

                        parsed_item = [first,second]

                        if " (" in parsed_item[rest_can_be_found] and parsed_item[rest_can_be_found].endswith(")"):
                            rest = parsed_item[rest_can_be_found]
                            parsed_item[rest_can_be_found] = rest.split(" (",1)[0].strip()
                            parsed_item += [rest.split(" (",1)[1][:-1].strip()]

                        elif " [" in parsed_item[rest_can_be_found] and parsed_item[rest_can_be_found].endswith("]"):
                            rest = parsed_item[rest_can_be_found]
                            parsed_item[rest_can_be_found] = rest.split(" [",1)[0].strip()
                            parsed_item += [rest.split(" [",1)[1][:-1].strip()]

                        else:
                            parsed_item += [""]

                        cat = item[0]
                        if cat == "":
                            cat = "default"

                        writer.writerow([cat] + parsed_item)

            emoji = util.emoji("excited")
            textmessage = f"Here is your memo/backlog export as `;`-delimited `.csv`-file! {emoji}"
            await ctx.send(textmessage, file=discord.File(rf"temp/memo_import_{user_id}.csv"))
            os.remove(f"{sys.path[0]}/temp/memo_import_{user_id}.csv")

        # IN CASE OF A TXT FILE
        elif fileformat == "txt":
            with open(f"temp/memo_import_{user_id}.txt", 'w') as f:

                if header:
                    if naive:
                        f.write(f"CATEGORY\tITEM\n")
                    else:
                        f.write(f"CATEGORY\tA\tB\tX\n")
                
                for item in bl_item_list:
                    if naive:
                        cat = item[0].replace("\t","_")
                        entry = item[1].replace("\t"," ")
                        f.write(f"{cat}\t{entry}")
                    else:
                        if " - " in item[1]:
                            first = item[1].split(" - ",1)[0]
                            second = item[1].split(" - ",1)[1]
                            rest_can_be_found = 1
                        else:
                            first = item[1]
                            second = ""
                            rest_can_be_found = 0

                        parsed_item = [first,second]

                        if " (" in parsed_item[rest_can_be_found] and parsed_item[rest_can_be_found].endswith(")"):
                            rest = parsed_item[rest_can_be_found]
                            parsed_item[rest_can_be_found] = rest.split(" (",1)[0].strip()
                            parsed_item += [rest.split(" (",1)[1][:-1].strip()]

                        elif " [" in parsed_item[rest_can_be_found] and parsed_item[rest_can_be_found].endswith("]"):
                            rest = parsed_item[rest_can_be_found]
                            parsed_item[rest_can_be_found] = rest.split(" [",1)[0].strip()
                            parsed_item += [rest.split(" [",1)[1][:-1].strip()]

                        else:
                            parsed_item += [""]

                        cat = item[0]
                        if cat == "":
                            cat = "default"

                        f.write(f"{cat}\t{parsed_item[0]}\t{parsed_item[1]}\t{parsed_item[2]}\n")

            emoji = util.emoji("excited")
            textmessage = f"Here is your memo/backlog export as `tab`-delimited `.txt`-file! {emoji}"
            await ctx.send(textmessage, file=discord.File(rf"temp/memo_import_{user_id}.txt"))
            os.remove(f"{sys.path[0]}/temp/memo_import_{user_id}.txt")

        else:
            await ctx.send("Error: Unknown file format.")



    ###########################################################################################################
    ###########################################################################################################
    ###########################################################################################################



    ###########################################################################################################
    ########################################### COMMANDS ######################################################
    ###########################################################################################################











    @commands.group(name="bl", aliases = ["backlog", "memo"], pass_context=True, invoke_without_command=True)
    @commands.check(MemoCheck.backlog_enabled)
    @commands.check(util.is_active)
    async def _backlog(self, ctx, *args):
        """
        Show backlog

        Use command with @member mention to see other user's backlog.
        Use command with argument `displaycat` to display categories alongside items.
        """
        #`-bl`: Shows backlog
        #`-blc <name>`: Shows backlog of category <name>
        #`-blx <name>`: Shows backlog excluding category <name>
        #`-showcats`: Shows categories in your backlog

        #`-add`: Adds to backlog (with default category)
        #`-add [<name>]`: Adds to category <name> in backlog
        #`-del`: Removes from backlog
        #`-edit <index>`: Edits entry nr <index> in backlog
        #`-catedit <index> <name>`: Edits category of entry nr <index> to <name>
        #`-catrename <old name> <new name>`

        #important note: 
        #categories cannot have spaces!
        if len(args) == 0:
            args = ("",)
        await self.backlog(ctx, args)
    @_backlog.error
    async def backlog_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='index', aliases = ["i", "bli", "blindex", "indices", "indexes", "blindices", "blindexes"])
    @commands.check(MemoCheck.backlog_enabled)
    @commands.check(util.is_active)
    async def _index(self, ctx, *args):
        """Show item of index i

        use `-index <index number>`
        """
        if len(args) == 0:
            await ctx.send("Command needs argument.")
        else:
            await self.backlog_index(ctx, args)
    @_index.error
    async def index_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_backlog.command(name='index', aliases = ["i", "indices", "indexes"], pass_context=True)
    @commands.check(MemoCheck.backlog_enabled)
    @commands.check(util.is_active)
    async def _backlog_index(self, ctx, *args):
        """Show item of index i

        use `-index <index number>`
        """
        if len(args) == 0:
            await ctx.send("Command needs argument.")
        else:
            await self.backlog_index(ctx, args)
    @_backlog_index.error
    async def backlog_index_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='add', aliases = ["bladd"])
    @commands.check(MemoCheck.backlog_enabled)
    @commands.check(util.is_active)
    async def _add(self, ctx, *args):
        """Add item to backlog

        Adds an item to the bottom of your memo/backlog. You can add multiple entries seperated by a semi-colon ;
        
        You can specify a category for the items by writing `-add [<categoryname>] <item name>`. The categoryname needs to be the first argument and within brackets, no spaces or semicolons!
        """
        if len(args) == 0:
            args = ("",)
        await self.backlog_add(ctx, args)
    @_backlog.error
    async def backlog_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_backlog.command(name="add", pass_context=True)
    @commands.check(MemoCheck.backlog_enabled)
    @commands.check(util.is_active)
    async def _backlog_add(self, ctx, *args):
        """Add item to backlog

        Adds an item to the bottom of your memo/backlog. You can add multiple entries seperated by a semi-colon ;
        
        You can specify a category for the items by writing `-add [<categoryname>] <item name>`. The categoryname needs to be the first argument and within brackets, no spaces or semicolons!
        """
        if len(args) == 0:
            args = ("",)
        await self.backlog_add(ctx, args)
    @_backlog_add.error
    async def backlog_add_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='del', aliases = ['delete', 'bldel'])
    @commands.check(MemoCheck.backlog_enabled)
    @commands.check(util.is_active)
    async def _del(self, ctx, *args):
        """Delete from backlog

        Deletes an item of your memo/backlog at a given index number.

        You can do `-del 5` to delete the fifth entry of your backlog.
        Also possible is `-del 1 4 17 8` to delete several entries at once,
        or use `-del 5 to 9` to delete multiple entries in a row.

        Another option is to use `-del last` to delete the last entry, 
        or do `-del last 3` to delete the last 3 entries etc.
        """
        if len(args) == 0:
            await ctx.send("Command needs argument.")
        else:
            await self.backlog_delete(ctx, args)
    @_del.error
    async def del_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_backlog.command(name='del', aliases = ['delete'], pass_context=True)
    @commands.check(MemoCheck.backlog_enabled)
    @commands.check(util.is_active)
    async def _backlog_delete(self, ctx, *args):
        """Delete from backlog

        Deletes an item of your memo/backlog at a given index number.

        You can do `-del 5` to delete the fifth entry of your backlog.
        Also possible is `-del 1 4 17 8` to delete several entries at once,
        or use `-del 5 to 9` to delete multiple entries in a row.

        Another option is to use `-del last` to delete the last entry, 
        or do `-del last 3` to delete the last 3 entries etc.
        """
        if len(args) == 0:
            await ctx.send("Command needs index number argument.")
        else:
            await self.backlog_delete(ctx, args)
    @_backlog_delete.error
    async def backlog_delete_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='edit', aliases = ['ed', 'bled', 'bledit'])
    @commands.check(MemoCheck.backlog_enabled)
    @commands.check(util.is_active)
    async def _edit(self, ctx, *args):
        """Edit item in backlog

        Edits an item of your memo/backlog at a given index number.
        1st arg needs to be index number.
        Everything that follows will be the new item text.

        (Categories won't be touched. To edit category use `-catedit`)
        """
        if len(args) == 0:
            await ctx.send("Command needs arguments.")
        else:
            await self.backlog_edit(ctx, args)
    @_edit.error
    async def edit_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_backlog.command(name='edit', aliases = ['ed'], pass_context=True)
    @commands.check(MemoCheck.backlog_enabled)
    @commands.check(util.is_active)
    async def _backlog_edit(self, ctx, *args):
        """Edit item in backlog

        Edits an item of your memo/backlog at a given index number.
        1st arg needs to be index number.
        Everything that follows will be the new item text.

        (Categories won't be touched. To edit category use `-catedit`)
        """
        if len(args) == 0:
            await ctx.send("Command needs argument.")
        else:
            await self.backlog_edit(ctx, args)
    @_backlog_edit.error
    async def backlog_edit_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='clearall', aliases = ['deleteall'])
    @commands.check(MemoCheck.backlog_enabled)
    @commands.check(util.is_active)
    async def _clear(self, ctx, *args):
        """Clear entire backlog"""
        await self.backlog_clearall(ctx)
    @_clear.error
    async def clear_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_backlog.command(name='clearall', aliases = ['deleteall', 'blclearall', 'bldeleteall'], pass_context=True)
    @commands.check(MemoCheck.backlog_enabled)
    @commands.check(util.is_active)
    async def _backlog_clear(self, ctx, *args):
        """Clear entire backlog"""
        await self.backlog_clearall(ctx)
    @_backlog_clear.error
    async def backlog_clear_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='suggest', aliases = ['sug', 'rec', 'recommend', 'blrec', 'blsug', 'blsuggest'])
    @commands.check(MemoCheck.backlog_enabled)
    @commands.check(util.is_active)
    async def _suggest(self, ctx, *args):
        """Recommend a backlog item

        Makes a recommendation message. Reacting with 📝 adds it to the reacting users backlog. 
        Seperate multiple entries via a semicolon ; 
        Everything after a | symbol will not get added to the backlog, so use it for extra info.
        """
        if len(args) == 0:
            await ctx.send("Command needs argument.")
        else:
            await self.backlog_suggest(ctx, args)
    @_suggest.error
    async def suggest_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_backlog.command(name='suggest', aliases = ['sug', 'rec', 'recommend'], pass_context=True)
    @commands.check(MemoCheck.backlog_enabled)
    @commands.check(util.is_active)
    async def _backlog_suggest(self, ctx, *args):
        """Recommend a backlog item

        Makes a recommendation message. Reacting with 📝 adds it to the reacting users backlog. 
        Seperate multiple entries via a semicolon ; 
        Everything after a | symbol will not get added to the backlog, so use it for extra info.
        """
        if len(args) == 0:
            await ctx.send("Command needs argument.")
        else:
            await self.backlog_suggest(ctx, args)
    @_backlog_suggest.error
    async def backlog_suggest_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='swap', aliases = ['sw', 'blsw', 'blswap', 'rotate', 'blrotate'])
    @commands.check(MemoCheck.backlog_enabled)
    @commands.check(util.is_active)
    async def _swap(self, ctx, *args):
        """Swap backlog entries

        Swaps entries in your backlog. Use `-swap <index number> <index number>` to swap 2 entries.
        If you put more than 2 index numbers the entries will rotate in the given order.
        """
        if len(args) == 0:
            await ctx.send("Command needs argument.")
        else:
            await self.backlog_swap(ctx, args)
    @_swap.error
    async def swap_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_backlog.command(name='swap', aliases = ['sw', 'rotate'], pass_context=True)
    @commands.check(MemoCheck.backlog_enabled)
    @commands.check(util.is_active)
    async def _backlog_swap(self, ctx, *args):
        """Swap backlog entries

        Swaps entries in your backlog. Use `-swap <index number> <index number>` to swap 2 entries.
        If you put more than 2 index numbers the entries will rotate in the given order.
        """
        if len(args) == 0:
            await ctx.send("Command needs argument.")
        else:
            await self.backlog_swap(ctx, args)
    @_backlog_swap.error
    async def backlog_swap_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='shift', aliases = ['sh', 'blshift', 'blsh'])
    @commands.check(MemoCheck.backlog_enabled)
    @commands.check(util.is_active)
    async def _shift(self, ctx, *args):
        """Shift backlog entries

        Shifts entries in your backlog. Use `-shift <index 1> to <index 2>` to shift entry <i1> to position <i2>. You can also write `-shift <index 1> to top` or `-shift <index 1> to bottom`, or shift multiple entries with e.g.
        `-shift <i1> <i2> <i3> to <i4>`

        Detail:
        Every 'unshifted' item with an index < <i4> remains above the shifted items, while every 'unshifted' item with an index ≥ <i4> will end up below. If however <i4> is the largest index in your backlog or if you use 'bottom', then all 'unshifted' entries will be places above.
        """
        if len(args) == 0:
            await ctx.send("Command needs argument.")
        else:
            await self.backlog_shift(ctx, args)
    @_shift.error
    async def shift_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_backlog.command(name='shift', aliases = ['sh'], pass_context=True)
    @commands.check(MemoCheck.backlog_enabled)
    @commands.check(util.is_active)
    async def _backlog_shift(self, ctx, *args):
        """Shift backlog entries

        Shifts entries in your backlog. Use `-shift <index 1> to <index 2>` to shift entry <i1> to position <i2>. You can also write `-shift <index 1> to top` or `-shift <index 1> to bottom`, or shift multiple entries with e.g.
        `-shift <i1> <i2> <i3> to <i4>`

        Detail:
        Every 'unshifted' item with an index < <i4> remains above the shifted items, while every 'unshifted' item with an index ≥ <i4> will end up below. If however <i4> is the largest index in your backlog or if you use 'bottom', then all 'unshifted' entries will be places above.
        """
        if len(args) == 0:
            await ctx.send("Command needs argument.")
        else:
            await self.backlog_shift(ctx, args)
    @_backlog_shift.error
    async def backlog_shift_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='ins', aliases = ['insert', 'in', 'blin', 'blins', 'blinsert'])
    @commands.check(MemoCheck.backlog_enabled)
    @commands.check(util.is_active)
    async def _insert(self, ctx, *args):
        """Insert at index

        Adds an item to a given index of your memo/backlog. You can add multiple entries seperated by a semi-colon ;
        """
        if len(args) == 0:
            await ctx.send("Command needs argument.")
        else:
            await self.backlog_insert(ctx, args)
    @_insert.error
    async def insert_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_backlog.command(name='ins', aliases = ['insert', 'in'], pass_context=True)
    @commands.check(MemoCheck.backlog_enabled)
    @commands.check(util.is_active)
    async def _backlog_insert(self, ctx, *args):
        """Insert at index

        Adds an item to a given index of your memo/backlog. You can add multiple entries seperated by a semi-colon ;
        """
        if len(args) == 0:
            await ctx.send("Command needs argument.")
        else:
            await self.backlog_insert(ctx, args)
    @_backlog_insert.error
    async def backlog_insert_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='catedit', aliases = ["categoryedit", "editcat", "editcategory", 'blcatedit', 'bleditcat'])
    @commands.check(MemoCheck.backlog_enabled)
    @commands.check(util.is_active)
    async def _blcategoryedit(self, ctx, *args):
        """Edit categories of items

        write `-catedit <n1> <n2> .... <nk> <categoryname>`
        you can also use `-catedit <n1> to <n2> <categoryname>`
        or
        `-catedit last (optional integer i) <categoryname>` to edit the category of the last i-many entries
        """    
        if len(args) == 0:
            await ctx.send("Command needs argument.")
        else:
            await self.backlog_catedit(ctx, args)
    @_blcategoryedit.error
    async def blcategoryedit_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_backlog.command(name='catedit', aliases = ["categoryedit", "editcat", "editcategory"], pass_context=True)
    @commands.check(MemoCheck.backlog_enabled)
    @commands.check(util.is_active)
    async def _backlog_blcategoryedit(self, ctx, *args):
        """Edit categories of items

        write `-cat <n1> <n2> .... <nk> <categoryname>`
        you can also use `-cat <n1> to <n2> <categoryname>`
        or
        `-cat last (optional integer i) <categoryname>` to edit the category of the last i-many entries
        """    
        if len(args) == 0:
            await ctx.send("Command needs argument.")
        else:
            await self.backlog_catedit(ctx, args)
    @_backlog_blcategoryedit.error
    async def backlog_blcategoryedit_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='catrename', aliases = ["categoryrename", "catre", "renamecat", "renamecategory", 'blcatrename', 'blrenamecat'])
    @commands.check(MemoCheck.backlog_enabled)
    @commands.check(util.is_active)
    async def _categoryrename(self, ctx, *args):
        """Rename category

        first argument: old category name
        second argument: new category name
        """ 
        if len(args) == 0:
            await ctx.send("Command needs argument.")
        else:
            await self.backlog_catrename(ctx, args)
    @_categoryrename.error
    async def categoryrename_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_backlog.command(name='catrename', aliases = ["categoryrename", "catre", "renamecat", "renamecategory"], pass_context=True)
    @commands.check(MemoCheck.backlog_enabled)
    @commands.check(util.is_active)
    async def _backlog_categoryrename(self, ctx, *args):
        """Rename category

        first argument: old category name
        second argument: new category name
        """ 
        if len(args) == 0:
            await ctx.send("Command needs argument.")
        else:
            await self.backlog_catrename(ctx, args)
    @_backlog_categoryrename.error
    async def backlog_categoryrename_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='clearcat', aliases = ["deletecat", "removecat", "clearcategory", "deletecategory", "removecategory", "delcat", "bldelcat", "blclearcat", "bldeletecat", "blremovecat"])
    @commands.check(MemoCheck.backlog_enabled)
    @commands.check(util.is_active)
    async def _clearcat(self, ctx, *args):
        """Clear your backlog of all entries of given category

        use i.e. `-clearcat <categoryname>`
        """ 
        if len(args) == 0:
            await ctx.send("Command needs argument.")
        else:
            await self.clear_category(ctx, args)
    @_clearcat.error
    async def clearcat_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_backlog.command(name='clearcat', aliases = ["deletecat", "removecat", "clearcategory", "deletecategory", "removecategory", "delcat", "clear"], pass_context=True)
    @commands.check(MemoCheck.backlog_enabled)
    @commands.check(util.is_active)
    async def _backlog_clearcat(self, ctx, *args):
        """Clear your backlog of all entries of given category

        use i.e. `-clearcat <categoryname>`
        """ 
        if len(args) == 0:
            await ctx.send("Command needs argument.")
        else:
            await self.clear_category(ctx, args)
    @_backlog_clearcat.error
    async def backlog_clearcat_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='search', aliases = ["blsearch", "match", "blmatch"])
    @commands.check(MemoCheck.backlog_enabled)
    @commands.check(util.is_active)
    async def _blsearch(self, ctx, *args):
        """Search backlog
        
        use `-search <search term>` to find all backlog entries matching that term
        """    
        if len(args) == 0:
            await ctx.send("Command needs argument.")
        else:
            await self.backlog_search(ctx, args)
    @_blsearch.error
    async def blsearch_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_backlog.command(name='search', aliases = ["match"], pass_context=True)
    @commands.check(MemoCheck.backlog_enabled)
    @commands.check(util.is_active)
    async def _backlog_blsearch(self, ctx, *args):
        """Search backlog
        
        use `-search <search term>` to find all backlog entries matching that term
        """    
        if len(args) == 0:
            await ctx.send("Command needs argument.")
        else:
            await self.backlog_search(ctx, args)
    @_backlog_blsearch.error
    async def backlog_blsearch_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='showcats', aliases = ["sc", "showc", "showcat", "catlist", "catslist", 'blshowcats', 'blsc'])
    @commands.check(MemoCheck.backlog_enabled)
    async def _showcategories(self, ctx, *args):
        """Show categories
        
        by mentioning another user you can display the categories of them, the mention has to be the 1st argument though.
        """   
        if len(args) == 0:
            args = ("normal",)
        await self.backlog_showcats(ctx, args)
    @_showcategories.error
    async def showcategories_error(self, ctx, error):
        await util.error_handling(ctx, error) 



    @_backlog.command(name='showcats', aliases = ["sc", "showc", "showcat", "catlist", "catslist"], pass_context=True)
    @commands.check(MemoCheck.backlog_enabled)
    async def _backlog_showcategories(self, ctx, *args):
        """Show categories
        
        by mentioning another user you can display the categories of them, the mention has to be the 1st argument though.
        """   
        if len(args) == 0:
            args = ("normal",)
        await self.backlog_showcats(ctx, args)
    @_backlog_showcategories.error
    async def backlog_showcategories_error(self, ctx, error):
        await util.error_handling(ctx, error) 



    @commands.group(name='blc', aliases = ["backlogcat", "backlogcats", "backlogcategory", "blcat", "blcats"], pass_context=True, invoke_without_command=True)
    @commands.check(MemoCheck.backlog_enabled)
    @commands.check(util.is_active)
    async def _backlogcategories(self, ctx, *args):
        """backlog, but only for given categories

        Shows your memo list / backlog filtered by a given category.
        Use `-blc <categoryname>`
        or
        `-blc <@user mention> <categoryname>`
        for other users backlog.
        Note that categories cannot have spaces.
        """   
        if len(args) == 0:
            args = ("default",) 
        await self.backlog_categories(ctx, args)
    @_backlogcategories.error
    async def backlogcategories_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_backlog.command(name='c', aliases = ["category", "cat", "cats"], pass_context=True)
    @commands.check(MemoCheck.backlog_enabled)
    @commands.check(util.is_active)
    async def _backlog_backlogcategories(self, ctx, *args):
        """backlog, but only for given categories

        Shows your memo list / backlog filtered by a given category.
        Use `-blc <categoryname>`
        or
        `-blc <@user mention> <categoryname>`
        for other users backlog.
        Note that categories cannot have spaces.
        """    
        if len(args) == 0:
            args = ("default",) 
        await self.backlog_categories(ctx, args)
    @_backlog_backlogcategories.error
    async def backlog_backlogcategories_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.group(name='blx', aliases = ["backlogwithout"], pass_context=True, invoke_without_command=True)
    @commands.check(MemoCheck.backlog_enabled)
    @commands.check(util.is_active)
    async def _backlogwithoutcategories(self, ctx, *args):
        """backlog without given categories

        specify the categories that you don't want to have displayed
        """
        if len(args) == 0:
            args = ("default",) 
        await self.backlog_without(ctx, args)
    @_backlogwithoutcategories.error
    async def backlogwithoutcategories_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_backlog.command(name='x', aliases = ["without"], pass_context=True)
    @commands.check(MemoCheck.backlog_enabled)
    @commands.check(util.is_active)
    async def _backlog_backlogwithoutcategories(self, ctx, *args):
        """backlog without given categories

        specify the categories that you don't want to have displayed
        """
        if len(args) == 0:
            args = ("default",) 
        await self.backlog_without(ctx, args)
    @_backlog_backlogwithoutcategories.error
    async def backlog_backlogwithoutcategories_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='blf', aliases = ["backlogfull", "memofull", "blfull"])
    @commands.check(MemoCheck.backlog_enabled)
    @commands.check(util.is_active)
    async def _backlogfull(self, ctx, *args):
        """Shows entire backlog in one page"""
        await self.backlog_full(ctx)
    @_backlogfull.error
    async def backlogfull_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_backlog.command(name='f', aliases = ["full"], pass_context=True)
    @commands.check(MemoCheck.backlog_enabled)
    @commands.check(util.is_active)
    async def _backlog_backlogfull(self, ctx, *args):
        """Shows entire backlog in one page"""
        await self.backlog_full(ctx)
    @_backlog_backlogfull.error
    async def backlog_backlogfull_error(self, ctx, error):
        await util.error_handling(ctx, error)



    # IMPORT/EXPORT COMMANDS (with .txt/.csv files)



    def parse_import(self, args):
        naive = False
        sorting = True
        header = True
        overwrite = False
        confirmation_skip = False
        fileformat = "txt"

        if len(args) > 0:
            simple_list = ["simple", "naive"]
            overwrite_list = ["overwrite", "override", "overrule"]
            confirmation_skip_list = ["-y", "auto", "automatic", "-yes"]
            unsorting_list = ["unsorted", "raw", "unsort", "unsorting", "nonsort", "nosort"]
            noheader_list = ["noheader", "notitle", "headerless", "titleless"]

            for arg in args:
                if arg.lower() in simple_list:
                    naive = True
                if arg.lower() in unsorting_list:
                    sorting = False
                if arg.lower() in noheader_list:
                    header = False
                if arg.lower() in overwrite_list:
                    overwrite = True
                if arg.lower() in confirmation_skip_list:
                    confirmation_skip = True

                if arg.lower() == "txt":
                    fileformat = "txt"
                elif arg.lower() == "csv":
                    fileformat = "csv"

        return naive, sorting, header, overwrite, confirmation_skip, fileformat



    @commands.command(name='blim', aliases = ["blimport", "memoimport", "blfileimport", "memofileimport"])
    @commands.check(MemoCheck.backlog_enabled)
    @commands.check(util.is_active)
    async def _backlogimport(self, ctx, *args):
        """Imports backlog from .txt or .csv file

        Column 1 has to be the category while column 2 should be the backlog item.
        You can divide the backlog item into 3 parts, and it will be displayed as
        `column1 entry - column2 entry (column3 entry)`

        You can specify argument `override` to clear your existing backlog and replace it with the uploaded information.
        Use `override -y` to skip the confirmation.

        Note: .txt files need to be TAB delimited, while .csv files need to be semicolon delimited.
        """

        naive, sorting, header, overwrite, confirmation_skip, fileformat = self.parse_import(args)
        await self.backlog_import(ctx, naive, overwrite, confirmation_skip)

    @_backlogimport.error
    async def backlogimport_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_backlog.command(name='import', aliases = ["fileimport"], pass_context=True)
    @commands.check(MemoCheck.backlog_enabled)
    @commands.check(util.is_active)
    async def _backlog_backlogimport(self, ctx, *args):
        """Imports backlog from .csv file

        Column 1 has to be the category while column 2 should be the backlog item.
        You can divide the backlog item into 3 parts, and it will be displayed as
        `column1 entry - column2 entry (column3 entry)`

        You can specify argument `override` to clear your existing backlog and replace it with the uploaded information.
        Use `override -y` to skip the confirmation.

        Note: .txt files need to be TAB delimited, while .csv files need to be semicolon delimited.
        """

        naive, sorting, header, overwrite, confirmation_skip, fileformat = self.parse_import(args)
        await self.backlog_import(ctx, naive, overwrite, confirmation_skip)

    @_backlog_backlogimport.error
    async def backlog_backlogimport_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='blex', aliases = ["blexport", "memoexport", "blfileexport", "memofileexport"])
    @commands.check(MemoCheck.backlog_enabled)
    @commands.check(util.is_active)
    async def _backlogexport(self, ctx, *args):
        """Exports backlog as .txt or .csv file

        Use with arg `simple` to put backlog category in column 1 and backlog item as a whole in column 2.
        Use without to backlog category in column 1 and the backlog item will be parsed into column 2 (artist), 3 (album) and 4 (other info) by utilising ` - ` as separation of text that goes into column 2 and 3, and column 4 gets text parts that are wrapped in parenthese or brackets at the end. 
        i.e. `artist name - album name (other info)`

        Other arguments:
        `headerless`: gives export without a header row
        `unsorted`: does not sort data

        Per default the export will be a TAB-delimited .txt file, by specifying `csv` in the arguments you can get a semicolon delimited .csv file as well.
        """

        naive, sorting, header, overwrite, confirmation_skip, fileformat = self.parse_import(args)
        await self.backlog_export(ctx, naive, sorting, header, fileformat)

    @_backlogexport.error
    async def backlogexport_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_backlog.command(name='export', aliases = ["fileexport"], pass_context=True)
    @commands.check(MemoCheck.backlog_enabled)
    @commands.check(util.is_active)
    async def _backlog_backlogexport(self, ctx, *args):
        """Exports backlog as .csv file

        Use with arg `simple` to put backlog category in column 1 and backlog item as a whole in column 2.
        Use without to backlog category in column 1 and the backlog item will be parsed into column 2 (artist), 3 (album) and 4 (other info) by utilising ` - ` as separation of text that goes into column 2 and 3, and column 4 gets text parts that are wrapped in parenthese or brackets at the end. 
        i.e. `artist name - album name (other info)`

        Other arguments:
        `headerless`: gives export without a header row
        `unsorted`: does not sort data

        Per default the export will be a TAB-delimited .txt file, by specifying `csv` in the arguments you can get a semicolon delimited .csv file as well.
        """

        naive, sorting, header, overwrite, confirmation_skip, fileformat = self.parse_import(args)
        await self.backlog_export(ctx, naive, sorting, header, fileformat)

    @_backlog_backlogexport.error
    async def backlog_backlogexport_error(self, ctx, error):
        await util.error_handling(ctx, error)



    # RANDOM COMMANDS



    @commands.command(name='blr', aliases = ["blroll", "blrandom", "blrand"])
    @commands.check(MemoCheck.backlog_enabled)
    @commands.check(util.is_active)
    async def _backlograndom(self, ctx, *args):
        """Gives random entry from backlog

        By using `-blr <category name>` you can roll a random item from given category.
        You can also give multiple category arguments.

        Use `except` as 1st argument to exclude the following categories."""
        user, color, rest_list = await util.fetch_member_and_color(ctx, args)
        cat_list = []

        if len(rest_list) == 0:
            cat_type = "all"

        else:
            if rest_list[0].lower() == "except":
                cat_type = "blx"
                if len(rest_list) == 1:
                    cat_list.append("default")
                else:
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
    @_backlograndom.error
    async def backlograndom_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_backlog.command(name='roll', aliases = ["r", "random", "rand"], pass_context=True)
    @commands.check(MemoCheck.backlog_enabled)
    @commands.check(util.is_active)
    async def _backlog_backlograndom(self, ctx, *args):
        """Gives random entry from backlog

        By using `-blr <category name>` you can roll a random item from given category.
        You can also give multiple category arguments.

        Use `except` as 1st argument to exclude the following categories."""
        user, color, rest_list = await util.fetch_member_and_color(ctx, args)
        cat_list = []

        if len(rest_list) == 0:
            cat_type = "all"

        else:
            if rest_list[0].lower() == "except":
                cat_type = "blx"
                if len(rest_list) == 1:
                    cat_list.append("default")
                else:
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
    @_backlog_backlograndom.error
    async def backlog_backlograndom_error(self, ctx, error):
        await util.error_handling(ctx, error)


    
    @_backlogcategories.command(name='roll', aliases = ["r", "random", "rand"], pass_context=True)
    @commands.check(MemoCheck.backlog_enabled)
    @commands.check(util.is_active)
    async def _backlogcategories_backlograndom(self, ctx, *args):
        """Gives random entry from backlog of given categories"""
        user, color, rest_list = await util.fetch_member_and_color(ctx, args)
        cat_list = []
        cat_type = "blc"
        if len(rest_list) == 0:
            cat_list.append("default")
        for arg in rest_list:
            arg2 = util.cleantext2(arg.lower())
            if arg2 == "":
                arg2 = "default"
            cat_list.append(arg2)

        await util.backlog_roll(ctx, user, cat_type, cat_list)
    @_backlogcategories_backlograndom.error
    async def backlogcategories_backlograndom_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_backlogwithoutcategories.command(name='roll', aliases = ["r", "random", "rand"], pass_context=True)
    @commands.check(MemoCheck.backlog_enabled)
    @commands.check(util.is_active)
    async def _backlogwithoutcategories_backlograndom(self, ctx, *args):
        """Gives random entry from backlog except given categories"""
        user, color, rest_list = await util.fetch_member_and_color(ctx, args)
        cat_list = []
        cat_type = "blx"
        if len(rest_list) == 0:
            cat_list.append("default")
        for arg in rest_list:
            arg2 = util.cleantext2(arg.lower())
            if arg2 == "":
                arg2 = "default"
            cat_list.append(arg2)

        await util.backlog_roll(ctx, user, cat_type, cat_list)
    @_backlogwithoutcategories_backlograndom.error
    async def backlogwithoutcategories_backlograndom_error(self, ctx, error):
        await util.error_handling(ctx, error)





async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(
        Memo(bot),
        guilds = [discord.Object(id = int(os.getenv("guild_id")))])