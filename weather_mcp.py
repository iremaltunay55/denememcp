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
API_KEY = os.environ.get("API_KEY", "FgRNkenGLf3Guq67iAtz6ngyx356ojve")
BASE_URL = "http://dataservice.accuweather.com"

# Create an async HTTP client
http_client = httpx.AsyncClient(timeout=10.0)

@mcp.tool()
async def search_location(
    query: Annotated[str, Field(description="City name or postal code to search for")],
    ctx: Context
) -> List[dict]:
    """
    Search for a location by name or postal code and return matching locations.
    Returns a list of locations with their keys, which can be used in other weather tools.
    """
    await ctx.info(f"Searching for location: {query}")

    try:
        # Call the AccuWeather API to search for locations
        url = f"{BASE_URL}/locations/v1/cities/search"
        params = {
            "apikey": API_KEY,
            "q": query
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

    except httpx.HTTPStatusError as e:
        await ctx.error(f"API error: {e.response.status_code} - {e.response.text}")
        return [{"error": f"API error: {e.response.status_code}"}]
    except Exception as e:
        await ctx.error(f"Error searching for location: {str(e)}")
        return [{"error": str(e)}]

@mcp.tool()
async def get_current_weather(
    location_key: Annotated[str, Field(description="AccuWeather location key (use search_location to find)")],
    ctx: Context
) -> dict:
    """
    Get current weather conditions for a location using its AccuWeather location key.
    """
    await ctx.info(f"Getting current weather for location key: {location_key}")

    try:
        # Call the AccuWeather API to get current conditions
        url = f"{BASE_URL}/currentconditions/v1/{location_key}"
        params = {
            "apikey": API_KEY,
            "details": "true"
        }

        response = await http_client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if not data:
            return {"error": "No weather data available"}

        # Extract the current conditions
        current = data[0]

        # Format the results
        result = {
            "temperature": {
                "value": current.get("Temperature", {}).get("Metric", {}).get("Value"),
                "unit": current.get("Temperature", {}).get("Metric", {}).get("Unit")
            },
            "weather_text": current.get("WeatherText"),
            "is_day_time": current.get("IsDayTime"),
            "relative_humidity": current.get("RelativeHumidity"),
            "wind": {
                "speed": {
                    "value": current.get("Wind", {}).get("Speed", {}).get("Metric", {}).get("Value"),
                    "unit": current.get("Wind", {}).get("Speed", {}).get("Metric", {}).get("Unit")
                },
                "direction": current.get("Wind", {}).get("Direction", {}).get("Localized")
            },
            "uv_index": current.get("UVIndex"),
            "uv_index_text": current.get("UVIndexText"),
            "precipitation": current.get("HasPrecipitation"),
            "precipitation_type": current.get("PrecipitationType"),
            "observation_time": current.get("LocalObservationDateTime")
        }

        return result

    except httpx.HTTPStatusError as e:
        await ctx.error(f"API error: {e.response.status_code} - {e.response.text}")
        return {"error": f"API error: {e.response.status_code}"}
    except Exception as e:
        await ctx.error(f"Error getting current weather: {str(e)}")
        return {"error": str(e)}

@mcp.tool()
async def get_forecast(
    location_key: Annotated[str, Field(description="AccuWeather location key (use search_location to find)")],
    ctx: Context,
    days: Annotated[int, Field(description="Number of days for forecast (1-5)", ge=1, le=5)] = 5
) -> dict:
    """
    Get a daily weather forecast for a location using its AccuWeather location key.
    """
    await ctx.info(f"Getting {days}-day forecast for location key: {location_key}")

    try:
        # Call the AccuWeather API to get the forecast
        url = f"{BASE_URL}/forecasts/v1/daily/{days}day/{location_key}"
        params = {
            "apikey": API_KEY,
            "metric": "true"
        }

        response = await http_client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        # Format the results
        result = {
            "headline": data.get("Headline", {}).get("Text"),
            "daily_forecasts": []
        }

        for forecast in data.get("DailyForecasts", []):
            daily = {
                "date": forecast.get("Date"),
                "temperature": {
                    "min": {
                        "value": forecast.get("Temperature", {}).get("Minimum", {}).get("Value"),
                        "unit": forecast.get("Temperature", {}).get("Minimum", {}).get("Unit")
                    },
                    "max": {
                        "value": forecast.get("Temperature", {}).get("Maximum", {}).get("Value"),
                        "unit": forecast.get("Temperature", {}).get("Maximum", {}).get("Unit")
                    }
                },
                "day": {
                    "icon_phrase": forecast.get("Day", {}).get("IconPhrase"),
                    "has_precipitation": forecast.get("Day", {}).get("HasPrecipitation"),
                    "precipitation_type": forecast.get("Day", {}).get("PrecipitationType"),
                    "precipitation_intensity": forecast.get("Day", {}).get("PrecipitationIntensity")
                },
                "night": {
                    "icon_phrase": forecast.get("Night", {}).get("IconPhrase"),
                    "has_precipitation": forecast.get("Night", {}).get("HasPrecipitation"),
                    "precipitation_type": forecast.get("Night", {}).get("PrecipitationType"),
                    "precipitation_intensity": forecast.get("Night", {}).get("PrecipitationIntensity")
                }
            }
            result["daily_forecasts"].append(daily)

        return result

    except httpx.HTTPStatusError as e:
        await ctx.error(f"API error: {e.response.status_code} - {e.response.text}")
        return {"error": f"API error: {e.response.status_code}"}
    except Exception as e:
        await ctx.error(f"Error getting forecast: {str(e)}")
        return {"error": str(e)}

@mcp.tool()
async def get_weather_summary(
    location: Annotated[str, Field(description="City name or postal code")],
    ctx: Context
) -> str:
    """
    Get a complete weather summary for a location, including current conditions and forecast.
    This is a convenience tool that combines search_location, get_current_weather, and get_forecast.
    """
    await ctx.info(f"Getting weather summary for: {location}")

    try:
        # First, search for the location
        locations = await search_location(location, ctx)

        if not locations or "error" in locations[0]:
            return f"Could not find location: {location}"

        # Use the first location
        location_data = locations[0]
        location_key = location_data["key"]
        location_name = f"{location_data['name']}, {location_data['administrative_area']}, {location_data['country']}"

        # Get current weather
        current = await get_current_weather(location_key, ctx)

        if "error" in current:
            return f"Error getting current weather for {location_name}: {current['error']}"

        # Get forecast
        forecast = await get_forecast(location_key, ctx)

        if "error" in forecast:
            return f"Error getting forecast for {location_name}: {forecast['error']}"

        # Format a nice summary
        summary = f"Weather for {location_name}:\n\n"

        # Current conditions
        summary += "CURRENT CONDITIONS:\n"
        summary += f"• Temperature: {current['temperature']['value']}°{current['temperature']['unit']}\n"
        summary += f"• Conditions: {current['weather_text']}\n"
        summary += f"• Humidity: {current['relative_humidity']}%\n"
        summary += f"• Wind: {current['wind']['speed']['value']} {current['wind']['speed']['unit']} {current['wind']['direction']}\n"
        summary += f"• UV Index: {current['uv_index']} ({current['uv_index_text']})\n"

        # Forecast
        summary += "\nFORECAST:\n"
        summary += f"• {forecast['headline']}\n\n"

        for i, day in enumerate(forecast['daily_forecasts']):
            date = day['date'].split('T')[0]
            summary += f"Day {i+1} ({date}):\n"
            summary += f"• Temperature: {day['temperature']['min']['value']}°{day['temperature']['min']['unit']} to {day['temperature']['max']['value']}°{day['temperature']['max']['unit']}\n"
            summary += f"• Day: {day['day']['icon_phrase']}\n"
            summary += f"• Night: {day['night']['icon_phrase']}\n"

            if day['day']['has_precipitation']:
                summary += f"• Precipitation: {day['day']['precipitation_type']} ({day['day']['precipitation_intensity']})\n"

            summary += "\n"

        return summary

    except Exception as e:
        await ctx.error(f"Error getting weather summary: {str(e)}")
        return f"Error getting weather summary: {str(e)}"

if __name__ == "__main__":
    # Get configuration from environment variables
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))

    # Run the server with HTTP transport
    mcp.run(transport="streamable-http", host=host, port=port, path="/mcp")
