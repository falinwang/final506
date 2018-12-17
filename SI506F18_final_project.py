# SI506F18_final_project.py
# My project will focus on searching recent "concerts" in Detroit area with Ticketmaster and then list the 10 most recent songs of that artists who performance in the concerts with iTunes research API.

# import
import requests
import json
import csv

# Create a cache file to store json file
CACHE_FNAME = 'cache_cache_cache.json'


# params_unique_combination provided by class
def params_unique_combination(baseurl, params_d, private_keys=["apikey"]):
    alphabetized_keys = sorted(params_d.keys())
    res = []
    for k in alphabetized_keys:
        if k not in private_keys:
            res.append("{}-{}".format(k, params_d[k]))
    return baseurl + "_".join(res)

print("=============== Step 0 =================")

## Step 0:
## Read the Ticketmaster API documentation and decide what data I want to request

print("=============== Step 1 =================")

## Step 1:
## Create a class called "TicketmasterEvent" by investigating Ticketmaster data to store the specific data for later use
# The structrue of Ticketmaster API data :
#   event_diction = CACHE_DICTION[unique_ident]["_embedded"]["events"][0]
#       [0]~[4]: each event
#
#   self.artists = CACHE_DICTION[unique_ident]["_embedded"]["events"][0]["_embedded"]["attractions"][0]["name"]
#       format: "Amos Lee"
#   self.eventname = CACHE_DICTION[unique_ident]["_embedded"]["events"][0]["name"]
#       format: "Amos Lee"
#   self.date = CACHE_DICTION[unique_ident]["_embedded"]["events"][0]["dates"]["start"]["localDate"]
#       format: "2019-04-02"
#   self.time = CACHE_DICTION[unique_ident]["_embedded"]["events"][0]["dates"]["start"]["localTime"]
#       format: "19:30:00"

class TicketmasterEvent(object):
    # Constructor
    def __init__(self, event_diction):
        self.artists = [] # create a list to store the artists because there might be more than 1 artist in a event
        for artist in event_diction["_embedded"]["attractions"]:
            self.artists.append(["name"])
        self.eventname = event_diction["name"] # the name of event
        self.date = event_diction["dates"]["start"]["localDate"] # the date of event
        self.time = event_diction["dates"]["start"]["localTime"] # the time of event

    # Print method
    def __str__(self):
        artists_string_grammar = ""
        how_many_artists = len(self.artists)
        if how_many_artists == 1:
            artists_string_grammar = self.artists
        elif how_many_artists == 2:
            artists_string_grammar = self.artists[0] + " and " + self.artists[0]
        else:
            for i in self.artists[:how_many_artists-1]:
                artists_string_grammar = artists_string_grammar + i + ", "
            artists_string_grammar = artists_string_grammar + ", and " + self.artists[-1]
        return "{} will performance in {} on {} {}!".format(artists_string_grammar, self.eventname, self.date, self.time)
        # print the artist name and the event details

print("=============== Step 2 =================")

## Step 2:
## Create a class called "ITunesMedia" that represents one piece of iTunes media, which would be a sond ny investigating iTunes API documentation.
# The structrue of iTunes API data:
#   CACHE_DICTION[unique_ident]["results"][0]
#
#   self.artists = CACHE_DICTION[unique_ident]["results"][0]["artistName"]
#       format: "Ariana Grande"
#   self.song = CACHE_DICTION[unique_ident]["results"][0]["trackName"]
#       format: "thank u, next"
#   self.milllength = CACHE_DICTION[unique_ident]["results"][0]["trackTimeMillis"]
#       format: 207322
#   self.collection = CACHE_DICTION[unique_ident]["results"][0]["collectionName"]
#       format: "thank u, next - Single"
#   self.date = CACHE_DICTION[unique_ident]["results"][0]["releaseDate"]
#       format: "2018-11-03T07:00:00Z"

class ITunesMedia(object):
    # Constructor
    def __init__(self, song_diction):
        self.artists = song_diction["artistName"] # the artist name of the song
        self.song = song_diction["trackName"] # the name of the song
        self.milllength = song_diction["trackTimeMillis"] # the length in milliseconds of the song # To be convert
        self.collection = song_diction["collectionName"] # the collection name of the song
        self.date = song_diction["releaseDate"] # released date of the song

    # Extra method
    def normallength(self):
        mins = int(self.length / 1000 / 60)
        secs = int((self.length / 1000) % 60)
        return "{}:{}".format(mins, secs)
        # Turn milliseconds to minutes and seconds

    # Print Method
    def __str__(self):
        return "Date: {} \n Artist: {} \n Song: {} \n Album: {} \n Length:{} ".format(self.date, self.artists, self.song, self.collection, self.normallength())

print("=============== Step 3 =================")

## Step 3:
## Make a search on Ticketmaster (accessing and caching data)
## ============================
## | Ticketmaster API request |
## ============================

# open master cache file and load it into dictionary to prepare for caching
try:
    cache_file = open(CACHE_FNAME, 'r')
    CACHE_DICTION = json.loads(cache_file.read())
    cache_file.close()
except:
    CACHE_DICTION = {}

# my API key
TICKETMASTER_API_KEY = "ANXpHUscAoL1olptTu6QJlhNmiCQ0BQD" # 5000 requests every 1 day

# My function to get event data with Ticketmaster API
# Input: postal code and the miles
# Ouput: return JSON file
def get_event_data_with_caching(input_postal_code, within_miles = "200"):
    baseurl = "https://app.ticketmaster.com/discovery/v2/events"    # baseurl
    diction_parameters = {}
    diction_parameters["apikey"] = TICKETMASTER_API_KEY
    diction_parameters["classificationName"] = "music"              # only return music result
    diction_parameters["size"] = "1"                                # only return one result
    diction_parameters["postalCode"] = input_postal_code
    diction_parameters["radius"] = within_miles

    unique_ident = params_unique_combination(baseurl, diction_parameters)

    if unique_ident in CACHE_DICTION:
        return CACHE_DICTION[unique_ident]
    else:
        resp = requests.get(baseurl, params=diction_parameters)
        python_object = json.loads(resp.text)

        cache_file_object = open(CACHE_FNAME, 'w')
        CACHE_DICTION[unique_ident] = python_object
        cache_file_object.write(json.dumps(CACHE_DICTION))
        cache_file_object.close()
        return CACHE_DICTION[unique_ident]

# aa_result = get_event_data_with_caching("48104")
# print(aa_result)


print("=============== Step 4 =================")
## Step 4:
## Using that data to create a list of instance of TicketmasterEvent

instance_list_tm = []
search_tm_events = get_event_data_with_caching("48104")
# print(search_tm_events)

for event_diction in search_tm_events["_embedded"]["events"]:
    instance = TicketmasterEvent(event_diction)
    instance_list_tm.append(instance.eventname)
print(instance_list_tm)


print("=============== Step 5 =================")
## Step 5:
## Create an empty list to hold iTunes results

itunes_results = []

print("=============== Step 6 =================")
## Step 6:
## For each TM event, make a search on the iTunes Search API
## ============================
## |    iTunes API request    |
## ============================


# My function to get track data with iTunes API
# Input: artist name and how many songs
# Output: return JSON file
def get_artist_songs_with_caching(input_artist, how_many_songs = "10"):
    baseurl = "https://itunes.apple.com/search"
    diction_parameters = {}
    diction_parameters["term"] = input_artist   # The URL-encoded text string you want to search for. For example: jack+johnson.	Any URL-encoded text string. Note: URL encoding replaces spaces with the plus (+) character and all characters except the following are encoded: letters, numbers, periods (.), dashes (-), underscores (_), and asterisks (*).
    diction_parameters["media"] = "music"
    diction_parameters["entity"] = "musicTrack"
    diction_parameters["limit"] = how_many_songs
    unique_ident = params_unique_combination(baseurl, diction_parameters)

    if unique_ident in CACHE_DICTION:
        return CACHE_DICTION[unique_ident]
    else:
        resp = requests.get(baseurl, params=diction_parameters)
        python_object = json.loads(resp.text)

        cache_file_object = open(CACHE_FNAME, 'w')
        CACHE_DICTION[unique_ident] = python_object
        cache_file_object.write(json.dumps(CACHE_DICTION))
        cache_file_object.close()
        return CACHE_DICTION[unique_ident]

ariana = get_artist_songs_with_caching("Ariana")
# print(ariana)

print("=============== Step 7 =================")
## Step 7:
## From the resulting data, create a list of instance of ITunesMedia
## Add everything in that list to master list of iTunes results

instance_list_it = []
result_it_search = get_artist_songs_with_caching("Ariana")
# print(result_it_search)

for song_diction in result_it_search['results']:
    instance = ITunesMedia(song_diction)
    instance_list_it.append(instance.song)

print(len(instance_list_it))
print(instance_list_it)

print("=============== Step 8 =================")
## Step 8:
## Make a CSV file called "event_media.csv"
## trackName, artistName, normallength, collection, releaseDate
