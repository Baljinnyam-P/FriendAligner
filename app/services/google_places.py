import os
import time
import requests
from typing import List, Dict

# Endpoints
GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
NEARBY_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"

def _get_api_key() -> str:
    key = os.getenv("GOOGLE_PLACES_API_KEY")
    if not key:
        raise RuntimeError("GOOGLE_PLACES_API_KEY not set in environment")
    return key

# Geocode zip code to lat/lng
def geocode_zip(zip_code: str) -> Dict:
    key = _get_api_key()
    resp = requests.get(GEOCODE_URL, params={"address": zip_code, "key": key}, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("results"):
        raise ValueError("Could not geocode zip code")
    loc = data["results"][0]["geometry"]["location"]
    return {"lat": loc["lat"], "lng": loc["lng"]}

#Find places by zip code and keyword
def find_places(zip_code: str, keyword: str, max_results: int = 10, radius: int = 5000) -> List[Dict]:
    key = _get_api_key()
    latlng = geocode_zip(zip_code)

    params = {
        "location": f"{latlng['lat']},{latlng['lng']}",
        "radius": radius,           
        "keyword": keyword,
        "key": key,
    }

    results = []
    url = NEARBY_SEARCH_URL
    while True:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        for r in data.get("results", []):
            simplified = {
                "name": r.get("name"),
                "rating": r.get("rating"),
                "user_ratings_total": r.get("user_ratings_total"),
                "vicinity": r.get("vicinity"),
                "formatted_address": r.get("formatted_address"),  # may be None for nearby search
                "place_id": r.get("place_id"),
                "geometry": r.get("geometry"),  
                "types": r.get("types", [])
            }
            results.append(simplified)
            if len(results) >= max_results:
                break

        # stop if we got enough
        if len(results) >= max_results:
            break
        next_token = data.get("next_page_token")
        if not next_token:
            break

        params = {"pagetoken": next_token, "key": key}
        time.sleep(2)

    # sort by rating 
    results_sorted = sorted(results, key=lambda x: (x.get("rating") or 0), reverse=True)
    return results_sorted[:max_results]

def get_place_details(place_id: str) -> Dict:
    """Fetch detailed info for a place_id (name, address, location)."""
    key = _get_api_key()
    params = {
        "place_id": place_id,
        "key": key,
        "fields": "name,formatted_address,geometry,place_id,website,formatted_phone_number,opening_hours,photos,reviews,rating,types"
    }
    resp = requests.get(DETAILS_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if data.get("status") != "OK":
        raise ValueError(f"Place details lookup failed: {data.get('status')}")
    result = data.get("result", {})
    # Photos: return photo_reference only (actual image requires another API call)
    photos = [p.get("photo_reference") for p in result.get("photos", [])]
    return {
        "name": result.get("name"),
        "formatted_address": result.get("formatted_address"),
        "place_id": result.get("place_id"),
        "location": result.get("geometry", {}).get("location"),
        "website": result.get("website"),
        "formatted_phone_number": result.get("formatted_phone_number"),
        "opening_hours": result.get("opening_hours"),
        "photos": photos,
        "reviews": result.get("reviews", []),
        "rating": result.get("rating"),
        "types": result.get("types", [])
    }
