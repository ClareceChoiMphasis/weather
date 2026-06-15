# Design Document

## Introduction

This document describes the architecture and implementation design for the `weather-city-forecast` CLI tool — a Python command-line application that retrieves and displays current weather and a 14-day forecast for a given city using the OpenWeatherMap API (free tier).

---

## Architecture Overview

The tool follows a simple layered architecture with clear separation between input handling, API communication, data transformation, and output rendering. All layers are stateless pure functions where possible to maximise testability.

```
┌─────────────────────────────────────┐
│              CLI Entry Point         │  main.py / cli.py
│   (argument parsing, orchestration)  │
└────────────────┬────────────────────┘
                 │
        ┌────────▼────────┐
        │   Input Layer    │  city resolution, API key reading
        └────────┬─────────┘
                 │
        ┌────────▼────────┐
        │   API Client     │  HTTP requests to OpenWeatherMap
        └────────┬─────────┘
                 │
        ┌────────▼────────┐
        │  Data Models     │  dataclasses for weather/forecast
        └────────┬─────────┘
                 │
        ┌────────▼────────┐
        │   Formatter      │  pure rendering functions
        └─────────────────┘
```

---

## Module Structure

```
weather/
├── main.py          # Entry point — wires all layers together
├── cli.py           # CLI argument parsing and interactive prompt
├── config.py        # API key reading from environment
├── client.py        # OpenWeatherMap HTTP client
├── models.py        # Dataclasses: CurrentWeather, ForecastDay
├── formatter.py     # Pure output formatting functions
└── errors.py        # Custom exception types
```

---

## Components

### `cli.py` — City Input Resolution

Responsible for obtaining a city name either from the CLI argument or via an interactive prompt.

```python
import argparse

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments. city is optional positional arg."""
    parser = argparse.ArgumentParser(
        description="Show current weather and 14-day forecast for a city."
    )
    parser.add_argument("city", nargs="?", default=None, help="City name")
    return parser.parse_args()

def prompt_for_city() -> str:
    """Repeatedly prompt until the user provides a non-empty city name."""
    while True:
        city = input("Enter city name: ").strip()
        if city:
            return city

def resolve_city(args: argparse.Namespace) -> str:
    """Return city from args or fall back to interactive prompt."""
    if args.city:
        return args.city
    return prompt_for_city()
```

### `config.py` — API Key Configuration

```python
import os
from .errors import MissingApiKeyError

def get_api_key() -> str:
    """Read OPENWEATHERMAP_API_KEY from environment. Raises on missing/empty."""
    key = os.environ.get("OPENWEATHERMAP_API_KEY", "").strip()
    if not key:
        raise MissingApiKeyError(
            "OPENWEATHERMAP_API_KEY is not set. "
            "Export it before running: export OPENWEATHERMAP_API_KEY=<your_key>"
        )
    return key
```

### `models.py` — Data Models

```python
from dataclasses import dataclass

@dataclass
class CurrentWeather:
    city: str
    country: str
    temperature_celsius: float
    condition: str
    humidity_percent: int
    wind_speed_ms: float

@dataclass
class ForecastDay:
    date: str          # ISO-8601 date string: YYYY-MM-DD
    high_celsius: float
    low_celsius: float
    condition: str
```

### `client.py` — OpenWeatherMap API Client

The free tier exposes two relevant endpoints:

| Endpoint | Purpose |
|---|---|
| `GET /data/2.5/weather` | Current weather by city name |
| `GET /data/2.5/forecast` | 3-hour step forecast (5 days on free tier) |

> **Free tier limitation**: The `/forecast` endpoint returns 3-hour interval data for 5 days (40 entries). The tool aggregates these into daily summaries. Fewer than 14 days is handled gracefully per Requirement 4.3.

```python
import requests
from .models import CurrentWeather, ForecastDay
from .errors import CityNotFoundError, ApiError, NetworkError

BASE_URL = "https://api.openweathermap.org/data/2.5"

def fetch_current_weather(city: str, api_key: str) -> CurrentWeather:
    """Fetch current weather for city. Raises on API/network errors."""
    try:
        response = requests.get(
            f"{BASE_URL}/weather",
            params={"q": city, "appid": api_key, "units": "metric"},
            timeout=10,
        )
    except requests.ConnectionError as exc:
        raise NetworkError(f"Network error: {exc}") from exc

    if response.status_code == 404:
        raise CityNotFoundError(f"City not found: '{city}'")
    if not response.ok:
        raise ApiError(f"API error: HTTP {response.status_code}")

    data = response.json()
    return CurrentWeather(
        city=data["name"],
        country=data["sys"]["country"],
        temperature_celsius=data["main"]["temp"],
        condition=data["weather"][0]["description"],
        humidity_percent=data["main"]["humidity"],
        wind_speed_ms=data["wind"]["speed"],
    )

def fetch_forecast(city: str, api_key: str) -> list[ForecastDay]:
    """Fetch forecast for city aggregated into daily entries."""
    try:
        response = requests.get(
            f"{BASE_URL}/forecast",
            params={"q": city, "appid": api_key, "units": "metric"},
            timeout=10,
        )
    except requests.ConnectionError as exc:
        raise NetworkError(f"Network error: {exc}") from exc

    if response.status_code == 404:
        raise CityNotFoundError(f"City not found: '{city}'")
    if not response.ok:
        raise ApiError(f"API error: HTTP {response.status_code}")

    return _aggregate_forecast(response.json()["list"])

def _aggregate_forecast(entries: list[dict]) -> list[ForecastDay]:
    """Aggregate 3-hour forecast entries into per-day high/low summaries."""
    from collections import defaultdict
    days: dict[str, dict] = defaultdict(lambda: {"highs": [], "lows": [], "conditions": []})

    for entry in entries:
        date = entry["dt_txt"][:10]  # YYYY-MM-DD
        days[date]["highs"].append(entry["main"]["temp_max"])
        days[date]["lows"].append(entry["main"]["temp_min"])
        days[date]["conditions"].append(entry["weather"][0]["description"])

    result = []
    for date in sorted(days.keys()):
        d = days[date]
        result.append(ForecastDay(
            date=date,
            high_celsius=max(d["highs"]),
            low_celsius=min(d["lows"]),
            condition=max(set(d["conditions"]), key=d["conditions"].count),  # mode
        ))
    return result
```

### `formatter.py` — Output Rendering

Pure functions that convert data models to terminal strings.

```python
from .models import CurrentWeather, ForecastDay

def format_current_weather(weather: CurrentWeather) -> str:
    lines = [
        f"=== Current Weather: {weather.city}, {weather.country} ===",
        f"  Temperature : {weather.temperature_celsius:.1f} °C",
        f"  Condition   : {weather.condition.capitalize()}",
        f"  Humidity    : {weather.humidity_percent}%",
        f"  Wind Speed  : {weather.wind_speed_ms:.1f} m/s",
    ]
    return "\n".join(lines)

def format_forecast(days: list[ForecastDay]) -> str:
    header = "=== 14-Day Forecast ==="
    rows = [header]
    for day in days:
        rows.append(
            f"  {day.date}  High: {day.high_celsius:.1f}°C  "
            f"Low: {day.low_celsius:.1f}°C  {day.condition.capitalize()}"
        )
    return "\n".join(rows)
```

### `errors.py` — Custom Exceptions

```python
class WeatherToolError(Exception):
    """Base exception for weather tool errors."""

class MissingApiKeyError(WeatherToolError):
    pass

class CityNotFoundError(WeatherToolError):
    pass

class ApiError(WeatherToolError):
    pass

class NetworkError(WeatherToolError):
    pass
```

### `main.py` — Entry Point

```python
import sys
from .cli import parse_args, resolve_city
from .config import get_api_key
from .client import fetch_current_weather, fetch_forecast
from .formatter import format_current_weather, format_forecast
from .errors import WeatherToolError

def main() -> None:
    try:
        api_key = get_api_key()
        args = parse_args()
        city = resolve_city(args)

        current = fetch_current_weather(city, api_key)
        forecast = fetch_forecast(city, api_key)

        print(format_current_weather(current))
        print()
        print(format_forecast(forecast))
        sys.exit(0)
    except WeatherToolError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
```

---

## Data Flow

```
User invokes CLI
      │
      ▼
parse_args() → city arg present?
      │ No                │ Yes
      ▼                   │
prompt_for_city()         │
      │                   │
      └──────────┬────────┘
                 ▼
          get_api_key()
                 │
                 ▼
     fetch_current_weather(city, key)
                 │
                 ▼
     fetch_forecast(city, key)
                 │
                 ▼
     format_current_weather() → print
     format_forecast()         → print
                 │
                 ▼
           sys.exit(0)

  On any WeatherToolError → print to stderr, sys.exit(1)
```

---

## Error Handling Strategy

| Condition | Exception Raised | Exit Code | Output |
|---|---|---|---|
| `OPENWEATHERMAP_API_KEY` missing/empty | `MissingApiKeyError` | 1 | stderr message with instructions |
| City not found (HTTP 404) | `CityNotFoundError` | 1 | stderr: city not found message |
| Network connection failure | `NetworkError` | 1 | stderr: connectivity problem description |
| Unexpected HTTP error | `ApiError` | 1 | stderr: message including HTTP status code |
| Successful execution | — | 0 | stdout: current weather + forecast |

All domain exceptions inherit from `WeatherToolError`, allowing a single `except` block in `main.py` to handle all error cases uniformly.

---

## OpenWeatherMap Free Tier Constraints

- The `/forecast` endpoint on the free tier returns data in 3-hour intervals for **5 days** (40 data points), not 14. The tool aggregates these into daily summaries and displays however many days are available, satisfying Requirement 4.3 without error.
- The `/weather` endpoint provides real-time current conditions and is fully supported on the free tier.
- Temperature units are requested as `metric` so values arrive in °C and wind speed in m/s, requiring no client-side conversion.

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Non-empty city argument is used without prompting

*For any* non-empty city string supplied as a CLI positional argument, `resolve_city` SHALL return that exact string and SHALL NOT invoke the interactive prompt.

**Validates: Requirements 1.1**

---

### Property 2: Interactive prompt loops until non-empty input

*For any* sequence of zero or more empty strings followed by a non-empty city name entered at the prompt, `prompt_for_city` SHALL return the first non-empty string and SHALL have called `input` exactly `(number of empty strings + 1)` times.

**Validates: Requirements 1.3, 1.4**

---

### Property 3: Current weather output contains all required fields

*For any* `CurrentWeather` data object, `format_current_weather` SHALL produce a string that contains the city name, country code, temperature value, condition description, humidity value, and wind speed value.

**Validates: Requirements 3.2**

---

### Property 4: Forecast output contains one entry per day with all required fields

*For any* list of `ForecastDay` objects (length 1 to 14), `format_forecast` SHALL produce a string with exactly one line per day that contains the date, a high temperature value, a low temperature value, and the condition description — with no error regardless of list length.

**Validates: Requirements 4.2, 4.3**

---

### Property 5: Unexpected HTTP status codes produce messages containing the status code

*For any* HTTP error status code returned by the OpenWeatherMap API (not 200, not 404), the resulting `ApiError` message SHALL contain that numeric status code, and the tool SHALL exit with a non-zero exit code.

**Validates: Requirements 6.2**

---

### Property 6: API client passes city name in request parameters

*For any* non-empty city string and valid API key, `fetch_current_weather` and `fetch_forecast` SHALL each make an HTTP GET request whose query parameters include the supplied city name.

**Validates: Requirements 3.1, 4.1**

---

### Property 7: Forecast aggregation produces valid daily summaries

*For any* list of 3-hour forecast entries spanning one or more days, `_aggregate_forecast` SHALL produce a list of `ForecastDay` objects where each entry's `high_celsius` is greater than or equal to its `low_celsius`, and the dates are strictly ascending with no duplicates.

**Validates: Requirements 4.2**
