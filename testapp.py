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

def get_json_ai(ai_response,start_ai,end_ai):
    try:
        json.loads(ai_response[start_ai:end_ai+1])
        return 0
    except Exception as e:
        print(f"Got the below error while converting to JSON :{e}")
        return -1
      

def get_charts_output(actual_resp, df):
    try:
        for i in actual_resp["metrics"]:
            x_col = i["x_axis"]
            agg_col = i["aggregation_column"]
            chart_type = i["chart_type"].lower()
            agg_type = i["aggregation_type"].upper()
            chart_name = i["name"].replace(" ", "_")

            # Check if required columns exist
            if x_col not in df.columns or agg_col not in df.columns:
                print(f"Skipping chart '{i['name']}': column not found.")
                continue

            # If AVG/SUM is requested, aggregation_column must be numeric
            if agg_type in ['SUM', 'AVG'] and not pd.api.types.is_numeric_dtype(df[agg_col]):
                print(f"Skipping chart '{i['name']}': aggregation column {agg_col} is not numeric.")
                continue

            # If COUNT is requested, we can proceed even with object types
            if chart_type == 'line':
                if agg_type == 'SUM':
                    agg_df = df.groupby(x_col)[agg_col].sum().reset_index()
                elif agg_type == 'AVG':
                    agg_df = df.groupby(x_col)[agg_col].mean().reset_index()
                elif agg_type == 'COUNT':
                    agg_df = df.groupby(x_col)[agg_col].count().reset_index()
                else:
                    continue
                fig = line_chart(df_data=agg_df, x_axis=x_col, y_axis=i["y_axis"], kpi_name=i["name"])

            elif chart_type == 'bar':
                if agg_type == 'SUM':
                    agg_df = df.groupby(x_col)[agg_col].sum().reset_index()
                elif agg_type == 'AVG':
                    agg_df = df.groupby(x_col)[agg_col].mean().reset_index()
                elif agg_type == 'COUNT':
                    agg_df = df.groupby(x_col)[agg_col].count().reset_index()
                else:
                    continue
                fig = bar_chart(df_data=agg_df, x_axis=x_col, y_axis=i["y_axis"], kpi_name=i["name"])

            elif chart_type == 'scatter':
                if pd.api.types.is_numeric_dtype(df[x_col]) and pd.api.types.is_numeric_dtype(df[agg_col]):
                    fig = scatter_chart(df_data=df, x_axis=x_col, y_axis=agg_col, kpi_name=i["name"])
                else:
                    print(f"Skipping scatter chart '{i['name']}': non-numeric axes.")
                    continue

            else:
                print(f"Unsupported chart type: {chart_type}")
                continue

            fig.write_html(os.path.join(charts_storage, f'{chart_name}.html'))

        return 0
    except Exception as e:
        print(f"Got the below exception {str(e)}")
        return -1

# def save_html_chart(chart, filename):
#     # Save the HTML representation of the chart to a file
#     with open(os.path.join(charts_storage, filename), 'w') as file:
#         file.write(chart.to_html(full_html=False))  

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = file_storage_folder

@app.route('/', methods=['GET', 'POST'])
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        print(request.files)
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            print(url_for('DfViewer',name=filename))
            return redirect(url_for('DfViewer',name=filename))
    return render_template('homepage.html')

@app.route('/DfViewer/<name>')
def DfViewer(name):
    file_type=f'comma'
    default_encoding='utf-8'
    for filename in os.listdir(charts_storage):
        file_path = os.path.join(charts_storage, filename)
        archive_path=os.path.join(charts_archive_storage, filename)
        shutil.move(file_path, archive_path)
    if name.endswith('xlsx'):
        file_type='Excel'
    elif name.endswith('csv'):
        try:
            with open(os.path.join(file_storage_folder,name), 'r') as file:
                lines = [file.readline() for _ in range(5)]
            # Check for comma (CSV) and pipe (PSV) separators
            if any(',' in line for line in lines):
                file_type= 'comma'
            elif any('|' in line for line in lines):
                file_type= 'pipe'                
        except:
                file_type= 'comma'
    try:
        chunk_file_name=str(name.split('.')[0])+'_chunk.'+str(name.split('.')[-1])
        with open(os.path.join(file_storage_folder,name), 'r') as input_file:
            first_5_lines = input_file.readlines()[:5]
        with open(os.path.join(file_chunck_path,chunk_file_name), 'w') as output_file:
            output_file.writelines(first_5_lines)
        if file_type=='pipe':
            df=pd.read_csv(os.path.join(file_chunck_path,chunk_file_name),sep='|',encoding=default_encoding)
        else:
            df=pd.read_csv(os.path.join(file_chunck_path,chunk_file_name),encoding=default_encoding)
    except UnicodeDecodeError as unerr:
        default_encoding='latin-1'
        df=pd.read_csv(os.path.join(file_storage_folder,name), encoding=default_encoding)
    df.columns = df.columns.str.upper()
    return render_template('DataFrame.html', tables=[df.to_html()], name=name,file_type=file_type,default_encoding=default_encoding,titles=[''])

@app.route('/genBi/<name>', methods=['GET', 'POST'])
def gen_bi(name):
    try:
        df = pd.read_csv(os.path.join(file_storage_folder, name))
    except UnicodeDecodeError:
        df = pd.read_csv(os.path.join(file_storage_folder, name), encoding='latin-1')

    df.columns = df.columns.str.upper()
    column_list = list(df.columns)
    start_time = timer()
    
     # Handle time filtering
    selected_year = request.args.get('time_filter')
    if selected_year and 'YEAR_ID' in df.columns:
        try:
            df = df[df['YEAR_ID'] == int(selected_year)]
        except ValueError:
            pass  # fallback in case of invalid year input
    # Get all unique years for the dropdown filter
    unique_years = sorted(df['YEAR_ID'].dropna().unique().tolist()) if 'YEAR_ID' in df.columns else []

    start_time = timer()

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
        print(f" The Actual KPI shown {json_response}")
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
                # Filter out any chart using columns not present in the dataset - added by me
                valid_cols = set(df.columns)
                actual_chart_resp["metrics"] = [
                    m for m in actual_chart_resp["metrics"]
                    if m["x_axis"] in valid_cols and m["aggregation_column"] in valid_cols
                ]
                print(f" The Actual chart shown {actual_chart_resp}")

                output = get_charts_output(df=df, actual_resp=actual_chart_resp)
        except Exception as e:
            print(f"Got the below exception {str(e)}")

    files = os.listdir(charts_storage)
    html_files = [f'charts_storage/{f}' for f in files if os.path.isfile(os.path.join(charts_storage, f))]

    kpi_ai_list = [f.replace("charts_storage/", "").replace("_", " ").split(".")[0] for f in html_files]
    imp_kpi_list_display = generate_imp_kpi_info(kpi_ai_list)
    end_time = timer()
    print(end_time - start_time)

    return render_template('AiOnBi.html', 
                           kpi_response=imp_kpi_list_display, 
                           name=name,
                           unique_years=unique_years,
                           selected_year=selected_year, 
                           html_files=html_files)   

@app.route('/filterCharts/<name>')
def filter_charts(name):
    time_filter = request.args.get('time_filter')

    try:
        df = pd.read_csv(os.path.join(file_storage_folder, name))
    except UnicodeDecodeError:
        df = pd.read_csv(os.path.join(file_storage_folder, name), encoding='latin-1')

    df.columns = df.columns.str.upper()

    if time_filter and 'YEAR_ID' in df.columns:
        try:
            df = df[df['YEAR_ID'] == int(time_filter)]
        except ValueError:
            pass

    # Run Gemini again
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

    get_charts_output(actual_chart_resp, df)

    html_files = [f for f in os.listdir(charts_storage) if f.endswith('.html')]

    return render_template("chart_iframes.html", html_files=html_files)

if __name__=="__main__":
    app.run(debug=True)