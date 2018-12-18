# SI506F18_final_project.py
# My project will focus on searching recent "concerts" in Detroit area with Ticketmaster and then list the 10 most recent songs of that artists who performance in the concerts with iTunes research API.
# -*- coding: utf-8 -*-

# import
import requests
import json
# import csv to create a csv file
import csv
# import sys to resolve the encoding problem
import sys
reload (sys)
sys.setdefaultencoding('utf-8')

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

# print("\n=============== TICKETMASTER =================\n")

## Step 0:
## Read the Ticketmaster API documentation and decide what data I want to request
##   Decision: Music Concerts

## Step 1:
## Create a class called "TicketmasterEvent" by investigating Ticketmaster data to store the specific data for later use
# The structrue of Ticketmaster API data :
#   event_diction = CACHE_DICTION[unique_ident]["_embedded"]["events"][0]
#       [0]~[4]: each event

#   self.artists = CACHE_DICTION[unique_ident]["_embedded"]["events"][0]["_embedded"]["attractions"][0]["name"]
#       format: "Amos Lee"
#   self.eventname = CACHE_DICTION[unique_ident]["_embedded"]["events"][0]["name"]
#       format: "Amos Lee"
#   self.eventlink = CACHE_DICTION[unique_ident]["_embedded"]["events"][0]["url"]
#       format: "https://www.ticketmaster.com/needtobreathe-acoustic-live-tour-ann-arbor-michigan-02-15-2019/event/08005568F16B575A"
#   self.date = CACHE_DICTION[unique_ident]["_embedded"]["events"][0]["dates"]["start"]["localDate"]
#       format: "2019-04-02"
#   self.time = CACHE_DICTION[unique_ident]["_embedded"]["events"][0]["dates"]["start"]["localTime"]
#       format: "19:30:00"

## TICKETMASTER CLASS
class TicketmasterEvent(object):
    # Constructor
    def __init__(self, event_diction):
        self.artists = [] # create a list to store the artists because there might be more than 1 artist in a event
        for artist in event_diction["_embedded"]["attractions"]:
            self.artists.append(artist["name"])
        self.eventname = event_diction["name"] # the name of event
        self.eventlink = event_diction["url"] # the link of event
        self.date = event_diction["dates"]["start"]["localDate"] # the date of event
        self.time = event_diction["dates"]["start"]["localTime"] # the time of event

    # Extra method
    # Adjust the grammer of artists for print method
    def artists_string_grammar(self):
        artists_string_grammar = ""
        how_many_artists = len(self.artists)
        if how_many_artists == 1:
            artists_string_grammar = self.artists[0]
        elif how_many_artists == 2:
            artists_string_grammar = self.artists[0] + " and " + self.artists[1]
        else:
            for i in self.artists[:how_many_artists-1]:
                artists_string_grammar = artists_string_grammar + i + ", "
            artists_string_grammar = artists_string_grammar + ", and " + self.artists[-1]
        return artists_string_grammar

    # def timeformatting(self):
    #     formatted_date = self.date.strftime('%d, %b %Y')
    #     return formatted_date

    # Print method
    def __str__(self):
        return "{} will performance in the concert '{}' on {} {}!\nYou can buy the ticket here: {}".format(self.artists_string_grammar().encode('utf-8'), self.eventname.encode('utf-8'), self.date, self.time, self.eventlink)
        # print the artist name and the event details

## Step 2:
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


## Step 3:
## Using that data to create a list of instance of TicketmasterEvent
# Create a empty instance list
instance_list_ticketmaster = []
instance_list_ticketmaster_artists = []

# # Request the data form ticketmaster api with the parameter: "48104" which is Ann Arbor, MI
# postalcode = input("To search the concert near you, enter 5 digits postal code (eg. 48104): ")
# nearest_concert = get_event_data_with_caching(postalcode)
#
# #   event_diction = CACHE_DICTION[unique_ident]["_embedded"]["events"][0]
# try:
#     for event_diction in nearest_concert["_embedded"]["events"]:
#         instance = TicketmasterEvent(event_diction)
#         instance_list_ticketmaster.append(instance)
#         instance_list_ticketmaster_artists = instance.artists
#     print("Searching for the concert ...")
# except:
#     print("Sorry, no concert in this area. Please try another postal code.")

while True:
    postalcode = input("To search the concert near you, enter 5 digits postal code (eg. 48104): \n")
    nearest_concert = get_event_data_with_caching(postalcode)
    try:
        for event_diction in nearest_concert["_embedded"]["events"]:
            instance = TicketmasterEvent(event_diction)
            instance_list_ticketmaster.append(instance)
            instance_list_ticketmaster_artists = instance.artists
        print("Searching for the concert in {} with Ticketmaster API ...".format(postalcode))
    except:
        print("\nSorry, no concert in this area. Please try another postal code.")
    else:
        print("Congrats! We found this concert for you:")
        break
print("==================================================================================")
# Print the concert details
if instance_list_ticketmaster != []:
    # print(instance_list_ticketmaster_artists)
    for i in instance_list_ticketmaster:
        print(i)
print("==================================================================================")
print("Guess what?! We also found 10 recommended songs of concert lineup for you!\n")



# =============== ITUNES =================

## Step 4:
## Create a class called "ITunesMedia" that represents one piece of iTunes media, which would be a sond ny investigating iTunes API documentation.
# The structrue of iTunes API data:
#   CACHE_DICTION[unique_ident]["results"][0]

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

## ITUNES CLASS
class ITunesMedia(object):
    # Constructor
    def __init__(self, song_diction):
        self.artists = song_diction["artistName"] # the artist name of the song
        self.song = song_diction["trackName"] # the name of the song
        self.milllength = song_diction["trackTimeMillis"] # the length in milliseconds of the song # To be convert
        self.collection = song_diction["collectionName"] # the collection name of the song
        self.date = song_diction["releaseDate"] # released date of the song

    # Additional method
    def normallength(self):
        mins = int(self.milllength / 1000 / 60)
        secs = int((self.milllength / 1000) % 60)
        return "{}:{}".format(mins, secs)
        # Turn milliseconds to minutes and seconds

    # Print Method
    def __str__(self):
        return "Artist: {} \nSong: {} \nAlbum: {} \nLength: {} \nDate: {} \n".format(self.artists.encode('utf-8'), self.song.encode('utf-8'), self.collection.encode('utf-8'), self.normallength(), self.date)


## Step 5:
## Make a search on iTunes API (accessing and caching data)
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


## Step 6:
## Create an empty master list to hold iTunes results
itunes_results_master = []

## Step 7:
## Create a list to store the instance of ITunesMedia of each artist we got from TicketmasterEvent
## The list will store the data of 10 songs of the artist

## For each artist of Ticketmaster event, make a search on the iTunes Search API
# instance_list_ticketmaster_artists = [u'NEEDTOBREATHE', u'Matt Maeson']

for artist in instance_list_ticketmaster_artists:
    instance_songs_of_artist = []
    json_itunes = get_artist_songs_with_caching(artist.replace(" ","+"))
    for song_diction in json_itunes['results']:
        data_each_song = ITunesMedia(song_diction)
        # print(data_each_song)
        ## Add each song's data in the list of instance_songs_of_artist
        instance_songs_of_artist.append(data_each_song)
    # print("End of {}".format(artist))
## Step 8:
    ## Add everything in that list to master list of iTunes results with sorted list
    ## The list of songs is sorted by the release date (from the latest to the oldest)
    itunes_results_master.append(sorted(instance_songs_of_artist, key = lambda x: x.date, reverse = True))

# print(itunes_results_master)


# print("\n=============== CSV =================\n")
## Step 9:
## Make a CSV file called "event_media.csv"

csv_file = open("event_media.CSV", "w")
csv_file.write("Concert,Date,Time,Lineup,Link\n")
for event in instance_list_ticketmaster:
    csv_file.write("{},{},{},{},{}\n".format(event.eventname, event.date, event.time, event.artists_string_grammar(), event.eventlink))
csv_file.write("\n")
csv_file.write("Artist,Track,Album,Length,Release Date\n")
for artist in itunes_results_master:
    for song in artist:
        csv_file.write("{},{},{},{},{}\n".format(song.artists.replace(',', '&'), song.song.replace(',', ''), song.collection.replace(',', '&'), song.normallength(), song.date))
csv_file.close()
print("The CSV file is created successfully. Open the file and Listen to the top 10 songs we have sorted for you.\nLet's start from the latest one! Enjoy!")
