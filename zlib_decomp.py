import zlib

filename = "zycxzla_vurgal_1773740750671.fr"
with open(filename, 'rb') as f:
    data = f.read()

# We iterate through the file byte by byte to find where the zlib stream starts
for i in range(len(data)):
    try:
        # Attempt to decompress from the current offset
        decompressed = zlib.decompress(data[i:])
        
        # Check if the result starts with the FB1 header you found earlier
        if decompressed.startswith(b""):
            print(f"[+] Found valid zlib stream at offset: {i}")
            with open("recovered_replay.fc2", "wb") as out:
                out.write(decompressed)
            print("[!] Successfully saved recovered_replay.fc2")
    except zlib.error:
        # Not a valid zlib start point, keep looking
        continue
print('failed to decompress')

