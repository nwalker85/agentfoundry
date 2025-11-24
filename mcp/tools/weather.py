"""Weather Tool Implementation.

Uses Open-Meteo API for free weather data (no API key required).
"""

from __future__ import annotations

import httpx
from pydantic import BaseModel, Field

from mcp.schemas import ToolResponse


# City coordinates lookup (expandable)
CITY_COORDINATES = {
    # North America
    "toronto": (43.65, -79.38),
    "new york": (40.71, -74.01),
    "los angeles": (34.05, -118.24),
    "chicago": (41.88, -87.63),
    "vancouver": (49.28, -123.12),
    "montreal": (45.50, -73.57),
    "san francisco": (37.77, -122.42),
    "seattle": (47.61, -122.33),
    "boston": (42.36, -71.06),
    "miami": (25.76, -80.19),
    "dallas": (32.78, -96.80),
    "houston": (29.76, -95.37),
    "atlanta": (33.75, -84.39),
    "denver": (39.74, -104.99),
    "phoenix": (33.45, -112.07),
    # Europe
    "london": (51.51, -0.13),
    "paris": (48.86, 2.35),
    "berlin": (52.52, 13.41),
    "amsterdam": (52.37, 4.90),
    "madrid": (40.42, -3.70),
    "rome": (41.90, 12.50),
    "barcelona": (41.39, 2.17),
    "vienna": (48.21, 16.37),
    "prague": (50.08, 14.44),
    "dublin": (53.35, -6.26),
    # Asia Pacific
    "tokyo": (35.68, 139.69),
    "singapore": (1.35, 103.82),
    "hong kong": (22.32, 114.17),
    "sydney": (33.87, 151.21),
    "melbourne": (-37.81, 144.96),
    "seoul": (37.57, 126.98),
    "mumbai": (19.08, 72.88),
    "delhi": (28.61, 77.21),
    "bangkok": (13.76, 100.50),
    "shanghai": (31.23, 121.47),
    "beijing": (39.90, 116.41),
    # South America
    "sao paulo": (-23.55, -46.63),
    "rio de janeiro": (-22.91, -43.17),
    "buenos aires": (-34.60, -58.38),
    "bogota": (4.71, -74.07),
    "lima": (-12.05, -77.04),
    # Africa & Middle East
    "cairo": (30.04, 31.24),
    "dubai": (25.20, 55.27),
    "johannesburg": (-26.20, 28.04),
    "cape town": (-33.93, 18.42),
    "tel aviv": (32.09, 34.78),
}

# Weather code descriptions (WMO codes)
WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


class WeatherRequest(BaseModel):
    """Request to get current weather for a city."""

    city: str = Field(..., description="City name (e.g., 'Toronto', 'New York', 'London')")
    units: str = Field(default="celsius", description="Temperature units: 'celsius' or 'fahrenheit'")


class WeatherData(BaseModel):
    """Weather data response."""

    city: str
    temperature: float
    temperature_unit: str
    feels_like: float | None = None
    humidity: int | None = None
    wind_speed: float | None = None
    wind_unit: str = "km/h"
    conditions: str
    weather_code: int
    latitude: float
    longitude: float


class WeatherTool:
    """MCP-facing wrapper for weather queries using Open-Meteo API."""

    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    def __init__(self) -> None:
        self.client = httpx.AsyncClient(timeout=10.0)

    async def get_weather(self, request: WeatherRequest) -> ToolResponse:
        """Get current weather for a city."""
        try:
            # Normalize city name for lookup
            city_lower = request.city.lower().strip()

            # Look up coordinates
            if city_lower not in CITY_COORDINATES:
                # Try partial match
                matches = [c for c in CITY_COORDINATES if city_lower in c or c in city_lower]
                if matches:
                    city_lower = matches[0]
                else:
                    return ToolResponse(
                        success=False,
                        error=f"City '{request.city}' not found. Available cities: {', '.join(sorted(CITY_COORDINATES.keys())[:20])}..."
                    )

            lat, lon = CITY_COORDINATES[city_lower]

            # Build API request
            temp_unit = "fahrenheit" if request.units.lower() == "fahrenheit" else "celsius"
            params = {
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m",
                "temperature_unit": temp_unit,
                "wind_speed_unit": "kmh",
            }

            response = await self.client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

            current = data.get("current", {})
            weather_code = current.get("weather_code", 0)

            weather_data = WeatherData(
                city=request.city.title(),
                temperature=current.get("temperature_2m", 0),
                temperature_unit="°F" if temp_unit == "fahrenheit" else "°C",
                feels_like=current.get("apparent_temperature"),
                humidity=current.get("relative_humidity_2m"),
                wind_speed=current.get("wind_speed_10m"),
                conditions=WEATHER_CODES.get(weather_code, "Unknown"),
                weather_code=weather_code,
                latitude=lat,
                longitude=lon,
            )

            return ToolResponse(
                success=True,
                data=weather_data.dict()
            )

        except httpx.HTTPStatusError as e:
            return ToolResponse(success=False, error=f"API error: {e.response.status_code}")
        except httpx.RequestError as e:
            return ToolResponse(success=False, error=f"Request failed: {str(e)}")
        except Exception as e:
            return ToolResponse(success=False, error=str(e))

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()


# Convenience function for direct use
async def get_current_weather(city: str, units: str = "celsius") -> ToolResponse:
    """Get current weather for a city.

    Args:
        city: City name (e.g., 'Toronto', 'New York', 'London')
        units: Temperature units - 'celsius' or 'fahrenheit'

    Returns:
        ToolResponse with weather data including temperature, humidity, conditions, etc.
    """
    tool = WeatherTool()
    try:
        return await tool.get_weather(WeatherRequest(city=city, units=units))
    finally:
        await tool.close()
