from fastapi import FastAPI, HTTPException, Query
import httpx
import time

app = FastAPI(title="Weather API Wrapper")


cache = {}

# Cache Time (10 minutes)
CACHE_TTL = 600

# Statistics
cache_hits = 0
cache_misses = 0



async def get_location(city: str):

    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"

    async with httpx.AsyncClient() as client:

        response = await client.get(url)

    if response.status_code != 200:
        raise HTTPException(500, "Location service unavailable")

    data = response.json()

    if "results" not in data:
        raise HTTPException(404, "City not found")

    result = data["results"][0]

    return result["latitude"], result["longitude"]





async def fetch_weather(city: str):

    lat, lon = await get_location(city)

    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}"
        f"&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,"
        f"wind_speed_10m"
    )

    async with httpx.AsyncClient(timeout=10) as client:

        response = await client.get(url)

    if response.status_code != 200:
        raise HTTPException(500, "Weather provider unavailable")

    data = response.json()

    current = data["current"]

    return {
        "temperature": current["temperature_2m"],
        "humidity": current["relative_humidity_2m"],
        "wind_speed": current["wind_speed_10m"]
    }



@app.get("/weather")

async def weather(
    city: str = Query(..., min_length=2)
):

    global cache_hits
    global cache_misses

    city = city.strip().lower()

    current_time = time.time()


    if city in cache:

        weather_data = cache[city]

        age = current_time - weather_data["timestamp"]

        if age < CACHE_TTL:

            cache_hits += 1

            return {
                "city": city.title(),
                "from_cache": True,
                "cache_age_seconds": round(age),
                "weather": weather_data["data"]
            }

   
    cache_misses += 1

    fresh_weather = await fetch_weather(city)

    cache[city] = {
        "timestamp": current_time,
        "data": fresh_weather
    }

    return {
        "city": city.title(),
        "from_cache": False,
        "cache_age_seconds": 0,
        "weather": fresh_weather
    }




@app.delete("/cache")

async def clear_cache(city: str):

    city = city.lower()

    if city in cache:
        del cache[city]
        return {"message": "Cache deleted"}

    raise HTTPException(404, "City not in cache")



@app.get("/stats")

async def stats():

    total = cache_hits + cache_misses

    hit_ratio = 0

    if total > 0:
        hit_ratio = round((cache_hits / total) * 100, 2)

    return {
        "cache_hits": cache_hits,
        "cache_misses": cache_misses,
        "hit_ratio": f"{hit_ratio} %",
        "cached_cities": list(cache.keys())
    }