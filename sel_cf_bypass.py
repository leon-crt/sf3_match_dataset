from seleniumbase import Driver
from seleniumbase.common.exceptions import TextNotVisibleException
from curl_cffi import requests
import json
import subprocess

# ---------------- USEFUL CLASSES AND STRUCTS ------------------

class Queue:
    q = []
    def __init__(self, q):
        self.q = q
    def push(self, item):
        self.q.append(item)
    def pop(self):
        popped = self.q[0]
        self.q = self.q[1:]
        return popped
    def top(self):
        return self.q[0]
    def size(self):
        return len(self.q)
        

class PlayerSchema:
    def __init__(self, name, country, rank, score):
        self.name:str = name
        self.country:str = country
        self.rank:int = rank
        self.score:int = score

class ReplaySchema:
    def __init__(self, quarkid, channelname, date, duration, emulator, gameid, num_matches, players, ranked=None, replay_file=None, realtime_views=None, saved_views=None):
        self.quarkid:str = quarkid
        self.channelname:str = channelname
        self.date:int = date
        self.duration:float = duration
        self.emulator:str = emulator
        self.gameid:str = gameid
        self.num_matches:int = num_matches
        self.players:PlayerSchema[2] = [PlayerSchema(**player) for player in players]
        self.ranked = ranked
        self.replay_file:str = replay_file
        self.realtime_views:int = realtime_views
        self.saved_views:int = saved_views


def getTheDamnCookie():
    # Get the damn cookie
    # Launch in undetected-chromedriver mode
    driver = Driver(uc=True)
    # Visit the target page
    driver.uc_open_with_reconnect(url, 4)
    driver.uc_gui_handle_captcha()
    # Wait for the desired text to appear
    cookies = driver.get_cookies()
    ua = driver.execute_script("return navigator.userAgent;")
    cookies = {c['name']: c['value'] for c in driver.get_cookies()}
    driver.quit()
    return cookies, ua

def getUsername(username, url, ua, cookies):
    response = requests.post(
    url,
    json={"req": "getuser", "username": username},
    cookies=cookies,
    headers={
        "User-Agent": ua,
        "Referer": url,
    },
    impersonate="chrome110" 
    )
    return response

def getReplays(limit, offset, cookies, ua, url):
    response = requests.post(
        url,
        json={"req": "searchquarks", "gameid": "sfiii3nr1", "limit": limit, "offset": offset}, # max replays per request is 101, offset should be taken from a file to save progress in scraping
        cookies=cookies,
        headers={
            "User-Agent": ua,
            "Referer": url,
        },
        impersonate="chrome110" 
    )

    replay_resp = response.json()
    replays = []
    if len(replay_resp['results']) <= 1:
        return replays # no more replays to be found
    
    # transpose from json to class
    for rep_json in replay_resp['results']['results']:
        # only process the replays that have at least one completed match
        if rep_json['num_matches'] >= 1: 
            replays.append(ReplaySchema(**rep_json))

    return replays



# ---------------- API QUARKID SCRAPING PART ------------------

url = "https://www.fightcade.com/api/"
ua:str = ""
cookies = {}
offset = 0

# Get parameters from config file if it exists otherwise create it
try:
    with open("config.json", 'r+') as f:
        config = json.loads(f.read())
        ua = config['user_agent']
        cookies = config['cookies']
        offset = config['offset']
        test_response = getUsername('otana', url, ua, cookies)
        # try auth params from config, if they dont work, update them
        if test_response.status_code == 403:
            cookies, ua = getTheDamnCookie()
            config['user_agent'] = ua
            config['cookies'] = cookies
            json.dump(config, f, ensure_ascii=False, indent=4)
        elif test_response.status_code != 200:
            print("Something went wrong with API call. Collection Interrupted.")
except(FileNotFoundError):
        with open("config.json", 'x') as f:
            cookies, ua = getTheDamnCookie()
            json.dump({"user_agent": ua, "cookies": cookies, "offset": 0}, f, ensure_ascii=False, indent=4)

replay_buf = Queue([])

# Collection loop that will be interrupted when no more replays are returned by the API call
while(True):
    replays = getReplays(100, offset, cookies, ua, url)
    if len(replays) < 1:
        print('No More Replays were returned by the API call, processed a total of ' + str(offset) + ' replays')
        break
    for replay in replays:
        replay_buf.push(replay)

    while(replay_buf.size() > 0):
        # TODO: CHANGE QUARKID QUEUE TO REPLAY QUEUE TO ACCESS PLAYER NAMES
        replay = replay_buf.pop()
        # CAN POSSIBLY HANDLE MORE THAN ONE EMU INSTANCE AT ONCE
        subprocess.run(["./emulator_build/fcadefbneo.exe", "filename:" + replay.players[0].name + "-" + replay.players[1].name + "_" + replay.quarkid, "quark:stream,sfiii3nr1," + replay.quarkid + ".9,7100", "./replay_extraction.lua"])
        # execute in command line: ./fcadefbneo.exe filename:<nameOfFile> quark:stream,sfiii3nr1,<quarkID>.9,7100 <path-to-lua> 
        # CREATE TCP SERVER TO KNOW WHEN LUA HAS FINISHED PROCESSING THE REPLAY

    # update config Json with new offset 
    offset += len(replays)
    with open("config.json", 'r+') as f:
        config = json.loads(f.read())
        config['offset'] = offset
        json.dump(config, f, ensure_ascii=False, indent=4)



