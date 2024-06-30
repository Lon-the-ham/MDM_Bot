import discord
from discord.ext import commands
from other.utils.utils import Utils as util
import os


class Help(commands.Cog):
    def __init__(self, bot: commands.bot) -> None:
        self.bot = bot
        self.prefix = os.getenv("prefix")



    async def get_cogs_and_commands_dictionary(self, ctx, lower):
        # first fetch all commands and their cogs, and sort the cogs
        commands_list = []
        for x in self.bot.commands:
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
        Use with command name or cog name to get info on that command or cog."""
        async with ctx.typing():
            if len(args) == 0:
                # If there are no arguments, just list the commands:
                commands_dict = await self.get_cogs_and_commands_dictionary(ctx, False)
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
                        commands_dict = await self.get_cogs_and_commands_dictionary(ctx, True)

                        if argument.replace("cog", "").replace(" ","") in commands_dict:
                            title = "Command Cog/Category"
                            description = ""

                            for command in commands_dict[argument.replace("cog", "").replace(" ","")]:
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



async def setup(bot: commands.bot) -> None:
    await bot.add_cog(
        Help(bot),
        guilds = [discord.Object(id = int(os.getenv("guild_id")))])