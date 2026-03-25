import requests

username = 'Otana'

address = 'https://www.fightcade.com/api/'
headers = {'Accept-Encoding': '*', 'Content-Type': 'application/json'}
body = {'req': 'getuser', 'username': username}

cf_clearance = {'cf_clearance': 'ker2YCJ8qmH2ETnaV6TMZTbOHKVNrqxcN60wJ5JxDzE-1773753677-1.2.1.1-5bysJWY7N9Z1Ylf8pizKo27.Q2K1VP55hCB1_.NVnMMAI1pDRwYELbE3Sw1lZKGPfiNRUHjJrPMym3CEuQlBPZtshXqQSYLL34MGDjRLR9tHsoy.i9dukJZc2K78bsSkr08741vWImGm8L.qCqrFIgIbl0IASq87ACoiFjbmVrY9RzrvLtpH4NNDQUQwPMj2_zHpNPNTW93iuUaadLRbrj6yQiBxOVEEHNIWOow3X3FnZXXoAwCVSSfnJlR1yo8q'}

r = requests.post(address, json=body, headers=headers, cookies=cf_clearance)
print('Request: \n' + str(r.request) + ' ' + r.request.url)
print('Headers: ' + str(r.request.headers))
print('Body: ' + str(r.request.body))

print('Response: \n' + str(r.status_code))
print(r.json())