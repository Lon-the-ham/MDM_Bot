import discord
from discord.ext import commands

class Settings(commands.Cog):
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


    @commands.command(name='set', aliases = ['setting', 'settings'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(is_valid_server)
    async def _settings(self, ctx: commands.Context, *args):
        """*change settings

        first argument has to specify the setting parameter, 
        i.e. status
        use e.g.: -set status w jamal doing ...things
        
        """
        if len(args) > 0:
            parameter = args[0].lower()
            if len(args) > 1:
                value = ' '.join(args[1:])

                settings = []
                try:
                    with open('cogs/settings/default_settings.txt', 'r') as s:
                        for line in s:
                            settings.append(line)
                except:
                    await ctx.send(f'Could not open settings file <:jakeslam:1014849819409383455>')

                parvals = []
                settings_strp = [line.strip() for line in settings if line.strip()]
                for s in settings_strp:
                    if ":" in s:
                        p = s.split(":",1)[0].lower()
                        v = s.split(":",1)[1]
                        parvals.append([p, v])
                    else:
                        print(f"Error with settings in: {s}")

                setting_found = False
                for pv in parvals:
                    p = pv[0]
                    if p == parameter:
                        setting_found = True
                        v = pv[1]
                        oldline = p + ":" + v
                        newline = parameter + ": " + value
                        filedata = '\n'.join(settings_strp)

                        try:
                            newdata = filedata.replace(oldline, newline)
                        except:
                            newdata = filedata
                            await ctx.send(f'Error during SEEK <:jakeslam:1014849819409383455>')

                        try:
                            f = open('cogs/settings/default_settings.txt', 'w')
                            f.write(newdata)
                            f.close()
                            await ctx.send(f'Set {parameter} to {value}')
                        except Exception as e:
                            print(e)
                            await ctx.send(f'Error occurred while rewriting file <:jakeslam:1014849819409383455>')
                if not setting_found:
                    await ctx.send(f'Did not find a setting parameter called {parameter} <:tigerpensive:1017483390326415410>')
            else:
                await ctx.send(f'This command needs also a value argument <:hmmm:975581998410252318>')
        else: 
            await ctx.send(f'This command needs a parameter argument followed by the value I am supposed to set it to. <:penguinconfuse:1017439518116298765>')
    @_settings.error
    async def settings_error(ctx, error, *args):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f'Sorry, you do not have permissions to do this!')
        elif isinstance(error, commands.BadArgument):
            await ctx.send('Something went wrong... something something bad argument <:seenoslowpoke:975062347871842324>')
        else:
            await ctx.send(f'Some error occurred <:penguinshy:1017439941074100344>')


    @commands.command(name='showsettings', aliases = ['displaysettings'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(is_valid_server)
    async def _showsettings(self, ctx: commands.Context, *args):
        """*display settings

        no arguments
        """
        settings = []
        try:
            with open('cogs/settings/default_settings.txt', 'r') as s:
                for line in s:
                    settings.append(line.strip())
            loading_complete = True
        except:
            await ctx.send(f'Could not open settings file <:jakeslam:1014849819409383455>')
            loading_complete = False

        if loading_complete:
            msg = ""
            settings_strp = [line.strip() for line in settings if line.strip()]
            for s in settings_strp:
                if ":" in s:
                    parameter = s.split(":",1)[0].lower()
                    value = s.split(":",1)[1]
                    msg += f"**{parameter}:** {value}\n"

            embed=discord.Embed(title=f"Settings of MDM Bot", description=msg, color=0x880808)
            try:
                embed.set_footer(text=f"The status here is the default status, that will be loaded upon reboot. To change the current status use -status command.")
            except:
                print("adding footer to embed failed")
            await ctx.send(embed=embed)
    @_settings.error
    async def settings_error(ctx, error, *args):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f'Sorry, you do not have permissions to do this!')
        elif isinstance(error, commands.BadArgument):
            await ctx.send('Something went wrong... something something bad argument <:seenoslowpoke:975062347871842324>')
        else:
            await ctx.send(f'Some error occurred <:penguinshy:1017439941074100344>')


async def setup(bot: commands.bot) -> None:
    await bot.add_cog(
        Settings(bot),
        guilds = [discord.Object(id = 413011798552477716)])