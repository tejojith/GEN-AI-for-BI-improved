# app.py - Fixed version with dynamic chart filtering

from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
import os, shutil
from werkzeug.utils import secure_filename
from markupsafe import escape
import pandas as pd
from geminiAi import generate_kpi, generate_chart, generate_imp_kpi_info, check_db
import json
import re
from charts import bar_chart, line_chart, scatter_chart
from timeit import default_timer as timer
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

from chart_func import get_charts_output
from key_func import get_json_ai, get_all_keys, allowed_file

file_storage_folder = config['PATHS']['FILE_STORAGE_FOLDER']
file_chunck_path = config['PATHS']['FILE_CHUNCK_PATH']
ALLOWED_EXTENSIONS = {'txt', 'csv', 'xlsx'}
charts_storage = config['PATHS']['CHARTS_STORAGE']
charts_archive_storage = config['PATHS']['CHARTS_ARCHIVE_STORAGE']

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = file_storage_folder


chart_configs = {}  # Store chart configurations for dynamic filtering


 # Assuming df is your DataFrame and 'datetime_column' is your datetime column
   
   
    # df['datetime_column'] = pd.to_datetime(df['datetime_column'])  # Convert to datetime if not already
    # df['year_id'] = df['datetime_column'].dt.year
    # df['month_id'] = df['datetime_column'].dt.month


@app.route('/', methods=['GET', 'POST'])
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        print(request.files)
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('DfViewer', name=filename))
    return render_template('homepage.html')

@app.route('/DfViewer/<name>')

def DfViewer(name):
    file_type = 'comma'
    default_encoding = 'utf-8'
    
    # Archive existing charts
    for filename in os.listdir(charts_storage):
        file_path = os.path.join(charts_storage, filename)
        archive_path = os.path.join(charts_archive_storage, filename)
        shutil.move(file_path, archive_path)
    
    # Determine file type
    if name.endswith('xlsx'):
        file_type = 'Excel'
    elif name.endswith('csv'):
        try:
            with open(os.path.join(file_storage_folder, name), 'r') as file:
                lines = [file.readline() for _ in range(100)]
            if any(',' in line for line in lines):
                file_type = 'comma'
            elif any('|' in line for line in lines):
                file_type = 'pipe'
        except:
            file_type = 'comma'
    
    # Create chunk file and read data
    try:
        chunk_file_name = str(name.split('.')[0]) + '_chunk.' + str(name.split('.')[-1])
        with open(os.path.join(file_storage_folder, name), 'r') as input_file:
            first_5_lines = input_file.readlines()[:5]
        with open(os.path.join(file_chunck_path, chunk_file_name), 'w') as output_file:
            output_file.writelines(first_5_lines)
        
        if file_type == 'pipe':
            df = pd.read_csv(os.path.join(file_chunck_path, chunk_file_name), sep='|', encoding=default_encoding)
        else:
            df = pd.read_csv(os.path.join(file_chunck_path, chunk_file_name), encoding=default_encoding)
    except UnicodeDecodeError:
        default_encoding = 'latin-1'
        df = pd.read_csv(os.path.join(file_storage_folder, name), encoding=default_encoding)
    
    # text = check_db(name)
    text = "test"

    df.columns = df.columns.str.upper() 
    return render_template('DataFrame.html', tables=[df.to_html()], name=name, 
                         file_type=file_type, default_encoding=default_encoding, titles=[''])

@app.route('/genBi/<name>', methods=['GET'])
def gen_bi(name):
    
    
    try:
        df = pd.read_csv(os.path.join(file_storage_folder, name))
    except UnicodeDecodeError:
        df = pd.read_csv(os.path.join(file_storage_folder, name), encoding='latin-1')

    df.columns = df.columns.str.upper()
    column_list = list(df.columns)

    #to separate into year_id and month_id
    ai_response = check_db(column_list)
    ai_response = ai_response.split('\n')[0].strip()
    if ai_response == "None":
        pass
    else:
        # Convert to datetime
        df[f"{ai_response}"] = pd.to_datetime(df[f"{ai_response}"])

        # Extract year and month
        df["YEAR_ID"] = df[f"{ai_response}"].dt.year
        df["MONTH_ID"] = df[f"{ai_response}"].dt.month

    # Get unique years/months for filter dropdowns (from full dataset)
    unique_years = sorted(df['YEAR_ID'].dropna().unique().tolist()) if 'YEAR_ID' in df.columns else []
    unique_months = sorted(df['MONTH_ID'].dropna().unique().tolist()) if 'MONTH_ID' in df.columns else []

    start_time = timer()
    global chart_configs
    # Generate KPIs and charts only once
    if name not in chart_configs:
        for i in range(3):
            ai_check = -1
            retries = 0
            max_retries = 5

            while ai_check < 0 and retries < max_retries:
                ai_response = generate_kpi(df_columns=column_list)
                start_ai = ai_response.find('{')
                end_ai = ai_response.rfind('}')
                ai_check = get_json_ai(ai_response=ai_response, start_ai=start_ai, end_ai=end_ai)
                print(f"Attempt {retries + 1}: The KPI response {ai_response}")
                retries += 1

            if ai_check < 0:
                return "Internal Server Error: Failed to generate valid KPI JSON from Gemini API", 500

            json_response = json.loads(ai_response[start_ai:end_ai + 1])
            json_keys_list = list(get_all_keys(json_response))

            for json_metadata in json_keys_list:
                if json_metadata.lower() == 'kpis':
                    json_header = json_metadata
                elif re.search('columns', json_metadata.lower()):
                    json_column = json_metadata
                else:
                    json_kpi_key = json_metadata

            actual_display = {}
            for data in json_response[json_header]:
                if len(data[json_column]) > 1:
                    actual_display[data[json_kpi_key]] = ','.join(data[json_column])

            try:
                output = -1
                while output < 0:
                    ai_chart_response = generate_chart(kpi_data=actual_display)
                    start_chart_ai = ai_chart_response.find('{')
                    end_chart_ai = ai_chart_response.rfind('}')
                    actual_chart_resp = json.loads(ai_chart_response[start_chart_ai:end_chart_ai + 1])

                    valid_cols = set(df.columns)
                    actual_chart_resp["metrics"] = [
                        m for m in actual_chart_resp["metrics"]
                        if m["x_axis"] in valid_cols and m["aggregation_column"] in valid_cols
                    ]

                    output = get_charts_output(df=df, actual_resp=actual_chart_resp)
                    
                    # Store chart configuration for dynamic filtering
                    chart_configs[name] = actual_chart_resp
                    
            except Exception as e:
                print(f"Got the below exception {str(e)}")

    # Generate charts with current filters
    selected_year = request.args.get('time_filter')
    selected_month = request.args.get('month_filter')


    filtered_df = df.copy()
    if selected_year and 'YEAR_ID' in df.columns:
        filtered_df = filtered_df[filtered_df['YEAR_ID'] == int(selected_year)]
    if selected_month and 'MONTH_ID' in df.columns:
        filtered_df = filtered_df[filtered_df['MONTH_ID'] == int(selected_month)]
    
    # Generate charts with filtered data
    if name in chart_configs:
        get_charts_output(df=filtered_df, actual_resp=chart_configs[name])

    files = os.listdir(charts_storage)
    html_files = [f'charts_storage/{f}' for f in files if os.path.isfile(os.path.join(charts_storage, f))]

    kpi_ai_list = [f.replace("charts_storage/", "").replace("_", " ").split(".")[0] for f in html_files]
    imp_kpi_list_display = generate_imp_kpi_info(kpi_ai_list)
    imp_kpi_list_display = imp_kpi_list_display.split('\n')
    imp1 = imp_kpi_list_display[0].strip()
    imp2 = imp_kpi_list_display[2].strip()
    imp3 = imp_kpi_list_display[4].strip()
    print(imp_kpi_list_display)
    
    end_time = timer()
    print(f"Processing time: {end_time - start_time}")

    return render_template('AiOnBi.html',
                           imp1=imp1,
                           imp2=imp2,
                           imp3=imp3,
                           name=name,
                           html_files=html_files,
                           unique_years=unique_years,
                           unique_months=unique_months,
                           selected_year=selected_year,
                           selected_month=selected_month)

@app.route('/filterCharts/<name>')
def filter_charts(name):
    """Dynamic chart filtering endpoint"""
    global chart_configs
    
    selected_year = request.args.get('time_filter')
    selected_month = request.args.get('month_filter')

    try:
        df = pd.read_csv(os.path.join(file_storage_folder, name))
    except UnicodeDecodeError:
        df = pd.read_csv(os.path.join(file_storage_folder, name), encoding='latin-1')

    df.columns = df.columns.str.upper()

    # Apply filters
    if selected_year and 'YEAR_ID' in df.columns:
        try:
            df = df[df['YEAR_ID'] == int(selected_year)]
        except ValueError:
            pass
    
    if selected_month and 'MONTH_ID' in df.columns:
        try:
            df = df[df['MONTH_ID'] == int(selected_month)]
        except ValueError:
            pass
    highlight = request.args.get('highlight')
    v1 = request.args.get('v1')  # format: '2024-3'
    v2 = request.args.get('v2')

    values1 = [tuple(map(int, v1.split('-')))] if v1 else []
    values2 = [tuple(map(int, v2.split('-')))] if v2 else []

    # Use stored chart configuration instead of calling Gemini again
    #most imp
    if name in chart_configs:
        get_charts_output(df=df, actual_resp=chart_configs[name],value1=values1, value2=values2)
    else:
        # Fallback: regenerate if config not found
        column_list = list(df.columns)
        ai_response = generate_kpi(df_columns=column_list)
        start_ai = ai_response.find('{')
        end_ai = ai_response.rfind('}')
        json_response = json.loads(ai_response[start_ai:end_ai + 1])
        
        actual_display = {
            kpi["KPI"]: ','.join(kpi["Columns"])
            for kpi in json_response.get("KPIs", []) if len(kpi["Columns"]) > 1
        }

        chart_response = generate_chart(kpi_data=actual_display)
        start = chart_response.find('{')
        end = chart_response.rfind('}')
        actual_chart_resp = json.loads(chart_response[start:end + 1])

        valid_cols = set(df.columns)
        actual_chart_resp["metrics"] = [
            m for m in actual_chart_resp["metrics"]
            if m["x_axis"] in valid_cols and m["aggregation_column"] in valid_cols
        ]

        get_charts_output(df, actual_chart_resp)
        chart_configs[name] = actual_chart_resp

    html_files = [f for f in os.listdir(charts_storage) if f.endswith('.html')]
    html_files_with_path = [f'charts_storage/{f}' for f in html_files]

    return render_template("chart_iframes.html", html_files=html_files_with_path)

if __name__ == "__main__":
    app.run(debug=True)