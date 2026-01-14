from   datetime import datetime
import os
import sqlite3
import zipfile

class SimpleUtils():



    def force_integer(s) -> int:
        try:
            i = int(s)
        except:
            try:
                i = int(s.strip())
            except:
                i = 0
        return i



    def on_off_from_bool(b: bool) -> str:
        if b:
            return "on"
        return "off"



    def on_off_to_bool(s: str) -> bool:
        s2 = s.lower().strip()   
        if   s2 == "off":
            return False
        elif s2 == "on":
            return True
        else:
            if s2 in ["no", "false", "disabled"]:
                return False
            return True



    def represents_integer(s):
        """checks if string is integer or float ending with .0"""
        if s.startswith("-") or s.startswith("+"):
            s = s[1:]
        if s.endswith(".0"):
            s = s[:-2]

        if len(s) < 1:
            return False 

        is_int = True 
        for char in s:
            if char not in ["0","1","2","3","4","5","6","7","8","9"]:
                is_int = False
                break

        return is_int



    def utcnow() -> int:
        return round((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds(), 0)


    def utcnow_deciseconds() -> int:
        return round((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds() * 10, 0)


    def utcnow_string() -> str:
        return datetime.today().strftime('%Y-%m-%d %H:%M:%S')



    def zip(src, dst) -> None:
        zf = zipfile.ZipFile("%s.zip" % (dst), "w", zipfile.ZIP_DEFLATED)
        abs_src = os.path.abspath(src)
        for dirname, subdirs, files in os.walk(src):
            for filename in files:
                absname = os.path.abspath(os.path.join(dirname, filename))
                arcname = absname[len(abs_src) + 1:]
                #print('zipping %s as %s' % (os.path.join(dirname, filename), arcname))
                zf.write(absname, arcname)
        zf.close()