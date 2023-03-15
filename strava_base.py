#imports
import time
import requests
import pandas
from pandas import json_normalize
import json
import csv

# http://www.strava.com/oauth/authorize?client_id=25544&response_type=code&redirect_uri=http://localhost/&approval_prompt=force&scope=activity:read_all,activity:write


def update_scope(app_id, client_secret):
  with open('strava_tokens.json') as json_file:
    strava_tokens = json.load(json_file)
  response = requests.post(url='https://www.strava.com/oauth/token',
                           data={
                             'client_id': app_id,
                             'redirect_url': 'localhost',
                             'response_type': 'code',
                             'approval_prompt': 'auto',
                             'scope': 'activity:read_all,activity:write'
                           })
  return response.json


def refresh_strava_token(app_id, client_secret):
  # Get the tokens from file to connect to Strava
  with open('strava_tokens.json') as json_file:
    strava_tokens = json.load(json_file)
  # If access_token has expired then
  # use the refresh_token to get the new access_token
  if strava_tokens['expires_at'] < time.time():
    # Make Strava auth API call with current refresh token
    response = requests.post(url='https://www.strava.com/oauth/token',
                             data={
                               'client_id': app_id,
                               'client_secret': client_secret,
                               'grant_type': 'refresh_token',
                               'refresh_token': strava_tokens['refresh_token']
                             })
    # Save response as json in new variable
    new_strava_tokens = response.json()
    # Save new tokens to file
    with open('strava_tokens.json', 'w') as outfile:
      json.dump(new_strava_tokens, outfile)
  # Use new Strava tokens from now
    strava_tokens = new_strava_tokens
  # Open the new JSON file and print the file contents
  # to check it's worked properly
  with open('strava_tokens.json') as check:
    data = json.load(check)
  print(data)


def update_strava_description(activity_id, new_description):
  with open('strava_tokens.json') as json_file:
    strava_tokens = json.load(json_file)

  url = "https://www.strava.com/api/v3/activities/" + str(activity_id)
  access_token = strava_tokens['access_token']
  body = {'description': new_description}

  # Update Activity
  r = requests.put(url + '?access_token=' + access_token, data=body)
  res = r.json()
  return r


def pull_strava_activity(activity_id):
  #pull base data
  with open('strava_tokens.json') as json_file:
    strava_tokens = json.load(json_file)
  # Loop through all activities
  url = "https://www.strava.com/api/v3/activities/" + str(
    activity_id) + "?include_all_efforts=True"
  access_token = strava_tokens['access_token']
  # Get first page of activities from Strava with all fields
  r = requests.get(url + '&access_token=' + access_token)
  r = r.json()

  df_base = json_normalize(r)

  #pull stream data
  with open('strava_tokens.json') as json_file:
    strava_tokens = json.load(json_file)
  # Loop through all activities
  url = "https://www.strava.com/api/v3/activities/" + str(
    activity_id
  ) + "/streams?keys=latlng,altitude,distance,time,heartrate,cadence,velocity_smooth,moving,grade_smooth&keys_by_type=True&"
  access_token = strava_tokens['access_token']
  # Get first page of activities from Strava with all fields
  r = requests.get(url + 'access_token=' + access_token)
  r = r.json()
  #print(r)
  df_stream = json_normalize(r)
  #print(df_stream)
  my_workout = {}
  try:
    df_stream.data
  except:
    my_workout['stream_length'] = 0
  else:
    my_workout['stream_length'] = len(df_stream.data[list(
      df_stream.type).index('distance')])

  #Translate the data streams into a useable object
  stream_sets = [
    'moving', 'latlng', 'velocity_smooth', 'grade_smooth', 'cadence',
    'distance', 'altitude', 'heartrate', 'time'
  ]

  my_workout['dist_delta'] = []
  my_workout['time_delta'] = []
  my_workout['cadence_bucket'] = []
  my_workout['hill_bucket'] = []
  my_workout['mph_v1'] = []
  my_workout['description'] = df_base['description'][0]

  #TODO: Add error handling around if the type cannot be found
  for i in stream_sets:
    if my_workout['stream_length'] > 0:
      try:
        df_stream.data[list(df_stream.type).index(i)]
      except:
        my_workout[i] = []
      else:
        my_workout[i] = df_stream.data[list(df_stream.type).index(i)]
  #Populate dist_delta and time delta
  for i in range(0, my_workout['stream_length']):
    if i == 0:
      my_workout['dist_delta'].append(my_workout['distance'][i])
      my_workout['time_delta'].append(my_workout['time'][i])
    else:
      my_workout['dist_delta'].append(my_workout['distance'][i] -
                                      my_workout['distance'][i - 1])
      my_workout['time_delta'].append(my_workout['time'][i] -
                                      my_workout['time'][i - 1])

    if (my_workout['time_delta'][i] == 0):
      my_workout['mph_v1'].append(0)
    else:
      my_workout['mph_v1'].append((my_workout['dist_delta'][i] * 3600.) /
                                  (my_workout['time_delta'][i] * 1609.344))

  return my_workout


def calc_metrics(my_workout, walk_limit, speed_limit, min_interval):
  #wrapper function encompassing all calc metrics - append to my workout
  my_workout = calc_walk_time(my_workout, walk_limit)
  my_workout = calc_altitude(my_workout)
  my_workout = calc_netElevChange(my_workout)
  my_workout = calc_stop_time(my_workout)
  my_workout = calc_intervals_v2(my_workout, speed_limit, min_interval)

  return my_workout


def calc_altitude(my_workout):
  avg_altitude = 0.0
  if my_workout['stream_length'] == 0 or len(my_workout['altitude']) == 0:
    my_workout['avg_altitude'] = 0
    return my_workout
  else:
    for i in range(0, my_workout['stream_length']):
      avg_altitude += my_workout['altitude'][i]
      if i == 0:
        my_workout['dist_delta'].append(my_workout['distance'][i])
        my_workout['time_delta'].append(my_workout['time'][i])
      else:
        my_workout['dist_delta'].append(my_workout['distance'][i] -
                                        my_workout['distance'][i - 1])
        my_workout['time_delta'].append(my_workout['time'][i] -
                                        my_workout['time'][i - 1])

      if (my_workout['time_delta'][i] == 0):
        my_workout['mph_v1'].append(0)
      else:
        my_workout['mph_v1'].append((my_workout['dist_delta'][i] * 3600.) /
                                    (my_workout['time_delta'][i] * 1609.344))

    my_workout['avg_altitude'] = round(
      (avg_altitude / my_workout['stream_length']) * (5280. / 1609.344) *
      (1 / 1000.), 1)
    return my_workout


def calc_netElevChange(my_workout):
  if my_workout['stream_length'] == 0 or len(my_workout['altitude']) == 0:
    my_workout['net_elev_change'] = 0
    return my_workout
  else:
    my_workout['net_elev_change'] = round(
      (my_workout['altitude'][int(my_workout['stream_length'] - 1)] -
       my_workout['altitude'][0]) * (5280. / 1609.344), 1)
    return my_workout


def calc_walk_time(my_workout, walk_limit):
  walk_time = 0.0
  for i in range(0, my_workout['stream_length']):
    if (my_workout['mph_v1'][i] <= walk_limit and my_workout['moving'][i]):
      walk_time += my_workout['time_delta'][i]
  #print(walk_time)
  my_workout['walk_time'] = walk_time
  return my_workout


def calc_stop_time(my_workout):
  stop_time = 0.0
  for i in range(0, my_workout['stream_length']):
    if (my_workout['moving'][i] == False):
      stop_time += my_workout['time_delta'][i]
  #print(stop_time)
  my_workout['stop_time'] = stop_time
  return my_workout


def calc_intervals(my_workout, speed_limit, min_interval):
  #Speed Miles
  speed_miles_v3 = 0.0
  temp_counter = 0.0
  in_streak = False
  d_start = 0.0
  t_start = 0.0
  streak_array = []
  for i in range(0, my_workout['stream_length']):
    if in_streak == True:
      live_speed = my_workout['velocity_smooth'][i]
      streak_speed = (my_workout['distance'][i] -
                      d_start) / (my_workout['time'][i] - t_start)
      if live_speed >= speed_limit * 0.85 * (
          1609.344 / 3600.) and streak_speed >= speed_limit * (1609.344 /
                                                               3600.):
        in_streak = True
        temp_counter += (my_workout['dist_delta'][i] / 1609.344)
      else:
        #End Streak
        in_streak = False
        if temp_counter >= min_interval:
          speed_miles_v3 += temp_counter
          streak_array.append(
            str(round(temp_counter, 2)) + 'mi interval at mile: ' +
            str(round((d_start) / 1609.344, 1)) +
            ' with an average speed of ' +
            str(round(streak_speed * (3600. / 1609.344), 2)) + 'mph \n')
        temp_counter = 0.0
    else:
      temp_counter = 0.0
      if (my_workout['velocity_smooth'][i] >= speed_limit *
          (1609.344 / 3600.)):
        temp_counter += (my_workout['dist_delta'][i] / 1609.344)
        in_streak = True
        d_start = my_workout['distance'][i]
        t_start = my_workout['time'][i]
      else:  #Not in streak, not fast = stay not in streak
        pass

  if temp_counter >= min_interval:
    streak_speed = (my_workout['distance'][i] -
                    d_start) / (my_workout['time'][i] - t_start)
    speed_miles_v3 += temp_counter
    streak_array.append(
      str(round(temp_counter, 2)) + 'mi interval at mile: ' +
      str(round((d_start) / 1609.344, 1)) + ' with an average speed of ' +
      str(round(streak_speed * (3600. / 1609.344), 1)) + 'mph \n')
  print(speed_miles_v3)
  print(streak_array)
  my_workout['speed_miles'] = round(speed_miles_v3, 2)
  my_workout['intervals'] = streak_array
  my_workout['interval_text'] = ""
  for j in streak_array:
    my_workout['interval_text'] += j + " "
  return my_workout


def calc_intervals_v2(my_workout, speed_limit, min_interval):
  #Speed Miles
  temp_counter = 0.0
  in_streak = False
  d_start = 0.0
  t_start = 0.0
  #Speed Limits
  speed_min = speed_limit * 0.8 * (1609.344 / 3600.)
  start_min = speed_limit * 0.9 * (1609.344 / 3600.)
  segment_min = 1.01 * speed_limit * (1609.344 / 3600.)

  #Outputs
  speed_miles_v3 = 0.0
  streak_array = []
  for i in range(0, my_workout['stream_length']):
    if in_streak == True:
      live_speed = my_workout['velocity_smooth'][i]
      streak_speed = (my_workout['distance'][i] -
                      d_start) / (my_workout['time'][i] - t_start)
      if (len(my_workout['altitude']) > 0):
        streak_climb = my_workout['altitude'][i] - a_start
      else:
        streak_climb = 0

      if live_speed >= speed_min and streak_speed >= segment_min:
        #Stay in the streak
        in_streak = True
        temp_counter += (my_workout['dist_delta'][i] / 1609.344)
      else:
        #End Streak
        in_streak = False
        multiplier = 1.04 - (0.1 * temp_counter)
        climb_multiplier = (1.00 - (0.0075 * streak_climb))
        if multiplier <= 0.98:
          multiplier = 0.98
        if multiplier >= 1.025:
          multiplier = 1.025
        if climb_multiplier <= 0.98:
          climb_multiplier = 0.98
        if climb_multiplier >= 1.01:
          climb_multiplier = 1.01
        total_streak_limit = speed_limit * multiplier * climb_multiplier
        #print(str(total_streak_limit)+' = '+str(speed_limit)+' x '+str(multiplier)+' x '+str(climb_multiplier))
        if temp_counter >= min_interval and streak_speed * (
            3600. / 1609.344) >= total_streak_limit:
          speed_miles_v3 += temp_counter
          streak_array.append(
            str(round(temp_counter, 2)) + 'mi interval at mile: ' +
            str(round((d_start) / 1609.344, 1)) +
            ' with an average speed of ' +
            str(round(streak_speed * (3600. / 1609.344), 1)) +
            'mph with net climb of ' + str(int(streak_climb *
                                               (5280 / 1609))) + ' ft \n')
        temp_counter = 0.0
    else:
      temp_counter = 0.0
      if (my_workout['velocity_smooth'][i] >= start_min):
        temp_counter += (my_workout['dist_delta'][i] / 1609.344)
        in_streak = True
        d_start = my_workout['distance'][i]
        t_start = my_workout['time'][i]
        if (len(my_workout['altitude']) > 0):
          a_start = my_workout['altitude'][i]
        else:
          a_start = 0
      else:  #Not in streak, not fast = stay not in streak
        pass
  if my_workout['stream_length'] > 0:
    if (len(my_workout['altitude']) > 0):
      streak_climb = my_workout['altitude'][i] - a_start
    else:
      streak_climb = 0
    multiplier = 1.05 - (0.1 * temp_counter)
    climb_multiplier = (1.00 - (0.0075 * streak_climb))
    if multiplier <= 0.98:
      multiplier = 0.98
    if multiplier >= 1.025:
      multiplier = 1.025
    if climb_multiplier <= 0.98:
      climb_multiplier = 0.98
    if climb_multiplier >= 1.01:
      climb_multiplier = 1.01
    total_streak_limit = speed_limit * multiplier * climb_multiplier
    #print(str(total_streak_limit)+' = '+str(speed_limit)+' x '+str(multiplier)+' x '+str(climb_multiplier))
    if temp_counter >= min_interval and streak_speed * (
        3600. / 1609.344) >= total_streak_limit:
      streak_speed = (my_workout['distance'][i] -
                      d_start) / (my_workout['time'][i] - t_start)
      speed_miles_v3 += temp_counter
      streak_array.append(
        str(round(temp_counter, 2)) + ' mi interval at mile: ' +
        str(round((d_start) / 1609.344, 1)) + ' with an average speed of ' +
        str(round(streak_speed * (3600. / 1609.344), 1)) +
        ' mph with net climb of ' + str(int(streak_climb *
                                            (5280. / 1609))) + ' ft \n')
  print(speed_miles_v3)
  print(streak_array)
  my_workout['speed_miles'] = round(speed_miles_v3, 2)
  my_workout['intervals'] = streak_array
  my_workout['interval_text'] = ""
  for j in streak_array:
    my_workout['interval_text'] += j + " "
  return my_workout
