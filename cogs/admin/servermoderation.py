# COG for mod features such as banning, kicking, timing out users


import discord
from discord.ext import commands
import datetime
import pytz
from tzlocal import get_localzone
from other.utils.utils import Utils as util
import sqlite3
import requests
import os
import sys
import zipfile


class Administration_of_Server(commands.Cog):
    def __init__(self, bot: commands.bot) -> None:
        self.bot = bot
        self.application_id = os.getenv("application_id")
        self.prefix = os.getenv("prefix")

    # FUNCTIONS

    async def get_immunitylist(self, ctx):
        try:
            # FETCH ALL USERS WITH MANAGE_GUILD PERMS

            moderator_serverfetched_list = []
            moderator_ID_serverfetched_list = []
            for member in ctx.guild.members:
                member_perms = [p for p in member.guild_permissions]
                for p in member_perms:
                    if p[1] and p[0] == "manage_guild":
                        moderator_serverfetched_list.append(member)
                        moderator_ID_serverfetched_list.append(str(member.id))

            # FETCH FROM MODERATOR DATABASE

            con = sqlite3.connect(f'databases/botsettings.db')
            cur = con.cursor()

            moderator_id_list = []
            mod_list = [[item[0],item[1]] for item in cur.execute("SELECT userid, details FROM moderators").fetchall()]
            if len(mod_list) == 0:
                pass
            else:
                for item in mod_list:
                    moderatorid = item[0]
                    modtype = item[1]
                    if modtype.lower() in ["dev", "owner"]: # devs and owner get always added
                        moderator_id_list.append(moderatorid)
                    else:
                        if moderatorid in moderator_ID_serverfetched_list: #other members will be checked for perms
                            moderator_id_list.append(moderatorid)
                        else:
                            # remove from list
                            cur.execute("DELETE FROM moderators WHERE userid = ?", (moderatorid,))
                            con.commit()
                            await util.changetimeupdate()

            for mod in moderator_serverfetched_list:
                if str(mod.id) in moderator_id_list:
                    pass
                else:
                    # add to list
                    cur.execute("INSERT INTO moderators VALUES (?, ?, ?)", (str(mod.name), str(mod.id), "mod"))
                    con.commit()
                    await util.changetimeupdate()

            immunity_list = moderator_id_list
            try:
                immunity_list += [item[0] for item in cur.execute("SELECT value FROM botsettings WHERE name = ?", ("app id", )).fetchall()]
            except Exception as e:
                print(f"Error while trying to compose immunity_list with bot data: {e}")
            try:
                immunity_list += [item[0] for item in cur.execute("SELECT value FROM botsettings WHERE name = ?", ("dev id", )).fetchall()]
            except Exception as e:
                print(f"Error while trying to compose immunity_list with developer data: {e}")
        except Exception as e:
            print(f"Error while trying to compose immunity_list with moderator data: {e}")
            immunity_list = []
        return immunity_list



    async def penaltynotifier(self, ctx, user_id):
        # returns True if feature is enabled AND the user is a full member
        # i.e. has the reference role (verified / community / everyone)
        con = sqlite3.connect(f'databases/botsettings.db')
        cur = con.cursor()

        # CHECK IF FEATURE IS ENABLED
        penaltynotifier_list = [item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("user mute/ban/kick notification",)).fetchall()]
        if len(penaltynotifier_list) == 0:
            print("Error: no penalty notifier entry in database, i.e. 'user mute/ban/kick notification'.")
            return False

        if len(penaltynotifier_list) > 1:
            print("Warning: Multiple 'user mute/ban/kick notification' entries in database.")
        penaltynotifier = penaltynotifier_list[0]

        if penaltynotifier.lower() in ["off","no","n"]:
            return False

        try:
            # CHECK IF USER HAS REFERENCE ROLE
            reference_role = await util.get_reference_role(ctx)
            try:
                the_member = ctx.guild.get_member(int(user_id))
                is_member = True
            except:
                is_member = False
                has_reference_role = False
                print("Did not notify user since they were not a server member.")

            if is_member:
                if reference_role in the_member.roles:
                    has_reference_role = True
                    print("Trying to send notification to user...")
                else:
                    has_reference_role = False
                    print("Did not notify user since they were not a full server member.")

            return has_reference_role

        except Exception as e:
            print("Error: ", e)
            return False



    ###########################################################################################################################

    # COMMANDS


    @commands.command(name='ban', aliases = ['userban'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _ban(self, ctx: commands.Context, *args):
        """🔒 ban user from server

        1st argument needs to be user id or @user mention, everything after will be read as ban reason.
        
        """
        if len(args) < 1:
            await ctx.send("Error: Missing arguments.")
            return

        # FETCHING USER ID (& REASON)
        try:
            user_id, reason = await util.fetch_id_from_args("user", "first", args)
        except:
            await ctx.send("Error while trying to fetch user.")

        print(f"banning user: {user_id} \nfor reason: {reason}")
        if reason == "":
            reason_string = ""
        else:
            reason_string = "\nReason: " + reason 

        # CHECK ROLES FOR DM REASONS LATER

        send_msg_bool = await self.penaltynotifier(ctx, user_id)

        # BANNING

        immunity_list = await self.get_immunitylist(ctx)

        if user_id in immunity_list:
            send_msg_bool = False
            pleademoji = util.emoji("pleading")
            await ctx.send(f'I- I really do not want to ban this user. {pleademoji}')
        else:
            try:
                user = await self.bot.fetch_user(user_id)
                await ctx.guild.ban(user, reason=reason, delete_message_days=0)
                
                banemoji = util.emoji("ban")
                header = f"Permanent ban"
                description = f'Banned <@{user_id}>. {banemoji}{reason_string}'
                embed=discord.Embed(title=header, description=description, color=0xB80F0A)
                await ctx.send(embed=embed)
            except Exception as e:
                await ctx.send(f'Error: {e}')
                send_msg_bool = False

        # DM THE USER

        if send_msg_bool:
            try:
                user = await self.bot.fetch_user(int(user_id))
                message = f"You have been banned from {ctx.guild.name}."
                message += reason_string
                embed=discord.Embed(title="", description=message, color=0xB80F0A)
                await user.send(embed=embed)
                print("Successfully notified user.")
            except Exception as e:
                print("Error while trying to DM banned user:", e)
    @_ban.error
    async def ban_error(self, ctx, error):
        await util.error_handling(ctx, error)
        


    @commands.command(name='kick', aliases = ['userkick'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _kick(self, ctx: commands.Context, *args):
        """🔒 Kicks user

        1st argument needs to be user id or @user mention, everything after will be read as kick reason.
        """
        if len(args) < 1:
            await ctx.send("Error: Missing arguments.")
            return

        # FETCHING USER ID (& REASON)

        try:
            user_id, reason = await util.fetch_id_from_args("user", "first", args)
        except:
            await ctx.send("Error while trying to fetch user.")
            return

        print(f"kicking user: {user_id} \nfor reason: {reason}")
        if reason == "":
            reason_string = ""
        else:
            reason_string = "\nReason: " + reason 

        # CHECK ROLES FOR DM REASONS LATER

        send_msg_bool = await self.penaltynotifier(ctx, user_id)

        # KICKING

        immunity_list = await self.get_immunitylist(ctx)

        if user_id in immunity_list:
            send_msg_bool = False
            pleademoji = util.emoji("pleading")
            await ctx.send(f'I- I really do not want to kick this user. {pleademoji}')
        else:
            try:
                user = await self.bot.fetch_user(user_id)
                await ctx.guild.kick(user, reason=reason)

                gunemoji = util.emoji("gun")
                header = f"Server kick"
                description = f'Kicked <@{user_id}>. {gunemoji}{reason_string}'
                embed=discord.Embed(title=header, description=description, color=0xB80F0A)
                await ctx.send(embed=embed)
            except Exception as e:
                await ctx.send(f'Error: {e}')
                send_msg_bool = False

        # DM THE USER

        if send_msg_bool:
            try:
                user = await self.bot.fetch_user(int(user_id))
                message = f"You have been kicked from {ctx.guild.name}."
                message += reason_string
                embed=discord.Embed(title="", description=message, color=0xB80F0A)
                await user.send(embed=embed)
                print("Successfully notified user.")
            except Exception as e:
                print("Error while trying to DM kicked user:", e)

    @_kick.error
    async def kick_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='unban', aliases = ['userunban'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _unban(self, ctx: commands.Context, *args):
        """🔒 Unbans user
        
        1st argument needs to be user id or @user mention.
        """
        if len(args) < 1:
            await ctx.send("Error: Missing arguments.")
            return

        # FETCH USER ID (& REASON)

        try:
            user_id, reason = await util.fetch_id_from_args("user", "first", args)
        except:
            await ctx.send("Error while trying to fetch user.")
            return

        print(f"unbanning user: {user_id} \nfor reason: {reason}")

        # UNBAN

        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user)

            emoji = util.emoji("celebrate")
            header = f"Account unban"
            description = f'Unbanned <@{user_id}>. {emoji}'
            embed=discord.Embed(title=header, description=description, color=0x4CBB17)
            await ctx.send(embed=embed)
        except:
            await ctx.send('Error in user argument')
    @_unban.error
    async def unban_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='mute', aliases = ['usermute','silence','timeout'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _mute(self, ctx: commands.Context, *args):
        """🔒 Mutes user
        
        1st argument needs to be user id or @user mention.
        Optional: 2nd argument is mute time* (if applicable, otherwise indefinite mute)
        Everything else will be read as mute reason.

        E.g.:
        Write `<prefix>mute <@id>` to mute a user indefinitely.
        Write `<prefix>mute <@id> <time>` to mute user for given time, where <time> has to be in the format: <integer><unit>

        *Valid time units are: min, hour(s), day(s), week(s), month(s)
        and can also be combined 
        i.e. `<prefix>mute <@id> 1 day 6 hours`.
        Alternatively, use `until` to set end of mute to a specific time via UNIX timestamp,
        i.e. `<prefix>mute <@id> until 1735771908`.
        """
        if len(args) < 1:
            await ctx.send("Error: Missing arguments.")
            return

        # TIMEOUT ENABLED?

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
            await ctx.send(f"Enable timeout system before muting users this way.\nUse `{self.prefix}help set timeout` for more info.")
            return

        # FETCH USER ID / MEMBER OBJECT

        try:
            user_id, rest = await util.fetch_id_from_args("user", "all", args)
        except:
            await ctx.send("Error while trying to fetch user.")
            return

        immunity_list = await self.get_immunitylist(ctx)

        if user_id in immunity_list:
            pleademoji = util.emoji("pleading")
            await ctx.send(f'I- I really do not want to mute this user. {pleademoji}')
            return
        else:
            try:
                the_member = ctx.guild.get_member(int(user_id))
            except:
                await ctx.channel.send(f'Error while trying to fetch member.')
                return

        # FETCH TIME

        try:
            now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())
            timeseconds, timetext, reason = await util.timeparse(rest, now)
        except Exception as e:
            await ctx.send(f"Error while trying to fetch time: {e}")
            return

        if timeseconds != "infinity":
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

        if timeseconds == "infinity":
            utc_timestamp = "none"
        else:
            utc_now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds()) 
            utc_timestamp = str(utc_now + int(timeseconds))

        con = sqlite3.connect(f'databases/timetables.db')
        cur = con.cursor()
        cur.execute("INSERT INTO timeout VALUES (?, ?, ?, ?)", (username, user_id, utc_timestamp, role_id_liststr))
        con.commit()
        await util.changetimeupdate()

        # CHECK ROLES WHETHER TO DM LATER

        send_msg_bool = await self.penaltynotifier(ctx, user_id)

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

        if reason == "":
            reason_string = ""
        else:
            reason_string = "\nReason: " + reason

        if timeseconds == "infinity":
            description = f"Muted <@{user_id}> indefinitely. {muteemoji}"
        else:
            description = f"Muted <@{user_id}> for {timetext}. {muteemoji}"
        description += reason_string
        header = "Timeout"
        embed=discord.Embed(title=header, description=description, color=0xB80F0A)
        await ctx.send(embed=embed)

        # DM THE USER

        if send_msg_bool:
            try:
                user = await self.bot.fetch_user(int(user_id))
                if timeseconds == "infinity":
                    timespec = ""
                else:
                    timespec = f" for {timetext}"
                message = f"You have been muted in {ctx.guild.name}{timespec}."
                message +=  reason_string
                embed=discord.Embed(title="", description=message, color=0xB80F0A)
                await user.send(embed=embed)
                print("Successfully notified user.")
            except Exception as e:
                print("Error while trying to DM muted user:", e)

    @_mute.error
    async def mute_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='unmute', aliases = ['unusermute','unsilence'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _unmute(self, ctx: commands.Context, *args):
        """🔒 Unmutes user
        
        1st argument needs to be user id or @user mention.
        """
        if len(args) < 1:
            await ctx.send("Error: Missing arguments.")
            return

        # TIMEOUT ENABLED?

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
            await ctx.send(f"Timeout functionality was turned off. Enable timeout system to use `{self.prefix}mute` and `{self.prefix}unmute`.\nUse `{self.prefix}help set timeout` for more info.")
            return

        async with ctx.typing():

            # FETCHING MEMBER

            try:
                user_id, reason = await util.fetch_id_from_args("user", "first", args)
            except:
                await ctx.send("Error with provided user id.")
                return

            try:
                the_member = ctx.guild.get_member(int(user_id))
            except:
                await ctx.channel.send(f'Error while trying to fetch member.')
                return

            # FETCHING OLD ROLE IDS FROM DATABASE

            try:
                con = sqlite3.connect(f'databases/timetables.db')
                cur = con.cursor()
                role_id_liststr = [item[0] for item in cur.execute("SELECT role_id_list FROM timeout WHERE userid = ?", (user_id,)).fetchall()][-1]
                cur.execute("DELETE FROM timeout WHERE userid = ?", (user_id,))
                con.commit()
                await util.changetimeupdate()
            except Exception as e:
                print(f"Error while trying to fetch old roles before timeout: {e}")
                try:
                    con = sqlite3.connect(f'databases/botsettings.db')
                    cur = con.cursor()
                    accesswall_status = [item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("access wall",)).fetchall()][0]
                    if accesswall_status == "on":
                        verified_id = [item[0] for item in cur.execute("SELECT role_id FROM specialroles WHERE name = ?", ("verified role",)).fetchall()][0]
                        role_id_liststr = f"[{verified_id}]"
                        await ctx.send(f"Issue while trying to fetch old roles from Timeout database: Giving user at least verified role.\n...continuing unmute...")
                    else:
                        role_id_liststr = ""
                        await ctx.send(f"Issue while trying to fetch old roles from Timeout database: No roles to assign back.\n...continuing unmute anyway...")
                except Exception as e:
                    print(e)
                    role_id_liststr = ""
                    await ctx.send(f"Problem while trying to fetch old roles from Timeout database: No roles to assign back.\n...continuing unmute anyway...")

            role_id_list = role_id_liststr.replace("[","").replace("]","").replace(" ","").split(",")
            while '' in role_id_list:
                role_id_list.remove('')

            # FETCHING ROLE OBJECTS

            try:
                con = sqlite3.connect(f'databases/botsettings.db')
                cur = con.cursor()
                timeoutrole_id = int([item[0] for item in cur.execute("SELECT role_id FROM specialroles WHERE name = ?", ("timeout role",)).fetchall()][0])
                #try:
                #    verified_role_id = int([item[0] for item in cur.execute("SELECT role_id FROM specialroles WHERE name = ?", ("verified role",)).fetchall()][0])
                #except:
                #    verified_role_id = "undefined"
                for role in ctx.guild.roles:
                    if role.id == timeoutrole_id:
                        timeout_role = role
                        break 
                else:
                    await ctx.send(f"Error: Could not find Timeout role.")
                    return
            except Exception as e:
                print(f"Error: {e}")
                await ctx.send(f"Error while trying to find Timeout role.")
                return

            old_roles_list = []
            all_roles = [r for r in ctx.guild.roles]
            for role_id in role_id_list:
                if int(role_id) not in [ctx.guild.id, timeoutrole_id]: #ignore @everyone role and timeout role
                    try:
                        r_id = int(role_id)
                        for role in all_roles:
                            if role.id == r_id:
                                old_roles_list.append(role)
                                break 
                        else:
                            print(f"Error: role with id {role_id} not found")
                    except:
                        print(f"Error: role has faulty id: {role_id}")

            if timeout_role not in the_member.roles:
                emoji = util.emoji("think")
                await ctx.send(f"User was not muted. {emoji}")
                return

            # END TIMEOUT: SWAPPING ROLES

            try:
                await the_member.edit(roles=old_roles_list)
            except:
                await the_member.remove_roles(timeout_role)
                if len(old_roles_list) > 0:
                    for r in old_roles_list:
                        if r.id != ctx.guild.id: #ignore @everyone role
                            try:
                                await the_member.add_roles(r)
                            except:
                                print(f"Error with: {r}, {r.id}")

            emoji = util.emoji("unleashed_mild")
            description = f"Unmuted <@{user_id}>. {emoji}"
            header = "Timeout ended"
            embed=discord.Embed(title=header, description=description, color=0x4CBB17)
            await ctx.send(embed=embed)

    @_unmute.error
    async def unmute_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='batchban', aliases = ['userbatchban'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _batchban(self, ctx, *args):
        """🔒 Bans multiple users
        
        Use `<prefix>batchban <optional: reason>` and attach a txt file with 1 id per row.

        (Users banned via batchban do not receive a notification even if the penalty notifer is enabled and they are full members, i.e. are verified/have community role etc. depending on settings.)
        """
        attachment_url = ctx.message.attachments[0].url
        file_request = requests.get(attachment_url)

        file_content = file_request.text 
        id_list = file_content.split("\n")

        reason = ' '.join(args[0:])

        successful_bans = []
        unsuccessful = []

        immunity_list = await self.get_immunitylist(ctx)

        for uid in id_list:
            user_id = uid.strip()

            if user_id in immunity_list:
                unsuccessful.append(user_id)
            else:
                try:
                    user = await self.bot.fetch_user(user_id)
                    await ctx.guild.ban(user, reason=reason, delete_message_days=0)
                    successful_bans.append(user_id)
                except:
                    unsuccessful.append(user_id)

        unsuccessful = list(dict.fromkeys(unsuccessful))
        successful_bans = list(dict.fromkeys(successful_bans))
        await ctx.send(f"Batch ban finished.\nSuccessfully banned: {len(successful_bans)}\nUnsuccsessful attempts: {len(unsuccessful)}")
        if len(unsuccessful) > 0:
            print(unsuccessful)
            string_unsuccessful = '\n'.join(unsuccessful)
            await ctx.send(f"IDs of unsuccessful attempts:\n{string_unsuccessful}"[:4096])
    @_batchban.error
    async def batchban_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='purge', aliases = ['delmsg'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _purge(self, ctx: commands.Context, *args):
        """🔒 Deletes given number of messages from channel (Limit 100)
        
        Use i.e. `<prefix>purge 5`

        Specify argument `nonbulk` or `nb` for short, so messages are deleted one by one. This will help if you have message deletion notification enabled, so all messages are shown in the botspam channel.
        Note that non-bulk purges can also delete messages older than 14 days (and the limit is raised to 1000). The default purge cannot do that.

        Specify argument(s) @user mention or user ID, so only messages of that user(s) will be deleted (the given number reflects the number of messages checked, not messages deleted then!)
        """
        def is_specified(m):
            return (m.author.id in user_specified)

        # PARSE SPECIFIER ARGUMENTS

        arguments = []
        for arg in args:
            arguments.append(arg.lower().strip())

        nonbulk = False
        if "nonbulk" in arguments:
            arguments.remove("nonbulk")
            nonbulk = True
        elif "nb" in arguments:
            arguments.remove("nb")
            nonbulk = True
        elif "non-bulk" in arguments:
            arguments.remove("non-bulk")
            nonbulk = True

        user_specified = []
        arguments2 = []
        for arg in arguments:
            if arg.startswith("<@") and arg.endswith(">"):
                arg2 = arg[2:-1]
            else:
                arg2 = arg

            if len(arg2) > 17 and util.represents_integer(arg2):
                try:
                    user_id = int(arg2)
                    user_specified.append(user_id)
                except Exception as e:
                    print("Error:", e)

            else:
                arguments2.append(arg)

        if len(args) == 0:
            await ctx.send("Command needs integer argument.")
            return

        await ctx.message.delete()

        # PARSE NUMBER ARGUMENT

        try:
            limit = int(arguments2[0])

            if nonbulk:
                if limit > 1000:
                    limit = 1000
                    print("reduced amount to 1000")
            else:
                if limit > 100:
                    limit = 100
                    print("reduced amount to 100")
            if limit < 1:
                raise ValueError("Limit must be an integer > 0.")
        except  Exception as e:
            print("Error:", e)
            await ctx.send("Error with given integer argument.")
            return

        # FETCH AND DELETE

        if nonbulk and len(user_specified) == 0:
            messages = [msg async for msg in ctx.channel.history(limit=limit)]
            for message in reversed(messages):
                await message.delete()
            print("non-bulk delete: done")

        elif nonbulk:
            messages = [msg async for msg in ctx.channel.history(limit=limit) if (msg.author.id in user_specified)]
            for message in reversed(messages):
                await message.delete()
            print("user specified non-bulk delete: done")
            print(user_specified)

        elif len(user_specified) == 0:
            await ctx.channel.purge(limit=limit)
            print("bulk delete: done")

        else:
            await ctx.channel.purge(limit=limit, check = is_specified)
            print("user specified bulk delete: done")
            print(user_specified)

    @_purge.error
    async def purge_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='verify', aliases = ['verifying'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _verify(self, ctx: commands.Context, *args):
        """🔒 Verifies user
        
        Use `<prefix>verify <user_id or @mention>` to remove gate-role, add verified-role and put a welcome message in general channel.
        You can put as additional argument "nomsg" to leave out the last step and verify them without a welcome message.
        """
        if len(args) < 1:
            emoji = util.emoji("pout")
            await ctx.send(f"Error: Missing arguments. {emoji}")
            return

        if len(args) > 1:
            specification = args[1]
        else:
            specification = ""

        additional_notes = ""

        # CHECK ACCESS WALL STATUS

        try:
            con = sqlite3.connect(f'databases/botsettings.db')
            cur = con.cursor()
            accesswall_status = [item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("access wall",)).fetchall()][0]
        except:
            await ctx.send(f"Error with access wall status in database.\nStill continue? (type `yes` to proceed or `no` to cancel)")
            try: # waiting for message
                async with ctx.typing():
                    response = await self.bot.wait_for('message', check=check, timeout=30.0) # timeout - how long bot waits for message (in seconds)
            except asyncio.TimeoutError: # returning after timeout
                await ctx.send("action timed out")
                return

            # if response is different than yes / y - return
            if response.content.lower() not in ["yes", "y"]:
                await ctx.send("cancelled action")
                return
            else:
                accesswall_status = "yes"
                additional_notes += "-check on accesswall status\n"

        if accesswall_status == "no":
            await ctx.send("Access wall is turned off. Enable via `-set accesswall on`.")
            return

        # FETCH USER

        try:
            user_id, reason = await util.fetch_id_from_args("user", "first", args)
        except:
            await ctx.send("Error while trying to fetch user ID.")
            return

        try:
            user = ctx.guild.get_member(int(user_id))
        except:
            await ctx.channel.send(f'Error while trying to fetch member.')
            return

        # FETCH ROLES
        
        try:
            verified_role_id = int([item[0] for item in cur.execute("SELECT role_id FROM specialroles WHERE name = ?", ("verified role",)).fetchall()][0])
            wintersgate_role_id = int([item[0] for item in cur.execute("SELECT role_id FROM specialroles WHERE name = ?", ("access wall role",)).fetchall()][0])
            verified_role = discord.utils.get(ctx.guild.roles, id = verified_role_id)
            wintersgate_role = discord.utils.get(ctx.guild.roles, id = wintersgate_role_id)
        except Exception as e:
            print(e)
            await ctx.channel.send(f'Error while trying to fetch roles.')
            return

        try:
            botspamchannel_id = int([item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("botspam channel id",)).fetchall()][0])
            botspam_channel = self.bot.get_channel(botspamchannel_id)
        except Exception as e:
            print(f"Error while trying to fetch bot spam channel: {e}")
            botspam_channel = ctx.channel
            additional_notes += "-check on botspam channel id in database\n"

        if wintersgate_role in user.roles:
            await user.remove_roles(wintersgate_role)
        else:
            print("User did not have the Winter's Gate role.")
            emoji = util.emoji("shrug")
            await botspam_channel.send(f"{user.display_name} did not have `Winter's Gate` role. {emoji}")

        # SWAP ROLES

        if verified_role in user.roles:
            newly_verified = False
            print("User already has verified role.")
            emoji = util.emoji("think_smug")
            await botspam_channel.send(f"{user.display_name} did already have the `Verified` role. {emoji}")
        else:
            newly_verified = True
            await user.add_roles(verified_role)

        await ctx.channel.send(f'Verified {user.display_name}!')

        # WELCOME MESSAGE

        if specification.lower() in ["nomsg", "no msg", "nomessage", "no message", "nom"]:
            await botspam_channel.send(f'Verified <@{user_id}> without welcome message.')
        else:
            if newly_verified:
                welcomemessage_list = [item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("welcome message",)).fetchall()]
                if len(welcomemessage_list) != 1:
                    if len(welcomemessage_list) == 0:
                        welcome = "off"
                        additional_notes += "-no welcome message settings in database\n"
                    else:
                        welcome = welcomemessage_list[0]
                        additional_notes += "-multiple welcome message settings in database\n"
                else:
                    welcome = welcomemessage_list[0]

                if welcome == "on":
                    try:
                        generalchannel_id = int([item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("general channel id",)).fetchall()][0])
                        general_channel = self.bot.get_channel(generalchannel_id)
                    except Exception as e:
                        print(e)
                        general_channel = ctx.channel
                        additional_notes += "-check on general channel id in database\n"

                    welcometext_list = [item[0].strip() for item in cur.execute("SELECT etc FROM serversettings WHERE name = ?", ("welcome message",)).fetchall()]
                    while "" in welcometext_list:
                        welcometext_list.remove("")
                    if len(welcometext_list) == 0 or welcometext_list[0].strip() == "":
                        #default
                        yayemoji = util.emoji("yay")
                        excitedemoji = util.emoji("excited_alot")
                        welcometext = f'Welcome <@{user_id}>! {yayemoji}\nYou made it {excitedemoji}'
                    else:
                        welcometext_preparse = welcometext_list[0]
                        welcometext = await util.customtextparse(welcometext_preparse, user_id)
                    await general_channel.send(welcometext)
                else:
                    print("welcome message turned off")
            else:
                emoji = util.emoji("derpy_playful")
                await ctx.channel.send(f'{user.display_name} was already verified. Uh... welcome anyway? {emoji}')

            if additional_notes != "":
                await botspam_channel.send(f"@MODS There were errors that need inspection:\n{additional_notes}")
    @_verify.error
    async def verify_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='verifyall', aliases = ['verifyingall'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _verifyall(self, ctx: commands.Context, *args):
        """🔒 Verifies all members
        
        If newly setting up an access wall, this comes in handy to verify all users who were already members before.
        """

        # FETCH ROLE

        try:
            verified_role_id = int([item[0] for item in cur.execute("SELECT role_id FROM specialroles WHERE name = ?", ("verified role",)).fetchall()][0])
            verified_role = discord.utils.get(ctx.guild.roles, id = verified_role_id)
        except Exception as e:
            print(e)
            await ctx.channel.send(f'Error while trying to fetch verified role.')
            return

        # CONFIRMATION

        async with ctx.typing():

            await ctx.send("Are you sure you want to give the verified role to all current members? Respond with `yes` to confirm.")

            try: # waiting for message
                response = await self.bot.wait_for('message', check=check, timeout=30.0) # timeout - how long bot waits for message (in seconds)
            except asyncio.TimeoutError: # returning after timeout
                await ctx.send("action timed out")
                return

            # if response is different than yes / y - return
            if response.content.lower() not in ["yes", "y"]:
                await ctx.send("cancelled action")
                return

            # ASSIGN

            for member in ctx.guild.members:
                if verified_role not in member.roles:
                    await member.add_roles(verified_role)

        await ctx.send("Finished assigning role to everyone.")

    @_verifyall.error
    async def verifyall_error(self, ctx, error):
        await util.error_handling(ctx, error)




    @commands.command(name='yeetaccesswall', aliases = ['yeetaw', 'awyeet', 'clearaccesswall', 'clearaw', 'awclear', 'purgeaccesswall', 'purgeaw', 'awpurge', 'winterspurge', 'gatepurge', 'wintersyeet'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _winterspurge(self, ctx: commands.Context, *args):
        """🔒 Kick accesswall dwellers

        Use `<prefix>yeetaw <number>` to kick all users who are for at least <number> days in access wall channel without being verified.
        Without a specified <number> the bot will assume <number>=7.
        """

        # CHECK ACCESS WALL STATUS

        try:
            con = sqlite3.connect(f'databases/botsettings.db')
            cur = con.cursor()
            accesswall_status = [item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("access wall",)).fetchall()][0]
        except:
            await ctx.send(f"Error with access wall status in database.")
            return

        if accesswall_status == "no":
            await ctx.send(f"Access wall is turned off. Enable via `{self.prefix}set accesswall on`.")
            return

        # INITIALISE NUMBER OF DAYS

        if len(args) == 0:
            day_threshold = 7
        else:
            arg1 = args[0]

            try:
                day_threshold = float(arg1)
            except:
                day_threshold = 7
                await ctx.send("argument is not a number, setting 7 days")

            if day_threshold < 0:
                day_threshold = 7
                await ctx.send("argument is negative, setting 7 days")

        # FETCH ROLES

        server = ctx.message.guild
        roles_found = True
        try:
            wintersgate_role_id = int([item[0] for item in cur.execute("SELECT role_id FROM specialroles WHERE name = ?", ("access wall role",)).fetchall()][0])
            wintersgate_role = discord.utils.get(server.roles, id = wintersgate_role_id)
        except Exception as e:
            print(e)
            await ctx.send("Winter's Gate role not found :(")
            roles_found = False
        try:
            verified_role_id = int([item[0] for item in cur.execute("SELECT role_id FROM specialroles WHERE name = ?", ("verified role",)).fetchall()][0])
            verified_role = discord.utils.get(server.roles, id = verified_role_id)
        except Exception as e:
            print(e)
            await ctx.send("Verified role not found :(")
            roles_found = False
        
        # FETCH MEMBERS TO YEET

        if roles_found:

            # filter for users that have WG role (and those who also have verified role)
            memberlist = ctx.guild.members
            WG_members = []
            verified_WG_members = []
            WG_members_younger = []

            for member in memberlist:
                if wintersgate_role in member.roles:

                    # check join_duration
                    try:
                        app_id = str(self.application_id)
                        device_timezone = [item[0] for item in cur.execute("SELECT type FROM botsettings WHERE name = ? AND value = ?", ("app id", app_id)).fetchall()][0]
                        timenow_object = pytz.timezone(device_timezone)
                    except Exception as e:
                        print(e)
                        try:
                            device_timezone = str(get_localzone())
                            timenow_object = pytz.timezone(device_timezone)
                        except Exception as e:
                            print(e)
                            device_timezone = 'Europe/Berlin'
                            timenow_object = pytz.timezone(device_timezone)
                        
                    duration = (datetime.datetime.now(timenow_object) - member.joined_at).total_seconds()/(24 * 3600)
                    print(f"{str(member)} joined {duration} days ago")

                    if duration > day_threshold:
                        if verified_role in member.roles:
                            verified_WG_members.append(member)
                        else:
                            WG_members.append(member)
                    else:
                        WG_members_younger.append(member)

            # KICK UNVERIFIED ACCESS WALL DWELLERS

            reason = f"not introducing for over {day_threshold} days"
            immunity_list = await self.get_immunitylist(ctx)

            for member in WG_members:
                user_id = member.id

                if user_id in immunity_list:
                    pleademoji = util.emoji("pleading")
                    await ctx.send(f'I- I really do not want to yeet <@{user_id}>. {pleademoji}')
                else:
                    try:
                        await ctx.guild.kick(member, reason=reason)
                        gunemoji = util.emoji("gun")
                        try:
                            user_name = member.name
                        except:
                            user_name = "?"
                        await ctx.send(f'Yeeted `{user_name}`/<@{user_id}> (for {reason}) {gunemoji}')
                        print(f"yeeted {str(member)}")
                    except:
                        emoji = util.emoji("hold_head")
                        await ctx.send(f'Error while trying to yeet {member.display_name} ({str(member)}) {emoji}')
            
            # NOTIFY ABOUT NOT KICKED USER
            
            if len(WG_members_younger) + len(verified_WG_members) == 0:
                print(f"no anomalies or members that have been less than {day_threshold} days in winters gate")
            else:
                title_young = f"Users who haven't been here for {day_threshold} days"
                title_anomaly = f"Anomalies with users who have both Access Wall and Verified role"
                youngermembers_string = ""
                anomalies_string = ""
                for member in WG_members_younger:
                    youngermembers_string += member.mention + "\n"
                for member in verified_WG_members:
                    anomalies_string += member.mention + "\n"

                embed = discord.Embed(title='Not yeeted', color=0x000000)
                if len(WG_members_younger) > 0:
                    embed.add_field(name=title_young, value=youngermembers_string[:1024], inline=False)
                if len(verified_WG_members) > 0:
                    embed.add_field(name=title_anomaly, value=anomalies_string[:1024], inline=False)
                await ctx.send(embed=embed)

    @_winterspurge.error
    async def winterspurge_error(self, ctx, error):
        await util.error_handling(ctx, error)



    ##################################################################################



    @commands.command(name='userinfo', aliases = ['memberinfo'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _userinfo(self, ctx: commands.Context, *args):
        """🔒 Show info about user

        has to be a member of the server
        """

        user = await util.fetch_member_tryloop(ctx, args)

        if user is None:
            emoji = util.emoji("sad")
            await ctx.send(f"Could not find such a member. {emoji}")
            return

        roles = user.roles[-1:0:-1]
        names = list(dict.fromkeys([str(user.name), str(user.display_name), str(user.nick)]))

        while "" in names:
            names.remove("")

        while "None" in names:
            names.remove("None")

        joined_at = user.joined_at
        since_created = (ctx.message.created_at - user.created_at).days
        if joined_at is not None:
            since_joined = (ctx.message.created_at - joined_at).days
            user_joined = joined_at.strftime("%d %b %Y %H:%M")
        else:
            since_joined = "?"
            user_joined = _("Unknown")
        user_created = user.created_at.strftime("%d %b %Y %H:%M")
        voice_state = user.voice
        member_number = (
            sorted(ctx.guild.members, key=lambda m: m.joined_at or ctx.message.created_at).index(user)
            + 1
        )

        created_on = ("{}\n({} days ago)").format(user_created, since_created)
        joined_on = ("{}\n({} days ago)").format(user_joined, since_joined)

        if roles:
            role_str = ", ".join([x.mention for x in roles])
            # 400 BAD REQUEST (error code: 50035): Invalid Form Body
            # In embed.fields.2.value: Must be 1024 or fewer in length.
            if len(role_str) > 1024:
                # Alternative string building time.
                # This is not the most optimal, but if you're hitting this, you are losing more time
                # to every single check running on users than the occasional user info invoke
                # We don't start by building this way, since the number of times we hit this should be
                # infintesimally small compared to when we don't across all uses of Red.
                continuation_string = (
                    "and {numeric_number} more roles not displayed due to embed limits."
                )
                available_length = 1024 - len(continuation_string)  # do not attempt to tweak, i18n

                role_chunks = []
                remaining_roles = 0

                for r in roles:
                    chunk = f"{r.mention}, "
                    chunk_size = len(chunk)

                    if chunk_size < available_length:
                        available_length -= chunk_size
                        role_chunks.append(chunk)
                    else:
                        remaining_roles += 1

                role_chunks.append(continuation_string.format(numeric_number=remaining_roles))

                role_str = "".join(role_chunks)
        else:
            role_str = None

        activity_list = []
        i = 0
        for activity in user.activities:
            i += 1
            string = util.cleantext2(activity.name)
            activity_list.append(string)

        status = ', '.join(activity_list)

        if status.strip() == "":
            status = "None"

        data = discord.Embed(description=f"Status: {status}", colour=user.colour)
            
        data.add_field(name=("Joined Discord on"), value=created_on)
        data.add_field(name=("Joined this server on"), value=joined_on)
        if role_str is not None:
            data.add_field(name=("Roles"), value=role_str, inline=False)
        if names:
            val = ", ".join(names)
            data.add_field(name=("Names"), value=val, inline=False)

        data.set_footer(text=("Member #{} | User ID: {}").format(member_number, user.id))

        name = str(user)
        name = " ~ ".join((name, user.nick)) if user.nick else name

        if user.avatar:
            data.set_author(name=f"{user.display_name}'s user info" , icon_url=user.avatar)
            data.set_thumbnail(url=user.avatar)
        else:
            data.set_author(name=name)

        await ctx.send(embed=data)

    @_userinfo.error
    async def userinfo_error(self, ctx, error):
        await util.error_handling(ctx, error) 



    @commands.command(name='booststatus', aliases = ['boosts'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _booststatus(self, ctx: commands.Context, *args):
        """🔒 Shows boost status

        shows number of boosts as well as the donors
        """
        server = ctx.guild
        boosts = server.premium_subscription_count
        donors = server.premium_subscribers

        if boosts >= 14:
            level = 3
        elif boosts >= 7:
            level = 2
        elif boosts >= 2:
            level = 1
        else:
            level = 0

        description = f"Number of boosts: **{boosts}**\nLevel (w/o perks): {level}"

        if boosts > 0:
            donor_mentions = []
            for donor in donors:
                donor_mentions.append(f"<@{donor.id}> ({donor.name})")
            description += f"\n\nServer booster(s):\n" + ", ".join(donor_mentions)

        embed = discord.Embed(title=f"Boost status of {server.name}", description=description, colour=0xf47fff)
        embed.set_thumbnail(url="https://i.imgur.com/5DJaIX2.png")

        await ctx.send(embed=embed)

    @_booststatus.error
    async def booststatus_error(self, ctx, error):
        await util.error_handling(ctx, error) 

    ###########################################################################################################################################



    def checkfile(self, filename):
        """returns True if .db file is readable"""
        if filename.endswith(".db"):
            try:
                con = sqlite3.connect(f'databases/{filename}')
                cur = con.cursor()  
                table_list = [item[0] for item in cur.execute("SELECT name FROM sqlite_master WHERE type = ?", ("table",)).fetchall()]
                #print(table_list)
                try:
                    for table in table_list:
                        cursor = con.execute(f'SELECT * FROM [{table}]')
                        column_names = list(map(lambda x: x[0], cursor.description))
                        #print(column_names)
                        try:
                            item_list = [item[0] for item in cur.execute(f"SELECT * FROM [{table}] ORDER BY {column_names[0]} ASC LIMIT 1").fetchall()]
                            #print(item_list)
                        except Exception as e:
                            print(f"Error with {filename} table {table} query:", e)
                            return False
                except Exception as e:
                    print(f"Error with {filename} table {table} structure:", e)
                    return False
            except Exception as e:
                print(f"Error with {filename}:", e)
                return False

            return True

        else:
            raise ValueError("Not a .db file!")



    @commands.command(name='troubleshoot', aliases = ['trouble','troubles'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _troubleshoot(self, ctx: commands.Context, *args):
        """🔒 Looks for problems and solutions with the database files"""

        broken_files = []

        for filename in os.listdir(f"{sys.path[0]}/databases/"):
            if filename.endswith(".db"):
                if self.checkfile(filename):
                    pass
                else:
                    broken_files.append(filename)

        if len(broken_files) == 0:
            await ctx.send("No errors detected. All available database files seem to be readable.")

        else:
            async with ctx.typing():
                await ctx.send(f"Issues detected. Looking for solutions...")

                try:
                    botspam_channel_id = int(os.getenv("bot_channel_id"))     
                    botspamchannel = await self.bot.fetch_channel(botspam_channel_id)

                    now = int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds())
                    last_occurence = 0
                    reached_end = False
                    async for msg in botspamchannel.history(limit=300):
                        if reached_end:
                            break
                        if "`LAST ACTIVE`" in msg.content and msg.author.bot:
                            try:
                                timestamp = int(msg.content.split("last edited: <t:")[1].split(":f> i.e. <t:")[0])
                                if timestamp > last_occurence:
                                    last_occurence = timestamp
                                    the_message = msg
                                    
                                    # CHECK FILES AND TRY
                                    
                                    if str(the_message.attachments) == "[]":
                                        print("Error: No attachment in `LAST ACTIVE` message.")
                                    else:
                                        print("...clearing space and retrieving files")
                                        for filename in os.listdir(f"{sys.path[0]}/temp/"):
                                            if filename.endswith(".db"): # gitignore and other things that might be happening in parallel
                                                os.remove(f"{sys.path[0]}/temp/{filename}")
                                        split_v1 = str(the_message.attachments).split("filename='")[1]
                                        filename = str(split_v1).split("' ")[0]
                                        if filename.endswith(".zip"): # Checks if it is a .zip file
                                            await the_message.attachments[0].save(fp="temp/re_{}".format(filename))
                                            continue_with_this = True

                                            # CHECK FILE EXTENSIONS

                                            with zipfile.ZipFile(f"{sys.path[0]}/temp/re_{filename}", 'r') as zip_ref:
                                                filename_list = zip_ref.namelist()
                                                for name in filename_list:
                                                    if name.endswith(".db") or name.endswith(".txt"):
                                                        pass
                                                    else:
                                                        print("Error with ZIP file, contained stuff other than .db and .txt files")
                                                        continue_with_this = False

                                                # EXTRACT FILES
                                                if continue_with_this:
                                                    zip_ref.extractall(f"{sys.path[0]}/temp/")

                                            # SWAP BROKEN FILES
                                            if continue_with_this:
                                                for filename in broken_files:
                                                    if filename.endswith(".db"):
                                                        if self.checkfile(filename):
                                                            dbExist = os.path.exists(f"{sys.path[0]}/databases/{filename}")
                                                            if dbExist:
                                                                os.remove(f"{sys.path[0]}/databases/{filename}")
                                                            os.replace(f"{sys.path[0]}/temp/{filename}", f"{sys.path[0]}/databases/{filename}")

                                                            while filename in broken_files:
                                                                broken_files.remove(filename)

                                                            await ctx.send(f"Fixed {filename} with backup from <t:{timestamp}:f>.")

                                                            if len(broken_files) == 0:
                                                                reached_end = True

                                            for filename in os.listdir(f"{sys.path[0]}/temp/"):   
                                                if filename.endswith(".db"): # gitignore and other things that might be happening in parallel            
                                                    os.remove(f"{sys.path[0]}/temp/{filename}")

                            except Exception as e:
                                print("Error with backup:", e)

                    for filename in os.listdir(f"{sys.path[0]}/temp/"):   
                        if filename.endswith(".db"):          
                            os.remove(f"{sys.path[0]}/temp/{filename}")

                    if len(broken_files) > 0:
                        text = ', '.join(broken_files)
                        await ctx.send(f"The following databases could not be fixed automatically:\n{text}\n\nPut the backup files you want as replacement in a .zip folder and upload it with `{self.prefix}loadbackup` to replace the files.\n______")
                        response = await util.are_you_sure_msg(ctx, self.bot, "In case there are no suitable backup files: Do you want to delete the corrupted files?\nSkip with `no`.")

                        if response:
                            for filename in broken_files:
                                try:
                                    os.remove(f"{sys.path[0]}/databases/{filename}")
                                except:
                                    pass
                            await ctx.send(f"Removed corrupted files. Please use `{self.prefix}update` now.")
                    else:
                        await ctx.send("Done.")

                except:
                    text = ', '.join(broken_files)
                    await ctx.send(f"It seems like the following database files are corrupted and need to be replaced with an older variant:\n{text}\n\nPut the backup files you want as replacement in a .zip folder and upload it with `{self.prefix}loadbackup` to replace the files.\n______")
                    response = await util.are_you_sure_msg(ctx, self.bot, "In case there are no suitable backup files: Do you want to delete the corrupted files?\nSkip with `no`.")

                    if response:
                        for filename in broken_files:
                            try:
                                os.remove(f"{sys.path[0]}/databases/{filename}")
                            except:
                                pass
                        await ctx.send(f"Removed corrupted files. Please use `{self.prefix}update` now.")

    @_troubleshoot.error
    async def troubleshoot_error(self, ctx, error):
        await util.error_handling(ctx, error)




async def setup(bot: commands.bot) -> None:
    await bot.add_cog(
        Administration_of_Server(bot),
        guilds = [discord.Object(id = int(os.getenv("guild_id")))])