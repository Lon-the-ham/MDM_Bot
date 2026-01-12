import discord
import sqlite3

from cogs.utils.utl_general import GeneralUtils as utl_g
from cogs.utils.utl_simple  import SimpleUtils  as utl_s

class DiscordUtils():

    #########################################################################################################
    ##                                        generic common def                                           ##
    #########################################################################################################

    def get_role_ids_from_member(member_obj):
        try:
            return [role.id for role in member.roles]
        except Exception as e:
            print(f"Error while trying to fetch roles from member: {e}")
            return []


    #########################################################################################################
    ##                                         generic async def                                           ##
    #########################################################################################################

    async def get_server(bot, guild_id = None):
        if guild_id is None:
            guild_id = bot.main_guild_id
        server = bot.get_guild(guild_id)
        if server is None:
            server = await bot.fetch_guild(guild_id)
        return server


    #########################################################################################################
    ##                                          MESSAGE SENDING                                            ##
    #########################################################################################################

    async def notification_send(bot, server_id: int, title: str, text: str, topic=None) -> None:
        def get_notification_channel_id(guild_id: int, subject: str) -> int:
            conS = sqlite3.connect(f'databases/{guild_id}/serversettings.db')
            curS = conS.cursor()
            if guild_id == 0:
                guild_id = bot.bot_channel_id
            try: 
                return int([item[0] for item in curS.execute("SELECT channel_id FROM special_channels WHERE channel_key = ?", (f"{subject} channel",)).fetchall()][0])
            except:
                return -1

        if server_id is None:
            server_id = 0

        if topic is None:
            topic = "botspam"

        channel_id = get_notification_channel_id(sever_id, topic)

        if channel_id < 0:
            print(f"Error (utl_d.notification_send): {topic} notification channel ID in database is faulty for server with ID {server_id}.")
            additional = f"Error: This message was supposed to be sent to the {topic} channel of server with ID {server_id}."

        channel = bot.get_channel(channel_id)
        await send_embed_message(channel, header, text, additional, None)



    async def send_embed_message(channel, header: str, text: str, footer: str, colour: hex) -> None:
        if len(header) > 256:
            header = header[:253] + "..."
        if len(text) > 4096:
            text = text[:4093] + "..."
        if len(footer) > 1024:
            footer = footer[:1021] + "..."

        embed = discord.Embed(title=header, description=text, color=colour)
        if footer.strip() != "":
            embed.set_footer(text=footer)
        await channel.send(embed=embed)


    #########################################################################################################
    ##                                          COOLDOWN                                                   ##
    #########################################################################################################


    async def cooldown(ctx, bot, service: str) -> int:
        """ == 0 : went through
            >  0 : stopped
        """
        if ctx is not None:
            user_obj  = ctx.message.author
            user_id   = user_obj.id
            guild     = ctx.guild
            user_type = "usr"

            # get mod tier to determine possibly privileged cooldown time
            if guild is not None:
                role_ids = utl_d.get_role_ids_from_member(user_obj)

                if guild.id in bot.modtier_settings:
                    for i in range(4):
                        role_id = bot.modtier_settings[guild.id][i+1]
                        if role_id in role_ids:
                            user_type = "mt" + str(i+1)
                            break

        else:
            # bot internal cooldowns not related to commands
            user_id   = 0
            user_type = "bot"

        # call actual cooldown function
        await utl_d.cooldown_process(service, bot.cooldown_settings, user_id, user_type)



    async def cooldown_process(service: str, cooldown_settings: dict, user_id: int, user_type: str) -> int:
        """ == 0 : went through
            >  0 : stopped
        """
        try:
            service_cooldown_sec  = cooldown_settings[service][user_type] / 10
            cooldown_type         = cooldown_settings[service]["tpe"]
            botwide_timeframe_sec = cooldown_settings[service]["btf"]
            botwide_amount_limit  = cooldown_settings[service]["bal"]
            precision             = cooldown_settings[service]["pre"]

        except:
            print(f"Cooldown Warning: Service '{service}' or user type '{user_type}' not known by cooldown dictionary.")
            user_cooldown_sec     = 1.0
            cooldown_type         = True # True: soft, False: hard
            botwide_timeframe_sec = 10
            botwide_amount_limit  = 5
            precision             = False

        step1_errorcode = utl_d.cooldown_step1_spamprevention(service, cooldown_type, user_id, precision)
        if step1_errorcode > 0:
            return step1_errorcode

        step2_errorcode = utl_d.cooldown_step2_user_cd(service, cooldown_type, service_cooldown_sec, user_id, precision)
        if step2_errorcode > 0:
            return step2_errorcode

        step3_errorcode = utl_d.cooldown_step3_botwide_cd(service, cooldown_type, botwide_timeframe_sec, botwide_amount_limit, precision)
        if step3_errorcode > 0:
            return step3_errorcode

        utl_d.cooldown_insert(service, user_id, precision)
        return 0



    async def cooldown_step1_spamprevention(service: str, cooldown_type: bool, user_id: int, precision: bool) -> int:
        #todo: prevent users from spaming a command too much
        return 0



    async def cooldown_step2_user_cd(service: str, cooldown_type: bool, service_cooldown_sec: float, user_id: int, precision: bool) -> int:
        if precision:
            try:
                conRAM = sqlite3.connect('file::memory:?cache=shared', uri=True)
                curRAM = conRAM.cursor()
                last_invoked = curRAM.execute("SELECT utc_timestamp_ds FROM cooldowns WHERE user_id = ? AND service = ? ORDER BY utc_timestamp_ds DESC", (user_id, service)).fetchone()
                if last_invoked is not None:
                    last_invoked = last_invoked / 10
            except Exception as e:
                print(f"Error while trying to fetch timestamp of {service} command last used in in-memory-database: {e}")
                last_invoked = None
        else:
            try:
                conT = sqlite3.connect('databases/tracking.db')
                curT = conT.cursor()
                last_invoked = curT.execute("SELECT utc_timestamp FROM cooldowns WHERE user_id = ? AND service = ? ORDER BY utc_timestamp DESC", (user_id, service)).fetchone()
            except Exception as e:
                print(f"Error while trying to fetch timestamp of {service} command last used in tracking-database: {e}")
                last_invoked = None

        if last_invoked is None:
            return 0

        waiting_time = (utl_s.utcnow_deciseconds() / 10) - last_invoked

        if waiting_time < service_cooldown_sec:
            if cooldown_type == 0 and waiting_time >= 0:
                await asyncio.sleep(waiting_time)
            elif waiting_time < 0:
                return 11 # error code for negative time
            else:
                return 12 # warning code for user cooldown
        return 0



    async def cooldown_step3_botwide_cd(service: str, cooldown_type: bool, botwide_timeframe_sec: float, botwide_amount_limit: int, precision: bool) -> int:
        def get_threshold() -> float:
            return (utl_s.utcnow_deciseconds() / 10) - botwide_timeframe_sec

        def get_invocation_list() -> list[float]:
            threshold = get_threshold() - 0.1
            if precision:
                try:
                    conRAM = sqlite3.connect('file::memory:?cache=shared', uri=True)
                    curRAM = conRAM.cursor()
                    list_invoked = [item[0] for item in curRAM.execute("SELECT utc_timestamp_ds FROM cooldowns WHERE service = ? AND utc_timestamp_ds > ?", (service, round(threshold,1))).fetchall()]

                except Exception as e:
                    print(f"Error while trying to fetch invoker list of {service} command last used in in-memory-database: {e}")
                    list_invoked = []
            else:
                try:
                    conT = sqlite3.connect('databases/tracking.db')
                    curT = conT.cursor()
                    list_invoked = [item[0] for item in curT.execute("SELECT utc_timestamp FROM cooldowns WHERE service = ? AND utc_timestamp > ?", (service, round(threshold,0))).fetchall()]
                except Exception as e:
                    print(f"Error while trying to fetch invoker list of {service} command last used in tracking-database: {e}")
                    list_invoked = []

            return list_invoked

        #######

        list_invoked = get_invocation_list()

        if len(list_invoked) < botwide_amount_limit or len(list_invoked) == 0:
            return 0
        elif cooldown_type == False:
            return 21 # warning code for botwide cooldown

        counter   = 0
        increment = 0.1 if precision else 1
        while len(list_invoked) >= botwide_amount_limit:
            counter += 1
            if len(list_invoked) == 0:
                return 0
            list_invoked.sort()
            oldest      = list_invoked[0]
            wait_time   = max(oldest - get_threshold(), increment)
            await asyncio.sleep(wait_time)
            if (counter > 70) or (counter > 20 and not precision):
                return 22 # error code for exceeded number of tries
            list_invoked = get_invocation_list()

        return 0



    def cooldown_insert(service: str, user_id: int, precision: bool):
        if precision:
            utcnow = utl_s.utcnow_deciseconds()

            con = sqlite3.connect('file::memory:?cache=shared', uri=True)
            cur = con.cursor()
        else:
            utcnow = utl_s.utcnow()

            con = sqlite3.connect('databases/tracking.db')
            cur = con.cursor()

        cur.execute("INSERT INTO cooldowns VALUES (?,?,?)", (service, user_id, utcnow))
        con.commit()




    def cooldown_garbage_collection():
        #todo: include in time schedule
        leeway = 1

        try:
            conRAM = sqlite3.connect('file::memory:?cache=shared', uri=True)
            curRAM = conRAM.cursor()

            i = 0
            for service in cooldown_settings.keys():
                if cooldown_settings[service]["pre"]:
                    threshold = round((utl_s.utcnow_deciseconds() / 10) - (max(cooldown_settings[service]["btf"], cooldown_settings[service]["usr"]) * (1 + leeway)), 1)

                    curRAM.execute("DELETE FROM cooldowns WHERE service = ? AND utc_timestamp_ds < ?", (service, threshold))
                    i += 1
            
            if i > 0:
                conRAM.commit()
        except Exception as e:
            print("Error during garbage collection for cooldown tracking (hard drive)")

        try:
            conT = sqlite3.connect('databases/tracking.db')
            curT = conT.cursor()

            i = 0
            for service in cooldown_settings.keys():
                if not cooldown_settings[service]["pre"]:
                    threshold = round((utl_s.utcnow_deciseconds() / 10) - (max(cooldown_settings[service]["btf"], cooldown_settings[service]["usr"]) * (1 + leeway)), 0)

                    curT.execute("DELETE FROM cooldowns WHERE service = ? AND utc_timestamp_ds < ?", (service, threshold))
                    i += 1

            if i > 0:
                conT.commit()
        except Exception as e:
            print("Error during garbage collection for cooldown tracking (in memory)")
