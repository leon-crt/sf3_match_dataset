import requests
import curl_cffi as cc

username = 'Otana'

address = 'https://www.fightcade.com/api/'
headers = {'Accept-Encoding': '*', 'Content-Type': 'application/json'}
body = {'req': 'getuser', 'username': username}

cf_clearance = {'cf_clearance': 'jgl9TbkNZNPQ7Rv5xyGbafIQIRu9uhZu.4xMzRHN.Yc-1773782830-1.2.1.1-YcgWbcDkyUkymZO67X6TkOBhW0kCK2hXZ9q4nmOCEtHbmClWs4NgZxaX.fRnjr1aJsd.FlRstWb7g8UByjDlO4bjYE9iali0BMQWOlND8D63sc7d9aNE9t1ctDtKCUZEPZ_8m8DqKNEUSFrXQHTYGnqBb539XRkTtUY.JNm_uNc3bvKb_.4vzPkEsWBuK1mvggBsBVyevSBPgwHqBWf0mwsmpxTMq.8X2blCI_n7..EPNCxsPv6t8h1c_e0.EpUpT0P7zQJ.3Pd93ChZDoMfds_ai0CAAXfbfnEHDLkxIJmseBbnN.FhcP.IApc_RzN3Zv3Cal_b4wn4M053AlKvVA'}

cookie = cc.Cookies(cf_clearance)
# with cc.Session(cookies=cookie) as s:
#     r:cc.Response = s.post(address, json=body, cookies=cookie)
r = requests.post(address, json=body, headers=headers, cookies=cf_clearance)
print('Request: \n' + str(r.request) + ' ' + r.request.url)
print('Headers: ' + str(r.request.headers))
print('Body: ' + str(r.request.body))
print('Response: \n' + str(r.status_code))
print(r.text)
print(r.json())

