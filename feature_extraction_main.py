import json
import os
import re
import subprocess
import socket
import time
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
    
def enumWindowsProc(hwnd, lParam):
    if (lParam is None) or ((lParam is not None) and win32process.GetWindowThreadProcessId(hwnd)[1] == lParam):
        text = win32gui.GetWindowText(hwnd)
        if text:
            win32api.SendMessage(hwnd, win32con.WM_CLOSE)

# second cmdline arg which is path of folder containing the replays of which we want the features
if len(sys.argv) > 1:
    path = sys.argv[1]
    print("Extracting features for replays at path: " + path + "...")
else:
    print("Provide a path for the feature extraction")
    sys.exit()

# Gather the quarkids
total_replays = os.listdir(path)
replay_q = Queue([])
for name in total_replays:
    # extract the quarkid
    player_side = name[0] # first number in the string is which player is the expert
    print(name)
    print(player_side)
    name = name[::-1] # reverse the string
    print(name)
    quarkid = re.match(r"^[rf\.]+\d*\-\d*\_",name).group()
    quarkid = quarkid[::-1].replace('.fr', '').replace('_', '') # put the string in the right order again and remove the .fr extension and the _
    # push the replay to the queue
    replay_q.push([name[::-1], quarkid, player_side])

processed_replay_number = 0

# Collection loop that will be interrupted when no more replays are returned by the API call
while(replay_q.size() > 0):
    replay = replay_q.pop()
    
    print("Extracting features of replay " + replay[1])
    # execute in command line: ./fcadefbneo.exe <path-to-filename> <path-to-lua> 
    emu_proc = subprocess.Popen(["./emulator_build/fcadefbneoNormal.exe", path + replay[0], "./feature_extraction.lua"])
    emu_killed = False
    # CREATE TCP SERVER TO KNOW WHEN LUA HAS FINISHED PROCESSING THE REPLAY
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST,PORT))
        # set timeout where if the message is not received from client side, emu has finished so exit the loop
        connected = False
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
                    processed_replay_number += 1
                    break
            # send quarkid and gather info to set appropriate timeout 
            else:
                try:
                    s.settimeout(10) # set a 10 sec timeout for first two pings
                    s.listen()
                    conn,addr = s.accept()
                    with conn:
                        data = conn.recv(1024)
                        print(data)
                        if first_ping == None:
                            # send the quarkid
                            conn.send(bytes(replay[1] + '\r\n', "utf-8"))
                            print(conn.recv(1024))
                            # send the player side
                            conn.send(bytes(replay[2], "utf-8"))
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

print("Finished processing replays, processed a total of: " + str(processed_replay_number))