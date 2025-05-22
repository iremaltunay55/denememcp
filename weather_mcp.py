#!/usr/bin/env python3
"""
Weather MCP - A FastMCP server for getting weather information using AccuWeather API
"""

import asyncio
import httpx
import os
from typing import Annotated, List
from pydantic import Field
from fastmcp import FastMCP, Context

# Initialize the FastMCP server
mcp = FastMCP("Weather MCP 🌤️")

# AccuWeather API configuration
DEFAULT_API_KEY = "FgRNkenGLf3Guq67iAtz6ngyx356ojve"
BASE_URL = "http://dataservice.accuweather.com"

# Create an async HTTP client with a shorter timeout for faster responses
http_client = httpx.AsyncClient(timeout=5.0)

def get_api_key(ctx: Context = None) -> str:
    """Get the API key from context or environment variables."""
    # First try to get from context (user configuration)
    if ctx and hasattr(ctx, 'config') and ctx.config and 'API_KEY' in ctx.config:
        return ctx.config['API_KEY']

    # Then try environment variable
    return os.environ.get("API_KEY", DEFAULT_API_KEY)

@mcp.tool()
async def search_location(
    query: Annotated[str, Field(description="City name or postal code to search for")],
    ctx: Context
) -> List[dict]:
    """
    Search for a location by name or postal code and return matching locations.
    Returns a list of locations with their keys, which can be used in other weather tools.
    """
    try:
        # Call the AccuWeather API to search for locations
        url = f"{BASE_URL}/locations/v1/cities/search"
        params = {
            "apikey": get_api_key(ctx),
            "q": query,
            "limit": 5  # Limit to 5 results for faster response
        }

        response = await http_client.get(url, params=params)
        response.raise_for_status()
        locations = response.json()

        # Format the results
        results = []
        for location in locations[:5]:  # Limit to 5 results
            results.append({
                "key": location.get("Key"),
                "name": location.get("LocalizedName"),
                "country": location.get("Country", {}).get("LocalizedName"),
                "administrative_area": location.get("AdministrativeArea", {}).get("LocalizedName")
            })

        return results

    except Exception as e:
        return [{"error": str(e)}]

@mcp.tool()
async def get_current_weather(
    location_key: Annotated[str, Field(description="AccuWeather location key (use search_location to find)")],
    ctx: Context
) -> dict:
    """
    Get current weather conditions for a location using its AccuWeather location key.
    """
    try:
        # Call the AccuWeather API to get current conditions
        url = f"{BASE_URL}/currentconditions/v1/{location_key}"
        params = {
            "apikey": get_api_key(ctx),
            "details": "false"  # Use minimal details for faster response
        }

        response = await http_client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if not data:
            return {"error": "No weather data available"}

        # Extract the current conditions
        current = data[0]

        # Format the results with minimal data for faster response
        result = {
            "temperature": {
                "value": current.get("Temperature", {}).get("Metric", {}).get("Value"),
                "unit": current.get("Temperature", {}).get("Metric", {}).get("Unit")
            },
            "weather_text": current.get("WeatherText"),
            "is_day_time": current.get("IsDayTime"),
            "precipitation": current.get("HasPrecipitation"),
            "observation_time": current.get("LocalObservationDateTime")
        }

        return result

    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def get_forecast(
    location_key: Annotated[str, Field(description="AccuWeather location key (use search_location to find)")],
    ctx: Context,
    days: Annotated[int, Field(description="Number of days for forecast (1-5)", ge=1, le=5)] = 1
) -> dict:
    """
    Get a daily weather forecast for a location using its AccuWeather location key.
    """
    try:
        # Call the AccuWeather API to get the forecast (default to 1 day for faster response)
        url = f"{BASE_URL}/forecasts/v1/daily/{days}day/{location_key}"
        params = {
            "apikey": get_api_key(ctx),
            "metric": "true",
            "details": "false"  # Use minimal details for faster response
        }

        response = await http_client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        # Format the results with minimal data for faster response
        result = {
            "headline": data.get("Headline", {}).get("Text"),
            "daily_forecasts": []
        }

        for forecast in data.get("DailyForecasts", []):
            daily = {
                "date": forecast.get("Date"),
                "temperature": {
                    "min": forecast.get("Temperature", {}).get("Minimum", {}).get("Value"),
                    "max": forecast.get("Temperature", {}).get("Maximum", {}).get("Value")
                },
                "day_phrase": forecast.get("Day", {}).get("IconPhrase"),
                "night_phrase": forecast.get("Night", {}).get("IconPhrase")
            }
            result["daily_forecasts"].append(daily)

        return result

    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def get_weather_summary(
    location: Annotated[str, Field(description="City name or postal code")],
    ctx: Context
) -> str:
    """
    Get a simple weather summary for a location.
    """
    try:
        # First, search for the location
        locations = await search_location(location, ctx)

        if not locations or "error" in locations[0]:
            return f"Could not find location: {location}"

        # Use the first location
        location_data = locations[0]
        location_key = location_data["key"]
        location_name = f"{location_data['name']}, {location_data['country']}"

        # Get current weather
        current = await get_current_weather(location_key, ctx)

        if "error" in current:
            return f"Error getting current weather: {current['error']}"

        # Format a simple summary
        summary = f"Weather for {location_name}:\n\n"
        summary += f"Temperature: {current['temperature']['value']}°{current['temperature']['unit']}\n"
        summary += f"Conditions: {current['weather_text']}\n"

        return summary

    except Exception as e:
        return f"Error getting weather summary: {str(e)}"

if __name__ == "__main__":
    # Get configuration from environment variables
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    path_prefix = os.environ.get("PATH_PREFIX", "/mcp")

    print(f"Starting Weather MCP server on {host}:{port}{path_prefix}")
    print(f"Default API key: {DEFAULT_API_KEY}")
    print(f"Environment API key: {os.environ.get('API_KEY', 'Not set')}")

    # Configure the server with optimized settings
    mcp.configure_context(lambda config: {"API_KEY": config.get("API_KEY", DEFAULT_API_KEY)})

    # Set server options for better performance
    server_options = {
        "transport": "streamable-http",
        "host": host,
        "port": port,
        "path": path_prefix,
        # Add performance options
        "workers": 1,  # Use a single worker for faster startup
        "log_level": "warning",  # Reduce logging overhead
    }

    # Run the server with optimized settings
    mcp.run(**server_options)
