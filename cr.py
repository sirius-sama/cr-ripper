#!/usr/bin/python

import os
import json
import glob
import time
import cli_ui
import shutil
import argparse
import requests
import subprocess
from data import config
from pymediainfo import MediaInfo

# Global variables
current_directory = os.getcwd()
output_directory = current_directory
cookies = f"{current_directory}/src/cookies/cr-cookies.txt"
config = config.config


# Argparse arguments
parser = argparse.ArgumentParser(description='This script rips content from crunchyroll')

parser.add_argument('URL', type=str, metavar='URL...', help='URL of the episode')
parser.add_argument('-res', '--resolution', type=str, metavar='', required=False, nargs='?', default='1080', help='Choose the resolution of the episode', choices=['240', '360', '480', '720', '1080'])
parser.add_argument('-title', '--title', action='store_true', required=False, help='Use episode name in title')
parser.add_argument('-pro', '--pro', action='store_true', required=False, help='Premium episode')
parser.add_argument('-tag', '--tag', type=str, metavar='', required=False, nargs='?', default=str(config['tag']), help='Name of the release group')


args = parser.parse_args()

meta = vars(args)

# Get info.json file of the episode

# Checking crunchyroll version (free of premium)
if args.pro == True:
    info_json_cmd = f"yt-dlp --external-downloader aria2c {meta['URL']} --cookies '{cookies}' -f 'best[height={meta['resolution']}]' --no-progress --write-info-json --no-download --cookies '{cookies}' -o '{current_directory}/episode.%(ext)s'"
else:
    info_json_cmd = f"yt-dlp --external-downloader aria2c {meta['URL']} -f 'best[height={meta['resolution']}]' --no-progress --write-info-json --no-download -o '{current_directory}/episode.%(ext)s'"


cli_ui.info(cli_ui.blue, "Gathering episode info.json file...")

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
else:
    season = f"S{meta['episode_info']['season_number']}"


if meta['episode_info']['season_number'] == 0:
    season = 'S01'

if meta['episode_info']['episode_number'] < 10:
    episode = f"E0{meta['episode_info']['episode_number']}"
else:
    episode = f"E{meta['episode_info']['episode_number']}"



if args.title == True:
    ep_name = meta['episode_info']['episode']
    ep_name = ep_name.replace('&','and').replace('~','').replace(':.',': ')
else:
    ep_name = ''



properTitle = f"{meta['episode_info']['series']}.{season}{episode}.{ep_name}.{meta['episode_info']['height']}.CR.WEB-DL.AAC2.0.H.264-{args.tag}"
properTitle = properTitle.replace(' ', '.').replace(':','.').replace('..','.')



# Checking crunchyroll version (free of premium)
if args.pro == True:
    download_cmd = f"yt-dlp --external-downloader aria2c {meta['URL']} --cookies '{cookies}' -f 'best[height={meta['episode_info']['height']}]' --write-subs --sub-langs 'en.*' -o '{current_directory}/[RAW]{properTitle}.%(ext)s'"
else:
    download_cmd = f"yt-dlp --external-downloader aria2c {meta['URL']} -f 'best[height={meta['episode_info']['height']}]' --write-subs --sub-langs 'en.*' -o '{current_directory}/[RAW]{properTitle}.%(ext)s'"


cli_ui.info(cli_ui.blue, "Downloading raw video and subtitles...")

info_json = subprocess.Popen(download_cmd, shell=True, text=True)
info_json.wait()

cli_ui.info(cli_ui.green, "Download has been finished.")


# Getting subtitle file location
result = [f for f in glob.glob('*US.ass') if f'{properTitle}']

for f in result:
    subtitle_file = os.path.abspath(f)


# Muxing
muxing_cmd = f"ffmpeg -i '[RAW]{properTitle}.mp4' -i '{subtitle_file}' -vcodec copy -acodec copy -map 0 -map 1 -metadata:s:a:0 language=jpn -metadata:s:s:0 language=eng -metadata:s:s:0 title=English -disposition:s:0 default -c copy {properTitle}.mkv"

muxing = subprocess.Popen(muxing_cmd, shell=True, text=True)

muxing.wait()

cli_ui.info(cli_ui.green, "Muxing has been finished.")


# Moving files meta info to tmp folder
folder_path = f"{current_directory}/tmp/{properTitle}"
if not os.path.exists(folder_path):
    os.makedirs(folder_path)

cli_ui.info(cli_ui.magenta, "Moving meta.json to", cli_ui.bold, f"{folder_path}")
shutil.move(f"{current_directory}/meta.json", f"{folder_path}/meta.json")


# Cleaning up RAW video and subtitle
raw_files = glob.glob(f'*{properTitle}*')

for raw_file in raw_files:
    cli_ui.info(cli_ui.red, "Removing", cli_ui.red, cli_ui.bold, f"{raw_file}")
    os.remove(os.path.abspath(raw_file))


cli_ui.info(cli_ui.yellow, cli_ui.bold, "Done :)")