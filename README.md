# Health_Data_Aggregator

## How to run

1. Create and activate Python virtual environment:

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate        # On macOS / Linux
    # or
    .venv\Scripts\activate           # On Windows PowerShell or CMD
    ```

2. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

3. Run the app with the desired metric as a command-line argument:

    ```bash
    python3 aggregate.py <metric>
    ```


**Available Metrics:**
- `average_calories_low_sleep` - Calculates the average calories burned on days with less than 6 hours of sleep
- `push_days` - Counts the total number of push day workouts
- `morning_workouts` - Counts the total number of workouts that occurred before 10:00 AM UTC

**Examples:**
```bash
python3 aggregate.py average_calories_low_sleep
python3 aggregate.py push_days
python3 aggregate.py morning_workouts
```

**Note**: The script requires exactly one argument (the metric name). If no argument is provided or an invalid metric is specified, it will display an error message and exit. Running any metric will first aggregate the data from `sleep.json` and `workouts.json` into `days.json`, then calculate and print the requested metric. 

I used a virtual environment to ensure all of the dependencies were up to date and easily shareable.

## Methodology

I used four builtin libraries: `zoneinfo`, `json`, `datetime`, and `sys`, and two imported libraries: `pytz` and `dateutil`. The core challenge was handling timestamps from multiple timezones and converting them to a standardized UTC format for accurate date-based aggregation. I used these libraries because when researching them on Google, they had the most functionality in terms of amount of datetimes and easily-readable objects and they were popular.

### Library Usage

- **zoneinfo**: Used to create timezone-aware datetime objects when building the timezone abbreviation mapping. It provides access to the IANA timezone database, allowing us to work with timezones by their standard names (e.g., "America/Los_Angeles").

- **json**: Used for reading input data from `sleep.json` and `workouts.json`, and writing the aggregated output to `days.json`. This handles the serialization and deserialization of the data structures.

- **datetime**: Core library for working with dates and times. Used to create datetime objects, convert between timezones using `astimezone()`, and extract date components. The `timezone.utc` constant is used as the target timezone for all conversions.

- **pytz**: Provides comprehensive timezone support with the `pytz.all_timezones` list containing all available timezone identifiers. Used to create timezone objects that can be passed to `dateutil.parser.parse()` via the `tzinfos` parameter. Essential for mapping timezone abbreviations (like "PST", "EST") to their corresponding timezone objects.

- **dateutil**: The `parser.parse()` function is the key component for parsing timestamps in various formats. It can handle:
  - ISO format: `"2023-10-01T08:00:00Z"`
  - Space-separated: `"2023-10-01 15:00:00 PST"`
  - Offset formats: `"2023-10-01T14:45:00-05:00"`
  - And many other variations

  The `tzinfos` parameter allows us to provide a dictionary mapping timezone abbreviations to timezone objects, enabling the parser to correctly interpret abbreviations like "PST", "EST", "PDT", etc.

- **sys**: Used for command-line argument handling. The `sys.argv` list contains the command-line arguments passed to the script, allowing users to specify which metric to calculate. `sys.exit()` is used to terminate the program with an appropriate exit code when invalid arguments are provided.

### Approach

1. **Timezone Mapping**: Build a comprehensive dictionary of timezone abbreviations by iterating through all available timezones and checking both winter (January) and summer (July) dates to capture both Standard Time (ST) and Daylight Saving Time (DST) abbreviations.

2. **Data Parsing**: Parse each timestamp from the input files using `dateutil.parser.parse()` with the timezone mapping, which automatically handles various timestamp formats and timezone representations.

3. **UTC Normalization**: Convert all parsed timestamps to UTC using `astimezone(timezone.utc)`, ensuring all data is on a common timezone for accurate date-based grouping.

4. **Date-Based Aggregation**: Extract the UTC date from each normalized timestamp and group sleep and workout data by date, handling cases where:
   - Multiple workouts occur on the same day
   - A workout occurs on a day without a sleep entry
   - Timestamps cross day boundaries (e.g., 11:45 PM PST becomes the next day in UTC)

5. **Metric Calculation**: Compute metrics from the aggregated data, such as average calories burned on days with low sleep duration.

### Artificial Intelligence
I used Cursor to help generate edge cases for `workouts.json` and `sleep.json` (based on 12 cases I had already written), particularly timestamps that cross day boundaries when converted to UTC. However, a majority of my research on these modules came from Google and Stack Overflow posts about how to convert such a wide range of timezones and specific use cases like dictionary handling and parsing. To create this README, I also gave a detailed structure and explanation of how to run, methodology, and code breakdown and had it expand on some finer details. I also had it generate some unique edge cases that would result in data loss or error and fixed them.

## Code Breakdown

The codebase consists of two main functions and three metric functions, with command-line argument handling in the main block.

### Functions

#### `get_comprehensive_tzinfos()`

**Purpose**: Creates a comprehensive mapping of timezone abbreviations to pytz timezone objects, covering both Standard Time (ST) and Daylight Saving Time (DST) abbreviations.

**How it works**:
1. Retrieves all available timezones from `pytz.all_timezones` (e.g., "America/Los_Angeles", "Europe/London")
2. Checks two dates (January 15 and July 15) to capture both ST and DST abbreviations:
   - Northern Hemisphere: January = ST, July = DST
   - Southern Hemisphere: January = DST, July = ST
3. For each timezone and date combination:
   - Creates a timezone-aware datetime using `ZoneInfo`
   - Extracts the abbreviation using `strftime('%Z')` (e.g., "PST", "PDT", "EST", "EDT")
   - Maps the abbreviation to the corresponding pytz timezone object
4. Returns a dictionary in the format: `{"PST": <pytz.timezone object>, "PDT": <pytz.timezone object>, ...}`

**Key insight**: By checking both winter and summer dates, we ensure that timezones with DST are represented by both their standard and daylight saving abbreviations, preventing `UnknownTimezoneWarning` errors when parsing timestamps. I separated this into another function because getting the timezone data has a lot of resource cost and I wanted it to be separate from the dataframe interactions.

#### `aggregate_sleep_data()`

**Purpose**: Aggregates sleep and workout data by UTC date, handling multiple timezone formats and cross-day boundary conversions. I decided to not have this output any text other than the errors and instead write the resulting object to a new file, days.json, instead, where it is easily viewable.

**Data Flow**:
1. **Load Data**: Reads `sleep.json` and `workouts.json` files
2. **Build Timezone Map**: Calls `get_comprehensive_tzinfos()` to get the abbreviation mapping
3. **Process Sleep Data**:
   - Parses each `sleep_start` timestamp using `parser.parse()` with `tzinfos`
   - Converts to UTC using `astimezone(timezone.utc)`
   - Extracts the UTC date and stores sleep quality and duration
   - Assumes one sleep entry per day (overwrites if duplicate dates exist)
4. **Process Workout Data**:
   - Parses each workout `time` timestamp similarly
   - Converts to UTC and extracts both the UTC date and UTC time
   - If the date already exists (has sleep data):
     - If workouts already exist for that day: accumulates calories, appends names/descriptions, extends lists, appends workout times
     - If no workouts yet: initializes workout fields including the workout time
   - If the date doesn't exist: creates a new entry with sleep_quality=0, sleep_duration=0 and all workout fields including time
5. **Output**: Writes the aggregated data to `days.json` with dates as keys and combined sleep/workout data as values. Each day entry includes workout times in UTC format (e.g., "14:30:00").

**Edge Cases Handled**:
- Timestamps that cross day boundaries (e.g., 11:45 PM PST = next day in UTC)
- Multiple workouts on the same day
- Workouts on days without sleep entries
- Various timestamp formats (ISO, space-separated, with offsets, with abbreviations)

### Metrics

Inside each metric, I call the `aggregate_sleep_data()` method to combine the dataframe and then output one value, to get a proper, concise result instead of a massive chunk of data.

#### `average_calories_low_sleep()`

**Purpose**: Calculates the average calories burned on days with less than 6 hours of sleep.

**How it works**:
1. Calls `aggregate_sleep_data()` to generate/update `days.json`
2. Loads the aggregated data from `days.json`
3. Iterates through all days and filters for those with `sleep_duration < 6`
4. Sums the calories burned for qualifying days (defaults to 0 if no workouts)
5. Calculates and prints the average: `total_calories / total_days`

**Output**: Prints a formatted string with the calculated average.

#### `push_days()`

**Purpose**: Counts the total number of push day workouts across all days.

**How it works**:
1. Calls `aggregate_sleep_data()` to generate/update `days.json`
2. Loads the aggregated data from `days.json`
3. Iterates through all days and checks if the workout name contains "push" (case-insensitive)
4. Counts occurrences of "push" in workout names (handles multiple push workouts on the same day)
5. Prints the total count

**Output**: Prints a formatted string with the total number of push day workouts.

**Note**: This metric counts all instances of "push" in workout names, so if a day has multiple push workouts, each one is counted separately.

#### `morning_workouts()`

**Purpose**: Counts the total number of workouts that occurred before 10:00 AM UTC.

**How it works**:
1. Calls `aggregate_sleep_data()` to generate/update `days.json`
2. Loads the aggregated data from `days.json`
3. Iterates through all days and checks if a workout time exists
4. Compares the workout time (as a string) to "10:00:00" using string comparison
5. If the time is earlier than 10:00:00, increments the counter
6. Prints the total count

**Output**: Prints a formatted string with the total number of morning workouts.

**Note**: The comparison uses string comparison, which works correctly for time strings in "HH:MM:SS" format. The time is stored in UTC, so this represents morning workouts in UTC timezone.

### Command-Line Interface

The main block (`if __name__ == "__main__":`) handles command-line argument processing:

1. **Argument Validation**: Checks if exactly one argument is provided using `len(sys.argv)`
   - If not, prints usage message and exits with code 1
2. **Metric Selection**: Retrieves the metric name from `sys.argv[1]`
3. **Metric Execution**: Matches the metric name to the corresponding function and executes it
4. **Error Handling**: If an invalid metric is provided, prints an error message and exits with code 1

**Usage Pattern**:
```python
sys.argv[0]  # Script name: "aggregate.py"
sys.argv[1]  # First argument: metric name (e.g., "average_calories_low_sleep")
```

This design allows for easy extension - simply add a new metric function and add a corresponding `elif` clause in the main block.

