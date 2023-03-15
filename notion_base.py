import requests, json, os
from datetime import datetime, timedelta

######################################################
# Table of Contents
#  -
#  -
#  -
######################################################


# Create a page
# Input: API Key and a data array json dump
# Input Example
#   data = json.dumps({'parent':{'database_id':dbid},
#           "properties":{
#               "Day":{
#                   "title":[
#                       {
#                       "text":{
#                           "content":str(date)
#                       }
#                       }
#                   ]
#               },
#               "Date":{
#                   "id":"Date",
#                   "type":"date",
#                   "date":{
#                     "start":str(date)
#                   }
#
#               }
#           }})
# Output:
# A page is created
# The returned r.content can be used to confirm creation and has the details about the page.
def create_page(key, data):
  post_location = 'https://api.notion.com/v1/pages'
  headers = {
    'Authorization': 'Bearer ' + key + '',
    'Content-Type': 'application/json',
    'Notion-Version': '2021-05-13'
  }

  r = requests.post(post_location, headers=headers, data=data)

  return r.content


# Pull all data
# Pulls all data from a database
# Input: API Key and a database ID
# Optional: initial_data = data (e.g. a sort) to be passed to the query. Format as a json.dumps
# Output: a dictionary with 0, 1, 2, ... representing the page results


def pull_all_data(key, dbid, initial_data=None):
  post_location = 'https://api.notion.com/v1/databases/' + dbid + '/query'
  headers = {
    'Authorization': 'Bearer ' + key + '',
    'Content-Type': 'application/json',
    'Notion-Version': '2021-05-13'
  }
  has_more = True
  result_array = {}
  i = 0

  while (has_more):
    if i == 0:  #start at the top
      r = requests.post(post_location, headers=headers, data=initial_data)
    else:
      data = json.loads(initial_data)
      data['start_cursor'] = r_format['next_cursor']
      r = requests.post(post_location, headers=headers, data=json.dumps(data))

    r_format = json.loads(r.content)
    result_array[i] = r_format
    i = i + 1
    has_more = r_format['has_more']

  return result_array


# Merge Result Array
# Input: the result array returned from a pull_all_data query
# Output: a list object of all the objects in the database


def merge_result_array(result_array):
  output = []
  len(result_array)
  for i in range(0, len(result_array)):
    for j in range(0, len(result_array[i]['results'])):
      output.append(result_array[i]['results'][j])

  return output


def update_page_property_new(key, page_id, property_name_array,
                             property_type_array, new_value_array):
  post_location = 'https://api.notion.com/v1/pages/' + page_id
  headers = {
    'Authorization': 'Bearer ' + key + '',
    'Content-Type': 'application/json',
    'Notion-Version': '2021-05-13'
  }
  text = '{\"properties\": {'
  for i in range(0, len(property_name_array)):
    if property_type_array[i] == "Text" or property_type_array[i] == "text":
      #updateData = {
      #        property_name_array[i]: {
      #            "rich_text": [
      #                {
      #                    "text": {
      #                        "content": new_value_array[i]
      #                    }
      #                }
      #            ]
      #        }
      #    }
      #}

      #text += json.dumps(updateData)
      #text+= json.dumps(property_name_array[i])+":"+json.dumps(new_value_array[i])+""
      #text+=  json.dumps(property_name_array[i])+":{"+json.dumps("rich_text")+":"+json.dumps(new_value_array[i])+"}"
      #text+=  json.dumps(property_name_array[i])+":{"+json.dumps("rich_text")+":[{\"text\": { \"content\":"+json.dumps(new_value_array[i])+"}}]}"
      pass
    else:
      text += json.dumps(property_name_array[i]) + ":" + json.dumps(
        new_value_array[i]) + ""
    if i < len(property_name_array) - 1:
      text += ", "
  text += "}}"
  print(text)
  r = requests.patch(post_location, headers=headers, data=text)
  returned_data = json.loads(r.content)
  return returned_data


def update_page_property(key, page_id, property_name, property_type,
                         new_value):
  post_location = 'https://api.notion.com/v1/pages/' + page_id
  headers = {
    'Authorization': 'Bearer ' + key + '',
    'Content-Type': 'application/json',
    'Notion-Version': '2021-05-13'
  }
  if property_type == 'relation':
    data = json.dumps({"properties": {property_name: new_value}})
    r = requests.patch(post_location, headers=headers, data=data)
    returned_data = json.loads(r.content)
    return returned_data
  elif property_type == 'number':
    data = json.dumps({"properties": {property_name: new_value}})
    r = requests.patch(post_location, headers=headers, data=data)
    returned_data = json.loads(r.content)
    return returned_data
  elif property_type == 'text':
    updateData = json.dumps({
      "properties": {
        property_name: {
          "rich_text": [{
            "text": {
              "content": new_value
            }
          }]
        }
      }
    })

    r = requests.patch(post_location, headers=headers, data=updateData)
    returned_data = json.loads(r.content)
    return returned_data
  else:
    return "Not Implemented"


def find_page_in_database(key, database_id, key_column, key_value):
  post_location = 'https://api.notion.com/v1/databases/' + database_id + '/query'
  headers = {
    'Authorization': 'Bearer ' + key + '',
    'Content-Type': 'application/json',
    'Notion-Version': '2021-05-13'
  }
  data = json.dumps(
    {"filter": {
      "property": key_column,
      "text": {
        "equals": key_value
      }
    }})

  r = requests.post(post_location, headers=headers, data=data)
  returned_data = json.loads(r.content)
  return returned_data


def find_page_in_database_by_date(key, database_id, key_column, key_value):
  post_location = 'https://api.notion.com/v1/databases/' + database_id + '/query'
  headers = {
    'Authorization': 'Bearer ' + key + '',
    'Content-Type': 'application/json',
    'Notion-Version': '2021-05-13'
  }
  data = json.dumps(
    {"filter": {
      "property": key_column,
      "date": {
        "equals": key_value
      }
    }})

  r = requests.post(post_location, headers=headers, data=data)
  returned_data = json.loads(r.content)
  return returned_data


def find_page_in_database_recent_week(key, database_id, key_column, key_value):
  post_location = 'https://api.notion.com/v1/databases/' + database_id + '/query'
  headers = {
    'Authorization': 'Bearer ' + key + '',
    'Content-Type': 'application/json',
    'Notion-Version': '2021-05-13'
  }
  print(str(key_value.strftime('%Y-%m-%d')))
  print(str((key_value - timedelta(days=6)).strftime('%Y-%m-%d')))
  data = json.dumps({
    "filter": {
      "and": [{
        "property": key_column,
        "date": {
          "on_or_before": str(key_value.strftime('%Y-%m-%d'))
        }
      }, {
        "property": key_column,
        "date": {
          "on_or_after":
          str((key_value - timedelta(days=6)).strftime('%Y-%m-%d'))
        }
      }]
    }
  })

  r = requests.post(post_location, headers=headers, data=data)
  returned_data = json.loads(r.content)
  return returned_data


def pull_single_page(key, page_to_pull):
  post_location = 'https://api.notion.com/v1/pages/' + page_to_pull
  headers = {
    'Authorization': 'Bearer ' + key + '',
    'Content-Type': 'application/json',
    'Notion-Version': '2021-08-16'
  }

  r = requests.get(post_location, headers=headers)
  returned_data = json.loads(r.content)
  return returned_data


def pull_all_page_content(key, page_to_pull, initial_data=None):
  post_location = 'https://api.notion.com/v1/blocks/' + page_to_pull + '/children?page_size=100'
  headers = {
    'Authorization': 'Bearer ' + key + '',
    'Content-Type': 'application/json',
    'Notion-Version': '2021-08-16'
  }
  has_more = True
  result_array = {}
  i = 0

  while (has_more):
    if i == 0:  #start at the top
      r = requests.get(post_location, headers=headers, data=initial_data)
    else:
      post_location_new = post_location + str(
        "&start_cursor=") + r_format['next_cursor']
      print(post_location_new)
      r = requests.get(post_location_new, headers=headers, data=initial_data)

    r_format = json.loads(r.content)
    result_array[i] = r_format
    i = i + 1
    has_more = r_format['has_more']

  return result_array
  #r = requests.get(post_location,headers=headers)
  #returned_data = json.loads(r.content)
  #return returned_data


def add_database_relation(key, database_to_update, page_name_field,
                          page_name_to_update, field_to_update,
                          id_relation_to_add):

  #Step 1: Pull pages current relation data
  page = find_page_in_database(key, database_to_update, page_name_field,
                               page_name_to_update)
  print(page)
  if len(page['results']) > 1:
    return "Error - multiple pages with that name"
  id_to_update = page['results'][0]['id']
  existing_property = page['results'][0]['properties'][field_to_update]
  #print(existing_property)

  #Step 2: Build value to append
  value_to_append = existing_property['relation']
  value_to_append.append({'id': id_relation_to_add})
  #print(value_to_append)

  #Step 3: Update the field
  update_page_property(key, id_to_update, field_to_update, 'relation',
                       value_to_append)


def add_database_relation_direct(key, page_id, field_to_update,
                                 id_relation_to_add):
  #Grab the page
  page = pull_single_page(key, page_id)
  #Grab the property
  existing_property = page['properties'][field_to_update]
  #print(existing_property)

  #Step 2: Build value to append
  value_to_append = existing_property['relation']
  value_to_append.append({'id': id_relation_to_add})
  #print(value_to_append)

  #Step 3: Update the field
  update_page_property(key, page_id, field_to_update, 'relation',
                       value_to_append)


def get_property_value(property_object):
  try:
    p_type = property_object['type']
    sub_type = ''
    if p_type == 'rollup':
      sub_type = property_object['rollup']['type']
    if p_type == 'number':
      return [p_type, property_object['number']]
    if p_type == 'string':
      return [p_type, property_object['string']]
    if p_type == 'rich_text':
      return [p_type, property_object['rich_text'][0]['text']['content']]
    if p_type == 'select':
      return [p_type, property_object['select']['name']]
    if p_type == 'multiselect':
      return [p_type, property_object[multi_select]]
    if p_type == 'relation':
      return [p_type, property_object['relation']]
    if p_type == 'date':
      if property_object['date']['end'] == None:
        return [p_type, property_object['date']['start']]
      else:
        return [p_type + '_range', property_object['date']['start']
                ]  # ,property_object['date']['end']]]
    if p_type == 'formula':
      sub_type = property_object['formula']['type']
    if p_type == 'title':
      sub_type = property_object['title'][0]['type']
      if sub_type == 'text':
        return [p_type, property_object['title'][0]['text']['content']]

    if sub_type == 'string':
      return [p_type, property_object[p_type]['string']]
    if sub_type == 'number':
      return [p_type, property_object[p_type]['number']]
    if sub_type == 'boolean':
      return [p_type, property_object[p_type]['boolean']]
    if sub_type == 'date':
      return [p_type, property_object[p_type]['date']['start']]

    return ['Error', None]
  except:
    return ['Error', None]


def get_block_content(block):
  ctr = ''
  b_type = block['type']

  c_type = 'text'
  if 'text' in block[b_type]:
    c_type = 'text'
  elif 'rich_text' in block[b_type]:
    c_type = 'rich_text'

  bt_length = len(block[b_type][c_type])

  if bt_length > 0:
    for j in block[b_type][c_type]:
      ctr += j['text']['content']

  return ctr


def link_by_date_to_month(key, db_to_link, page_id, date, month_field,
                          month_db, month_date_field):
  # Do stuff to find the id we need to add
  # get the actual day number
  new_date = datetime.strptime(date, '%Y-%m-%d')
  print(new_date)
  day_num = new_date.strftime("%d")
  print(day_num)
  # subtract those number of days from input date
  # using the timedelta
  month_start_date = new_date - timedelta(days=int(day_num) - 1)
  print(str(month_start_date.strftime('%Y-%m-%d')))
  month_page = find_page_in_database_by_date(
    key, month_db, month_date_field,
    str(month_start_date.strftime('%Y-%m-%d')))

  #print(month_page)
  id_relation_to_add = month_page['results'][0]['id']
  # Add the relation
  add_database_relation_direct(key, page_id, month_field, id_relation_to_add)


def link_by_date_to_week(key, db_to_link, page_id, date, week_field, week_db,
                         week_date_field):
  # Do stuff to find the id we need to add
  # get the actual day number
  new_date = datetime.strptime(date, '%Y-%m-%d')
  # subtract those number of days from input date
  # using the timedelta

  week_page = find_page_in_database_recent_week(key, week_db, week_date_field,
                                                new_date)

  #print(month_page)
  id_relation_to_add = week_page['results'][0]['id']
  # Add the relation
  add_database_relation_direct(key, page_id, week_field, id_relation_to_add)
