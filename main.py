#imports

import sys
import os
import re

# setting path
import time
import requests
import pandas
from pandas import json_normalize
import json
from datetime import datetime, timedelta
from math import *
import notion_base as nb
import strava_base as sb

#response1 = sb.update_scope(os.environ["app_id"], os.environ["client_secret"])
#print(response1)

sb.refresh_strava_token(os.environ["app_id"], os.environ["client_secret"])

activities = [8715887806]

#Using Strava Base
for activity in activities:
  #Pull Data from Strava
  my_workout = sb.pull_strava_activity(activity)
  #print(my_workout['stream_length'])
  my_workout = sb.calc_metrics(my_workout, 4.0, 7.8, 0.1)
  #print(my_workout)
  #Find entry in Notion
  my_page = nb.find_page_in_database(os.environ["API_KEY_1"],
                                     os.environ["Fitness_DB"], 'Id',
                                     str(activity))

  if len(my_page['results']) != 1:
    raise Exception("Not one result, sorry bro!")
  else:
    page_id = my_page['results'][0]['id']
    #Update entry as needed
    #nb.update_page_property(key, page_id, property_name, property_type, new_value)
    base_desc = my_workout["description"]
    tts = ''
    if base_desc.find('Weather Summary') >= 0:
      tts += base_desc.split('Weather Summary:')[1].split('Klimat.app')[0]
    else:
      tts += base_desc.split('Klimat.app')[0]

    temp_values = re.findall(r'\d+', tts)
    my_numbers = list(map(int, temp_values))

    workout_temp = (my_numbers[0] + my_numbers[1]) / 2
    workout_dp = (my_numbers[4] + my_numbers[5]) / 2
    workout_hi = (my_numbers[len(my_numbers) - 1])

    #Update Numeric Fields
    property_name_array = [
      'WalkTime', 'StopTime', 'Altitude', 'NetElevGain', 'SpeedMilesCalc',
      'SpeedMiles', 'Temp', 'Heat Index', 'Dew Point'
    ]
    property_type_array = [
      'Number', 'Number', 'Number', 'Number', 'Number', 'Number', 'Number',
      'Number', 'Number'
    ]
    property_value_array = [
      my_workout['walk_time'], my_workout['stop_time'],
      my_workout['avg_altitude'], my_workout['net_elev_change'],
      my_workout['speed_miles'], my_workout['speed_miles'], workout_temp,
      workout_hi, workout_dp
    ]
    update_data = nb.update_page_property_new(os.environ["API_KEY_1"], page_id,
                                              property_name_array,
                                              property_type_array,
                                              property_value_array)

    #print(update_data)

    #Append Metrics to the workout description
    current_description = my_workout["description"]
    new_description = current_description + '\n Advanced Metrics by Mumapps:'
    new_description = new_description + '\n ' + str(
      my_workout["speed_miles"]) + ' speed miles'
    new_description = new_description + '\n' + my_workout["interval_text"]

    if current_description.find('Mumapps') >= 0:
      pass
    else:
      result = sb.update_strava_description(activity, new_description)
      print(result)
    # TODO

    #Update Text Fields Individually
    update_data_2 = nb.update_page_property(os.environ["API_KEY_1"], page_id,
                                            "Interval Details", "text",
                                            my_workout["interval_text"])
    update_data_3 = nb.update_page_property(os.environ["API_KEY_1"], page_id,
                                            "Notes", "text",
                                            my_workout["description"])
    #print(update_data)

    #Update the month field
    print(my_page['results'][0]['properties']['Date']['date']['start'])

    # last 3: month_field, month_db, month_date_field)
    link_result = nb.link_by_date_to_month(
      os.environ["API_KEY_1"], os.environ["Fitness_DB"], page_id,
      my_page['results'][0]['properties']['Date']['date']['start'], 'Month',
      os.environ["Monthly_DB"], 'Date')

    #print(link_result)

    link_result_2 = nb.link_by_date_to_week(
      os.environ["API_KEY_1"], os.environ["Fitness_DB"], page_id,
      my_page['results'][0]['properties']['Date']['date']['start'],
      'Actual Week', os.environ["Weekly_DB"], 'Week Start')

    print(link_result_2)
