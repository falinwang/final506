# SI506F18_project_apis.py
# Author: Roy Wang
# Final Project Preparation


if FLICKR_KEY == "" or not FLICKR_KEY:
    FLICKR_KEY = input("Enter your flickr API key now, or paste it in the assignment .py file to avoid this prompt in the future. (Do NOT include quotes around it when you type it in to the command prompt!) \n>>")

def params_unique_combination(baseurl, params_d, private_keys=["api_key"]):
    alphabetized_keys = sorted(params_d.keys())
    res = []
    for k in alphabetized_keys:
        if k not in private_keys:
            res.append("{}-{}".format(k, params_d[k]))
    return baseurl + "_".join(res)

def get_flickr_data(tagstr, numfoto = 50):
    baseurl = "https://api.flickr.com/services/rest/"
    params_d = {}
    params_d["media"] = "photos"
    params_d["tag_mode"] = "all"
    params_d["format"] = "json"
    params_d["method"] = "flickr.photos.search"
    params_d["per_page"] = numfoto
    params_d["api_key"] = FLICKR_KEY
    params_d["tags"] = tagstr
    uni_ident = params_unique_combination(baseurl, params_d)
    if uni_ident in CACHE_DICTION:
        return CACHE_DICTION[uni_ident]
    else:
        resp = requests.get(baseurl, params=params_d)
        resp_str = resp.text
        python_object = json.loads(resp_str[14:-1])
        cache_file_object = open(CACHE_FNAME, 'w')
        CACHE_DICTION[uni_ident] = python_object
        cache_file_object.write(json.dumps(CACHE_DICTION))
        cache_file_object.close()
        return CACHE_DICTION[uni_ident]

TICKETMASTER_API_KEY = "ANXpHUscAoL1olptTu6QJlhNmiCQ0BQD"
ITUNES_API_KEY = ""
ticketmaster_root_url = "https://app.ticketmaster.com/discovery/v2/"


# Look up multiple artists by their AMG artist IDs and get each artist’s 5 most recent songs: https://itunes.apple.com/lookup?amgArtistId=468749,5723&entity=song&limit=5&sort=recent.


class TicketmasterEvent:
    ''
    def __init__:
        pass

    def get_ticketmaster_data(concernamt):
        ticketmaster_root_url = "https://app.ticketmaster.com/discovery/v2/"
        diction_parameters = {}
        diction_parameters["apikey"] = TICKETMASTER_API_KEY
        diction_parameters["classificationName"] = "music"
        diction_parameters["dmaId"] = dmaid

    def __str__:
        pass

class ITunesMedia:
    """ iTunes: https://affiliate.itunes.apple.com/resources/documentation/itunes-store-web-service-search-api/ """
    def __init__:
        pass
    def __str__:
        pass
