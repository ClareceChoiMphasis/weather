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
