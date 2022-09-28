#!/usr/bin/python

import os
import json
import time
import argparse
import requests
import subprocess
from data import config
from pymediainfo import MediaInfo


# Global variables
current_directory = os.getcwd()
output_directory = current_directory
config = config.config


# Argparse arguments
parser = argparse.ArgumentParser(description='This script rips content from crunchyroll')

parser.add_argument('URL', type=str, metavar='URL...', help='URL of the episode')
parser.add_argument('-res', '--resolution', type=str, metavar='', required=False, nargs='?', default='1080', help='Choose the resolution of the episode', choices=['480', '720', '1080'])
parser.add_argument('-title', '--title', type=str, metavar='', required=False, nargs='?', default='y', help='Use this when you want to use episode name in the main title')
parser.add_argument('-tag', '--tag', type=str, metavar='', required=False, nargs='?', help='Name of the release group')


args = parser.parse_args()

meta = vars(args)


info_json_cmd = f"yt-dlp {meta['URL']} -f 'best[height={meta['resolution']}]' --no-progress --write-info-json --no-download -o '{current_directory}/episode.%(ext)s'"

print('Gathering episode info.json file...')

info_json = subprocess.Popen(info_json_cmd, shell=True, text=True)
info_json.wait()


with open('episode.info.json', 'r') as f:
    data = json.load(f)
    meta['episode_info'] = data

with open('meta.json', 'w') as f:
    json.dump(meta, f, indent=4)




# Make proper title
if meta['episode_info']['season_number'] < 10:
    season = f"S0{meta['episode_info']['season_number']}"

if meta['episode_info']['season_number'] == 0:
    season = 'S01'

if meta['episode_info']['episode_number'] < 10:
    episode = f"E0{meta['episode_info']['episode_number']}"




if meta['tag'] != 'null':
    tag = meta['tag']

elif meta['tag'] == 'null' and config['tag'] != '':
    tag = config['tag']

else:
    tag = 'NOGROUP'




if meta['title'] != 'y':
    ep_name = ''
else:
    ep_name = meta['episode_info']['episode']



properTitle = f"{meta['episode_info']['series']}.{season}{episode}.{ep_name}.{meta['resolution']}.CR.WEB-DL.AAC2.0.H.264-{tag}"
properTitle = properTitle.replace(' ', '.').replace('..','.')



# Start download
download_cmd = f"yt-dlp {meta['URL']} -f 'best[height={meta['resolution']}]' -o '{current_directory}/[RAW]{properTitle}.%(ext)s'"

print('Downloading raw video and subtitles...')

info_json = subprocess.Popen(download_cmd, shell=True, text=True)
info_json.wait()

print('Download Has been finished.')