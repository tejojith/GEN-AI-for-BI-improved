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

def get_charts_output(actual_resp, df, value1 = None, value2 = None):
    value1 = value1 or []
    value2 = value2 or []

    try:
        for i in actual_resp["metrics"]:
            x_col = i["x_axis"]
            agg_col = i["aggregation_column"]
            chart_type = i["chart_type"].lower()
            agg_type = i["aggregation_type"].upper()
            chart_name = i["name"].replace(" ", "_")

            if x_col not in df.columns or agg_col not in df.columns:
                continue

            if agg_type in ['SUM', 'AVG'] and not pd.api.types.is_numeric_dtype(df[agg_col]):
                continue

            if chart_type in ['bar', 'line']:
                if agg_type == 'SUM':
                    agg_df = df.groupby(x_col)[agg_col].sum().reset_index()
                elif agg_type == 'AVG':
                    agg_df = df.groupby(x_col)[agg_col].mean().reset_index()
                elif agg_type == 'COUNT':
                    agg_df = df.groupby(x_col)[agg_col].count().reset_index()
                else:
                    continue

                # Pass to chart function
                if chart_type == 'bar':
                    fig = bar_chart(agg_df, x_col, i["y_axis"], i["name"], df, value1, value2)
                else:
                    fig = line_chart(agg_df, x_col, i["y_axis"], i["name"], df, value1, value2)

            elif chart_type == 'scatter':
                if pd.api.types.is_numeric_dtype(df[x_col]) and pd.api.types.is_numeric_dtype(df[agg_col]):
                    fig = scatter_chart(df, x_col, agg_col, i["name"], value1=value1, value2=value2)
                else:
                    continue
            else:
                continue

            fig.write_html(os.path.join(charts_storage, f'{chart_name}.html'))

        return 0
    except Exception as e:
        print(f"Exception in get_charts_output: {str(e)}")
        return -1

# def save_html_chart(chart, filename):
#     # Save the HTML representation of the chart to a file
#     with open(os.path.join(charts_storage, filename), 'w') as file:
#         file.write(chart.to_html(full_html=False))  
