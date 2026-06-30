import requests
from haversine import haversine, Unit

def search_places(query):
    query_param = query.replace(" ", "+")
    url = f'https://nominatim.openstreetmap.org/search?q={query_param}&format=json'
    headers = {"User-Agent": "ai-trip-planner-app"}
    response = requests.get(url, headers=headers)
    data = response.json()
    result = [{"name": item['name'], "lat": item['lat'], "lon": item['lon'], "display_name": item['display_name']} for item in data]
    return result

def get_distance(place1: dict, place2: dict):
    first_place = (float(place1["lat"]), float(place1["lon"]))
    second_place = (float(place2["lat"]), float(place2["lon"]))
    distance_km = haversine(first_place, second_place, unit=Unit.KILOMETERS)
    return f'{distance_km:.2f} km'

place1 = search_places("Артем Астана")[0] 
place2 = search_places("Мега Астана")[0]
distance = get_distance(place1, place2)  
print(distance)