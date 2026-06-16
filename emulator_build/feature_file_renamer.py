import re
import os
import sys
from pathlib import Path

path = ''
feat_path = './features'
player = ''
if len(sys.argv) > 1:
    path = sys.argv[1]
    player = sys.argv[2]
    print("Extracting features for replays at path: " + path + "...")
else:
    print("Provide a path for the feature extraction")
    sys.exit()

featList = os.listdir(feat_path)
replayList = os.listdir(path)
quarkid = ''
previous_quarkid = ''
player_side = 0
for file in featList:
    file = file[::-1] # reverse the string
    print(file)
    quarkid = re.match(r"^[rf\.]+\d*\-\d*\_",file).group()
    quarkid = quarkid[::-1]
    file = file[::-1]
    if quarkid != previous_quarkid:
        for replay in replayList:
            if quarkid in replay:
                replay.replace(quarkid, '')
                rep_params = replay.split('-')
                p1 = rep_params[1]
                p2 = rep_params[2]
                player_side = 1 + int(p1 == player)
                previous_quarkid = quarkid
    os.rename(feat_path + '/' + file, feat_path + '/' + player_side + '-' + file)
    
                