import discord
import asyncio
import os
from os.path import dirname
import sys
import zipfile
from dotenv import load_dotenv
from datetime import datetime
import sqlite3
# cloud stuff
import contextlib
import six
import time
import unicodedata
import dropbox
import functools
import typing


load_dotenv()
app_id = os.getenv("application_id")
bot_instance = os.getenv("bot_instance")
discord_token = os.getenv("discord_token")
prefix = os.getenv("prefix")
guild_id = int(os.getenv("guild_id"))
bot_channel_id = int(os.getenv("bot_channel_id"))



##### DISCORD BACKUP



async def sendit(string, d_client):
    await d_client.login(discord_token)
    channel = await d_client.fetch_channel(bot_channel_id)
    await channel.send(string)

    utc_time_stamp = int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds())
    timestring = f"<t:{utc_time_stamp}:F>"

    try:

        # FETCH APP 

        try:
            con = sqlite3.connect(f'databases/botsettings.db')
        except:
            con = sqlite3.connect(f'../databases/botsettings.db')
        cur = con.cursor()
        try:
            app_list = [item[0] for item in cur.execute("SELECT details FROM botsettings WHERE name = ? AND value = ?", ("app id", app_id)).fetchall()]
        except:
            print("No data to back up yet.")
            app_list = []

        if len(app_list) == 0:
            print("error: no app with this id in database")
        else:
            instance = app_list[0]
            date = datetime.today().strftime('%Y-%m-%d_%H-%M-%S')

            # COPY FILES

            try:
                zf = zipfile.ZipFile(f"temp/backup_{date}_{instance}.zip", "w")
            except:
                zf = zipfile.ZipFile(f"../temp/backup_{date}_{instance}.zip", "w")
            db_directory = f"{dirname(sys.path[0])}/databases"

            lastedited = 0
            lastchanged = 0
            for filename in os.listdir(db_directory):
                if str(filename).endswith(".db") or str(filename).endswith(".txt"): # skip .gitignore file
                    if ("activity.db" in str(filename)) or ("scrobbledata.db" in str(filename)) or ("scrobbledata_releasewise.db" in str(filename)) or ("scrobblestats.db" in str(filename)) or ("scrobblegenres.db" in str(filename)):
                        continue

                    zf.write(os.path.join(db_directory, filename), filename)

                    edittime = int(os.path.getmtime(os.path.join(db_directory, filename)))
                    if (edittime > lastedited) and ("activity.db" not in str(filename)) and ("scrobbledata.db" not in str(filename)) and ("scrobbledata_releasewise.db" not in str(filename)) and ("scrobblestats.db" not in str(filename)) and ("scrobblegenres.db" not in str(filename)):
                        lastedited = edittime
                    if str(filename) == "aftermostchange.db":
                        try:
                            try:
                                conL = sqlite3.connect(f'databases/aftermostchange.db')
                            except:
                                conL = sqlite3.connect(f'../databases/aftermostchange.db')
                            curL = conL.cursor()
                            lastchange_list = [item[0] for item in curL.execute("SELECT value FROM lastchange WHERE name = ?", ("time",)).fetchall()]
                            lastchanged = int(lastchange_list[-1])
                        except Exception as e:
                            print(f"Error while trying to read out aftermostchange.db: {e}")
            zf.close()


            # CHECK ACTIVITY

            try:
                conA = sqlite3.connect(f'databases/activity.db')
            except:
                conA = sqlite3.connect(f'../databases/activity.db')
            curA = conA.cursor()
            activity_list = [item[0] for item in curA.execute("SELECT value FROM activity WHERE name = ?", ("activity",)).fetchall()]
            last_activity = activity_list[0]
            if last_activity == "active":
                textmessage = f"`LAST ACTIVE`\nlast edited: <t:{lastedited}:f> i.e. <t:{lastedited}:R>"
            else:
                textmessage = f"last edited: <t:{lastedited}:f> i.e. <t:{lastedited}:R>"
            if lastchanged > 0:
                textmessage += f"\nlast changed: <t:{lastchanged}:f> i.e. <t:{lastchanged}:R>"
            else:
                textmessage += f"\n(no last change date found)"


            # SEND STUFF

            try:
                try:
                    await channel.send(textmessage, file=discord.File(rf"temp/backup_{date}_{instance}.zip"))
                except:
                    try:
                        await channel.send(textmessage, file=discord.File(rf"../temp/backup_{date}_{instance}.zip"))
                    except:
                        await channel.send(textmessage, file=discord.File(rf"{dirname(sys.path[0])}/temp/backup_{date}_{instance}.zip"))
            except Exception as e:
                print(f"Error while trying to send backup file: {e}")
            try:
                os.remove(f"temp/backup_{date}_{instance}.zip")
            except:
                os.remove(f"../temp/backup_{date}_{instance}.zip")

            # UPLOAD scrobble data to cloud
            try: # put delay per instance
                app_list = [item[0] for item in cur.execute("SELECT details FROM botsettings WHERE name = ? AND value = ?", ("app id", app_id)).fetchall()]
                instance = app_list[0]
                waitingtime = max(int(instance.strip()) - 1, 0) * 30
            except:
                waitingtime = random.randint(120, 210)
            try:
                print(f"waiting {waitingtime} seconds")
                await asyncio.sleep(waitingtime)
            except:
                pass
            await cloud_upload_scrobble_backup()

    except Exception as e:
        await channel.send(f"Error while trying to backup data.```{e}```")





##################################### ENCRYPTION




def encode(key, clear):
    enc = []
    for i in range(len(clear)):
        key_c = key[i % len(key)]
        enc_c = chr((ord(clear[i]) + ord(key_c)) % 256)
        enc.append(enc_c)
    return base64.urlsafe_b64encode("".join(enc).encode()).decode()

def decode(key, enc):
    dec = []
    enc = base64.urlsafe_b64decode(enc).decode()
    for i in range(len(enc)):
        key_c = key[i % len(key)]
        dec_c = chr((256 + ord(enc[i]) - ord(key_c)) % 256)
        dec.append(dec_c)
    return "".join(dec)

def get_random_string(length):
    characters = string.ascii_letters + string.digits + string.punctuation
    result_str = ''.join(random.choice(characters) for i in range(length))
    return result_str

def get_enc_key():
    key = os.getenv('encryption_key')

    if key is None:
        try:
            con = sqlite3.connect(f'databases/activity.db')
        except:
            con = sqlite3.connect(f'../databases/activity.db')
        cur = con.cursor()
        key_list = [item[0] for item in cur.execute("SELECT value FROM hostdata WHERE name = ?", ("encryption key",)).fetchall()]

        if len(key_list) > 0:
            key = key_list[0]
        else:
            i = random.randint(100, 200)
            key = Utils.get_random_string(i)
            cur.execute("INSERT INTO hostdata VALUES (?,?,?,?)", ("encryption key", key, "", ""))
            con.commit()

    return key





##################################### CLOUD FUNCTIONS




def dropbox_list_folder(dbx, folder, subfolder):
    """List a folder.

    Return a dict mapping unicode filenames to
    FileMetadata|FolderMetadata entries.
    """
    path = '/%s/%s' % (folder, subfolder.replace(os.path.sep, '/'))
    while '//' in path:
        path = path.replace('//', '/')
    path = path.rstrip('/')
    try:
        with stopwatch('list_folder'):
            res = dbx.files_list_folder(path)
    except dropbox.exceptions.ApiError as err:
        print('Folder listing failed for', path, '-- assumed empty:', err)
        return {}
    else:
        rv = {}
        for entry in res.entries:
            rv[entry.name] = entry
        return rv



def dropbox_download(dbx, folder, subfolder, name):
    """Download a file.

    Return the bytes of the file, or None if it doesn't exist.
    """
    path = '/%s/%s/%s' % (folder, subfolder.replace(os.path.sep, '/'), name)
    while '//' in path:
        path = path.replace('//', '/')
    with stopwatch('download'):
        try:
            md, res = dbx.files_download(path)
        except dropbox.exceptions.HttpError as err:
            print('*** HTTP error', err)
            return None
    data = res.content
    print(len(data), 'bytes; md:', md)
    return data



def dropbox_upload(dbx, fullname, folder, subfolder, name, overwrite=False):
    """Upload a file.

    Return the request response, or None in case of error.
    """
    path = '/%s/%s/%s' % (folder, subfolder.replace(os.path.sep, '/'), name)
    while '//' in path:
        path = path.replace('//', '/')
    mode = (dropbox.files.WriteMode.overwrite
            if overwrite
            else dropbox.files.WriteMode.add)
    mtime = os.path.getmtime(fullname)
    with open(fullname, 'rb') as f:
        data = f.read()
    with stopwatch('upload %d bytes' % len(data)):
        try:
            res = dbx.files_upload(data, path, mode, client_modified=datetime(*time.gmtime(mtime)[:6]), mute=True)
        except dropbox.exceptions.ApiError as err:
            print('*** API error', err)
            return None
    try:
        print('uploaded as', res.name.encode('utf-8'))
    except Exception as e:
        pass
    return res


@contextlib.contextmanager
def stopwatch(message):
    """Context manager to print how long a block of code took."""
    t0 = time.time()
    try:
        yield
    finally:
        t1 = time.time()
        print('Total elapsed time for %s: %.3f' % (message, t1 - t0))



async def cloud_upload_scrobble_backup():
    # ZIP ALL DATABASES
    try:
        con = sqlite3.connect(f'databases/botsettings.db')
        rootdir = f"{sys.path[0]}/databases"
    except:
        con = sqlite3.connect(f'../databases/botsettings.db')
        rootdir = f"{str(sys.path[0]).rsplit('/',1)[0]}/databases"
    cur = con.cursor()
    app_list = [item[0] for item in cur.execute("SELECT details FROM botsettings WHERE name = ? AND value = ?", ("app id", app_id)).fetchall()]
    try:
        instance = app_list[0]
    except:
        instance = f"unknown{app_id}"

    # FETCH DROPBOX AUTH INFO

    dropbox_key = os.getenv('dropbox_key')
    dropbox_secret = os.getenv('dropbox_secret')
    folder = f'backups_instance_{instance}'

    if (dropbox_key is None or dropbox_key == "") or (dropbox_secret is None or dropbox_secret == ""):
        scrobblefeature_list = [item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("scrobbling functionality",)).fetchall()]
        if len(scrobblefeature_list) == 0 or scrobblefeature_list[0] != "on":
            pass
        return

    # CHECKING IF FILES ARE CORRUPTED

    all_files_good = True

    for filename in ['scrobbledata.db', 'scrobbledata_releasewise.db', 'scrobblestats.db', 'scrobblegenres.db']:
        try:
            try:
                con = sqlite3.connect(f'databases/{filename}')
            except:
                con = sqlite3.connect(f'../databases/{filename}')
            cur = con.cursor()  
            table_list = [item[0] for item in cur.execute("SELECT name FROM sqlite_master WHERE type = ?", ("table",)).fetchall()]
            #print(table_list)
            try:
                for table in table_list:
                    cursor = con.execute(f'SELECT * FROM {table}')
                    column_names = list(map(lambda x: x[0], cursor.description))
                    #print(column_names)
                    try:
                        item_list = [item[0] for item in cur.execute(f"SELECT * FROM {table} ORDER BY {column_names[0]} ASC LIMIT 1").fetchall()]
                        #print(item_list)
                    except Exception as e:
                        print(f"Error with {filename} table {table} query:", e)
                        all_files_good = False
            except Exception as e:
                print(f"Error with {filename} table {table} structure:", e)
                all_files_good = False
        except Exception as e:
            print(f"Error with {filename}:", e)
            all_files_good = False

    if not all_files_good:
        return

    # CONNECT TO DROPBOX

    TOKEN, expiration_time = await get_temporary_dropbox_token(None, d_client)

    dbx = dropbox.Dropbox(TOKEN)

    # UPLOAD FILES

    for dn, dirs, files in os.walk(rootdir):
        subfolder = dn[len(rootdir):].strip(os.path.sep)
        listing = dropbox_list_folder(dbx, folder, subfolder)
        print('Descending into', subfolder, '...')

        # First do all the files.
        for name in files:
            if not (name.startswith('scrobble') and name.endswith('.db')):
                continue

            fullname = os.path.join(dn, name)
            try:
                if not isinstance(name, six.text_type):
                    name = name.decode('utf-8')
                nname = unicodedata.normalize('NFC', name)
            except:
                nname = name
            if name.startswith('.'):
                print('Skipping dot file:', name)
            elif name.startswith('@') or name.endswith('~'):
                print('Skipping temporary file:', name)
            elif name.endswith('.pyc') or name.endswith('.pyo'):
                print('Skipping generated file:', name)
            elif nname in listing:
                md = listing[nname]
                mtime = os.path.getmtime(fullname)
                mtime_dt = datetime(*time.gmtime(mtime)[:6])
                size = os.path.getsize(fullname)
                if (isinstance(md, dropbox.files.FileMetadata) and
                        mtime_dt == md.client_modified and size == md.size):
                    print(name, 'is already synced [stats match]')
                else:
                    #print(name, 'exists with different stats, downloading')
                    #res = dropbox_download(dbx, folder, subfolder, name)
                    #with open(fullname) as f:
                    #    data = f.read()
                    #if res == data:
                    #    print(name, 'is already synced [content match]')
                    #else:
                    #    print(name, 'has changed since last sync')
                    await dropbox_upload(dbx, fullname, folder, subfolder, name, overwrite=True)
            else:
                await dropbox_upload(dbx, fullname, folder, subfolder, name)

        # Then choose which subdirectories to traverse.
        keep = []
        for name in dirs:
            if name.startswith('.'):
                print('Skipping dot directory:', name)
            elif name.startswith('@') or name.endswith('~'):
                print('Skipping temporary directory:', name)
            elif name == '__pycache__':
                print('Skipping generated directory:', name)
            elif yesno('Descend into %s' % name, True, args):
                print('Keeping directory:', name)
                keep.append(name)
            else:
                print('OK, skipping directory:', name)
        dirs[:] = keep

    # CREATE TXT FILE WITH LATEST UPDATE DATE

    try:
        lasttime = last_scrobble_time_in_db()

        try:
            con = sqlite3.connect(f'databases/botsettings.db')
            newdir = f"{sys.path[0]}/temp"
        except:
            con = sqlite3.connect(f'../databases/botsettings.db')
            newdir = f"{str(sys.path[0]).rsplit('/',1)[0]}/temp"
        cur = con.cursor()  

        with open(f"{newdir}/time.txt", "w") as file:
            file.write(f"{lasttime}")
        try:
            # UPLOAD TXT FILE

            for dn, dirs, files in os.walk(newdir):
                subfolder = dn[len(newdir):].strip(os.path.sep)
                listing = dropbox_list_folder(dbx, folder, subfolder)

                for name in files:
                    if not name == f"time.txt":
                        continue

                    fullname = os.path.join(dn, name)
                    try:
                        if not isinstance(name, six.text_type):
                            name = name.decode('utf-8')
                        nname = unicodedata.normalize('NFC', name)
                    except:
                        nname = name
                    if name.startswith('.'):
                        print('Skipping dot file:', name)
                    elif name.startswith('@') or name.endswith('~'):
                        print('Skipping temporary file:', name)
                    elif name.endswith('.pyc') or name.endswith('.pyo'):
                        print('Skipping generated file:', name)
                    elif nname in listing:
                        md = listing[nname]
                        mtime = os.path.getmtime(fullname)
                        mtime_dt = datetime(*time.gmtime(mtime)[:6])
                        size = os.path.getsize(fullname)
                        if (isinstance(md, dropbox.files.FileMetadata) and
                                mtime_dt == md.client_modified and size == md.size):
                            print(name, 'is already synced [stats match]')
                        else:
                            dropbox_upload(dbx, fullname, folder, subfolder, name, overwrite=True)
                    else:
                        dropbox_upload(dbx, fullname, folder, subfolder, name)
        except Exception as e:
            print("Error while trying to save last time stamp in cloud:", e)

        os.remove(f"{newdir}/time.txt")
    except Exception as e:
        print("Error while trying to set last time stamp:", e)

    dbx.close()
    print("done")



def last_scrobble_time_in_db():
    lasttime = 0
    try:
        con = sqlite3.connect(f'databases/scrobbledata_releasewise.db')
    except:
        con = sqlite3.connect(f'../databases/scrobbledata_releasewise.db')
    cur = con.cursor()  
    table_list = [item[0] for item in cur.execute("SELECT name FROM sqlite_master WHERE type = ?", ("table",)).fetchall()]
    #print(table_list)
    for table in table_list:
        try:
            result = con.execute(f'SELECT MAX(last_time) FROM {table}')
            rtuple = result.fetchone()
            if int(rtuple[0]) > lasttime:
                lasttime = int(rtuple[0])
        except Exception as e:
            print(f"Skipping table {table}:", e)
            continue

    return lasttime



async def get_temporary_dropbox_token(ctx, bot):
    if ctx == None:
        try:
            try:
                con = sqlite3.connect(f'databases/botsettings.db')
            except:
                con = sqlite3.connect(f'../databases/botsettings.db')
            cur = con.cursor()
            botspamchannel_id = int([item[0] for item in cur.execute("SELECT value FROM serversettings WHERE name = ?", ("botspam channel id",)).fetchall()][0])
        except:
            print("Bot spam/notification channel ID in database is faulty.")
            try:
                botspamchannel_id = int(os.getenv("bot_channel_id"))
                if botspamchannel_id is None:
                    raise ValueError("No botspamchannel id provided in .env file")
            except Exception as e:
                print(f"Error in util.get_temporary_dropbox_token():", e)
                return
        try:
            channel = bot.get_channel(botspamchannel_id)
        except Exception as e:
            print("Error in util.get_temporary_dropbox_token():", e)
            return
    else:
        channel = ctx.channel

    try:
        con = sqlite3.connect(f'databases/activity.db')
    except:
        con = sqlite3.connect(f'../databases/activity.db')
    cur = con.cursor()
    token_list = [[item[0],item[1]] for item in cur.execute("SELECT value, details FROM hostdata WHERE name = ?", ("dropbox token",)).fetchall()]
    now = int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds())

    # first check database
    if len(token_list) > 0 and now < int(token_list[0][1]) - 120:
        temp_token = str(token_list[0][0]).strip()
        expiration_time = int(token_list[0][1])
        print("using token saved in database")

    else:
        # check botspam messages
        the_message = None
        found = False
        try:
            conB = sqlite3.connect(f'databases/botsettings.db')
        except:
            conB = sqlite3.connect(f'../databases/botsettings.db')
        curB = conB.cursor()
        app_id_list = [item[0] for item in curB.execute("SELECT value FROM botsettings WHERE name = ?", ("app id",)).fetchall()]

        async for msg in channel.history(limit=100):
            if "`token:`" in msg.content and str(msg.author.id) in app_id_list:
                try:
                    the_message = msg
                    found = True
                    break
                except Exception as e:
                    print(e)

        if found:
            try:
                encrypted_thingy = str(the_message.content).split('`token:` ')[1].split('\n`expires:`')[0]
                temp_token = decode(get_enc_key(), encrypted_thingy)
                expiration_time = int(the_message.content.split('\n`expires:` ')[1].strip())

                if now > int(expiration_time) - 120:
                    raise ValueError("old token")
                print("using token from discord share")

                could_parse_token = True
            except Exception as e:
                print("Issue:", e)
                could_parse_token = False
        
        if not could_parse_token:
            # receive new temporary token

            refresh_token = os.getenv('dropbox_refresh_token')
            client_id = os.getenv('dropbox_key')
            client_secret = os.getenv('dropbox_secret')

            url = f"https://api.dropbox.com/oauth2/token"
            payload = {
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token',
                'client_id': client_id,
                'client_secret': client_secret,
            }
            response = requests.post(url, data=payload)

            try:
                temp_token = response.json()['access_token']
            except:
                temp_token = str(response.text).split('"access_token": "',1)[1].split('", "',1)[0].strip()
            try:
                duration = int(response.json()['expires_in'])
            except:
                duration = int(str(response.text).split('"expires_in":',1)[1].split('}',1)[0].strip())

            encoded_key = encode(get_enc_key(), temp_token)
            expiration_time = now + duration
            print("using fresh token")

            await channel.send(f"`token:` {encoded_key}\n`expires:` {expiration_time}")

    if len(token_list) > 0:
        cur.execute("UPDATE hostdata SET value = ?, details = ? WHERE name = ?", (temp_token, str(expiration_time), "dropbox token"))
    else:
        cur.execute("INSERT INTO hostdata VALUES (?,?,?,?)", ("dropbox token", temp_token, str(expiration_time), ""))
    con.commit()

    return temp_token, expiration_time





##################################### START


# vvv 

d_client = discord.Client(intents = discord.Intents.all())

asyncio.run(sendit("`--rebooting.`", d_client))