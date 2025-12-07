from datetime import datetime, timezone
from dateutil import parser, tz
import json
import pytz
from zoneinfo import ZoneInfo


def get_comprehensive_tzinfos():
    tzinfos = {}
    
    all_timezones_pytz = pytz.all_timezones
        
    for count in all_timezones_pytz:
        try:
            
            dt_with_timezone = datetime.now(ZoneInfo(count))
        
            # Get the timezone abbreviation
            abbreviation = dt_with_timezone.strftime('%Z')
            
            if abbreviation not in tzinfos:
                tzinfos[abbreviation] = pytz.timezone(count)
                
        except pytz.UnknownTimeZoneError:
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
        time_parsed = parser.parse(day['sleep_start'], tzinfos=tzinfos)
        utc_parsed = time_parsed.astimezone(timezone.utc)
        std = str(utc_parsed.date())
        days[std] = {"sleep_quality": day['sleep_quality'], "sleep_duration": day['sleep_duration']} #assuming one sleep entry per day
    
    for workout in workouts_data:
        time_parsed = parser.parse(workout['time'], tzinfos=tzinfos)
        utc_parsed = time_parsed.astimezone(timezone.utc)
        std = str(utc_parsed.date())
        if std in days:
            if "calories_burned" in days[std]:
                days[std]["calories_burned"] += workout['calories_burned'] #could be multiple workouts per day
                days[std]["name"] += ", " + workout['name']
                days[std]["description"] += workout['description']
                days[std]["muscles"] += workout['muscles']
                days[std]["equipment"] += workout['equipment']
            else:
                days[std]["calories_burned"] = workout['calories_burned'] 
                days[std]["name"] = workout['name']
                days[std]["description"] = workout['description']
                days[std]["muscles"] = workout['muscles']
                days[std]["equipment"] = workout['equipment']
            
        else:
            days[std] = {"sleep_quality": 0, "sleep_duration": 0, "calories_burned": workout['calories_burned'], "name": workout['name'], "description": workout['description'], "muscles": workout['muscles'], "equipment": workout['equipment']}
    
    for day in days:
        print(days[day])
    with open("days.json", "w") as f:
        json.dump(days, f, indent=4)

def average_calories_low_sleep():
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
    print(total_calories / total_days)

if __name__ == "__main__":
    average_calories_low_sleep()