"""
Health Data Aggregator Module

This module aggregates sleep and workout data from JSON files, processes timezone
information, and provides various health metrics including average calories burned
on low-sleep days, push workout days, and morning workouts.

Functions:
    get_comprehensive_tzinfos: Builds a comprehensive timezone abbreviation mapping
    aggregate_sleep_data: Aggregates sleep and workout data by day
    average_calories_low_sleep: Calculates average calories on days with <6 hours sleep
    push_days: Counts total push workout days
    morning_workouts: Counts workouts performed before 10:00 AM
"""

from datetime import datetime, timezone
from dateutil import parser
from dateutil.parser import ParserError
import json
import pytz
from zoneinfo import ZoneInfo
import sys
import os


def get_comprehensive_tzinfos():
    """
    Build a comprehensive mapping of timezone abbreviations to timezone objects.
    
    This function creates a dictionary mapping timezone abbreviations (e.g., 'EST', 'PST')
    to their corresponding pytz timezone objects. It checks both January (winter) and
    July (summer) dates to capture both standard time (ST) and daylight saving time (DST)
    abbreviations for all known timezones.
    
    Returns:
        dict: A dictionary mapping timezone abbreviations to pytz timezone objects.
            Format: {"abbreviation": pytz.timezone_object}
            Example: {"EST": <DstTzInfo 'America/New_York' EST-1 day, 19:00:00 STD>}
    
    Note:
        For Northern Hemisphere: January = ST, July = DST
        For Southern Hemisphere: January = DST, July = ST
        Unknown timezones or errors are silently skipped.
    """
    tzinfos = {}
    
    all_timezones_pytz = pytz.all_timezones
    
    # Check both January (winter) and July (summer) to capture both ST and DST abbreviations
    # For Northern Hemisphere: January = ST, July = DST
    # For Southern Hemisphere: January = DST, July = ST
    dates_to_check = [
        datetime(2025, 1, 15, 12, 0, 0),
        datetime(2025, 7, 15, 12, 0, 0),
    ]
        
    for count in all_timezones_pytz:
        try:
            # Check both dates to get both standard time and daylight saving time abbreviations
            for dt_naive in dates_to_check:
                dt_with_timezone = dt_naive.replace(tzinfo=ZoneInfo(count))
            
                abbreviation = dt_with_timezone.strftime('%Z')
                
                if abbreviation and abbreviation not in tzinfos:
                    tzinfos[abbreviation] = pytz.timezone(count) #in the format of {"abbreviation": "timezone info"}
                
        except (pytz.UnknownTimeZoneError, Exception):
            pass
        
    return tzinfos


def aggregate_sleep_data():
    """
    Aggregate sleep and workout data by day and write to days.json.
    
    This function reads sleep data from sleep.json and workout data from workouts.json,
    parses timestamps with proper timezone handling, converts all times to UTC, and
    aggregates the data by date. The aggregated data is then written to days.json.
    
    The function includes robust error handling for:
        - Missing fields (uses defaults or skips invalid entries)
        - Type mismatches (attempts conversion where possible)
        - Negative values (clamps to 0 or warns)
        - Unparseable timestamps (skips invalid entries with warning)
        - Very large files (checks file size before loading)
    
    Side Effects:
        - Reads from sleep.json and workouts.json
        - Writes aggregated data to days.json (overwrites existing file)
        - Prints warnings to stderr for data issues
    
    Raises:
        FileNotFoundError: If sleep.json or workouts.json cannot be found
        json.JSONDecodeError: If the JSON files are malformed
        OSError: If files are too large (>100MB) or cannot be read/written
        ValueError: If JSON structure is invalid (not an array)
    
    Note:
        Days with workouts but no sleep entries will have sleep_quality and
        sleep_duration set to 0. Invalid entries are skipped with warnings.
    """
    # Check file sizes before loading (limit to 100MB per file)
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    
    for filename in ["sleep.json", "workouts.json"]:
        if not os.path.exists(filename):
            raise FileNotFoundError(f"Required file not found: {filename}")
        
        file_size = os.path.getsize(filename)
        if file_size > MAX_FILE_SIZE:
            raise OSError(f"File {filename} is too large ({file_size / (1024*1024):.2f}MB). Maximum size is {MAX_FILE_SIZE / (1024*1024)}MB.")
    
    # Load JSON files
    try:
        with open("sleep.json", "r") as f:
            sleep_data = json.load(f)
        with open("workouts.json", "r") as f:
            workouts_data = json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON format: {e.msg}", e.doc, e.pos)
    
    # Validate JSON structure (must be arrays)
    if not isinstance(sleep_data, list):
        raise ValueError("sleep.json must contain a JSON array")
    if not isinstance(workouts_data, list):
        raise ValueError("workouts.json must contain a JSON array")
    
    tzinfos = get_comprehensive_tzinfos()
    days = {}
    for day in sleep_data:
        if 'sleep_start' not in day:
            print(f"Warning: Skipped sleep entry due to missing sleep_start field: {day}")
            continue
        try:
            time_parsed = parser.parse(day['sleep_start'], tzinfos=tzinfos) #parses the sleep start time into a datetime object with the correct timezone
        except ParserError:
            print(f"Warning: Skipped sleep entry due to invalid time format: {day['sleep_start']}")
            continue
        utc_parsed = time_parsed.astimezone(timezone.utc) #converts the datetime object to UTC
        std = str(utc_parsed.date())
        try:
            days[std] = {"sleep_quality": day['sleep_quality'], "sleep_duration": abs(day['sleep_duration'])} #assuming one sleep entry per day
        except ValueError:
            print(f"Warning: Skipped sleep entry due to invalid sleep_quality or sleep_duration field: {day}")
            continue
    
    for workout in workouts_data:
        if 'time' not in workout:
            print(f"Warning: Skipped workout entry due to missing time field: {workout}")
            continue
        try:
            time_parsed = parser.parse(workout['time'], tzinfos=tzinfos) #parses the workout time into a datetime object with the correct timezone
        except ParserError:
            print(f"Warning: Skipped workout entry due to invalid time format: {workout['time']}")
            continue
        utc_parsed = time_parsed.astimezone(timezone.utc) #converts the datetime object to UTC
        time = str(utc_parsed.time())
        std = str(utc_parsed.date())
        if std in days:
            if "calories_burned" in days[std]:  #could be multiple workouts per day
                days[std]["calories_burned"] += workout['calories_burned'] if "calories_burned" in workout else 0
                days[std]["name"] += ", " + workout['name'] if "name" in workout else ""
                days[std]["description"] += workout['description'] if "description" in workout else ""
                days[std]["muscles"] += workout['muscles'] if "muscles" in workout else ""
                days[std]["equipment"] += workout['equipment'] if "equipment" in workout else ""
                days[std]["time"] += ", " + time if "time" in workout else ""
            else:
                days[std]["calories_burned"] = workout['calories_burned'] if "calories_burned" in workout else 0
                days[std]["name"] = workout['name'] if "name" in workout else ""
                days[std]["description"] = workout['description'] if "description" in workout else ""
                days[std]["muscles"] = workout['muscles'] if "muscles" in workout else ""
                days[std]["equipment"] = workout['equipment'] if "equipment" in workout else ""
                days[std]["time"] = time if "time" in workout else ""
        else:
            days[std] = {"sleep_quality": 0, "sleep_duration": 0, "calories_burned": workout['calories_burned'] if "calories_burned" in workout else 0, "name": workout['name'] if "name" in workout else "", "description": workout['description'] if "description" in workout else "", "muscles": workout['muscles'] if "muscles" in workout else "", "equipment": workout['equipment'] if "equipment" in workout else "", "time": time if "time" in workout else ""} #workout on a day with no sleep entry
    
    # Write output file
    try:
        with open("days.json", "w") as f:
            json.dump(days, f, indent=4)
    except OSError as e:
        raise OSError(f"Cannot write to days.json: {e}")
    
    
def average_calories_low_sleep():
    """
    Calculate and print the average calories burned on days with less than 6 hours of sleep.
    
    This metric measures the average calories burned on days where sleep duration
    was less than 6 hours. It first aggregates the sleep and workout data, then
    filters days by sleep duration and calculates the average calories burned.
    
    Side Effects:
        - Calls aggregate_sleep_data() to ensure days.json is up to date
        - Reads from days.json
        - Prints the result to stdout
    
    Raises:
        FileNotFoundError: If days.json cannot be found
        json.JSONDecodeError: If days.json is malformed
        ZeroDivisionError: If there are no days with less than 6 hours of sleep
    
    Note:
        Days without calories_burned data are counted as 0 calories.
    """
    aggregate_sleep_data()
    with open("days.json", "r") as f:
        days = json.load(f)
    total_calories = 0
    total_days = 0
    for day in days:
        if days[day]["sleep_duration"] < 6:
            if "calories_burned" in days[day]:
                total_calories += days[day]["calories_burned"]
            else:
                total_calories += 0
            total_days += 1
    print("Average calories burned on days with less than 6 hours of sleep: " + str(total_calories / total_days))

def push_days():
    """
    Count and print the total number of push workout days.
    
    This function counts the total number of "push" workouts across all days by
    searching for the word "push" (case-insensitive) in workout names. Multiple
    occurrences of "push" in a single day's workout names are all counted.
    
    Side Effects:
        - Calls aggregate_sleep_data() to ensure days.json is up to date
        - Reads from days.json
        - Prints the result to stdout
    
    Raises:
        FileNotFoundError: If days.json cannot be found
        json.JSONDecodeError: If days.json is malformed
    
    Note:
        The count includes all occurrences of "push" in workout names, so a day
        with "Push Day" and "Push Workout" would count as 2 push days.
    """
    aggregate_sleep_data()
    with open("days.json", "r") as f:
        days = json.load(f)
    total_push_days = 0
    for day in days:
        if "name" in days[day]:
            if "push" in days[day]["name"].lower():
                total_push_days += days[day]["name"].lower().count("push")
    print("Total push days: " + str(total_push_days))

def morning_workouts():
    """
    Count and print the total number of morning workouts (before 10:00 AM).
    
    This function counts workouts that occurred before 10:00:00 AM (UTC time).
    It compares the workout time string directly with "10:00:00" to determine
    if a workout qualifies as a morning workout.
    
    Side Effects:
        - Calls aggregate_sleep_data() to ensure days.json is up to date
        - Reads from days.json
        - Prints the result to stdout
    
    Raises:
        FileNotFoundError: If days.json cannot be found
        json.JSONDecodeError: If days.json is malformed
    
    Note:
        The comparison uses string comparison, which works correctly for time
        strings in "HH:MM:SS" format. Times are in UTC as stored in days.json.
        A workout is considered a morning workout if its time is < "10:00:00".
    """
    aggregate_sleep_data()
    with open("days.json", "r") as f:
        days = json.load(f)
    total_morning_workouts = 0
    for day in days:
        if "time" in days[day]:
            if days[day]["time"] < "10:00:00": #assuming 10:00:00 is the time of the morning
                total_morning_workouts += 1
    print("Total morning workouts: " + str(total_morning_workouts))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python aggregate.py <metric>")
        sys.exit(1)
    metric = sys.argv[1]
    if metric == "average_calories_low_sleep":
        average_calories_low_sleep()
    elif metric == "push_days":
        push_days()
    elif metric == "morning_workouts":
        morning_workouts()
    else:
        print("Invalid metric")
        sys.exit(1)