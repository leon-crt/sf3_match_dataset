import socket
import os

fcade_address = '141.94.138.123'
fcade_port = 7100

fcade_socket = socket.create_connection(address=(fcade_address, fcade_port))

date_id = '1773245874617'
sub_id = '6933'
quark_id = date_id + '-' + sub_id
# samcog vs sleepw4lker -> 1773245934968-9749
# pngyakuza vs ghusek -> 1773245874617-6933
# 1773740750671-9930

msg_1 = b'\x00\x00\x00\x14'

msg_2 = b'\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x1d\x00\x00\x00\x01'

msg_3 = b'\x00\x00\x00 '

msg_4 = b'\x00\x00\x00\x02\x00\x00\x00\x14\x00\x00\x00\x14' + (quark_id + '.7').encode() + b'\x00\x00\x00 \x00\x00\x00\x03\x00\x00\x00\x0c\x00\x00\x00\x14' + (quark_id + '.7').encode()

msg_arr = {msg_1, msg_2, msg_3, msg_4}


def send_msg(msg:str, socket:socket, rcv:bool, sz=0) -> bytes:
    socket.send(msg)
    data = ''
    if rcv:
        data = socket.recv(sz)
    return data

class Player_Info:
    name:str
    rank:str
    matches:str
    country:str
    def __init__(self, query_str):
        query_str = query_str.replace('\x00', '')
        query_str = query_str.replace('\r', '')
        query_str = query_str.replace('\x12', '')

        name_rank, self.matches, self.country = query_str.split(',')
        self.name, self.rank = name_rank.split('#')

# for msg in msg_arr:
#     data = 'ack'
#     if msg == msg_2 or msg == msg_4:
#         data = send_msg(msg, fcade_socket, True)
#     else:
#         send_msg(msg, fcade_socket, False)
#     print(data)

send_msg(msg_1, fcade_socket, False)
print(send_msg(msg_2, fcade_socket, True, 66))
send_msg(msg_3, fcade_socket, False)

query_b = send_msg(msg_4, fcade_socket, True, 113)
query:str = query_b.decode(encoding='utf-8')
player_1_info = Player_Info(query[16:32])
player_2_info = Player_Info(query[32:51])

file_path = player_1_info.name + '_' + player_2_info.name + '_' + date_id + '_1' + '.fr'
with open(file_path, 'wb+') as replay_f:
    buf = fcade_socket.recv(1024)
    while len(buf) > 0:
        buf = fcade_socket.recv(1024)
        replay_f.write(buf)

fcade_socket.close()