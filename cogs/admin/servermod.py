import discord
from discord.ext import commands

class ServerModeration(commands.Cog):
    def __init__(self, bot: commands.bot) -> None:
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
        

    @commands.command(name='ban', aliases = ['userban'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(is_valid_server)
    async def _ban(self, ctx: commands.Context, *args):
        """*Bans user

        """
        if len(args) >= 1:
            user_arg = args[0]
            if len(args) >= 2:
                reason = ' '.join(args[1:])
            else:
                reason = ""

            print("parsing...")
            user_id = user_arg
            if len(user_arg) > 3:
                if user_arg[0] == "<" and user_arg[1] == "@" and user_arg[-1] == ">":
                    #user_id = user_arg[2:-1]
                    user_id = user_arg.replace("<@", "").replace(">","")

            print(f"banning user: {user_id} \nfor reason: {reason}")
            if reason == "":
                reason_string = ""
            else:
                reason_string = "\nReason: " + reason 

            immunity_list = ["586358910148018189", "958105284759400559"]

            if user_id in immunity_list:
                await ctx.send('I- I really do not want to ban this user. <:hampleading:1017443036843753553>')
            else:
                try:
                    user = await self.bot.fetch_user(user_id)
                    await ctx.guild.ban(user, reason=reason, delete_message_days=0)
                    await ctx.send(f'Banned <@{user_id}>. <:banbun:1075093521553440799>{reason_string}')
                except:
                    await ctx.send('Error in user argument')
        else:
            await ctx.send('Error: missing arguments')
    @_ban.error
    async def ban_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f'Sorry, you do not have permissions to do this!')
        elif isinstance(error, commands.CheckFailure):
            await ctx.channel.send(f'Error: This is a melodeathcord specific command.')
        else:
            await ctx.channel.send(f'An error ocurred.')


    @commands.command(name='kick', aliases = ['userkick'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(is_valid_server)
    async def _kick(self, ctx: commands.Context, *args):
        """*Kicks user

        """
        if len(args) >= 1:
            user_arg = args[0]
            if len(args) >= 2:
                reason = ' '.join(args[1:])
            else:
                reason = ""

            print("parsing...")
            user_id = user_arg
            if len(user_arg) > 3:
                if user_arg[0] == "<" and user_arg[1] == "@" and user_arg[-1] == ">":
                    user_id = user_arg.replace("<@", "").replace(">","")

            print(f"banning user: {user_id} \nfor reason: {reason}")
            if reason == "":
                reason_string = ""
            else:
                reason_string = "\nReason: " + reason 

            immunity_list = ["586358910148018189", "958105284759400559"]

            if user_id in immunity_list:
                await ctx.send('I- I really do not want to kick this user. <:hampleading:1017443036843753553>')
            else:
                try:
                    user = await self.bot.fetch_user(user_id)
                    await ctx.guild.kick(user, reason=reason)
                    await ctx.send(f'Kicked <@{user_id}>. <:jacegun:1035530576494604409>{reason_string}')
                except:
                    await ctx.send('Error in user argument')
        else:
            await ctx.send('Error: missing arguments')
    @_kick.error
    async def kick_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f'Sorry, you do not have permissions to do this!')
        elif isinstance(error, commands.CheckFailure):
            await ctx.channel.send(f'Error: This is a melodeathcord specific command.')
        else:
            await ctx.channel.send(f'An error ocurred.')


    @commands.command(name='unban', aliases = ['userunban'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(is_valid_server)
    async def _unban(self, ctx: commands.Context, *args):
        """*Unbans user

        """
        if len(args) >= 1:
            user_arg = args[0]
            if len(args) >= 2:
                reason = ' '.join(args[1:])
            else:
                reason = ""

            print("parsing...")
            user_id = user_arg
            if len(user_arg) > 3:
                if user_arg[0] == "<" and user_arg[1] == "@" and user_arg[-1] == ">":
                    user_id = user_arg[2:-1]

            print(f"unbanning user: {user_arg} \nfor reason: {reason}")

            try:
                user = await self.bot.fetch_user(user_id)
                await ctx.guild.unban(user)
                await ctx.send(f'Unbanned <@{user_id}>. <:celebrate:1017439343746482206>')
            except:
                await ctx.send('Error in user argument')
        else:
            await ctx.send('Error: missing arguments')
    @_unban.error
    async def unban_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f'Sorry, you do not have permissions to do this!')
        elif isinstance(error, commands.CheckFailure):
            await ctx.channel.send(f'Error: This is a melodeathcord specific command.')
        else:
            await ctx.channel.send(f'An error ocurred.')




    @commands.command(name='mute', aliases = ['usermute','silence'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(is_valid_server)
    async def _mute(self, ctx: commands.Context, *args):
        """*Mutes user

        Write -mute <@id> to mute a user indefinitely.
        Write -mute <@id> <time> to mute user for given time.
        <time> has to be in the format: <integer><m/h/d>

        Everything after will be part of the mute reason.
        """
        if len(args) >= 1:
            # first argument
            user_arg = args[0]

            print("mute. getting id:")
            user_id = user_arg
            if len(user_arg) > 3:
                if user_arg[0] == "<" and user_arg[1] == "@" and user_arg[-1] == ">":
                    user_id = user_arg[2:-1]
            print(user_id)

            muting_time = "infinity"
            time_num = -1
            reason = "none"

            # second argument
            if len(args) >= 2:
                muting_time = args[1]

                try:    
                    time_as_num = int(muting_time)
                    time_is_num = True
                except:
                    time_is_num = False

                if time_is_num:
                    time_num = time_as_num
                    if len(args) >= 3:
                        time_unit = args[2]
                    if len(args) >=4:
                        reason = ' '.join(args[3:])

                else:
                    if len(args) >=3:
                        reason = ' '.join(args[2:])

                    time_alpha = ''
                    time_unit = ''
                    still_number_part = True
                    for c in muting_time:
                        if c in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'] and still_number_part:
                            time_alpha = time_alpha + c
                        else:
                            still_number_part = False 
                            time_unit = time_unit + c

                    try:
                        time_num = int(time_alpha)
                    except:
                        time_num = -1
                        print('Error with time argument')

            ##############
            #going further

            try:
                id_as_num = int(user_id)
                id_is_num = True 
            except:
                id_is_num = False

            if id_is_num:
                proceed = False
                immunity_list = ["586358910148018189", "958105284759400559"]
                if user_id in immunity_list:
                    await ctx.send('I- I really do not want to mute this user. <:hampleading:1017443036843753553>')
                else:
                    proceed = True
                    try:
                        print("guild:")
                        guild = ctx.guild
                        print(guild)
                        print("user:")
                        user = ctx.guild.get_member(int(user_id))
                        print(str(user))
                    except:
                        await ctx.send('Error in user argument')
                        proceed = False

                if proceed:
                    if time_num < 0:
                        try:
                            print("trying to assign")
                            #await user.edit(mute = True)
                            guild = ctx.guild
                            mute_role = discord.utils.get(guild.roles, name = "Timeout")
                            print(str(mute_role))

                            await user.add_roles(mute_role)
                            await ctx.send(f"Muted {user.display_name} indefinitely. <:nospeakpichu:975062505816727613>")
                        except Exception as e:
                            print(e)
                            await ctx.send('Error: I could not mute this user.\n' + str(e))
                    else:
                        if time_unit.lower() in ['m','min','minute','minutes']:
                            multiplier = 60
                            unit = 'minute(s)'
                        elif time_unit.lower() in ['h','hour','hours']:
                            multiplier = 60*60 
                            unit = 'hour(s)'
                        elif time_unit.lower() in ['d','day','days', 'dayz']:
                            multiplier = 60*60*24 
                            unit = 'day(s)'
                        elif time_unit.lower() in ['mon','month','months', 'moon', 'moons']:
                            multiplier = 60*60*24*(29 + 1/2)
                            unit = 'moon(s) 🌙'
                        #elif time_unit.lower() in ['s','sec','secs', 'second', 'seconds']:
                        #    multiplier = 1
                        #    unit = 'second(s)'
                        else:
                            proceed = False 
                            await ctx.send('Error: Time unit not supported.')

                        if proceed:
                            seconds_muted = time_num * multiplier
                            try:
                                #await user.edit(mute = True)
                                guild = ctx.guild
                                mute_role = discord.utils.get(guild.roles, name = "Timeout")
                                await user.add_roles(mute_role)
                                await ctx.send(f"Muted {user.display_name} for about {time_num} {unit}. <:nospeakpichu:975062505816727613>")
                            except:
                                await ctx.send('Error: I could not mute this user.')

                            try:
                                # UNDER CONSTRUCTION

                                # idea: put into db the timestamp when to unmute a specific user
                                # and then have a cronjob to check every now and then whether
                                # enough time has passed to unmute

                                x = int("this is not a number")
                                #conunm = sqlite3.connect('other/unmuting.db')
                                #curunm = conunm.cursor()
                                #curunm.execute('''CREATE TABLE IF NOT EXISTS unmuting (userid text, username text, mute_reason text, muted_time text, unmuting_time text, pending text)''')
                                
                                #curunm.execute("INSERT INTO unmuting VALUES (?, ?, ?, ?, ?, ?)", ())
                                #conunm.commit()
                            except:
                                await ctx.send('Uh..')
                                await ctx.send(f'I have problems with the unmuting at given time. Mute is indefinite now. <:batwelp:1014849421906804806>')
            else:
                await ctx.send('Error: user id ')
        else:
            await ctx.send('Error: missing arguments')
    @_mute.error
    async def mute_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f'Sorry, you do not have permissions to do this!')
        elif isinstance(error, commands.CheckFailure):
            await ctx.channel.send(f'Error: This is a melodeathcord specific command.')
        else:
            await ctx.channel.send(f'An error ocurred.')



    @commands.command(name='unmute', aliases = ['unusermute','unsilence'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(is_valid_server)
    async def _unmute(self, ctx: commands.Context, *args):
        """*Unmutes user

        """
        if len(args) >= 1:
            user_arg = args[0]
            if len(args) >= 2:
                reason = ' '.join(args[1:])
            else:
                reason = ""

            print("parsing...")
            user_id = user_arg
            if len(user_arg) > 3:
                if user_arg[0] == "<" and user_arg[1] == "@" and user_arg[-1] == ">":
                    user_id = user_arg[2:-1]

            print(f"unmuting user: {user_arg} \nfor reason: {reason}")

            try:
                print("fetching role")
                guild = ctx.guild
                mute_role = discord.utils.get(guild.roles, name = "Timeout")
                print("fetching user")
                user = ctx.guild.get_member(int(user_id))
                print(str(user))
                #await user.edit(mute = False)
                await user.remove_roles(mute_role)
                await ctx.send(f'User {user.display_name} unmuted <a:elmoburnbutcute:1039866486346493958>')
            except:
                await ctx.send('Error in user argument')
        else:
            await ctx.send('Error: missing arguments')
    @_unmute.error
    async def unmute_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f'Sorry, you do not have permissions to do this!')
        elif isinstance(error, commands.CheckFailure):
            await ctx.channel.send(f'Error: This is a melodeathcord specific command.')
        else:
            await ctx.channel.send(f'An error ocurred.')



    @commands.command(name='batchban', aliases = ['userbatchban'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(is_valid_server)
    async def _batchban(self, ctx, *args):
        """*Bans users
        
        use '-batchban <reason>' and attach a txt file with 1 id per row
        """
        attachment_url = ctx.message.attachments[0].url
        file_request = requests.get(attachment_url)
        #print(file_request.content)

        file_content = file_request.text 
        print(file_content)
        id_list = file_content.split("\n")

        reason = ' '.join(args[0:])
        print(f"ban reason: {reason}")

        successful_bans = []
        unsuccessful = []

        for uid in id_list:
            user_id = uid.strip()

            print(f"banning user: {user_id}")

            immunity_list = ["586358910148018189", "958105284759400559"]

            if user_id in immunity_list:
                print("user immune to ban...")
                unsuccessful.append(user_id)
            else:
                try:
                    user = await self.bot.fetch_user(user_id)
                    await ctx.guild.ban(user, reason=reason, delete_message_days=0)
                    successful_bans.append(user_id)
                    print("ban successful!!!")
                except:
                    unsuccessful.append(user_id)
                    print("ban unsuccessful :(")

        unsuccessful = list(dict.fromkeys(unsuccessful))
        successful_bans = list(dict.fromkeys(successful_bans))
        await ctx.send(f"Batch ban finished.\nSuccessfully banned: {len(successful_bans)}\nUnsuccsessful attempts: {len(unsuccessful)}")
        print(unsuccessful)
    @_batchban.error
    async def batchban_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f'Sorry, you do not have permissions to do this!')
        elif isinstance(error, commands.CheckFailure):
            await ctx.channel.send(f'Error: This is a melodeathcord specific command.')
        else:
            await ctx.channel.send(f'An error ocurred.')



    @commands.command(name='verify', aliases = ['verif','verified','verifying'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(is_valid_server)
    async def _verify(self, ctx: commands.Context, *args):
        """*Verifies user
        
        use "-verify <user_id or @mention>" to remove gate-role, add verified-role and put a welcome message in #general.
        you can put as addition argument "nomsg" to leave out the last step and verify them without a welcome message.
        """
        if len(args) >= 1:
            user_arg = args[0]
            if len(args) >= 2:
                specification = ' '.join(args[1:])
            else:
                specification = ""

            print("parsing...")
            user_id = user_arg
            if len(user_arg) > 3:
                if user_arg[0] == "<" and user_arg[1] == "@" and user_arg[-1] == ">":
                    user_id = user_arg.replace("<@", "").replace(">","")

            proceed = True
            try:
                guild = ctx.guild
                user = ctx.guild.get_member(int(user_id))
            except:
                await ctx.channel.send(f'Error while trying to fetch user.')
                proceed = False
            try:
                #verified_role_id = 1073291335097913435
                #wintersgate_role_id = 1073293423232172072
                verified_role = discord.utils.get(guild.roles, id = 1073291335097913435)
                wintersgate_role = discord.utils.get(guild.roles, id = 1073293423232172072)
            except:
                await ctx.channel.send(f'Error while trying to fetch roles.')
                proceed = False

            if proceed:
                botspam_channel = self.bot.get_channel(416384984597790750)

                if wintersgate_role in user.roles:
                    await user.remove_roles(wintersgate_role)
                else:
                    print("User did not have the Winter's Gate role.")
                    await botspam_channel.send(f"{user.display_name} did not have `Winter's Gate` role. <:shrugknight:976571063351787590>")

                if verified_role in user.roles:
                    newly_verified = False
                    print("User already has verified role.")
                    await botspam_channel.send(f"{user.display_name} did already have the `Verified` role. <:thonkin:1017478779293147157>")
                else:
                    newly_verified = True
                    await user.add_roles(verified_role)


                if specification.lower() in ["nomsg", "no msg", "nomessage", "no message", "nom"]:
                    #botspam_channel = self.bot.get_channel(416384984597790750)
                    await botspam_channel.send(f'Verified <@{user_id}> without welcome message.')
                else:
                    if newly_verified:
                        general_channel = self.bot.get_channel(413027360783204363)
                        await general_channel.send(f'Welcome <@{user_id}>! You made it <:wizard:1019019110572625952>\nWhat are your favourite bands? <a:excitedcat:968929424365981817>')
                    else:
                        await ctx.channel.send(f'{user.display_name} was already verified. Uh... welcome anyway? <:charmanderpy:1014855943177113673>')
        else:
            await ctx.send('Error: missing arguments <:gengarpout:752263422141530242>')

    @_verify.error
    async def verify_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f'Sorry, you do not have permissions to do this!')
        elif isinstance(error, commands.CheckFailure):
            await ctx.channel.send(f'Error: This is a melodeathcord specific command.')
        else:
            await ctx.channel.send(f'An error ocurred.')





async def setup(bot: commands.bot) -> None:
    await bot.add_cog(
        ServerModeration(bot),
        guilds = [discord.Object(id = 413011798552477716)])