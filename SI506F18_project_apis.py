# SI506F18_project_apis.py
# Author: Roy Wang
# Final Project Preparation
# My project will focus on searching recent "concerts" in Detroit area with Ticketmaster and then list the 10 most recent songs of that artists who performance in the concerts with iTunes research API.

import requests
import json

def params_unique_combination(baseurl, params_d, private_keys=["apikey"]):
    alphabetized_keys = sorted(params_d.keys())
    res = []
    for k in alphabetized_keys:
        if k not in private_keys:
            res.append("{}-{}".format(k, params_d[k]))
    return baseurl + "_".join(res)

## ========== Part 1 ==========
##   Ticketmaster API request
## ============================

print("=============== Part 1 =================")

CACHE_FNAME_TM = 'cache_file_ticketmaster.json'
try:
    cache_file_ticketmaster = open(CACHE_FNAME_TM, 'r')
    CACHE_DICTION_TM = json.loads(cache_file_ticketmaster.read())
    cache_file_ticketmaster.close()
except:
    CACHE_DICTION_TM = {}

TICKETMASTER_API_KEY = "ANXpHUscAoL1olptTu6QJlhNmiCQ0BQD" # 5000 requests every 1 day

def get_event_data_with_caching(input_postal_code, within_miles = "200"):
    baseurl = "https://app.ticketmaster.com/discovery/v2/events"
    diction_parameters = {}
    diction_parameters["apikey"] = TICKETMASTER_API_KEY
    diction_parameters["classificationName"] = "music"
    diction_parameters["size"] = "1"
    diction_parameters["postalCode"] = input_postal_code
    diction_parameters["radius"] = within_miles
    unique_ident = params_unique_combination(baseurl, diction_parameters)
    if unique_ident in CACHE_DICTION_TM:
        return CACHE_DICTION_TM[unique_ident]
    else:
        resp = requests.get(baseurl, params=diction_parameters)
        python_object = json.loads(resp.text)

        cache_file_object = open(CACHE_FNAME_TM, 'w')
        CACHE_DICTION_TM[unique_ident] = python_object
        cache_file_object.write(json.dumps(CACHE_DICTION_TM))
        cache_file_object.close()
        return CACHE_DICTION_TM[unique_ident]

# aa_result = get_event_data_with_caching("48104")
# print(aa_result)
# print("________________")

class TicketmasterEvent(object):
    def __init__(self, event_diction):
        self.artists = event_diction["_embedded"]["events"][0]["_embedded"]["attractions"][0]["name"]
        self.concert = event_diction["_embedded"]["events"][0]["name"]
        self.date = event_diction["_embedded"]["events"][0]["dates"]["start"]["localDate"]
        self.address = event_diction["_embedded"]["events"][0]["_embedded"]["venues"][0]["address"]["line1"]

    def __str__(self):
        return "date includes: {}, address includes: {}, and the artists includes: {}.".format(self.date, self.address,self.artists)


concert_of_48104 = TicketmasterEvent(get_event_data_with_caching("48104"))
print(concert_of_48104.artists)

## ========== Part 2 ==========
##   Ticketmaster API request
## ============================
print("=============== Part 2 =================")

CACHE_FNAME_IT = 'cache_file_itunes.json'
try:
    cache_file_itunes = open(CACHE_FNAME_IT, 'r')
    CACHE_DICTION_IT = json.loads(cache_file_itunes.read())
    cache_file_itunes.close()
except:
    CACHE_DICTION_IT = {}

def get_artist_songs_with_caching(input_artist, how_many_songs = "10"):
    baseurl = "https://itunes.apple.com/search"
    diction_parameters = {}
    diction_parameters["term"] = input_artist   # The URL-encoded text string you want to search for. For example: jack+johnson.	Any URL-encoded text string. Note: URL encoding replaces spaces with the plus (+) character and all characters except the following are encoded: letters, numbers, periods (.), dashes (-), underscores (_), and asterisks (*).
    diction_parameters["media"] = "music"
    diction_parameters["entity"] = "musicTrack"
    diction_parameters["limit"] = how_many_songs
    unique_ident = params_unique_combination(baseurl, diction_parameters)
    
    if unique_ident in CACHE_DICTION_IT:
        return CACHE_DICTION_IT[unique_ident]
    else:
        resp = requests.get(baseurl, params=diction_parameters)
        python_object = json.loads(resp.text)
        cache_file_object = open(CACHE_FNAME_IT, 'w')
        CACHE_DICTION_IT[unique_ident] = python_object
        cache_file_object.write(json.dumps(CACHE_DICTION_IT))
        cache_file_object.close()
        return CACHE_DICTION_IT[unique_ident]

# ariana = get_artist_songs_with_caching("Ariana")
# print(ariana)


class ITunesMedia(object):
    """ iTunes: https://affiliate.itunes.apple.com/resources/documentation/itunes-store-web-service-search-api/ """
    def __init__(self, songs_diction):
        self.artists = []
        for track in songs_diction["results"]:
            self.artists.append(track["artistName"])

    def __str__(self):
        return "This is about {}".format(self.artists)


tm_cache = open("cache_file_ticketmaster.json")
tm_diction = json.loads(tm_cache.read())
tm_cache.close()
tm = TicketmasterEvent(tm_diction[list(tm_diction.keys())[0]])

print("who?", tm.artists)
# print(get_artist_songs_with_caching(tm.artists))


it_cache = open("cache_file_itunes.json")
it_diction = json.loads(it_cache.read())
it_cache.close()
print(ITunesMedia(it_diction[list(it_diction.keys())[1]]))



# TODO: (1) the songs should be sorted by release date, (2) think if I want to get only one concert, 
