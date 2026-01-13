import base64
import random
import string

class EncryptionUtils():

    #########################################################################################################
    ##                                    KEY GENERATION                                                   ##
    #########################################################################################################



    def generate_random_string(length):
        characters = string.ascii_letters + string.digits + string.punctuation
        result_str = ''.join(random.choice(characters) for i in range(length))
        return result_str



    def get_encryption_key():
        key = os.getenv('encryption_key')

        if key is None:
            con = sqlite3.connect(f'databases/host0.db')
            cur = con.cursor()
            key_list = [item[0] for item in cur.execute("SELECT value FROM settings WHERE name = ?", ("encryption key",)).fetchall()]

            if len(key_list) > 0:
                key = key_list[0]
            else:
                i = random.randint(128, 256)
                key = EncryptionUtils.generate_random_string(i)
                cur.execute("INSERT INTO settings VALUES (?,?,?,?)", ("encryption key", key, "", ""))
                con.commit()

        return key



    #########################################################################################################
    ##                                    VIGENERE CIPHER                                                  ##
    #########################################################################################################



    def simple_encode(key, clear):
        enc = []
        for i in range(len(clear)):
            key_c = key[i % len(key)]
            enc_c = chr((ord(clear[i]) + ord(key_c)) % 256)
            enc.append(enc_c)
        return base64.urlsafe_b64encode("".join(enc).encode()).decode()



    def simple_decode(key, enc):
        dec = []
        enc = base64.urlsafe_b64decode(enc).decode()
        for i in range(len(enc)):
            key_c = key[i % len(key)]
            dec_c = chr((256 + ord(enc[i]) - ord(key_c)) % 256)
            dec.append(dec_c)
        return "".join(dec)



    