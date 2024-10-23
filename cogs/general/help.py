import discord
from discord.ext import commands
from other.utils.utils import Utils as util
import os
import sqlite3

class Help(commands.Cog):
    def __init__(self, bot: commands.bot) -> None:
        self.bot = bot
        self.prefix = os.getenv("prefix")



    async def get_cogs_and_commands_dictionary(self, ctx, lower, only_locks, ignore_locks):
        # first fetch all commands and their cogs, and sort the cogs
        commands_list = []
        for x in self.bot.commands:

            if only_locks:
                if not str(x.help).startswith("🔒"):
                    continue
            elif ignore_locks:
                if str(x.help).startswith("🔒"):
                    continue

            if str(x.help).startswith(("㊙️", "🔜")): # hidden and future commands
                continue

            total_check = True

            for check_function in x.checks:
                try:
                    check = await check_function(ctx)
                except Exception as e:
                    try:
                        check = check_function(ctx)
                    except:
                        total_check = False
            if not check:
                total_check = False

            if total_check:
                if lower:
                    commands_list.append([str(x.name).lower(), str(x.cog_name).lower()])
                else:
                    commands_list.append([str(x.name), str(x.cog_name)])

        # then separate them by cog
        commands_dict = {}
        for command in commands_list:
            command_name = command[0]
            command_cog = command[1]

            if command_cog not in commands_dict:
                commands_dict[command_cog] = []

            commands_dict[command_cog].append(command_name)

        # then sort commands alphabetically
        for cog in commands_dict:
            commands_dict[cog].sort()

        return commands_dict



    def get_subcommands(self, ctx, command):
        """
        with argument: gives list of subcommand objects
        """
        subcommands_list = []

        if command is None:
            return subcommands_list

        try:
            if isinstance(command, commands.Group):
                for subcommand in command.walk_commands():  # iterate through all of the command's parents/subcommands
                    if subcommand.parents[0] == command:  # check if the latest parent of the subcommand is the command itself
                        subcommands_list.append(subcommand)

                return subcommands_list
            else:
                #print("command was not a group")
                return []
        except Exception as e:
            print("Error while trying to fetch subcommands:", e)
            return []



    @commands.command(name='help', aliases = ['halp'])
    @commands.check(util.is_active)
    async def _help(self, ctx, *args):
        """shows command info
        
        Use without arguments to get an overview of all commands.
        Use with command name or cog name to get info on that command or cog.

        Users with extra permissions may use `-help simple` to filter out all mod commands,
        or even use `-help mod` to only show mod-locked commands."""
        async with ctx.typing():

            # filter for commands with descriptions starting with a lock emoji
            if len(args) == 1 and args[0].lower() in ["memberview", "simple", "pleb"]:
                only_locks = False
                ignore_locks = True
            elif len(args) == 1 and args[0].lower() in ["mod", "mods", "moderator", "moderation", "moderators"]: 
                only_locks = True
                ignore_locks = False
            else:
                only_locks = False
                ignore_locks = False

            # distinguish
            if len(args) == 0 or only_locks or ignore_locks:

                # If there are no commandname/cogname arguments, just list the commands:
                commands_dict = await self.get_cogs_and_commands_dictionary(ctx, False, only_locks, ignore_locks)
                title = "Commands"
                description = ""
                help_part = ""

                for cog in {key:commands_dict[key] for key in sorted(commands_dict.keys())}:

                    # under construction 1: exclude commands where help is restricted
                    if cog.lower() == "help":
                        help_part += f"__**{cog}**__\n"
                        help_part += ', '.join(commands_dict[cog])
                        help_part += "\n"
                    else:
                        description += f"__**{cog}**__\n"
                        description += ', '.join(commands_dict[cog])
                        description += "\n"

                description += help_part

            else:
                command_names_list = []
                for x in self.bot.commands:
                    command_names_list.append(str(x.name).lower())
                    for y in x.aliases:
                        command_names_list.append(str(y).lower())

                argument = ' '.join(args).lower()

                if argument in command_names_list:
                    # If the argument is a command, get the help text from that command:
                    # under construction 2: adapt prefix in 
                    title = f""
                    command = self.bot.get_command(argument)

                    description = f"**{str(command.name)}**"
                    if command.aliases:
                        description += f"   [aliases: " + ', '.join(command.aliases) + "]\n\n"
                    else:
                        description += "\n\n"

                    if command.help is None:
                        description += "`Error: dev forgot to add a desciption lmao`"
                    else:
                        description += str(command.help).replace("<prefix>", self.prefix)

                else:
                    # If argument is a subcommand, get the help text from that subcommand:
                    # under construction 2: adapt prefix in 
                    if len(args) > 1 and args[0].lower() in command_names_list and args[1] != "cog":

                        parent_command = self.bot.get_command(args[0].lower())
                        subcommands = self.get_subcommands(ctx, parent_command)
                        for arg in args[1:]:
                            found = False
                            for command in subcommands:
                                if arg.lower() == command.name or arg.lower() in command.aliases:
                                    found = True
                                    break

                            if found:
                                parent_command = command
                                subcommands = self.get_subcommands(ctx, parent_command)
                            else:
                                emoji = util.emoji("think")
                                title = f"Error {emoji}"
                                description = "Don't think I got that subcommand, chief!"
                                break

                        else:
                            title = f""
                            description = f"**{command.name}**"
                            if command.aliases:
                                description += f"   [aliases: " + ', '.join(command.aliases) + "]\n"
                            else:
                                description += "\n"
                            description += f"subcommand of " + ' '.join(args[:-1]) + "\n\n"
                            description += command.help.replace("<prefix>", self.prefix)

                    else:
                        # if the argument is a cog, get the cog commands
                        commands_dict = await self.get_cogs_and_commands_dictionary(ctx, True, only_locks, ignore_locks)
                        filtered_dict = {}

                        for key, value in commands_dict.items():
                            new_key = util.alphanum(key, "lower")
                            filtered_dict[new_key] = value

                        filtered_argument = util.alphanum(argument.replace("cog", ""), "lower")

                        if filtered_argument in filtered_dict:
                            title = "Command Cog/Category"
                            description = ""

                            for command in filtered_dict[filtered_argument]:
                                description += f"{self.prefix}{command} : "
                                description += self.bot.get_command(command).help.split("\n")[0].replace("<prefix>", self.prefix)
                                description += "\n"

                        else:
                            # If someone is just trolling:
                            emoji = util.emoji("think")
                            title = f"Error {emoji}"
                            description = "Don't think I got that command, chief!"

            help_embed = discord.Embed(title=title, description=description)
            await ctx.send(embed=help_embed)

    @_help.error
    async def help_error(self, ctx, error):
        await util.error_handling(ctx, error)




    #########################################################################################################################################



    @commands.command(name='test')
    @commands.check(util.is_active)
    async def _test(self, ctx, *args):
        """check availability

        The bot will reply with a message if online and active.
        """    
        await ctx.send(f'`I am online!`')
        
    @_test.error
    async def test_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='version', aliases = ["v"])
    @commands.check(util.is_active)
    async def _botversion(self, ctx):
        """shows version of the bot
        """    
        version = util.get_version()
        await ctx.send(f"MDM Bot {version}")
    @_botversion.error
    async def botversion_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @commands.command(name='info', aliases = ["serverinfo"])
    @commands.check(util.is_active)
    async def _serverinfo(self, ctx):
        """shows server information
        """
        # GET SERVER ID and NAME
        guild_id = ctx.guild.id
        mainserver_id = util.get_main_server_id()

        server_name = ctx.guild.name

        # GET SERVER CREATION DATE

        server_birthdate = ctx.guild.created_at.strftime("%Y/%m/%d - %H:%M:%S")

        # GET MEMBERS

        member_count = len(ctx.guild.members)

        # GET USER BREAKDOWN

        breakdown_found = False

        if guild_id == mainserver_id:
            inactivity_filter_enabled = False
            try:
                con = sqlite3.connect(f'databases/botsettings.db')
                cur = con.cursor()
                if "on" == [item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("inactivity filter",)).fetchall()][0].strip().lower():
                    inactivity_filter_enabled = True
            except Exception as e:
                print("Error:", e)

            if inactivity_filter_enabled:
                try:
                    inactivity_role_id = int([item[0] for item in cur.execute("SELECT role_id FROM specialroles WHERE name = ?", ("inactivity role",)).fetchall()][0])
                    inactivity_role = discord.utils.get(ctx.guild.roles, id = inactivity_role_id)
                    bot_count = 0
                    active_count = 0
                    inactive_count = 0
                    for member in ctx.guild.members:
                        if member.bot:
                            bot_count += 1
                        else:
                            if len(member.roles) < 3 and inactivity_role in member.roles:
                                inactive_count += 1
                            else:
                                active_count += 1

                    user_breakdown = f"active: {active_count}, inactive: {inactive_count}, bots: {bot_count}"
                    breakdown_found = True
                except Exception as e:
                    print("Error:", e)

        if (breakdown_found == False):
            bot_count = 0
            human_count = 0
            for member in ctx.guild.members:
                if member.bot:
                    bot_count += 1
                else:
                    human_count += 1

            user_breakdown = f"actual users: {human_count}, bots: {bot_count}"

        # GET OWNER

        try:
            if ctx.guild.owner.display_name.lower() != ctx.guild.owner.name.lower():
                owner = f"{ctx.guild.owner.display_name} ({ctx.guild.owner.name})"
            else:
                owner = ctx.guild.owner.name
        except:
            owner = "*unknown*"

        description = f"**Users:**\n{member_count}\n({user_breakdown})\n\n"
        description += f"**Owner:**\n{owner}\n\n"
        description += f"**Server ID:**\n{guild_id}\n\n"
        description += f"**created:** {server_birthdate} UTC"
        embed = discord.Embed(title=f"Server info for {server_name}", description=description, color=0x000000)
        try:
            embed.set_thumbnail(url=ctx.guild.icon.url)
        except Exception as e:
            print("Error:", e)

        await ctx.send(embed=embed)

    @_serverinfo.error
    async def serverinfo_error(self, ctx, error):
        await util.error_handling(ctx, error)



async def setup(bot: commands.bot) -> None:
    await bot.add_cog(
        Help(bot),
        guilds = [discord.Object(id = int(os.getenv("guild_id")))])