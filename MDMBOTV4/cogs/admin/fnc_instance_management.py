import asyncio
import discord
import sqlite3

from cogs.utils.utl_discord import DiscordUtils        as utl_d
from cogs.utils.utl_general import GeneralUtils        as utl_g
from cogs.utils.utl_simple  import SimpleUtils         as utl_s

from cogs.admin.utl_admin   import AdministrationUtils as utl_a




class AdministrationFunctions():

    async def botrole_assignment(self, ctx, assign=True) -> bool:
        pass




    
    async def botstatus(self, ctx) -> None:
        version = utl_a.get_version()
        app_num = utl_a.get_instance_number(ctx.bot.application_id)

        if app_num is None:
            await ctx.send("Error:")
        else:
            if ctx.bot.is_active():
                emoji    = utl_g.emoji("awoken")
                activity = "active"
            else:
                emoji    = utl_g.emoji("sleep")
                activity = "inactive"
            await ctx.send(f"This instance ({app_num}) is set `{activity}` {emoji}.\nMDM Bot {version}")



    async def load_backups(self, ctx) -> None:
        pass
        


    async def make_backups(self, ctx, this_instance_was_active: bool) -> None:
        pass



    async def switch_instance(self, ctx) -> None:
        """switches the active instance"""

        if len(args) == 0:
            ctx.send(f"No argument provided. Command needs either integer argument (application index) or `off` argument.")
            return

        arg = args[0]
        if arg.lower() == "off":
            await self.switch_instance_off(ctx)
            return

        if not utl_s.represents_integer(arg):
            ctx.send(f"Argument invalid. Command needs either integer argument (application index) or `off` argument.")
            return

        # search for application of given index
        app_index           = utl_s.force_integer(arg)
        index_found, app_id = utl_a.find_application_by_index(app_index)

        if not index_found:
            await ctx.send(f"Application with index {app_index} not found.")
            return

        confirmed = await utl_d.confirmation_check(ctx, "Are you sure you want to switch instances? Respond with `yes` to confirm.")

        if not confirmed:
            return  

        # start actual switching
        reference_message   = await ctx.send(f"...starting switch") # store time to check back in order to decide when cloud backup can be loaded
        reference_time      = reference_message.created_at             

        # memorise whether to sync or not
        syncing = True
        if len(args) > 1 and ''.join(args[1:]).lower() in ["nosync", "nosynchronisation", "nonsync", "nosynch", "nosynchro", "nosynchronization"]:
            syncing = False

        async with ctx.typing():
            # save activity status for later

            con0 = sqlite3.connect(f'databases/0host.db')
            cur0 = con0.cursor()
            activity_list = [item[0].lower().strip() for item in curA.execute("SELECT value FROM meta WHERE name = ?", ("active",)).fetchall()]
            this_instance_was_active = (activity_list[0] == "yes") and ctx.bot.is_active()

            # first set to inactive, so no other commands are executed
            curA.execute("UPDATE activity SET value = ? WHERE name = ?", ("no", "active"))
            conA.commit()

            # then synchronise LOCAL databases
            await ctx.send("...creating backups")
            await asyncio.sleep(1)
            await self.make_backups(ctx, this_instance_was_active)

            if this_instance_was_active:
                await ctx.send("...awaiting")
                if syncing:
                    await asyncio.sleep(2)
            else:
                if syncing == False:
                    await ctx.send("...skipping synchronisation")
                else:
                    await ctx.send("...start synchronisation process")
                    await self.synchronise_databases(ctx)

            # then sync CLOUD databases
            if syncing:
                try:
                    called_from = "switch"
                    await ctx.send("Cloud Sync Download is disabled")
                    await self.synchronise_cloud(ctx, reference_time, called_from)
                except Exception as e:
                    await ctx.send(f"Error while trying to sync with cloud data: {e}")

            # then set the correct app to active
            if app_id == self.application_id:
                cur0.execute("UPDATE meta SET value = ? WHERE name = ?", ("yes", "active"))
                con0.commit()
                ctx.bot.activity_status = 1

                emoji = util.emoji("awoken")
                try:
                    await self.botrole_assignment(ctx, True)
                except Exception as e:
                    print("Error while trying to assign bot role:", e)
            else:
                # keep inactive
                emoji = util.emoji("sleep")
                try:
                    await self.botrole_assignment(ctx, False)
                except Exception as e:
                    print("Error while trying to unassign bot role:", e)

            await ctx.send(f"done {emoji}")




    async def switch_instance_off(self, ctx) -> None:

        confirmed = await utl_d.confirmation_check(ctx, "Are you sure you want to deactivate all bot instances? Respond with `yes` to confirm.")

        if not confirmed:
            return  

        async with ctx.typing():

            con0 = sqlite3.connect(f'databases/0host.db')
            cur0 = con0.cursor()
            activity_list            = [item[0].lower().strip() for item in cur0.execute("SELECT value FROM meta WHERE name = ?", ("active",)).fetchall()]
            this_instance_was_active = (activity_list[0] == "yes") and ctx.bot.is_active()

            cur0.execute("UPDATE meta SET value = ? WHERE name = ?", ("no", "active"))
            con0.commit()

            if this_instance_was_active:
                await asyncio.sleep(1)
                await self.make_backups(ctx, this_instance_was_active)

            try:
                await self.botrole_assignment(ctx, False)
            except Exception as e:
                print("Error while trying to unassign bot role:", e)
            await ctx.send(f"Shut down.")



    async def synchronise_cloud(self, ctx, reference_time, called_from) -> None:
        pass #TODO



    async def synchronise_databases(self, ctx) -> None:
        pass