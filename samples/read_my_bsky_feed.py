print("Username: ")

username = input()
print("Password: ")
password = input()

from atproto import Client

client = Client()
session = client.login(username, password)

data = client.get_posts()
print(data)