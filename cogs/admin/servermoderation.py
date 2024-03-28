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
                print("Error while trying to DM muted user:", e)
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
                print("Error while trying to DM muted user:", e)

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
        Write `-mute <@id>` to mute a user indefinitely.
        Write `-mute <@id> <time>` to mute user for given time, where <time> has to be in the format: <integer><unit>

        *Valid time units are: min, hour(s), day(s), week(s), month(s)
        and can also be combined 
        i.e. `-mute <@id> 1 day 6 hours`.
        Alternatively, use `until` to set end of mute to a specific time via UNIX timestamp,
        i.e. `-mute <@id> until 1735771908`.
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
            user_id, rest = await util.fetch_id_from_args("user", "first", args)
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
        
        Use `-batchban <optional: reason>` and attach a txt file with 1 id per row.

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



    @commands.command(name='verify', aliases = ['verifying'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _verify(self, ctx: commands.Context, *args):
        """🔒 Verifies user
        
        Use `-verify <user_id or @mention>` to remove gate-role, add verified-role and put a welcome message in general channel.
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

                    welcometext_list = [item[0].strip() for item in cur.execute("SELECT details FROM serversettings WHERE name = ?", ("welcome message",)).fetchall()]
                    while "" in welcometext_list:
                        welcometext_list.remove("")
                    if len(welcometext_list) == 0 or welcometext_list[0].strip() == "":
                        #default
                        yayemoji = util.emoji("yay")
                        excitedemoji = util.emoji("excited_alot")
                        welcometext = f'Welcome <@{user_id}>! {yayemoji}\nYou made it {excitedemoji}'
                    else:
                        welcometext_preparse = welcometext_list[0]
                        welcometext = await util.customtextparse(welcometext_preparse, userid)
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

        Use `-yeetaw <number>` to kick all users who are for at least <number> days in access wall channel without being verified.
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
                        await ctx.send(f'Yeeted <@{user_id}> (for {reason}) {gunemoji}')
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




    @commands.command(name='troubleshoot', aliases = ['trouble','troubles'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _troubleshoot(self, ctx: commands.Context, *args):
        """🔒 Looks for problems and solutions with the database files"""

        # FIND CORRUPTED DBs
        # >>>>>>> SELECT * FROM dbname.sqlite_master WHERE type='table';
        # >>>>>>> PRAGMA table_info(table_name);
        # SEARCH FOR BACKUP FILE WITH WORKING DB FILE
        # IF NOT ASK TO DELETE AND CREATE NEW
        await ctx.send("under construction")
    @_troubleshoot.error
    async def troubleshoot_error(self, ctx, error):
        await util.error_handling(ctx, error)




async def setup(bot: commands.bot) -> None:
    await bot.add_cog(
        Administration_of_Server(bot),
        guilds = [discord.Object(id = int(os.getenv("guild_id")))])