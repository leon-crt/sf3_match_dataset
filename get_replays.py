from seleniumbase import Driver
from seleniumbase.common.exceptions import TextNotVisibleException
from curl_cffi import requests
import json
import subprocess
import socket
import time
from datetime import datetime
import win32process
import win32gui
import win32api
import win32con
import sys

# WEBSOCKET STUFF
HOST = "127.0.0.1"
PORT = 42069

# ---------------- USEFUL CLASSES AND FUNCTIONS ------------------

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
    def __init__(self, name:str, country, rank, score):
        self.name:str = name.replace(' ', '_') # we dont want any spaces in the file paths just to be safe
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

def getReplays(limit, offset, username, cookies, ua, url):
    response = requests.post(
        url,
        json={"req": "searchquarks","username": username, "gameid": "sfiii3nr1", "limit": limit, "offset": offset}, # max replays per request is 101, offset should be taken from a file to save progress in scraping
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
    total = len(replay_resp['results']['results'])
    print("Fetched " + str(total) + " replays: " + str(len(replays)) + " are of the appropriate minimum length and will be processed.")
    return replays, total # return the total number of fetched replays as well so we can advance the offset correctly

def enumWindowsProc(hwnd, lParam):
    if (lParam is None) or ((lParam is not None) and win32process.GetWindowThreadProcessId(hwnd)[1] == lParam):
        text = win32gui.GetWindowText(hwnd)
        if text:
            win32api.SendMessage(hwnd, win32con.WM_CLOSE)

# ---------------- API QUARKID SCRAPING PART ------------------

url = "https://www.fightcade.com/api/"
ua:str = ""
cookies = {}
offset = 0
username = ""
config = {}

# second cmdline arg which is username of who we want the replays of
if len(sys.argv) > 1:
    username = sys.argv[1]
    print("Fetching Replay Information for user: " + username + "...")
else:
    print("Fetching Replay Information for all users...")

# get parameters from config file if it exists otherwise create it
try:
    with open("config.json", 'r+') as f:
        config = json.loads(f.read())
        ua = config['user_agent']
        cookies = config['cookies']
        if (username != config['username']):
            config['username'] = username
            config['offset'] = 0
        offset = config['offset']
        # try auth params from config, if they dont work, update them
        test_response = getUsername("otana", url, ua, cookies)
        if test_response.status_code == 403:
            print("API auth credentials no longer valid, updating.")
            cookies, ua = getTheDamnCookie()
            config['user_agent'] = ua
            config['cookies'] = cookies
            config['offset'] = offset
            # deleting previous file contents
            f.seek(0)
            f.truncate()
            # writing new auth credentials to file
            json.dump(config, f, ensure_ascii=False, indent=4)
        elif test_response.status_code != 200:
            print("Something went wrong with API call. Collection Interrupted.")
except(FileNotFoundError):
        with open("config.json", 'x') as f:
            cookies, ua = getTheDamnCookie()
            config['user_agent'] = ua
            config['cookies'] = cookies
            config['offset'] = 0
            config['username'] = username
            json.dump(config, f, ensure_ascii=False, indent=4)

replay_buf = Queue([])

# ---------------------- EMULATOR RECORDING PART ---------------------------

print("Initiating Replay Recording")

# Collection loop that will be interrupted when no more replays are returned by the API call
while(True):
    replays, total_fetched = getReplays(100, offset, username, cookies, ua, url)
    if len(replays) < 1:
        print('No More Replays were returned by the API call, processed a total of ' + str(offset) + ' replays')
        break
    for replay in replays:
        replay_buf.push(replay)
    
    offset += total_fetched

    while(replay_buf.size() > 0):
        replay = replay_buf.pop()

        # get player side
        player_side = 1
        if(replay.players[0].name == username.replace(' ', '_')):
            player_side = 1
        else:
            player_side = 2
        
        print("Recording replay " + replay.quarkid + " - played on date: " + datetime.fromtimestamp(replay.date/1000).strftime('%Y-%m-%d %H:%M:%S'))

        # CAN POSSIBLY HANDLE MORE THAN ONE EMU INSTANCE AT ONCE (but would not know how to identify which process is sending signals)
        # execute in command line: ./fcadefbneo.exe filename:<nameOfFile> quark:stream,sfiii3nr1,<quarkID>.9,7100 <path-to-lua> 
        emu_proc = subprocess.Popen(["./emulator_build/fcadefbneo.exe", "filename:" + str(player_side) + '-' + str(replay.players[0].rank) + str(replay.players[1].rank) + '-' + replay.players[0].name + "-" + replay.players[1].name + "_" + replay.quarkid + ".fr", "quark:stream,sfiii3nr1," + replay.quarkid + ".9,7100", "./emulator_build/replay_extraction.lua"])
        emu_killed = False
        # CREATE TCP SERVER TO KNOW WHEN LUA HAS FINISHED PROCESSING THE REPLAY
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST,PORT))
            # set timeout where if the message is not received from client side, emu has finished so exit the loop
            first_ping = None
            second_ping = None
            tolerance = 1
            while True:
                if (second_ping != None):
                    try:
                        timeout_delta = second_ping - first_ping
                        s.settimeout(timeout_delta + tolerance) # set timeout as the time between the first two pings + some tolerance
                        s.listen()
                        conn,addr = s.accept()
                        with conn:
                            data = conn.recv(1024)
                    # Timeout means the replay is over and the recording is done
                    except socket.timeout:
                        break
                # gather info to set appropriate timeout
                else:
                    try:
                        s.settimeout(10) # set a 10 sec timeout for first two pings
                        s.listen()
                        conn,addr = s.accept()
                        with conn:
                            data = conn.recv(1024)
                        if(first_ping != None):
                            second_ping = time.time()
                        else:
                            first_ping = time.time()
                    except socket.timeout: # Likely a guru meditation error, skip the replay
                        print("Error - could not launch emulator correctly for this replay. Skipping to the next replay.")
                        emu_proc.kill()
                        emu_killed = True
                        break
        # kill emulator process and go on to the next replay if it's not dead yet because of an error
        if (not emu_killed):
            win32gui.EnumWindows(enumWindowsProc, emu_proc.pid)
            time.sleep(1) # not sure if this is necessary but wouldn't want overlapping instances of the emulator

    # update config Json with new offset 
    with open("config.json", 'w') as f:
        config['offset'] = offset
        json.dump(config, f, ensure_ascii=False, indent=4)