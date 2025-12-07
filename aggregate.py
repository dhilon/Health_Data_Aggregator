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
        days[utc_parsed.date()] = {"sleep_quality": day['sleep_quality'], "sleep_duration": day['sleep_duration']} #assuming one sleep entry per day
    
    for workout in workouts_data:
        time_parsed = parser.parse(workout['time'], tzinfos=tzinfos)
        utc_parsed = time_parsed.astimezone(timezone.utc)
        print(utc_parsed.date())
        if utc_parsed.date() in days:
            if "calories_burned" in days[utc_parsed.date()]:
                days[utc_parsed.date()]["calories_burned"] += workout['calories_burned'] #could be multiple workouts per day
                days[utc_parsed.date()]["name"] += workout['name']
                days[utc_parsed.date()]["description"] += workout['description']
                days[utc_parsed.date()]["muscles"] += workout['muscles']
                days[utc_parsed.date()]["equipment"] += workout['equipment']
            days[utc_parsed.date()]["calories_burned"] = workout['calories_burned'] 
            days[utc_parsed.date()]["name"] = workout['name']
            days[utc_parsed.date()]["description"] = workout['description']
            days[utc_parsed.date()]["muscles"] = workout['muscles']
            days[utc_parsed.date()]["equipment"] = workout['equipment']
            
        else:
            days[utc_parsed.date()] = {"sleep_quality": 0, "sleep_duration": 0, "calories_burned": workout['calories_burned'], "name": workout['name'], "description": workout['description'], "muscles": workout['muscles'], "equipment": workout['equipment']}
    # with open("days.json", "w") as f:
    #    json.dump(days, f, indent=4)

if __name__ == "__main__":
    aggregate_sleep_data()