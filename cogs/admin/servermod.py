import discord
from discord.ext import commands

class ServerModeration(commands.Cog):
    def __init__(self, bot: commands.bot) -> None:
        self.bot = bot
        

    @commands.command(name='ban', aliases = ['userban'])
    @commands.has_permissions(manage_guild=True)
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

            immunity_list = ["586358910148018189", "958105284759400559"]

            if user_id in immunity_list:
                await ctx.send('I- I really do not want to ban this user. <:hampleading:1017443036843753553>')
            else:
                try:
                    user = await self.bot.fetch_user(user_id)
                    await ctx.guild.ban(user, reason=reason, delete_message_days=0)
                except:
                    await ctx.send('Error in user argument')
        else:
            await ctx.send('Error: missing arguments')


    @commands.command(name='kick', aliases = ['userkick'])
    @commands.has_permissions(manage_guild=True)
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

            immunity_list = ["586358910148018189", "958105284759400559"]

            if user_id in immunity_list:
                await ctx.send('I- I really do not want to kick this user. <:hampleading:1017443036843753553>')
            else:
                try:
                    user = await self.bot.fetch_user(user_id)
                    await ctx.guild.kick(user, reason=reason)
                except:
                    await ctx.send('Error in user argument')
        else:
            await ctx.send('Error: missing arguments')


    @commands.command(name='unban', aliases = ['userunban'])
    @commands.has_permissions(manage_guild=True)
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
            except:
                await ctx.send('Error in user argument')
        else:
            await ctx.send('Error: missing arguments')


    @commands.command(name='mute', aliases = ['usermute','silence'])
    @commands.has_permissions(manage_guild=True)
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


    @commands.command(name='unmute', aliases = ['unusermute','unsilence'])
    @commands.has_permissions(manage_guild=True)
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
                await ctx.send(f'User {user.display_name} unmuted')
            except:
                await ctx.send('Error in user argument')
        else:
            await ctx.send('Error: missing arguments')



    @commands.command(name='batchban', aliases = ['userbatchban'])
    @commands.has_permissions(manage_guild=True)
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






async def setup(bot: commands.bot) -> None:
    await bot.add_cog(
        ServerModeration(bot),
        guilds = [discord.Object(id = 413011798552477716)])