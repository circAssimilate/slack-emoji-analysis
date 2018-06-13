# Slack Emoji Analysis

## Overview
Generates a CSV with Slack username and total number of reactions for a specified emoji. This 
script searches for an emoji, by name, for a specified channel. Many values are currently set by 
default - look at the defined constants in the top of `main.py` or run `python main.py --help` to learn more 

## Setup
1. In order to fetch data for consumption in this script, a `credentials.yaml` file should be created with this format:

```
slack_api_token: abcd-123456789-987654321
```

2. Create a token at https://api.slack.com/custom-integrations/legacy-tokens and add it to `credentials.yaml`
3. Run `mkdir input && mkdir output` in the root directory of the repo

## Running
Currently, many defaults are set for this script, but they can all be changed. Here's an example of how it can be ran:

```
python main.py --fetch_data --number_of_messages=5250 --channel_id='C03DZSU21' --filename='5250_messages' --run_analysis --emoji_name='onit' --user_to_filter='U75GYH87J'
```

Run `python main.py --help` to learn about the different configuration options.

## Notable Things
 * You may need to `pip install` some imported python libraries
 * Defaults are set for use in code review analysis, this will change in the future
 * Slack data will be dumped in `input/` and CSV analysis in `output/`
