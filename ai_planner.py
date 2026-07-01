import requests
from haversine import haversine, Unit
from dotenv import load_dotenv
from groq import Groq
from sentence_transformers import SentenceTransformer
import os
import json
import telebot

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
model = SentenceTransformer('all-MiniLM-L6-v2')
bot = telebot.TeleBot(os.getenv('TELEGRAM_BOT_TOKEN'))

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
    "role": "system", "content":"Пользователь турист, выдавай инфо достопримечательностей местности, запрещяется советовать харамные заведения,запрещяется говорить на темы которые не относиться у туризму, не отоброжай координаты а только расстояние"
    }]

def get_model_answer():
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=messages,
        tools=tools
    )
    return response.choices[0].message

def handler_answer(question: str):
    user_message = { "role": "user", "content": f'{question}'}
    messages.append(user_message)
    message = get_model_answer()
    if message.tool_calls == None:
         pass
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
    return message.content

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, """👋 Привет! Я — AI Trip Planner!

🗺 Помогу спланировать маршрут по всем городам.

Просто напиши мне, например:
- "Я буду 2 дня в Алматы, куда сходить?"
- "Что посмотреть в Астане за 1 день с семьёй?"
- "Куда сходить в Шымкенте без машины?"

И я составлю маршрут специально для тебя! 🇰🇿
""")
    
def send_long_message(chat_id, text):
    max_length = 4000
    for i in range(0, len(text), max_length):
        chunk = text[i:i + max_length]
        bot.send_message(chat_id, chunk)
    
@bot.message_handler(func=lambda m: not m.text.startswith('/'))
def handle_message(message):
    try:
        answer = handler_answer(message.text)
        send_long_message(message.chat.id, answer)
    except Exception as e:
        print(f"ОШИБКА: {e}")  # ← добавь эту строку
        bot.send_message(message.chat.id, 
        "⚠️ Временная ошибка, попробуй через минуту")

bot.polling(interval=1, timeout=20, non_stop=True)