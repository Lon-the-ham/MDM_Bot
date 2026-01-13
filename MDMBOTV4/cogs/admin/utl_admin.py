import sqlite3



class AdministrationUtils():

    def get_instance_number(app_id) -> int:
        con = sqlite3.connect(f'databases/botsettings.db')
        cur = con.cursor()
        app_id = str(app_id)
        app_list = [item[0] for item in cur.execute("SELECT num FROM bot_settings WHERE name = ? AND value = ?", ("app id", app_id)).fetchall()]

        if len(app_list) > 0:
            if len(app_list) > 1:
                print(f"Warning: Multiple app numbers for application with id {app_id}.")
            return app_list[0]

        print(f"Error: No app with this id in database.")
        return None



    def get_version() -> str:
        con = sqlite3.connect(f'databases/0host.db')
        cur = con.cursor()
        version_list = [item[0] for item in cur.execute("SELECT value FROM meta WHERE name = ?", ("version",)).fetchall()]

        if len(version_list) == 0:
            version = "version ?"            
        else:
            version = version_list[0] 

        return version