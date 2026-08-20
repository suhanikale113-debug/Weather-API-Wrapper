import time

CACHE = {}

TTL = 600      # 10 minutes


def get(city):
    city = city.lower()

    if city not in CACHE:
        return None

    data = CACHE[city]

    current = time.time()

    if current - data["timestamp"] > TTL:
        del CACHE[city]
        return None

    return data


def set(city, weather):
    city = city.lower()

    CACHE[city] = {
        "weather": weather,
        "timestamp": time.time()
    }


def delete(city):
    city = city.lower()

    if city in CACHE:
        del CACHE[city]