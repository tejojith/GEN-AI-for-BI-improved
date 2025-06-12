import plotly.express as px

def bar_chart(df_data, x_axis, y_axis, kpi_name, raw_df=None, value1=None, value2=None):
    value1 = value1 or []
    value2 = value2 or []
    df_data = df_data.copy()
    
    # Initialize all points as 'Total'
    df_data['highlight'] = 'Total'
    
    if value1 or value2:
        # Extract years from value1 and value2 selections
        value1_years = set()
        value2_years = set()
        
        for year, month in value1:
            value1_years.add(year)
        
        for year, month in value2:
            value2_years.add(year)
        
        # Method 1: If x_axis contains year data directly
        if x_axis in ['YEAR_ID', 'year', 'Year']:
            def assign_color_by_year(year_val):
                if year_val in value1_years:
                    return 'Value1'
                elif year_val in value2_years:
                    return 'Value2'
                else:
                    return 'Total'
            
            df_data['highlight'] = df_data[x_axis].apply(assign_color_by_year)
        
        # Method 2: If we have raw_df, check if the selected year-month combinations exist
        elif raw_df is not None:
            value1_x_vals = set()
            value2_x_vals = set()
            
            # For each value1 selection, check if data exists and get corresponding x_axis values
            for year, month in value1:
                matching_rows = raw_df[(raw_df['YEAR_ID'] == year) & (raw_df['MONTH_ID'] == month)]
                if not matching_rows.empty:
                    value1_x_vals.update(matching_rows[x_axis].unique())
                else:
                    # If specific month doesn't exist, include the whole year
                    year_rows = raw_df[raw_df['YEAR_ID'] == year]
                    if not year_rows.empty:
                        value1_x_vals.update(year_rows[x_axis].unique())
            
            # Same for value2
            for year, month in value2:
                matching_rows = raw_df[(raw_df['YEAR_ID'] == year) & (raw_df['MONTH_ID'] == month)]
                if not matching_rows.empty:
                    value2_x_vals.update(matching_rows[x_axis].unique())
                else:
                    # If specific month doesn't exist, include the whole year
                    year_rows = raw_df[raw_df['YEAR_ID'] == year]
                    if not year_rows.empty:
                        value2_x_vals.update(year_rows[x_axis].unique())
            
            def assign_color(x_val):
                if x_val in value1_x_vals:
                    return 'Value1'
                elif x_val in value2_x_vals:
                    return 'Value2'
                else:
                    return 'Total'
            
            df_data['highlight'] = df_data[x_axis].apply(assign_color)
        
        # Method 3: Direct year-month matching if df_data has both columns
        elif 'YEAR_ID' in df_data.columns and 'MONTH_ID' in df_data.columns:
            def assign_color_direct(row):
                year_month = (row['YEAR_ID'], row['MONTH_ID'])
                year_only = row['YEAR_ID']
                
                # Check exact year-month match first
                if year_month in value1:
                    return 'Value1'
                elif year_month in value2:
                    return 'Value2'
                # Then check year-only match
                elif year_only in value1_years:
                    return 'Value1'
                elif year_only in value2_years:
                    return 'Value2'
                else:
                    return 'Total'
            
            df_data['highlight'] = df_data.apply(assign_color_direct, axis=1)
        
        # Method 4: String/numeric matching for various formats
        else:
            # Create comprehensive sets of possible representations
            value1_identifiers = set()
            value2_identifiers = set()
            
            for year, month in value1:
                value1_identifiers.update([
                    year,  # Just the year
                    str(year),
                    f"{year}-{month:02d}",
                    f"{year}_{month:02d}",
                    f"{month:02d}/{year}",
                    f"{month}/{year}",
                    str(year * 100 + month)
                ])
            
            for year, month in value2:
                value2_identifiers.update([
                    year,  # Just the year
                    str(year),
                    f"{year}-{month:02d}",
                    f"{year}_{month:02d}",
                    f"{month:02d}/{year}",
                    f"{month}/{year}",
                    str(year * 100 + month)
                ])
            
            def assign_color_flexible(x_val):
                if x_val in value1_identifiers or str(x_val) in value1_identifiers:
                    return 'Value1'
                elif x_val in value2_identifiers or str(x_val) in value2_identifiers:
                    return 'Value2'
                else:
                    return 'Total'
            
            df_data['highlight'] = df_data[x_axis].apply(assign_color_flexible)

    fig = px.bar(df_data, x=x_axis, y=y_axis, title=kpi_name, color='highlight',
                 color_discrete_map={'Total': "#636EFA", 'Value1': "#63FAAE", 'Value2': '#EF553B'})
    return fig


def line_chart(df_data, x_axis, y_axis, kpi_name, raw_df=None, value1=None, value2=None):
    value1 = value1 or []
    value2 = value2 or []
    df_data = df_data.copy()
    
    # Initialize all points as 'Total'
    df_data['highlight'] = 'Total'
    
    if value1 or value2:
        # Extract years from selections
        value1_years = set()
        value2_years = set()
        
        for year, month in value1:
            value1_years.add(year)
        
        for year, month in value2:
            value2_years.add(year)
        
        # Same logic as bar_chart
        if x_axis in ['YEAR_ID', 'year', 'Year']:
            def assign_color_by_year(year_val):
                if year_val in value1_years:
                    return 'Value1'
                elif year_val in value2_years:
                    return 'Value2'
                else:
                    return 'Total'
            
            df_data['highlight'] = df_data[x_axis].apply(assign_color_by_year)
        
        elif raw_df is not None:
            value1_x_vals = set()
            value2_x_vals = set()
            
            for year, month in value1:
                matching_rows = raw_df[(raw_df['YEAR_ID'] == year) & (raw_df['MONTH_ID'] == month)]
                if not matching_rows.empty:
                    value1_x_vals.update(matching_rows[x_axis].unique())
                else:
                    year_rows = raw_df[raw_df['YEAR_ID'] == year]
                    if not year_rows.empty:
                        value1_x_vals.update(year_rows[x_axis].unique())
            
            for year, month in value2:
                matching_rows = raw_df[(raw_df['YEAR_ID'] == year) & (raw_df['MONTH_ID'] == month)]
                if not matching_rows.empty:
                    value2_x_vals.update(matching_rows[x_axis].unique())
                else:
                    year_rows = raw_df[raw_df['YEAR_ID'] == year]
                    if not year_rows.empty:
                        value2_x_vals.update(year_rows[x_axis].unique())
            
            def assign_color(x_val):
                if x_val in value1_x_vals:
                    return 'Value1'
                elif x_val in value2_x_vals:
                    return 'Value2'
                else:
                    return 'Total'
            
            df_data['highlight'] = df_data[x_axis].apply(assign_color)
        
        else:
            # Flexible matching including year-only
            value1_identifiers = set()
            value2_identifiers = set()
            
            for year, month in value1:
                value1_identifiers.update([
                    year, str(year), f"{year}-{month:02d}", f"{year}_{month:02d}",
                    f"{month:02d}/{year}", f"{month}/{year}", str(year * 100 + month)
                ])
            
            for year, month in value2:
                value2_identifiers.update([
                    year, str(year), f"{year}-{month:02d}", f"{year}_{month:02d}",
                    f"{month:02d}/{year}", f"{month}/{year}", str(year * 100 + month)
                ])
            
            def assign_color_flexible(x_val):
                if x_val in value1_identifiers or str(x_val) in value1_identifiers:
                    return 'Value1'
                elif x_val in value2_identifiers or str(x_val) in value2_identifiers:
                    return 'Value2'
                else:
                    return 'Total'
            
            df_data['highlight'] = df_data[x_axis].apply(assign_color_flexible)

    fig = px.line(df_data, x=x_axis, y=y_axis, title=kpi_name, color='highlight',
                  color_discrete_map={'Value1': "#63FAAE", 'Total': "#636EFA", 'Value2': '#EF553B'})
    return fig


def scatter_chart(df_data, x_axis, y_axis, kpi_name, value1=None, value2=None):
    value1 = value1 or []
    value2 = value2 or []
    df_data = df_data.copy()
    
    # Initialize all points as 'Total'
    df_data['highlight'] = 'Total'
    
    if value1 or value2:
        # Extract years
        value1_years = set()
        value2_years = set()
        
        for year, month in value1:
            value1_years.add(year)
        
        for year, month in value2:
            value2_years.add(year)
        
        # Direct year-month matching if available
        if 'YEAR_ID' in df_data.columns and 'MONTH_ID' in df_data.columns:
            def assign_color_direct(row):
                year_month = (row['YEAR_ID'], row['MONTH_ID'])
                year_only = row['YEAR_ID']
                
                if year_month in value1:
                    return 'Value1'
                elif year_month in value2:
                    return 'Value2'
                elif year_only in value1_years:
                    return 'Value1'
                elif year_only in value2_years:
                    return 'Value2'
                else:
                    return 'Total'
            
            df_data['highlight'] = df_data.apply(assign_color_direct, axis=1)
        
        else:
            # Flexible matching for x and y axes
            value1_identifiers = set()
            value2_identifiers = set()
            
            for year, month in value1:
                value1_identifiers.update([
                    year, str(year), f"{year}-{month:02d}", f"{year}_{month:02d}",
                    f"{month:02d}/{year}", f"{month}/{year}", str(year * 100 + month)
                ])
            
            for year, month in value2:
                value2_identifiers.update([
                    year, str(year), f"{year}-{month:02d}", f"{year}_{month:02d}",
                    f"{month:02d}/{year}", f"{month}/{year}", str(year * 100 + month)
                ])
            
            def assign_color_flexible(row):
                x_val = row[x_axis]
                y_val = row[y_axis]
                
                # Check both x and y values
                if (x_val in value1_identifiers or str(x_val) in value1_identifiers or
                    y_val in value1_identifiers or str(y_val) in value1_identifiers):
                    return 'Value1'
                elif (x_val in value2_identifiers or str(x_val) in value2_identifiers or
                      y_val in value2_identifiers or str(y_val) in value2_identifiers):
                    return 'Value2'
                else:
                    return 'Total'
            
            df_data['highlight'] = df_data.apply(assign_color_flexible, axis=1)

    fig = px.scatter(df_data, x=x_axis, y=y_axis, title=kpi_name, color='highlight',
                     color_discrete_map={'Value1': "#63FAAE", 'Total': '#636EFA', 'Value2': '#EF553B'})
    return fig