# COG FOR ALL THINGS MANAGING SETTINGS


# MEMO to devs:
# every new setting needs to be not only added as
#     > a @_set.command() subcommand
# (for on/off commands it just needs to be added to the async function for all on/off commands)
# but also
#     > added to showsettings command (and appended to at least one of the "desctext_..." lists)
#     > listed in the dictionary of the set (group) command 
# if it's an on/off switch 
#     > also added to database_on_off_switch(...) function
# and added to
#     > update command
#     > setup command





import discord
from discord.ext import commands
import datetime
from tzlocal import get_localzone
import pytz
from other.utils.utils import Utils as util
import os
import sqlite3
from emoji import UNICODE_EMOJI


class Administration_of_Settings(commands.Cog):
    def __init__(self, bot: commands.bot) -> None:
        self.bot = bot
        self.application_id = os.getenv("application_id")
        self.prefix = os.getenv("prefix")




    @commands.command(name='showsettings', aliases = ['settings'])
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _showsettings(self, ctx: commands.Context, *args):
        """🔒 Shows bot settings
        
        Optionally, you can give the following arguments:
          emoji: shows the emoji the bot uses
          keys: shows whether certain keys are provided
          roles: shows reaction roles and special roles
          
        Or these although they are covered by the default command:
          channels: shows special channels
          features: shows enabled/disabled functionality
          mods: shows moderators 
          notifications: shows enabled/disabled notifications

        """ 
        if len(args) == 0:
            argument = "general"
        else:
            argument = args[0].lower()

        #################################################### BOTSETTINGS

        con = sqlite3.connect(f'databases/botsettings.db')
        cur = con.cursor()

        desctext_general = []
        desctext_roles = []
        desctext_emoji = []

        desctext_mods = []
        desctext_channels = []
        desctext_features = []
        desctext_keys = []
        desctext_notifications = []


        # MAIN SERVER
        main_server_list = [[item[0],item[1]] for item in cur.execute("SELECT value, details FROM botsettings WHERE name = ?", ("main server id",)).fetchall()]
        if len(main_server_list) == 0:
            main_server_id = "error⚠️"
            main_server_name = "error⚠️"
            print("Error: no main server in database")
        else:
            if len(main_server_list) > 1:
                print("Warning: there are multiple main server entries in the database")
            main_server_id = main_server_list[0][0]
            main_server_name = main_server_list[0][1]

        # APPS
        desctext_general.append(f"\n**Instances:**")
        app_list = [[item[0],item[1],item[2]] for item in cur.execute("SELECT value, type, details FROM botsettings WHERE name = ?", ("app id",)).fetchall()]
        if len(main_server_list) == 0:
            app_instances = "error⚠️"
            print("Error: no app in database")
            desctext_general.append(app_instances)
        else:
            #app_text_list = []
            app_list.sort(key=lambda x: x[2])
            for item in app_list:
                app_id = item[0]
                timezone = item[1]
                instance_nr = util.cleantext(item[2])
                #app_text_list.append(f"`Instance {instance_nr}`: <@{app_id}> [TZ: {timezone}]")
                desctext_general.append(f"`Instance {instance_nr}`: <@{app_id}> [TZ: {timezone}]")
            #app_instances = '\n'.join(app_text_list)


        # BOT STATUS
        desctext_general.append(f"\n**Bot activity status:**")
        bot_status_list = [[item[0],item[1]] for item in cur.execute("SELECT value, type FROM botsettings WHERE name = ?", ("status",)).fetchall()]
        if len(bot_status_list) == 0:
            bot_status = "error⚠️"
            print("Error: no bot status in database")
        else:
            if len(bot_status_list) > 1:
                print("Warning: there are multiple bot status entries in the database")
            status_value = bot_status_list[0][0]
            short_type = bot_status_list[0][1]

            if short_type == "w":
                bot_status = f"watching {status_value}"
            elif short_type == "p":
                bot_status = f"playing {status_value}"
            elif short_type == "l":
                bot_status = f"listening to {status_value}"
            elif short_type == "s":
                bot_status = f"streaming {status_value}"
            elif short_type == "n":
                bot_status = f" "
            else:
                bot_status = f"error⚠️"
                print("Error: bot status type not valid")
        desctext_general.append(f"`{bot_status}`")

        #################################################### MODERATORS

        desctext_general.append(f"\n**Moderators:**")
        moderator_serverfetched_list = []
        moderator_ID_serverfetched_list = []
        moderation_bot_list = []
        for member in ctx.guild.members:
            member_perms = [p for p in member.guild_permissions]
            for p in member_perms:
                if p[1] and p[0] == "manage_guild":
                    if not member.bot:
                        moderator_serverfetched_list.append(member)
                        moderator_ID_serverfetched_list.append(str(member.id))
                    else:
                        moderation_bot_list.append(member)
        moderator_id_list = []
        mod_list = [[item[0],item[1]] for item in cur.execute("SELECT userid, details FROM moderators").fetchall()]
        if len(mod_list) == 0:
            moderator_text = "error⚠️"
            print("Error: no moderators in database")
        else:
            for item in mod_list:
                moderatorid = item[0]
                modtype = item[1]
                if modtype.lower() == "mod":
                    modtype_icon = ""
                elif modtype.lower() == "dev":
                    modtype_icon = util.emoji("computer")
                elif modtype.lower() == "owner":
                    modtype_icon = util.emoji("crown")
                elif modtype.lower().startswith("custom"):
                    modtype_icon = util.emoji(modtype.lower())
                    modtype = "mod"
                else:
                    print(f"Warning: modtype of mod with id {moderatorid} is not correct.")
                    modtype_icon = ""

                if modtype.lower() in ["dev", "owner"]:
                    moderator_id_list.append(moderatorid)
                    desctext_general.append(f"<@{moderatorid}> {modtype_icon}")
                    desctext_mods.append(f"<@{moderatorid}> {modtype_icon}")
                else:
                    if moderatorid in moderator_ID_serverfetched_list:
                        moderator_id_list.append(moderatorid)
                        desctext_general.append(f"<@{moderatorid}> {modtype_icon}")
                        desctext_mods.append(f"<@{moderatorid}> {modtype_icon}")
                    else:
                        #remove from list
                        cur.execute("DELETE FROM moderators WHERE userid = ?", (moderatorid,))
                        con.commit()
                        await util.changetimeupdate()

        for mod in moderator_serverfetched_list:
            if str(mod.id) in moderator_id_list:
                pass
            else:
                desctext_general.append(f"<@{str(mod.id)}>")
                desctext_mods.append(f"<@{str(mod.id)}>")
                # add to list
                cur.execute("INSERT INTO moderators VALUES (?, ?, ?)", (str(mod.name), str(mod.id), "mod"))
                con.commit()
                await util.changetimeupdate()

        if len(moderation_bot_list) > 0:
            desctext_mods.append(f"\n**Moderatoration Bots:**")
            emoji = util.emoji("bot")
            for bot in [m for m in sorted(moderation_bot_list, key=lambda m: m.display_name)]:
                desctext_mods.append(f"<@{str(bot.id)}> {emoji}")



        #################################################### CHANNELS (INITIALISATION ONLY, adding to output later)

        botspamchannel_list = [item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("botspam channel id",)).fetchall()]
        if len(botspamchannel_list) == 0:
            botspamchannel_id = "error⚠️"
            print("Error: no botspam channel in database")
        else:
            if len(botspamchannel_list) > 1:
                print("Warning: there are multiple bot spam channel entries in the database")
            botspamchannel_id = botspamchannel_list[0]

        generalchannel_list = [item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("general channel id",)).fetchall()]
        if len(generalchannel_list) == 0:
            generalchannel_id = "error⚠️"
            print("Error: no botspam channel in database")
        else:
            if len(generalchannel_list) > 1:
                print("Warning: there are multiple general channel entries in the database")
            generalchannel_id = generalchannel_list[0]

        rolechannel_list = [item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("role channel id",)).fetchall()]
        if len(rolechannel_list) == 0:
            rolechannel_id = "error⚠️"
            print("Error: no role channel in database")
        else:
            if len(rolechannel_list) > 1:
                print("Warning: there are multiple role channel entries in the database")
            rolechannel_id = rolechannel_list[0]

        accesswallchannel_list = [item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("access wall channel id",)).fetchall()]
        if len(accesswallchannel_list) == 0:
            accesswallchannel_id = "error⚠️"
            print("Error: no accesswall channel in database")
        else:
            if len(accesswallchannel_list) > 1:
                print("Warning: there are multiple access wall channel entries in the database")
            accesswallchannel_id = accesswallchannel_list[0]

        ruleschannel_list = [item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("rules channel id",)).fetchall()] # turing test channel
        if len(ruleschannel_list) == 0:
            ruleschannel_id = "error⚠️"
            print("Error: no turing test/rules channel in database")
        else:
            if len(ruleschannel_list) > 1:
                print("Warning: there are multiple turing test/rules channel entries in the database")
            ruleschannel_id = ruleschannel_list[0]



        #################################################### ON/OFF SETTINGS



        desctext_general.append(f"\n**Settings:**")
        accesswall_list = [item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("access wall",)).fetchall()]
        if len(accesswall_list) == 0:
            accesswall = "error⚠️"
            print("Error: no accesswall on/off in database")
        else:
            if len(accesswall_list) > 1:
                print("Warning: there are multiple accesswall on/off entries in the database")
            accesswall = accesswall_list[0]

        accesswalltext_list = [item[0] for item in cur.execute("SELECT etc FROM serversettings WHERE name = ?", ("access wall",)).fetchall()]
        if len(accesswalltext_list) == 0:
            accesswalltext = "default"
        else:
            accesswalltext = accesswalltext_list[0].strip()
            if accesswalltext == "":
                accesswalltext = "default"
            else:
                accesswalltext = "custom"

        desctext_general.append(f"Access wall system: `{accesswall}` ({accesswalltext})")
        desctext_features.append(f"Access wall system: `{accesswall}` ({accesswalltext})")

        ##### turing test

        turingtest_list = [item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("turing test",)).fetchall()]
        if len(turingtest_list) == 0:
            turingtest = "error⚠️"
            print("Error: no turingtest on/off in database")
        else:
            if len(turingtest_list) > 1:
                print("Warning: there are multiple turingtest on/off entries in the database")
            turingtest = turingtest_list[0]


        if accesswall == "on":

            desctext_general.append(f"Access wall turing test: `{turingtest}`")
            desctext_features.append(f"Access wall turing test: `{turingtest}`")
            
            rulesmessageid_list = [item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("rules channel id",)).fetchall()]
            if len(rulesmessageid_list) == 0:
                if turingtest == "off":
                    rulesmessage_id = "not provided"
                else:
                    rulesmessage_id = "error⚠️"
                    print("Error: no rules message id in database")
            else:
                if len(rulesmessageid_list) > 1:
                    print("Warning: there are multiple rules message id entries in the database")
                rulesmessage_id = rulesmessageid_list[0]
                rulesmessage = f"https://discord.com/channels/{main_server_id}/{ruleschannel_id}/{rulesmessage_id}"

            rulesfirstreaction_list = [item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("rules first reaction",)).fetchall()]
            if len(rulesfirstreaction_list) == 0:
                if turingtest == "off":
                    rulesfirstreaction = "not provided"
                else:
                    rulesfirstreaction = "error⚠️"
                    print("Error: no rules message id in database")
            else:
                if len(rulesfirstreaction_list) > 1:
                    print("Warning: there are multiple rules message id entries in the database")
                rulesfirstreaction = rulesfirstreaction_list[0]

            desctext_general.append(f" ⮡  turing test task: {rulesmessage} ↔ {rulesfirstreaction}")
            desctext_features.append(f" ⮡  turing test task: {rulesmessage} ↔ {rulesfirstreaction}")

            turingbanmessage_list = [[item[0],item[1]] for item in cur.execute("SELECT value, details FROM serversettings WHERE name = ?", ("turing ban message",)).fetchall()]
            if len(turingbanmessage_list) == 0:
                if turingtest == "off":
                    turingbanmessage_switch = "not provided"
                    turingbanmessage_text = "not provided"
                else:
                    turingbanmessage_switch = "error⚠️"
                    turingbanmessage_text = "error⚠️"
                    print("Error: no turing ban message entry in database")
                tbm_type = "none"
            else:
                if len(turingbanmessage_list) > 1:
                    print("Warning: there are multiple turing ban message entries in the database")
                turingbanmessage_switch = turingbanmessage_list[0][0]
                turingbanmessage_text = turingbanmessage_list[0][1]
                if turingbanmessage_text.strip() in [""]:
                    tbm_type = "default text"
                else:
                    tbm_type = "custom text"

            desctext_general.append(f" ⮡  turing ban message: `{turingbanmessage_switch}` ({tbm_type})")
            desctext_features.append(f" ⮡  turing ban message: `{turingbanmessage_switch}` ({tbm_type})")


        elif accesswall == "off":
            automaticrole_list = [item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("automatic role",)).fetchall()]
            if len(automaticrole_list) == 0:
                automaticrole = "error⚠️"
                print("Error: no automatic role setting in database")
            else:
                if len(automaticrole_list) > 1:
                    print("Warning: there are multiple automatic role entries in the database")
                automaticrole = automaticrole_list[0]

            desctext_general.append(f"Auto-Role on join: `{automaticrole}`")
            desctext_features.append(f"Auto-Role on join: `{automaticrole}`")

        #####

        botdisplay_list = [item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("bot display",)).fetchall()]
        if len(botdisplay_list) == 0:
            botdisplay = "error⚠️"
            print("Error: no botdisplay on/off in database")
        else:
            if len(botdisplay_list) > 1:
                print("Warning: there are multiple botdisplay on/off entries in the database")
            botdisplay = botdisplay_list[0]
        desctext_general.append(f"Bot sidebar display switch: `{botdisplay}`")
        desctext_features.append(f"Bot sidebar display switch: `{botdisplay}`")

        memobacklog_func_list = [item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("backlog functionality",)).fetchall()]
        if len(memobacklog_func_list) == 0:
            memobacklog_func = "error⚠️"
            print("Error: no memo/backlog on/off in database")
        else:
            if len(memobacklog_func_list) > 1:
                print("Warning: there are multiple memo/backlog on/off entries in the database")
            memobacklog_func = memobacklog_func_list[0]
        desctext_general.append(f"Memo/Backlog functionality: `{memobacklog_func}`")
        desctext_features.append(f"Memo/Backlog functionality: `{memobacklog_func}`")

        custom_reminders_list = [item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("reminder functionality",)).fetchall()]
        if len(custom_reminders_list) == 0:
            customreminder_func = "error⚠️"
            print("Error: no custom reminder on/off in database")
        else:
            if len(custom_reminders_list) > 1:
                print("Warning: there are multiple custom reminder on/off entries in the database")
            customreminder_func = custom_reminders_list[0]
        desctext_general.append(f"Custom reminder functionality: `{customreminder_func}`")
        desctext_features.append(f"Custom reminder functionality: `{customreminder_func}`")

        genretagreminder_list = [item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("genre tag reminder",)).fetchall()]
        if len(genretagreminder_list) == 0:
            genretagreminder = "error⚠️"
            print("Error: no genre tag reminder on/off in database")
        else:
            if len(genretagreminder_list) > 1:
                print("Warning: there are multiple genre tag reminder on/off entries in the database")
            genretagreminder = genretagreminder_list[0]
        desctext_general.append(f"GenreTag Remind functionality: `{genretagreminder}`")
        desctext_features.append(f"GenreTag Remind functionality: `{genretagreminder}`")

        penaltynotifier_list = [item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("user mute/ban/kick notification",)).fetchall()]
        if len(penaltynotifier_list) == 0:
            print("Error: no penalty notifier entry in database, i.e. 'user mute/ban/kick notification'.")
            penaltynotifier = "error⚠️"
        else:
            if len(penaltynotifier_list) > 1:
                print("Warning: Multiple 'user mute/ban/kick notification' entries in database.")
            penaltynotifier = penaltynotifier_list[0]
        desctext_general.append(f"Penalty notifier: `{penaltynotifier}`")
        desctext_features.append(f"Penalty notifier: `{penaltynotifier}`")

        pingterest_func_list = [item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("pingable interests functionality",)).fetchall()]
        if len(pingterest_func_list) == 0:
            pingterest_func = "error⚠️"
            print("Error: no pingable interest on/off in database")
        else:
            if len(pingterest_func_list) > 1:
                print("Warning: there are multiple pingable interest on/off entries in the database")
            pingterest_func = pingterest_func_list[0]
        desctext_general.append(f"Pingable interests functionality: `{pingterest_func}`")
        desctext_features.append(f"Pingable interests functionality: `{pingterest_func}`")

        reactionroles_list = [[item[0],item[1]] for item in cur.execute("SELECT value, details FROM serversettings WHERE name = ?", ("reaction roles",)).fetchall()]
        if len(reactionroles_list) == 0:
            reactionroles = "error⚠️"
            sorting = "/"
            print("Error: no reaction roles on/off in database")
        else:
            if len(reactionroles_list) > 1:
                print("Warning: there are multiple reaction roles on/off entries in the database")
            reactionroles = reactionroles_list[0][0]
            sorting = reactionroles_list[0][1]
            if reactionroles == "off":
                sorting = "/"
        desctext_general.append(f"Reaction role system: `{reactionroles}` (sorting: `{sorting}`)")
        desctext_features.append(f"Reaction role system: `{reactionroles}` (sorting: `{sorting}`)")

        timeout_list = [item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("timeout system",)).fetchall()]
        if len(timeout_list) == 0:
            timeout = "error⚠️"
            print("Error: no timeout on/off in database")
        else:
            if len(timeout_list) > 1:
                print("Warning: there are multiple timeout on/off entries in the database")
            timeout = timeout_list[0]
        desctext_general.append(f"Timeout system: `{timeout}`")
        desctext_features.append(f"Timeout system: `{timeout}`")

        welcomemessage_list = [[item[0],item[1],item[2]] for item in cur.execute("SELECT value, details, etc FROM serversettings WHERE name = ?", ("welcome message",)).fetchall()]
        if len(welcomemessage_list) == 0:
            welcomemessage = "error⚠️"
            texttype = "⚠️"
            print("Error: no welcome message on/off in database")
        else:
            if len(welcomemessage_list) > 1:
                print("Warning: there are multiple welcome message on/off entries in the database")
            welcomemessage = welcomemessage_list[0][0]
            if accesswall == "on":
                welcometext = welcomemessage_list[0][2]
            else:
                welcometext = welcomemessage_list[0][1]
            if welcometext.strip() == "":
                texttype = "default"
            else:
                texttype = "custom"
        desctext_general.append(f"Welcome message: `{welcomemessage}` (text: `{texttype}`)")
        desctext_features.append(f"Welcome message: `{welcomemessage}` (text: `{texttype}`)")

        #################################################### NOTIFICATIONS

        desctext_general.append(f"\n**Notifications:**")

        notification_joinleaveserver_list = [item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("join/leave server notification",)).fetchall()]
        if len(notification_joinleaveserver_list) == 0:
            notification_joinleaveserver = "error⚠️"
            print("Error: no join/leave server notification setting in database")
        else:
            if len(notification_joinleaveserver_list) > 1:
                print("Warning: there are multiple join/leave server notification setting entries in the database")
            notification_joinleaveserver = notification_joinleaveserver_list[0]
        desctext_general.append(f"Join/leave server: `{notification_joinleaveserver}`")
        desctext_notifications.append(f"Join/leave server: `{notification_joinleaveserver}`")

        notification_createdeletechannel_list = [item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("create/delete channel notification",)).fetchall()]
        if len(notification_createdeletechannel_list) == 0:
            notification_createdeletechannel = "error⚠️"
            print("Error: no create/delete channel notification setting in database")
        else:
            if len(notification_createdeletechannel_list) > 1:
                print("Warning: there are multiple create/delete channel notification setting entries in the database")
            notification_createdeletechannel = notification_createdeletechannel_list[0]
        desctext_general.append(f"Create/delete channel: `{notification_createdeletechannel}`")
        desctext_notifications.append(f"Create/delete channel: `{notification_createdeletechannel}`")

        notification_createdeletethread_list = [item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("create/delete thread notification",)).fetchall()]
        if len(notification_createdeletethread_list) == 0:
            notification_createdeletethread = "error⚠️"
            print("Error: no create/delete thread notification setting in database")
        else:
            if len(notification_createdeletethread_list) > 1:
                print("Warning: there are multiple create/delete thread notification setting entries in the database")
            notification_createdeletethread = notification_createdeletethread_list[0]
        desctext_general.append(f"Create/delete threads: `{notification_createdeletethread}`")
        desctext_notifications.append(f"Create/delete threads: `{notification_createdeletethread}`")

        notification_createdeleteroles_list = [item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("create/delete role notification",)).fetchall()]
        if len(notification_createdeleteroles_list) == 0:
            notification_createdeleteroles = "error⚠️"
            print("Error: no create/delete roles notification setting in database")
        else:
            if len(notification_createdeleteroles_list) > 1:
                print("Warning: there are multiple create/delete roles notification setting entries in the database")
            notification_createdeleteroles = notification_createdeleteroles_list[0]
        desctext_general.append(f"Create/delete roles: `{notification_createdeleteroles}`")
        desctext_notifications.append(f"Create/delete roles: `{notification_createdeleteroles}`")

        notification_assignroles_list = [item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("assign role notification",)).fetchall()]
        if len(notification_assignroles_list) == 0:
            notification_assignroles = "error⚠️"
            print("Error: no assign roles notification setting in database")
        else:
            if len(notification_assignroles_list) > 1:
                print("Warning: there are multiple assign roles notification setting entries in the database")
            notification_assignroles = notification_assignroles_list[0]
        desctext_general.append(f"Assign/unassign roles: `{notification_assignroles}`")
        desctext_notifications.append(f"Assign/unassign roles: `{notification_assignroles}`")

        notification_joinleavevoicechat_list = [item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("join/leave voicechat notification",)).fetchall()]
        if len(notification_joinleavevoicechat_list) == 0:
            notification_joinleavevoicechat = "error⚠️"
            print("Error: no join/leave voice channel notification setting in database")
        else:
            if len(notification_joinleavevoicechat_list) > 1:
                print("Warning: there are multiple join/leave voice channel notification setting entries in the database")
            notification_joinleavevoicechat = notification_joinleavevoicechat_list[0]
        desctext_general.append(f"Join/leave voice chat: `{notification_joinleavevoicechat}`")
        desctext_notifications.append(f"Join/leave voice chat: `{notification_joinleavevoicechat}`")

        notification_editmessage_list = [item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("edit message notification",)).fetchall()]
        if len(notification_editmessage_list) == 0:
            notification_editmessage = "error⚠️"
            print("Error: no edit message notification setting in database")
        else:
            if len(notification_editmessage_list) > 1:
                print("Warning: there are multiple edit message notification setting entries in the database")
            notification_editmessage = notification_editmessage_list[0]
        desctext_general.append(f"Message edits: `{notification_editmessage}`")
        desctext_notifications.append(f"Message edits: `{notification_editmessage}`")

        notification_namechange_list = [item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("user name change notification",)).fetchall()]
        if len(notification_namechange_list) == 0:
            notification_namechange = "error⚠️"
            print("Error: no user name change notification setting in database")
        else:
            if len(notification_namechange_list) > 1:
                print("Warning: there are multiple user name change notification setting entries in the database")
            notification_namechange = notification_namechange_list[0]
        desctext_general.append(f"Message edits: `{notification_namechange}`")
        desctext_notifications.append(f"Message edits: `{notification_namechange}`")

        notification_scheduledevents_list = [item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("scheduled event notification",)).fetchall()]
        if len(notification_scheduledevents_list) == 0:
            notification_scheduledevents = "error⚠️"
            print("Error: no 'scheduled events' notification setting in database")
        else:
            if len(notification_scheduledevents_list) > 1:
                print("Warning: there are multiple 'scheduled events' notification setting entries in the database")
            notification_scheduledevents = notification_scheduledevents_list[0]
        desctext_general.append(f"Scheduled Events: `{notification_scheduledevents}`")
        desctext_notifications.append(f"Scheduled Events: `{notification_scheduledevents}`")

        notification_invitecreation_list = [item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("invite notification",)).fetchall()]
        if len(notification_invitecreation_list) == 0:
            notification_invitecreation = "error⚠️"
            print("Error: no 'invite creation' notification setting in database")
        else:
            if len(notification_invitecreation_list) > 1:
                print("Warning: there are multiple 'invite creation' notification setting entries in the database")
            notification_invitecreation = notification_invitecreation_list[0]
        desctext_general.append(f"Invite Creation: `{notification_invitecreation}`")
        desctext_notifications.append(f"Invite Creation: `{notification_invitecreation}`")

        notification_modsmodsmods_list = [item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("mods mods mods notification",)).fetchall()]
        if len(notification_modsmodsmods_list) == 0:
            notification_modsmodsmods = "error⚠️"
            print("Error: no 'mods mods mods' notification setting in database")
        else:
            if len(notification_modsmodsmods_list) > 1:
                print("Warning: there are multiple 'mods mods mods' notification setting entries in the database")
            notification_modsmodsmods = notification_modsmodsmods_list[0]
        desctext_general.append(f"'Mods Mods Mods' calls: `{notification_modsmodsmods}`")
        desctext_notifications.append(f"'Mods Mods Mods' calls: `{notification_modsmodsmods}`")


        #################################################### CHANNELS (adding to output)

        desctext_general.append(f"\n**Channels:**")

        desctext_general.append(f"Notification channel: <#{botspamchannel_id}>")
        desctext_channels.append(f"Notification channel: <#{botspamchannel_id}>")

        if welcomemessage == "on":
            desctext_general.append(f"General channel: <#{generalchannel_id}>")
            desctext_channels.append(f"General channel: <#{generalchannel_id}>")

        if reactionroles == "on":
            desctext_general.append(f"Reaction Roles channel: <#{rolechannel_id}>")
            desctext_channels.append(f"Reaction Roles channel: <#{rolechannel_id}>")

        if accesswall == "on":
            desctext_general.append(f"Access wall channel: <#{accesswallchannel_id}>")
            desctext_channels.append(f"Access wall channel: <#{accesswallchannel_id}>")

        if turingtest == "on":
            desctext_general.append(f"Turing test channel: <#{ruleschannel_id}>")
            desctext_channels.append(f"Turing test channel: <#{ruleschannel_id}>")

        #################################################### REACTION ROLES

        if reactionroles == "on":
            desctext_general.append(f"\n**Reaction role categories:**")
            reactionrolesettings_list = [[item[0],item[1],item[2],item[3],item[4]] for item in cur.execute("SELECT name, turn, type, msg_id, rankorder FROM reactionrolesettings").fetchall()]
            if len(reactionrolesettings_list) == 0: 
                reactionroles_text == "none"
            else:
                if rolechannel_id in ["", "not provided"]:
                    reactionroles_text = "none"
                else:
                    #reactionroles_text_list = []
                    reactionrolesettings_list.sort(key=lambda x: int(x[4]))
                    for setting in reactionrolesettings_list:
                        name = setting[0]
                        turn = setting[1]
                        buttontype = setting[2]
                        msg_id = setting[3]
                        order = setting[4]
                        text = f"{order}. {name}: {turn}"

                        if turn == "on":
                            if buttontype == "free":
                                btype = "f"
                            elif buttontype == "radiobutton":
                                btype = "r"
                            else:
                                btype = "?"
                            text += f" https://discord.com/channels/{main_server_id}/{rolechannel_id}/{msg_id} ({btype})"
                        desctext_general.append(text)
                        #reactionroles_text_list.append(text)

                    #reactionroles_text = '\n'.join(reactionroles_text_list)
            desctext_general.append(f"(f): free,   (r): radiobutton")

        #################################################### ROLES

        if accesswall == "off" and automaticrole == "off" and botdisplay == "off" and timeout == "off":
            print("no special roles")
        else:
            desctext_roles.append(f"**Special roles:**")
        if accesswall == "on":
            accesswallrole_list = [item[0] for item in cur.execute("SELECT role_id FROM specialroles WHERE name = ?", ("access wall role",)).fetchall()]
            if len(accesswallrole_list) == 0:
                if accesswall == "off":
                    accesswall_role = "not provided"
                else:
                    accesswall_role = "error⚠️"
                    print("Error: no access wall role in database")
            else:
                if len(accesswallrole_list) > 1:
                    print("Warning: there are multiple access wall role entries in the database")
                accesswall_role = accesswallrole_list[0]
            desctext_roles.append(f"Access wall role: <@&{accesswall_role}>")
        elif accesswall == "off":
            if automaticrole == "on":
                communityrole_list = [item[0] for item in cur.execute("SELECT role_id FROM specialroles WHERE name = ?", ("community role",)).fetchall()]
                if len(communityrole_list) == 0:
                    community_role = "error⚠️"
                    print("Error: no community role in database")
                else:
                    if len(communityrole_list) > 1:
                        print("Warning: there are multiple community entries in the database")
                    community_role = communityrole_list[0]
                desctext_roles.append(f"Community role: <@&{community_role}>")

        if botdisplay == "on":
            botdisplayrole_list = [item[0] for item in cur.execute("SELECT role_id FROM specialroles WHERE name = ?", ("bot display role",)).fetchall()]
            if len(botdisplayrole_list) == 0:
                if botdisplay == "off":
                    botdisplay_role = "not provided"
                else:
                    botdisplay_role = "error⚠️"
                    print("Error: no bot display role in database")
            else:
                if len(botdisplayrole_list) > 1:
                    print("Warning: there are multiple bot display role entries in the database")
                botdisplay_role = botdisplayrole_list[0]
            desctext_roles.append(f"Bot display role: <@&{botdisplay_role}>")

        if timeout == "on":
            timeoutrole_list = [item[0] for item in cur.execute("SELECT role_id FROM specialroles WHERE name = ?", ("timeout role",)).fetchall()]
            if len(timeoutrole_list) == 0:
                if timeout == "off":
                    timeout_role = "not provided"
                else:
                    timeout_role = "error⚠️"
                    print("Error: no timeout role in database")
            else:
                if len(timeoutrole_list) > 1:
                    print("Warning: there are multiple timeout role entries in the database")
                timeout_role = timeoutrole_list[0]
            desctext_roles.append(f"Timeout role: <@&{timeout_role}>")

        if accesswall == "on":
            verifiedrole_list = [item[0] for item in cur.execute("SELECT role_id FROM specialroles WHERE name = ?", ("verified role",)).fetchall()]        
            if len(verifiedrole_list) == 0:
                if accesswall == "off":
                    verified_role = "not provided"
                else:
                    verified_role = "error⚠️"
                    print("Error: no verified role in database")
            else:
                if len(verifiedrole_list) > 1:
                    print("Warning: there are multiple verified role entries in the database")
                verified_role = verifiedrole_list[0]
            desctext_roles.append(f"Verified role: <@&{verified_role}>")

        #################################################### EMOJI

        emojisettings_list = [[item[0],item[1],item[2]] for item in cur.execute("SELECT purpose, call, extra FROM emojis").fetchall()]
        if len(emojisettings_list) == 0: 
            emojis_text == "none"
        else:
            if rolechannel_id in ["", "not provided"]:
                emojis_text = "none"
            else:
                #emojis_text_list = []
                i = 0
                emojisettings_list.sort(key=lambda x: x[0])
                for setting in emojisettings_list:
                    i+=1
                    name = setting[0]
                    call = setting[1]
                    backupcall = setting[2]
                    if call.strip() == "":
                        emoji = backupcall
                    else:
                        emoji = call

                    text = f"{i}. {name}: {emoji}"
                    #emojis_text_list.append(text)
                    desctext_emoji.append(text)
                #reactionroles_text = '\n'.join(reactionroles_text_list)

        ######################################################### KEYS

        try:
            exchangerate_key = os.getenv("exchangerate_key")
            desctext_keys.append("Exchangerate Key: provided ✅")
        except:
            desctext_keys.append("Exchangerate Key: none 🚫")

        try:
            LFM_API_KEY = os.getenv("lfm_api_key")
            desctext_keys.append("LastFM Key: provided ✅")
        except:
            desctext_keys.append("LastFM Key: none 🚫")

        try:
            LFM_SHARED_SECRET = os.getenv("lfm_shared_secret")
            desctext_keys.append("LastFM Secret: provided ✅")
        except:
            desctext_keys.append("LastFM Secret: none 🚫")

        try:
            ClientID = os.getenv("Spotify_ClientID")
            desctext_keys.append("Spotify Client ID: provided ✅")
        except:
            desctext_keys.append("Spotify Client ID: none 🚫")

        try:
            ClientSecret = os.getenv("Spotify_ClientSecret")
            desctext_keys.append("Spotify Client Secret: provided ✅")
        except:
            desctext_keys.append("Spotify Client Secret: none 🚫")



        #################################################### SELF-ASSIGNABLE ROLES

        con = sqlite3.connect('databases/roles.db')
        cur = con.cursor()
        categories = [item[0] for item in cur.execute("SELECT category FROM roles").fetchall()]
        categories = list(dict.fromkeys(categories))
        if len(categories) == 0:
            desctext_roles.append(f"\nno roles in role database, use `{self.prefix}roleupdate`")
        else:
            desctext_roles.append(f"\n**Role categories:**")
        for cat in sorted(categories):
            roles = [[item[0],item[1]] for item in cur.execute("SELECT name, assignable FROM roles WHERE category = ?", (cat,)).fetchall()]
            a = 0 #assignable
            u = 0 #unassignable (for regular users)
            for role in sorted(roles):
                rolename = role[0]
                assignability = role[1].lower()
                if assignability == "true":
                    a += 1
                elif  assignability == "false":
                    u += 1
                else:
                    print(f"Error with assignability of role {rolename}.")
            if len(roles) != a+u:
                unassignability = "(error⚠️)"
            else:
                if a == 0:
                    unassignability = "(🔒)"
                elif u == 0:
                    unassignability = ""
                else:
                    unassignability = f"(🔒`{u}`)"
            desctext_roles.append(f"{cat}: `{len(roles)}` roles {unassignability}")

        ####################################################

        color = 0x468284
        footer = f"server id: {main_server_id}"
        if argument in ["general", "default"]:
            header = f"General settings of {main_server_name}"
            await util.multi_embed_message(ctx, header, desctext_general, color, footer, None)

        elif argument in ["emoji", "emojis", "moji", "mojis"]:
            header = f"Emoji settings of {main_server_name}"
            await util.multi_embed_message(ctx, header, desctext_emoji, color, footer, None)

        elif argument in ["role", "roles"]:
            header = f"Roles settings of {main_server_name}"
            await util.multi_embed_message(ctx, header, desctext_roles, color, footer, None)


        elif argument in ["mod", "mods", "moderator", "moderators", "staff"]:
            header = f"Moderators of {main_server_name}"
            await util.multi_embed_message(ctx, header, desctext_mods, color, footer, None)

        elif argument in ["channel", "channels"]:
            # check threads
            total_text_channels = len(ctx.guild.text_channels)
            total_voice_channels = len(ctx.guild.voice_channels)
            total_threads = "?"
            # under construction (if solution to this found)
            open_threads = 0
            for channel in ctx.guild.text_channels:
                open_threads += len(channel.threads)

            try:
                # fetch reference role (verified/community/everyone)
                reference_role = await util.get_reference_role(ctx)
                # check public channels
                public_channels_readonly = 0
                public_channels_write = 0
                public_open_threads = 0
                for channel in ctx.guild.text_channels:
                    public_perms = channel.permissions_for(reference_role)
                    publicview = False
                    if ('send_messages', True) in public_perms:
                        public_channels_write += 1
                        publicview = True
                    elif ('read_messages', True) in public_perms:
                        public_channels_readonly += 1
                        publicview = True

                    if publicview:
                        for thread in channel.threads:
                            if thread.archived or thread.locked:
                                pass
                            else:
                                public_open_threads += 1
                public_vc = 0
                for channel in ctx.guild.voice_channels:
                    voice_perms = channel.permissions_for(reference_role)
                    if ('connect', True) in voice_perms:
                        public_vc += 1
                public_info = True
            except Exception as e:
                public_info = False
                print(f"Error while trying to check channel publicity: {e}")

            # add info
            desctext_channels.append(f"\n**Channels info:**")
            desctext_channels.append(f"Text channels: {total_text_channels}")
            desctext_channels.append(f"Open threads: {open_threads}")
            desctext_channels.append(f"Voice channels: {total_voice_channels}")
            if public_info:
                desctext_channels.append(f"\n**Public info:**")
                desctext_channels.append(f"Text chat channels: {public_channels_write}")
                desctext_channels.append(f"Read-only channels: {public_channels_readonly}")
                desctext_channels.append(f"Open threads: {public_open_threads}")
                desctext_channels.append(f"Voice channels: {public_vc}")
            header = f"Channel settings of {main_server_name}"
            await util.multi_embed_message(ctx, header, desctext_channels, color, footer, None)

        elif argument in ["feature", "features", "on/off", "onoff"]:
            header = f"Feature settings of {main_server_name}"
            await util.multi_embed_message(ctx, header, desctext_features, color, footer, None)

        elif argument in ["key", "keys"]:
            header = f"Key settings of {main_server_name}"
            await util.multi_embed_message(ctx, header, desctext_keys, color, footer, None)

        elif argument in ["notification", "notifications"]:
            desctext_notifications.append(f"\nNotification channel: <#{botspamchannel_id}>")
            header = f"Notification settings of {main_server_name}"
            await util.multi_embed_message(ctx, header, desctext_notifications, color, footer, None)
        else:
            await ctx.send(f"The provided argument seems to be faulty.")

    @_showsettings.error
    async def showsettings_error(self, ctx, error):
        await util.error_handling(ctx, error)











    #########################################################################################################################################
    #########################################################################################################################################
    #########################################################################################################################################
    #########################################################################################################################################
    #########################################################################################################################################
    #########################################################################################################################################
    #########################################################################################################################################
    #########################################################################################################################################
    #########################################################################################################################################
    #########################################################################################################################################
    #########################################################################################################################################
    #########################################################################################################################################
    #########################################################################################################################################

    # SET COMMAND










    @commands.group(name="set", pass_context=True, invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    @commands.check(util.is_active)
    async def _set(self, ctx):
        """🔒 tweak settings

        ℹ️ Use `-set` without subcommand to get a sorted list of subcommands!
        """
        subcommand_dict = {
            #
            "activity": "",
            #channels:
            "botspamchannel": "channels",
            "generalchannel": "channels",
            "rolechannel": "channels",
            "accesswallchannel": "channels",
            "turingchannel": "channels",
            "genretagchannel": "channels",
            #
            #role stuff:
            "reactrolecat": "role settings", 
            "reactroleorder": "role settings", 
            "reactrolesorting": "role settings", 
            "reactroletype": "role settings", 
            "reactroleembed": "role settings", 
            "rolecat": "role settings", 
            "rolemoji": "role settings", 
            "assignability": "role settings",
            # text customisation
            "accesswalltext": "text customisation", 
            #"turingbantext": "text customisation",
            "welcometext": "text customisation",
            #on/off feature switches:
            "accesswall": "feature on/off switches", 
            "autorole": "feature on/off switches", 
            "turingtest": "feature on/off switches", 
            "turingmsg": "feature on/off switches",
            "turingbanmsg": "feature on/off switches",
            "botroleswitch": "feature on/off switches", 
            "genretagreminder":  "feature on/off switches", 
            "memo": "feature on/off switches", 
            "pingterest": "feature on/off switches", 
            "reactionroles": "feature on/off switches", 
            "reminders": "feature on/off switches",
            "timeout": "feature on/off switches", 
            "welcome": "feature on/off switches", 
            "penaltynotifier": "feature on/off switches", 
            # on/off notifications
            "joinleavenotification": "notification on/off switches", 
            "channelnotification": "notification on/off switches", 
            "threadnotification": "notification on/off switches", 
            "rolenotification": "notification on/off switches", 
            "assignnotification": "notification on/off switches", 
            "vcnotification": "notification on/off switches", 
            "editnotification": "notification on/off switches", 
            "eventnotification": "notification on/off switches", 
            "invite notification": "notification on/off switches", 
            "usernamenotification": "notification on/off switches",
            "modsmodsmodsnotification": "notification on/off switches",
            }
        res = {}
        for key, val in sorted(subcommand_dict.items()):
            if val not in res:
                res[val] = []
            res[val].append(key)

        messagetext = "Needs one of the following subcommands:\n\n"
        for val in sorted(res):
            command_class = str(val)
            if command_class == "":
                command_class = "api & bot settings"
            command_list = ', '.join(sorted(res[val]))
            messagetext += f"**{command_class}**```{command_list}```" 
        await ctx.send(messagetext)
    @_set.error
    async def set_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_set.command(name="activity", aliases = ["status"], pass_context=True)
    @commands.check(util.is_active)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _set_status(self, ctx, *args):
        """Set the bot status displayed in the sidebar

        1st argument needs to be one of the following:
        > c : competing in
        > l : listening to
        > p : playing
        > s : streaming
        > w : watching
        > n : (no status)

        Everything that follows will be part of the bot's activity status.
        """
        if len(args) == 0:
            await ctx.send("Command needs arguments.\n1st arg needs to be C, L, P, S, W or N. The following will be the activity status text.```> c : competing in\n> l : listening to\n> p : playing\n> s : streaming \n> w : watching\n> n : (no status)```")
            return

        stat_type = args[0].lower()

        if stat_type in ["competing", "competingin", "compete"]:
            stat_type = "c"
        elif stat_type in ["listening", "listeningto", "listen"]:
            stat_type = "l"
        elif stat_type in ["playing", "play"]:
            stat_type = "p"
        elif stat_type in ["streaming", "stream"]:
            stat_type = "s"
        elif stat_type in ["watching", "viewing", "watch"]:
            stat_type = "w"
        elif stat_type in ["no", "non", "none", "off"]:
            stat_type = "n"

        if stat_type not in ["c", "l", "p", "s", "w", "n"]:
            await ctx.send("1st arg needs to be C, L, P, S, W or N.")
            return

        if stat_type in ["c", "l", "p", "s", "w"] and len(args) == 1:
            await ctx.send("Provided activity is an empty string.")
            return

        stat_name = ' '.join(args[1:]).replace("\\e", "") # \e empty character

        if len(stat_name) > 128:
            stat_name = stat_name[:128]
            print("Warning: Activity status name too long. Reduced it to 128 chars.")

        try:
            if stat_type == 'c':
                await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.competing, name=stat_name))
                print(f'set status COMPETING IN {stat_name}')
            elif stat_type == 'p':
                await self.bot.change_presence(activity=discord.Game(name=stat_name))
                print(f'set status PLAYING {stat_name}')
            elif stat_type == 's':
                my_twitch_url = "https://www.twitch.tv/mdmbot/home"
                await self.bot.change_presence(activity=discord.Streaming(name=stat_name, url=my_twitch_url))
                print(f'set status STREAMING {stat_name}')
            elif stat_type == 'l':
                await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=stat_name))
                print(f'set status LISTENING TO {stat_name}')
            elif stat_type == 'w':
                await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=stat_name))
                print(f'set status WATCHING {stat_name}')
            elif stat_type == 'n':
                await self.bot.change_presence(activity=None)
                print('empty status')
        except Exception as e:
            print(e)
            await ctx.send("Error while trying to change activity status in discord presence.")
            return

        try:
            con = sqlite3.connect(f'databases/botsettings.db')
            cur = con.cursor()  
            cur.execute("UPDATE botsettings SET value = ?, type = ? WHERE name = ?", (stat_name, stat_type, "status"))
            con.commit()
            await util.changetimeupdate()
        except Exception as e:
            print(e)
            await ctx.send("Error while trying to change activity status in database.")
            return

        await ctx.send("Activity changed!")
    @_set_status.error
    async def set_status_error(self, ctx, error):
        await util.error_handling(ctx, error)


    ################################################################################# CHANNELS
    
    async def database_channel_change(self, ctx, args, db_entry_name):
        channeldict = {
            "access wall channel id": "Access wall channel",
            "botspam channel id": "Botspam/notification channel",
            "general channel id": "General (welcome) channel",
            "role channel id": "(Reaction) Roles channel",
            "rules channel id": "Turing test channel"
        }
        channel_name = channeldict[db_entry_name]
        if len(args) == 0:
            await ctx.send("Command needs an argument.")
            return
        try:
            channel_id, rest = await util.fetch_id_from_args("channel", "first", args)
        except Exception as e:
            await ctx.send(f"Error: {e}")
            return
        for channel in ctx.guild.text_channels:
            if str(channel.id) == channel_id:
                print(f"found channel: {channel.name}")
                break 
        else:
            await ctx.send(f"This channel seems to not exist.")
            return
        try:
            con = sqlite3.connect(f'databases/botsettings.db')
            cur = con.cursor()  
            cur.execute("UPDATE serversettings SET value = ? WHERE name = ?", (channel_id, db_entry_name))
            con.commit()
            await util.changetimeupdate()
        except Exception as e:
            print(e)
            await ctx.send(f"Error while trying to change {channel_name} in database.")
            return
        await ctx.send(f"{channel_name} changed to <#{channel_id}>!")


    @_set.command(name="botspamchannel", aliases = ["notification", "notifications", "notificationchannel", "botspam"], pass_context=True)
    @commands.check(util.is_active)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _set_botspam(self, ctx, *args):
        """Set the botspam/notifications channel id

        Use `-set botspam <channelid>` or `-set botspam <#channelname>`.

        This channel will be used for all kinds of notifications from this bot.
        """
        await self.database_channel_change(ctx, args, "botspam channel id")
    @_set_botspam.error
    async def set_botspam_error(self, ctx, error):
        await util.error_handling(ctx, error)


    @_set.command(name="generalchannel", aliases = ["general"], pass_context=True)
    @commands.check(util.is_active)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _set_general(self, ctx, *args):
        """Set the general channel id

        Use `-set general <channelid>` or `-set general <#channelname>`.

        This channel is where welcome messages will appear.
        """
        await self.database_channel_change(ctx, args, "general channel id")
    @_set_general.error
    async def set_general_error(self, ctx, error):
        await util.error_handling(ctx, error)


    @_set.command(name="rolechannel", aliases = ["roleschannel"], pass_context=True)
    @commands.check(util.is_active)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _set_rolechannel(self, ctx, *args):
        """Set the roles channel id

        Use `-set roles <channelid>` or `-set roles <#channelname>`.

        This channel is where users can assign/unsassign roles to themselves by placing reacts.
        Use `-help set reactionroles`
        """
        await self.database_channel_change(ctx, args, "role channel id")
    @_set_rolechannel.error
    async def set_rolechannel_error(self, ctx, error):
        await util.error_handling(ctx, error)


    @_set.command(name="accesswallchannel", aliases = ["wintersgatechannel"], pass_context=True)
    @commands.check(util.is_active)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _set_accesswallchannel(self, ctx, *args):
        """Set the access wall channel id

        Use `-set accesswallchannel <channelid>` or `-set accesswallchannel <#channelname>`.

        If access wall is enabled, this channel is where new users are placed to itroduce themselves before they are verified and get access to the (rest of the) server.
        """
        await self.database_channel_change(ctx, args, "access wall channel id")
    @_set_accesswallchannel.error
    async def set_accesswallchannel_error(self, ctx, error):
        await util.error_handling(ctx, error)


    @_set.command(name="turingchannel", aliases = ["turingtestchannel"], pass_context=True)
    @commands.check(util.is_active)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _set_turingchannel(self, ctx, *args):
        """Set the turing test channel id

        Use `-set turingchannel <channelid>` or `-set turingchannel <#channelname>`.

        If access wall and turing test are enabled, this channel is where the turing test is conducted to auto-ban bot users.
        See more info with `-help set turingtest`.
        """
        await self.database_channel_change(ctx, args, "rules channel id")
    @_set_turingchannel.error
    async def set_turingchannel_error(self, ctx, error):
        await util.error_handling(ctx, error)



    ################################################################################# 



    @_set.command(name="reactrolecat", aliases = ["reactionrolecategories"], pass_context=True)
    @commands.check(util.is_active)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _set_reactrolecategories(self, ctx, *args):
        """Include/exclude role categories for reaction role feature
        
        1st arg needs to be the category name. (write spaces as underscores)
        2nd arg needs to be `on`, `off`, `rename` or `remove`.

        `on` and `off` enable/disable the availability of role reacts (and adds them to the database if they weren't there before). 
        Use `-rolechannelupdate` to refresh the reaction embeds in the #roles channel.

        With `rename` you can rename a role category. Needs a 3rd argument with a new name.
        With `remove` you can remove a role category entirely from the database.
        Roles of that category will be moved to the default `none` category.

        (Note: using `-set reactrolecat <category name> on` will also automatically make these roles assignable via `-role <role name>` for users, setting role categories `off` does not revert that. To do that use `-set assignability` command.)
        """
        
        if len(args) <= 1:
            await ctx.send("Error: Command needs 1st argument that is the category name and 2nd argument that is either `on`, `off`, `rename` or `remove`")
            return

        category = args[0].lower() #role categories are case insensitive
        subcommand = args[1].lower()
        con = sqlite3.connect(f'databases/botsettings.db')
        cur = con.cursor()

        ##################################### ON

        if subcommand in ["on", "add"]:
            category_turn_list = [item[0] for item in cur.execute("SELECT turn FROM reactionrolesettings WHERE name = ?", (category,)).fetchall()]

            if len(category_turn_list) == 0:

                reactionrolesettings_list = [item[0] for item in cur.execute("SELECT turn FROM reactionrolesettings").fetchall()]
                n_in_reactionrolesettings = len(reactionrolesettings_list)

                info = "\n\nFree categories allow users to select as many roles from the category as they want.\nRadiobutton categories allow only a maximum of 1 role of that category, i.e. recommended for name color roles."
                await ctx.send(f"A category called `{category}` is not yet in the reaction role settings.\nTo configure it as `free` type `F`, to configure it as `radiobutton` type `R`. To leave and cancel this setting type anything else.{info}")
                try: # waiting for message
                    async with ctx.typing():
                        response = await self.bot.wait_for('message', check=check, timeout=30.0) # timeout - how long bot waits for message (in seconds)
                except asyncio.TimeoutError: # returning after timeout
                    await ctx.send("Action timed out.")
                    return

                # if response is different than yes / y - return
                if response.content.lower() not in ["free", "f", "radiobutton", "radio", "r"]:
                    await ctx.send("Cancelled action.")
                    return
                elif response.content.lower() in ["free", "f"]:
                    buttontype = "free"
                    #await ctx.send(f"Set reaction role category `{category}` to `free`.")

                elif response.content.lower() in ["radiobutton", "radio", "r"]:
                    buttontype = "radiobutton"
                    #await ctx.send(f"Set reaction role category `{category}` to `radiobutton`.")

                cur.execute("INSERT INTO reactionrolesettings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (category, "on", buttontype, "", str(n_in_reactionrolesettings+1), "", "", "", ""))
                con.commit()
                await util.changetimeupdate()
                await ctx.send(f"Successfully added reaction role category `{category}`. Switch = `on`, Buttontype = `{buttontype}`.")

            else:
                if len(category_turn_list) > 1:
                    print(f"Warning: There are multiple entries of category '{category}' in the reaction_role_settings table.")
                cur.execute("UPDATE reactionrolesettings SET turn = ? WHERE name = ?", ("on", category))
                con.commit()
                await util.changetimeupdate()
                await ctx.send(f"Changed role reaction setting of `{category}` roles to `on`.\n(Assignability of these roles set to `True`)")

            # CHANGE ASSIGNABILITY IN ROLES.DB

            conR = sqlite3.connect(f'databases/roles.db')
            curR = conR.cursor()

            curR.execute("UPDATE roles SET assignable = ? WHERE LOWER(category) = ?", ("true", category))
            conR.commit()
            await util.changetimeupdate()

            # sanity check

            reference_role = await util.get_reference_role(ctx)
            default_perms = [perm[0] for perm in reference_role.permissions if perm[1]]
            try:
                everyone_perms = await util.get_everyone_perms(ctx)
                default_perms += everyone_perms
            except Exception as e:
                print("Error during sanity check in reactrolecat:", e)

            roles_of_category_list = [item[0] for item in curR.execute("SELECT id FROM roles WHERE category = ?", (category,)).fetchall()]

            roles_n_perms = [[str(r.id), r.permissions] for r in ctx.guild.roles]
            roles_with_higher_perms = []
            for rp in roles_n_perms:
                r_id = rp[0]
                if r_id in roles_of_category_list:
                    r_perm_list = [perm[0] for perm in rp[1] if perm[1]]
                    r_has_higher_perms = False
                    for perm in r_perm_list:
                        if perm in default_perms:
                            pass
                        else:
                            r_has_higher_perms = True
                    if r_has_higher_perms:
                        roles_with_higher_perms.append(r_id)

            if len(roles_with_higher_perms) == 0:
                pass
            else:
                roles_perms_message = f"Some roles of that category have higher perms than the default role <@&{str(reference_role.id)}>:\n\nRoles in question: "
                for role_id in roles_with_higher_perms:
                    roles_perms_message += f"<@&{role_id}> "

                emoji = util.emoji("attention")
                header = f"{emoji} Warning"

                embed=discord.Embed(title=header, description=roles_perms_message[:4096], color=0xFFF200)
                await ctx.send(embed=embed)

        ##################################### OFF

        elif subcommand == "off":
            category_turn_list = [item[0] for item in cur.execute("SELECT turn FROM reactionrolesettings WHERE name = ?", (category,)).fetchall()]

            if len(category_turn_list) == 0:
                reactionrolesettings_list = [item[0] for item in cur.execute("SELECT turn FROM reactionrolesettings").fetchall()]
                n_in_reactionrolesettings = len(reactionrolesettings_list)

                info = "\n\nFree categories allow users to select as many roles from the category as they want.\nRadiobutton categories allow only a maximum of 1 role of that category, i.e. recommended for name color roles."
                await ctx.send(f"A category called `{category}` is not yet in the reaction role settings.\nTo configure it as `free` type `F`, to configure it as `radiobutton` type `R`. To leave and cancel this setting type anything else.{info}")

                try: # waiting for message
                    async with ctx.typing():
                        response = await self.bot.wait_for('message', check=check, timeout=30.0) # timeout - how long bot waits for message (in seconds)
                except asyncio.TimeoutError: # returning after timeout
                    await ctx.send("Action timed out.")
                    return

                # if response is different than yes / y - return
                if response.content.lower() not in ["free", "f", "radiobutton", "radio", "r"]:
                    await ctx.send("Cancelled action.")
                    return
                elif response.content.lower() in ["free", "f"]:
                    buttontype = "free"
                    #await ctx.send(f"Set reaction role category `{category}` to `free`.")

                elif response.content.lower() in ["radiobutton", "radio", "r"]:
                    buttontype = "radiobutton"
                    #await ctx.send(f"Set reaction role category `{category}` to `radiobutton`.")

                cur.execute("INSERT INTO reactionrolesettings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (category, "off", buttontype, "", str(n_in_reactionrolesettings+1), "", "", "", ""))
                con.commit()
                await util.changetimeupdate()
                await ctx.send(f"Successfully added reaction role category `{category}`. Switch = `off`, Buttontype = `{buttontype}`.")

            else:
                if len(category_turn_list) > 1:
                    print(f"Warning: There are multiple entries of category '{category}' in the reaction_role_settings table.")
                cur.execute("UPDATE reactionrolesettings SET turn = ? WHERE name = ?", ("off", category))
                con.commit()
                await util.changetimeupdate()
                await ctx.send(f"Changed role reaction setting of `{category}` roles to `off`.\n(Assignability unchanged, to make these role unassignable use `{self.prefix}set assignability {category} off`.)")

        ##################################### REMOVE

        elif subcommand == "remove":
            category_turn_list = [item[0] for item in cur.execute("SELECT turn FROM reactionrolesettings WHERE name = ?", (category,)).fetchall()]

            if len(category_turn_list) == 0:
                await ctx.send(f"There is no category `{category}` in the database for role reaction category settings.")

            else:
                # DELETE CATEGORY FROM REACTION ROLES SETTING
                cur.execute("DELETE FROM reactionrolesettings WHERE name = ?", (category,))
                con.commit()
                await util.changetimeupdate()

                # RE-RANK OTHER ROLE CATEGORIES
                try:
                    all_categories_list = [[item[0], int(item[1])] for item in cur.execute("SELECT name, rankorder FROM reactionrolesettings").fetchall()]
                    i = 0
                    for item in all_categories_list.sort(key=lambda x: x[1]):
                        i += 1
                        cat = item[0]
                        rank = str(i)
                        cur.execute("UPDATE reactionrolesettings SET rankorder = ? WHERE name = ?", (rank, cat))
                    con.commit()
                except Exception as e:
                    print("Error while trying to update reaction role category ranks:", e)
                    try:
                        all_categories_list_str = [[item[0], item[1]] for item in cur.execute("SELECT name, rankorder FROM reactionrolesettings").fetchall()]
                        all_categories_list = []
                        i = 0
                        for item in all_categories_list_str:
                            i += 1
                            cat = item[0]
                            try:
                                rank = int(item[1])
                            except:
                                rank = len(all_categories_list_str) + i
                            all_categories_list.append([cat, rank])
                        i = 0
                        for item in all_categories_list.sort(key=lambda x: x[1]):
                            i += 1
                            cat = item[0]
                            rank = str(i)
                            cur.execute("UPDATE reactionrolesettings SET rankorder = ? WHERE name = ?", (rank, cat))
                        con.commit()
                    except Exception as e:
                        print("Error while trying to update reaction role category ranks:", e)
                        await ctx.send(f"An error ocurred while trying to update role category ranks")
                        return

                # update roles database
                con = sqlite3.connect(f'databases/roles.db')
                cur = con.cursor()
                role_id_list = [item[0] for item in cur.execute("SELECT id FROM roles WHERE category = ?", (category, )).fetchall()]
                for role_id in role_id_list:
                    cur.execute("UPDATE roles SET category = ? WHERE id = ?", ("none", role_id))
                con.commit()
                await util.changetimeupdate()
                await ctx.send(f"Removed category {category}.")

        ##################################### RENAME

        elif subcommand in ["rename", "rename_to","renameto"]:
            if len(args) <= 2:
                await ctx.send("Error: `rename` command needs a 3rd argument for the new category name (no spaces for new name, use underscores instead).")
                return

            new_category = args[2].lower() #role categories are case insensitive
            if len(args) >= 4 and args[2].lower() == "to":
                new_category = args[3].lower()

            category_turn_list = [item[0] for item in cur.execute("SELECT turn FROM reactionrolesettings WHERE name = ?", (category,)).fetchall()]

            if len(category_turn_list) == 0:
                await ctx.send(f"There is no category `{category}` in the database for role reaction category settings.")

            else:
                # update reaction_role_settings
                cur.execute("UPDATE reactionrolesettings SET name = ? WHERE name = ?", (new_category, category))
                con.commit()

                # update roles database
                con = sqlite3.connect(f'databases/roles.db')
                cur = con.cursor()
                cur.execute("UPDATE roles SET category = ? WHERE category = ?", (new_category, category))
                con.commit()
                await util.changetimeupdate()
                await ctx.send(f"Renamed category {category} to {new_category}.")

        ##################################### ?

        else:
            await ctx.send("Error: Faulty argument.\n1st argument is the category (write spaces as underscores), and 2nd argument needs to be `on`, `off`, `rename` or `remove`")

    @_set_reactrolecategories.error
    async def set_reactrolecategories_error(self, ctx, error):
        await util.error_handling(ctx, error)


    @_set.command(name="reactroleorder", aliases = ["reactionroleorder", "reactionrolerank", "reactioncatorder", "reactioncatrank", "reactioncategoryorder", "reactioncategoryrank", "reactrolerank", "reactcatrank", "reactcategoryrank", "reactcatorder", "reactcategoryorder"], pass_context=True)
    @commands.check(util.is_active)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _set_reactroleorder(self, ctx, *args):
        """Set the order of reaction roles
        
        1st arg needs to be the category name. (no spaces, use underscores)
        2nd arg needs to be an index number.
        """

        if len(args) <= 1:
            await ctx.send("Error: Command needs 1st argument that is the category name and 2nd argument needs to be an integer.")
            return

        con = sqlite3.connect(f'databases/botsettings.db')
        cur = con.cursor()

        # CHECK VALIDITY OF ARGUMENTS

        category = args[0].lower() #role categories are case insensitive
        category_search = [item[0] for item in cur.execute("SELECT rankorder FROM reactionrolesettings WHERE name = ?", (category,)).fetchall()]

        if len(category_search) == 0:
            await ctx.send("Error: Could not find such a reaction role category.")
            return
        elif len(category_search) > 1:
            print(f"Warning: There are multiple role reaction settings of category {category} in the database.")

        try:
            index = int(args[1].lower())
            if index < 0:
                await ctx.send("Error: 2nd argument is negative.")
                return
        except:
            await ctx.send("Error: 2nd argument needs to be an integer.")
            return

        # SORT OLD LIST IN DATABASE (BUT EXCLUDE TARGET CATEGORY)
        
        all_categories_list_str = [[item[0], item[1]] for item in cur.execute("SELECT name, rankorder FROM reactionrolesettings").fetchall()]
        other_categories_list = []
        i = 0
        for item in all_categories_list_str:
            cat = item[0]

            if cat != category:
                i += 1
                try:
                    rank = int(item[1])
                except:
                    rank = len(other_categories_list_str) + i
                other_categories_list.append([cat, rank])

        other_categories_sorted = sorted(other_categories_list, key=lambda x: x[1])

        # RESORT WITH SHIFTING TARGET CATEGORY TO TARGET INDEX

        if index < 1:
            index = 1
        elif index > len(all_categories_list_str):
            index = len(all_categories_list_str)

        i = 0
        for item in other_categories_sorted:
            i += 1
            if index == i: 
                rank = str(i)
                cur.execute("UPDATE reactionrolesettings SET rankorder = ? WHERE name = ?", (rank, category))
                i += 1
            cat = item[0]
            rank = str(i)
            cur.execute("UPDATE reactionrolesettings SET rankorder = ? WHERE name = ?", (rank, cat))
        con.commit()
        await util.changetimeupdate()
        await ctx.send("Reordered reaction roles.")
        
    @_set_reactroleorder.error
    async def set_reactroleorder_error(self, ctx, error):
        await util.error_handling(ctx, error)


    @_set.command(name="reactrolesorting", aliases = ["reactionrolesorting", "reactcategorysorting", "reactioncategorysorting", "reactcatsorting", "reactioncatsorting", "reactrolesort", "reactionrolesort", "reactcategorysort", "reactioncategorysort", "reactcatsort", "reactioncatsort"], pass_context=True)
    @commands.check(util.is_active)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _set_reactrolesorting(self, ctx, *args):
        """Set sorting of roles within category
        
        1st arg needs to be `rank` or `alphabetical`.

        `rank` orders the roles by role hierarchy, that is the order the roles are displayed in the roles settings of the server.
        `alphabetical` sorts them by name.
        """
        if len(args) == 0:
            await ctx.send("Error: Command needs `rank` or `alphabetical` argument.")
            return

        sorting = ' '.join(args).lower()
        if sorting in ["rank", "byrank"]:
            sorting = "by rank"

        if sorting not in ["by rank", "alphabetical"]:
            await ctx.send("Error: 1st argument needs to be `rank` or `alphabetical`.")
            return

        con = sqlite3.connect(f'databases/botsettings.db')
        cur = con.cursor()
        reaction_role_settings_list = [item[0] for item in cur.execute("SELECT details FROM serversettings WHERE name = ?", ("reaction roles", )).fetchall()]

        if len(reaction_role_settings_list) == 0:
            await ctx.send("Error: No entry of reaction role setting in the database.")
        else:
            if len(reaction_role_settings_list) > 1:
                print("Warning: There are multiple reaction roles server settings entries.")

            cur.execute("UPDATE serversettings SET details = ? WHERE name = ?", (sorting, "reaction roles"))
            con.commit()
            await util.changetimeupdate()
            await ctx.send(f"Changed role sorting to `{sorting}`.")
        
    @_set_reactrolesorting.error
    async def set_reactrolesorting_error(self, ctx, error):
        await util.error_handling(ctx, error)


    @_set.command(name="reactroletype", aliases = ["reactionroletype", "reactrolebutton", "reactbuttontype"], pass_context=True)
    @commands.check(util.is_active)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _set_reactroletype(self, ctx, *args):
        """Set button type of roles within category
        
        1st arg needs to be reaction role category name.
        2nd arg needs to be `f` (free) or `r` (radiobutton).

        Free categories allow users to select as many roles from the category as they want.
        Radiobutton categories allow only a maximum of 1 role of that category, i.e. recommended for name color roles.
        """

        if len(args) < 2:
            await ctx.send("Error: Command needs 1st arg category name and 2nd arg `f` (free) or `r` (radiobutton).")
            return

        category = args[0].lower() #role categories are case insensitive
        buttontype = args[1].lower()

        # CHECK VALIDITY OF ARGS

        con = sqlite3.connect(f'databases/botsettings.db')
        cur = con.cursor()
        category_search = [item[0] for item in cur.execute("SELECT rankorder FROM reactionrolesettings WHERE name = ?", (category,)).fetchall()]
        if len(category_search) == 0:
            await ctx.send("Error: Could not find such a reaction role category.")
            return
        elif len(category_search) > 1:
            print(f"Warning: There are multiple role reaction settings of category {category} in the database.")

        if buttontype in ["free"]:
            btype = "f"
        elif buttontype in ["radiobutton", "radio"]:
            btype = "r"
        else:
            await ctx.send("Error: 2nd arguments needs to be either `f` (free) or `r` (radiobutton).")
            return

        # UPDATE DB

        cur.execute("INSERT INTO reactionrolesettings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (category, "off", buttontype, "", str(n_in_reactionrolesettings+1), "", "", "", ""))
        con.commit()
        await util.changetimeupdate()
        await ctx.send(f"Successfully changed `{category}`. Switch = `off`, Buttontype = `{buttontype}`.")

    @_set_reactroletype.error
    async def set_reactroletype_error(self, ctx, error):
        await util.error_handling(ctx, error)


    @_set.command(name="reactroleembed", aliases = ["reactionroleembed"], pass_context=True)
    @commands.check(util.is_active)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _set_reactroleembed(self, ctx, *args):
        """Set customised embed for reaction role category
        
        By default every embed will have a simple title, text, footer and black embed color.
        You can customise some of these values via:
        `-set reactroleembed <category name> ;; <embed title> ;; <embed text> ;; <embed footer> ;; <embed HEX color>`

        You do not have to give all arguments, but you need the double-semicolons, so the bot is able to parse the positional arguments.
        Category name is mandatory, but if you want to -for example- only alter the footer, use
        `-set reactroleembed <category name> ;; ;; ;; <embed footer> ;; `

        If you want to remove a specific entry and set it back to the default write "remove" into the positional argument, 
        e.g.
        `-set reactroleembed <category name> ;; ;; remove ;; ;; remove`
        if you want to remove the embed text and embed HEX color.
        """

        arguments = (' '.join(args)).split(";;")
        if len(arguments) < 5:
            await ctx.send(f"Error: Command needs 5 positional arguments of the form:\n`{self.prefix}set reactroleembed <category name> ;; <embed title> ;; <embed text> ;; <embed footer> ;; <embed HEX color>`\n\nSee `{self.prefix}help set reactroleembed` for more info.")
            return 

        # PARSE ARGUMENTS

        category = arguments[0].strip().lower().replace(" ","_")
        embed_title = arguments[1].strip()
        embed_text = arguments[2].strip()
        embed_footer = arguments[3].strip()
        embed_color = arguments[4].strip()
        action = ""

        if embed_title == "" and embed_text == "" and embed_footer == "" and embed_color == "":
            await ctx.send("Error: No arguments to change provided.")
            return

        if len(embed_title) > 256:
            embed_title = embed_title[:253] + "..."
        if len(embed_text) > 2048:
            embed_text = embed_text[:2045] + "..."
        if len(embed_footer) > 2048:
            embed_footer = embed_footer[:2045] + "..."

        if embed_color not in ["", "remove"]:
            if embed_color.startswith("0x") and len(embed_color) == 8:
                embed_color = embed_color[2:]
            if not embed_color.startswith("#"):
                embed_color = "#" + embed_color
            if not util.hexmatch(embed_color):
                embed_color = ""
                action += "Error with color argument: Set to default black #000000."

        # CHECK VALIDITY OF CATEGORY

        con = sqlite3.connect(f'databases/botsettings.db')
        cur = con.cursor()
        category_search = [item[0] for item in cur.execute("SELECT embed_color FROM reactionrolesettings WHERE LOWER(name) = ?", (category,)).fetchall()]
        if len(category_search) == 0:
            await ctx.send("Error: Could not find such a reaction role category.")
            return
        elif len(category_search) > 1:
            print(f"Warning: There are multiple role reaction settings of category {category} in the database.")

        previous_color = category_search[0]

        # EDIT IN DATABASE

        description = ""

        if embed_title == "":
            # do nothing
            pass
        elif embed_title.lower() in ["remove", "delete"]:
            cur.execute("UPDATE roles SET embed_header = ? WHERE LOWER(category) = ?", ("", category))
            description += "Set embed title back to default.\n" 
        else:
            cur.execute("UPDATE roles SET embed_header = ? WHERE LOWER(category) = ?", (embed_title, category))
            short_header = util.cleantext(embed_header)
            if short_header > 256:
                short_header = short_header[:253] + "..."
            description += f"Set embed title to `{short_header}`.\n" 

        if embed_text == "":
            # do nothing
            pass
        elif embed_text.lower() in ["remove", "delete"]:
            cur.execute("UPDATE roles SET embed_text = ? WHERE LOWER(category) = ?", ("", category))
            description += "Set embed text back to default.\n" 
        else:
            cur.execute("UPDATE roles SET embed_text = ? WHERE LOWER(category) = ?", (embed_text, category))
            short_text = util.cleantext(embed_text)
            if short_text > 256:
                short_text = short_text[:253] + "..."
            description += f"Set embed text to `{short_text}`.\n" 

        if embed_footer == "":
            # do nothing
            pass
        elif embed_footer.lower() in ["remove", "delete"]:
            cur.execute("UPDATE roles SET embed_footer = ? WHERE LOWER(category) = ?", ("", category))
            description += "Set embed footer back to default.\n" 
        else:
            cur.execute("UPDATE roles SET embed_footer = ? WHERE LOWER(category) = ?", (embed_footer, category))
            short_footer = util.cleantext(embed_footer)
            if short_footer > 256:
                short_footer = short_footer[:253] + "..."
            description += f"Set embed footer to `{short_footer}`.\n" 

        if embed_color == "":
            # do nothing
            pass
        elif embed_color.lower() in ["remove", "delete"]:
            cur.execute("UPDATE roles SET embed_color = ? WHERE LOWER(category) = ?", ("", category))
            description += "Set embed footer back to default.\n" 
        else:
            cur.execute("UPDATE roles SET embed_color = ? WHERE LOWER(category) = ?", (embed_color, category))
            description += f"Set embed color to `{embed_color}`.\n" 

        con.commit()
        await util.changetimeupdate()

        # RESPONSE

        try:
            hex_color = int(embed_color.replace("#",""), 16)
        except:
            try:
                hex_color = int(previous_color.replace("#",""), 16)
            except:
                hex_color = 0x000000
        header = f"Changed reaction role embed settings for category {category}"
        embed=discord.Embed(title=header, description=description, color=hex_color)    
        embed.set_footer(text=action)

    @_set_reactroleembed.error
    async def set_reactroleembed_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_set.command(name="rolecat", aliases = ["rolecategory"], pass_context=True)
    @commands.check(util.is_active)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _set_rolecat(self, ctx, *args):
        """Set category for roles
        
        1st arg needs to be the role id, @role mention or role name* 
        (*warning: names aren't necessarily unique)
        2nd argument needs to be the category name of the category you want to place the role under.
        (category cannot have spaces, use underscores instead)
        i.e. `-set rolecat <role id> <cat name>`

        If you want to add multiple roles at once you must use @role mentions for all of them.
        i.e. `-set rolecat <@role1> <@role2> <@role3> <cat name>`
        """

        if len(args) < 2:
            await ctx.send("Error: Command needs 1st arg role id/name/mention and 2nd arg category name.")
            return

        # check if multiple roles are provided

        if len(args) >= 3:
            all_args_mentions = True
            for arg in args[:-1]:
                if len(arg) > 5 and arg[:3] == "<@&" and arg[-1] == ">":
                    try:
                        txt = arg[3:-1]
                        num = int(txt)
                    except:
                        all_args_mentions = False
                else:
                    all_args_mentions = False

        # update role database

        await util.update_role_database(ctx)

        con = sqlite3.connect(f'databases/roles.db')
        cur = con.cursor()
        roles_list = [[item[0],item[1]] for item in cur.execute("SELECT role_id, name FROM roles WHERE id = ?", (role_id,)).fetchall()]


        if all_args_mentions:

            # CHANGE MULTIPLE ROLECATEGORIES (ONLY @MENTIONS)

            category = args[-1].lower() #role categories are case insensitive

            try:
                role_ids_string, rest = await util.fetch_id_from_args("role", "multiple", args[-1])
            except Exception as e:
                print("Error:", e)
                await ctx.send("Error while trying to fetch roles from command arguments.")
                return

            role_id_list = role_ids_string.split(";") #these are the roles to change category for
            errorlist = []

            for role_id in role_id_list:
                for r in roles_list:
                    r_id = r[0]
                    if r_id == role_id:
                        found_role = True
                        the_role_id = r_id
                        the_role_name = r[1]
                        break
                else:
                    found_role = False 

                if not found_role:
                    await ctx.send("Error: Could not find role.")
                    errorlist.append(f"<@&{role_id}>")

                else:
                    # MAKE CHANGES

                    cur.execute("UPDATE roles SET category = ? WHERE id = ?", (category, the_role_id))
                    con.commit()
                    await ctx.send(f"Changed category of role {the_role_name} to {category}")

            await util.changetimeupdate()
            # handle errors
            if len(errorlist) > 0:
                errorlist_string = ',\n'.join(errorlist)
                await ctx.send(f"Errors with the following roles:```{errorlist_string}```")


        else:
            # CHANGE ONE ROLECATEGORY (@MENTION, ID, NAME)

            role_string = ' '.join(args[:-1]).lower()
            role_string_compact = util.alphanum(role_string)
            category = args[-1].lower() #role categories are case insensitive

            # CHECK VALIDITY OF ROLE

            try:
                role_id, rest = await util.fetch_id_from_args("role", "first", [role_string])
            except Exception as e:
                print("Error:", e)
                role_id = "error"


            for r in roles_list:
                r_id = r[0]
                if r_id == role_id:
                    found_role = True
                    the_role_id = r_id
                    the_role_name = r[1]
                    break
            else:
                for r in roles_list:
                    r_id = r[0]
                    r_name = r[1]
                    if r_name == role_string:
                        found_role = True
                        the_role_id = r_id
                        the_role_name = r[1]
                        break
                else:
                    for r in roles_list:
                        r_id = r[0]
                        r_compact = util.alphanum(r[1].lower())
                        if r_compact == role_string_compact:
                            found_role = True
                            the_role_id = r_id
                            the_role_name = r[1]
                            break
                    else:
                        found_role = False 

            if not found_role:
                await ctx.send("Error: Could not find role.")
                return

            # MAKE CHANGES

            cur.execute("UPDATE roles SET category = ? WHERE id = ?", (category, the_role_id))
            con.commit()
            await util.changetimeupdate()

            await ctx.send(f"Changed category of role {the_role_name} to {category}")

    @_set_rolecat.error
    async def set_rolecat_error(self, ctx, error):
        await util.error_handling(ctx, error)


    @_set.command(name="rolemoji", aliases = ["roleemoji"], pass_context=True)
    @commands.check(util.is_active)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _set_rolemoji(self, ctx, *args):
        """Set emoji of roles (for reacts)

        Set emoji for assigning/unassigning a role with a react in #roles channel via
        `-set rolecat <@role> <emoji>`
        1st argument needs to be an @mention of the role or the role id.
        2nd argument needs to be the emoji.

        Keep in mind:
        >> You need to update the #roles channel embeds via `-rcupdate` to let this work properly. (Just changing the emoji without updating the embed will make the assign/unassign not work with the old emoji.)
        >> Only relevant for emojis that ought to be displayed in the #roles channel.
        >> An emoji is not allowed to be assigned to multiple roles.
        
        You can also change multiple role-emojis at once by separating role-emoji pairs with a semicolon.
        i.e. `-set rolecat <@role1> <emoji1>; <@role2> <emoji2> ; <@role3> <emoji3>`
        """

        if len(args) < 2:
            await ctx.send("Error: Command needs 1st arg role id/mention and 2nd arg emoji.\nIf you want to remove the role emoji from a role use `none` as 2nd argument.")
            return

        # PARSE ROLE PART AND EMOJI PART

        args_split = ' '.join(args).split(";")
        role_emoji_pairs = []
        error_1_args = [] # error for not having enough arguments
        for arg in args_split:
            splitstring = arg.strip().split()
            if len(splitstring) >= 1:
                if len(splitstring) >= 2:
                    # 2 arguments
                    role_arg = splitstring[0].strip()
                    emoji_arg = splitstring[1].strip()
                    role_emoji_pairs.append([role_arg, emoji_arg])
                else:
                    # 1 argument (needs splitting)
                    if arg.strip().startswith("<@&"):
                        splitstring = arg.strip().split(">", 1)
                        role_arg = splitstring[0].strip() + ">"
                        emoji_arg = splitstring[1].strip()
                    else:
                        role_arg = ""
                        emoji_arg = ""

                        found_nondigit = False
                        for char in arg.strip():
                            if char in ["0","1","2","3","4","5","6","7","8","9"] and found_nondigit == False:
                                role_arg += char
                            else:
                                found_nondigit = True
                                emoji_arg += char

                        if len(role_arg) > 6 and len(emoji_arg) > 2:
                            role_emoji_pairs.append([role_arg, emoji_arg])
                        else:
                            error_1_args.append(arg.strip())
            else:
                # 0 arguments
                error_1_args.append(arg.strip())

        if len(role_emoji_pairs) == 0:
            await ctx.send(f"Error: Missing arguments.\nUse i.e. `{self.prefix}set rolecat <@role> <emoji>` or provide multiple role-emoji pairs separated by semicolons.")
            return


        # UPDATE ROLE DATABASE

        await util.update_role_database(ctx)

        # CHECK EACH ROLE/EMOJI PAIR

        con = sqlite3.connect('databases/roles.db')
        cur = con.cursor()

        error_2_args = [] # error for faulty roles
        error_3_args = [] # error for faulty emojis
        error_4_args = [] # error for already used emojis
        successful_pairs = []

        for item in role_emoji_pairs:
            role_arg = item[0]
            emoji_arg = item[1]

            # CHECK VALIDITY OF ARGUMENTS: ROLE

            role_id_list = [item[0] for item in cur.execute("SELECT id FROM roles").fetchall()]

            try:
                role_id, rest = await util.fetch_id_from_args("role", "first", [role_arg])
                role_valid = True
            except:
                role_id = "error"
                role_valid = False

            if role_valid and role_id not in role_id_list:
                role_valid = False

            # CHECK VALIDITY OF ARGUMENTS: EMOJI

            if emoji_arg in UNICODE_EMOJI['en']:
                matching_emojis = [item[0] for item in cur.execute("SELECT name FROM roles WHERE details = ?", (emoji_arg,)).fetchall()]
                if len(matching_emojis) == 0:
                    emoji_valid = True
                else:
                    emoji_valid = False
                    error_4_args.append(emoji_arg)
            else:
                mdmbot_emojis = [str(x) for x in self.bot.emojis]
                if emoji_arg in mdmbot_emojis:
                    matching_emojis = [item[0] for item in cur.execute("SELECT name FROM roles WHERE details = ?", (emoji_arg,)).fetchall()]
                    if len(matching_emojis) == 0:
                        print('%s not in use. good.' % str(emoji_arg))
                        emoji_valid = True
                    else:
                        emoji_valid = False
                        error_4_args.append(emoji_arg)
                else:
                    if emoji_arg.lower() in ["none", "`none`", "remove", "delete"]:
                        emoji_valid = True
                        emoji_arg = ""
                    else:
                        emoji_valid = False
                        error_3_args.append(emoji_arg)

            # MAKE CHANGES TO DATABASE

            if emoji_valid and role_valid:
                cur.execute("UPDATE roles SET details = ? WHERE id = ?", (emoji_arg, role_id))
                con.commit()
                successful_pairs.append([role_id, emoji_arg])

        await util.changetimeupdate()

        # SEND MESSAGE

        message_textlist = []
        if len(successful_pairs) == 0:
            message_textlist.append(f"Action failed.\n")
            color = 0xc21807
            header = "Reaction role emoji change attempt"
        else:
            message_textlist.append(f"Successfully changed ascribed emoji of")
            for item in successful_pairs:
                role_id = item[0]
                emoji_arg = item[1]
                message_textlist.append(f"<@&{role_id}> to {emoji_arg}")
            color = 0x3bb143
            header = "Reaction role emoji change"

        if len(error_1_args)+len(error_2_args)+len(error_3_args)+len(error_4_args) > 0:
            message_textlist.append(f"\nErrors:")

            if len(successful_pairs) > 0:
                color = 0xfff700

            if len(error_1_args) > 0:
                error1_text = "Couldn't parse: "
                error1_text += ', '.join(error_1_args) + "."
                message_textlist.append(error1_text)

            if len(error_2_args) > 0:
                error2_text = "Could not find role(s) with id(s): "
                error2_text += ', '.join(error_2_args) + "."
                message_textlist.append(error2_text)

            if len(error_3_args) > 0:
                error2_text = "Could not find emoji(s): "
                error2_text += ', '.join(error_3_args) + "."
                message_textlist.append(error3_text)

            if len(error_4_args) > 0:
                error2_text = "Already used emoji(s): "
                error2_text += ', '.join(error_4_args) + "."
                message_textlist.append(error4_text)

        footer = ""
        await util.multi_embed_message(ctx, header, message_textlist, color, footer, None)

    @_set_rolemoji.error
    async def set_rolemoji_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_set.command(name="assignability", aliases = ["roleassignability"], pass_context=True)
    @commands.check(util.is_active)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _set_assignability(self, ctx, *args):
        """Set assignability of roles

        Use command with role id/mention OR with role category.

        ...
        On setup per default roles without extra permissions (except special functionality roles) are assingnable while everything else isn't.
        After setup every new role created with `-createrole` will be assignable, while every role created otherwise will be set unassignable per default.
        (This is just the default setting and you can always change assignability with this command provided that the command does not have any extra permissions (beyond viewing certain channels).)
        """

        if len(args) < 2:
            await ctx.send("Error: Command needs 1st arg role id/mention or role category name, and 2nd argument `true` or `false`.")
            return

        assignability = util.cleantext(args[-1].lower()).replace("'","")
        role_arg = ' '.join(args[:-1])

        # CHECK VALIDITY OF BOOLEAN ARGUMENT

        if assignability in ["true", "t", "yes", "y", "on"]:
            assignability = "true"
        elif assignability in ["false", "f", "no", "n", "off"]:
            assignability = "false"
        else:
            await ctx.send(f"Invalid boolean argument: {assignability}. Needs to be `true` or `false`.")

        # PARSE ROLE/CATEGORY ARGUMENT

        if role_arg.startswith("<@&") and role_arg.endswith(">"):
            role_id_str = role_arg.replace("<@&","").replace(">","")
            try:
                role_id_int = int(role_id_str)
                role_id = str(role_id_int)
            except:
                await ctx.send("Error: Role mention seems to be incorrect.")
                return

        elif util.represents_integer(role_arg) and len(role_arg) > 7:
            try:
                role_id_int = int(role_arg)
                role_id = str(role_id_int)
            except:
                await ctx.send("Error: Role id seems to be incorrect.")
                return
        else:
            role_id = "none"

        # update role database

        await util.update_role_database(ctx)

        # CHECK VALIDITY OF ROLE/CATEGORY ARGUMENT

        con = sqlite3.connect('databases/roles.db')
        cur = con.cursor()
        all_role_ids = [item[0] for item in cur.execute("SELECT id FROM roles").fetchall()]

        role_found = False
        cat_found = False

        if role_id in all_role_ids:
            role_found = True

        if not role_found:
            conB = sqlite3.connect(f'databases/botsettings.db')
            curB = conB.cursor()
            reaction_categories = [item[0] for item in curB.execute("SELECT name FROM reactionrolesettings").fetchall()]

            for rolecat in reaction_categories:
                if util.alphanum(role_arg,"lower") == util.alphanum(rolecat,"lower"):
                    cat_found = True 
                    category_name = rolecat
                    break

        if not role_found and not cat_found:
            all_role_names = [[item[0],item[1]] for item in cur.execute("SELECT id, name FROM roles").fetchall()]

            for role in all_role_names:
                if util.alphanum(role_arg,"lower") == util.alphanum(role[1],"lower"):
                    role_found = True 
                    role_id = role[0]
                    break 

        # CHANGE ASSIGNABILITY / SEND MESSAGE
        
        if role_found:
            cur.execute("UPDATE roles SET assignable = ? WHERE id = ?", (assignability, str(role_id)))
            con.commit()
            await util.changetimeupdate()
            description = f"Changed assignability of <@&{role_id}> to {assignability}."
            color = 0x5DBB63
            embed=discord.Embed(title="", description=description, color=color)
            await ctx.send(embed=embed)
            return

        if cat_found:
            role_ids = [item[0] for item in cur.execute("SELECT id FROM roles WHERE category = ?", (category_name,)).fetchall()]
            cur.execute("UPDATE roles SET assignable = ? WHERE LOWER(category) = ?", (assignability, category_name.lower()))
            con.commit()
            await util.changetimeupdate()
            description = f"Changed assignability of all roles of category **{category_name}** to {assignability}.\n\nThis includes: "
            n = len(role_ids)
            i = 0
            for r_id in role_ids:
                i += 1
                description += f"<@&{r_id}>"
                if i < n:
                    description += ", "
            color = 0x5DBB63
            embed=discord.Embed(title="", description=description[:4096], color=color)
            await ctx.send(embed=embed)
            return

        await ctx.send("Error: Could not find such a role or category of roles.")

    @_set_assignability.error
    async def set_assignability_error(self, ctx, error):
        await util.error_handling(ctx, error)




    #################################################################################  ON/OFF SWITCH


    async def database_on_off_switch(self, ctx, args, switch_name):
        switch_displayname_dict = {
            "access wall": "Access wall feature",
            "automatic role": "Automatic role (upon join) feature",
            "backlog functionality": "Memo/backlog feature",
            "bot display": "Bot's sidebar role switch",
            "genre tag reminder": "Genre Tag Reminder",
            "pingable interests functionality": "Pingable interest feature",
            "reaction roles": "Reaction role feature",
            "reminder functionality": "Custom reminder feature",
            "timeout system": "Timeout feature",
            "turing test": "Turing test feature",
            "user mute/ban/kick notification": "User penalty notifier",
            "turing ban message": "TuringTest ban message",
            "welcome message": "Welcoming feature",
            #
            "assign role notification": "Role (assign/unassign) notification",
            "create/delete channel notification": "Channel (create/delete) notification",
            "create/delete role notification": "Role (create/delete) notification",
            "create/delete thread notification": "Thread (create/delete) notification",
            "edit message notification": "Message editing notification",
            "join/leave server notification": "Server joining/leaving notification",
            "join/leave voicechat notification": "Voice chat (join/leave) notification",
            "mods mods mods notification": "Mods mods mods notification",
            "scheduled event notification": "Scheduled Event Notification",
            "invite notification": "Invite Creation Notification",
            "user name change notification": "User servername change notification",
        }
        switch_displayname = switch_displayname_dict[switch_name]

        if len(args) == 0:
            await ctx.send("Command needs an `on` or `off` argument.")
            return

        switchturn = args[0].lower().replace("`","")

        if switchturn not in ["on", "off"]:
            await ctx.send("Argument needs to be either `on` or `off`.")
            return

        try:
            con = sqlite3.connect(f'databases/botsettings.db')
            cur = con.cursor()  
            cur.execute("UPDATE serversettings SET value = ? WHERE name = ?", (switchturn, switch_name))
            con.commit()
            await util.changetimeupdate()
        except Exception as e:
            print(e)
            await ctx.send(f"Error while trying to change {switch_displayname} in database.")
            return
        await ctx.send(f"{switch_displayname} turned {switchturn}!")


    @_set.command(name="accesswall", aliases = ["wintersgate"], pass_context=True)
    @commands.check(util.is_active)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _set_accesswall(self, ctx, *args):
        """Enable/disable access wall
        
        1st arg needs to be `on` or `off`.

        An access wall is a system where newly joining users will have to introduce themselves and then be verified by a moderator before they can see and access the rest of the server.
        You will need a seperate channel (specify with command `-set accesschannel <channel id>`) where new users will land instead, as well as 2 roles: 
        One for the newly joined members (specify with command `-set accessrole <role id>`),
        and one for all the verified members (specify with command `-set verifiedrole <role id>`).

        Keep in mind that you also need to change permission so that all channels, except e.g. #rules, #roles, #announcements (that should be visible to all) need to be ONLY accessible by members who have the verified role. Also, members with the access wall role need to be able to access the access wall channel.

        If you're newly setting up this access wall, use `-verifyall` to verify all members that have already joined.
        """
        await self.database_on_off_switch(ctx, args, "access wall")
    @_set_accesswall.error
    async def set_accesswall_error(self, ctx, error):
        await util.error_handling(ctx, error)


    @_set.command(name="autorole", aliases = ["communityrole"], pass_context=True)
    @commands.check(util.is_active)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _set_autorole(self, ctx, *args):
        """Enable/disable auto role assignment on join

        1st arg needs to be `on` or `off`.

        In case an access wall is NOT set up it may still make sense to assign all new members a member or community role automatically.
        Set up the auto-role via `-set autorole <role id>`.
        """
        await self.database_on_off_switch(ctx, args, "automatic role")
    @_set_autorole.error
    async def set_autorole_error(self, ctx, error):
        await util.error_handling(ctx, error)


    @_set.command(name="turingtest", aliases = ["turing"], pass_context=True)
    @commands.check(util.is_active)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _set_turingtest(self, ctx, *args):
        """Enable/disable turing test
        (only available if access wall is enabled)

        1st arg needs to be `on` or `off`.

        Since many (malicious) bot accounts join servers these days, there is a little *turing test* you can enable to automatically ban them.
        The functionality is simple: A lot of these bot accounts try to pretend to be human users by reacting to the last few messages in channels they can access (such as #roles and #rules). 
        Since most just pick the first placed reaction on these messages, we suggest to write into your #rules that users shall not react with whatever the first react on this message is until they are verified, because they'd automatically get auto-banned.
        This application will then ban anyone with the access wall role but no verified role who reacts to a specific message designated via `-set turingmsg <message id>` (the last message in the #rules channel is recommended).
        """
        await self.database_on_off_switch(ctx, args, "turing test")
    @_set_turingtest.error
    async def set_turingtest_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_set.command(name="turingbanmsg", aliases = ["turingbanmessage"], pass_context=True)
    @commands.check(util.is_active)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _set_turingbanmsg(self, ctx, *args):
        """Enable/disable turing ban message
        (only available if turing test is enabled)

        1st arg needs to be `on` or `off`.

        Notify banned members."""
        await self.database_on_off_switch(ctx, args, "turing ban message")
    @_set_turingbanmsg.error
    async def set_turingbanmsg_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_set.command(name="turingmsg", aliases = ["turingcalibration", "turingmessage"], pass_context=True)
    @commands.check(util.is_active)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _set_turingcalibration(self, ctx, *args):
        """Recalibrate turing test

        Takes last message in designated Turing Test channel, provided via `-set turingchannel <channel id>` (rec.: #rules channel), and designates it to be the message where the *Turing Test* is performed. See `-help set turingtest` for more info.

        Optional: 1st argument can be a message id to pick a specific message other than the last one.
        """

        # GET TURING CHANNEL

        con = sqlite3.connect(f'databases/botsettings.db')
        cur = con.cursor()  

        try:
            rules_channel_id = [item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("rules channel id",)).fetchall()][0].strip()
        except Exception as e:
            print(e)
            await ctx.send(f"Error while trying to fetch ID of channel that was chosen for the Turing test.\nUse `{self.prefix}set turingchannel #channel` and choose a valid channel.")
            return

        for channel in ctx.guild.text_channels:
            if str(channel.id) == rules_channel_id:
                turing_channel = channel
                break 
        else:
            await ctx.send(f"The channel left in the database seems to not exist.\nUse `{self.prefix}set turingchannel #channel` and choose a valid channel.")
            return

        # SET ID OF TURING MESSAGE

        if len(args) == 0: 
            # if no argument is provided look for last message in channel
            message = await channel.fetch_message(turing_channel.last_message_id)
            turingmsg_id = str(message.id)

            reactions = message.reactions
            if len(reactions) == 0:
                turingmsg_emoji = util.emoji("pensive") 
                await message.add_reaction(turingmsg_emoji)
            else:
                turingmsg_emoji = str(reactions[0])
        else: 
            # if argument is provided try to fetch that message
            turingmsg_arg = args[0].lower()
            if turingmsg_id.startswith("https://discord.com/channels/"):
                turingmsg_id = turingmsg_arg.split("/")[-1]
            else:
                turingmsg_id = turingmsg_arg
            try:
                turingmsg_id_int = int(turingmsg_id)
            except:
                print("Error: Argument not an integer (or message link)")
                await ctx.send(f"Error: Provided argument faulty. Argument needs to be a Message ID or a Message Link.")
                return
            try:
                message = await the_channel.fetch_message(turingmsg_id_int)
            except Exception as e:
                print(e)
                await ctx.send(f"Error: Could not find message in channel {the_channel.mention}.")
                return

            reactions = message.reactions
            if len(reactions) == 0:
                turingmsg_emoji = util.emoji("pensive") 
                await message.add_reaction(turingmsg_emoji)
            else:
                turingmsg_emoji = str(reactions[0])

        # UPDATE DB

        cur.execute("UPDATE serversettings SET value = ? WHERE name = ?", (turingmsg_id, "rules message id"))
        cur.execute("UPDATE serversettings SET value = ? WHERE name = ?", (turingmsg_emoji, "rules first reaction"))
        con.commit()
        await util.changetimeupdate()

        await ctx.send(f"Done. Set trigger to: {turingmsg_emoji}")
    @_set_turingcalibration.error
    async def set_turingcalibration_error(self, ctx, error):
        await util.error_handling(ctx, error)


    @_set.command(name="botroleswitch", aliases = ["displayroleswitch"], pass_context=True)
    @commands.check(util.is_active)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _set_botrole(self, ctx, *args):
        """Enable/disable switching display role

        1st arg needs to be `on` or `off`.

        This feature is only needed in case this application runs on multiple instances for redundancy.
        Since it might be helpful to only have the active instance displayed on the sidebar you can let the application automatically assign/unassign the role from the active/inactive instances of this bot if this feature is set to `on`.
        The bot role has to specified via `-set botrole <role id>`
        """
        await self.database_on_off_switch(ctx, args, "bot display")
    @_set_botrole.error
    async def set_botrole_error(self, ctx, error):
        await util.error_handling(ctx, error)


    @_set.command(name="memo", aliases = ["backlog", "memos", "backlogs"], pass_context=True)
    @commands.check(util.is_active)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _set_memo(self, ctx, *args):
        """Enable/disable memo/backlog functionality

        1st arg needs to be `on` or `off`.

        This is a memo feature with which all users can add and remove items to their personal memo.
        (The memo will be accessible outside of the main server as well.)
        """
        await self.database_on_off_switch(ctx, args, "backlog functionality")
    @_set_memo.error
    async def set_memo_error(self, ctx, error):
        await util.error_handling(ctx, error)


    @_set.command(name="genretagreminder", aliases = ["genrereminder", "tagreminder"], pass_context=True)
    @commands.check(util.is_active)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _set_genretagreminder(self, ctx, *args):
        """Enable/disable memo/backlog functionality

        1st arg needs to be `on` or `off`.

        This is a reminder feature that notifies people to tag their spotify/youtube/applemusic links with a genre or ffo (for fans of) for specific channels.
        To edit channels use `-set genretagchannels`.
        """
        await self.database_on_off_switch(ctx, args, "genre tag reminder")
    @_set_genretagreminder.error
    async def set_genretagreminder_error(self, ctx, error):
        await util.error_handling(ctx, error)


    @_set.command(name="pingterest", aliases = ["pingterests", "pingableinterests"], pass_context=True)
    @commands.check(util.is_active)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _set_pingterest(self, ctx, *args):
        """Enable/disable pingable interest functionality

        1st arg needs to be `on` or `off`.

        This is a notification feature where users can create/join/leave interest topics and can then be pinged via `-ping <interest>`.
        This is functionally not really different from Roles, but sometimes servers do not want to have Roles that are too off-topic, so this is a way to have 'less official' interest roles.
        (They also function outside of the main server.)
        """
        await self.database_on_off_switch(ctx, args, "pingable interests functionality")
    @_set_pingterest.error
    async def set_pingterest_error(self, ctx, error):
        await util.error_handling(ctx, error)


    @_set.command(name="reactionroles", aliases = ["reactionrole"], pass_context=True)
    @commands.check(util.is_active)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _set_reactionroles(self, ctx, *args):
        """Enable/disable reaction roles

        1st arg needs to be `on` or `off`.

        Sometimes it's easier to have a #roles channel where people can pick their roles such as username color, pronouns, etc. by just placing a react.
        """
        await self.database_on_off_switch(ctx, args, "reaction roles")
    @_set_reactionroles.error
    async def set_reactionroles_error(self, ctx, error):
        await util.error_handling(ctx, error)


    @_set.command(name="timeout", aliases = ["muting"], pass_context=True)
    @commands.check(util.is_active)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _set_timeout(self, ctx, *args):
        """Enable/disable timeout functionality

        1st arg needs to be `on` or `off`.

        Discord's native timeout system to mute users can be a bit clunky. With this feature mods can lock users out of the server for a given time (or indefinitely), while keeping some customisability such as which channels a user can still read or having a customised message in the dedicated timeout channel. Additionally, users can `-selfmute` for a given time if they want to pause from the server for i.e. studying.

        To properly set this feature up the following things would be required:
        > a timeout channel that is not visible for regular users
        > a timeout role that on its own has no writing perms on the server, and viewing perms limited to the timeout channel (and if you like some other view-only channels, i.e. the #rules channel)
        """
        await self.database_on_off_switch(ctx, args, "timeout system")
    @_set_timeout.error
    async def set_timeout_error(self, ctx, error):
        await util.error_handling(ctx, error)


    @_set.command(name="welcome", aliases = ["welcoming"], pass_context=True)
    @commands.check(util.is_active)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _set_welcome(self, ctx, *args):
        """Enable/disable welcome message

        1st arg needs to be `on` or `off`.

        Discord's own welcoming message can be a bit eh. With this feature mods can set a custom welcome message. Also, in case an access wall is set up, the welcome message will be sent for all to see once a user is actually verified instead and not when they join. (The message they get upon joining will be handled by the access wall system. See `-help set accesswall` for more info.)

        Use `-welcomemsg <text>` to set a custom welcome message. Use `\\n` for line breaks and `@user` for mentioning the joinee.
        """
        await self.database_on_off_switch(ctx, args, "welcome message")
    @_set_welcome.error
    async def set_welcome_error(self, ctx, error):
        await util.error_handling(ctx, error)


    @_set.command(name="penaltynotifier", aliases = ["userpenaltynotification", "usernotification", "userpenaltynotifier", "usernotifier"], pass_context=True)
    @commands.check(util.is_active)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _set_penaltynotifier(self, ctx, *args):
        """Enable/disable notification for users that get muted/kicked/banned

        1st arg needs to be `on` or `off`.

        If this feature is enabled users get notified when they are muted, kicked or banned from the server. 
        However, if the access wall is enabled they only get notified if they are verified members.
        """
        await self.database_on_off_switch(ctx, args, "user mute/ban/kick notification")
    @_set_penaltynotifier.error
    async def set_penaltynotifier_error(self, ctx, error):
        await util.error_handling(ctx, error)


    @_set.command(name="reminders", aliases = ["reminder", "reminderfunctionality"], pass_context=True)
    @commands.check(util.is_active)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _set_reminders(self, ctx, *args):
        """Enable/disable custom reminders

        1st arg needs to be `on` or `off`.

        If this feature is enabled all users can create reminders via `-remind`. If not, then only mods can do that. 
        Already existing reminders will still trigger even if this feature is disabled.
        Existing recurring reminders will trigger without pinging as long as this feature is disabled.
        """
        await self.database_on_off_switch(ctx, args, "reminder functionality")
    @_set_reminders.error
    async def set_reminders_error(self, ctx, error):
        await util.error_handling(ctx, error)



    ################################################################################# ON/OFF (NOTIFICATIONS)


    @_set.command(name="channelnotification", aliases = ["channelsnotification"], pass_context=True)
    @commands.check(util.is_active)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _set_channelnotification(self, ctx, *args):
        """Enable/disable notifications for channel creations/deletions/changes

        1st arg needs to be `on` or `off`.
        """
        await self.database_on_off_switch(ctx, args, "create/delete channel notification")
    @_set_channelnotification.error
    async def set_channelnotification_error(self, ctx, error):
        await util.error_handling(ctx, error)


    @_set.command(name="threadnotification", aliases = ["threadsnotification"], pass_context=True)
    @commands.check(util.is_active)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _set_threadnotification(self, ctx, *args):
        """Enable/disable notifications for thread creations/deletions/changes

        1st arg needs to be `on` or `off`.
        """
        await self.database_on_off_switch(ctx, args, "create/delete thread notification")
    @_set_threadnotification.error
    async def set_threadnotification_error(self, ctx, error):
        await util.error_handling(ctx, error)


    @_set.command(name="rolenotification", aliases = ["rolesnotification"], pass_context=True)
    @commands.check(util.is_active)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _set_rolenotification(self, ctx, *args):
        """Enable/disable notifications for role creations/deletions/changes

        1st arg needs to be `on` or `off`.
        """
        await self.database_on_off_switch(ctx, args, "create/delete role notification")
    @_set_rolenotification.error
    async def set_rolenotification_error(self, ctx, error):
        await util.error_handling(ctx, error)


    @_set.command(name="assignnotification", aliases = ["assignotification"], pass_context=True)
    @commands.check(util.is_active)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _set_assignnotification(self, ctx, *args):
        """Enable/disable notifications for role assigning/unassigning

        1st arg needs to be `on` or `off`.
        """
        await self.database_on_off_switch(ctx, args, "assign role notification")
    @_set_assignnotification.error
    async def set_assignnotification_error(self, ctx, error):
        await util.error_handling(ctx, error)


    @_set.command(name="vcnotification", aliases = ["voicechatnotification"], pass_context=True)
    @commands.check(util.is_active)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _set_vcnotification(self, ctx, *args):
        """Enable/disable notifications for voice chat join/leave

        1st arg needs to be `on` or `off`.
        """
        await self.database_on_off_switch(ctx, args, "join/leave voicechat notification")
    @_set_vcnotification.error
    async def set_vcnotification_error(self, ctx, error):
        await util.error_handling(ctx, error)

    

    @_set.command(name="joinleavenotification", aliases = ["serverjoinleavenotification"], pass_context=True)
    @commands.check(util.is_active)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _set_joinleavenotification(self, ctx, *args):
        """Enable/disable notifications for members joining/leaving the server

        1st arg needs to be `on` or `off`.
        """
        await self.database_on_off_switch(ctx, args, "join/leave server notification")
    @_set_joinleavenotification.error
    async def set_joinleavenotification_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_set.command(name="editnotification", aliases = ["msgeditnotification", "messageeditnotification"], pass_context=True)
    @commands.check(util.is_active)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _set_editnotification(self, ctx, *args):
        """Enable/disable notifications for edited and deleted messages

        1st arg needs to be `on` or `off`.
        """
        await self.database_on_off_switch(ctx, args, "edit message notification")
    @_set_editnotification.error
    async def set_editnotification_error(self, ctx, error):
        await util.error_handling(ctx, error)


    @_set.command(name="usernamenotification", aliases = ["namechangenotification"], pass_context=True)
    @commands.check(util.is_active)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _set_usernamenotification(self, ctx, *args):
        """Enable/disable notifications for when users change their server name

        1st arg needs to be `on` or `off`.
        """
        await self.database_on_off_switch(ctx, args, "user name change notification")
    @_set_usernamenotification.error
    async def set_usernamenotification_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_set.command(name="eventnotification", aliases = ["eventsnotification", "scheduledeventnotification", "scheduledeventsnotification"], pass_context=True)
    @commands.check(util.is_active)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _set_scheduledeventnotification(self, ctx, *args):
        """Enable/disable notifications for scheduled events

        1st arg needs to be `on` or `off`.
        """
        await self.database_on_off_switch(ctx, args, "scheduled event notification")
    @_set_scheduledeventnotification.error
    async def set_scheduledeventnotification_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_set.command(name="invitenotification", aliases = ["invitationnotification", "invitecreatenotification"], pass_context=True)
    @commands.check(util.is_active)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _set_invitenotification(self, ctx, *args):
        """Enable/disable notifications for invite creation

        1st arg needs to be `on` or `off`.
        """
        await self.database_on_off_switch(ctx, args, "invite notification")
    @_set_invitenotification.error
    async def set_invitenotification_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_set.command(name="modsmodsmodsnotification", aliases = ["modsmodsmods"], pass_context=True)
    @commands.check(util.is_active)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _set_modsmodsmodsnotification(self, ctx, *args):
        """Enable/disable notifications for when users write 'mods mods mods'

        1st arg needs to be `on` or `off`.
        """
        await self.database_on_off_switch(ctx, args, "mods mods mods notification")
    @_set_modsmodsmodsnotification.error
    async def set_modsmodsmodsnotification_error(self, ctx, error):
        await util.error_handling(ctx, error)




    #######################################################################################################

    @_set.command(name="emoji", aliases = ["emojis"], pass_context=True)
    @commands.check(util.is_active)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _set_emojis(self, ctx, *args):
        """Set emojis the bot uses in its messages

        1st arg needs to be the emoji's shorthand name as you can find in `-settings emoji`.
        2nd arg needs to be the new emoji.
        """
        if len(args) <= 1:
            await ctx.send(f"Error: Too few arguments.\n1st arg needs to be the emoji's shorthand name as you can find in `{self.prefix}settings emoji`.\n2nd arg needs to be the new emoji.")
            return

        con = sqlite3.connect(f'databases/botsettings.db')
        cur = con.cursor()
        emoji_shortnames = [item[0] for item in cur.execute("SELECT purpose FROM emojis").fetchall()] 

        shortname = args[0].lower()
        new_emoji = args[1]

        if shortname not in emoji_shortnames:
            await ctx.send(f"Error: Could not find this shortname.\nCheck with `{self.prefix}settings emoji` which shortnames currently exist in the database.")
            return

        cur.execute("UPDATE emojis SET call = ? WHERE purpose = ?", (new_emoji, shortname))
        con.commit()
        await util.changetimeupdate()

        await ctx.send("Done.")

    @_set_emojis.error
    async def set_emojis_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_set.command(name="genretagchannel", aliases = ["genretagchannels"], pass_context=True)
    @commands.check(util.is_active)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _set_genretagchannel(self, ctx, *args):
        """Set the channels where the genre tag reminder is active

        1st argument needs to be add or remove to change channels
        1st arg can be show to just show channels
        """
        if len(args) == 0:
            await ctx.send("Error: Command needs either 1st arg `add` or `remove` followed by channel ids, or 1st arg `show`.")

        directive = args[0].lower()

        con = sqlite3.connect(f'databases/botsettings.db')
        cur = con.cursor()

        genretagreminder_list = [item[0] for item in curB.execute("SELECT etc FROM serversettings WHERE name = ?", ("genre tag reminder",)).fetchall()]
        if len(genretagreminder_list) == 0:
            cur.execute("INSERT INTO serversettings VALUES (?, ?, ?, ?)", ("genre tag reminder", "off", "", ""))
            con.commit()
            await util.changetimeupdate()
            channel_list = []
        else:
            channel_list = genretagreminder_list[0].split(";;")

        if directive in ["add", "insert", "remove", "delete", "del", "rem", "show", "display"]:
            try:
                given_channels_str, rest = await util.fetch_id_from_args("channel", "multiple", args)
                given_channels = given_channels_str.split(";")
            except Exception as e:
                await ctx.send(f"Error while trying to fetch channel args: {e}")
                return

        if directive in ["add", "insert"]:
            for channel in given_channels:
                if channel not in channel_list:
                    channel_list.append()
            channel_list_str = ';;'.join(channel_list)
            cur.execute("UPDATE serversettings SET etc = ? WHERE name = ?", (channel_list_str, "genre tag reminder"))
            con.commit()
            await util.changetimeupdate()

        elif directive in ["remove", "delete", "del", "rem"]:
            for channel in given_channels:
                if channel in channel_list:
                    channel_list.remove(channel)
            channel_list_str = ';;'.join(channel_list)
            cur.execute("UPDATE serversettings SET etc = ? WHERE name = ?", (channel_list_str, "genre tag reminder"))
            con.commit()
            await util.changetimeupdate()

        elif directive in ["show", "display"]:
            pass

        else:
            await ctx.send("Error: Command needs either 1st arg `add` or `remove` followed by channel ids, or 1st arg `show`.")
            return

        header = "Genre Tag Reminder Channels"
        description = ""
        for channel in channel_list:
            description += f"<#{channel}> "
        embed=discord.Embed(title=header, description=description[:4096], color=0x000000)
        await ctx.send(embed=embed)
    @_set_genretagchannel.error
    async def set_genretagchannel_error(self, ctx, error):
        await util.error_handling(ctx, error)


    # other text customisation

    @_set.command(name="welcometext", aliases = ["welcomemsgtext", "welcomemessagetext"], pass_context=True)
    @commands.check(util.is_active)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _set_welcometext(self, ctx, *args):
        """Set the welcome message text

        Depending on whether the access wall is set `on` or `off` you can set a different text that will be saved
        """
        con = sqlite3.connect(f'databases/botsettings.db')
        cur = con.cursor()
        user_id = str(ctx.message.author.id)
        
        if len(args) == 0:
            text = ""
        else:
            text = ' '.join(args)

        # Check whether accesswall on/off
        accesswall_list = [item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("access wall",)).fetchall()]
        if len(accesswall_list) == 0:
            accesswall = "off"
        else:
            accesswall = accesswall_list[0].lower()

        # EDIT IN DATABASE
        if accesswall != "on":
            yayemoji = util.emoji("yay")
            default_text = f'Welcome <@{user_id}>! {yayemoji}'
            cur.execute("UPDATE serversettings SET details = ? WHERE name = ?", (text, "welcome message"))
        else:
            yayemoji = util.emoji("yay")
            excitedemoji = util.emoji("excited_alot")
            default_text = f'Welcome <@{user_id}>! {yayemoji}\nYou made it {excitedemoji}'
            cur.execute("UPDATE serversettings SET etc = ? WHERE name = ?", (text, "welcome message"))
        con.commit()  
        await util.changetimeupdate()

        # RESPONSE
        if len(args) == 0:
            await ctx.send("Set welcome message text back to default.")
            welcome_text = default_text
        else:
            await ctx.send("Done.")
            welcome_text = await util.customtextparse(text, user_id)

        # PREVIEW
        await ctx.send("`PREVIEW:`\n" + welcome_text)

    @_set_welcometext.error
    async def set_welcometext_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_set.command(name="accesswalltext", aliases = ["accesswallmsg"], pass_context=True)
    @commands.check(util.is_active)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _set_accesswalltext(self, ctx, *args):
        """Set the initial message text in the access wall when new users join 
        """
        con = sqlite3.connect(f'databases/botsettings.db')
        cur = con.cursor()
        user_id = str(ctx.message.author.id)
        
        if len(args) == 0:
            text = ""
        else:
            text = ' '.join(args)

        # EDIT IN DATABASE
        cur.execute("UPDATE serversettings SET etc = ? WHERE name = ?", (text, "access wall"))
        con.commit()
        await util.changetimeupdate()

        # RESPONSE
        if len(args) == 0:
            await ctx.send("Set access wall message text back to default.")
            accesswall_text = f'Welcome <@{user_id}>!\nGive us a little intro about yourself and a moderator will verify and grant you access to the rest of the server as soon as possible.'
        else:
            await ctx.send("Done.")
            accesswall_text = await util.customtextparse(text, user_id)

        # PREVIEW
        await ctx.send("`PREVIEW:`\n" + accesswall_text)

    @_set_accesswalltext.error
    async def set_accesswalltext_error(self, ctx, error):
        await util.error_handling(ctx, error)



    @_set.command(name="turingbantext", aliases = ["turingbanmsgtext", "turingbanmessagetext"], pass_context=True)
    @commands.check(util.is_active)
    @commands.has_permissions(manage_guild=True)
    @commands.check(util.is_main_server)
    async def _set_turingbantext(self, ctx, *args):
        """Set the ban message text for those failing the turing test.

        Use command without argument to disable message.
        """
        con = sqlite3.connect(f'databases/botsettings.db')
        cur = con.cursor()
        user_id = str(ctx.message.author.id)
        
        if len(args) == 0:
            text = ""
        else:
            text = ' '.join(args)

        # CHECK IF ACCESS WALL, TURING TEST AND TURING BAN MESSAGE FEATURE IS ENABLED
        disabled_list = []
        turingbanmessage_list = [item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("turing ban message",)).fetchall()]
        if len(turingbanmessage_list) == 0:
            turingbanmessage = "off"
        else:
            turingbanmessage = turingbanmessage_list[0].lower()
            if turingbanmessage == "on":
                disabled_list.append("the turing ban message")

        accesswall_list = [item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("access wall",)).fetchall()]
        if len(accesswall_list) == 0:
            accesswall = "off"
        else:
            accesswall = accesswall_list[0].lower()
            if accesswall == "on":
                disabled_list.append("the access wall")

        turingtest_list = [item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("turing test",)).fetchall()]
        if len(accesswall_list) == 0:
            turingtest = "off"
        else:
            turingtest = turingtest_list[0].lower()
            if turingtest == "on":
                disabled_list.append("the turing test")

        if len(disabled_list) > 0:
            note = "\nNote that "
            note += ', '.join(disabled_list)
            if len(disabled_list) == 1:
                note += "feature is "
            else:
                note += "features are "
            note += "turned off."
        else:
            note = ""

        # EDIT IN DATABASE
        cur.execute("UPDATE serversettings SET details = ? WHERE name = ?", (text, "turing ban message"))
        con.commit()
        await util.changetimeupdate()

        # RESPONSE
        if len(args) == 0:
            await ctx.send(f"Disabled turing ban message, set to none.")
        else:
            await ctx.send(f"Done.{note}\n\n`DM PREVIEW:`")

            # PREVIEW
            message = util.customtextparse(text, user_id)
            embed=discord.Embed(title="", description=message, color=0xB80F0A)
            await ctx.send(embed=embed)

    @_set_turingbantext.error
    async def set_turingbantext_error(self, ctx, error):
        await util.error_handling(ctx, error)







    #########################################################################################################################################
    #########################################################################################################################################
    #########################################################################################################################################
    #########################################################################################################################################
    #########################################################################################################################################
    #########################################################################################################################################
    #########################################################################################################################################
    #########################################################################################################################################
    #########################################################################################################################################
    #########################################################################################################################################
    #########################################################################################################################################
    #########################################################################################################################################
    #########################################################################################################################################

    # UPDATE AND SETUP 






    @commands.command(name="update", aliases = ["botupdate"], pass_context=True)
    @commands.has_permissions(manage_guild=True)
    async def _botupdate(self, ctx, *args):
        """Update bot

        Only needed when updating the version of the bot from GitHub.
        i.e. New features will be included in the databases and automatically turned "off". Without this errors might occur because the setting is missing entirely.
        """

        # FETCH SERVER ID FROM .ENV FILE AND RETURN IF NOT MAIN SERVER
        try:
            app_id = os.getenv("application_id")
            bot_instance = os.getenv("bot_instance")
            guild_id = int(os.getenv("guild_id"))
            bot_channel_id = int(os.getenv("bot_channel_id"))
        except:
            print("Error: .env file not set up correctly.")
            await ctx.send("Error: Environment file not set up correctly.")
            return

        if ctx.guild.id != guild_id:
            await ctx.send("This command is restricted for use in this application's main server.")
            return

        # CREATE ALL DATABASES AND TABLES
        # FILL WITH DEFAULT DATA IF EMPTY
        async with ctx.typing():

            await ctx.send(f"Starting update of MDM Bot (instance: {bot_instance})...")

            # ACTIVITY DB

            conA = sqlite3.connect(f'databases/activity.db')
            curA = conA.cursor()
            curA.execute('''CREATE TABLE IF NOT EXISTS activity (name text, value text)''')
            activity_list = [item[0] for item in curA.execute("SELECT value FROM activity WHERE name = ?", ("activity",)).fetchall()]
            if len(activity_list) == 0:
                curA.execute("INSERT INTO activity VALUES (?,?)", ("activity", "inactive"))
                conA.commit()
                print("Updated activity table")
            elif len(activity_list) > 1:
                print("Warning: Multiple activity entries in activity.db")

            # AFTERMOST CHANGE DB

            conL = sqlite3.connect(f'databases/aftermostchange.db')
            curL = conL.cursor()
            curL.execute('''CREATE TABLE IF NOT EXISTS lastchange (name text, value text, details text)''')
            changetime_list = [item[0] for item in curA.execute("SELECT value FROM activity WHERE name = ?", ("time",)).fetchall()]
            if len(changetime_list) == 0:
                utc_timestamp = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())
                try:
                    human_readable_time = str(datetime.datetime.utcfromtimestamp(utc_timestamp).strftime('%Y-%m-%d %H:%M:%S UTC'))
                except:
                    human_readable_time = "error"
                curL.execute("INSERT INTO lastchange VALUES (?,?,?)", ("time", str(utc_timestamp), human_readable_time))
                conL.commit()
                print("Updated aftermost change table")
            elif len(achangetime_list) > 1:
                print("Warning: Multiple time entries in aftermostchange.db")

            # BOTSETTINGS DB: BOTSETTINGS

            conB = sqlite3.connect(f'databases/botsettings.db')
            curB = conB.cursor()
            curB.execute('''CREATE TABLE IF NOT EXISTS botsettings (name text, value text, type text, details text)''')
            botsettings_status_list = [item[0] for item in curB.execute("SELECT value FROM botsettings WHERE name = ?", ("status",)).fetchall()]
            if len(botsettings_status_list) == 0:
                curB.execute("INSERT INTO botsettings VALUES (?, ?, ?, ?)", ("status", "", "n", ""))
                conB.commit()
                print("Updated botsettings table: status")
            elif len(botsettings_status_list) > 1:
                print("Warning: Multiple status entries in botsettings table (botsettings.db)")

            botsettings_mainserver_list = [item[0] for item in curB.execute("SELECT details FROM botsettings WHERE name = ?", ("main server id",)).fetchall()]
            if len(botsettings_mainserver_list) == 0:
                curB.execute("INSERT INTO botsettings VALUES (?, ?, ?, ?)", ("main server id", str(guild_id), "", ctx.guild.name))
                conB.commit()
                print("Updated botsettings table: main server")
            else:
                if len(botsettings_mainserver_list) > 1:
                    print("Warning: Multiple main server entries in botsettings table (botsettings.db)")
                old_server_name = botsettings_mainserver_list[0]
                if old_server_name != ctx.guild.name:
                    curB.execute("UPDATE botsettings SET details = ? WHERE name = ?", (ctx.guild.name, "main server id"))
                    conB.commit()
                    print("Updated server name")

            botsettings_appid_list = [item[0] for item in curB.execute("SELECT type FROM botsettings WHERE name = ? AND details = ?", ("app id", bot_instance)).fetchall()]            
            try:
                timezone = str(get_localzone())
                timenow_object = pytz.timezone(timezone)
            except Exception as e:
                print("Error while trying to fetch device timezone: ", e)
                timezone = 'error'
            if len(botsettings_appid_list) == 0:
                curB.execute("INSERT INTO botsettings VALUES (?, ?, ?, ?)", ("app id", app_id, timezone, bot_instance))
                conB.commit()
                print("Updated botsettings table: app instance")
            else:
                if len(botsettings_appid_list) > 1:
                    print(f"Warning: Multiple app instance {bot_instance} entries in botsettings table (botsettings.db)")
                old_timezone = botsettings_appid_list[0]
                if old_timezone != timezone and timezone != "error":
                    curB.execute("UPDATE botsettings SET type = ? WHERE name = ? AND details = ?", (timezone, "app id", bot_instance))
                    conB.commit()
                    print("Updated time zone")


            # BOTSETTINGS DB: MODERATORS

            curB.execute('''CREATE TABLE IF NOT EXISTS moderators (name text, userid text, details text)''')
            changed_something = False
            try:
                # FETCH ALL USERS WITH MANAGE_GUILD PERMS
                moderator_serverfetched_list = []
                moderator_ID_serverfetched_list = []
                moderation_bot_list = []
                for member in ctx.guild.members:
                    member_perms = [p for p in member.guild_permissions]
                    for p in member_perms:
                        if p[1] and p[0] == "manage_guild":
                            if not member.bot:
                                moderator_serverfetched_list.append(member)
                                moderator_ID_serverfetched_list.append(str(member.id))
                            else:
                                moderation_bot_list.append(member)
                # FETCH FROM MODERATOR DATABASE
                moderator_id_list = []
                mod_list = [[item[0],item[1]] for item in curB.execute("SELECT userid, details FROM moderators").fetchall()]
                # REMOVE OLD MODS
                if len(mod_list) == 0:
                    pass
                else:
                    for item in mod_list:
                        moderatorid = item[0]
                        modtype = item[1]
                        if modtype.lower() in ["dev", "owner"]: # devs and owner get always added
                            moderator_id_list.append(moderatorid)
                        else:
                            if moderatorid in moderator_ID_serverfetched_list: #other members will be checked for perms
                                moderator_id_list.append(moderatorid)
                            else:
                                # remove from list
                                curB.execute("DELETE FROM moderators WHERE userid = ?", (moderatorid,))
                                conB.commit()
                                changed_something = True
                # ADD NEW MODS
                for mod in moderator_serverfetched_list:
                    if str(mod.id) in moderator_id_list:
                        pass
                    else:
                        # add to list
                        curB.execute("INSERT INTO moderators VALUES (?, ?, ?)", (str(mod.name), str(mod.id), "mod"))
                        conB.commit()
                        changed_something = True
                if changed_something:
                    print("Updated moderator list.")
            except Exception as e:
                print("Error while handling moderators: ", e)


            # BOTSETTINGS DB: SERVERSETTINGS 

            curB.execute('''CREATE TABLE IF NOT EXISTS serversettings (name text, value text, details text, etc text)''')

            # channels

            botspamchannelid_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("botspam channel id",)).fetchall()]
            if len(botspamchannelid_list) == 0:
                botspamchannelid = os.getenv("bot_channel_id")
                curB.execute("INSERT INTO serversettings VALUES (?, ?, ?, ?)", ("botspam channel id", botspamchannelid, "", ""))
                conB.commit()
                print("Updated serversettings table: botspam channel id")
            elif len(botspamchannelid_list) > 1:
                print("Warning: Multiple botspam channel entries in serversettings table (botsettings.db)")

            accesswallchannelid_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("access wall channel id",)).fetchall()]
            if len(accesswallchannelid_list) == 0:
                curB.execute("INSERT INTO serversettings VALUES (?, ?, ?, ?)", ("access wall channel id", "none", "", ""))
                conB.commit()
                print("Added dummy entry for access wall channel id")
            elif len(accesswallchannelid_list) > 1:
                print("Warning: Multiple access wall channel id entries in serversettings table (botsettings.db)")

            generalchannelid_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("general channel id",)).fetchall()]
            if len(generalchannelid_list) == 0:
                curB.execute("INSERT INTO serversettings VALUES (?, ?, ?, ?)", ("general channel id", "none", "", ""))
                conB.commit()
                print("Added dummy entry for general channel id")
            elif len(generalchannelid_list) > 1:
                print("Warning: Multiple general channel id entries in serversettings table (botsettings.db)")

            rolechannelid_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("role channel id",)).fetchall()]
            if len(rolechannelid_list) == 0:
                curB.execute("INSERT INTO serversettings VALUES (?, ?, ?, ?)", ("role channel id", "none", "", ""))
                conB.commit()
                print("Added dummy entry for role channel id")
            elif len(rolechannelid_list) > 1:
                print("Warning: Multiple role channel id entries in serversettings table (botsettings.db)")

            ruleschannelid_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("rules channel id",)).fetchall()]
            if len(ruleschannelid_list) == 0:
                curB.execute("INSERT INTO serversettings VALUES (?, ?, ?, ?)", ("rules channel id", "none", "", ""))
                conB.commit()
                print("Added dummy entry for turing test channel id (rules channel id)")
            elif len(ruleschannelid_list) > 1:
                print("Warning: Multiple turing test channel id (rules channel id) entries in serversettings table (botsettings.db)")

            # on/off switches

            accesswall_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("access wall",)).fetchall()]
            if len(accesswall_list) == 0:
                curB.execute("INSERT INTO serversettings VALUES (?, ?, ?, ?)", ("access wall", "off", "", ""))
                conB.commit()
                print("Updated serversettings table: access wall")
            elif len(accesswall_list) > 1:
                print("Warning: Multiple access wall entries in serversettings table (botsettings.db)")

            welcomemessage_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("welcome message",)).fetchall()]
            if len(welcomemessage_list) == 0:
                curB.execute("INSERT INTO serversettings VALUES (?, ?, ?, ?)", ("welcome message", "off", "", ""))
                conB.commit()
                print("Updated serversettings table: welcome message")
            elif len(welcomemessage_list) > 1:
                print("Warning: Multiple welcome message entries in serversettings table (botsettings.db)")

            reactionroles_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("reaction roles",)).fetchall()]
            if len(reactionroles_list) == 0:
                curB.execute("INSERT INTO serversettings VALUES (?, ?, ?, ?)", ("reaction roles", "off", "by rank", ""))
                conB.commit()
                print("Updated serversettings table: reaction roles")
            elif len(reactionroles_list) > 1:
                print("Warning: Multiple reaction roles entries in serversettings table (botsettings.db)")

            botdisplay_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("bot display",)).fetchall()]
            if len(botdisplay_list) == 0:
                curB.execute("INSERT INTO serversettings VALUES (?, ?, ?, ?)", ("bot display", "off", "", ""))
                conB.commit()
                print("Updated serversettings table: bot display")
            elif len(botdisplay_list) > 1:
                print("Warning: Multiple bot display entries in serversettings table (botsettings.db)")

            timeoutsystem_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("timeout system",)).fetchall()]
            if len(timeoutsystem_list) == 0:
                curB.execute("INSERT INTO serversettings VALUES (?, ?, ?, ?)", ("timeout system", "off", "", ""))
                conB.commit()
                print("Updated serversettings table: timeout system")
            elif len(timeoutsystem_list) > 1:
                print("Warning: Multiple timeout system entries in serversettings table (botsettings.db)")

            turingtest_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("turing test",)).fetchall()]
            if len(turingtest_list) == 0:
                curB.execute("INSERT INTO serversettings VALUES (?, ?, ?, ?)", ("turing test", "off", "", ""))
                conB.commit()
                print("Updated serversettings table: turing test")
            elif len(turingtest_list) > 1:
                print("Warning: Multiple turing test entries in serversettings table (botsettings.db)")
            rulesfirstreact_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("rules first reaction",)).fetchall()]
            if len(rulesfirstreact_list) == 0:
                curB.execute("INSERT INTO serversettings VALUES (?, ?, ?, ?)", ("rules first reaction", "", "", ""))
                conB.commit()
                print("Created dummy entry for turing test 1st react (rules first reaction)")
            elif len(rulesfirstreact_list) > 1:
                print("Warning: Multiple turing test 1st react (rules first reaction) entries in serversettings table (botsettings.db)")
            turingbanmsg_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("turing ban message",)).fetchall()]
            if len(turingbanmsg_list) == 0:
                curB.execute("INSERT INTO serversettings VALUES (?, ?, ?, ?)", ("turing ban message", "off", "", ""))
                conB.commit()
                print("Updated serversettings table: turing ban msg entry")
            elif len(turingbanmsg_list) > 1:
                print("Warning: Multiple turing ban msg entries in serversettings table (botsettings.db)")

            automaticrole_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("automatic role",)).fetchall()]
            if len(automaticrole_list) == 0:
                curB.execute("INSERT INTO serversettings VALUES (?, ?, ?, ?)", ("automatic role", "off", "", ""))
                conB.commit()
                print("Updated serversettings table: automatic role")
            elif len(automaticrole_list) > 1:
                print("Warning: Multiple automatic role entries in serversettings table (botsettings.db)")

            genretagreminder_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("genre tag reminder",)).fetchall()]
            if len(genretagreminder_list) == 0:
                curB.execute("INSERT INTO serversettings VALUES (?, ?, ?, ?)", ("genre tag reminder", "off", "", ""))
                conB.commit()
                print("Updated serversettings table: genre tag reminder")
            else:
                if len(genretagreminder_list) > 1:
                    print("Warning: there are multiple genre tag reminder on/off entries in the database")

            pingterest_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("pingable interests functionality",)).fetchall()]
            if len(pingterest_list) == 0:
                curB.execute("INSERT INTO serversettings VALUES (?, ?, ?, ?)", ("pingable interests functionality", "on", "", ""))
                conB.commit()
                print("Updated serversettings table: pingable interests functionality")
            elif len(pingterest_list) > 1:
                print("Warning: Multiple pingable interests functionality entries in serversettings table (botsettings.db)")

            backlogfunctionality_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("backlog functionality",)).fetchall()]
            if len(backlogfunctionality_list) == 0:
                curB.execute("INSERT INTO serversettings VALUES (?, ?, ?, ?)", ("backlog functionality", "on", "", ""))
                conB.commit()
                print("Updated serversettings table: backlog feature")
            elif len(backlogfunctionality_list) > 1:
                print("Warning: Multiple backlog feature entries in serversettings table (botsettings.db)")

            penaltynotifier_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("user mute/ban/kick notification",)).fetchall()]
            if len(penaltynotifier_list) == 0:
                curB.execute("INSERT INTO serversettings VALUES (?, ?, ?, ?)", ("user mute/ban/kick notification", "on", "", ""))
                conB.commit()
                print("Updated serversettings table: penalty notifier (user mute/ban/kick notification)")
            elif len(penaltynotifier_list) > 1:
                print("Warning: Multiple penalty notifier (user mute/ban/kick notification) entries in serversettings table (botsettings.db)")

            reminderfeature_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("reminder functionality",)).fetchall()]
            if len(reminderfeature_list) == 0:
                curB.execute("INSERT INTO serversettings VALUES (?, ?, ?, ?)", ("reminder functionality", "on", "", ""))
                conB.commit()
                print("Updated serversettings table: reminder functionality")
            elif len(penaltynotifier_list) > 1:
                print("Warning: Multiple reminder functionality entries in serversettings table (botsettings.db)")

            # on/off notification

            createdeletechannelnotif_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("create/delete channel notification",)).fetchall()]
            if len(createdeletechannelnotif_list) == 0:
                curB.execute("INSERT INTO serversettings VALUES (?, ?, ?, ?)", ("create/delete channel notification", "off", "", ""))
                conB.commit()
                print("Updated serversettings table: create/delete channel notification")
            elif len(createdeletechannelnotif_list) > 1:
                print("Warning: Multiple create/delete channel notification entries in serversettings table (botsettings.db)")

            createdeleterolenotif_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("create/delete role notification",)).fetchall()]
            if len(createdeleterolenotif_list) == 0:
                curB.execute("INSERT INTO serversettings VALUES (?, ?, ?, ?)", ("create/delete role notification", "off", "", ""))
                conB.commit()
                print("Updated serversettings table: create/delete role notification")
            elif len(createdeleterolenotif_list) > 1:
                print("Warning: Multiple create/delete role notification entries in serversettings table (botsettings.db)")

            assignrolenotif_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("assign role notification",)).fetchall()]
            if len(assignrolenotif_list) == 0:
                curB.execute("INSERT INTO serversettings VALUES (?, ?, ?, ?)", ("assign role notification", "off", "", ""))
                conB.commit()
                print("Updated serversettings table: assign role notification")
            elif len(assignrolenotif_list) > 1:
                print("Warning: Multiple assign role notification entries in serversettings table (botsettings.db)")

            joinleaveVCnotif_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("join/leave voicechat notification",)).fetchall()]
            if len(joinleaveVCnotif_list) == 0:
                curB.execute("INSERT INTO serversettings VALUES (?, ?, ?, ?)", ("join/leave voicechat notification", "off", "", ""))
                conB.commit()
                print("Updated serversettings table: join/leave voicechat notification")
            elif len(joinleaveVCnotif_list) > 1:
                print("Warning: Multiple join/leave voicechat notification entries in serversettings table (botsettings.db)")

            joinleaveservernotif_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("join/leave server notification",)).fetchall()]
            if len(joinleaveservernotif_list) == 0:
                curB.execute("INSERT INTO serversettings VALUES (?, ?, ?, ?)", ("join/leave server notification", "off", "", ""))
                conB.commit()
                print("Updated serversettings table: join/leave server notification")
            elif len(joinleaveservernotif_list) > 1:
                print("Warning: Multiple join/leave server notification entries in serversettings table (botsettings.db)")

            editmessagenotif_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("edit message notification",)).fetchall()]
            if len(editmessagenotif_list) == 0:
                curB.execute("INSERT INTO serversettings VALUES (?, ?, ?, ?)", ("edit message notification", "off", "", ""))
                conB.commit()
                print("Updated serversettings table: edit message notification")
            elif len(editmessagenotif_list) > 1:
                print("Warning: Multiple edit message notification entries in serversettings table (botsettings.db)")

            createdeletethreadnotif_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("create/delete thread notification",)).fetchall()]
            if len(createdeletethreadnotif_list) == 0:
                curB.execute("INSERT INTO serversettings VALUES (?, ?, ?, ?)", ("create/delete thread notification", "off", "", ""))
                conB.commit()
                print("Updated serversettings table: create/delete thread notification")
            elif len(createdeletethreadnotif_list) > 1:
                print("Warning: Multiple create/delete thread notification entries in serversettings table (botsettings.db)")

            changeusernamenotif_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("user name change notification",)).fetchall()]
            if len(changeusernamenotif_list) == 0:
                curB.execute("INSERT INTO serversettings VALUES (?, ?, ?, ?)", ("user name change notification", "off", "", ""))
                conB.commit()
                print("Updated serversettings table: user name change notification")
            elif len(changeusernamenotif_list) > 1:
                print("Warning: Multiple user name change notification entries in serversettings table (botsettings.db)")

            scheduledeventnotif_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("scheduled event notification",)).fetchall()]
            if len(scheduledeventnotif_list) == 0:
                curB.execute("INSERT INTO serversettings VALUES (?, ?, ?, ?)", ("scheduled event notification", "off", "", ""))
                conB.commit()
                print("Updated serversettings table: scheduled event notification")
            elif len(scheduledeventnotif_list) > 1:
                print("Warning: Multiple scheduled event notification entries in serversettings table (botsettings.db)")

            invitecreationnotif_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("invite notification",)).fetchall()]
            if len(invitecreationnotif_list) == 0:
                curB.execute("INSERT INTO serversettings VALUES (?, ?, ?, ?)", ("invite notification", "off", "", ""))
                conB.commit()
                print("Updated serversettings table: invite notification")
            elif len(invitecreationnotif_list) > 1:
                print("Warning: Multiple invite notification entries in serversettings table (botsettings.db)")

            modsmodsmodsnotif_list = [item[0] for item in curB.execute("SELECT value FROM serversettings WHERE name = ?", ("mods mods mods notification",)).fetchall()]
            if len(modsmodsmodsnotif_list) == 0:
                curB.execute("INSERT INTO serversettings VALUES (?, ?, ?, ?)", ("mods mods mods notification", "off", "", ""))
                conB.commit()
                print("Updated serversettings table: mods mods mods notification")
            elif len(modsmodsmodsnotif_list) > 1:
                print("Warning: Multiple mods mods mods notification entries in serversettings table (botsettings.db)")


            # BOTSETTINGS DB: SPECIALROLES

            curB.execute('''CREATE TABLE IF NOT EXISTS specialroles (name text, role_id text, type text, details text)''')

            specialroles_accesswall_list = [item[0] for item in curB.execute("SELECT role_id FROM specialroles WHERE name = ?", ("access wall role",)).fetchall()]
            if len(specialroles_accesswall_list) == 0:
                curB.execute("INSERT INTO specialroles VALUES (?, ?, ?, ?)", ("access wall role", "", "", ""))
                conB.commit()
                print("Added dummy entry for access wall role")
            elif len(specialroles_accesswall_list) > 1:
                print("Warning: Multiple access wall role entries in specialroles table (botsettings.db)")

            specialroles_botdisplay_list = [item[0] for item in curB.execute("SELECT role_id FROM specialroles WHERE name = ?", ("bot display role",)).fetchall()]
            if len(specialroles_botdisplay_list) == 0:
                curB.execute("INSERT INTO specialroles VALUES (?, ?, ?, ?)", ("bot display role", "", "", ""))
                conB.commit()
                print("Added dummy entry for bot display role")
            elif len(specialroles_botdisplay_list) > 1:
                print("Warning: Multiple bot display role entries in specialroles table (botsettings.db)")

            specialroles_community_list = [item[0] for item in curB.execute("SELECT role_id FROM specialroles WHERE name = ?", ("community role",)).fetchall()]
            if len(specialroles_community_list) == 0:
                curB.execute("INSERT INTO specialroles VALUES (?, ?, ?, ?)", ("community role", "", "", ""))
                conB.commit()
                print("Added dummy entry for community role")
            elif len(specialroles_accesswall_list) > 1:
                print("Warning: Multiple community role entries in specialroles table (botsettings.db)")

            specialroles_timeout_list = [item[0] for item in curB.execute("SELECT role_id FROM specialroles WHERE name = ?", ("timeout role",)).fetchall()]
            if len(specialroles_timeout_list) == 0:
                curB.execute("INSERT INTO specialroles VALUES (?, ?, ?, ?)", ("timeout role", "", "", ""))
                conB.commit()
                print("Added dummy entry for timeout role")
            elif len(specialroles_timeout_list) > 1:
                print("Warning: Multiple timeout role entries in specialroles table (botsettings.db)")

            specialroles_verified_list = [item[0] for item in curB.execute("SELECT role_id FROM specialroles WHERE name = ?", ("verified role",)).fetchall()]
            if len(specialroles_verified_list) == 0:
                curB.execute("INSERT INTO specialroles VALUES (?, ?, ?, ?)", ("verified role", "", "", ""))
                conB.commit()
                print("Added dummy entry for verified role")
            elif len(specialroles_verified_list) > 1:
                print("Warning: Multiple verified role entries in specialroles table (botsettings.db)")


            # BOTSETTINGS DB: REACTIONROLESETTINGS

            curB.execute('''CREATE TABLE IF NOT EXISTS reactionrolesettings (name text, turn text, type text, msg_id text, rankorder text, embed_header text, embed_text text, embed_footer text, embed_color text)''')

            # BOTSETTINGS DB: EMOJI

            curB.execute('''CREATE TABLE IF NOT EXISTS emojis (purpose text, call text, extra text, alias text)''')

            conB = sqlite3.connect('databases/botsettings.db')
            curB = conB.cursor()
            botsettings_emoji = [item[0].strip() for item in curB.execute("SELECT purpose FROM emojis").fetchall()]

            default_emoji_dict = {
                            "attention" : "⚠️",
                            "awoken" : "🌞",
                            "aww" : "☺️",
                            "aww2" : "☺️",
                            "aww3" : "☺️",
                            "ban" : "🔨",
                            "bongo" : "🪘",
                            "bot" : "🤖",
                            "bouncy" : "⛹️",
                            "celebrate" : "🥳",
                            "cheer" : "😃",
                            "computer" : "💻",
                            "cover_eyes" : "🙈",
                            "cover_eyes2" : "🙈",
                            "cozy" : "😌",
                            "crown" : "👑",
                            "cry" : "😭",
                            "cry2" : "😭",
                            "dance" : "🕺",
                            "dance2" : "💃",
                            "derpy" : "🤪",
                            "derpy_playful" : "🤪",
                            "disappointed" : "😞",
                            "excited" : "😁",
                            "excited_alot" : "😁",
                            "excited_face" : "😁",
                            "giggle" : "😆",
                            "grin" : "🙃",
                            "gun" : "🔫",
                            "hello" : "👋",
                            "hello2" : "👋",
                            "hello3" : "👋",
                            "hold_head" : "🙉",
                            "hmm" : "🤔",
                            "hmm2" : "🤔",
                            "load" : "⏳",
                            "lurk" : "👀",
                            "lurk2" : "👀",
                            "lurk3" : "👀",
                            "metal" : "🤘",
                            "morning" : "🌞",
                            "mute" : "🙊",
                            "nice" : "😀",
                            "no" : "🙅",
                            "note" : "📝",
                            "ohh" : "😮",
                            "pain" : "💀",
                            "panic" : "😱",
                            "pensive" : "😔",
                            "pensive2" : "😔",
                            "pleading" : "😴",
                            "pout" : "🙎",
                            "sad" : "😢",
                            "shaking" : "🫨",
                            "shrug" : "🤷",
                            "shy" : "🙈",
                            "sleep" : "😴",
                            "smug" : "👀",
                            "sob" : "😭",
                            "surprised" : "😮",
                            "surprised2" : "😮",
                            "think" : "🤔",
                            "think_hmm" : "🤔",
                            "think_sceptic" : "🤔",
                            "think_smug" : "🤔",
                            "thumb_up" : "👍",
                            "thumbs_up" : "👍",
                            "umm" : "😐",
                            "unleashed" : "🦖",
                            "unleashed_mild" : "🦕",
                            "upset" : "😾",
                            "welp" : "🙈",
                            "yay" : "😄",
                            "yay2" : "😄",
                            "yes" : "🙆",
                            "bye" : "👋",
                        }

            for moji_purpose in default_emoji_dict:
                if moji_purpose in botsettings_emoji:
                    pass
                else:
                    curB.execute("INSERT INTO emojis VALUES (?, ?, ?, ?)", (moji_purpose, "", default_emoji_dict[moji_purpose], ""))
                    conB.commit()
                    print(f"Added emoji for {moji_purpose} into database.")


            # TIMETABLES DB

            conT = sqlite3.connect(f'databases/timetables.db')
            curT = conT.cursor()
            curT.execute('''CREATE TABLE IF NOT EXISTS reminders (reminder_id text, username text, userid text, utc_timestamp text, remindertext text, channel text, channel_name text, og_message text, og_time text)''')
            curT.execute('''CREATE TABLE IF NOT EXISTS recurring (reminder_id text, username text, userid text, pinglist text, interval text, next_time text, remindertitle text, remindertext text, adaptivelink text, channel text, channel_name text, thumbnail text, emoji text)''')
            curT.execute('''CREATE TABLE IF NOT EXISTS timeout (username text, userid text, utc_timestamp text, role_id_list text)''')
            curT.execute('''CREATE TABLE IF NOT EXISTS zcounter (num text)''')

            # ROLES DB

            conR = sqlite3.connect(f'databases/roles.db')
            curR = conR.cursor()
            curR.execute('''CREATE TABLE IF NOT EXISTS roles (id text, name text, assignable text, category text, permissions text, color text, details text)''')
            await util.update_role_database(ctx) # update role database


            # BACKLOG/MEMO DB

            conM = sqlite3.connect('databases/memobacklog.db')
            curM = conM.cursor()
            curM.execute('''CREATE TABLE IF NOT EXISTS memobacklog (bgid text, userid text, username text, backlog text, details text)''')

            # PINGABLE INTERESTS

            conP = sqlite3.connect('databases/pingterest.db')
            curP = conP.cursor()                                                                                              
            curP.execute('''CREATE TABLE IF NOT EXISTS pingterests (pingterest text, userid text, username text, details text)''')

            # NOW PLAYING SETTINGS

            conNP = sqlite3.connect('databases/npsettings.db')
            curNP = conNP.cursor()
            curNP.execute('''CREATE TABLE IF NOT EXISTS npreactions (id text, name text, emoji1 text, emoji2 text, emoji3 text, emoji4 text, emoji5 text, details text)''')
            curNP.execute('''CREATE TABLE IF NOT EXISTS lastfm (id text, name text, lfm_name text, lfm_link text, details text)''')
            curNP.execute('''CREATE TABLE IF NOT EXISTS tagsettings (id text, name text, spotify_monthlylisteners text, spotify_genretags text, lastfm_listeners text, lastfm_total_artistplays text, lastfm_artistscrobbles text, lastfm_albumscrobbles text, lastfm_trackscrobbles text, lastfm_rank text, musicbrainz_tags text, musicbrainz_area text, musicbrainz_date text, rym_genretags text, rym_albumrating text)''')


            # COOLDOWNS i.e. PREVENTIVE SELF RATE LIMITING

            conC = sqlite3.connect('databases/cooldowns.db')
            curC = conC.cursor()
            curC.execute('''CREATE TABLE IF NOT EXISTS cooldowns (service text, last_used text, limit_seconds text, limit_type text, long_limit_seconds text, long_limit_amount text)''') # soft limit type: delay, hard limit type: stop request

            cooldown_db_list = [item[0] for item in curC.execute("SELECT service FROM cooldowns").fetchall()]
            cooldowns = ["lastfm", "metallum", "musicbrainz", "openweathermap", "spotify"]
            cooldowns_crit = ["rym"]
            for cd in cooldowns:
                if cd not in cooldown_db_list:
                    curC.execute("INSERT INTO cooldowns VALUES (?, ?, ?, ?, ?, ?)", (cd, "0", "1", "soft", "20", "10"))
            for cd in cooldowns_crit:
                if cd not in cooldown_db_list:
                    curC.execute("INSERT INTO cooldowns VALUES (?, ?, ?, ?, ?, ?)", (cd, "0", "3", "hard", "30", "5"))
            conC.commit()

            curC.execute('''CREATE TABLE IF NOT EXISTS userrequests (service text, userid text, username text, time_stamp text)''')
            curC.execute("DELETE FROM userrequests")
            conC.commit()

            # Currency ExchangeRates

            conER = sqlite3.connect('databases/exchangerate.db')
            curER = conER.cursor()
            curER.execute('''CREATE TABLE IF NOT EXISTS USDexchangerate (code text, value text, currency text, country text, last_updated text, time_stamp text)''')
            try:
                response, success = await util.scrape_exchangerates()
            except Exception as e:
                print("Error while trying to get exchange rates via webscrape:", e)

            # SHENANIGANS

            conSH = sqlite3.connect('databases/shenanigans.db')
            curSH = conSH.cursor()
            curSH.execute('''CREATE TABLE IF NOT EXISTS sudo (sudo_id text, command text, response1 text, response2 text)''')
            curSH.execute('''CREATE TABLE IF NOT EXISTS inspire (quote_id text, quote text, author text, link text)''')
            curSH.execute('''CREATE TABLE IF NOT EXISTS mrec (mrec_id text, subcommand text, alias text, link text)''')

            # USER DATA

            conU = sqlite3.connect('databases/userdata.db')
            curU = conU.cursor()
            curU.execute('''CREATE TABLE IF NOT EXISTS location (user_id text, username text, city text, state text, country text, longitude text, latitude text)''')


            # search for other mdm bot instances and add them to app list in botsettings.db
            # under construction

            await util.changetimeupdate()

            version = util.get_version()
            await ctx.send(f"Updated to {version}.")
    @_botupdate.error
    async def botupdate_error(self, ctx, error):
        await util.error_handling(ctx, error)





    @commands.command(name="setup", aliases = ["botsetup"], pass_context=True)
    @commands.has_permissions(manage_guild=True)
    async def _botsetup(self, ctx, *args):
        """Set up bot

        For first-time setup of the bot,
        but also for re-setting up the bot.
        """

        # FETCH ACTIVITY AND RETURN IF NOT ACTIVE

        # CHECK MAIN SERVER

        conA = sqlite3.connect(f'../databases/activity.db')
        curA = conA.cursor()
        curA.execute('''CREATE TABLE IF NOT EXISTS activity (name text, value text)''')

        # CREATE ACTIVITY FILE IF NOT EXISTENT >> ACTIVITY
        # CREATE SERVERSETTINGS FILE IF NOT EXISTENT >> APP ID, BOTSPAM CHANNEL, MAIN SERVER FROM .ENV

        # FETCH SERVER ID FROM .ENV FILE AND RETURN IF NOT MAIN SERVER

        await ctx.send("under construction")







#####################################################################

async def setup(bot: commands.bot) -> None:
    await bot.add_cog(
        Administration_of_Settings(bot),
        guilds = [discord.Object(id = int(os.getenv("guild_id")))])