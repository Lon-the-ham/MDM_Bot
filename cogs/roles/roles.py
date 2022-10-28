import os
import datetime
import discord
from discord.ext import commands
import asyncio
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
import sys
import traceback


default_perms = ['create_instant_invite', 'add_reactions', 'stream', 'read_messages', 'send_messages', 'send_tts_messages', 'embed_links', 'attach_files', 'read_message_history', 'external_emojis', 'connect', 'speak', 'use_voice_activation', 'change_nickname', 'use_slash_commands', 'request_to_speak', 'use_application_commands', 'create_public_threads', 'create_private_threads', 'external_stickers', 'send_messages_in_threads', 'use_embedded_activities']  


class Roles(commands.Cog):
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



    @commands.command(name='color', aliases=['colour'])
    @commands.check(is_valid_server)
    #@commands.has_permissions(manage_guild=True)
    async def _color(self, ctx: commands.Context, *args):
        """Choose name color

        Choose your displayed user name color by using -color #<HEX code> or -color <color name>."""

        color_dictionary= {}
        user = ctx.message.author
        user_perms_full = [p for p in user.guild_permissions]
        user_perms = []
        for p in user_perms_full:
            if p[1]:
                user_perms.append(p[0])

        if 'manage_guild' in user_perms:
            mod_perms = True 
            assign_different_user = False
            the_color = 'FFFFFF'
            if len(args) >= 2:
                for member in ctx.guild.members:
                    mention = '<@%s>' % member.id
                    if args[0] == mention:
                        user = member
                        the_role = ' '.join(args[1:])
                        assign_different_user = True
                        break
            await ctx.send(f'Command under construction <:attention:961365426091229234>')
        else:
            mod_perms = False
            assign_different_user = False
            the_color = 'FFFFFF'
            await ctx.send(f'Command under construction <:attention:961365426091229234>')
    @_color.error
    async def color_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.channel.send(f'Error: This is a melodeathcord specific command.')
        else:
            await ctx.channel.send(f'An error ocurred.')

    
    @commands.command(name='roles', aliases=['ranks'])
    @commands.check(is_valid_server)
    #@commands.has_permissions(manage_guild=True)
    async def _roles(self, ctx: commands.Context):
        """Prints assignable roles

        Only roles without extra-permissions and of categories album, pronoun or other are assignable."""
        header = 'assignable roles:'
        descriptions = []

        con = sqlite3.connect('cogs/roles/roles.db')
        cur = con.cursor()
        #cur.execute('''CREATE TABLE IF NOT EXISTS roles (id text, name text, assignable text, category text, permissions text, color text, details text)''')

        categories = [item[0] for item in cur.execute("SELECT category FROM roles WHERE assignable = ? AND permissions = ?", ('True','')).fetchall()]
        categories = sorted(list(set(categories)))
        
        if len(categories) == 0:
            await ctx.send(f'There seem to be no assignable roles.. <:stones_weep:961183294010056724>')
        else:
            for cat in categories:
                message = ''
                roles = [item[0] for item in cur.execute("SELECT name FROM roles WHERE assignable = ? AND category = ? AND permissions = ?", ('True', str(cat), '')).fetchall()]
                for role in sorted(roles):
                    message = message + str(role) + '\n'
                descriptions.append(message)

            embed=discord.Embed(title=header, color=0xFFA500)
            for i in range(0,min(25, len(categories))): 
                cat = categories[i]
                embed.add_field(name=str(cat)+'s:', value=descriptions[i], inline=False)
            await ctx.send(embed=embed)
        #await ctx.message.add_reaction('<:wizard:1019019110572625952>')
    @_roles.error
    async def roles_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.channel.send(f'Error: This is a melodeathcord specific command.')
        else:
            await ctx.channel.send(f'An error ocurred.')


    @commands.command(name='role', aliases=['rank'])
    @commands.check(is_valid_server)
    async def _role(self, ctx: commands.Context, *args):
        """Assign/unassign role

        Use the role name (ids or role mentions currently do not work). Only roles without extra-permissions and of categories 'album', 'pronoun' or 'other' are assignable.

        Moderators can assign all roles without extra-permissions. To assign roles to other users use -role <@user mention> <role name>."""
        user = ctx.message.author
        guild = self.bot.get_guild('413011798552477716')
        all_roles = [r for r in ctx.guild.roles]
        con = sqlite3.connect('cogs/roles/roles.db')
        cur = con.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS roles (id text, name text, assignable text, category text, permissions text, color text, details text)''')

        user_perms_full = [p for p in user.guild_permissions]
        user_perms = []
        for p in user_perms_full:
            if p[1]:
                user_perms.append(p[0])

        #fetch all role names that user is allowed to assign
        if 'manage_guild' in user_perms:
            mod_perms = True 
            assign_different_user = False
            assignable_roles = [item[0] for item in cur.execute("SELECT name FROM roles WHERE permissions = ?", ('',)).fetchall()]
            the_role = ' '.join(args)
            if len(args) >= 2:
                for member in ctx.guild.members:
                    mention = '<@%s>' % member.id
                    if args[0] == mention:
                        user = member
                        the_role = ' '.join(args[1:])
                        assign_different_user = True
                        break
        else:
            mod_perms = False
            assign_different_user = False
            assignable_roles = [item[0] for item in cur.execute("SELECT name FROM roles WHERE assignable = ? AND permissions = ?", ('True','')).fetchall()]
            the_role = ' '.join(args)
        
        if len(assignable_roles) == 0:
            await ctx.send(f'There seem to be no assignable roles.. <:stones_weep:961183294010056724>')
        else:
            #get role id
            role_found = False
            for role in assignable_roles:
                if the_role.lower() == role.lower():
                    role_found = True
                    role_id_list = cur.execute("SELECT id FROM roles WHERE permissions = ? AND name = ? COLLATE NOCASE", ('', the_role.lower())).fetchall()
                    role_id = role_id_list[0][0]
                    break
            #assign/unassign
            if role_found:
                for role in all_roles:
                    if role_id == str(role.id):
                        #THIS IS THE ROLE
                        if role in user.roles:
                            await user.remove_roles(role)
                            if assign_different_user == False:
                                msg = 'Removed the role `%s` from you! <:attention:961365426091229234>' % role.name
                            else:
                                msg = 'Removed the role `%s` from %s! <:no:953795036426956841>' % (role.name, user.display_name)
                            await ctx.send(msg)
                        else:
                            await user.add_roles(role)
                            if assign_different_user == False:
                                msg = 'Assigned the role `%s` to you! <:wizard:1019019110572625952>' % role.name
                            else:
                                msg = 'Assigned the role `%s` to %s! <:pvmpkin:953790640444031026>' % (role.name,user.display_name)
                            await ctx.send(msg)
            else:
                if (mod_perms == False and assign_different_user == False and the_role.startswith('<@')):
                    await ctx.send('Seems like you do not have permission to do something like that... :/')
                else:
                    await ctx.send('This role is either not assignable or does not exist :(')
    @_role.error
    async def role_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.channel.send(f'Error: This is a melodeathcord specific command.')
        else:
            await ctx.channel.send(f'An error ocurred.')


    @commands.command(name='serverroles', aliases=['databaseroles', 'dbroles'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(is_valid_server)
    async def _serverroles(self, ctx: commands.Context):
        """*Prints all roles in db

        Only for server managers."""

        header = 'all roles in database:'
        descriptions = []

        con = sqlite3.connect('cogs/roles/roles.db')
        cur = con.cursor()
        #cur.execute('''CREATE TABLE IF NOT EXISTS roles (id text, name text, assignable text, category text, permissions text, color text, details text)''')

        categories = [item[0] for item in cur.execute("SELECT category FROM roles").fetchall()]
        categories = list(set(categories))
        
        if len(categories) == 0:
            await ctx.send(f'There seem to be no assignable roles.. <:stones_weep:961183294010056724>')
        else:
            for cat in categories:
                message = ''
                roles = [item[0] for item in cur.execute("SELECT name FROM roles WHERE category = ?", (str(cat),)).fetchall()]
                for role in sorted(roles):
                    message = message + str(role) + '\n'
                descriptions.append(message)

            embed=discord.Embed(title=header, color=0xFF8C00)
            for i in range(0,min(25, len(categories))): 
                cat = categories[i]
                plural = ''
                if cat in ['album', 'pronoun']:
                    plural = 's'
                embed.add_field(name=str(cat) + plural + ':', value=descriptions[i], inline=False)
            await ctx.send(embed=embed)
        #await ctx.message.add_reaction('<:wizard:1019019110572625952>')
    @_serverroles.error
    async def serverroles_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f'Sorry, you do not have permissions to do this!')
        elif isinstance(error, commands.CheckFailure):
            await ctx.channel.send(f'Error: This is a melodeathcord specific command.')
        else:
            await ctx.channel.send(f'An error ocurred.')


    @commands.command(name='userroles', aliases=['memberroles'])
    @commands.has_permissions(manage_guild=True, manage_roles=True)
    @commands.check(is_valid_server)
    async def _userroles(self, ctx, *args):
        """*Roles of user"""
        guild = self.bot.get_guild('413011798552477716')
        #default_perms = ['create_instant_invite', 'add_reactions', 'stream', 'read_messages', 'send_messages', 'send_tts_messages', 'embed_links', 'attach_files', 'read_message_history', 'external_emojis', 'connect', 'speak', 'use_voice_activation', 'change_nickname', 'use_slash_commands', 'request_to_speak', 'use_application_commands']    
        user_name = ' '.join(args)
        userlist = ctx.guild.members

        found = False
        for user in userlist:
            mention = '<@%s>' % user.id
            if user_name == mention:
                user_id = user
                found = True
                break
        if found == False:
            for user in userlist:
                if user_name == user.name or user_name == str(user.id):
                    user_id = user
                    found = True
                    break
        if found == False:
            for user in userlist:
                if user_name == user.display_name or user_name == user.nick:
                    user_id = user
                    found = True
                    break

        if found == False:
            await ctx.send("Could not find user :(")
        else:
            user_roles = []
            for role in user_id.roles:
                user_roles.append(role.name)
            user.roles.sort()
            print(user_roles)
            header = 'Roles of %s' % user_id
            embed = discord.Embed(title=header, description =', '.join(user_roles), color=0xFF8C00)
            await ctx.send(embed=embed)
            #await ctx.send("User has roles: ```" + ', '.join(user_roles) + '```')           
    @_userroles.error
    async def userroles_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f'Sorry, you do not have permissions to do this!')
        elif isinstance(error, commands.CheckFailure):
            await ctx.channel.send(f'Error: This is a melodeathcord specific command.')
        else:
            await ctx.channel.send(f'An error ocurred.')


    @commands.command(name='userperms', aliases=['memberperms', 'userpermissions', 'memberpermissions'])
    @commands.has_permissions(manage_guild=True, manage_roles=True)
    @commands.check(is_valid_server)
    async def _userperms(self, ctx, *args):
        """*Perms of user"""
        guild = self.bot.get_guild('413011798552477716')
        #default_perms = ['create_instant_invite', 'add_reactions', 'stream', 'read_messages', 'send_messages', 'send_tts_messages', 'embed_links', 'attach_files', 'read_message_history', 'external_emojis', 'connect', 'speak', 'use_voice_activation', 'change_nickname', 'use_slash_commands', 'request_to_speak', 'use_application_commands', 'create_public_threads', 'create_private_threads', 'external_stickers', 'send_messages_in_threads', 'use_embedded_activities']    
        user_name = ' '.join(args)
        userlist = ctx.guild.members

        found = False
        for user in userlist:
            mention = '<@%s>' % user.id
            if user_name == mention:
                user_id = user
                found = True
                break
        if found == False:
            for user in userlist:
                if user_name == user.name or user_name == str(user.id):
                    user_id = user
                    found = True
                    break
        if found == False:
            for user in userlist:
                if user_name == user.display_name or user_name == user.nick:
                    user_id = user
                    found = True
                    break

        if found == False:
            await ctx.send("Could not find user :(")
        else:
            print(user_id)
            user_perms_full = [p for p in user_id.guild_permissions]

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
                lowperms_msg = '\n```' + ', '.join(perms_low) + '```'
            if len(perms_high) == 0:
                highperms_msg = 'none\n'
            else:
                highperms_msg = '\n```' + ', '.join(perms_high) + '```'

            header = 'Permissions of %s' % str(user_id)
            embed = discord.Embed(title=header, color=0xFF8C00)
            embed.add_field(name='default permissions:', value=lowperms_msg, inline=False)
            embed.add_field(name='higher permissions:', value=highperms_msg, inline=False)
            await ctx.send(embed=embed)
    @_userperms.error
    async def userperms_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f'Sorry, you do not have permissions to do this!')
        elif isinstance(error, commands.CheckFailure):
            await ctx.channel.send(f'Error: This is a melodeathcord specific command.')
        else:
            await ctx.channel.send(f'An error ocurred.')


    @commands.command(name='whohasrole', aliases=['whohasrank'])
    @commands.check(is_valid_server)
    #@commands.has_permissions(manage_guild=True, manage_roles=True)
    async def _whohasrole(self, ctx, *args):
        """*Users with given role"""
        #guild = self.bot.get_guild('413011798552477716')
        server = ctx.message.guild

        role_name = (' '.join(args))
        role_id = server.roles[0]
        for role in server.roles:
            mention = '<@&%s>' % role.id
            if role_name == mention or role_name == role.name or role_name == str(role.id):
                role_id = role
                break
        else:
            await ctx.send("Role doesn't exist :(")
            return
        
        memberlist = ctx.guild.members
        members_w_t_role = []
        for member in memberlist:
            if role in member.roles:
                members_w_t_role.append(str(member))
        members_w_t_role.sort()
        header = "members with role %s are:" % role_name

        embed = discord.Embed(title=header, description='\n'.join(members_w_t_role), color=0xFF8C00)
        await ctx.send(embed=embed)          
    #@_whohasrole.error
    #async def whohasrole_error(ctx, error, *args):
    #    if isinstance(error, commands.MissingPermissions):
    #        await ctx.send(f'Sorry, you do not have permissions to do this!')
    @_whohasrole.error
    async def whohasrole_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.channel.send(f'Error: This is a melodeathcord specific command.')
        else:
            await ctx.channel.send(f'An error ocurred.')


    @commands.command(name='roleperms', aliases=['rankperms', 'rolepermissions', 'rankpermissions'])
    @commands.has_permissions(manage_guild=True, manage_roles=True)
    @commands.check(is_valid_server)
    async def _roleperms(self, ctx, *args):
        """*Permissions of a role

        Only for server managers."""
        #default_perms = ['create_instant_invite', 'add_reactions', 'stream', 'read_messages', 'send_messages', 'send_tts_messages', 'embed_links', 'attach_files', 'read_message_history', 'external_emojis', 'connect', 'speak', 'use_voice_activation', 'change_nickname', 'use_slash_commands', 'request_to_speak', 'use_application_commands']    
        the_role = ' '.join(args)
        guild = self.bot.get_guild('413011798552477716')
        all_roles = [[str(r.id),str(r.name),r.permissions] for r in ctx.guild.roles]
        #print(all_roles)

        found_role = False
        for role in all_roles:
            mention = '<@&%s>' % role[0]
            if the_role in [role[0], role[1], mention]:
                found_role = True

                #await ctx.send(f'found role! permissions:')
                try:
                    perm_list = [perm[0] for perm in role[2] if perm[1]]
                    perms_low = []
                    perms_high = []
                    for perm in perm_list:
                        if perm in default_perms:
                            perms_low.append(perm)
                        else:
                            perms_high.append(perm)

                    if len(perms_low) == 0:
                        lowperms_msg = 'none\n'
                    else:
                        lowperms_msg = '\n```' + ', '.join(perms_low) + '```'
                    if len(perms_high) == 0:
                        highperms_msg = 'none\n'
                    else:
                        highperms_msg = '\n```' + ', '.join(perms_high) + '```'

                    header = 'Permissions of role'
                    embed = discord.Embed(title=header, color=0xFF8C00)
                    embed.add_field(name='default permissions:', value=lowperms_msg, inline=False)
                    embed.add_field(name='higher permissions:', value=highperms_msg, inline=False)
                    await ctx.send(embed=embed)
                    #await ctx.send('default permissions: '+ lowperms_msg +'higher permissions: '+ highperms_msg)
                except:
                    await ctx.send('error with fetching permissions')
        if found_role == False:
            await ctx.send(f'did not find role :(')
    @_roleperms.error
    async def roleperms_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f'Sorry, you do not have permissions to do this!')
        elif isinstance(error, commands.CheckFailure):
            await ctx.channel.send(f'Error: This is a melodeathcord specific command.')
        else:
            await ctx.channel.send(f'An error ocurred.')


    @commands.command(name='roleupdate', aliases=['rankupdate'])
    @commands.has_permissions(manage_guild=True, manage_roles=True)
    @commands.check(is_valid_server)
    async def _roleupdate(self, ctx):
        """*Update role database

        Only for server managers."""
        con = sqlite3.connect('cogs/roles/roles.db')
        cur = con.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS roles (id text, name text, assignable text, category text, permissions text, color text, details text)''')

        known_ids = []
        r = cur.execute("SELECT id FROM roles")
        for row in r:
            known_ids.append(row[0])

        try:
            # add missing roles to db    
            guild = self.bot.get_guild('413011798552477716')
            existing_roles = [[str(r.id),str(r.name),'#' + str(r.color)[1:]] for r in ctx.guild.roles]
            for role in existing_roles:
                if not (role[0] in known_ids):
                    cur.execute("INSERT INTO roles VALUES (?, ?, ?, ?, ?, ?, ?)", (role[0], role[1], 'False', 'none', '', role[2], ''))
                    con.commit()

            # remove non-existing roles from db
            existing_role_ids = [r[0] for r in existing_roles]
            for role_id in known_ids:
                if not (role_id in existing_role_ids):
                    cur.execute("DELETE FROM roles WHERE id = ?", (role_id,))
                    con.commit()
            print('updated availability of roles')

            # update permissions and colors
            roles_n_perms = [[str(r.id), r.permissions, '#' + str(r.color)[1:]] for r in ctx.guild.roles]
            for rp in roles_n_perms:
                r_id = rp[0]
                r_col = rp[2]
                r_perm_list = [perm[0] for perm in rp[1] if perm[1]]
                #default_perms = ['create_instant_invite', 'add_reactions', 'stream', 'read_messages', 'send_messages', 'send_tts_messages', 'embed_links', 'attach_files', 'read_message_history', 'external_emojis', 'connect', 'speak', 'use_voice_activation', 'change_nickname', 'use_slash_commands', 'request_to_speak', 'use_application_commands']            
                r_perm_list_wodef = []
                for perm in r_perm_list:
                    if perm in default_perms:
                        pass
                    else:
                        r_perm_list_wodef.append(perm) 
                r_perms = ', '.join(r_perm_list_wodef)
                cur.execute("UPDATE roles SET permissions = ? WHERE id = ?", (str(r_perms), str(r_id)))
                cur.execute("UPDATE roles SET color = ? WHERE id = ?", (r_col, str(r_id)))
                con.commit()
            print('updated permissions of roles')

            #update names
            names = [[str(r.id), r.name] for r in ctx.guild.roles]
            for n in names:
                r_id = n[0]
                r_name = n[1]
                cur.execute("UPDATE roles SET name = ? WHERE id = ?", (str(r_name), str(r_id)))
                con.commit()
            print('updated permissions of roles')
            await ctx.send(f'Successfully updated role database! <:wizard:1019019110572625952>')
        except:
            await ctx.send(f'Some error occured... <:pikacry:959405314220888104>')
    @_roleupdate.error
    async def roleupdate_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f'Sorry, you do not have permissions to do this!')
        elif isinstance(error, commands.CheckFailure):
            await ctx.channel.send(f'Error: This is a melodeathcord specific command.')
        else:
            await ctx.channel.send(f'An error ocurred.')


    @commands.command(name='rolecat', aliases=['rankcat', 'rolecategory', 'rankcategory'])
    @commands.has_permissions(manage_guild=True, manage_roles=True)
    @commands.check(is_valid_server)
    async def _rolecat(self, ctx, *args):
        """*Change role category

        Use -role <role id or name> <category>. Categories cannot have spaces. Only for server managers. """
        try:
            arglen = len(args)
            rolename = " ".join(args[0:arglen-1])
            category = args[arglen-1].lower()

            if category == 'pronouns':
                category = 'pronoun'
            if category == 'albums':
                category = 'album'
            if category == 'others':
                category = 'other'
                
            assignable_categories = ['album', 'pronoun', 'other']

            con = sqlite3.connect('cogs/roles/roles.db')
            cur = con.cursor()

            dementioned_rolename = rolename.replace("<","").replace(">","").replace("@","").replace("&","")

            if dementioned_rolename.isnumeric():
                # argument is probably the roles id
                entries = [item for item in cur.execute("SELECT id FROM roles WHERE id = ?", (dementioned_rolename,)).fetchall()]
                if len(entries) == 0:
                    await ctx.send(f'this role does not seem to exist in the database <:pikacry:959405314220888104>')
                else:
                    if category in assignable_categories:
                        cur.execute("UPDATE roles SET category = ?, assignable = ? WHERE id = ?", (category, 'True', entries[0]))
                    else:
                        cur.execute("UPDATE roles SET category = ?, assignable = ? WHERE id = ?", (category, 'False', entries[0]))
                    con.commit()
                    await ctx.send(f'Successfully changed category of `' + rolename + '` to ' + category + '! <:wizard:1019019110572625952>')
            else:
                # argument is probably the roles name
                entries = [item for item in cur.execute("SELECT name FROM roles WHERE name = ?", (rolename,)).fetchall()]
                if len(entries) == 0:
                    await ctx.send(f'this role does not seem to exist in the database <:pikacry:959405314220888104>')
                else:
                    if category in assignable_categories:
                        cur.execute("UPDATE roles SET category = ?, assignable = ? WHERE name = ?", (category, 'True', rolename))
                    else:
                        cur.execute("UPDATE roles SET category = ?, assignable = ? WHERE name = ?", (category, 'False', rolename))
                    con.commit()
                    await ctx.send(f'Successfully changed category of `' + rolename + '` to ' + category + '! <:wizard:1019019110572625952>')
        except Exception as e:
            print(e)
            await ctx.send(f'Some error occured... <:pikacry:959405314220888104>')
    @_rolecat.error
    async def rolecat_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f'Sorry, you do not have permissions to do this!')
        elif isinstance(error, commands.CheckFailure):
            await ctx.channel.send(f'Error: This is a melodeathcord specific command.')
        else:
            await ctx.channel.send(f'An error ocurred.')


    @commands.command(name='rolecol', aliases=['rolecolor', 'rolecolour', 'rankcol', 'cankcolor', 'rankcolour'])
    @commands.has_permissions(manage_guild=True, manage_roles=True)
    @commands.check(is_valid_server)
    async def _rolecolor(self, ctx, *args):
        """*Change role color

        Use -rolecol <role id or name> #<HEX code>. Only for server managers."""
        try:
            arglen = len(args)
            rolename = " ".join(args[0:arglen-1])
            color = args[arglen-1]

            hexmatch = re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', color)
            if hexmatch:
                hex_color = int(color.replace("#",""), 16)
                con = sqlite3.connect('cogs/roles/roles.db')
                cur = con.cursor()

                dementioned_rolename = rolename.replace("<","").replace(">","").replace("@","").replace("&","")

                if dementioned_rolename.isnumeric():
                    # argument is probably the roles id
                    role = discord.utils.get(member.guild.roles, id=dementioned_rolename)
                    await role.edit(colour=discord.Colour(hex_color))
                    #db
                    entries = [item for item in cur.execute("SELECT id FROM roles WHERE id = ?", (dementioned_rolename,)).fetchall()]
                    if len(entries) == 0:
                        await ctx.send(f'this role does not seem to exist in the database <:pikacry:959405314220888104>')
                    else:
                        cur.execute("UPDATE roles SET color = ? WHERE id = ?", (color, entries[0]))
                        con.commit()
                        msg = 'Successfully changed color of `' + rolename + '` to ' + color + '! <:wizard:1019019110572625952>'
                        embed = discord.Embed(description=msg, color=hex_color)
                        await ctx.send(embed=embed)
                else:
                    # argument is probably the roles name
                    role = discord.utils.get(ctx.guild.roles, name=rolename)
                    await role.edit(colour=discord.Colour(hex_color))
                    #db
                    entries = [item for item in cur.execute("SELECT name FROM roles WHERE name = ?", (rolename,)).fetchall()]
                    if len(entries) == 0:
                        await ctx.send(f'this role does not seem to exist in the database <:pikacry:959405314220888104>')
                    else:
                        cur.execute("UPDATE roles SET color = ? WHERE name = ?", (color, rolename))
                        con.commit()
                        msg = 'Successfully changed color of `' + rolename + '` to ' + color + '! <:wizard:1019019110572625952>'
                        embed = discord.Embed(description=msg, color=hex_color)
                        await ctx.send(embed=embed)
            else:
                await ctx.send(f'That is not a valid HEX color entry... <:cryers_of_the_plague:969570217439137792>')
        except Exception as e:
            print(e)
            await ctx.send(f'Some error occured... <:pikacry:959405314220888104>')
    @_rolecolor.error
    async def rolecolor_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f'Sorry, you do not have permissions to do this!')
        elif isinstance(error, commands.CheckFailure):
            await ctx.channel.send(f'Error: This is a melodeathcord specific command.')
        else:
            await ctx.channel.send(f'An error ocurred.')


    @commands.command(name='newrole', aliases=['newrank', 'createrole', 'createrank'])
    @commands.has_permissions(manage_guild=True, manage_roles=True)
    @commands.check(is_valid_server)
    async def _newrole(self, ctx, *args):
        """*Creates permissionless role

        Use -newrole <category> #<HEX code> <new role name> to create new role. Category and Hex code are optional. Category must be either album, pronoun, color or other, while HEX code must start with an #."""
        role_name = ' '.join(args)

        HEX_code = '#FFFFFF'
        category = 'none'
        default_hex = True 
        default_cat = True
        if len(args) >= 2:
            match_0 = re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', args[0])
            if match_0:
                HEX_code = args[0]
                default_hex = False
                role_name = ' '.join(args[1:])
                if args[1].lower() in ['album', 'albums', 'pronoun', 'pronouns', 'other', 'others', 'none', 'nones','color', 'colour', 'colors', 'colours']:
                    category = args[1].lower()
                    default_cat = False
                    if category[-1] == 's': category = category[:-1]
                    role_name = ''
                    if len(args) >=3:
                        role_name = ' '.join(args[2:])
            match_1 = re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', args[1])
            if args[0].lower() in ['album', 'albums', 'pronoun', 'pronouns', 'other', 'others', 'none', 'nones','color', 'colour', 'colors', 'colours']:
                category = args[0].lower()
                default_cat = False
                role_name = ' '.join(args[1:])
                if category[-1] == 's': category = category[:-1]
                if match_1:
                    HEX_code = args[1]
                    default_hex = False
                    role_name = ''
                    if len(args) >=3:
                        role_name = ' '.join(args[2:])
        print(category)
        print(HEX_code)
        print(role_name)
        #check if role already exists
        guild = self.bot.get_guild('413011798552477716')
        all_roles = [str(r.name).lower() for r in ctx.guild.roles]
        if role_name.lower() in all_roles:
            await ctx.send('Role with this name already exists! <:surprisedpikachu:934595236859109377>')
        else:
            discord_hex = int(HEX_code[1:], 16)
            guild = ctx.guild
            role = await guild.create_role(name=role_name, color=discord_hex) 
            con = sqlite3.connect('cogs/roles/roles.db')
            cur = con.cursor()
            msg = 'Created role: %s\nof category: %s\nwith HEX color: %s' % (role_name, category, HEX_code)
            embed = discord.Embed(description=msg, color=discord_hex)
            if category.lower() in ['none','nones']:
                cur.execute("INSERT INTO roles VALUES (?, ?, ?, ?, ?, ?, ?)", (str(role.id), role_name, 'False', 'none', '', HEX_code, ''))
                con.commit()
            elif category.lower() in ['color', 'colour', 'colors', 'colours']:
                cur.execute("INSERT INTO roles VALUES (?, ?, ?, ?, ?, ?, ?)", (str(role.id), role_name, 'False', 'color', '', HEX_code, ''))
                con.commit()
            else:
                cur.execute("INSERT INTO roles VALUES (?, ?, ?, ?, ?, ?, ?)", (str(role.id), role_name, 'True', category, '', HEX_code, ''))
                con.commit()
            await ctx.send(embed=embed)
    @_newrole.error
    async def newrole_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f'Sorry, you do not have permissions to do this!')
        elif isinstance(error, commands.CheckFailure):
            await ctx.channel.send(f'Error: This is a melodeathcord specific command.')
        else:
            await ctx.channel.send(f'An error ocurred.')


    @commands.command(name='removerole', aliases=['removerank', 'deleterole', 'deleterank'])
    @commands.has_permissions(manage_guild=True, manage_roles=True)
    @commands.check(is_valid_server)
    async def _removerole(self, ctx, *args):
        """*Deletes role"""
        role_to_delete = ' '.join(args)
        guild = self.bot.get_guild('413011798552477716')
        #default_perms = ['create_instant_invite', 'add_reactions', 'stream', 'read_messages', 'send_messages', 'send_tts_messages', 'embed_links', 'attach_files', 'read_message_history', 'external_emojis', 'connect', 'speak', 'use_voice_activation', 'change_nickname', 'use_slash_commands', 'request_to_speak', 'use_application_commands']                            
        all_roles = [r for r in ctx.guild.roles]

        role_found = False
        for role in all_roles:
            mention = '<@&%s>' % str(role.id)
            if role_to_delete == str(role.id) or role_to_delete == mention:
                role_found = True
                the_role = role
                break
        if role_found == False:
            for role in all_roles:
                if role_to_delete.lower() == role.name.lower():
                    role_found = True
                    the_role = role
                    break

        if role_found == True:
            perm_list = [perm[0] for perm in the_role.permissions if perm[1]]
            perms_low = []
            perms_high = []
            for perm in perm_list:
                if perm in default_perms:
                    perms_low.append(perm)
                else:
                    perms_high.append(perm)

            if len(perms_high) == 0:
                try:
                    #await ctx.guild.delete_role(the_role)
                    await the_role.delete()
                    con = sqlite3.connect('cogs/roles/roles.db')
                    cur = con.cursor()
                    cur.execute("DELETE FROM roles WHERE id = ?", (str(the_role.id),))
                    con.commit()
                    await ctx.send("The role `{}` haveth been deleted! <:hellmo:954376033921040425>".format(the_role.name))
                except:
                    await ctx.send("Some error occured! <:cryers_of_the_plague:969570217439137792>")
            else:
                await ctx.send(f"This role has higher permissions. I don't want to fiddle with that. <:mildpanic:960328452911800340>")
        else:
            await ctx.send(f'This role seems to not exist... :O')
    @_removerole.error
    async def removerole_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f'Sorry, you do not have permissions to do this!')
        elif isinstance(error, commands.CheckFailure):
            await ctx.channel.send(f'Error: This is a melodeathcord specific command.')
        else:
            await ctx.channel.send(f'An error ocurred.')


    @commands.command(name='roleicon', aliases = ['seticon', 'setroleicon', 'roleemoji', 'rolesemoji', 'rolemoji'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(is_valid_server)
    async def _roleicon(self, ctx: commands.Context, *args):
        """*Changes react-moji

        Write -roleicon <role> <emoji>
        """
        try:
            arglen = len(args)
            rolename = " ".join(args[0:arglen-1])
            icon = args[arglen-1]

            con = sqlite3.connect('cogs/roles/roles.db')
            cur = con.cursor()

            emoji_valid = False
            if icon in UNICODE_EMOJI['en']:
                print('%s is an emoji' % str(icon))

                matching_emojis = [item for item in cur.execute("SELECT name FROM roles WHERE details = ?", (icon,)).fetchall()]
                if len(matching_emojis) == 0:
                    print('%s not in use. good.' % str(icon))
                    emoji_valid = True
                else:
                    msg = "Action cancelled. This emoji (%s) is already in use by role `%s`! <:attention:961365426091229234>" % (str(icon), str(matching_emojis[0][0]))
                    await ctx.send(msg)
            else:
                await  ctx.send(f'I do not recognise this emoji <:derpy:955227738690687048> (also custom emojis are not allowed... yet.)')



            if emoji_valid:
                dementioned_rolename = rolename.replace("<","").replace(">","").replace("@","").replace("&","")

                if dementioned_rolename.isnumeric():
                    # argument is probably the roles id
                    role = discord.utils.get(member.guild.roles, id=dementioned_rolename)
                    #db
                    entries = [item for item in cur.execute("SELECT id FROM roles WHERE id = ?", (dementioned_rolename,)).fetchall()]
                    if len(entries) == 0:
                        await ctx.send(f'this role does not seem to exist in the database <:pikacry:959405314220888104>')
                    else:
                        cur.execute("UPDATE roles SET details = ? WHERE id = ?", (icon, entries[0]))
                        con.commit()
                        msg = 'Successfully changed the reaction emoji of `' + rolename + '` to ' + icon + '! <:wizard:1019019110572625952>'
                        embed = discord.Embed(description=msg, color=0xFFA500)
                        await ctx.send(embed=embed)
                else:
                    # argument is probably the roles name
                    role = discord.utils.get(ctx.guild.roles, name=rolename)
                    #db
                    entries = [item for item in cur.execute("SELECT name FROM roles WHERE name = ?", (rolename,)).fetchall()]
                    if len(entries) == 0:
                        await ctx.send(f'this role does not seem to exist in the database <:pikacry:959405314220888104>')
                    else:
                        cur.execute("UPDATE roles SET details = ? WHERE name = ?", (icon, rolename))
                        con.commit()
                        msg = 'Successfully changed the reaction emoji of `' + rolename + '` to ' + icon + '! <:wizard:1019019110572625952>'
                        embed = discord.Embed(description=msg, color=0xFFA500)
                        await ctx.send(embed=embed)
        except Exception as e:
            print(e)
            await ctx.send(f'Some error occured... <:pikacry:959405314220888104>')
    @_roleicon.error
    async def roleicon_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f'Sorry, you do not have permissions to do this!')
        elif isinstance(error, commands.CheckFailure):
            await ctx.channel.send(f'Error: This is a melodeathcord specific command.')
        else:
            await ctx.channel.send(f'An error ocurred.') 


    @commands.command(name='rcupdate', aliases = ['rolechannelupdate', 'roleschannelupdate', 'rolechannelup', 'roleschannelup', 'rcup'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(is_valid_server)
    async def _rcupdate(self, ctx: commands.Context):
        """*Update #roles

        deletes all messages, and creates new ones with updated roles. use -roleupdate before this
        """
        print("Updating #roles channel!")
        existing_roles = [str(r.id) for r in ctx.guild.roles]
        con = sqlite3.connect('cogs/roles/roles.db')
        cur = con.cursor()
        color_roles = [[item[0], item[1], item[2]] for item in cur.execute("SELECT id,name, details FROM roles WHERE category = ?", ("color",)).fetchall()]
        pronoun_roles = [[item[0], item[1], item[2]] for item in cur.execute("SELECT id,name, details FROM roles WHERE category = ?", ("pronoun",)).fetchall()]
        other_roles = [[item[0], item[1], item[2]] for item in cur.execute("SELECT id,name, details FROM roles WHERE category = ?", ("other",)).fetchall()]

        for channel in ctx.guild.text_channels:
                if str(channel.name).lower() == "roles":
                    the_channel = channel
                    break 

        print("fetching roles...")
        existing_color_roles = []
        existing_pronoun_roles = []
        existing_other_roles = []
        for role_id in existing_roles:
            # get all color roles
            for c_role in color_roles:
                if role_id == c_role[0]:
                    existing_color_roles.append(c_role)
            # get all pronoun roles
            for p_role in pronoun_roles:
                if role_id == p_role[0]:
                    existing_pronoun_roles.append(p_role)
            # get all other roles
            for o_role in other_roles:
                if role_id == o_role[0]:
                    existing_other_roles.append(o_role)


        # delete all messages in #roles
        print("deleting old messages...")
        await the_channel.purge(limit=10)

        # make new message with all color roles
        print("preparing colour role message")
        color_role_string = ""
        for c_role in reversed(existing_color_roles):
            mention = "<@&%s>" % c_role[0]
            color_role_string = color_role_string + c_role[2] + " " + mention + "\n"
        msg1 = color_role_string #+ "🚫 Remove colour"
        embed1 = discord.Embed(title="React to choose a name colour!", description=msg1, color=0x990000)
        embed1.set_footer(text = "A second react will automatically remove the role from your first react.")
        message1 = await the_channel.send(embed=embed1)
        # add reactions to them
        for c_role in reversed(existing_color_roles):
            try:
                await message1.add_reaction(c_role[2])
            except:
                error_message = "Error in trying to add reaction %s" % (c_role[2])
                await ctx.send(error_message)
        #try:
        #    await message1.add_reaction("🚫")
        #except:
        #    error_message = "Error in trying to add reaction %s" % ("🚫")
        #    await ctx.send(error_message)

        # make new message with all pronoun roles
        print("preparing pronoun role message")
        pronoun_role_string = ""
        for p_role in reversed(existing_pronoun_roles):
            mention = "<@&%s>" % p_role[0]
            pronoun_role_string = pronoun_role_string + p_role[2] + " " + mention + "\n"
        msg2 = pronoun_role_string #+ "❌ Remove pronouns."
        embed2 = discord.Embed(title="React to choose your pronouns!", description=msg2, color=0x990000)
        embed2.set_footer(text = "Remove react to remove role.")
        message2 = await the_channel.send(embed=embed2)
        # add reactions to them
        for p_role in reversed(existing_pronoun_roles):
            try:
                await message2.add_reaction(p_role[2])
            except:
                error_message = "Error in trying to add reaction %s" % (p_role[2])
                await ctx.send(error_message)
        #try:
        #    await message2.add_reaction("❌")
        #except:
        #    error_message = "Error in trying to add reaction %s" % ("❌")
        #    await ctx.send(error_message)


        # make new message with all other roles
        print("preparing other role message")
        other_role_string = ""
        for o_role in reversed(existing_other_roles):
            mention = "<@&%s>" % o_role[0]
            other_role_string = other_role_string + o_role[2] + " " + mention + "\n"
        msg3 = "If you want to get pinged whenever there will be an album exchange or a listening party, or if you want to be indentified as e.g. musician, go grab some of these roles here!\n\n" + other_role_string
        embed3 = discord.Embed(title="React to choose some extra roles!", description=msg3, color=0x990000)
        embed3.set_footer(text = "To get other roles like album roles go to #bot-commands and use -role <role name> to assign/unassign a role.\nUse -roles to get a list of all assignable roles.")
        message3 = await the_channel.send(embed=embed3)
        # add reactions to them
        for o_role in reversed(existing_other_roles):
            try:
                await message3.add_reaction(o_role[2])
            except:
                error_message = "Error in trying to add reaction %s" % (o_role[2])
                await ctx.send(error_message)
        
    @_rcupdate.error
    async def rcupdate_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f'Sorry, you do not have permissions to do this!')
        elif isinstance(error, commands.CheckFailure):
            await ctx.channel.send(f'Error: This is a melodeathcord specific command.')
        else:
            await ctx.channel.send(f'An error ocurred.')




async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(
        Roles(bot),
        guilds = [discord.Object(id = 413011798552477716)])