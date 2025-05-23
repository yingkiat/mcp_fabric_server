import requests
import certifi
print(certifi.where())
r = requests.get("https://login.microsoftonline.com", timeout=10)
print(r.status_code)