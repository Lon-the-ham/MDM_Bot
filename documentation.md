...documentation is under construction...


## Features that need API keys

Some features use external APIs and won't work or only partly if you don't create an account and put the api key you receive into the environment file. Don't worry, all APIs that are used here are free services.


### Algebaric Computation

To let users be able to use the `-calc` command and receive computation results you need to connect the bot to WolframAlpha. For that create an account on WolframAlpha and then get on https://developer.wolframalpha.com/access an App ID. Add that to your `.env` file as follows:

> wolframalpha_id = `app ID`

Note that the API has a monthly limit of 2000 queries.


### Currency Exchange Rate Conversion

With the `-con` command you can not only convert metres to miles or fahrenheit to celsius, but also different currencies using daily updated exchange rates. If you only stick to the few most prominent currencies in the world such as the US Dollar, Euro or Yen, then the implemented web scraper will probably suffice, but if you want to be able to convert all kinds of currencies you can get an api key for the ExchangeRate-API here: https://www.exchangerate-api.com/ 
Makre sure to add the key to your `.env` file as follows:

> exchangerate_key = `api key`


### Google Image Search

If you want to be able to search out image results via the google API with `-img`, you can head over to https://developers.google.com/custom-search/v1/overview and get an API key for that. Then continue to https://programmablesearchengine.google.com/u/1/controlpanel/all , create a search engine, enable "image search", "search the entire web" and perhaps also "safe search", and get the ID. Then add key and ID to your `.env` file as follows

> google_search_key = `api key`

> google_search_engine_id = `search engine ID`

Keep in mind that there is a daily limit of 100 queries. 


### LastFM

To fetch information from people's last.fm via `-fm` or `-fmx` you don't necessarily need the API, because the bot has an integrated web scrape, that may be a bit slower but is still able to fetch information. To fully use it's potential (also in terms of fetching tags), use `-fakenowplaying` or all kinds of stats commands regarding users scrobble data like `-whoknows`, you may want to create an last.fm API account here:

https://www.last.fm/api/account/create

You probably have to create a regular last.fm account first if you don't have one, and then create an API account within it. There you should receive an API key and a secret, as well as select a name for your application. Put these 4 things into the `.env` file as follows:

> lfm_app_name = `app name`

> lfm_api_key = `api key`

> lfm_shared_secret = `shared secret`

> lfm_registered_to = `your last.fm account name`

Optional:

Per default the scrobbling commands in this bot are disabled. When you enable them via `-set scrobbleautoupdate on` and let users import their scrobble data from lastfm you get comparably large databases on your device, which are often times too large for discord. Due to this backups of databases exclude these scrobble databases. In case you want to create regular backups of these as well go to https://www.dropbox.com/developers/apps?_tk=pilot_lp&_ad=topbar4&_camp=myapps and create a dropbox account as well as an application. Get `client id` and `client secret` and follow these instructions https://www.dropboxforum.com/t5/Dropbox-API-Support-Feedback/Get-refresh-token-from-access-token/td-p/596739 to get a `refresh token`. Then save these in the `.env`-file as follows:

> dropbox_key = `client id`

> dropbox_secret = `client secret`

> dropbox_refresh_token = `refresh token`

Optionally add

> encryption_key = `some random letters`

which will be used for encoding and decoding the tokens. Make sure it is long and doesn't contain words. If you don't add this, the bot will randomly generate a key, which is also fine, just ONLY IF YOU USE MULTIPLE INSTNACES make sure to manually add this generated key to the .env or the activity .db of the other instances.

Regardless of whether you added a dropbox connection, this bot will regularly make backups of all (non-scrobble) databases and send them as zip-file to your bot notification channel if you restart it via start_discordbot.sh. If you provide a dropbox token it will additionally also make backups of the scrobble databases and upload them to the cloud.


### MusicBrainz

It can be nice to have the bot fetch genre tags from the MusicBrainz database, if it doesn't find tags on last.fm etc. You do not need an API key for that, in fact the feature probably already works without anything. However the devs over at MusicBrainz ask users to provide a contact e-mail address when using their services. For this reason it is probably nice if you'd provide a contact e-mail as follows in your environment file:

> contact_email = `e-mail address`

The bot will then automatically include it in the header of an api inquiry.


### Spotify

To get use of Spotify's Rich Presence and display what you are currently listening to with `-np` (or `-sp`) you don't need an API key. However, if you also want the bot to display genre tags and the monthly listener count via `-npx` (or `-spx`) you need an account at Spotify for Developers.

Visit https://developer.spotify.com/documentation/web-api/tutorials/getting-started and create an app and request an access token. You should get a client ID and client secret. Add these 2 keys to your `.env` file as follows:

> Spotify_ClientID = `client ID`

> Spotify_ClientSecret = `client secret`

### Weather

With `-w` people can query the OpenWeatherMap API to get weather and temperature data of a given location. To enable this feature you need to head over to https://openweathermap.org/price#weather and select the free plan. The API key you receive then needs to be added to the environment file as follows:

> openweathermap_key = `api key`
