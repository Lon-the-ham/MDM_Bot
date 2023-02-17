import os
import datetime
import discord
from discord.ext import commands
import sqlite3



class ReactionEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        valid_servers = [413011798552477716]
        server_id = payload.guild_id
        if server_id in valid_servers:
            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            react = payload.emoji.name
            user = payload.member

            role_channel = self.bot.get_channel(966276028630728744)
            if channel.id != role_channel.id:
                if str(message.author.id) == '958105284759400559':
                    if str(user.id) != '958105284759400559':
                        if message.embeds:   #check if list is not empty
                            embed = message.embeds[0]
                            if 'recommendation' in str(embed.title).lower():
                                if react == "📝":
                                    testprint = "detected 📝 react by %s" % user.name
                                    print(testprint)
                                    
                                    conbg = sqlite3.connect('cogs/backlog/memobacklog.db') 
                                    curbg = conbg.cursor()
                                    curbg.execute('''CREATE TABLE IF NOT EXISTS memobacklog (bgid text, userid text, username text, backlog text, details text)''')
                                    
                                    now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())
                                    bl_entries = [x.strip() for x in (str(embed.description).split("▪️")[0].replace("*", " ").strip()).split(";") if x.strip()] #the x for x if x should remove all empty strings
                                    i=1000
                                    for bl_entry in bl_entries:
                                        mmid = str(now) + "_" + str(user.id) + "_0rec" + str(i)
                                        print(f"adding entry {i - 999} to backlog")
                                        curbg.execute("INSERT INTO memobacklog VALUES (?, ?, ?, ?, ?)", (mmid, str(user.id), str(user.name), bl_entry, ""))
                                        conbg.commit()
                                        i += 1

                                    footer = str(embed.footer.text)
                                    newfooter = footer + "\n-added to " + str(user.display_name) + "'s backlog"
                                    embed.set_footer(text = newfooter)
                                    #embed.set_thumbnail(url=icon)
                                    await message.edit(embed=embed)


                            if 'pingterest: ' in str(embed.title).lower():
                                pi_name = str(embed.title).lower().split("pingterest: ")[-1]
                                
                                if react == "✅":
                                    conpi = sqlite3.connect('cogs/pingterest/pingterest.db')
                                    curpi = conpi.cursor()
                                    curpi.execute('''CREATE TABLE IF NOT EXISTS pingterests (pingterest text, userid text, username text, details text)''')

                                    pi_list = [[item[0], item[1], item[2], item[3]] for item in curpi.execute("SELECT pingterest, userid, username, details FROM pingterests WHERE pingterest = ? AND details = ?", (pi_name, "template")).fetchall()]

                                    if len(pi_list) == 0:
                                        print("error: pingterest does not exist")
                                    else:
                                        pi_user = [[item[0], item[1], item[2], item[3]] for item in curpi.execute("SELECT pingterest, userid, username, details FROM pingterests WHERE pingterest = ? AND userid = ?", (pi_name, str(user.id))).fetchall()]
                                        if len(pi_user) == 0:
                                            print("pingterest: %s (user joining)" % pi_name)
                                            curpi.execute("INSERT INTO pingterests VALUES (?, ?, ?, ?)", (pi_name, str(user.id), str(user.name), ""))
                                            conpi.commit()
                                            print("successfully joined pingterest")
                                        else:
                                            print("pingterest: %s (already joined)" % pi_name)
                                elif react == "🚫":
                                        conpi = sqlite3.connect('pingterest.db')
                                        curpi = conpi.cursor()
                                        curpi.execute('''CREATE TABLE IF NOT EXISTS pingterests (pingterest text, userid text, username text, details text)''')

                                        pi_list = [[item[0], item[1], item[2], item[3]] for item in curpi.execute("SELECT pingterest, userid, username, details FROM pingterests WHERE pingterest = ? AND details = ?", (pi_name, "template")).fetchall()]

                                        if len(pi_list) == 0:
                                            print("error: pingterest does not exist")
                                        else:
                                            pi_user = [[item[0], item[1], item[2], item[3]] for item in curpi.execute("SELECT pingterest, userid, username, details FROM pingterests WHERE pingterest = ? AND userid = ?", (pi_name, str(user.id))).fetchall()]
                                            if len(pi_user) != 0:
                                                print("pingterest: %s (user joined)" % pi_name)
                                                curpi.execute("DELETE FROM pingterests WHERE pingterest = ? AND userid = ?", (pi_name, str(user.id)))
                                                conpi.commit()
                                                print("successfully left pingterest")
                                            else:
                                                print("pingterest: %s (not joined)" % pi_name)


    


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(
        ReactionEvents(bot),
        guilds = [discord.Object(id = 413011798552477716)])