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



    @commands.command(name='help', aliases = ['halp'])
    @commands.check(util.is_active)
    async def _help(self, ctx, args=None):
        """shows command info
        
        Use without arguments to get an overview of all commands.
        Use with command name our cog name to get info on that command or cog."""
        async with ctx.typing():
            if not args:
                # If there are no arguments, just list the commands:
                commands_dict = await self.get_cogs_and_commands_dictionary(ctx, False)
                title = "Commands"
                description = ""
                help_part = ""

                for cog in {key:commands_dict[key] for key in sorted(commands_dict.keys())}:
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

                argument = str('_'.join(args)).lower()

                if argument in command_names_list:
                    # If the argument is a command, get the help text from that command:
                    title = f""
                    command = self.bot.get_command(argument)

                    description = f"**{command.name}**"
                    if command.aliases:
                        description += f"   [aliases: " + ', '.join(command.aliases) + "]\n\n"
                    else:
                        description += "\n\n"
                    description += command.help

                else:
                    # if the argument is a cog, get the cog commands
                    commands_dict = await self.get_cogs_and_commands_dictionary(ctx, True)

                    if argument.replace("cog", "").replace("_","") in commands_dict:
                        title = "Command Cog/Category"
                        description = ""

                        for command in commands_dict[argument.replace("cog", "").replace("_","")]:
                            description += f"{self.prefix}{command} : "
                            description += self.bot.get_command(command).help.split("\n")[0]
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