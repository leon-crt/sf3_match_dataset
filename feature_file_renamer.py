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
    file_args = file.split('-') # reverse the string
    quarkid = file_args[3] + '-' + file_args[4]
    
    if quarkid != previous_quarkid:
        for replay in replayList:
            if quarkid in replay:
                replay = replay.replace('_' + quarkid + '.fr', '')
                rep_params = replay.split('-')
                p1 = rep_params[1]
                p2 = rep_params[2]
                player_side = 1 + (1 - int(p1 == player))
                previous_quarkid = quarkid
                break
    new_file_name = str(player_side) + file[1:]
    os.rename(feat_path + '/' + file, f"{feat_path}/{new_file_name}")
    
                