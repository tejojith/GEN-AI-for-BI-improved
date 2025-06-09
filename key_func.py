from flask import Flask,render_template, request, flash, redirect, url_for
import os,shutil
from werkzeug.utils import secure_filename
from markupsafe import escape
import pandas as pd
from geminiAi import generate_kpi,generate_chart,generate_imp_kpi_info
# from openai_gen import generate_kpi,generate_chart,generate_imp_kpi_info
import json
import re
from charts import bar_chart, line_chart, scatter_chart
from timeit import default_timer as timer
import configparser
config = configparser.ConfigParser()
config.read('config.ini')


file_storage_folder=config['PATHS']['FILE_STORAGE_FOLDER']
file_chunck_path=config['PATHS']['FILE_CHUNCK_PATH']
ALLOWED_EXTENSIONS = {'txt', 'csv', 'xlsx'}
charts_storage=config['PATHS']['CHARTS_STORAGE']
charts_archive_storage=config['PATHS']['CHARTS_ARCHIVE_STORAGE']


      

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_json_ai(ai_response,start_ai,end_ai):
    try:
        json.loads(ai_response[start_ai:end_ai+1])
        return 0
    except Exception as e:
        print(f"Got the below error while converting to JSON :{e}")
        return -1
    

def get_all_keys(json_data):
    keys = set()

    if isinstance(json_data, dict):
        for key, value in json_data.items():
            keys.add(key)
            keys.update(get_all_keys(value))
    elif isinstance(json_data, list):
        for item in json_data:
            keys.update(get_all_keys(item))

    return keys