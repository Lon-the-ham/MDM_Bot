import asyncio
import os
import sqlite3

from pathlib import Path

from cogs.utils.utl_simple  import SimpleUtils  as utl_s



class GeneralUtils():



    #########################################################################################################
    ##                                       common def                                                    ##
    #########################################################################################################

    def colour(name: str) -> hex:
        colour_dict = {
            "black"     : 0x000000,
            "white"     : 0xFFFFFF,
        }

        return colour_dict.get(name, None)


    def create_serverspecific_mod_database(server_id: int) -> int:
        error_code = 0

        try:
            Path(f"../databases/{server_id}").mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"> error with folder for server {server_id}:", e)
            error_code += 1

        try:
            conS = sqlite3.connect(f'databases/{server_id}/serversettings.db')
            curS = conS.cursor()
            curS.execute('''CREATE TABLE IF NOT EXISTS functionalities        (name text, active bool, param_1 text, param_2 text)''')
            curS.execute('''CREATE TABLE IF NOT EXISTS notifications          (name text, active bool, channel_id integer, channel_name text)''')
            curS.execute('''CREATE TABLE IF NOT EXISTS protections            (id_type text, name text, obj_id integer, ban integer, kick integer, mute integer)''')
            curS.execute('''CREATE TABLE IF NOT EXISTS reaction_role_settings (role_category text, active bool, radiobutton bool, msg_id integer, embed_header text, embed_text text, embed_footer text, embed_color integer)''')
            curS.execute('''CREATE TABLE IF NOT EXISTS roles                  (role_id integer, name text, assignable bool, color integer, category text, emoji text, permissions text)''')
            curS.execute('''CREATE TABLE IF NOT EXISTS special_channels       (channel_key text, channel_id integer, channel_name text)''')
            curS.execute('''CREATE TABLE IF NOT EXISTS special_roles          (role_key text, role_id integer, role_name text)''')
        except Exception as e:
            print(f"> error with serversettings database for server {server_id}:", e)
            error_code += 2

        if error_code > 0:
            print(f"> Creation of server specific mod database (ID: {server_id}) returned with error code {error_code}")
        return error_code



    def create_serverspecific_qol_databases(server_id: int) -> int:
        error_code = 0

        try:
            Path(f"../databases/{server_id}").mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"> error with folder for server {server_id}:", e)
            error_code += 1

        try:
            conC = sqlite3.connect(f'databases/{server_id}/community.db')
            curC = conC.cursor()
            curC.execute('''CREATE TABLE IF NOT EXISTS pingterests     (name text, user_id integer, username text, details text)''')
            curC.execute('''CREATE TABLE IF NOT EXISTS scrobble_crowns (artist_full text, artist_key text, crown_holder text, discord_name text, playcount integer, details text)''')
        except Exception as e:
            print(f"> error with community database for server {server_id}:", e)
            error_code += 2

        try:
            conSh = sqlite3.connect(f'databases/{server_id}/shenanigans.db')
            curSh = conSh.cursor()
            curSh.execute('''CREATE TABLE IF NOT EXISTS custom  (custom_id integer, trigger_text text, trigger_type text, response text, response_type text)''')
            curSh.execute('''CREATE TABLE IF NOT EXISTS inspire (quote_id  integer, quote text, author text, link text)''')
            curSh.execute('''CREATE TABLE IF NOT EXISTS mrec    (mrec_id   integer, subcommand text, alias text, link text)''')
            curSh.execute('''CREATE TABLE IF NOT EXISTS sudo    (sudo_id   integer, command text, response1 text, response2 text)''')
        except Exception as e:
            print(f"> error with shenanigans database for server {server_id}:", e)
            error_code += 4

        if error_code > 0:
            print(f"> Creation of server specific QoL databases (ID: {server_id}) returned with error code {error_code}")
        return error_code



    def emoji(name: str) -> str:
        """find fitting emoji in database, otherwise return empty string"""
        try:
            con = sqlite3.connect(f'databases/botsettings.db')
            cur = con.cursor()
            emoji_list = [[item[0],item[1],item[2]] for item in cur.execute("SELECT name, value, fallback FROM emoji").fetchall()]

            # fetch emoji by name: if value is empty choose fallback
            emote = ""
            term = name.lower().strip()
            
            for item in emoji_list:
                if term == item[0]:
                    if item[1].strip() == "":
                        emote = item[2]
                    else:
                        emote = item[1]
                    break
            else:
                term = ''.join(e for e in name.strip().lower().replace(" ","_") if e.isalnum() or e == "_")
                for item in emoji_list:
                    if term == item[0]:
                        if item[1].strip() == "":
                            emote = item[2]
                        else:
                            emote = item[1]
                        break
                    else:
                        term = ''.join(e for e in name.strip().lower() if e.isalnum())
                        for item in emoji_list:
                            if term == item[0]:
                                if item[1].strip() == "":
                                    emote = item[2]
                                else:
                                    emote = item[1]
                                break
                            else:
                                emote = ""

            # if search was unsuccessful look for alias and choose one at random

            if emote == "":
                term = ''.join(e for e in name.strip().lower().replace(" ","_") if e.isalnum() or e == "_")
                alias_list = [[item[0],item[1]] for item in cur.execute("SELECT value, fallback FROM emoji WHERE LOWER(alt_name) = ?", (term,)).fetchall()]

                if len(alias_list) > 0:
                    first_choice_list = []
                    second_choice_list = []

                    for item in alias_list:
                        if item[0].strip() == "":
                            emoji = item[1].strip()
                            if emoji not in second_choice_list:
                                second_choice_list.append(emoji)
                        else:
                            emoji = item[0].strip()
                            if emoji not in first_choice_list:
                                first_choice_list.append(emoji)

                    if len(first_choice_list) > 0:
                        emote = random.choice(first_choice_list)

                    elif len(second_choice_list) > 0:
                        emote = random.choice(second_choice_list)

            if emote.strip() == "":                
                print(f"Notification: Emoji with name '{name}' returned an empty string.")

            return emote.strip()

        except Exception as e:
            print(f"Error: {e}\n[utlG emoji]")
            return ""
            


    def get_moderated_servers() -> list[int]:
        try:
            conB = sqlite3.connect('databases/botsettings.db')
            curB = conB.cursor()
            return [utl_s.force_integer(item[0]) for item in curB.execute("SELECT value FROM bot_settings WHERE name = ? ORDER BY num ASC", ("server id",)).fetchall()]
        
        except Exception as e:
            print(f"Error while trying to get all moderated servers from settings: {e}")
            result = []
            for dir_name in [name for name in os.listdir("./databases") if os.path.isdir(name)]:
                if utl_s.represents_integer(dir_name):
                    if os.path.isfile(f"./databases/{dir_name}/serversettings.db") and not os.path.isfile(f"./databases/{dir_name}/unmoderate.txt"):
                        # todo: check whether moderation wasn't removed later, perhaps a txt-file that's just called "unmoderate"
                        result.append(utl_s.force_integer(dir_name))
            return result



    def update_change_time(database_name: str) -> None:
        pass #todo



    





        
