# MAIN PYTHON FILE

import asyncio
import discord
import os
import traceback

from discord.ext import commands

from cogs.utils.prc_bootload    import Environment          as env
from cogs.utils.prc_bootload    import BootLoadFunctions    as blf
from cogs.utils.prc_update      import BotUpdate            as upd
from cogs.utils.utl_discord     import DiscordUtils         as utl_d
from cogs.utils.utl_general     import GeneralUtils         as utl_g
from cogs.utils.utl_simple      import SimpleUtils          as utl_s
from cogs.utils.utl_trans       import TransformationUtils  as utl_t

environment = env()



class MDMBot(commands.Bot):

    def __init__(self):
        super().__init__(
            case_insensitive = True,
            command_prefix   = environment.prefix,
            help_command     = None,
            intents          = discord.Intents.all()
            )

        self.activity_status            = -1
        self.version                    = "??"
        self.bot_channel_id             = environment.bot_channel_id
        self.host_id                    = environment.host_user_id
        self.main_guild_id              = environment.main_guild_id
        self.main_extension_dict        = environment.main_extension_dict
        self.optional_extension_dict    = environment.optional_extension_dict
        self.prfx                       = environment.prefix
        self.reboot_time_string         = environment.reboot_time_string
        self.webinfo_import             = environment.webinfo_import
        self.bot_master_ids             = []
        self.cooldown_settings          = {}
        self.modtier_settings           = {}



    #########################################################################################################
    ##                                         direct checks                                               ##
    #########################################################################################################


    def is_active(self):
        return (self.activity_status > 0)


    def import_rym_enabled(self):
        return self.webinfo_import["rym"]


    def import_metallum_enabled(self):
        return self.webinfo_import["ma"]


    def import_scrobbles_enabled(self):
        return self.webinfo_import["lfm"]




    #########################################################################################################
    ##                                           bot setup                                                 ##
    #########################################################################################################



    async def setup_hook(self):

        # loading cogs
        for ext in self.main_extension_dict.keys():
            if (self.main_extension_dict.get(ext) is None) or (str(self.main_extension_dict.get(ext)).lower().strip() != "false"):
                await self.load_extension(ext)
            else:
                print(f"> cog {ext} disabled")

        # loading optional cogs
        for ext in self.optional_extension_dict.keys():
            if (self.optional_extension_dict.get(ext) is None) or (str(self.optional_extension_dict.get(ext)).lower().strip() != "false"):
                try:
                    await self.load_extension(ext)
                    print(f"> optional cog {ext} enabled")
                except Exception as e:
                    try:
                        if f"Extension '{ext}' raised an error:" in str(traceback.format_exc()):
                            reason = str(traceback.format_exc()).split(f"Extension '{ext}' raised an error:")[-1].strip()
                        else:
                            reason = str(traceback.format_exc()).strip().split("\n")[-1].strip()
                        if reason.endswith(f"discord.ext.commands.errors.ExtensionNotFound: Extension '{ext}' could not be loaded."):
                            pass #default
                        else:
                            print(f"> {reason}")
                    except:
                        pass

        # putting together
        await bot.tree.sync(guild = discord.Object(id = self.main_guild_id))



    async def on_ready(self):
        print('> logged in as {0.user}'.format(bot))
        try:
            # setup/load meta information
            blf.create_necessary_databases(bot)
            upd.update_bot()
            self.activity_status, load_settings = blf.load_activeness()
            self.version                        = blf.getsave_version_from_file()

            await blf.set_discord_status(bot, load_settings)
            blf.set_reboot_time(self.reboot_time_string)
            blf.clear_db_residue()
            await blf.instance_wide_activity_check(bot)
            blf.setup_cooldown_settings(bot)
            blf.setup_cooldown_in_memory_db()
            blf.setup_webinfo_import(bot)
            blf.setup_bot_masters(bot)

            # announce presence
            channel = bot.get_channel(self.bot_channel_id)
            emoji   = utl_g.emoji("login")
            await channel.send(f'`I have logged in` {emoji}')
                        
        except Exception as e:
            print(f"> error in executing on_ready: {e}")
            print(traceback.format_exc())
            if self.activity_status == -1:
                print("Error: failed loading, please restart")


###################################

bot = MDMBot()
bot.run(environment.discord_token)

###################################