import requests

def search(query):
    url = "http://localhost:8080/search"
    params = {"q": query, "format": "json"}
    return requests.get(url, params=params).json()

print(search("delhi air quality diwali"))
