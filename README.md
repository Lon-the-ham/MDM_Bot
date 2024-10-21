# MDM_Bot

This discord bot is meant for actively moderating one server and providing additional QoL features that you can also use on other servers. Host it on your own device or web service to have full control over your discord server moderation without having to rely on proprietary bots with undisclosed source code.

The main difference to other discord bots is that you can host multiple instances of this app on multiple devices and switch between them in case one instance/device has connection issues or breaks etc, but of course you can still use this bot just with one instance on one device like most other discord applications. For more information what's all possible with this bot read the documentation.md.

---

# How to setup this bot on your raspberry pi:

The description in the following assumes you use Ubuntu (or the Ubuntu console for Windows) on your PC. The steps should be the same on other terminals, but the commands might be called differently.

### First time pi installs:

After you had the raspberry pi imager configure the SD card and you successfully connected it to your wifi, ssh into your raspi and use the update commands to update your system and python to the latest version by using these commands in your console:

> sudo apt-get update
  
> sudo apt-get upgrade
  
> sudo apt install python3-pip

### Install other packages:

Next you need to install a few packages that the applications uses:

> pip install asyncio
  
> python3 -m pip install -U discord.py

> pip install python-dotenv
  
> pip install emoji==1.7
  
> python3 -m pip install requests

> pip install googletrans==3.1.0a0
  
> pip install spotipy
  
> pip install pytz

> pip install tzlocal==2.1

> pip install beautifulsoup4

> pip install pandas

> sudo apt-get install libopenblas-dev

These are optional (more information in the documentation.md):

> pip install asyncpraw

> pip install dropbox

> pip install langdetect

> sudo apt install font-manager

> sudo apt install ffmpeg

> pip install bar-chart-race


### Create a discord application

Visit https://discord.com/developers/applications and create an account for your application. Make sure to note down the `application ID` as well as the `token` somewhere, you will need them later. Also make sure to disable the check on "Public Bot", while enabling all "Privileged Gateway Intents", i.e. enable all 3: Presence Intent, Server Members Intent, Message Content Intent.

While you're on the developer portal you can also add your new bot to the servers you want to have it on. Make sure that the bot has all necessary permissions to be able to do what it needs to do (basically all permissions on the server you want it to moderate on, and standard read/write/react permissions on servers it's just for its QoL features). You CAN use this app JUST for its QoL features, but it still needs a place where you can set it up and configure it, so you'd need to designate some discord server as your main server anyway (possibly just a private one just for yourself) then. Note your main server's `server ID` down, as well as the `channel ID` for the channel the bot should send notifications to (or be configured in).

### Get the code onto your device

Download the latest release version of this bot and extract the files (while preserving the folder structure) into some directory of your choice on your raspberry pi, e.g. `home/bots/MDM_Bot/`. Now you need to create an environment file called `.env` (that's the entire name) in the same folder that contains `mdmbot.py` and `start_discordbot.sh`. And add the following 6 lines

> application_id = `application ID`
> 
> bot_instance = 1
> 
> discord_token = `token`
> 
> prefix = -
> 
> guild_id = `server ID`
> 
> bot_channel_id = `channel ID`

where you insert the IDs and the token you wrote down earlier. The prefix can be any command prefix of your choice, we personally use a hyphen. The bot_instance number is only really important if you want to host this on multiple devices, just choose "1" for the first device, "2" for the second (if there is one) and so on.

If everything is set in place changing directory (e.g. with `cd home/bots/MDM_Bot/`) to the folder containing `mdmbot.py` you should be able to start the bot locally by using the command

> python3 mdmbot.py

When the bot successfully logged in, it will send a message to the bot_channel you provided in the `.env` file.
(Use CTRL+C in your console to halt the script.)

### Let the device run the app automatically

The next step is to let your raspberry pi run the application on its own. For that you first need to change some permissions on the shell files, so change directory into the folder containing `mdmbot.py` and use 

> chmod +x start_discordbot.sh

and perhaps also 

> chmod +x stop_bot.sh

but that latter one is optional. Now test if the bot starts running if you use the command

> ./start_discordbot.sh

If this doesn't work you may need to run the command

> sed -i -e 's/\r$//' start_discordbot.sh

and also

> sed -i -e 's/\r$//' stop_bot.sh

Now you should be able to start the bot using the shell script.
Next we will set up a cronjob, basically a recurring task that the raspberry pi will do. For that use command

> sudo nano /etc/crontab

and it should open the crontab file. There you can write two lines at the bottom of the file

> 6  5    * * *   pi    /home/pi/bots/MDM_Bot/start_discordbot.sh
> 
> @reboot pi    sleep 10;  /home/pi/bots/MDM_Bot/start_discordbot.sh

Just make sure the path matches the path the file has in your case and replace the "pi" with whatever name you gave your device (per default it's usually "pi" though).

The first line will restart the bot every day at 5:06 AM (device's local time), and the second line will restart the bot when you start your device. You can ofc change the time it updates or even change it to "only restarting once a week" or something, but we recommend restarting the script every once in a while in case the device loses connection and is unable to reconnect afterwards or for whatever other issues may happen.

If all that is done you can un- and replug your device and the app should get going!

### Last steps

Now that your raspberry is setup successfully, the only remaining thing is to configure the application itself within discord. 

IMPORTANT: For anything to work first use command `-update` to let the app set up its databases. Otherwise the bot will run into issues trying to execute many of its commands. After that use `-switch 1` (or whatever number you gave it as bot_instance) to set it to active.

Then you can use `-setup` if you want to be guided through a few of the bigger moderation settings, or just use `-set` to see what kinds of settings you can adapt manually. The documentation.md may help you with all the feature this application provides and deciding which ones you want to enable/disable.

---

Note: We are updating this application every now and then, so if you want the new features and bug fixes you may want to update the .py files on your device every now and then as well. Just make sure to preserve the database folder containing all your server/user specific information and the `.env` file, everything else can then be replaced. After you've switched the files, you may need to run `-update` again on your main server.
