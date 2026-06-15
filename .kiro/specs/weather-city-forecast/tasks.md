# Implementation Plan: weather-city-forecast

## Overview

Build a Python CLI tool that fetches and displays current weather and a 5-day (free tier) forecast for a given city using the OpenWeatherMap API. The implementation follows a layered architecture: CLI input → API client → data models → formatter → output.

## Tasks

- [ ] 1. Set up project structure and core types
  - [ ] 1.1 Create the `weather/` package with all module stubs
    - Create `weather/__init__.py`, `weather/errors.py`, `weather/models.py`
    - Define all custom exception classes in `errors.py`: `WeatherToolError`, `MissingApiKeyError`, `CityNotFoundError`, `ApiError`, `NetworkError`
    - Define `CurrentWeather` and `ForecastDay` dataclasses in `models.py`
    - Create a `pyproject.toml` (or `setup.py`) with `requests` as a dependency and a `weather` console script entry point pointing to `weather.main:main`
    - _Requirements: 2.1, 3.2, 4.2_

- [ ] 2. Implement the CLI input layer
  - [ ] 2.1 Implement `cli.py` — argument parsing and city resolution
    - Write `parse_args()`, `prompt_for_city()`, and `resolve_city()` as specified in the design
    - `prompt_for_city` must loop until a non-empty string is entered
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [ ]* 2.2 Write property test for non-empty city arg bypass (Property 1)
    - **Property 1: Non-empty city argument is used without prompting**
    - For any non-empty city string passed as a positional arg, `resolve_city` returns it unchanged and `input` is never called
    - **Validates: Requirements 1.1**

  - [ ]* 2.3 Write property test for interactive prompt loop (Property 2)
    - **Property 2: Interactive prompt loops until non-empty input**
    - For any sequence of N empty strings followed by one non-empty string, `prompt_for_city` returns the non-empty string and calls `input` exactly N+1 times
    - **Validates: Requirements 1.3, 1.4**

- [ ] 3. Implement API key configuration
  - [ ] 3.1 Implement `config.py` — read API key from environment
    - Write `get_api_key()` that reads `OPENWEATHERMAP_API_KEY` and raises `MissingApiKeyError` if missing or empty
    - _Requirements: 2.1, 2.2_

  - [ ]* 3.2 Write unit tests for `get_api_key`
    - Test: key present and non-empty → returned correctly
    - Test: variable not set → raises `MissingApiKeyError`
    - Test: variable set to empty string → raises `MissingApiKeyError`
    - _Requirements: 2.1, 2.2_

- [ ] 4. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Implement the OpenWeatherMap API client
  - [ ] 5.1 Implement `fetch_current_weather` in `client.py`
    - Send GET `/data/2.5/weather` with `q`, `appid`, `units=metric`; parse response into `CurrentWeather`
    - Raise `CityNotFoundError` on 404, `ApiError` on other non-2xx, `NetworkError` on `requests.ConnectionError`
    - _Requirements: 3.1, 5.1, 5.2, 6.1, 6.2_

  - [ ]* 5.2 Write property test for city name in request parameters (Property 6 — current weather)
    - **Property 6 (current): API client passes city name in request parameters**
    - For any non-empty city string and API key, the outgoing GET request's query params include the exact city string
    - **Validates: Requirements 3.1**

  - [ ] 5.3 Implement `fetch_forecast` and `_aggregate_forecast` in `client.py`
    - Send GET `/data/2.5/forecast`; aggregate 3-hour entries into per-day `ForecastDay` objects (max daily temp, min daily temp, mode condition)
    - Apply same error handling as `fetch_current_weather`
    - _Requirements: 4.1, 4.2, 4.3, 5.1, 5.2, 6.1, 6.2_

  - [ ]* 5.4 Write property test for forecast aggregation validity (Property 7)
    - **Property 7: Forecast aggregation produces valid daily summaries**
    - For any list of 3-hour entries spanning one or more days, `_aggregate_forecast` returns `ForecastDay` objects where `high_celsius >= low_celsius`, dates are strictly ascending, and there are no duplicate dates
    - **Validates: Requirements 4.2**

  - [ ]* 5.5 Write property test for city name in forecast request parameters (Property 6 — forecast)
    - **Property 6 (forecast): API client passes city name in forecast request parameters**
    - For any non-empty city string, the outgoing forecast GET request's query params include the exact city string
    - **Validates: Requirements 4.1**

  - [ ]* 5.6 Write property test for unexpected HTTP status codes (Property 5)
    - **Property 5: Unexpected HTTP status codes produce messages containing the status code**
    - For any HTTP status code that is not 200 and not 404, `fetch_current_weather` raises `ApiError` whose message contains the numeric status code
    - **Validates: Requirements 6.2**

- [ ] 6. Implement the output formatter
  - [ ] 6.1 Implement `format_current_weather` in `formatter.py`
    - Return a multi-line string containing city name, country code, temperature, condition, humidity, and wind speed as shown in the design
    - _Requirements: 3.2, 3.3_

  - [ ]* 6.2 Write property test for current weather output fields (Property 3)
    - **Property 3: Current weather output contains all required fields**
    - For any `CurrentWeather` object, `format_current_weather` output contains the city, country, temperature value, condition, humidity value, and wind speed value
    - **Validates: Requirements 3.2**

  - [ ] 6.3 Implement `format_forecast` in `formatter.py`
    - Return a header line plus one row per `ForecastDay` containing date, high, low, and condition
    - Must handle lists of any length from 1 to 14 without error
    - _Requirements: 4.2, 4.3_

  - [ ]* 6.4 Write property test for forecast output rows (Property 4)
    - **Property 4: Forecast output contains one entry per day with all required fields**
    - For any list of `ForecastDay` objects (length 1–14), `format_forecast` produces exactly one line per day containing date, high temp value, low temp value, and condition — with no exception raised
    - **Validates: Requirements 4.2, 4.3**

- [ ] 7. Implement the entry point and wire all layers together
  - [ ] 7.1 Implement `main.py` — orchestrate all layers
    - Call `get_api_key()`, `parse_args()`, `resolve_city()`, `fetch_current_weather()`, `fetch_forecast()`, `format_current_weather()`, `format_forecast()` in order
    - Print current weather block, blank line, then forecast block to stdout; exit 0 on success
    - Catch `WeatherToolError` subclasses, print to stderr, exit 1
    - _Requirements: 2.2, 3.3, 5.2, 6.1, 6.2, 7.1_

  - [ ]* 7.2 Write integration tests for `main.py` error paths
    - Test: missing API key → stderr message + exit 1
    - Test: city not found → stderr message + exit 1
    - Test: network error → stderr message + exit 1
    - Test: unexpected HTTP error including status code → stderr + exit 1
    - _Requirements: 2.2, 5.1, 5.2, 6.1, 6.2_

- [ ] 8. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Use `pytest` and `hypothesis` for unit and property-based tests respectively
- Mock `requests.get` and `input` in tests; no real network calls needed
- The free tier `/forecast` endpoint returns 5 days of 3-hour data (40 entries), not 14 — this is handled gracefully per Requirement 4.3
- Property tests use `hypothesis` strategies to generate arbitrary inputs (strings, integers, lists of dataclasses)
- Each task references specific requirements for traceability

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["2.1", "3.1"] },
    { "id": 2, "tasks": ["2.2", "2.3", "3.2", "5.1", "5.3"] },
    { "id": 3, "tasks": ["5.2", "5.4", "5.5", "5.6", "6.1", "6.3"] },
    { "id": 4, "tasks": ["6.2", "6.4", "7.1"] },
    { "id": 5, "tasks": ["7.2"] }
  ]
}
```
