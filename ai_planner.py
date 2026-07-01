import requests
from haversine import haversine, Unit
from dotenv import load_dotenv
from groq import Groq
from sentence_transformers import SentenceTransformer
import os
import json

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
model = SentenceTransformer('all-MiniLM-L6-v2')

def search_places(query):
    query_param = query.replace(" ", "+")
    url = f'https://nominatim.openstreetmap.org/search?q={query_param}&format=json'
    headers = {"User-Agent": "ai-trip-planner-app"}
    response = requests.get(url, headers=headers)
    data = response.json()
    result = [{"name": item['name'], "lat": item['lat'], "lon": item['lon'], "display_name": item['display_name']} for item in data]
    return json.dumps(result)

def get_distance(place1: dict, place2: dict):
    first_place = (float(place1["lat"]), float(place1["lon"]))
    second_place = (float(place2["lat"]), float(place2["lon"]))
    distance_km = haversine(first_place, second_place, unit=Unit.KILOMETERS)
    return f'{distance_km:.2f} km'

# place1 = search_places("Артем Астана")[0] 
# place2 = search_places("Мега Астана")[0]
# distance = get_distance(place1, place2)  

available_functions = {
    "search_places": search_places,
    "get_distance": get_distance
}

tools = [
    {
        "type":"function",
        "function": {
            "name": "search_places",
            "description": "Выдает инфо по местности: координаты, наименования",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Название местности которая нас интересует"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_distance",
            "description": "Выдает дистанцию между 2 местностями в километрах",
            "parameters": {
                "type": "object",
                "properties": {
                    "place1": {
                        "type": "object",
                        "description": "словарь в котором есть координаты lat, lon"
                    },
                    "place2": {
                        "type": "object",
                        "description": "словарь в котором есть координаты lat, lon"
                    }
                },
                "required": ["place1", "place2"]
            }
        }
    }
]

messages = [{
    "role": "system", "content":"Пользователь турист, выдавай инфо достопримечательностей местности, запрещяется советовать харамные заведения"
    }]
user_message = { "role": "user", "content":"Я буду два дня в Караганде, куда сходить?"}
messages.append(user_message)
def get_model_answer():
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=messages,
        tools=tools
    )
    return response.choices[0].message

message = get_model_answer()
if message.tool_calls == None:
    print(message)
else:
    while message.tool_calls:
        func_name = message.tool_calls[0].function.name
        func_argument = json.loads(message.tool_calls[0].function.arguments)
        real_func = available_functions[func_name]
        result = real_func(**func_argument)
        message_user = {"role": "tool", "content": result, "tool_call_id": message.tool_calls[0].id}
        messages.append(message)
        messages.append(message_user)
        message = get_model_answer()
        print(message)