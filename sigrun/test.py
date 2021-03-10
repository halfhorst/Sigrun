import requests

# url = "https://discord.com/api/v8/applications/816920217795952640/guilds/358815703186407434/commands"
url = "https://discord.com/api/v8/applications/816920217795952640/commands"

json = {
    "name": "uptime",
    "description": "Get Valheim server uptime",
}

# For authorization, you can use either your bot token
headers = {
    "Authorization":
    "Bot ODE2OTIwMjE3Nzk1OTUyNjQw.YEB-PQ.6DZzD0QXI1uhtTFT4R8ciHK-0Bg"
}

# or a client credentials token for your app with the applications.commands.update scope
# headers = {"Authorization": "Bearer abcdefg"}

r = requests.post(url, headers=headers, json=json)
# r = requests.get(url, headers=headers)

print(r.json())

# r = requests.delete(url + ("/819092103434862592"), headers=headers)

# print(r)