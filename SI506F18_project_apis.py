# SI506F18_project_apis.py
# Author: Roy Wang
# Final Project Preparation
# My project will focus on searching recent "concerts" in Detroit area with Ticketmaster and then list the 10 most recent songs of that artists who performance in the concerts with iTunes research API.

import requests
import json

CACHE_FNAME = 'cache_file_name.json'
try:
    cache_file = open(CACHE_FNAME, 'r')
    CACHE_DICTION = json.loads(cache_file.read())
    cache_file.close()
except:
    CACHE_DICTION = {}

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

TICKETMASTER_API_KEY = "ANXpHUscAoL1olptTu6QJlhNmiCQ0BQD" # 5000 requests every 1 day


def get_event_data_with_caching(input_postal_code):
    baseurl = "https://app.ticketmaster.com/discovery/v2/events"
    diction_parameters = {}
    diction_parameters["apikey"] = TICKETMASTER_API_KEY
    diction_parameters["classificationName"] = "music"
    diction_parameters["size"] = "5"
    diction_parameters["postalCode"] = input_postal_code
    diction_parameters["radius"] = "200"
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

aa_result = get_event_data_with_caching("48104")
print(aa_result)
print("________________")

# class TicketmasterEvent(object):
#     def __init__(self):
#         pass
# 
#     def __str__(self):
#         pass


## ========== Part 2 ==========
##   Ticketmaster API request
## ============================

def get_artist_songs_with_caching(input_artist, limit = 10):
    baseurl = "https://itunes.apple.com/search"
    diction_parameters = {}
    diction_parameters["term"] = input_artist   # The URL-encoded text string you want to search for. For example: jack+johnson.	Any URL-encoded text string. Note: URL encoding replaces spaces with the plus (+) character and all characters except the following are encoded: letters, numbers, periods (.), dashes (-), underscores (_), and asterisks (*).
    diction_parameters["media"] = "music"
    diction_parameters["entity"] = "musicTrack"
    diction_parameters["limit"] = limit
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
print(ariana)


# ITUNES_API_KEY = ""
# class ITunesMedia(object):
#     """ iTunes: https://affiliate.itunes.apple.com/resources/documentation/itunes-store-web-service-search-api/ """
#     def __init__(self):
#         pass
#     def __str__(self):
#         pass
