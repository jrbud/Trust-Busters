import requests
API_KEY = "WE NEED ONE"
domain = "cocacola.com"

headers = {"Authorization": f"Bearer {API_KEY}"}
r = requests.get(f"https://api.brandfetch.io/v2/brands/{domain}", headers=headers, timeout=10)
r.raise_for_status()
print(r.json())
