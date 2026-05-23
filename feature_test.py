import csv
import numpy as np
import matplotlib.pyplot as plt

def load_file(path, filename):
    with open(path + filename, newline='') as f:
        reader = csv.reader(f)
        data = list(reader)
    dataP1, dataP2 = [data[1]], []
    for i in range(1, int((len(data)-1)/2)):
        dataP1.append(data[i*2+1])
        dataP2.append(data[i*2])
    dataP2.append(data[-1])
    return np.array(dataP1), np.array(dataP2)

def col_to_int(column):
    res = []
    for elem in column:
        res.append(int(elem))
    return np.array(res)

def test_ranges(data, playerLabel):
    posX = col_to_int(data[1:,2])
    posY = col_to_int(data[1:,3])
    health = col_to_int(data[1:,4])
    meter = col_to_int(data[1:,5])
    stun = col_to_int(data[1:,6])
    isStunned = col_to_int(data[1:,7])
    hit = col_to_int(data[1:,8])
    thrown = col_to_int(data[1:,9])
    plt.plot(stun,label='stun')
    plt.plot(hit*health, '.', label='hit')
    plt.plot(isStunned*10, '-', label='isStunned')
    plt.plot(health, '-.', label="health",)
    plt.plot(thrown*health, '-.', label="thrown")
    plt.plot(meter, '-.', label='meter')

    plt.xlabel("Frames")
    plt.ylabel("State variables value")
    plt.legend()
    plt.title(playerLabel + ' state data')
    plt.show()


dataP1, dataP2 = load_file("features/Makoto2/Akuma1/", "2-Akuma1-Makoto2-1770485490476-1711-2.csv")
test_ranges(dataP1, 'P1')
test_ranges(dataP2, 'P2')