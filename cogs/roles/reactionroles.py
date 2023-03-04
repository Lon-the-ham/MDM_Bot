import os
import datetime
import discord
from discord.ext import commands
import sqlite3



class RoleEvents(commands.Cog):
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
                pass 
            elif str(user.id) == '958105284759400559':
                print('bot reacted itself')
            else:
                guild = self.bot.get_guild(payload.guild_id)
                all_roles = [r for r in guild.roles]
                con = sqlite3.connect('cogs/roles/roles.db')
                cur = con.cursor()
                color_roles = [[item[0], item[1], item[2]] for item in cur.execute("SELECT id, name, details FROM roles WHERE category = ?", ("color",)).fetchall()]
                pronoun_roles = [[item[0], item[1], item[2]] for item in cur.execute("SELECT id, name, details FROM roles WHERE category = ?", ("pronoun",)).fetchall()]
                other_roles = [[item[0], item[1], item[2]] for item in cur.execute("SELECT id, name, details FROM roles WHERE category = ?", ("music",)).fetchall()]

                if message.embeds:   #check if list is not empty
                    embed = message.embeds[0]
                    if (('color' in str(embed.title).lower()) or ('colour' in str(embed.title).lower())):
                        accepted_reacts = True
                        valid_emojis_list = []
                        for col in color_roles:
                            valid_emojis_list.append(col[2])

                        if react in valid_emojis_list:
                            for c_role in color_roles:
                                if react == c_role[2]:
                                    set_color = c_role[1]
                                    break
                        #if react == "🐳":
                        #    set_color = "Blue"
                        #elif react == "🫐":
                        #    set_color = "Dark Blue"
                        #elif react == "❄️":
                        #    set_color = "Teal"
                        #elif react == "🦚":
                        #    set_color = "Turkiz"
                        #elif react == "🌺":
                        #    set_color = "Rose"
                        #elif react == "🐷":
                        #    set_color = "Pink"
                        #elif react == "🍇":
                        #    set_color = "Violet"
                        #elif react == "🦀":
                        #    set_color = "Red"
                        #elif react == "🍊":
                        #    set_color = "Orange"
                        #elif react == "🥑":
                        #    set_color = "Green"
                        #elif react == "🎍":
                        #    set_color = "Lightgreen"
                        #elif react == "✨":
                        #    set_color = "Yellow"
                        #elif react == "🙊":
                        #    set_color = "Beige"
                        #elif react == "🐑":
                        #    set_color = "White"
                        #elif react == "🏴‍☠️":
                        #    set_color = "Black"
                        #
                        #elif react == "🚫":
                        #    set_color = ""
                        else:
                            set_color = ""
                            accepted_reacts = False

                        if accepted_reacts:
                            if set_color != "":
                                try:
                                    the_role = discord.utils.get(user.guild.roles, name=set_color)
                                    await user.add_roles(the_role)
                                    print("Added role: %s" % set_color)
                                except:
                                    print("some error occured while trying to assign a role")
                            else:
                                print("removing all color roles")

                            other_color_roles = [[item[0], item[1]] for item in cur.execute("SELECT name, id FROM roles WHERE category = ? AND permissions = ? AND name != ?", ('color','', set_color)).fetchall()]

                            for other_color in other_color_roles:
                                for role in all_roles:
                                    if other_color[1] == str(role.id):
                                        if role in user.roles:
                                            await user.remove_roles(role)
                                            print("Removed role: %s" % role.name)
                                        else:
                                            print("Did not have role: %s" % role.name)
                        else:
                            await message.remove_reaction(payload.emoji, user)
                            print("non accepted react detected")

                    elif ('pronoun' in str(embed.title).lower()):
                        accepted_reacts = True
                        valid_emojis_list = []
                        for pron in pronoun_roles:
                            valid_emojis_list.append(pron[2])

                        if react in valid_emojis_list:
                            for p_role in pronoun_roles:
                                if react == p_role[2]:
                                    set_pronoun = p_role[1]
                                    break
                        #if react == "♀️":
                        #    set_pronoun = "She/Her"
                        #elif react == "♂️":
                        #    set_pronoun = "He/Him"
                        #elif react == "👤":
                        #    set_pronoun = "Any/All"
                        #elif react == "🧍":
                        #    set_pronoun = "They/Them"
                        #
                        #elif react == "❌":
                        #    set_pronoun = ""
                        else:
                            set_pronoun = ""
                            accepted_reacts = False

                        if accepted_reacts:
                            if set_pronoun != "":
                                try:
                                    the_role = discord.utils.get(user.guild.roles, name=set_pronoun)
                                    await user.add_roles(the_role)
                                    print("Added role: %s" % set_pronoun)
                                except:
                                    print("some error occured while trying to assign pronouns")
                            else:
                                print("removing all pronoun roles (not working)")

                            #other_pronoun_roles = [[item[0], item[1]] for item in cur.execute("SELECT name, id FROM roles WHERE category = ? AND permissions = ? AND name != ?", ('pronoun','', set_pronoun)).fetchall()]

                            #for other_pronoun in other_pronoun_roles:
                            #    for role in all_roles:
                            #        if other_pronoun[1] == str(role.id):
                            #            if role in user.roles:
                            #                await user.remove_roles(role)
                            #                print("Removed role: %s" % role.name)
                            #            else:
                            #                print("Did not have role: %s" % role.name)
                        else:
                            await message.remove_reaction(payload.emoji, user)
                            print("non accepted react detected")
                    elif ('other' in str(embed.title).lower()) or ('extra' in str(embed.title).lower()):
                        accepted_reacts = True
                        valid_emojis_list = []
                        for role in other_roles:
                            valid_emojis_list.append(role[2])

                        if react in valid_emojis_list:
                            for o_role in other_roles:
                                if react == o_role[2]:
                                    set_other = o_role[1]
                                    break
                        #elif react == "❌":
                        #    set_other = ""
                        else:
                            set_other = ""
                            accepted_reacts = False

                        if accepted_reacts:
                            if set_other != "":
                                try:
                                    the_role = discord.utils.get(user.guild.roles, name=set_other)
                                    await user.add_roles(the_role)
                                    print("Added role: %s" % set_pronoun)
                                except:
                                    print("some error occured while trying to assign a role")
                            else:
                                print("removing all 'other' roles (not working)")

                        else:
                            await message.remove_reaction(payload.emoji, user)
                            print("non accepted react detected")
                    else:
                        print("neither `pronoun`, `colour` or `other` mentioned in message")
                else:
                    print('message has no embed')
        else:
            pass
            #print(f"reaction added in different server: {server_id}")


    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        valid_servers = [413011798552477716]
        server_id = payload.guild_id
        if server_id in valid_servers:
            guild = await self.bot.fetch_guild(server_id)
            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            react = payload.emoji.name
            #user = payload.member
            user = await guild.fetch_member(payload.user_id)

            role_channel = self.bot.get_channel(966276028630728744)

            if channel.id != role_channel.id:
                return
            elif user is None:
                print('user is None (%s)' % str(user))
            elif str(user.id) == '958105284759400559':
                print('bot reacted itself')
            else:
                guild = self.bot.get_guild(payload.guild_id)
                all_roles = [r for r in guild.roles]
                con = sqlite3.connect('cogs/roles/roles.db')
                cur = con.cursor()
                color_roles = [[item[0], item[1], item[2]] for item in cur.execute("SELECT id, name, details FROM roles WHERE category = ?", ("color",)).fetchall()]
                pronoun_roles = [[item[0], item[1], item[2]] for item in cur.execute("SELECT id, name, details FROM roles WHERE category = ?", ("pronoun",)).fetchall()]
                other_roles = [[item[0], item[1], item[2]] for item in cur.execute("SELECT id, name, details FROM roles WHERE category = ?", ("music",)).fetchall()]

                accepted_reacts = True
                valid_emojis_list = []
                for rol in color_roles+pronoun_roles+other_roles:
                    valid_emojis_list.append(rol[2])

                if react in valid_emojis_list:
                    for c_role in color_roles+pronoun_roles+other_roles:
                        if react == c_role[2]:
                            set_role = c_role[1]
                            break
                else:
                    set_role = ""
                    accepted_reacts = False

                if set_role != "":
                    try:
                        the_role = discord.utils.get(user.guild.roles, name=set_role)
                        await user.remove_roles(the_role)
                        print("Removed role: %s" % set_role)
                    except:
                        print("some error occured while trying to remove a role")
                else:
                    print("removed some invalid role")
        else:
            pass
            #print(f"reaction removed in different server: {server_id}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(
        RoleEvents(bot),
        guilds = [discord.Object(id = 413011798552477716)])