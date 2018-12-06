# SI506F18_project_apis.py
# Author: Roy Wang
# Final Project Preparation
# My project will focus on searching recent "concerts" in Detroit area with Ticketmaster and then list the 10 most recent songs of that artists who performance in the concerts with iTunes research API.
import requests
import json
import random

CACHE_FNAME = 'cache_file_name.json'
try:
    cache_file = open(CACHE_FNAME, 'r')
    cache_contents = cache_file.read()
    CACHE_DICTION = json.loads(cache_contents)
    cache_file.close()
except:
    CACHE_DICTION = {}

TICKETMASTER_API_KEY = "ANXpHUscAoL1olptTu6QJlhNmiCQ0BQD" # 5000 requests every 1 day
def params_unique_combination(baseurl, params_d, private_keys=["apikey"]):
    alphabetized_keys = sorted(params_d.keys())
    res = []
    for k in alphabetized_keys:
        if k not in private_keys:
            res.append("{}-{}".format(k, params_d[k]))
    return baseurl + "_".join(res)

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

# class TicketmasterEvent(object):
#     def __init__(self):
#         pass

#     def params_unique_combination(baseurl, params_d, private_keys=["api_key"]):
#         alphabetized_keys = sorted(params_d.keys())
#         res = []
#         for k in alphabetized_keys:
#             if k not in private_keys:
#                 res.append("{}-{}".format(k, params_d[k]))
#         return baseurl + "_".join(res)

#     def get_ticketmaster_data(self, ):
#         ticketmaster_root_url = "https://app.ticketmaster.com/discovery/v2/"
#         diction_parameters = {}
#         diction_parameters["apikey"] = TICKETMASTER_API_KEY
#         diction_parameters["classificationName"] = "music"
#         diction_parameters["dmaId"] = dmaid
# 
#     def __str__(self):
#         pass


# https://app.ticketmaster.com/discovery/v2/events.json?size=5&classificationName=music&postalCode=48104&radius=200&apikey=ANXpHUscAoL1olptTu6QJlhNmiCQ0BQD





# Look up multiple artists by their AMG artist IDs and get each artist’s 5 most recent songs: https://itunes.apple.com/lookup?amgArtistId=468749,5723&entity=song&limit=5&sort=recent.

# ITUNES_API_KEY = ""
# class ITunesMedia(object):
#     """ iTunes: https://affiliate.itunes.apple.com/resources/documentation/itunes-store-web-service-search-api/ """
#     def __init__(self):
#         pass
#     def __str__(self):
#         pass
