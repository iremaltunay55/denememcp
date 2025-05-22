# Weather MCP

A Minimum Consumable Product (MCP) for getting weather information using the AccuWeather API.

## Features

- Search for locations by name or postal code
- Get current weather conditions for a location
- Get a 1-5 day weather forecast for a location
- Get a complete weather summary including current conditions and forecast

## Requirements

- Python 3.7+
- FastMCP
- httpx

## Installation

1. Install the required packages:

```bash
pip install fastmcp httpx
```

2. Run the MCP server:

```bash
python weather_mcp.py
```

## Usage

The MCP server provides the following tools:

### search_location

Search for a location by name or postal code.

Parameters:
- `query`: City name or postal code to search for

Returns:
- A list of matching locations with their AccuWeather location keys

### get_current_weather

Get current weather conditions for a location.

Parameters:
- `location_key`: AccuWeather location key (use search_location to find)

Returns:
- Current weather conditions including temperature, weather text, humidity, wind, etc.

### get_forecast

Get a daily weather forecast for a location.

Parameters:
- `location_key`: AccuWeather location key (use search_location to find)
- `days`: Number of days for forecast (1-5, default: 5)

Returns:
- Weather forecast including temperature, conditions, precipitation, etc.

### get_weather_summary

Get a complete weather summary for a location, including current conditions and forecast.

Parameters:
- `location`: City name or postal code

Returns:
- A formatted text summary of the current weather and forecast

## Example

```python
import asyncio
from fastmcp import Client

client = Client("weather_mcp.py")

async def get_weather():
    async with client:
        # Get a complete weather summary for Istanbul
        result = await client.call_tool("get_weather_summary", {"location": "Istanbul"})
        print(result[0].text)

asyncio.run(get_weather())
```

## API Key

This MCP uses the AccuWeather API with the following API key:

```
FgRNkenGLf3Guq67iAtz6ngyx356ojve
```

Note: The AccuWeather API has rate limits. For production use, consider obtaining your own API key from [AccuWeather](https://developer.accuweather.com/).
