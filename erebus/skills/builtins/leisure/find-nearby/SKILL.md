---
name: find-nearby
description: Find nearby restaurants, cafes, bars, and services using OpenStreetMap — no API keys required.
metadata:
  version: "1.0.0"
  author: erebus
  tags: ["leisure", "places", "restaurants", "maps", "local"]
---

# Find Nearby Places

Use this skill to find nearby places and services using OpenStreetMap.

## When to Use

- User asks for restaurants, cafes, bars nearby
- User needs to find a pharmacy, hospital, or service
- User wants local recommendations
- User asks about places in a specific area

## API (Overpass / Nominatim)

### Geocode Location
```bash
curl -s "https://nominatim.openstreetmap.org/search?q={location}&format=json&limit=1"
```

### Find Places Near Coordinates
```bash
curl -s "https://overpass-api.de/api/interpreter" \
  --data-urlencode "data=[out:json][timeout:10];node[amenity=restaurant](around:1000,{lat},{lon});out body 10;"
```

### Supported Amenities
restaurant, cafe, bar, pub, fast_food, pharmacy, hospital, bank, atm, fuel, parking, school, library, cinema, theatre

## Process

1. **Locate**: Geocode the user's location or area
2. **Search**: Query Overpass for the requested amenity type
3. **Filter**: Apply distance and rating filters
4. **Present**: Format results with name, address, distance
