import os
import discord
from discord.ext import commands
import sqlite3



class RoleEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.valid_server = int(os.getenv("guild_id"))

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):

        # CHECK SERVER

        server_id = payload.guild_id
        if server_id != self.valid_server:
            return

        user = payload.member
        try: 
            if user.bot:
                return
        except:
            # somehow the payload.member object is None in on_raw_reaction_remove() while it is not in on_raw_reaction_add()
            pass

        #channel = self.bot.get_channel(payload.channel_id)
        #message = await channel.fetch_message(payload.message_id)

        channel_id = payload.channel_id
        message_id = payload.message_id

        react = payload.emoji.name #for default emojis
        react2 = str(payload.emoji) #for custom emojis
        user_id = payload.user_id

        # CHECK SETTINGS

        conB = sqlite3.connect(f'databases/botsettings.db')
        curB = conB.cursor()

        try:
            reaction_role_settings_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("reaction roles", )).fetchall()]
            reaction_role_setting = reaction_role_settings_list[0]
            if reaction_role_setting != "on":
                return
        except Exception as e:
            print("Error while trying to fetch reaction roles setting:", e)
            return

        try:
            role_channel_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("role channel id", )).fetchall()]
            role_channel_id = int(role_channel_list[0])
        except Exception as e:
            print("Error while trying to fetch role channel id:", e)
            return

        # CHECK CHANNEL

        if channel_id != role_channel_id:
            return

        # CHECK USER

        application_list = [item[0] for item in curB.execute("SELECT value FROM botsettings WHERE name = ?", ("app id", )).fetchall()]
        application_list += str(self.bot.application_id)
        if str(user_id) in application_list:
            return

        # FETCH ROLE CATEGORIES

        try:
            category_list = [[item[0].lower(),item[1].lower(),item[2]] for item in curB.execute("SELECT name, type, msg_id FROM reactionrolesettings WHERE turn = ?", ("on",)).fetchall()]
            msg_cat_dict = {}
            cat_type_dict = {}
            for item in category_list:
                cat = item[0]
                msg_cat_dict[item[2]] = cat
                cat_type_dict[cat] = item[1]
        except Exception as e:
            print("Error while trying to fetch list of enabled reaction roles:", e)
            return

        if str(message_id) not in msg_cat_dict: 
            print("reaction to message that is not an enabled reaction role category in the database")
            return

        category = msg_cat_dict[str(message_id)]
        cat_type = cat_type_dict[category]

        # FETCH ROLES

        try:
            con = sqlite3.connect('databases/roles.db')
            cur = con.cursor()
            assignable_role_ids = [[item[0],item[1]] for item in cur.execute("SELECT id, details FROM roles WHERE permissions = ? AND LOWER(category) = ?", ("",category)).fetchall()]
            emoji_role_dict = {}
            for item in assignable_role_ids:
                role_id = item[0]
                emoji = item[1]
                emoji_role_dict[emoji] = role_id
        except Exception as e:
            print("Error while trying to fetch roles from database:", e)
            return

        # GET THE SPECIFIC ROLE

        if react in emoji_role_dict:
            role_id = emoji_role_dict[react]
        elif react2 in emoji_role_dict:
            role_id = emoji_role_dict[react2]
        else:
            try:
                channel = self.bot.get_channel(payload.channel_id)
                message = await channel.fetch_message(payload.message_id)
                await message.remove_reaction(payload.emoji, user)
                print("non accepted react detected")
            except:
                print("could not remove reaction")
            return

        try:
            guild = self.bot.get_guild(payload.guild_id) # check if guild is in cache
            if guild is None:
                try:
                    guild = message.guild # if message was already initialized
                except:
                    guild = await self.bot.fetch_guild(payload.guild_id) # fetch guild (this sometimes doesn't work somehow)
                    if guild is None:
                        try:
                            channel = self.bot.get_channel(channel_id) # initialize message 
                            message = await channel.fetch_message(message_id)
                            guild = message.guild
                        except:
                            raise ValueError("could not fetch guild")
            the_role = discord.utils.get(guild.roles, id = int(role_id))
        except Exception as e:
            print("could not fetch role via id. try updating role database:", e)
            return

        try:
            if user is None:
                user = guild.get_member(user_id)
                await user.add_roles(the_role)
            else:
                try:
                    # user was initialized from payload.member
                    await user.add_roles(the_role)
                except:
                    user = guild.get_member(user_id)
                    await user.add_roles(the_role)
        except:
            print(f"could not assign role {the_role.name} to user")
            return

        # UNASSIGN RADIOBUTTON ROLES

        if cat_type.lower() not in ["r", "radio", "radiobutton"]:
            return

        role_ids = list(emoji_role_dict.values())
        for role in guild.roles:
            if str(role.id) in role_ids and role.id != the_role.id:
                if role in user.roles:
                    await user.remove_roles(role)
                    print(f"Removed role: {role.name}")
                else:
                    print(f"Did not have role: {role.name}")



    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        # CHECK SERVER

        server_id = payload.guild_id
        if server_id != self.valid_server:
            return

        user = payload.member
        try: 
            if user.bot:
                return
        except:
            # somehow the payload.member object is None in on_raw_reaction_remove() while it is not in on_raw_reaction_add()
            pass

        #channel = self.bot.get_channel(payload.channel_id)
        #message = await channel.fetch_message(payload.message_id)

        channel_id = payload.channel_id
        message_id = payload.message_id

        react = payload.emoji.name #for default emojis
        react2 = str(payload.emoji) #for custom emojis
        user_id = payload.user_id

        # CHECK SETTINGS

        conB = sqlite3.connect(f'databases/botsettings.db')
        curB = conB.cursor()

        try:
            reaction_role_settings_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("reaction roles", )).fetchall()]
            reaction_role_setting = reaction_role_settings_list[0]
            if reaction_role_setting != "on":
                return
        except Exception as e:
            print("Error while trying to fetch reaction roles setting:", e)
            return

        try:
            role_channel_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("role channel id", )).fetchall()]
            role_channel_id = int(role_channel_list[0])
        except Exception as e:
            print("Error while trying to fetch role channel id:", e)
            return

        # CHECK CHANNEL

        if channel_id != role_channel_id:
            return

        # CHECK USER

        application_list = [item[0] for item in curB.execute("SELECT value FROM botsettings WHERE name = ?", ("app id", )).fetchall()]
        application_list += str(self.bot.application_id)
        if str(user_id) in application_list:
            return

        # FETCH ROLE CATEGORIES

        try:
            category_list = [[item[0].lower(),item[1].lower(),item[2]] for item in curB.execute("SELECT name, type, msg_id FROM reactionrolesettings WHERE turn = ?", ("on",)).fetchall()]
            msg_cat_dict = {}
            cat_type_dict = {}
            for item in category_list:
                cat = item[0]
                msg_cat_dict[item[2]] = cat
                cat_type_dict[cat] = item[1]
        except Exception as e:
            print("Error while trying to fetch list of enabled reaction roles:", e)
            return

        if str(message_id) not in msg_cat_dict: 
            print("reaction to message that is not an enabled reaction role category in the database")
            return

        category = msg_cat_dict[str(message_id)]
        cat_type = cat_type_dict[category]

        # FETCH ROLES

        try:
            con = sqlite3.connect('databases/roles.db')
            cur = con.cursor()
            assignable_role_ids = [[item[0],item[1]] for item in cur.execute("SELECT id, details FROM roles WHERE permissions = ? AND LOWER(category) = ?", ("",category)).fetchall()]
            emoji_role_dict = {}
            for item in assignable_role_ids:
                role_id = item[0]
                emoji = item[1]
                emoji_role_dict[emoji] = role_id
        except Exception as e:
            print("Error while trying to fetch roles from database:", e)
            return

        # GET THE SPECIFIC ROLE

        if react in emoji_role_dict:
            role_id = emoji_role_dict[react]
        elif react2 in emoji_role_dict:
            role_id = emoji_role_dict[react2]
        else:
            return

        try:
            guild = self.bot.get_guild(payload.guild_id) # check if guild is in cache
            if guild is None:
                guild = await self.bot.fetch_guild(payload.guild_id) # fetch guild (this sometimes doesn't work somehow)
                if guild is None:
                    try:
                        channel = self.bot.get_channel(channel_id) # initialize message 
                        message = await channel.fetch_message(message_id)
                        guild = message.guild
                    except:
                        raise ValueError("could not fetch guild")
            the_role = discord.utils.get(guild.roles, id = int(role_id))
        except:
            print("could not fetch role via id. try updating role database")
            return

        try:
            if user is None:
                user = guild.get_member(user_id)
                await user.remove_roles(the_role)
            else:
                try:
                    # if user was initialized from payload.member
                    await user.remove_roles(the_role)
                except:
                    user = guild.get_member(user_id)
                    await user.remove_roles(the_role)
        except:
            print(f"could not unassign role {the_role.name} from user")
            return



async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(
        RoleEvents(bot),
        guilds = [discord.Object(id = int(os.getenv("guild_id")))])