import os
import datetime
import sqlite3
import discord
import asyncio
import requests

import config.config as config


# create/connect to database

con = sqlite3.connect('../cogs/utility/currency/exchangerate.db')
cur = con.cursor()
cur.execute('''CREATE TABLE IF NOT EXISTS USDexchangerate (code text, value text, currency text, country text, last_updated text, time_stamp text)''')


# connecting to discord bot
async def sendit(title, msg):
    await client.login(discord_token)
    botspamchannel = await client.fetch_channel(416384984597790750) 
    embed=discord.Embed(title=title, description=msg, color=0x000000)
    await botspamchannel.send(embed=embed)

def send_discord(success, msg):
    print("Sending notifications to discord")
    if success:
        title = "Updated database"
    else:
        title = "Error"
    asyncio.run(sendit(title, msg))
    print("Done.")


# connecting to exchangerate api
def get_exchangerates():
    api_key = config.exchangerate_key
    url = f'https://v6.exchangerate-api.com/v6/{api_key}/latest/USD'

    response = requests.get(url)
    data = response.json()
    connectionresult = data["result"]

    errormessage = ""
    if connectionresult.lower() == "success":
        update_time = str(data['time_last_update_utc'])
        update_time_stamp = str(data['time_last_update_unix'])
        print(data['base_code'])

        rates = data['conversion_rates']
        keysList = list(rates.keys())

        known_currencies = [item[0] for item in cur.execute("SELECT code FROM USDexchangerate").fetchall()]

        try:
            for currency in keysList:
                exchange = rates[currency]
                if currency in known_currencies:
                    cur.execute("UPDATE USDexchangerate SET value = ?, last_updated = ?, time_stamp = ? WHERE code = ?", (exchange, update_time, update_time_stamp, currency))
                    con.commit()
                else:
                    names_and_countries = [["AED","UAE Dirham","United Arab Emirates"],["AFN","Afghan Afghani","Afghanistan"],["ALL","Albanian Lek","Albania"],["AMD","Armenian Dram","Armenia"],["ANG","Netherlands Antillian Guilder","Netherlands Antilles"],["AOA","Angolan Kwanza","Angola"],["ARS","Argentine Peso","Argentina"],["AUD","Australian Dollar","Australia"],["AWG","Aruban Florin","Aruba"],["AZN","Azerbaijani Manat","Azerbaijan"],["BAM","Bosnia and Herzegovina Mark","Bosnia and Herzegovina"],["BBD","Barbados Dollar","Barbados"],["BDT","Bangladeshi Taka","Bangladesh"],["BGN","Bulgarian Lev","Bulgaria"],["BHD","Bahraini Dinar","Bahrain"],["BIF","Burundian Franc","Burundi"],["BMD","Bermudian Dollar","Bermuda"],["BND","Brunei Dollar","Brunei"],["BOB","Bolivian Boliviano","Bolivia"],["BRL","Brazilian Real","Brazil"],["BSD","Bahamian Dollar","Bahamas"],["BTN","Bhutanese Ngultrum","Bhutan"],["BWP","Botswana Pula","Botswana"],["BYN","Belarusian Ruble","Belarus"],["BZD","Belize Dollar","Belize"],["CAD","Canadian Dollar","Canada"],["CDF","Congolese Franc","Democratic Republic of the Congo"],["CHF","Swiss Franc","Switzerland"],["CLP","Chilean Peso","Chile"],["CNY","Chinese Renminbi","China"],["COP","Colombian Peso","Colombia"],["CRC","Costa Rican Colon","Costa Rica"],["CUP","Cuban Peso","Cuba"],["CVE","Cape Verdean Escudo","Cape Verde"],["CZK","Czech Koruna","Czech Republic"],["DJF","Djiboutian Franc","Djibouti"],["DKK","Danish Krone","Denmark"],["DOP","Dominican Peso","Dominican Republic"],["DZD","Algerian Dinar","Algeria"],["EGP","Egyptian Pound","Egypt"],["ERN","Eritrean Nakfa","Eritrea"],["ETB","Ethiopian Birr","Ethiopia"],["EUR","Euro","European Union"],["FJD","Fiji Dollar","Fiji"],["FKP","Falkland Islands Pound","Falkland Islands"],["FOK","Faroese Króna","Faroe Islands"],["GBP","Pound Sterling","United Kingdom"],["GEL","Georgian Lari","Georgia"],["GGP","Guernsey Pound","Guernsey"],["GHS","Ghanaian Cedi","Ghana"],["GIP","Gibraltar Pound","Gibraltar"],["GMD","Gambian Dalasi","The Gambia"],["GNF","Guinean Franc","Guinea"],["GTQ","Guatemalan Quetzal","Guatemala"],["GYD","Guyanese Dollar","Guyana"],["HKD","Hong Kong Dollar","Hong Kong"],["HNL","Honduran Lempira","Honduras"],["HRK","Croatian Kuna","Croatia"],["HTG","Haitian Gourde","Haiti"],["HUF","Hungarian Forint","Hungary"],["IDR","Indonesian Rupiah","Indonesia"],["ILS","Israeli New Shekel","Israel"],["IMP","Manx Pound","Isle of Man"],["INR","Indian Rupee","India"],["IQD","Iraqi Dinar","Iraq"],["IRR","Iranian Rial","Iran"],["ISK","Icelandic Króna","Iceland"],["JEP","Jersey Pound","Jersey"],["JMD","Jamaican Dollar","Jamaica"],["JOD","Jordanian Dinar","Jordan"],["JPY","Japanese Yen","Japan"],["KES","Kenyan Shilling","Kenya"],["KGS","Kyrgyzstani Som","Kyrgyzstan"],["KHR","Cambodian Riel","Cambodia"],["KID","Kiribati Dollar","Kiribati"],["KMF","Comorian Franc","Comoros"],["KRW","South Korean Won","South Korea"],["KWD","Kuwaiti Dinar","Kuwait"],["KYD","Cayman Islands Dollar","Cayman Islands"],["KZT","Kazakhstani Tenge","Kazakhstan"],["LAK","Lao Kip","Laos"],["LBP","Lebanese Pound","Lebanon"],["LKR","Sri Lanka Rupee","Sri Lanka"],["LRD","Liberian Dollar","Liberia"],["LSL","Lesotho Loti","Lesotho"],["LYD","Libyan Dinar","Libya"],["MAD","Moroccan Dirham","Morocco"],["MDL","Moldovan Leu","Moldova"],["MGA","Malagasy Ariary","Madagascar"],["MKD","Macedonian Denar","North Macedonia"],["MMK","Burmese Kyat","Myanmar"],["MNT","Mongolian Tögrög","Mongolia"],["MOP","Macanese Pataca","Macau"],["MRU","Mauritanian Ouguiya","Mauritania"],["MUR","Mauritian Rupee","Mauritius"],["MVR","Maldivian Rufiyaa","Maldives"],["MWK","Malawian Kwacha","Malawi"],["MXN","Mexican Peso","Mexico"],["MYR","Malaysian Ringgit","Malaysia"],["MZN","Mozambican Metical","Mozambique"],["NAD","Namibian Dollar","Namibia"],["NGN","Nigerian Naira","Nigeria"],["NIO","Nicaraguan Córdoba","Nicaragua"],["NOK","Norwegian Krone","Norway"],["NPR","Nepalese Rupee","Nepal"],["NZD","New Zealand Dollar","New Zealand"],["OMR","Omani Rial","Oman"],["PAB","Panamanian Balboa","Panama"],["PEN","Peruvian Sol","Peru"],["PGK","Papua New Guinean Kina","Papua New Guinea"],["PHP","Philippine Peso","Philippines"],["PKR","Pakistani Rupee","Pakistan"],["PLN","Polish Złoty","Poland"],["PYG","Paraguayan Guaraní","Paraguay"],["QAR","Qatari Riyal","Qatar"],["RON","Romanian Leu","Romania"],["RSD","Serbian Dinar","Serbia"],["RUB","Russian Ruble","Russia"],["RWF","Rwandan Franc","Rwanda"],["SAR","Saudi Riyal","Saudi Arabia"],["SBD","Solomon Islands Dollar","Solomon Islands"],["SCR","Seychellois Rupee","Seychelles"],["SDG","Sudanese Pound","Sudan"],["SEK","Swedish Krona","Sweden"],["SGD","Singapore Dollar","Singapore"],["SHP","Saint Helena Pound","Saint Helena"],["SLL","Old Sierra Leonean Leone","Sierra Leone"],["SLE","Sierra Leonean Leone","Sierra Leone"],["SOS","Somali Shilling","Somalia"],["SRD","Surinamese Dollar","Suriname"],["SSP","South Sudanese Pound","South Sudan"],["STN","São Tomé and Príncipe Dobra","São Tomé and Príncipe"],["SYP","Syrian Pound","Syria"],["SZL","Eswatini Lilangeni","Eswatini"],["THB","Thai Baht","Thailand"],["TJS","Tajikistani Somoni","Tajikistan"],["TMT","Turkmenistan Manat","Turkmenistan"],["TND","Tunisian Dinar","Tunisia"],["TOP","Tongan Pa'anga","Tonga"],["TRY","Turkish Lira","Turkey"],["TTD","Trinidad and Tobago Dollar","Trinidad and Tobago"],["TVD","Tuvaluan Dollar","Tuvalu"],["TWD","New Taiwan Dollar","Taiwan"],["TZS","Tanzanian Shilling","Tanzania"],["UAH","Ukrainian Hryvnia","Ukraine"],["UGX","Ugandan Shilling","Uganda"],["USD","United States Dollar","United States"],["UYU","Uruguayan Peso","Uruguay"],["UZS","Uzbekistani So'm","Uzbekistan"],["VES","Venezuelan Bolívar Soberano","Venezuela"],["VND","Vietnamese Đồng","Vietnam"],["VUV","Vanuatu Vatu","Vanuatu"],["WST","Samoan Tālā","Samoa"],["XAF","Central African CFA Franc","CEMAC"],["XCD","East Caribbean Dollar","Organisation of Eastern Caribbean States"],["XDR","Special Drawing Rights","International Monetary Fund"],["XOF","West African CFA franc","CFA"],["XPF","CFP Franc","Collectivités d'Outre-Mer"],["YER","Yemeni Rial","Yemen"],["ZAR","South African Rand","South Africa"],["ZMW","Zambian Kwacha","Zambia"],["ZWL","Zimbabwean Dollar","Zimbabwe"]]
                    name = ""
                    country = ""
                    for item in names_and_countries:
                        if item[0].upper() == currency.upper():
                            name = item[1]
                            country = item[2]
                    cur.execute("INSERT INTO USDexchangerate VALUES (?, ?, ?, ?, ?, ?)", (currency, exchange, name, country, update_time, update_time_stamp))
                    con.commit()
            message = f"Updated currency exchange rates <:kowalskinotes:975580577963057202>.\nData from {update_time}."
        except Exception as e:
            print("An error occured.:")
            print(e)
            errormessage = "Error while inserting data into database.\n```" + str(e) + "```"        
    else:
        errormessage = "Error while fetching data from ExchangeRate-API."


    if errormessage == "":
        send_discord(True, message)
    else:
        send_discord(False, errormessage)




# vvv run code vvv

discord_token = config.discord_token
client = discord.Client(intents = discord.Intents.default())

get_exchangerates()
