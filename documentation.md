...documentation is under construction...


## Features that need API keys

Some features use external APIs and won't work or only partly if you don't create an account and put the api key you receive into the environment file. Don't worry, all APIs that are used here are free services.


### Currency Exchange Rate Conversion

With the `-con` command you can not only convert metres to miles or fahrenheit to celsius, but also different currencies using daily updated exchange rates. If you only stick to the few most prominent currencies in the world such as the US Dollar, Euro or Yen, then the implemented web scraper will probably suffice, but if you want to be able to convert all kinds of currencies you can get an api key for the ExchangeRate-API here: https://www.exchangerate-api.com/ 
Makre sure to add the key to your `.env` file as follows:

> exchangerate_key = `api key`


### Google Image Search

If you want to be able to search out image results via the google API with `-img`, you can head over to https://developers.google.com/custom-search/v1/overview and get an API key for that. Then add that key to your `.env` file as follows

> google_search_key = `api key`

Just keep in mind that there is a daily limit of 100 queries. 


### LastFM

To fetch information from people's last.fm via `-fm` or `-fmx` you don't necessarily need the API, because the bot has an integrated web scrape, that may be a bit slower but is still able to fetch information. To fully use it's potential (also in terms of fetching tags) and also use `-fakenowplaying` and `-fnpx`, which are commands that search for a given "artist - track" and show it as if you were currently listening to it, you may want to create an last.fm API account here:

https://www.last.fm/api/account/create

You probably have to create a regular last.fm account first if you don't have one, and then create an API account within it. There you should receive an API key and a secret, as well as select a name for your application. Put these 4 things into the `.env` file as follows:

> lfm_app_name = `app name`

> lfm_api_key = `api key`

> lfm_shared_secret = `shared secret`

> lfm_registered_to = `your last.fm account name`

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