import discord
from discord.ext import commands
import sqlite3
import datetime
import pytz
from other.utils.utils import Utils as util
from urllib.parse import urlparse
import os
import re
import asyncio
from emoji import UNICODE_EMOJI
import traceback


class Event_Response(commands.Cog):
    def __init__(self, bot: commands.bot) -> None:
        self.bot = bot

    def is_inactive(self):
        try:
            activity = util.is_active()
            return not activity
        except:
            return True

    # HELPFUL FUNCTIONS

    def find_urls(self, message_string):
        url_list = re.findall(r'(https?://[^\s]+)', message_string)
        return url_list

    def get_domains(self, url_list):
        domain_list = []
        for url in url_list:
            domain = urlparse(url).netloc
            if domain.endswith(".bandcamp.com"):
                domain = "bandcamp.com"
            domain_list.append(domain)
        return domain_list



    def get_botspamchannelid(self):
        conB = sqlite3.connect(f'databases/botsettings.db')
        curB = conB.cursor()
        botspamchannelid_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("botspam channel id",)).fetchall()]
        while "" in botspamchannelid_list:
            botspamchannelid_list.remove("")
        if len(botspamchannelid_list) == 0:
            print("Error: No botspam channel id")
            bot_channel_string = os.getenv("bot_channel_id")
            if util.represents_integer(bot_channel_string):
                botspamchannelid = int(bot_channel_string)
            else:
                raise ValueError(f"invalid botspam channel id (.env)")
                return
        else:
            if util.represents_integer(botspamchannelid_list[0]):
                botspamchannelid = int(botspamchannelid_list[0])
            else:
                raise ValueError(f"invalid botspam channel id (DB)")
                return
        return botspamchannelid



    async def botspam_send(self, title, text, footer, image, author, color, timestamp):
        botspamchannelid = self.get_botspamchannelid()
        try:
            botspam_channel = self.bot.get_channel(botspamchannelid)
        except:
            raise ValueError(f"could not find bot spam channel with provided id")
            return
        try:
            if timestamp == None or timestamp == "":
                timestamp = datetime.datetime.now()
            header = title[:256]
            description = text[:4096]
            if color == "" or color == None:
                color = 0x000000
            embed = discord.Embed(title=header, description=description, color=color, timestamp=timestamp)
            if footer.strip() != "":
                embed.set_footer(text=footer)
            else:
                embed.set_footer(text='\u200b')
            if image.strip() != "":
                embed.set_thumbnail(url=image)

            if author != None and str(author) != "":
                try:
                    embed.set_author(name=author.name, icon_url=str(author.avatar))
                except Exception as e:
                    embed.set_author(name=author.name, icon_url="https://cdn.discordapp.com/embed/avatars/0.png")
                    print(e)
            await botspam_channel.send(embed=embed)
        except Exception as e:
            print(e)
            raise ValueError(f"could not send embed")


    def setting_enabled(self, name):
        """Checks if a setting is enabled and returns True or False"""
        conB = sqlite3.connect(f'databases/botsettings.db')
        curB = conB.cursor()
        setting_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", (name,)).fetchall()]
        if len(setting_list) == 0:
            setting = "off"
        else:
            if len(setting_list) > 1:
                print(f"Warning: Multiple '{name}' entries in serversettings.")
            setting = setting_list[0].lower()

        if setting == "on":
            return True
        else:
            return False



    ######################################################### LISTENERS ##################################################################



    @commands.Cog.listener()
    async def on_member_join(self, member):
        if self.is_inactive():
            return

        server = member.guild
        user_id = member.id
        conB = sqlite3.connect(f'databases/botsettings.db')
        curB = conB.cursor()
        main_server = [item[0] for item in curB.execute("SELECT value FROM botsettings WHERE name = ?", ("main server id", )).fetchall()]

        if str(server.id) not in main_server:
            print(f"{member.name} joined {server.name}")
            return

        if self.setting_enabled("inactivity filter"):
            try:
                conUA = sqlite3.connect('databases/useractivity.db')
                curUA = conUA.cursor()
                curUA.execute("DELETE FROM useractivity WHERE userid = ?", (str(member.id),))

                join_time = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())

                curUA.execute("INSERT INTO useractivity VALUES (?, ?, ?, ?, ?)", (str(member.name), str(member.id), "0", str(join_time), ""))
                conUA.commit()
            except Exception as e:
                print("Error:", e)

        # CHECK IF ACCESS WALL IS ENABLED

        if self.setting_enabled("access wall"):
            try:
                # GET ROLE AND CHANNEL

                specialroles_accesswall_list = [item[0] for item in curB.execute("SELECT role_id FROM specialroles WHERE name = ?", ("access wall role",)).fetchall()]
                accesswall_role_id = int(specialroles_accesswall_list[0])
                accesswallchannelid_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("access wall channel id",)).fetchall()]
                accesswallchannelid = int(accesswallchannelid_list[0])
                wintersgate_role = server.get_role(accesswall_role_id)
                await member.add_roles(wintersgate_role)
                accesswall_channel = self.bot.get_channel(accesswallchannelid)

                # GET MESSAGE TEXT

                welcometext_list = [item[0].strip() for item in curB.execute("SELECT etc FROM serversettings WHERE name = ?", ("access wall",)).fetchall()]
                while "" in welcometext_list:
                    welcometext_list.remove("")
                if len(welcometext_list) == 0 or welcometext_list[0].strip() == "":
                    #default text
                    welcometext = f'Welcome <@{user_id}>!\nGive us a little intro about yourself and a moderator will verify and grant you access to the rest of the server as soon as possible.'
                else:
                    welcometext_preparse = welcometext_list[0]
                    welcometext = await util.customtextparse(welcometext_preparse, user_id)
                await accesswall_channel.send(welcometext)

            except Exception as e:
                print(e)
                botspamchannelid_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("botspam channel id",)).fetchall()]
                while "" in botspamchannelid_list:
                    botspamchannelid_list.remove("")
                if len(botspamchannelid_list) == 0:
                    print("Error: No botspam channel id")
                    botspamchannelid = int(os.getenv("bot_channel_id"))
                else:
                    botspamchannelid = int(botspamchannelid_list[0])
                try:
                    botspam_channel = self.bot.get_channel(botspamchannelid)
                    await botspam_channel.send(f"Error while trying to assign access wall role:\n{e}")
                except:
                    print("Error on member join.")

        else:
            # CHECK IF AUTOMATIC ROLE IS ENABLED

            if self.setting_enabled("automatic role"):
                communityrole_list = [item[0].strip() for item in curB.execute("SELECT role_id FROM specialroles WHERE name = ?", ("community role",)).fetchall()]
                while "" in communityrole_list:
                    communityrole_list.remove("")

                if len(communityrole_list) != 0:
                    try:
                        communityrole_id = int(communityrole_list[0])
                        community_role = server.get_role(communityrole_id)
                        await member.add_roles(community_role)
                    except Exception as e:
                        print(e)
                        botspamchannelid_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("botspam channel id",)).fetchall()]
                        while "" in botspamchannelid_list:
                            botspamchannelid_list.remove("")
                        if len(botspamchannelid_list) == 0:
                            print("Error: No botspam channel id")
                            botspamchannelid = int(os.getenv("bot_channel_id"))
                        else:
                            botspamchannelid = int(botspamchannelid_list[0])
                        try:
                            botspam_channel = self.bot.get_channel(botspamchannelid)
                            await botspam_channel.send(f"Error while trying to assign community role:\n{e}")
                        except:
                            print("Error on member join.")

            # CHECK IF GENERAL WELCOME MESSAGE IS ENABLED

            if self.setting_enabled("welcome message"):
                try:
                    generalchannel_id = int([item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("general channel id",)).fetchall()][0])
                    general_channel = self.bot.get_channel(generalchannel_id)

                    welcometext_list = [item[0].strip() for item in curB.execute("SELECT details FROM serversettings WHERE name = ?", ("welcome message",)).fetchall()]
                    while "" in welcometext_list:
                        welcometext_list.remove("")
                    if len(welcometext_list) == 0 or welcometext_list[0].strip() == "":
                        #default
                        yayemoji = util.emoji("yay")
                        welcometext = f'Welcome <@{user_id}>! {yayemoji}'
                    else:
                        welcometext_preparse = welcometext_list[0]
                        welcometext = await util.customtextparse(welcometext_preparse, user_id)
                    await general_channel.send(welcometext)
                except Exception as e:
                    print(f"Error while trying to send welcome message: {e}")

        # CHECK IF SERVER JOIN NOTIFICATION IS ENABLED

        if not self.setting_enabled("join/leave server notification"):
            return

        title = "Member joined"
        try:
            created_utc = member.created_at.astimezone(pytz.utc)
            now_utc = datetime.datetime.now(datetime.timezone.utc)
            age = now_utc - created_utc
            age_seconds = age.total_seconds()
            now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())
            age_string = util.seconds_to_readabletime(age_seconds, now)
        except Exception as e:
            print(e)
            age_string = "error"
        text = f"<@{user_id}>\nAccount Age: {age_string}"
        footer = f"NAME: {member.name}, ID: {user_id}"   
        image = str(member.avatar)
        color = 0x3cb043
        await self.botspam_send(title, text, footer, image, None, color, None)

        # under construction: NPsettings change inactive to active?



    @commands.Cog.listener()
    async def on_raw_member_remove(self, payload):
        if self.is_inactive():
            return

        user = payload.user
        server_id = payload.guild_id

        conB = sqlite3.connect(f'databases/botsettings.db')
        curB = conB.cursor()    
        main_server = [item[0] for item in curB.execute("SELECT value FROM botsettings WHERE name = ?", ("main server id", )).fetchall()]
        if str(server_id) not in main_server:
            print(f"{user.name} left server of id {server_id}")
            return
        print(f"{user.name} left main server")

        # REMOVE USER FROM USER ACTIVITY LIST

        try:
            conUA = sqlite3.connect('databases/useractivity.db')
            curUA = conUA.cursor()
            curUA.execute("DELETE FROM useractivity WHERE userid = ?", (str(user.id),))
            conUA.commit()
        except Exception as e:
            print("Error:", e)

        # CHECK IF SERVER LEAVE NOTIFICATION IS ENABLED

        if not self.setting_enabled("join/leave server notification"):
            return

        title = "Member left"
        text = f"<@{user.id}>"
        footer = f"NAME: {user.name}, ID: {user.id}"   
        image = str(user.avatar)
        color = 0xd30000
        await self.botspam_send(title, text, footer, image, None, color, None)



    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if self.is_inactive():
            return
        member = before
        server = member.guild
        if not server:
            return
        conB = sqlite3.connect(f'databases/botsettings.db')
        curB = conB.cursor()    
        main_server = [item[0] for item in curB.execute("SELECT value FROM botsettings WHERE name = ?", ("main server id", )).fetchall()]

        if str(server.id) not in main_server:
            #print(f"{member.name} updated in {server.name}")
            return

        updated_smth_to_notify = False
        title = ""
        text = ""

        if before.nick != after.nick: # nickname change
            if not self.setting_enabled("user name change notification"):
                return
            text += f"<@{member.id}>'s changed nickname from {before.nick} to {after.nick}.\n"
            updated_smth_to_notify = True

        if before.roles != after.roles: # roles change
            if not self.setting_enabled("assign role notification"):
                return
            added_roles = []
            removed_roles = []

            for role in before.roles:
                if role not in after.roles:
                    removed_roles.append(f"`{role.name}`")
            for role in after.roles:
                if role not in before.roles:
                    added_roles.append(f"`{role.name}`")

            if len(added_roles) == 1:
                text += f"<@{member.id}> was given the " + added_roles[0] + "role." 
            elif len(added_roles) > 1:
                text += f"<@{member.id}> was given the roles: " + ', '.join(added_roles) + ".\n"

            if len(removed_roles) == 1:
                text += f"<@{member.id}> was removed from the " + removed_roles[0] + "role." 
            elif len(removed_roles) > 1:
                text += f"<@{member.id}> was removed from the roles: " + ', '.join(removed_roles) + ".\n"
            updated_smth_to_notify = True

        if before.timed_out_until is None and after.timed_out_until is not None: # timeout (the discord internal one)
            if not self.setting_enabled("user mute/ban/kick notification"):
                return
            endtime = after.timed_out_until
            now_utc = datetime.datetime.utcnow()
            remaining = (endtime - now_utc).total_seconds()
            now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())
            remaining_string = util.seconds_to_readabletime(remaining, now)
            text += f"<@{member.id}> was timed out via the discord internal time out feature.\n{remaining_string}\n"
            updated_smth_to_notify = True


        footer = f"ID: {member.id}"
        image = ""
        color = 0x0e4c92

        if updated_smth_to_notify:
            await self.botspam_send(title, text, footer, image, member, color, None)
        else:
            print("voice state update")



    @commands.Cog.listener()
    async def on_member_ban(self, server, user):
        if self.is_inactive():
            return
        if not server:
            return
        conB = sqlite3.connect(f'databases/botsettings.db')
        curB = conB.cursor()    
        main_server = [item[0] for item in curB.execute("SELECT value FROM botsettings WHERE name = ?", ("main server id", )).fetchall()]
        if str(server.id) not in main_server:
            print(f"{user.name} was banned from {server.name}")
            return

        # CHECK IF BAN NOTIFICATION IS ENABLED

        if not self.setting_enabled("join/leave server notification"): 
            return
        
        # CHECK IF THE LAST BAN WAS A TURING TEST BAN

        #def predicate(event):
        #    return event.action is discord.AuditLogAction.ban
        #try:
        #    event = await guild.audit_logs().find(predicate)
        #    if event.reason == "Failed the Turing Test (auto-ban)":
        #        # in this case a notification was already sent via turing test
        #        return
        #except Exception as e:
        #    print(e)

        bans = await message.guild.bans()
        for ban_entry in bans[:100]: 
            b_user = ban_entry.user
            b_reason = ban_entry.reason 
            if b_user.id == user.id:
                if b_reason == "Failed the Turing Test (auto-ban)":
                    return
                break

        # NOTIFY

        title = "Member banned"
        emoji = util.emoji("ban")
        text = f"<@{user.id}> {emoji}"
        footer = f"NAME: {user.name}, ID: {user.id}"   
        image = str(user.avatar)
        color = 0xd30000
        await self.botspam_send(title, text, footer, image, None, color, None)



    @commands.Cog.listener()
    async def on_member_unban(self, server, user):
        if self.is_inactive():
            return
        if not server:
            return
        conB = sqlite3.connect(f'databases/botsettings.db')
        curB = conB.cursor()    
        main_server = [item[0] for item in curB.execute("SELECT value FROM botsettings WHERE name = ?", ("main server id", )).fetchall()]
        if str(server.id) not in main_server:
            print(f"{user.name} was unbanned in {server.name}")
            return

        # CHECK IF UNBAN NOTIFICATION IS ENABLED

        if not self.setting_enabled("join/leave server notification"): 
            return

        title = "Member unbanned"
        emoji = util.emoji("ban")
        text = f"<@{user.id}> {emoji}"
        footer = f"NAME: {user.name}, ID: {user.id}"   
        image = str(user.avatar)
        color = 0x0e4c92
        await self.botspam_send(title, text, footer, image, None, color, None)



    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if self.is_inactive():
            return
        if before.author.bot:
            return
        server = before.guild
        if not server:
            return
        conB = sqlite3.connect(f'databases/botsettings.db')
        curB = conB.cursor()    
        main_server = [item[0] for item in curB.execute("SELECT value FROM botsettings WHERE name = ?", ("main server id", )).fetchall()]
        if not self.setting_enabled("edit message notification"):
            return
        if str(server.id) not in main_server:
            print(f"{before.author.name} edited message in {server.name}")
            return

        botspamchannelid = self.get_botspamchannelid()
        if str(before.channel.id) == str(botspamchannelid):
            suppressbotspamedit_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("suppress botspam edit/delete",)).fetchall()]
            if len(suppressbotspamedit_list) > 0:
                if suppressbotspamedit_list[0] == "on":
                    print(f"supressing msg edit ({before.author.name}) in botspam channel")
                    return

        now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())

        old_time = before.created_at
        old = int((old_time.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())

        if (now - old) > 7200:
            print(f"ignore edit of 2h+ old message ({now - old})")
            return

        if before.content == after.content and before.attachments == after.attachments:
            return

        #try:
        #    edit_time = after.created_at
        #    timestamp = edit_time.replace(tzinfo=timezone.utc).timestamp()
        #except:
        #    timestamp = ""

        title = f"Message Edited: {str(before.jump_url)}"
        # TEXT BEGIN
        text = f"\n**Before**:\n"
        text += util.cleantext2(before.content[:1024])
        if len(before.content) > 1024:
            text += "..."
        text += f"\n\n**After**:\n"
        text += util.cleantext2(after.content[:1024])
        if len(after.content) > 1024:
            text += "..."
        #text += f"<t:{timestamp}:f>"
        # TEXT END
        footer = f"NAME: {before.author.name}, ID: {before.author.id}"

        image = ""

        color = 0x0e4c92
        await self.botspam_send(title, text, footer, image, before.author, color, None) #after.created_at)



    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if self.is_inactive():
            return
        if message.author.bot:
            return
        server = message.guild
        if not server:
            return
        conB = sqlite3.connect(f'databases/botsettings.db')
        curB = conB.cursor()    
        main_server = [item[0] for item in curB.execute("SELECT value FROM botsettings WHERE name = ?", ("main server id", )).fetchall()]

        if not self.setting_enabled("edit message notification"):
            return
        if str(server.id) not in main_server:
            print(f"{message.author.name}'s message deleted in {server.name}")
            return

        botspamchannelid = self.get_botspamchannelid()
        if str(message.channel.id) == str(botspamchannelid):
            suppressbotspamedit_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("suppress botspam edit/delete",)).fetchall()]
            if len(suppressbotspamedit_list) > 0:
                if suppressbotspamedit_list[0] == "on":
                    print(f"supressing msg deletion ({message.author.name}) in botspam channel")
                    return

        title = f"Message deleted in <#{message.channel.id}>"
        # TEXT BEGIN
        text = util.cleantext2(message.content[:2048])
        if len(message.content) > 2048:
            text += "..."
        #text += f"<t:{timestamp}:f>"
        # TEXT END
        footer = f"NAME: {message.author.name}, ID: {message.author.id}"

        try:
            image = message.attachments[0].url # under construction
        except Exception as e:
            image = ""
        
        color = 0xd30000
        await self.botspam_send(title, text, footer, image, message.author, color, None) #message.created_at)



    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages):
        if self.is_inactive():
            return
        message = messages[0]
        server = message.guild
        if not server:
            return
        conB = sqlite3.connect(f'databases/botsettings.db')
        curB = conB.cursor()    
        main_server = [item[0] for item in curB.execute("SELECT value FROM botsettings WHERE name = ?", ("main server id", )).fetchall()]
        if not self.setting_enabled("edit message notification"):
            return
        if str(server.id) not in main_server:
            print(f"bulk message delete ({len(messages)}) in {server.name}")
            return

        botspamchannelid = self.get_botspamchannelid()
        if str(message.channel.id) == str(botspamchannelid):
            suppressbotspamedit_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("suppress botspam edit/delete",)).fetchall()]
            if len(suppressbotspamedit_list) > 0:
                if suppressbotspamedit_list[0] == "on":
                    print(f"supressing bulk delete in botspam channel")
                    return

        title = f"Bulk message delete"
        text += f"{len(messages)} deleted in <#{message.channel.id}>"
        image = ""
        color = 0xd30000
        await self.botspam_send(title, text, footer, image, None, color, None)


            
    @commands.Cog.listener()
    async def on_message(self, message):
        if self.is_inactive():
            return
        if message.author.bot:
            return
        server = message.guild
        if not server:
            return
        conB = sqlite3.connect(f'databases/botsettings.db')
        curB = conB.cursor()
        main_server = [item[0] for item in curB.execute("SELECT value FROM botsettings WHERE name = ?", ("main server id", )).fetchall()]
        if str(server.id) not in main_server:
            return

        # 1 USER ACTIVITY TRACKING (FOR INACTIVITY FILTER)

        if self.setting_enabled("inactivity filter"):
            try:
                inactivityfilter_list = [[item[0],item[1]] for item in curB.execute("SELECT details, etc FROM serversettings WHERE name = ?", ("inactivity filter",)).fetchall()]
                days = int(inactivityfilter_list[0][0])
                startingpoint = int(inactivityfilter_list[0][1])

                conUA = sqlite3.connect(f'databases/useractivity.db')
                curUA = conUA.cursor()
                user = message.author
                msg_utc = int((message.created_at.replace(tzinfo=None) - datetime.datetime(1970, 1, 1)).total_seconds())
                useractivity_list = [item[0] for item in curUA.execute("SELECT last_active FROM useractivity WHERE userid = ?", (str(user.id),)).fetchall()]

                if len(useractivity_list) == 0:
                    roleliststring = ';;'.join([str(y.id) for y in user.roles])
                    join_utc = int((user.joined_at.replace(tzinfo=None) - datetime.datetime(1970, 1, 1)).total_seconds())
                    curUA.execute("INSERT INTO useractivity VALUES (?, ?, ?, ?, ?)", (str(user.name), str(user.id), str(msg_utc), str(join_utc), roleliststring))
                    conUA.commit()
                    await util.changetimeupdate()
                else:
                    lastactive = int(useractivity_list[0])

                    if lastactive + 12*60*60 > msg_utc: # only update every 12 hours
                        # recent message
                        pass
                    else:
                        rolelist = [str(y.id) for y in user.roles]

                        update_userroles = True
                        if len(rolelist) <= 1:
                            try:
                                accesswallrole_list = [item[0] for item in cur.execute("SELECT role_id FROM specialroles WHERE name = ?", ("access wall role",)).fetchall()]
                                accesswallrole_id = accesswallrole_list[0]
                            except:
                                accesswallrole_id = ""
                            try:
                                timeoutrole_list = [item[0] for item in cur.execute("SELECT role_id FROM specialroles WHERE name = ?", ("timeout role",)).fetchall()]
                                timeoutrole_id = timeoutrole_list[0]
                            except:
                                timeoutrole_id = ""
                            try:
                                inactivityrole_list = [item[0] for item in cur.execute("SELECT role_id FROM specialroles WHERE name = ?", ("inactivity role",)).fetchall()]
                                inactivityrole_id = inactivityrole_list[0]
                            except:
                                inactivityrole_id = ""

                            if inactivityrole_id in rolelist or timeoutrole_id in rolelist or accesswallrole_id in rolelist:
                                update_userroles = False

                        if update_userroles:
                            roleliststring = ';;'.join(rolelist)
                            curUA.execute("UPDATE useractivity SET last_active = ?, previous_roles = ? WHERE userid = ?", (str(msg_utc), roleliststring, str(user.id)))
                        else:
                            curUA.execute("UPDATE useractivity SET last_active = ? WHERE userid = ?", (str(msg_utc), str(user.id)))
                        conUA.commit()
                        await util.changetimeupdate()
            except Exception as e:
                print("Error while trying to track user activity:", e)

        # 2 MODS MODS MODS FUNCTION

        if self.setting_enabled("mods mods mods notification"):
            alphabeticonly = ''.join(x for x in message.content if x.isalpha()).lower()
            if "modsmodsmods" in alphabeticonly:
                user = message.author
                if not user.bot:
                    # notify if someone wrote MODS MODS MODS or similar
                    that_author = user.mention
                    title = "Mods were called 👀"
                    text = f"User: {that_author}\nMessage link: {message.jump_url}"
                    footer = ""
                    image = ""
                    color = 0x0e4c92
                    await self.botspam_send(title, text, footer, image, None, color, None)
                    await message.add_reaction("👀")


        # 3 GENRE TAG FUNCTION
        channel = message.channel
        try:
            # check if genre tag reminder is enabled
            tag_reminding = self.setting_enabled("genre tag reminder")
            if tag_reminding:
                # check the channels the tag reminder should operate in
                genretagchannel_list = [item[0] for item in curB.execute("SELECT etc FROM serversettings WHERE name = ?", ("genre tag reminder",)).fetchall()]
                if len(genretagchannel_list) == 0:
                    tag_reminding = False
                else:
                    genretagchannel_string = genretagchannel_list[0]
                    genretagchannels = genretagchannel_string.split(";;")
        except Exception as e:
            tag_reminding = False
            print(e)

        if tag_reminding:
            # check if channel is one of those needin
            if str(channel.id) in genretagchannels:
                urls_in_message = self.find_urls(message.content)
                if len(urls_in_message) > 0:
                    # actually has links
                    linkdomains = self.get_domains(urls_in_message)
                    print(linkdomains)

                    trigger_links = ["open.spotify.com",
                                    "on.soundcloud.com",
                                    "www.youtube.com",
                                    "youtu.be",
                                    "geo.music.apple.com",
                                    "bandcamp.com"]

                    found_trigger_link = False
                    for link in trigger_links:
                        if link in linkdomains:
                            print(f"found {link}")
                            found_trigger_link = True

                    if found_trigger_link:
                        # check if the message also contains genre or ffo
                        valid_singleword_descriptors = ["genre:", "ffo:", "genre", "ffo"] #customise 
                        valid_multipleword_descriptors = [] #customise 

                        message_words = message.content.lower().split()
                        found_descriptor = False

                        for descriptor in valid_singleword_descriptors:
                            if descriptor in message_words:
                                found_descriptor = True
                        for descriptor in valid_multipleword_descriptors:
                            if descriptor in message.content.lower():
                                found_descriptor = True

                        if found_descriptor:
                            print("found descriptor, no action needed")
                        else:
                            # SEND REMINDER EMBED
                            col = 0xFFF700
                            msgtext = f"Have you properly tagged your post with a genre, sound description and/or FFO?\nIf yes, react with ✅. If no, pls add that and then react with ✅."
                            embed=discord.Embed(title="Tag Reminder", url="", description=msgtext, color=col)
                            remindermsg = await message.reply(embed=embed, mention_author=True)

                            # SAVE IN DATABASE
                            conRA = sqlite3.connect('databases/robotactivity.db')
                            curRA = conRA.cursor()
                            embed_type = "tag reminder"
                            channel_name = str(message.channel.name)
                            guild_id = str(message.guild.id)
                            channel_id = str(message.channel.id)
                            message_id = str(remindermsg.id)
                            app_id = str(self.bot.application_id)
                            called_by_id = str(message.author.id)
                            called_by_name = str(message.author.name)
                            utc_timestamp = str(int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds()))
                            curRA.execute("INSERT INTO raw_reaction_embeds VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (embed_type, channel_name, guild_id, channel_id, message_id, app_id, called_by_id, called_by_name, utc_timestamp))
                            conRA.commit()
                            await util.changetimeupdate()

                            # ADD REACTION
                            await remindermsg.add_reaction("✅")
                            print("reminded")



    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        if self.is_inactive():
            return
        server = role.guild
        if not server:
            return
        conB = sqlite3.connect(f'databases/botsettings.db')
        curB = conB.cursor()    
        main_server = [item[0] for item in curB.execute("SELECT value FROM botsettings WHERE name = ?", ("main server id", )).fetchall()]
        if str(server.id) not in main_server:
            return

        if not self.setting_enabled("create/delete role notification"):
            return

        title = "Role created"
        text = f"{role.name}\n<@&{role.id}>"
        footer = ""
        image = ""
        color = 0x3cb043
        await self.botspam_send(title, text, footer, image, None, color, None)



    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        if self.is_inactive():
            return
        server = role.guild
        if not server:
            return
        conB = sqlite3.connect(f'databases/botsettings.db')
        curB = conB.cursor()    
        main_server = [item[0] for item in curB.execute("SELECT value FROM botsettings WHERE name = ?", ("main server id", )).fetchall()]
        if str(server.id) not in main_server:
            return

        if not self.setting_enabled("create/delete role notification"):
            return

        title = "Role deleted"
        text = f"{role.name}"
        footer = ""
        image = ""
        color = 0xd30000
        await self.botspam_send(title, text, footer, image, None, color, None)



    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        if self.is_inactive():
            return
        server = before.guild
        if not server:
            return
        conB = sqlite3.connect(f'databases/botsettings.db')
        curB = conB.cursor()    
        main_server = [item[0] for item in curB.execute("SELECT value FROM botsettings WHERE name = ?", ("main server id", )).fetchall()]
        if str(server.id) not in main_server:
            return

        if not self.setting_enabled("create/delete role notification"):
            return

        title = "Role updated"
        updated_smth_to_notify = False

        text = f"<@&{before.id}>\n"
        if before.name != after.name:
            text += f"Updated name from {before.name} to {after.name}.\n"
            updated_smth_to_notify = True
        if before.color != after.color:
            text += f"Updated color from `{str(before.color)}` to `{str(after.color)}`.\n"
            updated_smth_to_notify = True
        if before.permissions != after.permissions:
            text += "Updated permissions."
            updated_smth_to_notify = True
        footer = ""
        image = ""
        color = after.color

        if updated_smth_to_notify:
            await self.botspam_send(title, text, footer, image, None, color, None)
        else:
            print("role got updated (but in a non-notify-worthy matter)")




    @commands.Cog.listener()
    async def on_scheduled_event_create(self, event):
        if self.is_inactive():
            return
        server = event.guild
        if not server:
            return
        conB = sqlite3.connect(f'databases/botsettings.db')
        curB = conB.cursor()    
        main_server = [item[0] for item in curB.execute("SELECT value FROM botsettings WHERE name = ?", ("main server id", )).fetchall()]
        if str(server.id) not in main_server:
            return

        if not self.setting_enabled("scheduled event notification"):
            return

        title = "Event was created"
        text = f"{event.name}"
        footer = ""
        image = ""
        color = 0x3cb043
        await self.botspam_send(title, text, footer, image, None, color, None)



    @commands.Cog.listener()
    async def on_scheduled_event_delete(self, event):
        if self.is_inactive():
            return
        server = event.guild
        if not server:
            return
        conB = sqlite3.connect(f'databases/botsettings.db')
        curB = conB.cursor()    
        main_server = [item[0] for item in curB.execute("SELECT value FROM botsettings WHERE name = ?", ("main server id", )).fetchall()]
        if str(server.id) not in main_server:
            return

        if not self.setting_enabled("scheduled event notification"):
            return

        title = "Event was deleted"
        text = f"{event.name}"
        footer = ""
        image = ""
        color = 0xd30000
        await self.botspam_send(title, text, footer, image, None, color, None)



    @commands.Cog.listener()
    async def on_scheduled_event_update(self, before, after):
        if self.is_inactive():
            return
        server = after.guild
        if not server:
            return
        conB = sqlite3.connect(f'databases/botsettings.db')
        curB = conB.cursor()    
        main_server = [item[0] for item in curB.execute("SELECT value FROM botsettings WHERE name = ?", ("main server id", )).fetchall()]
        if str(server.id) not in main_server:
            return

        if not self.setting_enabled("scheduled event notification"):
            return

        title = "Event was updated"
        text = f"{after.name}"
        footer = ""
        image = ""
        color = 0x0e4c92
        await self.botspam_send(title, text, footer, image, None, color, None)



    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        if self.is_inactive():
            return
        server = invite.guild
        if not server:
            return
        conB = sqlite3.connect(f'databases/botsettings.db')
        curB = conB.cursor()    
        main_server = [item[0] for item in curB.execute("SELECT value FROM botsettings WHERE name = ?", ("main server id", )).fetchall()]
        if str(server.id) not in main_server:
            return

        if not self.setting_enabled("invite notification"):
            return

        created_time = invite.created_at 
        expiration_time = invite.expires_at

        if expiration_time is None:
            expiration_string = "Permanent invite."
        else:
            try:
                remaining = (expiration_time - created_time).total_seconds()
                now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())
                remaining_string = util.seconds_to_readabletime(remaining, now)
                expiration_string = f"Expires in {remaining_string}."
            except:
                expiration_string = "Expires in `error`."

        title = "Invite created"
        text = f"Invite with code {invite.code} created by <@{invite.inviter.id}>.\n{expiration_string}."
        footer = f"user: {invite.inviter.name}, channel: {invite.channel.name}"
        image = ""
        color = 0x0e4c92
        await self.botspam_send(title, text, footer, image, None, color, None)



    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        if self.is_inactive():
            return
        server = channel.guild
        if not server:
            return
        conB = sqlite3.connect(f'databases/botsettings.db')
        curB = conB.cursor()    
        main_server = [item[0] for item in curB.execute("SELECT value FROM botsettings WHERE name = ?", ("main server id", )).fetchall()]
        if str(server.id) not in main_server:
            return

        if not self.setting_enabled("create/delete channel notification"):
            return

        title = f"Channel created <#{channel.id}>"
        text = f"Channel `{util.cleantext2(channel.name)}` has been created."
        footer = ""
        image = ""
        color = 0x3cb043
        await self.botspam_send(title, text, footer, image, None, color, None)



    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        if self.is_inactive():
            return
        server = channel.guild
        if not server:
            return
        conB = sqlite3.connect(f'databases/botsettings.db')
        curB = conB.cursor()    
        main_server = [item[0] for item in curB.execute("SELECT value FROM botsettings WHERE name = ?", ("main server id", )).fetchall()]
        if str(server.id) not in main_server:
            return

        if not self.setting_enabled("create/delete channel notification"):
            return

        title = f"Channel deleted"
        text = f"Channel `{util.cleantext2(channel.name)}` has been deleted."
        footer = ""
        image = ""
        color = 0xd30000
        await self.botspam_send(title, text, footer, image, None, color, None)



    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        if self.is_inactive():
            return
        server = after.guild
        if not server:
            return
        conB = sqlite3.connect(f'databases/botsettings.db')
        curB = conB.cursor()    
        main_server = [item[0] for item in curB.execute("SELECT value FROM botsettings WHERE name = ?", ("main server id", )).fetchall()]
        if str(server.id) not in main_server:
            return

        if not self.setting_enabled("create/delete channel notification"):
            return

        title = "Channel updated"
        updated_smth_to_notify = False
        text = f"<#{before.id}>"

        if before.name != after.name:
            text += f"changed name from {before.name} to {after.name}"
            updated_smth_to_notify = True
        if before.nsfw != after.nsfw:
            text += f"changed nsfw status"
            updated_smth_to_notify = True
        footer = ""
        image = ""
        color = 0x0e4c92

        if updated_smth_to_notify:
            await self.botspam_send(title, text, footer, image, None, color, None)
        else:
            print("channel update")



    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        if self.is_inactive():
            return
        server = thread.guild
        if not server:
            return
        conB = sqlite3.connect(f'databases/botsettings.db')
        curB = conB.cursor()    
        main_server = [item[0] for item in curB.execute("SELECT value FROM botsettings WHERE name = ?", ("main server id", )).fetchall()]
        if str(server.id) not in main_server:
            return

        if not self.setting_enabled("create/delete thread notification"):
            return

        title = "Thread created"
        text = f"{thread.name} aka <#{thread.id}>"
        try:
            text += f"\nin channel <#{thread.parent_id}>"
            footer = f"parent channel: {thread.parent.name}"
        except:
            footer = ""
        image = ""
        color = 0x3cb043
        await self.botspam_send(title, text, footer, image, None, color, None)



    @commands.Cog.listener()
    async def on_thread_remove(self, thread):
        if self.is_inactive():
            return
        server = thread.guild
        if not server:
            return
        conB = sqlite3.connect(f'databases/botsettings.db')
        curB = conB.cursor()    
        main_server = [item[0] for item in curB.execute("SELECT value FROM botsettings WHERE name = ?", ("main server id", )).fetchall()]
        if str(server.id) not in main_server:
            return

        if not self.setting_enabled("create/delete thread notification"):
            return

        title = "Thread removed"
        text = f"{thread.name}"
        try:
            text += f"\nin channel <#{thread.parent_id}>"
            footer = f"parent channel: {thread.parent.name}"
        except:
            footer = ""
        image = ""
        color = 0xd30000
        await self.botspam_send(title, text, footer, image, None, color, None)



    @commands.Cog.listener()
    async def on_thread_delete(self, thread):
        if self.is_inactive():
            return
        server = thread.guild
        if not server:
            return
        conB = sqlite3.connect(f'databases/botsettings.db')
        curB = conB.cursor()    
        main_server = [item[0] for item in curB.execute("SELECT value FROM botsettings WHERE name = ?", ("main server id", )).fetchall()]
        if str(server.id) not in main_server:
            return

        if not self.setting_enabled("create/delete thread notification"):
            return

        title = "Thread deleted"
        text = f"{thread.name}"
        try:
            text += f"\nin channel <#{thread.parent_id}>"
            footer = f"parent channel: {thread.parent.name}"
        except:
            footer = ""
        footer = ""
        image = ""
        color = 0xd30000
        await self.botspam_send(title, text, footer, image, None, color, None)



    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if self.is_inactive():
            return
        server = member.guild
        if not server:
            return
        conB = sqlite3.connect(f'databases/botsettings.db')
        curB = conB.cursor()    
        main_server = [item[0] for item in curB.execute("SELECT value FROM botsettings WHERE name = ?", ("main server id", )).fetchall()]
        if str(server.id) not in main_server:
            return

        if not self.setting_enabled("join/leave voicechat notification"):
            return

        updated_smth_to_notify = False

        if before.channel is None and after.channel is not None:
            title = ""
            text = f"<@{member.id}> joined VoiceChat <#{after.channel.id}>."
            color = 0x3cb043
            updated_smth_to_notify = True

        elif before.channel is not None and after.channel is None:
            title = ""
            text = f"<@{member.id}> left VoiceChat <#{before.channel.id}>."
            color = 0xd30000
            updated_smth_to_notify = True

        elif before.channel is not None and after.channel is not None and before.channel.id != after.channel.id:
            title = ""
            text = f"<@{member.id}> switched from VoiceChat <#{before.channel.id}> to <#{after.channel.id}>."
            color = 0x0e4c92
            updated_smth_to_notify = True

        footer = f"NAME: {member.name}, ID: {member.id}"
        image = ""

        if updated_smth_to_notify:
            await self.botspam_send(title, text, footer, image, member, color, None)
        else:
            print("voice state update")




    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if self.is_inactive():
            return

        # INITIALISE

        try:
            conB = sqlite3.connect(f'databases/botsettings.db')
            curB = conB.cursor()    
            main_server = [item[0] for item in curB.execute("SELECT value FROM botsettings WHERE name = ?", ("main server id", )).fetchall()]
            server_id = str(payload.guild_id)

            channel_id = payload.channel_id
            message_id = payload.message_id
            cmid = f"{str(channel_id)}/{str(message_id)}"

            react = payload.emoji.name
            user = payload.member
            user_id = payload.user_id

            if user.bot:
                return

            # RETRIEVE CHANNELS

            try:
                # ROLE REACTION ASSIGNMENT
                reactionrole_enabled = self.setting_enabled("reaction roles")
                rolechannel_id = ""

                # ROLE CHANNEL
                rolechannel_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("role channel id",)).fetchall()]
                if len(rolechannel_list) == 0:
                    reactionrole_enabled = False
                else:
                    rolechannel_id = rolechannel_list[0].strip()
                    if not util.represents_integer(rolechannel_id):
                        reactionrole_enabled = False
            except:
                reactionrole_enabled = False

            try:
                # ACCESS WALL AND TURING TEST ENABLED?
                turingtest_enabled = (self.setting_enabled("access wall") and self.setting_enabled("turing test"))
                ruleschannel_id = ""

                # TURING TEST (RULES) CHANNEL
                ruleschannel_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("rules channel id",)).fetchall()] # turing test channel
                if len(ruleschannel_list) == 0:
                    turingtest_enabled = False
                else:
                    ruleschannel_id = ruleschannel_list[0].strip()
                    if not util.represents_integer(ruleschannel_id):
                        turingtest_enabled = False
            except:
                turingtest_enabled = False

            # FETCH APPLICATION IDs

            application_list = [item[0] for item in curB.execute("SELECT value FROM botsettings WHERE name = ?", ("app id", )).fetchall()]
            application_list += str(self.bot.application_id)

            # GET TO ACTION
            # 1. REACTION OUTSIDE ROLE CHANNEL (SUGGESTIONS / PINGTERESTS / TAG REMINDERS)

            if not reactionrole_enabled or str(channel_id) != rolechannel_id:
                
                if str(user_id) not in application_list: # reaction not by an MDM bot instance

                    conRA = sqlite3.connect('databases/robotactivity.db')
                    curRA = conRA.cursor()
                    rawreactionembed_list = [[item[0],item[1],item[2]] for item in curRA.execute("SELECT embed_type, channel_id, message_id FROM raw_reaction_embeds").fetchall()]
                    rawreactionembed_dict = {}
                    for item in rawreactionembed_list:
                        channel_message_ids = f"{item[1]}/{item[2]}"
                        rawreactionembed_dict[channel_message_ids] = item[0]

                    if cmid in rawreactionembed_dict:

                        channel = self.bot.get_channel(channel_id) 
                        message = await channel.fetch_message(message_id)

                        if message.embeds:   #check if list is not empty
                            embed = message.embeds[0]

                            # A) SUGGESTION FUNCTIONALITY

                            if rawreactionembed_dict[cmid] == "recommendation": #'Recommendation' == str(embed.title):
                                if react == "📝":
                                    testprint = "detected 📝 react by %s" % user.name
                                    print(testprint)
                                    
                                    conM = sqlite3.connect('databases/memobacklog.db') 
                                    curM = conM.cursor()
                                    curM.execute('''CREATE TABLE IF NOT EXISTS memobacklog (bgid text, userid text, username text, backlog text, details text)''')
                                    
                                    now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())
                                    bl_entries = [x.strip() for x in (str(embed.description).split("▪️")[0].replace("*", " ").strip()).split(";") if x.strip()] #the x for x if x should remove all empty strings
                                    i=1000
                                    for bl_entry in bl_entries:
                                        mmid = str(now) + "_" + str(user.id) + "_0rec" + str(i)
                                        print(f"adding entry {i - 999} to backlog")
                                        curM.execute("INSERT INTO memobacklog VALUES (?, ?, ?, ?, ?)", (mmid, str(user.id), str(user.name), bl_entry, ""))
                                        conM.commit()
                                        i += 1
                                    await util.changetimeupdate()

                                    try:
                                        footer = str(embed.footer.text)
                                        newfooter = footer + "\n-added to " + util.cleantext2(str(user.display_name))[:20].strip() + "'s backlog"
                                        L = len(newfooter)
                                        if L > 2048:
                                            newfooter = newfooter[L-2048:]
                                        embed.set_footer(text = newfooter[:2048])
                                        await message.edit(embed=embed)
                                    except Exception as e:
                                        print(e)

                            # B) PINGTEREST SUBSCRIPTION

                            elif rawreactionembed_dict[cmid] == "pingterest": #str(embed.title).startswith('Pingterest: '):
                                pi_name = str(embed.title).lower().split("pingterest: ")[-1]
                                
                                if react == "✅":
                                    conP = sqlite3.connect('databases/pingterest.db')
                                    curP = conP.cursor()
                                    curP.execute('''CREATE TABLE IF NOT EXISTS pingterests (pingterest text, userid text, username text, details text)''')

                                    pi_list = [[item[0], item[1], item[2], item[3]] for item in curP.execute("SELECT pingterest, userid, username, details FROM pingterests WHERE pingterest = ? AND details = ?", (pi_name, "template")).fetchall()]

                                    if len(pi_list) == 0:
                                        print("error: pingterest does not exist")
                                    else:
                                        pi_user = [[item[0], item[1], item[2], item[3]] for item in curP.execute("SELECT pingterest, userid, username, details FROM pingterests WHERE pingterest = ? AND userid = ?", (pi_name, str(user.id))).fetchall()]
                                        if len(pi_user) == 0:
                                            print("pingterest: %s (user joining)" % pi_name)
                                            curP.execute("INSERT INTO pingterests VALUES (?, ?, ?, ?)", (pi_name, str(user.id), str(user.name), ""))
                                            conP.commit()
                                            print("successfully joined pingterest")
                                            await util.changetimeupdate()
                                            try:
                                                if embed.footer.text is None:
                                                    footer = ""
                                                else:
                                                    footer = str(embed.footer.text)
                                                newfooter = footer + "\n-" + util.cleantext2(str(user.display_name))[:20].strip() + " joined!"
                                                L = len(newfooter)
                                                if L > 2048:
                                                    newfooter = newfooter[L-2048:]
                                                embed.set_footer(text = newfooter[:2048])
                                                await message.edit(embed=embed)
                                            except Exception as e:
                                                print(e)
                                        else:
                                            print("pingterest: %s (already joined)" % pi_name)
                                            try:
                                                if embed.footer.text is None:
                                                    footer = ""
                                                else:
                                                    footer = str(embed.footer.text)
                                                newfooter = footer + "\n-" + util.cleantext2(str(user.display_name))[:20].strip() + " already joined"
                                                L = len(newfooter)
                                                if L > 2048:
                                                    newfooter = newfooter[L-2048:]
                                                embed.set_footer(text = newfooter[:2048])
                                                await message.edit(embed=embed)
                                            except Exception as e:
                                                print(e)

                                elif react == "🚫":
                                    conP = sqlite3.connect('databases/pingterest.db')
                                    curP = conP.cursor()
                                    curP.execute('''CREATE TABLE IF NOT EXISTS pingterests (pingterest text, userid text, username text, details text)''')

                                    pi_list = [[item[0], item[1], item[2], item[3]] for item in curP.execute("SELECT pingterest, userid, username, details FROM pingterests WHERE pingterest = ? AND details = ?", (pi_name, "template")).fetchall()]

                                    if len(pi_list) == 0:
                                        print("error: pingterest does not exist")
                                    else:
                                        pi_user = [[item[0], item[1], item[2], item[3]] for item in curP.execute("SELECT pingterest, userid, username, details FROM pingterests WHERE pingterest = ? AND userid = ?", (pi_name, str(user.id))).fetchall()]
                                        if len(pi_user) != 0:
                                            print("pingterest: %s (user joined)" % pi_name)
                                            curP.execute("DELETE FROM pingterests WHERE pingterest = ? AND userid = ?", (pi_name, str(user.id)))
                                            conP.commit()
                                            print("successfully left pingterest")
                                            await util.changetimeupdate()
                                            try:
                                                if embed.footer.text is None:
                                                    footer = ""
                                                else:
                                                    footer = str(embed.footer.text)
                                                newfooter = footer + "\n-" + util.cleantext2(str(user.display_name))[:20].strip() + " left..."
                                                L = len(newfooter)
                                                if L > 2048:
                                                    newfooter = newfooter[L-2048:]
                                                embed.set_footer(text = newfooter[:2048])
                                                await message.edit(embed=embed)
                                            except Exception as e:
                                                print(e)
                                        else:
                                            print("pingterest: %s (not joined)" % pi_name)
                                            try:
                                                if embed.footer.text is None:
                                                    footer = ""
                                                else:
                                                    footer = str(embed.footer.text)
                                                newfooter = footer + "\n-" + util.cleantext2(str(user.display_name))[:20].strip() + " already unjoined"
                                                L = len(newfooter)
                                                if L > 2048:
                                                    newfooter = newfooter[L-2048:]
                                                embed.set_footer(text = newfooter[:2048])
                                                await message.edit(embed=embed)
                                            except Exception as e:
                                                print(e)

                            # C) TAG REMINDER FEATURE

                            elif rawreactionembed_dict[cmid] == "tag reminder": #str(embed.title) == "Tag Reminder":
                                if react == "✅":
                                    await message.delete()
                                    print("deleted tag reminder message")

                                    conRA = sqlite3.connect('databases/robotactivity.db')
                                    curRA = conRA.cursor()
                                    curRA.execute("DELETE FROM raw_reaction_embeds WHERE message_id = ? AND channel_id = ?", (str(message_id), str(channel_id)))
                                    conRA.commit()
                                    await util.changetimeupdate()


            # GET TO ACTION
            # 2. REACTION IN TURING/RULES CHANNEL

            if server_id not in main_server:
                return

            if turingtest_enabled:

                if str(channel_id) == ruleschannel_id: # turing test channel

                    # CHECK MESSAGE ID
                    rulesmsg_id = ""
                    rulesmsg_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("rules message id",)).fetchall()] # turing test channel
                    if len(rulesmsg_list) == 0:
                        turingtest_enabled = False
                    else:
                        rulesmsg_id = rulesmsg_list[0]
                        if not util.represents_integer(rulesmsg_id):
                            turingtest_enabled = False

                    if turingtest_enabled and str(message_id) == rulesmsg_id: # rules message / turing test message

                        # users reacting with the first react are very likely to be bots

                        # CHECK REACTION EMOJI
                        react2 = str(payload.emoji) # for custom emoji

                        trigger_reaction = ""
                        triggermoji_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("rules first reaction",)).fetchall()] # turing test channel
                        if len(triggermoji_list) == 0:
                            turingtest_enabled = False
                        else:
                            trigger_reaction = triggermoji_list[0]

                        if turingtest_enabled and ((react.lower() == trigger_reaction.lower()) or (react2.lower() == trigger_reaction.lower())):
                            print("found turing test trigger react")
                            userroleIDs = [y.id for y in user.roles]

                            # CHECK ACCESS WALL ROLE

                            try:
                                accesswall_role_id = int([item[0] for item in curB.execute("SELECT role_id FROM specialroles WHERE name = ?", ("access wall role",)).fetchall()][0])
                            except:
                                turingtest_enabled = False

                            if turingtest_enabled and accesswall_role_id in userroleIDs: # has access wall/winters gate role
                                print("user is in access wall")

                                # CHECK VERIFIED ROLE
                                try:
                                    verified_role_id = int([item[0] for item in curB.execute("SELECT role_id FROM specialroles WHERE name = ?", ("verified role",)).fetchall()][0])
                                except:
                                    turingtest_enabled = False

                                if turingtest_enabled and verified_role_id not in userroleIDs: # user does not have verified role

                                    # actual ban
                                    print("user not verified yet. preparing to ban...")

                                    # get guild
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

                                    for i in range(0,10):
                                        print(10-i)
                                        await asyncio.sleep(1)

                                    await guild.ban(user, reason="Failed the Turing Test (auto-ban)", delete_message_days=0)

                                    # confirmation
                                    try:
                                        title = "Failed Turing Test"
                                        emoji = util.emoji("ban")
                                        text = f"Banned <@{user.id}> {emoji}"
                                        footer = f"NAME: {user.name}, ID: {user.id}"
                                        image = str(user.avatar)
                                        color = 0xd30000
                                        await self.botspam_send(title, text, footer, image, None, color, None)
                                    except Exception as e:
                                        print("Error while trying to send turing ban confirmation:", e)


                                    # send bye in access wall
                                    accesswallchannelid_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("access wall channel id",)).fetchall()]
                                    accesswallchannelid = int(accesswallchannelid_list[0])
                                    wintersgate_channel = self.bot.get_channel(accesswallchannelid)
                                    emoji = util.emoji("bye")
                                    await wintersgate_channel.send(f'Bye <@{user.id}>! {emoji}')
                                    

                                    # send DM
                                    turingbanmessage_enabled = self.setting_enabled("turing ban message")

                                    if turingbanmessage_enabled:
                                        turingbanmessage_list = [item[0] for item in curB.execute("SELECT details FROM serversettings WHERE name = ?", ("turing ban message",)).fetchall()]

                                        if len(turingbanmessage_list) > 0 and turingbanmessage_list[0].strip() != "":
                                            try:
                                                user = await self.bot.fetch_user(user.id)
                                                message = await util.customtextparse(turingbanmessage_list[0].strip(), str(user.id))
                                                embed=discord.Embed(title="", description=message, color=0xB80F0A)
                                                await user.send(embed=embed)
                                                print("Successfully notified user.")
                                            except Exception as e:
                                                print("Error while trying to DM banned user:", e)
                                        else:
                                            print("Turing ban message enabled but no message text provided.")

        except Exception as e:
            print("Error in on_raw_reaction_add():", e)
            print(traceback.format_exc())

            

async def setup(bot: commands.bot) -> None:
    await bot.add_cog(
        Event_Response(bot),
        guilds = [discord.Object(id = int(os.getenv("guild_id")))])