import click
import json
import os
import requests
import sys
import yaml

script_dir = os.path.dirname(__file__)
credentials = yaml.load(open(os.path.join(script_dir, 'credentials.yaml')))

DEFAULT_MESSAGE_USERS_FILTER = 'U75GYH87J,U75UEBVGE'
DEFAULT_CHANNEL_ID = 'C03DZSU21'
DEFAULT_REACTION = 'onit'
DEFAULT_MESSAGE_COUNT = 3000
DEFAULT_FILENAME = 'slack'

MESSAGE_LIMIT_PER_RESPONSE = 1000


def create_csv(filename):
  print 'Creating CSV'
  return open(os.path.join(script_dir, 'output/{}.csv'.format(filename)), 'w')


def add_two_column_row(column_1, column_2, csv):
  csv.write('{}, {}\n'.format(column_1, column_2))


def filter_messages(messages, user_filter):
  messages_to_filter = []
  if user_filter is not None:
    print 'Filtering {} messages for user(s) {}'.format(len(messages), user_filter)
    for message in messages:
      if 'user' in message and message['user'] in user_filter.split(','):
        messages_to_filter.append(message)
  else:
    print 'Not filtering by user ID'
    messages_to_filter = messages
  messages_with_reactions = list(filter(lambda x: 'reactions' in x, messages_to_filter))
  print '{} messages from user with reactions filtered'.format(len(messages_with_reactions))
  return messages_with_reactions


def create_assignee_list(messages, users, reaction):
  assignees = [];
  for message in messages:
    found_reaction = list(filter(lambda x: 'name' in x and x['name'] == reaction, message['reactions']))
    if len(found_reaction):
      assignees = assignees + found_reaction[0]['users']
  assignee_list = list(map(lambda x: list(filter(lambda y: y['id'] == x, users))[0]['name'], assignees));
  print '{} user reactions found for "{}" emoji'.format(len(assignee_list), reaction)
  return assignee_list


def calculate_and_write_totals(assignees, csv):
  unique_assignees = set(assignees)
  if len(unique_assignees):
    print 'Assignee List:'
    for assignee in unique_assignees:
      print ' - {}: {}'.format(assignee, assignees.count(assignee))
      add_two_column_row(assignee, assignees.count(assignee), csv)


def make_slack_api_request(url, params=None):
  headers = {
    'Authorization': 'Bearer {}'.format(credentials['slack_api_token']),
    'content-type': 'application/json'
  }
  return requests.get(url, params=params, headers=headers)


def fetch_users():
  print 'Fetching users'
  users_request = make_slack_api_request('https://slack.com/api/users.list')
  try:
    users = users_request.json()['members']
  except Exception as e:
    print e
    users = []

  print '{} users fetched'.format(len(users))
  return users


def fetch_messages(channel_id, messages_to_fetch, latest=None, messages=[]):
  print 'Fetching messages for channel ID {} - {} more to go'.format(channel_id, messages_to_fetch)
  all_messages = messages

  if messages_to_fetch == 0:
    print '{} messages fetched'.format(len(messages))
    return messages
  elif messages_to_fetch > MESSAGE_LIMIT_PER_RESPONSE:
    msg_count = MESSAGE_LIMIT_PER_RESPONSE
    messages_left = messages_to_fetch - msg_count
  else:
    msg_count = messages_to_fetch
    messages_left = 0

  try:
    msgs_request = make_slack_api_request('https://slack.com/api/channels.history', {
      'channel': channel_id,
      'count': msg_count,
      'inclusive': True,
      'latest': latest,
    })
    messages_fetched = msgs_request.json()['messages']
    all_messages = messages + messages_fetched
    latest = messages_fetched[-1]['ts']
    return fetch_messages(channel_id, messages_left, latest, all_messages)
  except Exception as e:
    print e
    return []


def fetch_and_write_data(filename, channel_id, count):
  messages = fetch_messages(channel_id, count)
  users = fetch_users()
  combined_data = {}
  combined_data['messages'] = messages
  combined_data['users'] = users
  combined_data_file = open(os.path.join(script_dir, 'input/{}.json'.format(filename)), 'w')
  combined_data_file.write(json.dumps(combined_data, indent=2, separators=(',', ': ')));
  combined_data_file.close()


@click.command()
@click.option(
  '-f', '--fetch_data',
  is_flag=True,
  help='Fetch user and channel messages from Slack API'
)
@click.option(
  '-n', '--number_of_messages',
  default=DEFAULT_MESSAGE_COUNT,
  type=click.INT,
  help='Number of messages to fetch (n/a without -f param)'
)
@click.option(
  '-c', '--channel_id',
  default=DEFAULT_CHANNEL_ID,
  type=click.STRING,
  help='Slack Channel API ID to filter by (n/a without -f param)'
)
@click.option(
  '-t', '--filename',
  default=DEFAULT_FILENAME,
  type=click.STRING,
  help='Name of analysis CSV and user data files (the latter is n/a without -f param)'
)
@click.option(
  '-r', '--run_analysis',
  is_flag=True,
  help='Run analysis on available data'
)
@click.option(
  '-e', '--emoji_name',
  default=DEFAULT_REACTION,
  type=click.STRING,
  help='Name of emoji/reaction to run a per user analysis on'
)
@click.option(
  '-u', '--users_to_filter',
  default=DEFAULT_MESSAGE_USERS_FILTER,
  type=click.STRING,
  help='Comma separated string of Slack User API ID(s) to filter messages on (if provided, only reactions on this user(s) will be reported). Pass an empty string to search all messages.'
)
def main(fetch_data, number_of_messages, channel_id, filename, run_analysis, emoji_name, users_to_filter):
  print 'Slack Emoji User Analysis'
  print '____________________'
  if not fetch_data and not run_analysis:
    print 'Must specify either -f to fetch data or -a to analyze data'

  if fetch_data:
    fetch_and_write_data(filename, channel_id, number_of_messages)

  if run_analysis:
    with open(os.path.join(script_dir, 'input/{}.json'.format(filename))) as json_data:
      data = json.load(json_data)
      filtered_messages = filter_messages(data['messages'], (users_to_filter or None))
      assignee_list = create_assignee_list(filtered_messages, data['users'], emoji_name)
      analysis_csv = create_csv(filename)
      calculate_and_write_totals(assignee_list, analysis_csv)
      analysis_csv.close()


if __name__ == "__main__":
  main()

