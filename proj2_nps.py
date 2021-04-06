#################################
##### Name: Yufeng Chen
##### Uniqname: kardel
#################################
import os
from bs4 import BeautifulSoup
import requests
import json
import secrets  # file that contains your API key
import urllib
from secrets import API_KEY


class NationalSite:
    '''a national site

    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.
    
    name: string
        the name of a national site (e.g. 'Isle Royale')

    address: string
        the city and state of a national site (e.g. 'Houghton, MI')

    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')

    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    '''

    def __init__(self, category, name, address, zipcode, phone):
        self.category = category
        self.name = name
        self.address = address
        self.zipcode = zipcode
        self.phone = phone

    def info(self):
        return self.name + " (" + self.category + "): " + self.address + " " + self.zipcode


def openCache(filename):
    if not os.path.exists(filename):
        return {}
    with open(filename, "r") as f:
        return json.load(f)


def closeCache(cache, filename):
    # if not os.path.exists(filename):

    with open(filename, "w") as f:
        json.dump(cache, f)


def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from "https://www.nps.gov"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''
    TARGET_URL = 'https://www.nps.gov/findapark/index.htm'
    BASE_URL = "https://www.nps.gov"
    CACHE_FILENAME = "STATE_URL_DICT.json"
    cache = openCache(CACHE_FILENAME)
    if len(cache) != 0:
        print("Using cache")
        return cache
    print("Fetching")
    response = urllib.request.urlopen(TARGET_URL)
    html = response.read().decode('utf-8')
    response.close()
    bs = BeautifulSoup(html, "html.parser")
    rd = {}
    for area in bs.findAll("area"):
        state = area["alt"].lower()
        link = BASE_URL + area["href"]
        rd[state] = link
    cache = rd
    closeCache(cache, CACHE_FILENAME)
    return rd


def get_site_instance(site_url):
    '''Make an instances from a national site URL.
    
    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov
    
    Returns
    -------
    instance
        a national site instance
    '''
    CACHE_FILENAME = "SITE_URL_DICT.json"
    cache = openCache(CACHE_FILENAME)
    if site_url in cache:
        c = cache[site_url]
        print("Using Cache")
        return NationalSite(c["category"], c['name'], c['address'], c['zipcode'], c['phone'])
    print("Fetching")
    with urllib.request.urlopen(site_url) as response:
        html = response.read().decode("utf-8")
    bs = BeautifulSoup(html, "html.parser")
    titleContainer = bs.find("div", class_="Hero-titleContainer clearfix")
    name = titleContainer.find("a").text
    category = titleContainer.find("span", class_="Hero-designation").text
    address_p = bs.find("p", class_="adr")
    # print(address_p, site_url)
    if address_p is None:
        return None
    addr = address_p.find("span", {"itemprop": "addressLocality"})
    state = address_p.find("span", {"itemprop": "addressRegion"})
    postalCode = address_p.find("span", {"itemprop": "postalCode"})
    zip_code = postalCode.text.strip()
    address = addr.text + ", " + state.text.strip()
    telephone = bs.find("span", {"itemprop": "telephone"}).text.strip()
    ns = NationalSite(category, name, address, zip_code, telephone)
    cache[site_url] = {'category': category, "name": name, "address": address, "zipcode": zip_code, "phone": telephone}
    closeCache(cache, CACHE_FILENAME)
    return ns


def get_sites_for_state(state_url):
    '''Make a list of national site instances from a state URL.
    
    Parameters
    ----------
    state_url: string
        The URL for a state page in nps.gov
    
    Returns
    -------
    list
        a list of national site instances
    '''
    BASE_URL = "https://www.nps.gov"
    # CACHE_FILENAME = "SITE_URL_DICT.json"
    # cache = openCache(CACHE_FILENAME)

    with urllib.request.urlopen(state_url) as response:
        html = response.read().decode("utf-8")
    bs = BeautifulSoup(html)
    blocks = bs.findAll("li", class_="clearfix")
    nationalSites = []
    for block in blocks:
        if block.get("id") is None:
            continue
        if not block.get("id").startswith("asset"):
            continue

        park_url = BASE_URL + block.find("div").find("h3").find("a")["href"]
        nationalSite = get_site_instance(park_url)
        if nationalSite is not None:
            nationalSites.append(nationalSite)
        # cache[state_url] = nationalSites
    return nationalSites


def get_nearby_places(site_object: NationalSite):
    '''Obtain API data from MapQuest API.
    
    Parameters
    ----------
    site_object: object
        an instance of a national site
    
    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''
    CACHE_FILENAME = "NEARBY_PLACES.json"
    cache = openCache(CACHE_FILENAME)
    if site_object.zipcode in cache:
        print("Using Cache")
        return cache[site_object.zipcode]
    print("Fetching")
    BASE_URL = "http://www.mapquestapi.com/search/v2/radius"
    origin = site_object.zipcode
    key = API_KEY
    radius = 10
    maxMatches = 10
    ambiguities = "ignore"
    outFormat = "json"
    url = BASE_URL + "?" + "key=" + key + "&maxMatches=" + str(maxMatches) + "&origin=" + str(origin) + "&radius=" + \
          str(radius) + "&ambiguities=" + ambiguities + "&outFormat=" + outFormat
    with urllib.request.urlopen(url) as response:
        js = response.read().decode("utf-8")
    # print(js)
    d = json.loads(js)
    cache[site_object.zipcode] = d
    closeCache(cache, CACHE_FILENAME)
    return d
    # urllib.request.open("")


def main():
    state_dict = build_state_url_dict()
    while True:
        token = input("Enter a state name (e.g. Michigan, michigan) or exit: ").strip().lower()
        if token == "exit":
            return
        if token not in state_dict:
            print("[Error] Enter proper state name")
            continue
        nationalStates = get_sites_for_state(state_dict[token])
        SEPERATOR = "----------------------------------"
        print(SEPERATOR)
        print("List of national sites in", token)
        print(SEPERATOR)
        for i, ns in enumerate(nationalStates):
            print("[" + str(i + 1) + "]", ns.info())
        while True:
            token = input("Choose the number for detail search or \"exit\" or \"back\": ").strip().lower()
            if token == "back":
                break
            elif token == "exit":
                return
            try:
                id = int(token)
                if id > len(nationalStates):
                    raise ValueError()
                ns = nationalStates[id - 1]
                nearJsDict = get_nearby_places(ns)
                print(SEPERATOR)
                print("Places near", ns.name)
                print(SEPERATOR)
                if "searchResults" not in nearJsDict:
                    print("No such near results")
                    print(SEPERATOR)
                    continue
                for result in nearJsDict["searchResults"]:
                    fields = result["fields"]
                    if "group_sic_code_name" not in fields or fields["group_sic_code_name"] == "" or \
                            fields["group_sic_code_name"] is None:
                        category = "no category"
                    else:
                        category = fields["group_sic_code_name"]
                    if "address" not in fields or fields["address"] == "" or fields["address"] is None:
                        address = "no address"
                    else:
                        address = fields["address"]
                    if "city" not in fields or fields["city"] == "" or fields["city"] is None:
                        city = "no city"
                    else:
                        city = fields["city"]
                    # print(result)
                    # print(address)
                    street_address = address + ", " + city
                    name = result["name"]
                    info = name + " (" + category + "): " + street_address
                    print("-", info)
            except ValueError as ve:
                print("[Error] Invalid input")
                print()
                print(SEPERATOR)


if __name__ == "__main__":
    main()
