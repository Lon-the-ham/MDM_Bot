import os
import sqlite3
import sys
import datetime
import zipfile
from   pathlib import Path
import time
#import shutil

backup   = True
wipe     = True
transfer = True

###### getting old databases ######
if transfer:
    conAc = sqlite3.connect('old_v3_databases/activity.db')
    curAc = conAc.cursor()
    conAf = sqlite3.connect('old_v3_databases/aftermostchange.db')
    curAf = conAf.cursor()
    conB = sqlite3.connect('old_v3_databases/botsettings.db')
    curB = conB.cursor()
    conC = sqlite3.connect('old_v3_databases/cooldowns.db')
    curC = conC.cursor()
    conE = sqlite3.connect('old_v3_databases/exchangerate.db')
    curE = conE.cursor()
    conM = sqlite3.connect('old_v3_databases/memobacklog.db')
    curM = conM.cursor()
    conN = sqlite3.connect('old_v3_databases/npsettings.db')
    curN = conN.cursor()
    conP = sqlite3.connect('old_v3_databases/pingterest.db')
    curP = conP.cursor()
    conRa = sqlite3.connect('old_v3_databases/robotactivity.db')
    curRa = conRa.cursor()
    conRo = sqlite3.connect('old_v3_databases/roles.db')
    curRo = conRo.cursor()
    conSd = sqlite3.connect('old_v3_databases/scrobbledata.db')
    curSd = conSd.cursor()
    conSm = sqlite3.connect('old_v3_databases/scrobblemeta.db')
    curSm = conSm.cursor()
    conSs = sqlite3.connect('old_v3_databases/scrobblestats.db')
    curSs = conSs.cursor()
    conSz = sqlite3.connect('old_v3_databases/shenanigans.db')
    curSz = conSz.cursor()
    conTt = sqlite3.connect('old_v3_databases/timetables.db')
    curTt = conTt.cursor()
    conUa = sqlite3.connect('old_v3_databases/useractivity.db')
    curUa = conUa.cursor()
    conUd = sqlite3.connect('old_v3_databases/userdata.db')
    curUd = conUd.cursor()

###### making backup ######

if backup:
    print("----BACKUP----\n(this can take a while depending on existing databases)")
    date = datetime.datetime.today().strftime('%Y-%m-%d_%H-%M-%S')
    src  = f"../databases"
    dst  = f"backup/databases_backup_{date}"
    #util_s.zip(src, dst)
    zf = zipfile.ZipFile("%s.zip" % (dst), "w", zipfile.ZIP_DEFLATED)
    abs_src = os.path.abspath(src)
    for dirname, subdirs, files in os.walk(src):
        for filename in files:
            print(f"Backing up {filename}")
            absname = os.path.abspath(os.path.join(dirname, filename))
            arcname = absname[len(abs_src) + 1:]
            #print('zipping %s as %s' % (os.path.join(dirname, filename), arcname))
            zf.write(absname, arcname)
    zf.close()
    print("----      ----")

if wipe:
    print("----WIPE----")
    #for file in os.listdir("../databases"):
    #    try:
    #        os.remove(os.path.join("../databases", file))
    #    except IsADirectoryError:
    #        pass
    def findNremove(path,pattern,maxdepth=2):
        cpath=path.count(os.sep)
        for r,d,f in os.walk(path):
            if r.count(os.sep) - cpath < maxdepth:
                for files in f:
                    if files.endswith(pattern):
                        try:
                            print("Removing %s" % (os.path.join(r,files)))
                            os.remove(os.path.join(r,files))
                        except Exception as e:
                            print(e)
                        else:
                            print("%s removed" % (os.path.join(r,files)))

    path=os.path.join("../databases")
    findNremove(path,".db")
    print("----    ----")

###### write new databases ######

if transfer:
    print("----TRANSFER----")
    # Print iterations progress
    def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
        """
        Call in a loop to create terminal progress bar
        @params:
            iteration   - Required  : current iteration (Int)
            total       - Required  : total iterations (Int)
            prefix      - Optional  : prefix string (Str)
            suffix      - Optional  : suffix string (Str)
            decimals    - Optional  : positive number of decimals in percent complete (Int)
            length      - Optional  : character length of bar (Int)
            fill        - Optional  : bar fill character (Str)
            printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
        """
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filledLength = int(length * iteration // total)
        bar = fill * filledLength + '-' * (length - filledLength)
        print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
        # Print New Line on Complete
        if iteration == total: 
            print()
    ############################################################################################################################################################
    # copy activity
    now  = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())
    date = datetime.datetime.today().strftime('%Y.%m.%d at %H:%M:%S')

    print("++++ Creating host data database")
    con0 = sqlite3.connect('../databases/0host.db') 
    cur0 = con0.cursor()

    activity_list      = [item[0] for item in curAc.execute("SELECT value FROM activity").fetchall()]
    hostdata_list      = [[item[0], item[1], item[2]+item[3]] for item in curAc.execute("SELECT name, value, details, etc FROM hostdata").fetchall()]
    version_list       = [item[1] for item in curAc.execute("SELECT name, value FROM version").fetchall()]
    lastchange_list    = [item[1] for item in curAf.execute("SELECT name, value, details FROM lastchange").fetchall()]

    if len(activity_list) > 0:
        active = activity_list[-1]
        if active == "inactive":
            active = "no"
        else:
            active = "yes"
    else:
        active = "no"

    if len(version_list) > 0:
        version = version_list[-1]
    else:
        version = "?"

    if len(lastchange_list) > 0:
        try:
            last_change = int(lastchange_list[-1])
        except:
            last_change = 0
    else:
        last_change = 0

    print("Transfering meta data")
    cur0.execute('''CREATE TABLE IF NOT EXISTS meta (name text, value text)''')
    cur0.execute("INSERT INTO meta VALUES (?, ?)", ("active",      active))
    cur0.execute("INSERT INTO meta VALUES (?, ?)", ("version",     version))

    for item in hostdata_list:
        if item[0] == "reboot time":
            item[0] = "time reboot"
        elif item[0] == "daily update time":
            item[0] = "time update"

    hostdata_list.append(["metallum scraping","off", ""])
    hostdata_list.append(["scrobbling","off", ""])

    hostdata_list.sort(key=lambda x: x[0])

    print("Transfering host settings")
    cur0.execute('''CREATE TABLE IF NOT EXISTS settings (name text, value text, details text)''')
    for item in hostdata_list:
        name    = item[0]
        value   = item[1]
        details = item[2]
        cur0.execute("INSERT INTO settings VALUES (?, ?, ?)", (name, value, details))

    con0.commit()

    ############################################################################################################################################################
    # combine botsettings->botsettings/emoji/mirrors, cooldowns->settings, robotactivity->gpt_setting, npsettings->unwanted_tags(_regex) || ignore aftermostchange
    lastedit_list    = [[item[0], item[1], item[2]] for item in curAf.execute("SELECT name, value, details FROM lastchange").fetchall()]
    botsettings_list = [[item[0], item[1], item[2], item[3]] for item in curB.execute("SELECT name, value, type, details FROM botsettings").fetchall()]
        #command restrictions weren't implemented yet
    emoji_list       = [[item[0], item[1], item[2], item[3]] for item in curB.execute("SELECT purpose, call, extra, alias FROM emojis").fetchall()]
    mirror_list      = [[item[0], item[1], item[2]] for item in curB.execute("SELECT service, url, priority FROM mirrors").fetchall()]
    
    cooldowns_list   = [[item[0], item[1], item[2], item[3], item[4], item[5]] for item in curC.execute("SELECT service, last_used, limit_seconds, limit_type, long_limit_seconds, long_limit_amount FROM cooldowns").fetchall()]
    gpt_list         = [[item[0], item[1], item[2], item[3]] for item in curRa.execute("SELECT type, content, details, etc FROM gpt_setting").fetchall()]

    unwanted_tags    = [[item[0], item[1]] for item in curN.execute("SELECT tagname, bantype FROM unwantedtags").fetchall()]
    unwanted_regex   = [[item[0], item[1]] for item in curN.execute("SELECT regex, id FROM unwantedtags_regex").fetchall()]

    guild_id   = 0
    guild_name = "main server"
    mainserver_id = 0

    print("++++ Creating bot settings database")
    con1 = sqlite3.connect('../databases/botsettings.db')
    cur1 = con1.cursor()

    print("Transfering bot settings")
    cur1.execute('''CREATE TABLE IF NOT EXISTS bot_settings (name text, num integer, value text, details text)''')
    for item in botsettings_list:
        name     = item[0]
        value    = item[1]
        details  = item[2]
        num      = None
        if name == "version":
            continue
        elif name == "main server id":
            name    = "server id"
            num     = 0
            details = item[3]
            guild_id   = value
            guild_name = details
            mainserver_id = value
        elif name == "app id":
            try:
                num = int(item[3])
            except:
                num = None
        cur1.execute("INSERT INTO bot_settings VALUES (?, ?, ?, ?)", (name, num, value, details))

    print("Transfering emoji")
    cur1.execute('''CREATE TABLE IF NOT EXISTS emoji (name text, value text, fallback text, alt_name text)''')
    emoji_list.append(["arrow_forward", "", "▶️", ""])
    emoji_list.append(["arrow_backward", "", "◀️", ""])
    emoji_list.append(["arrow_forward_double", "", "⏩", ""])
    emoji_list.append(["arrow_backward_double", "", "⏪", ""])
    emoji_list.append(["arrow_circle", "", "🔄", ""])
    emoji_list.sort(key=lambda x: x[0])
    for item in emoji_list:
        name     = item[0]
        value    = item[1]
        fallback = item[2]
        alt_name = item[3]
        if name.endswith("2") or name.endswith("3"):
            name = name[0:-1]
        elif name.startswith("excited"):
            name = "excited"
        elif name == "hold_head":
            name = "ohno"
        elif name == "no_stonks":
            name = "stonks_down"
        cur1.execute("INSERT INTO emoji VALUES (?, ?, ?, ?)", (name, value, fallback, alt_name))

    print("Transfering mirrors")
    cur1.execute('''CREATE TABLE IF NOT EXISTS mirrors (service text, url text, priority integer, details text)''')
    for item in mirror_list:
        name     = item[0]
        url      = item[1]
        try:
            priority = int(item[2])
        except:
            priority = -1
        details  = ""
        cur1.execute("INSERT INTO mirrors VALUES (?, ?, ?, ?)", (name, url, priority, details))

    print("Transfering cooldown settings")
    cur1.execute('''CREATE TABLE IF NOT EXISTS cooldown_settings (service text, cd_user integer, cd_mod_t4 integer, cd_mod_t3 integer, cd_mod_t2 integer, cd_mod_t1 integer, cd_type text, cd_bot integer, botwide_timeframe integer, botwide_amount_limit integer)''')
    for item in gpt_list:
        name     = item[0]
        value    = item[1]
        if name == "user cooldown":
            for c_item in cooldowns_list:
                if c_item[0] == "gpt":
                    c_item[2] = value
                    c_item[3] = "soft"
                    c_item[4] = value
                    c_item[5] = value
        elif name == "user cooldown mod exempt":
            pass
        else:
            pass
            #todo->add to botsettings db / EXTERNAL SERVICES TABLE?

    cooldowns_list.sort(key=lambda x: x[0])

    for item in cooldowns_list: # change to deciseconds
        service     = item[0]
        limit_type  = item[3]
        cd_bot      = 10
        try:
            limitamount = int(item[5])
        except:
            limitamount = 10
        try:
            cd_user = int(item[2]) * 10
        except:
            cd_user = 10
        try:
            timeframe = int(item[4]) * 10
        except:
            timeframe = cd_user
        cur1.execute("INSERT INTO cooldown_settings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (service, cd_user, cd_user, cd_user, 10, 10, limit_type, cd_bot, timeframe, limitamount))

    print("Writing permissions")
    cur1.execute('''CREATE TABLE IF NOT EXISTS permissions (perm text, user bool, mod_t4 bool, mod_t3 bool, mod_t2 bool, mod_t1 bool)''')
    perm_list = ["ban", "kick", "mute", "ban_immunity", "kick_immunity", "mute_immunity", "server_settings", "music_settings"]
    # editing botsettings requires to be a T1 mod of the main server or one of the hosts (todo: how to exchange that info automatically?)
    for perm in perm_list:
        p_u = False
        p_s = False # supporter? let's add that to protections in server_settings
        p_1 = True
        p_2 = True
        p_3 = True
        p_4 = True
        if perm in ["ban_immunity", "kick_immunity"]:
            p_s = True
        elif perm in ["kick"]:
            p_4 = False
        elif perm in ["ban"]:
            p_3 = False
            p_4 = False
        elif perm in ["server_settings"]:
            p_2 = False
            p_3 = False
            p_4 = False
        cur1.execute("INSERT INTO permissions VALUES (?, ?, ?, ?, ?, ?)", (perm, p_u, p_4, p_3, p_2, p_1))

    print("Transfering tag black list")
    cur1.execute('''CREATE TABLE IF NOT EXISTS unwanted_tags (string text, compare_type text, details text)''')
    unwanted_tags.sort(key=lambda x: x[0])
    unwanted_tags.sort(key=lambda x: x[1], reverse=True)
    for item in unwanted_tags:
        string = item[0]
        comptype = item[1]
        if comptype == "tag":
            comptype = "exact"
        elif comptype == "phrase":
            comptype = "included"
        cur1.execute("INSERT INTO unwanted_tags VALUES (?, ?, ?)", (string, comptype, f"v3->v4 conversion - {date}"))
    for item in unwanted_regex:
        string = item[0]
        cur1.execute("INSERT INTO unwanted_tags VALUES (?, ?, ?)", (string, "regex", f"v3->v4 conversion - {date}"))

    con1.commit()

    ############################################################################################################################################################
    def forceinteger(s):
        try:
            i = int(s)
        except:
            i = 0
        return i

    def forcedouble(s):
        try:
            d = float(s)
        except:
            d = 0.0
        return d

    def converthex(s):
        try:
            return int(s, 16)
        except:
            return 0

    # copy timetables
    print("++++ Creating time table database")
    recurring_list = [(item[0], item[1], forceinteger(item[2]), item[3], item[4], forceinteger(item[5]), item[6], item[7], item[8], forceinteger(guild_id), guild_name, forceinteger(item[9]), item[10], item[11], item[12]) for item in curTt.execute("SELECT reminder_id, username, userid, pinglist, interval, next_time, remindertitle, remindertext, adaptivelink, channel, channel_name, thumbnail, emoji FROM recurring").fetchall()]
    reminders_list = [(forceinteger(item[0]), item[1], forceinteger(item[2]), forceinteger(item[3]), item[4], forceinteger(guild_id), guild_name, forceinteger(item[5]), item[6], forceinteger(item[7]), forceinteger(item[8])) for item in curTt.execute("SELECT reminder_id, username, userid, utc_timestamp, remindertext, channel, channel_name, og_message, og_time FROM reminders").fetchall()]
    zcounter_list  = [item[0] for item in curTt.execute("SELECT num FROM zcounter").fetchall()]
    recurring_ids  = []
    conS = sqlite3.connect('../databases/schedule.db')
    curS = conS.cursor()
    print("Transfering recurring reminders")
    curS.execute('''CREATE TABLE IF NOT EXISTS recurring (reminder_id text, username text, user_id integer, pinglist text, interval text, next_time integer, remindertitle text, remindertext text, adaptivelink text, guild_id integer, guild_name text, channel_id integer, channel_name text, thumbnail text, emoji text)''')
    for item in recurring_list:
        recurring_ids.append(forceinteger(item[0].replace("R", "")))
        curS.execute("INSERT INTO recurring VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", item)
    print("Transfering one-time reminders")
    curS.execute('''CREATE TABLE IF NOT EXISTS reminders (reminder_id integer, username text, user_id integer, utc_timestamp integer, remindertext text, guild_id integer, guild_name text, channel_id integer, channel_name text, og_message_id integer, og_time integer)''')
    for item in reminders_list:
        curS.execute("INSERT INTO reminders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", item)
    print("Transfering markers")
    curS.execute('''CREATE TABLE IF NOT EXISTS taskmarker (type text, num integer)''')
    if len(recurring_list) > 0:
        curS.execute("INSERT INTO taskmarker VALUES (?, ?)", ("recurring", max(recurring_ids)+1))
    else:
        curS.execute("INSERT INTO taskmarker VALUES (?, ?)", ("recurring", 101))
    if len(zcounter_list) > 0:
        for item in zcounter_list:
            value = forceinteger(item)
            curS.execute("INSERT INTO taskmarker VALUES (?, ?)", ("reminders", value))
    else:
        curS.execute("INSERT INTO taskmarker VALUES (?, ?)", ("reminders", 101))
    conS.commit()

    ############################################################################################################################################################
    # combine cooldowns->last_used, robotactivity->raw_reaction_embed, useractivity, (robotactivity->gpt_usercooldown?), timetables->timeout
    print("++++ Creating cooldown and embed tracking database")
    conT = sqlite3.connect('../databases/tracking.db')
    curT = conT.cursor()

    gptcooldown_list  = [[item[0],item[1]] for item in curRa.execute("SELECT userid, last_time FROM gpt_usercooldown").fetchall()]
    timeout_list      = [[item[0],item[1],item[2],item[3]] for item in curTt.execute("SELECT username, userid, utc_timestamp, role_id_list FROM timeout").fetchall()]
    useractivity_list = [[item[0],item[1],item[2],item[3],item[4]] for item in curUa.execute("SELECT username, userid, last_active, join_time, previous_roles FROM useractivity").fetchall()]
    react_embed_list  = [[item[0],item[1],item[2],item[3],item[4],item[5],item[6],item[7],item[8]] for item in curRa.execute("SELECT embed_type, channel_name, guild_id, channel_id, message_id, app_id, called_by_id, called_by_name, utc_timestamp FROM raw_reaction_embeds").fetchall()]

    # tracking shall primarily occur within RAM
    print("Transfering cooldowns")
    curT.execute('''CREATE TABLE IF NOT EXISTS cooldowns (service text, user_id integer, utc_timestamp integer)''') # only for LONG cooldowns
    curT.execute('''CREATE TABLE IF NOT EXISTS pipes     (name text, user text, utc_timestamp integer, estimate integer)''') # scrobbleupdate

    for item in cooldowns_list:
        service   = item[0]
        last_used = forceinteger(item[1])
        curT.execute("INSERT INTO cooldowns VALUES (?, ?, ?)", (service, 0, last_used))
        # can be deleted later

    for item in gptcooldown_list:
        service   = "gpt"
        user_id   = forceinteger(item[0])
        last_used = forceinteger(item[1])
        curT.execute("INSERT INTO cooldowns VALUES (?, ?, ?)", (service, user_id, last_used))
        # can be deleted later

    print("Creating database change log")
    curT.execute('''CREATE TABLE IF NOT EXISTS last_changed (server_id integer, db_name text, utc_timestamp integer, time_string text)''')
    for db_name in ["botsettings", "info", "schedule", "tracking", "userdata"]:
        curT.execute("INSERT INTO last_changed VALUES (?, ?, ?, ?)", (0, db_name, now, date))

    # exclusion_status: inactive, timeout, access wall 
    print("Transfering exclusions")
    curT.execute('''CREATE TABLE IF NOT EXISTS users_excluded (status text, guild_id integer, guild_name text, user_id integer, user_name text, role_id_list text, utc_timestamp integer)''') 
    
    for item in timeout_list:
        status   = "timeout"
        username = item[0]
        user_id  = forceinteger(item[1])
        utc_time = forceinteger(item[2])
        role_id_list = item[3].replace("[","").replace("]","").replace(", ", ";")
        curT.execute("INSERT INTO users_excluded VALUES (?, ?, ?, ?, ?, ?, ?)", (status, guild_id, guild_name, user_id, username, role_id_list, utc_time))

    print("Transfering activities")
    curT.execute('''CREATE TABLE IF NOT EXISTS user_activity (guild_id integer, guild_name text, user_id integer, user_name text, last_active integer, join_time integer, previous_roles text)''') 
    for item in useractivity_list:
        username   = item[0]
        user_id    = forceinteger(item[1])
        lastactive = forceinteger(item[2])
        join_time  = forceinteger(item[3])
        previous_roles = item[4].replace(";;", ";")
        curT.execute("INSERT INTO user_activity VALUES (?, ?, ?, ?, ?, ?, ?)", (guild_id, guild_name, user_id, username, lastactive, join_time, role_id_list))

    print("Transfering raw reaction embeds")
    curT.execute('''CREATE TABLE IF NOT EXISTS reaction_embeds_multipage  (embed_type text, guild_id integer, channel_id integer, message_id integer, app_id integer, invoker_id integer, page integer, title text, url text, thumbnail text, color integer, content text, fields_titles text, fields_contents text, footer text, author_name text, author_url text, author_icon text, invoker_name text, guild_name text, channel_name text, utc_timestamp integer)''')
    curT.execute('''CREATE TABLE IF NOT EXISTS reaction_embeds_singlepage (embed_type text, guild_id integer, channel_id integer, message_id integer, app_id integer, invoker_id integer, invoker_name text, guild_name text, channel_name text, utc_timestamp integer)''') 
    for item in react_embed_list:
        embed_type     = item[0]
        channel_name   = item[1]
        server_id      = forceinteger(item[2])
        if server_id == forceinteger(guild_id): # guild_id == 0 <=> direct_message
            servername = guild_name
        else:
            servername = ""
        channel_id     = forceinteger(item[3])
        message_id     = forceinteger(item[4])
        app_id         = forceinteger(item[5])
        called_by_id   = forceinteger(item[6])
        called_by_name = item[7]
        utc_timestamp  = forceinteger(item[8])
        curT.execute("INSERT INTO reaction_embeds_singlepage VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (embed_type, server_id, channel_id, message_id, app_id, called_by_id, called_by_name, servername, channel_name, utc_timestamp))

    conT.commit()

    # combine userdata, npsettings->lastfm/npreactions/tagsettings, memobacklog
    print("++++ Creating user data database")
    conU = sqlite3.connect('../databases/userdata.db')
    curU = conU.cursor()

    locations_list   = [[item[0],item[1],item[2],item[3],item[4],item[5],item[6]] for item in curUd.execute("SELECT user_id, username, city, state, country, longitude, latitude FROM location").fetchall()]
    lastfm_list      = [[item[0],item[1],item[2],item[3]] for item in curN.execute("SELECT id, name, lfm_name, lfm_link FROM lastfm").fetchall()]
    tagsetting_list  = [[item[0],item[1],item[2],item[3],item[4],item[5],item[6],item[7],item[8],item[9],item[10],item[11],item[12],item[13],item[14],item[15],item[16]] for item in curN.execute("SELECT id, name, spotify_monthlylisteners, spotify_genretags, lastfm_listeners, lastfm_total_artistplays, lastfm_artistscrobbles, lastfm_albumscrobbles, lastfm_trackscrobbles, lastfm_rank, lastfm_tags, musicbrainz_tags, musicbrainz_area, musicbrainz_date, rym_genretags, rym_albumrating, redundancy_filter, crown FROM tagsettings").fetchall()]
    memobacklog_list = [[item[0],item[1],item[2],item[3],item[4]] for item in curM.execute("SELECT bgid, userid, username, backlog, details FROM memobacklog").fetchall()]

    print("Transfering locations")
    curU.execute('''CREATE TABLE IF NOT EXISTS location (user_id integer, username text, city text, state text, country text, zip_code text, longitude text, latitude text)''')
    for item in locations_list:
        user_id     = forceinteger(item[0])
        username    = item[1]
        city        = item[2]
        state       = item[3]
        country     = item[4]
        zip_code    = ""
        longitude   = item[5]
        latitude    = item[6]
        curU.execute("INSERT INTO location VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (user_id, username, city, state, country, zip_code, longitude, latitude))

    print("Transfering last.fm handles")
    curU.execute('''CREATE TABLE IF NOT EXISTS lastfm (user_id integer, username text, lfm_name text, lfm_link text, details text)''')
    for item in lastfm_list:
        user_id     = forceinteger(item[0])
        username    = item[1]
        lfm_name    = item[2]
        lfm_link    = item[3]
        details     = ""
        curU.execute("INSERT INTO lastfm VALUES (?, ?, ?, ?, ?)", (user_id, username, lfm_name, lfm_link, details))

    print("Rewriting tag settings")
    curU.execute('''CREATE TABLE IF NOT EXISTS tag_settings (user_id integer, username text, artist_scrobbles integer, album_scrobbles integer, track_scrobbles integer, server_rank integer, server_crown integer, server_artistplays integer, spotify_monthlylisteners integer, spotify_genretags integer, lastfm_listeners integer, lastfm_total_artistplays integer, lastfm_tags integer, musicbrainz_tags integer, musicbrainz_area integer, musicbrainz_date integer, rym_genretags integer, rym_area integer, rym_date integer, rym_releasetype integer, rym_average_rating integer, rym_individual_rating integer, redundancy_filter integer)''')
    for item in tagsetting_list:
        user_id                  = forceinteger(item[0])
        username                 = item[1].replace("\_","_")

        # 1: always on, 0: standard, -1: always off
        # 2 for tags: standard or as substitute
        artist_scrobbles         = 1
        album_scrobbles          = 1
        track_scrobbles          = 1
        server_rank              = 1
        server_crown             = 1
        server_artist_scrobbles  = -1

        # standard: only when -sp
        spotify_monthlylisteners = 0 
        spotify_genretags        = 0
        # standard: only when -fm
        lastfm_listeners         = 0
        lastfm_total_artistplays = 0
        lastfm_tags              = 2
        # standard: ?
        musicbrainz_tags         = 2
        musicbrainz_area         = -1
        musicbrainz_date         = -1
        # standard: ?
        rym_genretags            = 2
        rym_area                 = -1
        rym_date                 = -1
        rym_releasetype          = -1
        rym_average_rating      = -1
        rym_individual_rating    = -1
        # standard: ?
        redundancy_filter        = 1 
        curU.execute("INSERT INTO tag_settings VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (user_id, username, artist_scrobbles, album_scrobbles, track_scrobbles, server_rank, server_crown, server_artist_scrobbles, spotify_monthlylisteners, spotify_genretags, lastfm_listeners, lastfm_total_artistplays, lastfm_tags, musicbrainz_tags, musicbrainz_area, musicbrainz_date, rym_genretags, rym_area, rym_date, rym_releasetype, rym_average_rating, rym_individual_rating, redundancy_filter))
    
    print("Transfering memo/backlog")
    curU.execute('''CREATE TABLE IF NOT EXISTS memo (memo_id text, user_id integer, username text, content text, category text, utc_timestamp integer)''')
    for item in memobacklog_list:
        memo_id  = item[0]
        user_id  = forceinteger(item[1])
        username = item[2] 
        content  = item[3]
        category = item[4]
        try:
            utc_timestamp = int(memo_id.split("_")[0])
        except:
            utc_timestamp = now
        curU.execute("INSERT INTO memo VALUES (?,?,?,?,?,?)", (memo_id, user_id, username, content, category, utc_timestamp))

    conU.commit()

    # copy exchangerates
    print("++++ Creating info database")
    conI = sqlite3.connect('../databases/info.db')
    curI = conI.cursor()

    exchangerates_list = [[item[0],item[1],item[2],item[3],item[4],item[5]] for item in curE.execute("SELECT code, value, currency, country, last_updated, time_stamp FROM USDexchangerate").fetchall()]

    print("Transfering exchangerates")
    curI.execute('''CREATE TABLE IF NOT EXISTS exchangerates_USD (code text, value text, currency text, country text, last_updated text, utc_timestamp integer)''')
    for item in exchangerates_list:
        code          = item[0]
        value         = item[1]
        currency      = item[2]
        country       = item[3] 
        last_updated  = item[4] 
        timestamp     = forceinteger(item[5])
        curI.execute("INSERT INTO exchangerates_USD VALUES (?,?,?,?,?,?)", (code, value, currency, country, last_updated, timestamp))

    conI.commit()

    # copy scrobbledata
    print("++++ Creating raw scrobble database")
    Path(f"../databases/music").mkdir(parents=True, exist_ok=True)
    conRw = sqlite3.connect('../databases/music/rawdata.db')
    curRw = conRw.cursor()

    scrobble_data_raw = []
    curSd.execute("SELECT name FROM sqlite_master WHERE type='table';")
    for table in curSd.fetchall():
        lfm_name = table[0]
        userscrobbles = [[lfm_name,item[0],item[1],item[2],item[3],item[4]] for item in curSd.execute(f"SELECT id, artist_name, album_name, track_name, date_uts FROM [{lfm_name}]").fetchall()]
        scrobble_data_raw += userscrobbles
        if len(userscrobbles) > 0:
            print(f"Transfering scrobbles of {lfm_name}")
            curRw.execute(f'''CREATE TABLE IF NOT EXISTS [{lfm_name}] (idx integer, artist text, album text, track text, utc_time integer)''')
            for item in userscrobbles:
                index    = forceinteger(item[1])
                artist   = item[2] 
                album    = item[3]  
                track    = item[4]  
                utc_time = forceinteger(item[5])
                curRw.execute(f"INSERT INTO [{lfm_name}] VALUES (?,?,?,?,?)", (index, artist, album, track, utc_time))
    conRw.commit()

    # combine scrobblemeta, scrobblestats and <rym_scraping stuff> and <transformed raw stuff>
    albuminfo_list   = [[item[0],item[1],item[2],item[3],item[4],item[5],item[6]] for item in curSm.execute("SELECT artist, artist_filtername, album, album_filtername, tags, cover_url, last_update FROM albuminfo").fetchall()]
    artistinfo_list  = [[item[0],item[1],item[2],item[3],item[4],item[5],item[6],item[7]] for item in curSm.execute("SELECT artist, filtername, mbid, tags_lfm, spotify_id, thumbnail, tags_spotify, spotify_update FROM artistinfo").fetchall()]
    trackinfo_list   = []
    artistalias_list = [[item[0],item[1]] for item in curSm.execute("SELECT alias_name, artist_key FROM artist_aliases").fetchall()]
    artistmeta_list  = [[item[0],item[1],item[2],item[3]] for item in conSs.execute("SELECT artist, thumbnail, tags_lfm, last_update FROM artistinfo").fetchall()]

    print("++++ Creating scrobble database")
    conFm = sqlite3.connect('../databases/music/fm.db')
    curFm = conFm.cursor()
    curFm.execute('''CREATE TABLE IF NOT EXISTS info_artists  (artist_key text, ambiguity_id integer, lfm_tags  text, lfm_image text, lfm_listeners integer, lfm_plays integer, lfm_updated integer, mb_area text, mbid text, mb_updated integer, spotify_tags text, spotify_image text, spotify_followers integer, spotify_popularity integer, spotify_id text, spotify_updated text, spotify_monthly_listeners integer, spotify_ml_updated integer, rym_tags text, rym_area text, rym_id integer, rym_updated integer, artist_full text)''')
    curFm.execute('''CREATE TABLE IF NOT EXISTS info_releases (artist_key text, ambiguity_id integer, album_key text, album_extra text, lfm_listeners integer, lfm_plays integer, lfm_cover text, lfm_tags text, lfm_updated integer, mb_tags text, mb_year integer, mb_date integer, mbid text, mb_updated integer, spotify_release_type text, spotify_cover text, spotify_tags text, spotify_popularity integer, spotify_id text, spotify_updated integer, rym_release_type text, rym_cover text, rym_tags_1 text, rym_tags_2 text, rym_descriptors text, rym_year integer, rym_date integer, rym_image text, rym_avg_score text, rym_voters integer, rym_artist_id integer, rym_album_id integer, rym_updated integer, artist_full text, album_full text)''')
    curFm.execute('''CREATE TABLE IF NOT EXISTS info_tracks   (artist_key text, album_key text, track_key text, ambiguity_id integer, album_extra text, track_extra text, lfm_tags text, lfm_duration_sec integer, mbid text, mb_duration_sec integer, spotify_id text, spotify_popularity integer, spotify_duration_ms integer, rym_duration_sec integer, rym_avg_score text, rym_voters text, artist_full text, album_full text, track_full text)''')
    curFm.execute('''CREATE TABLE IF NOT EXISTS namealias_artists  (artist_alias text, artist_key text, ambiguity_id integer, details text, utc_timestamp integer)''')
    curFm.execute('''CREATE TABLE IF NOT EXISTS namealias_releases (artist_key text, ambiguity_id integer, album_alias text, album_key text, album_extra text, details text, utc_timestamp integer)''')
    curFm.execute('''CREATE TABLE IF NOT EXISTS scrobbles (lfm_name text, utc_time integer, artist_key text, album_key text, track_key text, ambiguity_id integer, album_extra text, track_extra text, artist_full text, album_full text, track_full text)''')
    
    print("Transfering artist aliases")
    for item in artistalias_list:
        artist_alias  = item[0]
        artist_key    = item[1]
        details       = "transfer v3->v4"
        utc_timestamp = now
        ambiguity_id  = 0
        curFm.execute("INSERT INTO namealias_artists VALUES (?,?,?,?,?)", (artist_alias, artist_key, ambiguity_id, details, utc_timestamp))
    conFm.commit()

    print("Creating album aliases")
    if True:
        artist_key    = "DEATH"
        album_alias   = "SOUNDOFPERSERVERENCE"
        album_key     = "SOUNDOFPERSEVERANCE"
        album_extra   = todo
        details       = "github"
        ambiguity_id  = 0
        utc_timestamp = 1767222000
        curFm.execute("INSERT INTO namealias_releases VALUES (?,?,?,?,?,?,?)", (artist_key, ambiguity_id, album_alias, album_key, album_extra, details, utc_timestamp))
    conFm.commit()

    def diacritic_uppercase_translation(old_string):
        diacritics = {
            ord("Æ"): "AE",
            ord("Ã"): "A",
            ord("Å"): "A",
            ord("Ā"): "A",
            ord("Ä"): "A",
            ord("Â"): "A",
            ord("À"): "A",
            ord("Á"): "A",
            ord("Å"): "A",
            ord("Ầ"): "A",
            ord("Ấ"): "A",
            ord("Ẫ"): "A",
            ord("Ẩ"): "A",
            ord("Ą"): "A",
            ord("Ç"): "C",
            ord("Č"): "C",
            ord("Ď"): "D",
            ord("Ė"): "E",
            ord("Ê"): "E",
            ord("Ë"): "E",
            ord("È"): "E",
            ord("É"): "E",
            ord("Ě"): "E",
            ord("Ē"): "E",
            ord("Ę"): "E",
            ord("Ğ"): "G",
            ord("Í"): "I",
            ord("İ"): "I",
            ord("Ï"): "I",
            ord("Î"): "I",
            ord("Ī"): "I",
            ord("Ł"): "L",
            ord("Ñ"): "N",
            ord("Ń"): "N",
            ord("Ň"): "N",
            ord("Ō"): "O",
            ord("Ø"): "O",
            ord("Õ"): "O",
            ord("Œ"): "OE",
            ord("Ó"): "O",
            ord("Ò"): "O",
            ord("Ô"): "O",
            ord("Ö"): "O",
            ord("Ř"): "R",
            ord("Š"): "S",
            ord("ẞ"): "SS",
            ord("Ś"): "S",
            ord("Š"): "S",
            ord("Ş"): "S",
            ord("Ť"): "T",
            ord("Ū"): "U",
            ord("Ù"): "U",
            ord("Ú"): "U",
            ord("Û"): "U",
            ord("Ü"): "U",
            ord("Ů"): "U",
            ord("Ý"): "Y",
            ord("Ÿ"): "Y",
            ord("Ž"): "Z",
        }
        new_string = old_string.translate(diacritics)

        return new_string

    def compactaliasconvert(input_string):
        alias_list = [item[0] for item in curFm.execute("SELECT artist_key FROM namealias_artists WHERE artist_alias = ?", (input_string,)).fetchall()]

        if len(alias_list) == 0:
            return input_string
        else:
            result_string = alias_list[-1]
            return result_string

    def compactaddendumfilter(input_string, *info):
        intermediate_string = input_string

        if len(info) > 0 :
            if info[0] == "artist":
                if input_string.endswith(" - Topic"):
                    intermediate_string = input_string.replace(" - Topic", "")
            elif info[0] == "album":
                if input_string.endswith(" - EP"):
                    intermediate_string = input_string.replace(" - EP", "")
                elif input_string.endswith(" - Reissue"):
                    intermediate_string = input_string.replace(" - Reissue", "")
                elif input_string.endswith(" - Remaster"):
                    intermediate_string = input_string.replace(" - Remaster", "")
                elif input_string.endswith(" - Remastered"):
                    intermediate_string = input_string.replace(" - Remastered", "")
                elif input_string.endswith(" - Re-Recorded"):
                    intermediate_string = input_string.replace(" - Re-Recorded", "")
                #elif input_string.endswith(" - Single"):
                #    intermediate_string = input_string.replace(" - Single", "")

                if " | Live in " in input_string and input_string.split(" | Live in ")[0] > 3:
                    intermediate_string = input_string.split(" | Live in ")[0]

        if "(" in intermediate_string and not intermediate_string.startswith("("):
            intermediate_string = intermediate_string.split("(",1)[0]
        if "[" in intermediate_string and not intermediate_string.startswith("["):
            intermediate_string = intermediate_string.split("[",1)[0]

        return intermediate_string

    def compactnamefilter(input_string, *info):
        # https://en.wikipedia.org/wiki/List_of_Latin-script_letters
        # get rid of bracket info
        if input_string is None or input_string == "":
            return ""

        edited_string = ""
        try:
            # upper case and remove brackets etc
            if len(info) > 0:
                edited_string = compactaddendumfilter(input_string, info[0]).upper()
            else:
                edited_string = input_string.upper()

            # replace & with AND
            if " & " in edited_string:
                edited_string = edited_string.replace(" & ", " AND ")

            # get rid of starting THE/A/AN
            if edited_string.startswith("THE "):
                if len(edited_string) > 4:
                    edited_string = edited_string[4:]
            elif edited_string.startswith("A "):
                if len(edited_string) > 2:
                    edited_string = edited_string[2:]
            elif edited_string.startswith("AN "):
                if len(edited_string) > 3:
                    edited_string = edited_string[3:]

            # get rid of non-alphanumeric
            filtered_string = ''.join([x for x in edited_string if x.isalnum()])

            if filtered_string == "":
                return edited_string
            else:
                edited_string = filtered_string

            # adapt accents
            edited_string = diacritic_uppercase_translation(edited_string)

            if len(info) > 1 and info[0] == "artist" and info[1] == "alias":
                edited_string = compactaliasconvert(edited_string)

            return edited_string

        except Exception as e:
            print(f"Error: {e}")
            return edited_string

    def getbracketinfo(input_string):
        found_bracket = False
        bracket_stuff = ""
        if len(input_string) > 0:
            for i in input_string[1:]:
                if i in ["(","[","{"]:
                    found_bracket = True
                if found_bracket:
                    bracket_stuff += i
        result = ''.join([e for e in bracket_stuff.strip() if e.isalpha() or e.isnumeric()])
        return result

    ########################################################################################

    #txt = "Combining last.fm and spoofy data"
    #empty = " " * len(txt)
    #print(f"{txt} - 0%")
    print("Combining last.fm and spoofy data")
    i = 0
    p = 1
    n = len(artistmeta_list)
    printProgressBar(0, n, prefix = 'Progress:', suffix = 'Complete', length = 50) ############# 1
    lfm_dict = {}
    for item in artistmeta_list:
        i += 1
        artist_full     = item[0]
        artist_key      = compactnamefilter(artist_full,"artist","alias")
        lfm_dict[artist_key] = (item[1], item[2], item[3])
        try:
            if (i/n > p/100):
                printProgressBar(i, n, prefix = 'Progress:', suffix = 'Complete', length = 50) # 2
                #print(f"{empty} - {p}%")
                p += 1
        except:
            pass
    printProgressBar(n, n, prefix = 'Progress:', suffix = 'Complete', length = 50) ############# 3
    #print(f"{empty} - 100%")

    checked_artists = {}
    i = 0
    p = 1
    n = len(artistinfo_list)
    #print("Transfering artist info - 0%")
    print("Transfering artist info")
    printProgressBar(0, n, prefix = 'Progress:', suffix = 'Complete', length = 50) ################# 1
    for item in artistinfo_list:
        i += 1
        artist_full     = item[0]
        artist_key      = compactnamefilter(artist_full,"artist","alias")
        ambiguity_id    = 0
        if artist_key in checked_artists:
            continue
        else:
            checked_artists[artist_key] = True
        lfm_tags        = item[3]
        lfm_listeners = None
        lfm_plays = None
        if artist_key in lfm_dict: # thumbnail, tags_lfm, last_update
            lfm_image = lfm_dict[artist_key][0]
            lfm_updated = forceinteger(lfm_dict[artist_key][2])
            if lfm_tags is None or str(lfm_tags).strip() == "":
                lfm_tags = lfm_dict[artist_key][1]
        else:
            lfm_image = None
            lfm_updated = None
        mb_area = None
        mbid            = item[2]
        mb_updated = None
        spotify_tags    = item[6]
        spotify_image   = item[5]
        spotify_followers = None
        spotify_popularity = None
        spotify_id      = item[4]
        spotify_updated = item[7]
        spotify_monthly_listeners = None
        spotify_ml_updated = None
        rym_tags = None
        rym_area = None
        rym_id = None
        rym_updated = None
        curFm.execute("INSERT INTO info_artists VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (artist_key, ambiguity_id, lfm_tags, lfm_image, lfm_listeners, lfm_plays, lfm_updated, mb_area, mbid, mb_updated, spotify_tags, spotify_image, spotify_followers, spotify_popularity, spotify_id, spotify_updated, spotify_monthly_listeners, spotify_ml_updated, rym_tags, rym_area, rym_id, rym_updated, artist_full))
        try:
            if (i/n > p/100):
                #print(f"                        - {p}%")
                printProgressBar(i, n, prefix = 'Progress:', suffix = 'Complete', length = 50) ##### 2
                p += 1
        except:
            pass
    conFm.commit()
    printProgressBar(n, n, prefix = 'Progress:', suffix = 'Complete', length = 50) ################# 3
    #print("                        - 100%")

    checked_albums = {}
    converted_albumentries = []
    i = 0
    p = 1
    n = len(albuminfo_list)
    #txt = "Converting album info"
    #empty = " " * len(txt)
    #print(f"{txt} - 0% (with {n} entries)")
    print("Converting album info")
    printProgressBar(0, n, prefix = 'Progress:', suffix = 'Complete', length = 50) ################# 1
    for item in albuminfo_list:
        i += 1
        artist_full  = item[0]
        album_full   = item[2]
        artist_key   = compactnamefilter(artist_full,"artist","alias")
        album_key    = compactnamefilter(album_full, "album")
        album_extra  = ""
        ambiguity_id = 0
        if " - " in album_full:
            temporary_string = album_full.split(" - ")[-1].strip().upper().strip()
            if temporary_string in ["EP", "REISSUE", "REMASTER", "REMASTERED", "RE-RECORDED"]:
                album_extra = [x for x in temporary_string if x.isalnum()]
            elif temporary_string.startswith(("LIVE IN ","REISSUE ","REMASTER ", "REMASTERED ", "RE-RECORDED ")):
                album_extra = [x for x in temporary_string if x.isalnum()]

        elif " | " in album_full:
            temporary_string = album_full.split(" | ")[-1].strip().upper().strip()
            if temporary_string in ["EP", "REISSUE", "REMASTER", "REMASTERED", "RE-RECORDED"]:
                album_extra = [x for x in temporary_string if x.isalnum()]
            elif temporary_string.startswith(("LIVE IN ","REISSUE ","REMASTER ", "REMASTERED ", "RE-RECORDED ")):
                album_extra = [x for x in temporary_string if x.isalnum()]

        if (artist_key, album_key, album_extra) in checked_albums:
            continue
        else:
            checked_artists[(artist_key, album_key, album_extra)] = True
        lfm_listeners = None
        lfm_plays = None
        lfm_cover   = item[5]
        lfm_tags    = item[4]
        lfm_updated = item[6]
        mb_tags = None
        mb_year = None
        mb_date = None
        mbid = None
        mb_updated = None
        spotify_release_type = None
        spotify_cover = None
        spotify_tags = None
        spotify_popularity = None
        spotify_id = None
        spotify_updated = None
        rym_release_type = None
        rym_cover = None
        rym_tags_1 = None
        rym_tags_2 = None
        rym_descriptors = None
        rym_year = None
        rym_date = None
        rym_image = None
        rym_avg_score = None
        rym_voters = None
        rym_artist_id = None
        rym_album_id = None
        rym_updated = None
        if album_extra != "" and (artist_key, album_key, "") not in checked_albums:
            converted_albumentries.append((artist_key, ambiguity_id, album_key, "", lfm_listeners, lfm_plays, lfm_cover, lfm_tags, lfm_updated, mb_tags, mb_year, mb_date, mbid, mb_updated, spotify_release_type, spotify_cover, spotify_tags, spotify_popularity, spotify_id, spotify_updated, rym_release_type, rym_cover, rym_tags_1, rym_tags_2, rym_descriptors, rym_year, rym_date, rym_image, rym_avg_score, rym_voters, rym_artist_id, rym_album_id, rym_updated, artist_full, album_full))
        converted_albumentries.append((artist_key, ambiguity_id, album_key, album_extra, lfm_listeners, lfm_plays, lfm_cover, lfm_tags, lfm_updated, mb_tags, mb_year, mb_date, mbid, mb_updated, spotify_release_type, spotify_cover, spotify_tags, spotify_popularity, spotify_id, spotify_updated, rym_release_type, rym_cover, rym_tags_1, rym_tags_2, rym_descriptors, rym_year, rym_date, rym_image, rym_avg_score, rym_voters, rym_artist_id, rym_album_id, rym_updated, artist_full, album_full))
        try:
            if (i/n > p/100):
                #print(f"{empty} - {p}%")
                printProgressBar(i, n, prefix = 'Progress:', suffix = 'Complete', length = 50) ##### 2
                p += 1
        except:
            pass
    #print(f"{empty} - 100%")
    printProgressBar(n, n, prefix = 'Progress:', suffix = 'Complete', length = 50)  ################ 3

    print("...sorting...")
    converted_albumentries.sort(key=lambda x: x[2])
    converted_albumentries.sort(key=lambda x: x[1])
    converted_albumentries.sort(key=lambda x: x[0])

    i = 0
    p = 1
    n = len(converted_albumentries)
    #txt = "Filling in album info"
    #empty = " " * len(txt)
    #print(f"{txt} - 0% (with {n} entries)")
    print("Filling in album info")
    printProgressBar(0, n, prefix = 'Progress:', suffix = 'Complete', length = 50)
    for item in converted_albumentries:
        i += 1
        curFm.execute("INSERT INTO info_releases VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", item)
        try:
            if (i/n > p/100):
                #print(f"{' '*len(txt)} - {p}%")
                printProgressBar(i, n, prefix = 'Progress:', suffix = 'Complete', length = 50)
                p += 1
        except:
            pass
    conFm.commit()
    printProgressBar(n, n, prefix = 'Progress:', suffix = 'Complete', length = 50)
    #print(f"{' '*len(txt)} - 100%")

    print("Write optimised scrobbles")
    i = 0
    p = 1
    n = len(scrobble_data_raw)
    printProgressBar(0, n, prefix = 'Progress:', suffix = 'Complete', length = 50)
    #txt = "Write optimised scrobbles"
    #empty = " " * len(txt)
    #print(f"{txt} - 0% (with {n} entries)")
    for item in scrobble_data_raw:
        i += 1
        lfm_name      = item[0]
        artist_full   = item[2] 
        album_full    = item[3]  
        track_full    = item[4]  
        utc_time      = forceinteger(item[5])

        artist_key    = compactnamefilter(artist_full,"artist","alias")
        album_key     = compactnamefilter(album_full, "album")
        track_key     = compactnamefilter(track_full, "track")
        album_extra   = getbracketinfo(album_full)
        track_extra   = getbracketinfo(track_full)
        ambiguity_id  = 0

        curFm.execute("INSERT INTO scrobbles VALUES (?,?,?,?,?,?,?,?,?,?,?)", (lfm_name, utc_time, artist_key, album_key, track_key, ambiguity_id, album_extra, track_extra, artist_full, album_full, track_full))
        
        try:
            if (i/n > p/100):
                #print(f"{empty} - {p}%")
                printProgressBar(i, n, prefix = 'Progress:', suffix = 'Complete', length = 50)
                p += 1
        except:
            pass
    conFm.commit()
    #print(f"{empty} - 100%")
    printProgressBar(n, n, prefix = 'Progress:', suffix = 'Complete', length = 50)

    ##########################################################################################################################################################
    ###### server-specific
    print("++++ Creating directories")
    servers = []
    curSs.execute("SELECT name FROM sqlite_master WHERE type='table';")
    for table in curSs.fetchall():
        if table[0].startswith("crowns_"):
            server_id = str(table[0]).replace("crowns_", "")
            crowns_artists = [item[0] for item in curSs.execute(f"SELECT artist FROM crowns_{server_id}").fetchall()]
            if len(crowns_artists) > 0:
                servers.append(server_id)
                Path(f"../databases/{server_id}").mkdir(parents=True, exist_ok=True)
    Path(f"../databases/{mainserver_id}").mkdir(parents=True, exist_ok=True)

    print("++++ Creating server specific databases")
    reactionrole_list   = [[item[0],item[1],item[2],item[3],item[4],item[5],item[6],item[7],item[8]] for item in curB.execute("SELECT name, turn, type, msg_id, rankorder, embed_header, embed_text, embed_footer, embed_color FROM reactionrolesettings").fetchall()]
    specialroles_list   = [[item[0],item[1]] for item in curB.execute("SELECT name, role_id FROM specialroles").fetchall()]
    roles_list          = [[item[0],item[1],item[2],item[3],item[4],item[5],item[6]] for item in curRo.execute("SELECT id, name, assignable, category, permissions, color, details FROM roles").fetchall()]
    protections_list    = [[item[0],item[1],item[2],item[3],item[4],item[5]] for item in curRo.execute("SELECT id_type, id, name, ban, kick, mute FROM protections").fetchall()]
    serversettings_list = [[item[0],item[1],item[2],item[3]] for item in curB.execute("SELECT name, value, details, etc FROM serversettings").fetchall()]

    # combine roles, shenanigans, botsettings->reactionrolesettings/serversettings/specialroles (deprecate command_restrictions, moderators?)
    conS = sqlite3.connect(f'../databases/{mainserver_id}/serversettings.db')
    curS = conS.cursor() # create table channels

    print("Copying roles")
    curS.execute('''CREATE TABLE IF NOT EXISTS roles (role_id integer, name text, assignable bool, color integer, category text, emoji text, permissions text)''')
    for item in roles_list:
        role_id     = forceinteger(item[0])
        name        = item[1]
        assignable  = (item[2].lower().strip() == "true")
        category    = item[3] 
        permissions = item[4] 
        color_str   = item[5].replace("#", "0x")
        color       = int(color_str, 16)
        emoji       = item[6]
        curS.execute("INSERT INTO roles VALUES (?,?,?,?,?,?,?)", (role_id, name, assignable, color, category, emoji, permissions))

    print("Transfering reaction role settings")
    curS.execute('''CREATE TABLE IF NOT EXISTS reaction_role_settings (role_category text, active bool, radiobutton bool, msg_id integer, embed_header text, embed_text text, embed_footer text, embed_color integer)''')
    for item in reactionrole_list:
        role_category = item[0]
        active        = (item[1].lower().strip() == "on")
        radiobutton   = (item[2].lower().strip() == "radiobutton")
        msg_id        = forceinteger(item[3])
        embed_header  = item[4]
        embed_text    = item[5]
        embed_footer  = item[6] 
        embed_color   = converthex(item[7].replace("#", "0x"))
        curS.execute("INSERT INTO reaction_role_settings VALUES (?,?,?,?,?,?,?,?)", (role_category, active, radiobutton, msg_id, embed_header, embed_text, embed_footer, embed_color))

    print("Transfering special roles")
    curS.execute('''CREATE TABLE IF NOT EXISTS special_roles (role_key text, role_id integer, role_name text)''')
    specialroles_list.sort(key=lambda x: x[0])
    specialroles_list += [["t1_moderator", -1],["t2_moderator", -1],["t3_moderator", -1],["t4_moderator", -1],["bot_admin", -1]]
    for item in specialroles_list:
        name    = item[0] #.replace("role", "").strip()
        role_id = forceinteger(item[1])
        if role_id == 0:
            role_id = -1
        role_name = ""
        curS.execute("INSERT INTO special_roles VALUES (?,?,?)", (name, role_id, role_name))

    print("Transfering ban/kick/mute protections")
    curS.execute('''CREATE TABLE IF NOT EXISTS protections (id_type text, name text, obj_id integer, ban integer, kick integer, mute integer)''')
    for item in protections_list:
        id_type = item[0]
        obj_id  = forceinteger(item[1])
        name    = item[2]
        enumdict = {"none": 0, "soft": 1, "hard": 2}
        ban     = enumdict[item[3]]
        kick    = enumdict[item[4]]
        mute    = enumdict[item[5]]
        curS.execute("INSERT INTO protections VALUES (?,?,?,?,?,?)", (id_type, name, obj_id, ban, kick, mute))

    curS.execute('''CREATE TABLE IF NOT EXISTS special_channels (channel_key text, channel_id integer, channel_name text)''')
    curS.execute('''CREATE TABLE IF NOT EXISTS notifications (name text, active bool, channel_id integer, channel_name text)''')
    curS.execute('''CREATE TABLE IF NOT EXISTS functionalities (name text, active bool, param_1 text, param_2 text)''')
    channels_list   = []
    notifications   = []
    functionalities = []
    turing_reaction = ""
    turing_msg_id   = ""

    print("Assorting server settings")
    for item in serversettings_list:
        name = item[0]
        val  = item[1]
        det  = item[2]
        etc  = item[3]
        if name.endswith("channel id"):
            if name.startswith("rules"):
                channel_key  = "turing channel"
            else:
                channel_key  = name.replace("channel id", "channel")
            channel_id   = forceinteger(val)
            channels_list.append([channel_key, channel_id])

        elif name.endswith("notification") or name.endswith("reporting"):
            notif_name = name.replace("notification", "")
            active     = (val.lower().strip() == "on")
            notifications.append([notif_name, active])

        else:
            if name == "rules first reaction":
                turing_reaction = val
            elif name == "rules message id":
                turing_msg_id = val
            else:
                functionalities.append(item)

    channels_list.sort(key=lambda x: x[0])
    notifications.sort(key=lambda x: x[0])
    functionalities.sort(key=lambda x: x[0])

    print("Transfering channel settings")
    for item in channels_list:
        curS.execute("INSERT INTO special_channels VALUES (?,?,?)", (item[0], item[1], ""))

    print("Transfering notification settings")
    for item in notifications:
        curS.execute("INSERT INTO notifications VALUES (?,?,?,?)", (item[0], item[1], 0, "default"))

    print("Transfering functionality settings")
    for item in functionalities:
        name   = item[0]
        active = (item[1] == "on")
        param1 = item[2]
        param2 = item[3]
        if name == "turing test":
            param1 = turing_reaction
            param2 = turing_msg_id
        curS.execute("INSERT INTO functionalities VALUES (?,?,?,?)", (name, active, param1, param2))

    conS.commit()

    # combine pingterest, crowns
    print("Transfering pingterests")
    conCm = sqlite3.connect(f'../databases/{mainserver_id}/community.db')
    curCm = conCm.cursor()
    curCm.execute('''CREATE TABLE IF NOT EXISTS pingterests (name text, user_id integer, username text, details text)''')
    pingterest_list = [[item[0],item[1],item[2],item[3]] for item in curP.execute("SELECT pingterest, userid, username, details FROM pingterests").fetchall()]
    pingterest_list.sort(key=lambda x: x[0])
    
    for item in pingterest_list:
        name     = item[0]
        user_id  = forceinteger(item[1])
        username = item[2]
        details  = item[3]
        curCm.execute("INSERT INTO pingterests VALUES (?,?,?,?)", (name, user_id, username, details))
    conCm.commit()
    conCm.close()

    print("Transfering shenanigans")
    conSh = sqlite3.connect(f'../databases/{mainserver_id}/shenanigans.db')
    curSh = conSh.cursor()
    curSh.execute('''CREATE TABLE IF NOT EXISTS custom  (custom_id integer, trigger_text text, trigger_type text, response text, response_type text)''')
    curSh.execute('''CREATE TABLE IF NOT EXISTS inspire (quote_id  integer, quote text, author text, link text)''')
    curSh.execute('''CREATE TABLE IF NOT EXISTS mrec    (mrec_id   integer, subcommand text, alias text, link text)''')
    curSh.execute('''CREATE TABLE IF NOT EXISTS sudo    (sudo_id   integer, command text, response1 text, response2 text)''')

    custom_shenanigan_list  = [(forceinteger(item[0]),item[1],item[2],item[3],item[4]) for item in curSz.execute("SELECT custom_id, trigger_text, trigger_type, response, response_type FROM custom").fetchall()]
    inspire_shenanigan_list = [(forceinteger(item[0]),item[1],item[2],item[3]) for item in curSz.execute("SELECT quote_id, quote, author, link FROM inspire").fetchall()]
    mrec_shenanigan_list    = [(forceinteger(item[0]),item[1],item[2],item[3]) for item in curSz.execute("SELECT mrec_id, subcommand, alias, link FROM mrec").fetchall()]
    sudo_shenanigan_list    = [(forceinteger(item[0]),item[1],item[2],item[3]) for item in curSz.execute("SELECT sudo_id, command, response1, response2 FROM sudo").fetchall()]

    for item in custom_shenanigan_list:
        curSh.execute("INSERT INTO custom VALUES (?,?,?,?,?)", item)

    for item in inspire_shenanigan_list:
        curSh.execute("INSERT INTO inspire VALUES (?,?,?,?)", item)

    for item in mrec_shenanigan_list:
        curSh.execute("INSERT INTO mrec VALUES (?,?,?,?)", item)

    for item in sudo_shenanigan_list:
        curSh.execute("INSERT INTO sudo VALUES (?,?,?,?)", item)

    conSh.commit()

    ######################################################################

    for db_name in ["community", "serversettings", "shenanigans"]:
        curT.execute("INSERT INTO last_changed VALUES (?, ?, ?, ?)", (mainserver_id, db_name, now, date))
    conT.commit()

    print("Transfering scrobble crowns")
    for server_id in servers:
        print(f"--server: {server_id}")
        tablename = f"crowns_{server_id}"
        conCm = sqlite3.connect(f'../databases/{server_id}/community.db')
        curCm = conCm.cursor()
        crowns_list = [[item[0],item[1],item[2],item[3]] for item in curSs.execute(f"SELECT artist, crown_holder, discord_name, playcount FROM {tablename}").fetchall()]
        curCm.execute('''CREATE TABLE IF NOT EXISTS scrobble_crowns (artist_full text, artist_key text, crown_holder text, discord_name text, playcount integer, details text)''')
        curCm.execute('''CREATE TABLE IF NOT EXISTS pingterests (name text, user_id integer, username text, details text)''')
        for item in crowns_list:
            artist_full  = item[0]
            artist_key   = compactnamefilter(artist_full,"artist","alias")
            crown_holder = item[1] 
            discord_name = item[2] 
            playcount    = forceinteger(item[3])
            details      = "transfer"
            curCm.execute("INSERT INTO scrobble_crowns VALUES (?,?,?,?,?,?)", (artist_full, artist_key, crown_holder, discord_name, playcount, details))
        conCm.commit()
        conCm.close()

        if server_id != mainserver_id:
            curT.execute("INSERT INTO last_changed VALUES (?, ?, ?, ?)", (server_id, "community", now, date))
            conT.commit()

    print("----      ----")

print("END.")
#########################