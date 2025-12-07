from datetime import datetime, timezone
from dateutil import parser
import json
import pytz
from zoneinfo import ZoneInfo
import sys


def get_comprehensive_tzinfos():
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
    with open("sleep.json", "r") as f:
        sleep_data = json.load(f)
    with open("workouts.json", "r") as f:
        workouts_data = json.load(f)
    tzinfos = get_comprehensive_tzinfos()
    days = {}
    for day in sleep_data:
        time_parsed = parser.parse(day['sleep_start'], tzinfos=tzinfos) #parses the sleep start time into a datetime object with the correct timezone
        utc_parsed = time_parsed.astimezone(timezone.utc) #converts the datetime object to UTC
        std = str(utc_parsed.date())
        days[std] = {"sleep_quality": day['sleep_quality'], "sleep_duration": day['sleep_duration']} #assuming one sleep entry per day
    
    for workout in workouts_data:
        time_parsed = parser.parse(workout['time'], tzinfos=tzinfos) #parses the workout time into a datetime object with the correct timezone
        utc_parsed = time_parsed.astimezone(timezone.utc) #converts the datetime object to UTC
        time = str(utc_parsed.time())
        std = str(utc_parsed.date())
        if std in days:
            if "calories_burned" in days[std]:
                days[std]["calories_burned"] += workout['calories_burned'] #could be multiple workouts per day
                days[std]["name"] += ", " + workout['name']
                days[std]["description"] += workout['description']
                days[std]["muscles"] += workout['muscles']
                days[std]["equipment"] += workout['equipment']
                days[std]["time"] += ", " + time
            else:
                days[std]["calories_burned"] = workout['calories_burned'] 
                days[std]["name"] = workout['name']
                days[std]["description"] = workout['description']
                days[std]["muscles"] = workout['muscles']
                days[std]["equipment"] = workout['equipment']
                days[std]["time"] = time
        else:
            days[std] = {"sleep_quality": 0, "sleep_duration": 0, "calories_burned": workout['calories_burned'], "name": workout['name'], "description": workout['description'], "muscles": workout['muscles'], "equipment": workout['equipment'], "time": time} #workout on a day with no sleep entry
    
    with open("days.json", "w") as f:
        json.dump(days, f, indent=4) #puts all of the days and their data into a json file

def average_calories_low_sleep(): #metric that measures the average calories burned on days with less than 6 hours of sleep
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