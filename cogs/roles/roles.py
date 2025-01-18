# COG FOR ROLE RELATED COMMANDS



import os
import datetime
import discord
from discord.ext import commands
import asyncio
import re
import sqlite3
from emoji import UNICODE_EMOJI
from other.utils.utils import Utils as util


class Roles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.prefix = os.getenv("prefix")


    ###############################################################################################################


    async def role_assigning(self, ctx, args, assigning):
        if len(args) < 1:
            await ctx.send("Error: Command needs a role argument.")
            return

        # CHECK IF MOD

        for perms in ctx.message.author.guild_permissions:
            if perms[0] == "manage_guild":
                if perms[1]:
                    is_mod = True
                else:
                    is_mod = False
                break
        else:
            print("Error: Something is wrong with permission manage_guild.")
            is_mod = False


        # CHECK VALIDITY OF ROLE ARG(S)
        # check these first so integers are treated as role ids, and not user ids

        role_list = []
        errors_roles_general = []
        try: 
            # CHECK FOR ROLE IDS OR MENTIONS
            role_ids, remainder_args_string = await util.fetch_id_from_args("role", "multiple", args)
            remainder_args = remainder_args_string.split()
            role_id_list = role_ids.split(";")
            for role_id in role_id_list:
                try:
                    the_role = discord.utils.get(ctx.guild.roles, id = int(role_id))
                    role_list.append(the_role)
                except:
                    errors_roles_general.append(role_id)

        except:
            # CHECK FOR ROLE NAMES
            remainder_args = []
            pre_role_string_list = []
            for arg in args:
                if arg.startswith("<@") and arg.endswith(">"):
                    pre_role_string_list.append(";")
                    remainder_args.append(arg)
                else:
                    pre_role_string_list.append(arg)

            role_string = ' '.join(pre_role_string_list)
            role_name_split = role_string.split(";")

            for term in role_name_split:
                if term.strip() == "":
                    pass
                else:
                    try:
                        the_role = await util.fetch_role_by_name(ctx, term.strip())
                        role_list.append(the_role)
                    except:
                        errors_roles_general.append(term.strip())

        if len(role_list) == 0:
            emoji = util.emoji("pensive")
            await ctx.send(f"Error: No valid role. {emoji}")
            return

        # FETCH USER ARGUMENT(S)

        errors_users = []
        multiple_users = False
        if is_mod:
            try:
                user_ids, rest = await util.fetch_id_from_args("user", "multiple", remainder_args)
                if user_ids == "None":
                    the_user = ctx.message.author
                    member_object_list = [the_user]
                else:
                    user_id_list = user_ids.split(";")
                    member_object_list = []
                    for user_id in user_id_list:
                        try:
                            the_user = ctx.guild.get_member(int(user_id))
                            member_object_list.append(the_user)
                        except:
                            errors_users.append(user_id)
            except Exception as e:
                the_user = ctx.message.author
                member_object_list = [the_user]
        else:
            the_user = ctx.message.author
            member_object_list = [the_user]

        # CHECK ASSIGNABILITY

        await util.update_role_database(ctx) # update role database

        con = sqlite3.connect(f'databases/roles.db')
        cur = con.cursor()
        if is_mod:
            assignable_role_ids = [item[0] for item in cur.execute("SELECT id FROM roles WHERE permissions = ?", ("", )).fetchall()]
        else:
            assignable_role_ids = [item[0] for item in cur.execute("SELECT id FROM roles WHERE LOWER(assignable) = ? AND permissions = ?", ("true", "")).fetchall()]

        errors_roles_assignability = []
        roles_to_assign = []
        for role in role_list:
            if str(role.id) in assignable_role_ids:
                roles_to_assign.append(role)
            else:
                errors_roles_assignability.append(role.mention)

        if len(roles_to_assign) == 0:
            emoji = util.emoji("pensive")
            await ctx.send(f"No assignable role provided. {emoji}")
            return

        # ASSIGN OR UNASSIGN?

        if assigning == "assign":
            assign = True
        elif assigning == "unassign":
            assign = False 
        else:
            assign = False
            for role in roles_to_assign:
                for member in member_object_list:
                    if role not in member.roles:
                        assign = True
                        break

        # EXECUTE ASSIGN/UNASSIGN PROCESS

        conB = sqlite3.connect(f'databases/botsettings.db')
        curB = conB.cursor()

        error_assigning = []
        successful_assignments = {}
        
        for role in roles_to_assign:
            category_list = [item[0] for item in cur.execute("SELECT category FROM roles WHERE id = ?", (str(role.id),)).fetchall()]
            category = category_list[0]
            rolebuttontype_list = [item[0] for item in curB.execute("SELECT type FROM reactionrolesettings WHERE LOWER(name) = ?", (category.lower(),)).fetchall()]
            
            if len(rolebuttontype_list) == 0:
                buttontype = "free"
            else:
                buttontype = rolebuttontype_list[0].lower()
                if buttontype == "radiobutton":
                    roles_from_same_category = [item[0] for item in cur.execute("SELECT id FROM roles WHERE LOWER(category) = ? AND id != ?", (category.lower(), str(role.id))).fetchall()]

            for member in member_object_list:
                if assign:
                    try:
                        # unassign all roles from same category, if radiobutton type
                        if buttontype == "radiobutton":
                            for other_role in member.roles:
                                if str(other_role.id) in roles_from_same_category:
                                    await member.remove_roles(other_role)

                        await member.add_roles(role)

                        if member.id not in successful_assignments:
                            successful_assignments[member.id] = True
                    except:
                        error_assigning.append(member.mention)
                        successful_assignments[member.id] = False
                else:
                    try:
                        await member.remove_roles(role)
                        if member.id not in successful_assignments:
                            successful_assignments[member.id] = True
                    except:
                        error_assigning.append(member.mention)
                        successful_assignments[member.id] = False

        errors_unique_assigning = list(dict.fromkeys(error_assigning))

        # CONFIRMATION MESSAGE

        if len(roles_to_assign) > 1:
            s = "s"
        else:
            s = ""

        if len(errors_roles_general) + len(errors_users) + len(errors_roles_assignability) + len(errors_unique_assigning) == 0:
            if assign:
                emoji = util.emoji("yay")
                await ctx.send(f"Successfully assigned role{s}! {emoji}")
            else:
                emoji = util.emoji("thumbs_up")
                await ctx.send(f"Successfully unassigned role{s}! {emoji}")
        else:
            if assign:
                header = "Role assigning attempt"
                assignment = "assign"
                direction = "to"
            else:
                header = "Role unassigning attempt"
                assignment = "unassign"
                direction = "from"

            all_successful_users = []
            for member in member_object_list:
                if member.id in successful_assignments:
                    if uccessful_assignments[member.id]:
                        all_successful_users.append(member.mention)

            text_list = []
            if len(all_successful_users) == 0:
                color = 0xa91b0d
                emoji = util.emoji("cry")
                text_list.append(f"Command failed {emoji}")
            else:
                color = 0xffd700
                text_list.append(f"Successfully {assignment}ed role{s} {direction} {', '.join(all_successful_users)}")

            if len(errors_roles_general) > 0:
                text_list.append("\nErrors with provided roles:")
                text_list.append(', '.join(errors_roles_general))
            if len(errors_roles_assignability) > 0:
                text_list.append("\nErrors with role assignability:")
                text_list.append(', '.join(errors_roles_assignability))
            if len(errors_users) > 0:
                text_list.append("\nErrors with provided user:")
                text_list.append(', '.join(errors_users))
            if len(errors_unique_assigning) > 0:
                text_list.append(f"\nErrors while trying to {assignment} {direction}:")
                text_list.append(', '.join(errors_unique_assigning))
            await util.multi_embed_message(ctx, header, text_list, color, "", None)





    @commands.command(name="role", aliases = ["rank"])
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _role(self, ctx, *args):
        """Assign/unassign role

        Use the role name, id or mention. Only roles that appear in `<prefix>roles` are assignable.
        You can also assign multiple roles at once, but they have to be either role ids/mentions OR role names separated by semicolons.
        i.e. `<prefix>role <role name1>; <role name2>; <role name3>`.
        
        Moderators can assign all roles without extra-permissions. To assign roles with extra permissions use `<prefix>designate`.
        To assign roles to other users use @user mentions (must NOT be id!), 
        i.e. `<prefix>role <@user mention> <role name>`.
        """        
        if len(args) < 1:
            await ctx.send("Error: Command needs a role argument.")
            return
        await self.role_assigning(ctx, args, "both")
    @_role.error
    async def role_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name="assign", aliases = ["assignrole"])
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _assign(self, ctx, *args):
        """㊙️ Assign role

        Use the role name, id or mention. Only roles that appear in `<prefix>roles` are assignable.
        You can also assign multiple roles at once, but they have to be either role ids/mentions OR role names separated by semicolons.
        i.e. `<prefix>assign <role name1>; <role name2>; <role name3>`.
        
        Moderators can assign all roles without extra-permissions. To assign roles with extra permissions use `<prefix>designate`.
        To assign roles to other users use @user mentions (must NOT be id!), 
        i.e. `<prefix>assign <@user mention> <role name>`.
        """        
        if len(args) < 1:
            await ctx.send("Error: Command needs a role argument.")
            return
        await self.role_assigning(ctx, args, "assign")
    @_assign.error
    async def assign_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name="unassign", aliases = ["unassignrole"])
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _unassign(self, ctx, *args):
        """㊙️ Unassign role

        Use the role name, id or mention. Only roles that appear in `<prefix>roles` are unassignable.
        You can also unassign multiple roles at once, but they have to be either role ids/mentions OR role names separated by semicolons.
        i.e. `<prefix>unassign <role name1>; <role name2>; <role name3>`.
        
        Moderators can unassign all roles without extra-permissions.
        To unassign roles from other users use @user mentions (must NOT be id!), 
        i.e. `<prefix>unassign <@user mention> <role name>`.
        """        
        if len(args) < 1:
            await ctx.send("Error: Command needs a role argument.")
            return
        await self.role_assigning(ctx, args, "unassign")
    @_unassign.error
    async def unassign_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name="designate", aliases=['undesignate'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _designate(self, ctx, *args):
        """🔒 Assign/unassign role with perms

        Use `<prefix>designate <@user mention> <role name>`.
        """     
        if len(args) < 2:
            await ctx.send("Error: Command needs a user and role argument.")
            return

        # PARSE ARGUMENTS

        try:
            role_id, remainder_args_string = await util.fetch_id_from_args("role", "all", args)
            user_id, rest = await util.fetch_id_from_args("user", "multiple", remainder_args_string.split())
        except Exception as e:
            print("Error:", e)
            await ctx.send("Error while trying to parse user and role.")
            return
        try:
            the_role = discord.utils.get(ctx.guild.roles, id = int(role_id))
        except Exception as e:
            print("Error:", e)
            await ctx.send("Error while trying to fetch role.")
            return
        try:
            member = ctx.guild.get_member(int(user_id))
        except Exception as e:
            print("Error:", e)
            await ctx.send("Error while trying to fetch member.")
            return

        # INQUIRE CONFIRMATION

        try:
            default_perms = await util.get_defaultperms(ctx)
            role_perms_higher = [perm[0] for perm in the_role.permissions if perm[1] and perm[0] not in default_perms]
        except Exception as e:
            print("Error:", e)
            await ctx.send("Error while trying fetch role permissions.")
            return

        if len(role_perms_higher) > 0:
            try:
                higherperms_string = ', '.join(role_perms_higher)
                text = f"`Confirmation required:` This role has higher permissions such as {higherperms_string}."
                response = await util.are_you_sure_msg(ctx, self.bot, text)
                if response == False:
                    return

            except Exception as e:
                print("Error:", e)
                await ctx.send("Error while trying to handle confirmation inquiry.")
                return

        # DO THE ASSIGNING/UNASSIGNING

        emoji = util.emoji("yay")
        if the_role in member.roles:
            try:
                await member.remove_roles(the_role)
            except Exception as e:
                print("Error:", e)
                await ctx.send(f"Error while trying to unassign `{the_role.name}` from `{member.name}`.")
                return

            await ctx.send(f"Successfully removed `{the_role.name}` from `{member.name}`! {emoji}")
        else:
            try:
                await member.add_roles(the_role)
            except Exception as e:
                print("Error:", e)
                await ctx.send(f"Error while trying to assign `{the_role.name}` to `{member.name}`.")
                return

            await ctx.send(f"Successfully assigned `{the_role.name}` to `{member.name}`! {emoji}")

    @_designate.error
    async def designate_error(self, ctx, error):
        await util.error_handling(ctx, error)



    ######################################################################## ROLE INFORMATION



    @commands.command(name='roles', aliases=['ranks'])
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _roles(self, ctx: commands.Context):
        """Prints assignable roles

        Roles without extra-permissions and of categories album, pronoun, music or other are assignable.
        Color and icon roles are also assignable, however a user can only have one of them."""

        await util.update_role_database(ctx) 

        # CHECK FOR ASSIGNABLE ROLES (WITH NO EXTRA PERMISSIONS)

        con = sqlite3.connect(f'databases/roles.db')
        cur = con.cursor()
        assignable_roles = [[item[0],item[1]] for item in cur.execute("SELECT name, category FROM roles WHERE LOWER(assignable) = ? AND permissions = ?", ("true", "")).fetchall()]
        categories = [item[1] for item in assignable_roles]
        categories = sorted(list(set(categories)))

        if len(assignable_roles) == 0:
            await ctx.send(f"There are no self-assignable roles in the database. Mods would need to use `{self.prefix}set assignability` command to change that.")
            return

        # ORGANISE ROLES IN DICT OF CATEGORIES

        cat_dict = {}
        for cat in categories:
            cat_dict[cat] = []
        for role in assignable_roles:
            role_name = role[0]
            role_cat = role[1]
            cat_dict[role_cat].append(util.cleantext2(role_name))

        # EMBED VARIABLES

        header = "Assignable Roles"
        text_string = ""
        footer = ""
        color = 0xFFA500

        fields_list = []
        i = 0
        for cat in sorted(list(cat_dict.keys())):
            fields_list.append([cat])
            for role in sorted(cat_dict[cat]):
                fields_list[i].append(role)
            i += 1

        await util.multi_field_embed(ctx, header, text_string, fields_list, color, footer, None)

    @_roles.error
    async def roles_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='serverroles', aliases=['serverranks'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _serverroles(self, ctx: commands.Context):
        """🔒 Prints all roles"""

        await util.update_role_database(ctx) 

        # CHECK FOR ASSIGNABLE ROLES (WITH NO EXTRA PERMISSIONS)

        con = sqlite3.connect(f'databases/roles.db')
        cur = con.cursor()
        all_roles = [[item[0],item[1]] for item in cur.execute("SELECT name, category FROM roles").fetchall()]
        categories = [item[1] for item in all_roles]
        categories = sorted(list(set(categories)))

        if len(all_roles) == 0:
            await ctx.send(f"There are no self-assignable roles in the database. Mods would need to use `{self.prefix}set assignability` command to change that.")
            return

        # ORGANISE ROLES IN DICT OF CATEGORIES

        cat_dict = {}
        for cat in categories:
            cat_dict[cat] = []
        for role in all_roles:
            role_name = role[0]
            role_cat = role[1]
            cat_dict[role_cat].append(util.cleantext2(role_name))

        # EMBED VARIABLES

        header = "All Server Roles"
        text_string = ""
        footer = ""
        color = 0xFF8C00

        fields_list = []
        i = 0
        for cat in sorted(list(cat_dict.keys())):
            fields_list.append([cat])
            for role in sorted(cat_dict[cat]):
                fields_list[i].append(role)
            i += 1

        await util.multi_field_embed(ctx, header, text_string, fields_list, color, footer, None)

    @_serverroles.error
    async def serverroles_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='userroles', aliases=['memberroles'])
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _userroles(self, ctx, *args):
        """Roles of user
        
        Use command with user @mention, id or name.
        """
        if len(args) < 1:
            await ctx.send("Error: Command needs a user argument.")
            return

        user_arg = ' '.join(args)
        userlist = ctx.guild.members

        found = False
        for user in userlist:
            mention = f'<@{user.id}>'
            if user_arg == mention or user_arg == str(user.id):
                user_object = user
                found = True
                break
        if found == False:
            for user in userlist:
                if user_arg == user.name:
                    user_object = user
                    found = True
                    break
        if found == False:
            for user in userlist:
                if user_arg == user.display_name or user_arg == user.nick:
                    user_object = user
                    found = True
                    break

        if found == False:
            await ctx.send("Could not find user :(")
        else:
            user_roles = []
            for role in user_object.roles:
                user_roles.append(util.cleantext2(role.name))
            #user_roles.sort() # would sort it alphabetically
            display_name = util.cleantext(user.display_name)
            header = f'Roles of {display_name}'
            text = ', '.join(user_roles)
            embed = discord.Embed(title=header, description = text[:4096], color=0xFF8C00)
            await ctx.send(embed=embed)
    @_userroles.error
    async def userroles_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='whohasrole', aliases=['whohasrank'])
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _whohasrole(self, ctx, *args):
        """Users with given role

        Use command with role @mention, name or id"""
        server = ctx.message.guild

        role_arg = ' '.join(args)

        # first try mentions, exact name or id
        for role in server.roles:
            mention = f'<@&{role.id}>'
            if role_arg == mention or role_arg == role.name or role_arg == str(role.id):
                the_role = role 
                break
        else:
            # second try close spelling
            for role in server.roles:
                role_arg_abridged = util.alphanum(role_arg,"lower")
                currently_checking_role = util.alphanum(role.name,"lower")
                if role_arg_abridged == currently_checking_role:
                    the_role = role 
                    break
            else:
                await ctx.send("Role doesn't exist :(")
                return
        
        memberlist = ctx.guild.members
        members_w_t_role = []
        for member in memberlist:
            if the_role in member.roles:
                members_w_t_role.append(util.cleantext2(member.name))
        members_w_t_role.sort()
        header = f"Members with role {the_role.name} are:"

        msg = '\n'.join(members_w_t_role)
        if len(msg) > 4096:
            msg = msg[:4092] + "\n..."

        embed = discord.Embed(title=header, description=msg, color=0xFF8C00)
        embed.set_footer(text = f"found {len(members_w_t_role)} members")
        await ctx.send(embed=embed)
    @_whohasrole.error
    async def whohasrole_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='whohasnorole', aliases=['whohasnorank'])
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _whohasnorole(self, ctx, *args):
        """Users without any role"""
        memberlist = ctx.guild.members
        members_without_roles = []
        for member in memberlist:
            if len([r for r in member.roles]) <= 1:
                members_without_roles.append(util.cleantext2(member.name))
        members_without_roles.sort()
        header = f"Members without any role are:"

        msg = '\n'.join(members_without_roles)
        if len(msg) > 4096:
            msg = msg[:4092] + "\n..."

        embed = discord.Embed(title=header, description=msg, color=0xFF8C00)
        embed.set_footer(text = f"found {len(members_without_roles)} members")
        await ctx.send(embed=embed)
    @_whohasnorole.error
    async def whohasnorole_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='userperms', aliases=['memberperms', 'userpermissions', 'memberpermissions'])
    @commands.has_permissions(manage_guild=True, manage_roles=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _userperms(self, ctx, *args):
        """🔒 Permissions of a user

        Use command with user @mention, id or name"""
        user_arg = ' '.join(args)
        userlist = ctx.guild.members

        found = False
        for user in userlist:
            mention = f'<@{user.id}>'
            if user_arg == mention or user_arg == str(user.id):
                user_object = user
                found = True
                break
        if found == False:
            for user in userlist:
                if user_arg.lower() == user.name.lower():
                    user_object = user
                    found = True
                    break
        if found == False:
            for user in userlist:
                if user_arg.lower() == user.display_name.lower():
                    user_object = user
                    found = True
                    break

        if found == False:
            await ctx.send("Could not find user :(")
        else:
            default_perms = await util.get_defaultperms(ctx)
            user_perms_full = [p for p in user_object.guild_permissions]

            user_perms = []
            for p in user_perms_full:
                if p[1]:
                    user_perms.append(p[0])
            
            perms_low = []
            perms_high = []
            for perm in user_perms:
                if perm in default_perms:
                    perms_low.append(perm)
                else:
                    perms_high.append(perm)

            if len(perms_low) == 0:
                lowperms_msg = 'none\n'
            else:
                lowperms_msg = '\n```' + ', '.join(perms_low)[:1017] + '```'
            if len(perms_high) == 0:
                highperms_msg = 'none\n'
            else:
                highperms_msg = '\n```' + ', '.join(perms_high)[:1017] + '```'

            header = f'User permissions of {str(user_object)}'
            embed = discord.Embed(title=header, color=0xFF8C00)
            embed.add_field(name='default permissions:', value=lowperms_msg, inline=False)
            embed.add_field(name='higher permissions:', value=highperms_msg, inline=False)
            await ctx.send(embed=embed)
    @_userperms.error
    async def userperms_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='roleperms', aliases=['rankperms', 'rolepermissions', 'rankpermissions'])
    @commands.has_permissions(manage_guild=True, manage_roles=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _roleperms(self, ctx, *args):
        """🔒 Permissions of a role

        Use command with role @mention, id or name"""

        role_arg = ' '.join(args)
        rolelist = ctx.guild.roles

        found = False
        for role in rolelist:
            mention = f'<@&{role.id}>'
            if role_arg == mention or role_arg == str(role.id):
                role_object = role
                found = True
                break
        if found == False:
            for role in rolelist:
                if role_arg.lower() == role.name.lower():
                    role_object = role
                    found = True
                    break
        if found == False:
            for role in rolelist:
                if util.alphanum(role_arg,"lower") == util.alphanum(role.name,"lower"):
                    role_object = role
                    found = True
                    break 

        if found == False:
            await ctx.send("Could not find role :(")
        else:
            default_perms = await util.get_defaultperms(ctx)
            role_perms_full = [p for p in role_object.permissions]

            role_perms = []
            for p in role_perms_full:
                if p[1]:
                    role_perms.append(p[0])
            
            perms_low = []
            perms_high = []
            for perm in role_perms:
                if perm in default_perms:
                    perms_low.append(perm)
                else:
                    perms_high.append(perm)

            if len(perms_low) == 0:
                lowperms_msg = 'none\n'
            else:
                lowperms_msg = '\n```' + ', '.join(perms_low)[:1017] + '```'
            if len(perms_high) == 0:
                highperms_msg = 'none\n'
            else:
                highperms_msg = '\n```' + ', '.join(perms_high)[:1017] + '```'

            header = f'Role permissions of {str(role_object)}'
            embed = discord.Embed(title=header, color=0xFF8C00)
            embed.add_field(name='default permissions:', value=lowperms_msg, inline=False)
            embed.add_field(name='higher permissions:', value=highperms_msg, inline=False)
            await ctx.send(embed=embed)
    @_roleperms.error
    async def roleperms_error(self, ctx, error):
        await util.error_handling(ctx, error)




    @commands.command(name='perms', aliases=['permissions'])
    @commands.has_permissions(manage_guild=True, manage_roles=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _perms(self, ctx, *args):
        """🔒 Permissions of a user/role

        This is a combined command of `<prefix>userperms` and `<prefix>roleperms`. 
        Command only works with @mention."""
        if len(args) == 0:
            await ctx.send("Command needs a @user or @role mention as argument.")
            return

        arg = args[0]
        if arg.startswith("<@&") and arg.endswith(">"):
            await self._roleperms(ctx, arg)
        elif arg.startswith("<@") and arg.endswith(">"):
            await self._userperms(ctx, arg)
        else:
            await ctx.send("Error: Invalid argument.")
    @_perms.error
    async def perms_error(self, ctx, error):
        await util.error_handling(ctx, error)



    ############################################################################## MODLOCKED ACTIONS



    @commands.command(name='roleupdate', aliases=['rankupdate'])
    @commands.has_permissions(manage_guild=True, manage_roles=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _roleupdate(self, ctx):
        """🔒Update role database
        
        does 3 things:
        > adds missing roles to db 
        > removes non-existing roles from db
        > updates names, permissions and colors
        """
        await util.update_role_database(ctx)
        await ctx.send("Updated role database.")
    @_roleupdate.error
    async def roleupdate_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='rolecolor', aliases=['rolecol', 'rolecolour', 'rankcol', 'cankcolor', 'rankcolour'])
    @commands.has_permissions(manage_guild=True, manage_roles=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _rolecolor(self, ctx, *args):
        """🔒 Change role color

        Use `<prefix>rolecol <role id or name> #<HEX code>`.
        Write `#` without code for no color."""

        # PARSE ARGUMENTS

        if len(args) < 2:
            await ctx.send("Error: Command needs 2 arguments.")
            return

        rolename = " ".join(args[0:-1])
        color_arg = args[-1]

        if not util.hexmatch(color_arg) and color_arg != "#": # just in case arguments were swapped
            rolename = " ".join(args[1:])
            color_arg = args[0]

            if not util.hexmatch(color_arg) and color_arg != "#":
                await ctx.send("Error: No valid HEX color argument. Make sure to have the 2nd argument be in the format `#000000`")
                return

        if color_arg == "#":
            hex_color = None
        else:
            hex_color = int(color_arg.replace("#",""), 16)
        con = sqlite3.connect('databases/roles.db')
        cur = con.cursor()

        # CHECK ROLE ARGUMENTs VALIDITY

        try: 
            # CHECK FOR ROLE ID OR MENTION
            role_id, rest = await util.fetch_id_from_args("role", "first", [rolename])
            the_role = discord.utils.get(ctx.guild.roles, id = int(role_id))
        except:
            # CHECK FOR ROLE NAMES
            try:
                the_role = await util.fetch_role_by_name(ctx, rolename)
            except:
                emoji = util.emoji("pensive")
                await ctx.send(f"Error: No valid role argument. {emoji}")
                return

        # CHANGE COLOR

        await the_role.edit(colour=discord.Colour(hex_color))

        msg = f"Successfully changed color of {the_role.mention} to `{color_arg}`! {emoji}"
        embed = discord.Embed(description=msg, color=hex_color)
        await ctx.send(embed=embed)

        await util.update_role_database(ctx)

    @_rolecolor.error
    async def rolecolor_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='newrole', aliases=['newrank', 'createrole', 'createrank'])
    @commands.has_permissions(manage_guild=True, manage_roles=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _newrole(self, ctx, *args):
        """🔒 Creates permissionless role

        Use `<prefix>newrole <new role name> #<HEX color> <category name>` to create new role.
        Category and Hex code are optional, but if you want to provide them you need to provide both. 
        (Categories cannot have spaces use underscores instead.)

        HEX code must start with an `#` like `#FF0000` for red. If you want to choose no color write `#` without a hex number."""

        if len(args) == 0:
            await ctx.send(f"Command needs arguments.\n\nUse `{self.prefix}newrole <new role name> #<HEX color> <category name>` to create new role.\nCategory and Hex code are optional, but if you want to provide them you need to provide both.\nHEX code must start with an `#` like `#FF0000` for red. If you want to choose no color write `#` without a hex number.")
            return

        await util.update_role_database(ctx)

        con = sqlite3.connect('databases/roles.db')
        cur = con.cursor()
        conB = sqlite3.connect(f'databases/botsettings.db')
        curB = conB.cursor()

        role_name = ' '.join(args)
        category = ""
        HEX_code = ""
        hex_color = 0xFFFFFF

        # CHECK FOR COLOR AND CATEGORY ARGUMENT

        if len(args) > 2:
            if args[-2].startswith("#"):
                color_arg = args[-2]

                if util.hexmatch(color_arg):
                    hex_color = int(color_arg.replace("#",""), 16)
                    HEX_code = color_arg
                else:
                    HEX_code = ""

                category = args[-1].lower()
                roles_of_category_list = [item[0] for item in cur.execute("SELECT id FROM roles WHERE LOWER(category) = ?", (category,)).fetchall()]
                reaction_categories = [item[0].lower() for item in curB.execute("SELECT name FROM reactionrolesettings").fetchall()]

                # confirm if role doesn't exist yet

                if len(roles_of_category_list) == 0 and category not in reaction_categories:
                    category_list = [item[0].lower() for item in cur.execute("SELECT category FROM roles").fetchall()]
                    catlist = list(dict.fromkeys(category_list))
                    msg_confirmation = "This role category doesn't exist yet. If you want to continue and create the category respond with `yes`.\n"
                    if len(roles_of_category_list) > 0:
                        rolecatstring = ', '.join(roles_of_category_list)
                        msg_confirmation += f"Role categories in role database:```{rolecatstring}```"
                    if len(reaction_categories) > 0:
                        reactcatstring = ', '.join(reaction_categories)
                        msg_confirmation += f"Role categories in role database:```{reactcatstring}```"
                    await ctx.send(msg_confirmation)
                    try: # waiting for message
                        async with ctx.typing():
                            response = await self.bot.wait_for('message', check=lambda message: util.confirmation_check(ctx, message), timeout=30.0) # timeout - how long bot waits for message (in seconds)
                    except asyncio.TimeoutError: # returning after timeout
                        await ctx.send("action timed out")
                        return

                    # if response is different than yes / y - return
                    if response.content.lower() not in ["yes", "y"]:
                        await ctx.send("cancelled action")
                        return

                role_name = ' '.join(args[:-2])

        # CHECK IF ROLENAME ALREADY EXISTS

        all_roles = [str(r.name).lower() for r in ctx.guild.roles]
        if role_name.lower() in all_roles:
            emoji = util.emoji("surprised")
            await ctx.send(f'Role with this name already exists! {emoji}')
        else:

            # CHECK IF THE ROLE SHOULD BE ASSIGNABLE FOR REGULAR USERS

            enabled_reaction_categories = [item[0].lower() for item in curB.execute("SELECT name FROM reactionrolesettings WHERE turn = ?", ("on",)).fetchall()]
            category_list = [[item[0].lower(),item[1]] for item in cur.execute("SELECT category, assignable, permissions FROM roles").fetchall()]
            category_dict = {}
            for item in category_list:
                cat = item[0]
                assignable = item[1]
                if cat not in category_dict:
                    category_dict[cat] = assignable
                else:
                    if item[1].lower() == "false":
                        category_dict[cat] = assignable

            if category in category_dict and category_dict[category].lower() == "true":
                assignability = "True"
            else:
                assignability = "False"

            if HEX_code == "":
                role = await ctx.guild.create_role(name=role_name, color=discord.Colour(0))
                msg = f"Created role: {role_name}\nof category: {category}\n(no color)\nAssignability: {assignability}"
            else:
                role = await ctx.guild.create_role(name=role_name, color=discord.Colour(hex_color)) 
                msg = f"Created role: {role_name}\nof category: {category}\nwith HEX color: {HEX_code}\nAssignability: {assignability}"

            embed = discord.Embed(description=msg, color=hex_color)
            
            cur.execute("INSERT INTO roles VALUES (?, ?, ?, ?, ?, ?, ?)", (str(role.id), role_name, assignability, category, '', HEX_code, ''))
            con.commit()
            await util.changetimeupdate()
            await ctx.send(embed=embed)

    @_newrole.error
    async def newrole_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='removerole', aliases=['removerank', 'deleterole', 'deleterank'])
    @commands.has_permissions(manage_guild=True, manage_roles=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _removerole(self, ctx, *args):
        """🔒 Deletes role"""

        role_to_delete = ' '.join(args)

        role_found = False
        for role in ctx.guild.roles:
            mention = f'<@&{role.id}>'
            if role_to_delete == str(role.id) or role_to_delete == mention:
                role_found = True
                the_role = role
                break
        if role_found == False:
            for role in ctx.guild.roles:
                if role_to_delete.lower() == role.name.lower():
                    role_found = True
                    the_role = role
                    break

        if role_found == False:
            await ctx.send(f'This role seems to not exist... :O')
            return

        default_perms = await util.get_defaultperms(ctx)
        perm_list = [perm[0] for perm in the_role.permissions if perm[1]]
        perms_low = []
        perms_high = []
        for perm in perm_list:
            if perm in default_perms:
                perms_low.append(perm)
            else:
                perms_high.append(perm)

        if len(perms_high) > 0:
            emoji = util.emoji("attention")
            header = f"{emoji} Warning"
            permissionstring = ', '.join(perms_high)
            msg = f"The role <@&{the_role.id}> has higher permissions.```{permissionstring}```\nRespond with `yes` to delete anyway."
            hex_color = 0xa91b0d
            embed = discord.Embed(title=header, description=msg, color=hex_color)
            await ctx.send(embed=embed)
            try: # waiting for message
                response = await self.bot.wait_for('message', check=lambda message: util.confirmation_check(ctx, message), timeout=30.0) # timeout - how long bot waits for message (in seconds)
            except asyncio.TimeoutError: # returning after timeout
                await ctx.send("action timed out")
                return

            # if response is different than yes / y - return
            if response.content.lower() not in ["yes", "y"]:
                await ctx.send("cancelled action")
                return

        try:
            await the_role.delete()
            con = sqlite3.connect('databases/roles.db')
            cur = con.cursor()
            cur.execute("DELETE FROM roles WHERE id = ?", (str(the_role.id),))
            con.commit()
            await util.changetimeupdate()
            emoji = util.emoji("unleashed")
            await ctx.send(f"The role `{the_role.name}` haveth been deleted! {emoji}")
        except:
            emoji = util.emoji("cry")
            await ctx.send(f"Error occured while trying to delete role! {emoji}")

    @_removerole.error
    async def removerole_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='checkrolemoji', aliases = ['rolemojicheck', 'checkroleemoji', 'roleemojicheck'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _checkrolemoji(self, ctx: commands.Context, *args):
        """🔒 Check role emoji

        Sanity Check if all role emojis are usable by MDM bot."""

        await util.update_role_database(ctx)
        mdmbot_emojis = [str(x) for x in self.bot.emojis]

        # FETCH ROLES WITH ASSIGNED EMOJI

        con = sqlite3.connect('databases/roles.db')
        cur = con.cursor()
        db_roles = [[item[0], item[1], item[2], item[3]] for item in cur.execute("SELECT id, name, details, category FROM roles").fetchall()]
        
        emoji_roles = []
        for role in db_roles:
            if role[2].strip() != "":
                emoji_roles.append(role)

        # FILTER FOR ROLES THAT HAVE AN ACTIVE REACTION ROLE CATEGORY

        db_react_roles = []
        conB = sqlite3.connect(f'databases/botsettings.db')
        curB = conB.cursor()
        reaction_categories = [item[0].lower() for item in curB.execute("SELECT name FROM reactionrolesettings WHERE turn = ?", ("on",)).fetchall()]
        for role in emoji_roles:
            if role[3].lower() in reaction_categories:
                db_react_roles.append(role) #that have emojis

        # CHECK USABILITY OF ASSIGNED EMOJI
        
        invalid_rolemoji_list = []
        nonrelevant_invalid_rolemoji_list = []
        for role in emoji_roles:
            rolename = role[1]
            rolemoji = role[2]
            if rolemoji in UNICODE_EMOJI['en']:
                #print(f"Found standard emoji {rolemoji} for role {rolename}")
                pass
            elif rolemoji in mdmbot_emojis:
                #print(f"Found custom emoji {rolemoji} for role {rolename}")
                pass
            else:
                print(f"ERROR: {rolename} has invalid emoji {rolemoji}")
                if role in db_react_roles:
                    invalid_rolemoji_list.append(role)
                else:
                    nonrelevant_invalid_rolemoji_list.append(role)

        # CHECK IF THERE ARE ROLES WITHOUT ANY EMOJI:

        role_id_missing_emoji = [] 

        for role in db_roles:
            if role[3].lower() in reaction_categories and role[2].strip() == "":
                role_id_missing_emoji.append(role[0])

        # CHECK IF EMOJI ARE UNIQUE
        
        emoji_list = [r[2] for r in emoji_roles]
        emoji_set = list(dict.fromkeys(emoji_list))
        emoji_count = dict((x, emoji_list.count(x)) for x in emoji_set)

        emoji_duplicates = False
        for key in emoji_count:
            if emoji_count[key] > 1:
                emoji_duplicates = True 

        relevant_dupe_list = []
        nonrelevant_dupe_list = []
        if emoji_duplicates:
            for emoji in sorted(emoji_set):
                list_of_fitting_role_ids = []
                for role in emoji_roles:
                    if role[2].strip().lower() == emoji.strip().lower():
                        list_of_fitting_role_ids.append(role[0])
                if len(list_of_fitting_role_ids) > 1:
                    if role in db_react_roles:
                        relevant_dupe_list.append(f"---emoji: {emoji}---")
                        for r_id in list_of_fitting_role_ids:
                            relevant_dupe_list.append(f"<@&{r_id}>")
                        relevant_dupe_list.append("")
                    else:
                        nonrelevant_dupe_list.append(f"---emoji: {emoji}---")
                        for r_id in list_of_fitting_role_ids:
                            nonrelevant_dupe_list.append(f"<@&{r_id}>")
                        nonrelevant_dupe_list.append("")


        # MESSAGE COMPOSITION

        if len(invalid_rolemoji_list) + len(nonrelevant_invalid_rolemoji_list) + len(role_id_missing_emoji) + len(relevant_dupe_list) + len(nonrelevant_dupe_list) == 0:
            emoji = util.emoji("thumb_up")
            await ctx.channel.send(f'All good. {emoji}')
        else:
            if len(invalid_rolemoji_list) == 0 and len(role_id_missing_emoji) == 0 and len(relevant_dupe_list) == 0:
                emoji = util.emoji("thumbs_up")
                await ctx.channel.send(f"All currently used reaction roles are fine. {emoji}\nI found however other role emoji that have issues:")
                description = ""

                if len(nonrelevant_invalid_rolemoji_list) > 0:
                    description += f"**Unable to use the following:**\n"
                    for role in nonrelevant_invalid_rolemoji_list:
                        description += f"<@&{role[0]}> with rolemoji: {role[2]}\n"

                if len(nonrelevant_dupe_list) > 0:
                    description += f"**Found the following duplicate emojis:**\n"
                    description += "\n".join(nonrelevant_dupe_list)   

                embed = discord.Embed(title = "", description=description[:4096], color=0xFEE12B)
                embed.set_footer(text = f"{len(nonrelevant_invalid_rolemoji_list)} cases detected")
                await ctx.send(embed=embed)
            else:
                if len(invalid_rolemoji_list) > 0:
                    title = "⚠️ Problem with usability of reaction role emojis"
                    description = "Found issues with the following roles that are in current use as reaction-assignable roles:\n"
                    for role in invalid_rolemoji_list:
                        description += f"<@&{role[0]}> with rolemoji: {role[2]}\n"

                    embed = discord.Embed(title = title, description=description[:4096], color=0xFF0000)
                    embed.set_footer(text = f"{len(invalid_rolemoji_list)} issues detected. Already created embeds + reacts in #roles channel should still work, but updating the reaction embeds will lead to problems if some emojis are not usable by the bot.")
                    await ctx.send(embed=embed)

                if len(nonrelevant_invalid_rolemoji_list) > 0:
                    description = "Issues with emojis of non-react roles:\n"
                    for role in nonrelevant_invalid_rolemoji_list:
                        description += f"<@&{role[0]}> with rolemoji: {role[2]}\n"

                    emoji = util.emoji("note")
                    embed = discord.Embed(title = f"{emoji} Note", description=description[:4096], color=0xFEE12B)
                    embed.set_footer(text = f"{len(nonrelevant_invalid_rolemoji_list)} cases detected")
                    await ctx.send(embed=embed)

                if len(role_id_missing_emoji) > 0:
                    title = "⚠️ Reaction roles with undefined reaction:\n"
                    description += "Some reaction roles have a missing emoji argument."
                    for role in nonrelevant_invalid_rolemoji_list:
                        description += f"<@&{role[0]}> with rolemoji: {role[2]}\n"

                    embed = discord.Embed(title = title, description=description[:4096], color=0xFEE12B)
                    embed.set_footer(text = f"{len(role_id_missing_emoji)} issues detected. It would not be possible to assign these roles via react in the #roles channel.")
                    await ctx.send(embed=embed)

                if len(relevant_dupe_list) > 0:
                    title = "⚠️ Duplicate reaction emojis"
                    description = f"Found the following duplicate emojis among currently used reaction roles:\n"
                    for role in relevant_dupe_list:
                        description += "\n".join(relevant_dupe_list)  

                    embed = discord.Embed(title = title, description=description[:4096], color=0xFF0000)
                    embed.set_footer(text = f"{len(relevant_dupe_list)} issues detected.")
                    await ctx.send(embed=embed)

                if len(nonrelevant_dupe_list) > 0:
                    emoji = util.emoji("note")
                    title = f"{emoji} Note"
                    description = f"Found the following duplicate emojis among roles not currently used as reaction roles:\n"
                    for role in nonrelevant_dupe_list:
                        description += "\n".join(nonrelevant_dupe_list)  

                    embed = discord.Embed(title = title, description=description[:4096], color=0xFF0000)
                    embed.set_footer(text = f"{len(nonrelevant_dupe_list)} cases detected.")
                    await ctx.send(embed=embed)

    @_checkrolemoji.error
    async def checkrolemoji_error(self, ctx, error):
        await util.error_handling(ctx, error)


    async def rolechannel_embed(self, ctx, cat, sorting, db_react_roles, role_channel):
        """cat must be a list with 8 elements"""

        # COMPOSE EMBED HEADER/FOOTER/COLOR
        cat_name = cat[0]
        cat_turn = cat[1]
        cat_type = cat[2]
        cat_header = cat[4]
        cat_text = cat[5]
        cat_footer = cat[6]
        cat_color = cat[7]
        if cat_header.strip() == "":
            if cat_type.lower() == "radiobutton":
                header = f"React to choose a {cat_name} role!"
            else:
                header = f"React to choose {cat_name} roles!"
        else:
            header = cat_header.strip()
        if cat_color.strip() == "":
            color = 0x000000
        else:
            try:
                color = int(cat_color.replace("#",""), 16)        
            except:
                color = 0xFFFFFF
        if cat_footer.strip() == "":
            if cat_type.lower() == "radiobutton":
                footer = "A second react will automatically remove the role from your first react."
            else:
                footer = "Remove react to remove role."
        else:
            footer = cat_footer.strip()

        # COMPOSE EMBED DESCRIPTION

        text_list = cat_text.strip().replace("\\n","\n").split("\n")
        reaction_emoji = []
        if sorting.lower() == "alphabetical":
            db_react_roles.sort(key=lambda x: x[1])
            for role in db_react_roles:
                if role[3].lower() == cat_name.lower():
                    r_id = role[0]
                    r_emoji = role[2]
                    text_list.append(f"{r_emoji} <@&{r_id}>")
                    reaction_emoji.append(r_emoji)
        else:
            cat_role_ids = []
            for role in db_react_roles:
                if role[3].lower() == cat_name.lower():
                    cat_role_ids.append(role[0])

            hierarchical_list = [x for x in ctx.guild.roles]
            for role in reversed(hierarchical_list):
                if str(role.id) in cat_role_ids:
                    for r in db_react_roles:
                        if r[0] == str(role.id):
                            r_emoji = r[2]
                            break
                    else:
                        r_emoji = "error"
                    text_list.append(f"{r_emoji} <@&{str(role.id)}>")
                    reaction_emoji.append(r_emoji)

        # SEND MESSAGES / UPDATE DB / ADD REACTS

        message = await util.multi_embed_message(ctx, header, text_list, color, footer, role_channel)

        curB.execute("UPDATE reactionrolesettings SET msg_id = ? WHERE LOWER(name) = ?", (str(message.id), cat_name.lower()))
        conB.commit()
        await util.changetimeupdate()

        try:
            for emoji in reaction_emoji:
                await message.add_reaction(emoji)
        except Exception as e:
            print(f"Error while trying to add reactions: {e}")



    @commands.command(name='rcupdate', aliases = ['rolechannelupdate', 'roleschannelupdate', 'rolechannelup', 'roleschannelup'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _rcupdate(self, ctx: commands.Context, *args):
        """🔒 Update #roles channel
        
        No arguments: Deletes all messages in #roles channel, and creates new ones with updated roles (for self-assigning of roles via reacts for all server members).
        (If there are more than 100 messages in the channel. Purge the channel first.)

        You can also provide category arguments. In this case no message will be deleted and only embeds of provided categories will be sent.
        However, a previously existing embed of that category will lose functionality in favour of the new embed.
        """
        def check(m): # checking if it's the same user and channel
            return ((m.author == ctx.author) and (m.channel == ctx.channel))

        await util.update_role_database(ctx)

        # CHECK REACTION ROLE ENABLING

        conB = sqlite3.connect(f'databases/botsettings.db')
        curB = conB.cursor()
        sorting_list = [[item[0],item[1]] for item in curB.execute("SELECT value, details FROM serversettings WHERE name = ?", ("reaction roles",)).fetchall()]
        if len(sorting_list) == 0:
            await ctx.send(f"Error: No reaction roles setting in database. Bot needs a proper setup via `{self.prefix}setup`.")
            return

        if len(sorting_list) > 1:
            print(f"Warning: There are multiple reaction role settings in the serversettings table.")

        turn = sorting_list[0][0]
        sorting = sorting_list[0][1]

        if turn.lower() != "on":
            await ctx.send(f"Reaction role feature is turned off. Enable it?\nRespond with `yes` to turn on and continue.")
            try: # waiting for message
                async with ctx.typing():
                    response = await self.bot.wait_for('message', check=lambda message: util.confirmation_check(ctx, message), timeout=30.0) # timeout - how long bot waits for message (in seconds)
            except asyncio.TimeoutError: # returning after timeout
                await ctx.send("Action timed out.")
                return

            # if response is different than yes / y - return
            if response.content.lower() not in ["yes", "y"]:
                await ctx.send("Cancelled action.")
                return
            else:
                cur.execute("UPDATE serversettings SET value = ? WHERE name = ?", ("on", "reaction roles"))
                con.commit()
                await util.changetimeupdate()
                await ctx.send(f"Reaction role feature is turned on. Continuing...")

        # RETRIEVE ROLES

        con = sqlite3.connect('databases/roles.db')
        cur = con.cursor()
        db_roles = [[item[0], item[1], item[2], item[3]] for item in cur.execute("SELECT id, name, details, category FROM roles").fetchall()]

        # FILTER FOR ROLES THAT HAVE AN ACTIVE REACTION ROLE CATEGORY

        db_react_roles = []
        reaction_categories = [item[0].lower() for item in curB.execute("SELECT name FROM reactionrolesettings WHERE turn = ?", ("on",)).fetchall()]

        if len(args) == 0:
            for role in db_roles:
                if role[3].lower() in reaction_categories:
                    db_react_roles.append(role)
        else:
            unused_cats = []
            provided_cats = []
            for cat in args:
                provided_cats.append(cat.lower())
                if cat.lower() not in reaction_categories:
                    unused_cats.append(cat)
            for role in db_roles:
                if role[3].lower() in reaction_categories and role[3].lower() in provided_cats:
                    db_react_roles.append(role)

            if len(unsused_cats) > 0:
                message = f"Error: Some of the role categories are not enabled in the reaction role settings."
                enabledcat_string = ', '.join(unsused_cats).lower()
                message += f"\nCategories that are not enabled: ````{enabledcat_string}```"
                message += f"\nUse `{self.prefix}reactrolecat <category name> on`"
                await ctx.send(message)
                return

        # CHECK EMOJI VALIDITY: MISSING EMOJI

        role_id_missing_emoji = [] 

        for role in db_react_roles:
            if role[2].strip() == "":
                role_id_missing_emoji.append(role[0])

        if len(role_id_missing_emoji) > 0:
            await ctx.send(f"Error: Missing emoji!")
            header = "Roles with missing emoji"
            color = 0xFFC700
            text_list = []
            for r_id in role_id_missing_emoji:
                text_list.append(f"<@&{r_id}>")
            footer = ""
            await util.multi_embed_message(ctx, header, text_list, color, footer, None)
            return

        # CHECK EMOJI VALIDITY: USABILITY BY BOT

        role_id_unusable_emoji = []
        for role in db_react_roles:
            emoji = role[2]
            if emoji not in UNICODE_EMOJI['en'] and emoji not in util.convert_stringlist(self.bot.emojis):
                role_id_unusable_emoji.append(role)

        if len(role_id_unusable_emoji) > 0:
            await ctx.send(f"Error: Unusable emoji!")
            header = "Roles with emoji that the bot cannot use"
            color = 0xFFC700
            text_list = []
            for role in role_id_missing_emoji:
                r_id = role[0]
                r_emoji = role[2]
                text_list.append(f"<@&{r_id}>: {r_emoji}")
            footer = ""
            await util.multi_embed_message(ctx, header, text_list, color, footer, None)
            return

        # CHECK EMOJI VALIDITY: UNIQUENESS

        emoji_list = [r[2] for r in db_react_roles]
        emoji_set = list(dict.fromkeys(emoji_list))
        emoji_count = dict((x, emoji_list.count(x)) for x in emoji_set)

        emoji_duplicates = False
        for key in emoji_count:
            if emoji_count[key] > 1:
                emoji_duplicates = True 

        if emoji_duplicates:
            await ctx.send(f"Error: There are emoji duplicates!")
            header = "Found duplicates"
            color = 0xFFC700
            text_list = []
            for emoji in sorted(emoji_set):
                list_of_fitting_role_ids = []
                for role in db_react_roles:
                    if role[2].strip().lower() == emoji.strip().lower():
                        list_of_fitting_role_ids.append(role[0])
                if len(list_of_fitting_role_ids) > 1:
                    text_list.append(f"---emoji: {emoji}---")
                    for r_id in list_of_fitting_role_ids:
                        text_list.append(f"<@&{r_id}>")
                    text_list.append("")
            footer = ""
            await until.multi_embed_message(ctx, header, text_list, color, footer, None)
            return

        # CHECK #ROLES CHANNEL

        role_channel_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("role channel id",)).fetchall()]
        if len(role_channel_list) == 0:
            await ctx.send(f"Error: No role channel id provided. Use `{self.prefix}help set rolechannel` for more info.")
            return

        if len(role_channel_list) > 1:
            print("Warning: There are multiple role channel entries in the database.")

        try:
            role_channel_id = int(role_channel_list[0])
            role_channel = self.bot.get_channel(role_channel_id)
        except:
            await ctx.send(f"Error with the provided role channel id: Use `{self.prefix}set rolechannel` to change to valid role channel id.")
            return

        if len(args) == 0:
            # CONFIRM FOR DELETION OF ALL MESSAGES IN #ROLES

            header = "Confirmation needed"
            text = f"Are you sure you want to delete all messages in <#{role_channel.id}>?"
            color = 0x000000

            response = await util.are_you_sure_embed(ctx, self.bot, header, text, color)

            if response == "False":
                await ctx.send("Cancelled action.")
                return
            if response == "Timed_Out":
                await ctx.send("Action timed out.")
                return
            # if response == "True" continue

            # DELETE MESSAGES
            try:
                mgs = [] 
                async for x in bot.logs_from(role_channel, limit = 100):
                    mgs.append(x)
                await self.bot.delete_messages(mgs)
            except Exception as e:
                await ctx.send(f"Failed to delete messages. :(\n```Error: {e}```")

            # CREATE NEW MESSAGES (FULL)

            reaction_cats = [[item[0],item[1],item[2],item[3],item[4],item[5],item[6],item[7]] for item in curB.execute("SELECT name, turn, type, rankorder, embed_header, embed_text, embed_footer, embed_color FROM reactionrolesettings WHERE turn = ?", ("on",)).fetchall()]
            reaction_cats.sort(key=lambda x: x[3])        

            for cat in reaction_cats:
                await self.rolechannel_embed(ctx, cat, sorting, db_react_roles, role_channel)

        else:
            # CREATE NEW MESSAGES (SELECTION)

            reaction_cats_all = [[item[0],item[1],item[2],item[3],item[4],item[5],item[6],item[7]] for item in curB.execute("SELECT name, turn, type, rankorder, embed_header, embed_text, embed_footer, embed_color FROM reactionrolesettings WHERE turn = ?", ("on",)).fetchall()]
            reaction_cats = []
            for cat in reaction_cats_all:
                catname = cat[0].lower()
                if catname in provided_cats:
                    reaction_cats.append(cat)     

            for cat in reaction_cats:
                await self.rolechannel_embed(ctx, cat, sorting, db_react_roles, role_channel)

        await ctx.send("Done.")

    @_rcupdate.error
    async def rcupdate_error(self, ctx, error):
        await util.error_handling(ctx, error)




    @commands.command(name='unassignall', aliases = ['massunassign'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _removeicons(self, ctx: commands.Context, *args):
        """🔒 Unassign role (or entire category of roles) from all users on the server
        """

        if len(args) == 0:
            await ctx.send("Error: command needs role argument")
            return 

        role_arg = ' '.join(args)

        # FETCH ROLE

        try: 
            # CHECK FOR ROLE ID OR MENTION
            role_id, rest = await util.fetch_id_from_args("role", "first", args)
            the_role = discord.utils.get(ctx.guild.roles, id = int(role_id))
        except:
            # CHECK FOR ROLE NAMES
            try:
                the_role = await util.fetch_role_by_name(ctx, role_arg)
            except:
                emoji = util.emoji("pensive")
                await ctx.send(f"Error: No valid role argument. {emoji}")
                return

        # SANITY CHECK (MORE PERMS THAN REFERENCE ROLE?)

        default_perms = await util.get_defaultperms(ctx)

        higher_perms = []
        for perm in the_role.permissions:
            if perm[1]:
                if perm[0] not in default_perms:
                    higher_perms.append(perm[0])

        if 'manage_guild' in higher_perms:
            emoji = util.emoji("no")
            await ctx.send(f"Error: I shall not remove a mod role. {emoji}")
            return

        # CONFIRMATION

        async with ctx.typing():

            await ctx.send(f"Are you sure you want to assign the {the_role.name} role to all current members? Respond with `yes` to confirm.")

            try: # waiting for message
                response = await self.bot.wait_for('message', check=lambda message: util.confirmation_check(ctx, message), timeout=30.0) # timeout - how long bot waits for message (in seconds)
            except asyncio.TimeoutError: # returning after timeout
                await ctx.send("action timed out")
                return

            # if response is different than yes / y - return
            if response.content.lower() not in ["yes", "y"]:
                await ctx.send("cancelled action")
                return

            # UNASSIGN

            errors = []

            for member in ctx.guild.members:
                if the_role in member.roles:
                    try:
                        await member.remove_roles(the_role)
                    except:
                        errors.append(member.name)

        if len(errors) == 0:
            await ctx.send("Finished unassigning role from everyone.")
        else:
            problemusers = ', '.join(errors)
            await ctx.send(f"Finished unassigning role from everyone, except: {problemusers}"[:2000])
    @_removeicons.error
    async def removeicons_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='assignall', aliases = ['massassign'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _removeicons(self, ctx: commands.Context, *args):
        """🔒 Assign role to all members on the server
        """

        if len(args) == 0:
            await ctx.send("Error: command needs role argument")
            return 

        role_arg = ' '.join(args)

        # FETCH ROLE

        try: 
            # CHECK FOR ROLE ID OR MENTION
            role_id, rest = await util.fetch_id_from_args("role", "first", args)
            the_role = discord.utils.get(ctx.guild.roles, id = int(role_id))
        except:
            # CHECK FOR ROLE NAMES
            try:
                the_role = await util.fetch_role_by_name(ctx, role_arg)
            except:
                emoji = util.emoji("pensive")
                await ctx.send(f"Error: No valid role argument. {emoji}")
                return

        # SANITY CHECK (MORE PERMS THAN REFERENCE ROLE?)

        default_perms = await util.get_defaultperms(ctx)

        higher_perms = []
        for perm in the_role.permissions:
            if perm[1]:
                if perm[0] not in default_perms:
                    higher_perms.append(perm[0])

        if 'manage_guild' in higher_perms:
            emoji = util.emoji("unleashed")
            await ctx.send(f"Error: I shall not make everyone to basically mods. Do you want chaos or something? {emoji}")
            return
        elif len(higher_perms) > 0:
            emoji = util.emoji("attention")
            permstring = ' '.join(higher_perms)
            await ctx.send(f"{emoji} Warning: The role you are about to assign to everyone has higher permissions.```{permstring}```"[:2000])


        # CONFIRMATION

        async with ctx.typing():

            await ctx.send(f"Are you sure you want to assign the {the_role.name} role to all current members? Respond with `yes` to confirm.")

            try: # waiting for message
                response = await self.bot.wait_for('message', check=lambda message: util.confirmation_check(ctx, message), timeout=30.0) # timeout - how long bot waits for message (in seconds)
            except asyncio.TimeoutError: # returning after timeout
                await ctx.send("action timed out")
                return

            # if response is different than yes / y - return
            if response.content.lower() not in ["yes", "y"]:
                await ctx.send("cancelled action")
                return

            # ASSIGN

            errors = []
            for member in ctx.guild.members:
                if the_role not in member.roles:
                    try:
                        await member.add_roles(the_role)
                    except:
                        errors.append(member.name)
        if len(errors) == 0:
            await ctx.send("Finished assigning role to everyone.")
        else:
            problemusers = ', '.join(errors)
            await ctx.send(f"Finished assigning role to everyone, except: {problemusers}"[:2000])
    @_removeicons.error
    async def removeicons_error(self, ctx, error):
        await util.error_handling(ctx, error)



    def mark_active_in_np_settings(self, user_id):
        # NPsettings change back to active
        conNP = sqlite3.connect('databases/npsettings.db')
        curNP = conNP.cursor()
        lfm_list = [[item[0],item[1].lower().strip()] for item in curNP.execute("SELECT lfm_name, details FROM lastfm WHERE id = ?", (str(user_id),)).fetchall()]

        if len(lfm_list) > 0:
            new_status = lfm_list[0][1].replace("inactive", "")
            if type(new_status) == str and len(new_status) > 0 and new_status[-1] == "_":
                new_status = new_status[:-1]
            curNP.execute("UPDATE lastfm SET details = ? WHERE id = ?", (new_status, str(user_id)))
            conNP.commit()



    @commands.command(name='letmeout', aliases = ['imactive', 'illbeactiveipromise', 'letmein'])
    @commands.check(util.inactivity_filter_enabled)
    @commands.check(util.is_active) 
    async def _recoverfrominactivity(self, ctx):
        """break out from inactivity channel
        """

        # FETCH ROLE
        
        conB = sqlite3.connect('databases/botsettings.db')
        curB = conB.cursor()

        inactivityrole_list = [item[0] for item in curB.execute("SELECT role_id FROM specialroles WHERE name = ?", ("inactivity role",)).fetchall()]        
        if len(inactivityrole_list) == 0 or not util.represents_integer(inactivityrole_list[0]):
            print("Error: Mods need to set an inactivity role!")
            return
        else:
            if len(inactivityrole_list) > 1:
                print("Warning: there are multiple inactivity role entries in the database")
            inactivity_role_id = int(inactivityrole_list[0])

        try:
            inactivity_role = ctx.guild.get_role(inactivity_role_id)
        except Exception as e:
            print("Error:", e)
            print("Error: Faulty inactivity role id!")
            return

        if inactivity_role is None:
            print("Error: Faulty inactivity role id!")
            return

        # CHECK IF USER HAS ROLE

        user = ctx.author

        if inactivity_role not in user.roles:
            await ctx.send("According to my check book you aren't marked as inactive.\nIf this is an error contact the mods.")
            self.mark_active_in_np_settings(str(user.id))
            return

        # FETCH PREVIOUS ROLES

        conUA = sqlite3.connect('databases/useractivity.db')
        curUA = conUA.cursor()
        prevroles_list = [item[0] for item in curUA.execute("SELECT previous_roles FROM useractivity WHERE userid = ?", (str(user.id),)).fetchall()]
        try:
            prevrole_idstrings = prevroles_list[0].split(";;")
            prevroles = []
            for role_id_str in prevrole_idstrings:
                if util.represents_integer(role_id_str):
                    role_id = int(role_id_str)
                    if role_id != inactivity_role_id:
                        try:
                            role = ctx.guild.get_role(role_id)
                            prevroles.append(role)
                        except Exception as e:
                            print(f"Error with role {role_id}: {e}")
                    else:
                        print("Warning: For some reason the user has the inactivity role in their previous roles.")

            # SWAP ROLES

            if len(prevroles) == 0:
                await user.remove_roles(inactivity_role)
            else:
                await user.edit(roles=prevroles)

        except Exception as e:
            print("Error:", e)

            prevroles = []

            # CHECK VERIFIED/COMMUNITY ROLE
            try:
                try:
                    if util.setting_enabled("access wall"):
                        verified_role_id = int([item[0] for item in curB.execute("SELECT role_id FROM specialroles WHERE name = ?", ("verified role",)).fetchall()][0])
                        verified_role = ctx.guild.get_role(verified_role_id)
                        prevroles.append(verified_role)
                except Exception as e:
                    print("Error:", e)
                try:
                    if util.setting_enabled("automatic role"):
                        community_role_id = [item[0].strip() for item in curB.execute("SELECT role_id FROM specialroles WHERE name = ?", ("community role",)).fetchall()]
                        community_role = ctx.guild.get_role(verified_role_id)
                        prevroles.append(community_role)
                except Exception as e:
                    print("Error:", e)
            except:
                pass

            try:
                await user.edit(roles=prevroles)
            except:
                await user.remove_roles(inactivity_role)

        await ctx.message.delete()

        # NOTIFY MODS

        bot_channel_id = int(os.getenv("bot_channel_id"))
        botspamchannel = self.bot.get_channel(bot_channel_id)
        emoji = util.emoji("unleashed")
        text = f"{user.mention} has broken out of inactivity! {emoji}"
        embed = discord.Embed(title="", description=text, color=0xffffff)
        embed.set_thumbnail(url="https://c.tenor.com/kekA7AIajFsAAAAd/tenor.gif")
        await botspamchannel.send(embed=embed)

        # UPDATE INACTIVITY DB

        now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())
        conUA = sqlite3.connect('databases/useractivity.db')
        curUA = conUA.cursor()
        curUA.execute("UPDATE useractivity SET last_active = ? WHERE userid = ?", (str(now), str(user.id)))
        conUA.commit()
        await util.changetimeupdate()

        self.mark_active_in_np_settings(str(user.id))
        
    @_recoverfrominactivity.error
    async def recoverfrominactivity_error(self, ctx, error):
        await util.error_handling(ctx, error)



async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(
        Roles(bot),
        guilds = [discord.Object(id = int(os.getenv("guild_id")))])