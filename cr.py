#!/usr/bin/python

import os
import json
import glob
import time
import cli_ui
import shutil
import argparse
import requests
import feedparser
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

parser.add_argument('input', type=str, metavar='URL.../Keywords', help='URL/Keywords of the episode')
parser.add_argument('-an', '--alternative-name', type=str, metavar='', required=False, nargs='?', help='Alternative name of the series')
parser.add_argument('-s', '--season', type=str, metavar='', required=False, nargs='?', help='Season number')
parser.add_argument('-e', '--episode', type=str, metavar='', required=False, nargs='?', help='Episode number')
parser.add_argument('-ns', '--no-season', action='store_true', required=False, help='Do not include season number in the title')
parser.add_argument('-res', '--resolution', type=str, metavar='', required=False, nargs='?', default='1080', help='Choose the resolution of the episode', choices=['240', '360', '480', '720', '1080'])
parser.add_argument('-title', '--title', action='store_true', required=False, help='Use episode name in title')
parser.add_argument('-pro', '--pro', action='store_true', required=False, help='Premium episode')
parser.add_argument('-tag', '--tag', type=str, metavar='', required=False, nargs='?', default=str(config['tag']), help='Name of the release group')


args = parser.parse_args()

meta = vars(args)



# https://www.crunchyroll.com/watch/GEVUZM77J/dog--chainsaw

# So there is a changed to the plan. CR new web ui showing episode few mins after they aired. So we gotta fetch the episode link from their feed. So, there would be search() function, which will search user given name in the feed, if found then it'll grab the episode link and convert it to main cr link, then pass that link to download() function. And after finish downloading it'll send files (mp4, sub) to mux() function. So what happens when the user don't want to search and put the direct link of the episode???!!!! 



def searchKeywords():
    if "crunchyroll" in meta['input'] and ' ' not in meta['input']:
        meta['URL'] = meta['input']

        downloadAndMux(meta['URL'])
    else:
        meta['Keywords'] = meta['input']

        cr_feed = feedparser.parse('https://www.crunchyroll.com/rss/anime')

        cli_ui.info(cli_ui.green, "Searching for", cli_ui.bold, f"{meta['Keywords']}")

        for entry in cr_feed.entries:
            if str(meta['Keywords']) in entry.title and "Dub" not in entry.title:
                meta['URL'] = entry.link
                cli_ui.info(cli_ui.blue, "Match found for", cli_ui.bold, f"{meta['Keywords']}")
                cli_ui.info(cli_ui.blue, "Title:", cli_ui.bold, f"{entry.title}")
                cli_ui.info(cli_ui.blue, "Link:", cli_ui.bold, f"{entry.link}")

                # Convert feed link to proper CR link
                headers = {
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:105.0) Gecko/20100101 Firefox/105.0',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate, br'
                }

                with requests.Session() as session:
                    r = session.get(meta['URL'], headers=headers)
                    meta['URL'] = r.url
                
                cli_ui.info(cli_ui.blue, "Redirected Link:", cli_ui.bold, f"{meta['URL']}")    

                downloadAndMux(meta['URL'])
                break
        else:
            cli_ui.info(cli_ui.red, "Nothing found related to", cli_ui.bold, f"{meta['Keywords']}")
            cli_ui.info(cli_ui.red, "Going to sleep for 3 sec")
            time.sleep(3)
            cli_ui.info(cli_ui.green, "Searching again...")
            searchKeywords()


def downloadAndMux(URL):

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


    # Remove info.json file
    os.remove('episode.info.json')


    # CONDITION:: If user inputs custom "name", "season", "episode", then use them, if these args value are "None", then use desired info from the episode.info.json/meta.json

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
        ep_name = ep_name.replace('&','and').replace('~','').replace(':.',': ').replace(',','')
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
    ## FFMEPG command
    # muxing_cmd = f"ffmpeg -i '[RAW]{properTitle}.mp4' -i '{subtitle_file}' -vcodec copy -acodec copy -map 0 -map 1 -metadata:s:a:0 language=jpn -metadata:s:s:0 language=eng -metadata:s:s:0 title=English -disposition:s:0 default -c copy {properTitle}.mkv"

    ## MKVmerge command
    muxing_cmd = f"mkvmerge -o {properTitle}.mkv [RAW]{properTitle}.mp4 --language 0:en --track-name 0:'English' {subtitle_file}"

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
    raw_files = [f for f in glob.glob(f"*{properTitle}*") if "RAW" in f]

    for raw_file in raw_files:
        cli_ui.info(cli_ui.red, "Removing", cli_ui.red, cli_ui.bold, f"{raw_file}")
        os.remove(os.path.abspath(raw_file))


    cli_ui.info(cli_ui.yellow, cli_ui.bold, "Done :)")



searchKeywords()