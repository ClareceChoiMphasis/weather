# Requirements Document

## Introduction

A Python command-line interface (CLI) tool that retrieves and displays current weather conditions and a 14-day forecast for a specified city using the OpenWeatherMap API (free tier). The user may supply the city as a command-line argument; if omitted, the tool prompts interactively. All output is rendered in the terminal.

## Glossary

- **CLI Tool**: The Python command-line application described in this document, invoked from a terminal.
- **OpenWeatherMap API**: The third-party REST weather service at openweathermap.org used as the data source (free tier plan).
- **API Key**: A user-supplied authentication token required by the OpenWeatherMap API.
- **Current Weather**: Real-time weather data for a city including temperature, conditions, humidity, and wind speed.
- **Forecast**: A 14-day (two-week) day-by-day weather outlook containing high/low temperatures and condition summaries.
- **City**: A human-readable city name used to identify the location for weather queries.
- **Exit Code**: The integer value returned to the operating system upon process termination (0 = success, non-zero = error).

## Requirements

### Requirement 1: City Input

**User Story:** As a user, I want to supply a city name either as a command-line argument or via an interactive prompt, so that I can use the tool conveniently in both scripted and interactive contexts.

#### Acceptance Criteria

1. WHEN the user invokes the CLI Tool with a city name as a positional command-line argument, THE CLI Tool SHALL use that city name for the weather query without prompting.
2. WHEN the user invokes the CLI Tool without a city name argument, THE CLI Tool SHALL display an interactive prompt asking the user to enter a city name.
3. WHEN the interactive prompt is displayed and the user enters a non-empty city name, THE CLI Tool SHALL use the entered city name for the weather query.
4. IF the user submits an empty string at the interactive prompt, THEN THE CLI Tool SHALL re-display the prompt until a non-empty city name is provided.

---

### Requirement 2: API Key Configuration

**User Story:** As a user, I want to configure my OpenWeatherMap API key once, so that the tool can authenticate with the API without requiring the key on every invocation.

#### Acceptance Criteria

1. THE CLI Tool SHALL read the OpenWeatherMap API key from the environment variable `OPENWEATHERMAP_API_KEY`.
2. IF the `OPENWEATHERMAP_API_KEY` environment variable is not set or is empty, THEN THE CLI Tool SHALL display an error message instructing the user to set the variable and exit with a non-zero Exit Code.

---

### Requirement 3: Current Weather Display

**User Story:** As a user, I want to see the current weather for my chosen city, so that I know the present conditions at a glance.

#### Acceptance Criteria

1. WHEN a valid city name is provided, THE CLI Tool SHALL query the OpenWeatherMap API for current weather data for that city.
2. WHEN current weather data is successfully retrieved, THE CLI Tool SHALL display the city name, country code, temperature in degrees Celsius, weather condition description, humidity percentage, and wind speed in metres per second.
3. WHEN current weather data is successfully retrieved, THE CLI Tool SHALL display the current weather before the Forecast output.

---

### Requirement 4: Two-Week Forecast Display

**User Story:** As a user, I want to see a 14-day weather forecast for my chosen city, so that I can plan ahead.

#### Acceptance Criteria

1. WHEN a valid city name is provided, THE CLI Tool SHALL query the OpenWeatherMap API for forecast data covering up to 14 days.
2. WHEN forecast data is successfully retrieved, THE CLI Tool SHALL display one entry per day showing the date, high temperature in degrees Celsius, low temperature in degrees Celsius, and weather condition description.
3. WHERE the OpenWeatherMap free tier provides fewer than 14 forecast days, THE CLI Tool SHALL display all available forecast days without error.

---

### Requirement 5: Error Handling — Unknown City

**User Story:** As a user, I want a clear message when the city I entered cannot be found, so that I can correct my input.

#### Acceptance Criteria

1. IF the OpenWeatherMap API returns a "city not found" response, THEN THE CLI Tool SHALL display a human-readable error message stating that the city could not be found.
2. IF the OpenWeatherMap API returns a "city not found" response, THEN THE CLI Tool SHALL exit with a non-zero Exit Code.

---

### Requirement 6: Error Handling — Network and API Failures

**User Story:** As a user, I want informative feedback when a network or API error occurs, so that I understand why the tool did not return results.

#### Acceptance Criteria

1. IF a network connection error occurs while contacting the OpenWeatherMap API, THEN THE CLI Tool SHALL display an error message describing the connectivity problem and exit with a non-zero Exit Code.
2. IF the OpenWeatherMap API returns an unexpected HTTP error status code, THEN THE CLI Tool SHALL display an error message that includes the HTTP status code and exit with a non-zero Exit Code.

---

### Requirement 7: Successful Exit

**User Story:** As a user and as a script author, I want the tool to exit cleanly after displaying results, so that I can use it reliably in automated pipelines.

#### Acceptance Criteria

1. WHEN weather data is successfully retrieved and displayed, THE CLI Tool SHALL exit with Exit Code 0.
