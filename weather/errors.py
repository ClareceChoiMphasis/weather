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
