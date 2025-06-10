import google.generativeai as genai
import configparser
import pandas as pd

config = configparser.ConfigParser()
config.read('config.ini')

genai.configure(api_key=config['AI API']['GEMINI_API_KEY'])

model = genai.GenerativeModel('gemini-1.5-pro')
no_of_kpi=10
def generate_kpi(df_columns):
    response = model.generate_content(f'''You are a retail Business intelligence Engineer.
                                      Provide the most important {no_of_kpi} KPI's and the column names
                                      from the below list of columns {','.join(df_columns)}.
                                      Ensure you use only these columns: {','.join(df_columns)}. Do not include any columns not listed.
                                      You should provide atleast 2 columns for 1 KPI.
                                      Please make sure you provide the output strictly in the below example json format, do not enter any new keys. Example:
                                      {{"KPIs": 
                                        [{{
                                            "KPI": "Total Sales", "Columns": ['SALES'] ['YEAR_ID']
                                            }}
                                         ],   
                                        }}
                                      ''')
    return response.text

def generate_chart(kpi_data):
    response = model.generate_content(f'''You are a retail Business intelligence Engineer.
                                      For the list of KPIs and columns {kpi_data},
                                      provide me the x-axis and y-axis for the columns and type of chart.
                                      You should provide atleast 1 chart for a KPI.
                                      Do not include any columns not listed.
                                      Please make sure you provide the output strictly in the below example format only, do not add any new keys. Do not make any change in the format.
                                        Example: for KPI:Monthly Sales Trend and columns MONTH_ID,SALES:                                       
                                        {{"metrics": [
                                            {{
                                            "name": "Monthly Sales Trend",
                                            "x_axis": "MONTH_ID",
                                            "y_axis": "SALES",
                                            "x_label": "Months",
                                            "y_label": "Sales"
                                            "aggregation_column": "SALES"
                                            "aggregation_type": "SUM"
                                            "chart_type": "line"
                                            }}
                                            ]  
                                            }}                                             
                                      ''')
    return response.text

def generate_imp_kpi_info(kpi_name_list):
  response = model.generate_content(f'''You are a retail Business intelligence Engineer.
                                      Out of the list of below KPIs: {kpi_name_list},
                                      Provide me the most important 3 KPIS and a definition restricted to 50 words only for each KPI.
                                      Strictly follow the KPI list, do not add any new KPI.
                                      If the list is small then 3 then provide the KPI information only for that.
                                      give the output in line by line give end of line character    
                                      ''')
  return response.text

def check_db(df_columns):
  response = model.generate_content(f'''You are a data engineer.
                                      Out of the list of table headings: {df_columns},
                                      check if there is a table heading with date or time and give me the columns to separate it to get year_id and month_id.
                                      If there is no date or time column then return "No date or time column found".
                                          
                                      ''')
  return response.text


    
