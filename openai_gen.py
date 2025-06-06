from openai import OpenAI
import configparser
import json

# Load API key from config.ini
config = configparser.ConfigParser()
config.read('config.ini')

model_name = "gpt-4o-mini"
no_of_kpi = 10

client = OpenAI(
  api_key="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"
)


def generate_kpi(df_columns):
    prompt = f"""
You are a retail Business Intelligence Engineer.
Provide the most important {no_of_kpi} KPIs and their associated columns from this list: {', '.join(df_columns)}.
Each KPI should use at least 2 columns.
Output JSON strictly in this format:

{{
  "KPIs": [
    {{
      "KPI": "Total Revenue",
      "Columns": ["SALES", "YEAR_ID"]
    }}
  ]
}}
    """
    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content


def generate_chart(kpi_data):
    prompt = f"""
You are a retail Business Intelligence Engineer.
For the following KPIs and their columns: {kpi_data},
provide at least one chart per KPI with x_axis, y_axis, chart_type, and aggregation.

Use strictly this format:

{{
  "metrics": [
    {{
      "name": "Monthly Sales Trend",
      "x_axis": "MONTH_ID",
      "y_axis": "SALES",
      "x_label": "Months",
      "y_label": "Sales",
      "aggregation_column": "SALES",
      "aggregation_type": "SUM",
      "chart_type": "line"
    }}
  ]
}}
    """
    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content


def generate_imp_kpi_info(kpi_name_list):
    prompt = f"""
You are a retail Business Intelligence Engineer.
Out of this list of KPIs: {kpi_name_list},
give definitions for the most important 3 KPIs in 50 words each.
Only use KPIs from the list. Output should be plain text or JSON.
    """
    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content
