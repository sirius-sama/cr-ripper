import os
import json
import time
import argparse
import requests
from pymediainfo import MediaInfo

# Global variables
current_directory = os.getcwd()
output_directory = current_directory


# Argparse arguments
parser = argparse.ArgumentParser(description='This script rips content from crunchyroll')

parser.add_argument('URL', type=str, metavar='URL...', help='URL of the episode')
parser.add_argument('-res', '--resolution', type=int, metavar='', required=False, default='1080', nargs='?', help='Choose the resolution of the episode', choices=['1080', '720', '480'])
parser.add_argument('-tag', '--tag', type=str, metavar='', required=False, nargs='?', help='Name of the release group')


args = parser.parse_args()

meta = vars(args)