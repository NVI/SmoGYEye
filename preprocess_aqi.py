import pandas as pd

def preprocess_site_list(site_file):
    # Make sure that state, county, and site codes are read as strings
    # instead of numbers
    col_types = {'State Code': str, 'County Code': str, 'Site Number': str}

    sites = pd.read_csv(site_file, dtype=col_types)

    # Columns that can be dropped from the site listing
    cols_to_drop = [
        'Land Use', 'Location Setting', 'Met Site State Code',
        'Met Site County Code', 'Met Site Site Number', 'Met Site Type',
        'Met Site Distance', 'Met Site Direction', 'GMT Offset',
        'Owning Agency', 'Local Site Name'
    ]

    sites = sites.drop(columns=cols_to_drop)

    # Convert site closing dates to datetime64 objects (does not work
    # with read_csv())
    sites['Site Closed Date'] = pd.to_datetime(sites['Site Closed Date'])

    # Get sites that have been closed down before 1992 and drop them
    # from the list
    outdated = sites.loc[
        sites['Site Closed Date'] < pd.to_datetime('01-01-1992')]
    sites = sites.drop(outdated.index)

    # Get the complete site code, add it as a column, and finally
    # use the site code as the index
    sites['site-code'] = sites['State Code'] + '-' + sites[
        'County Code'] + '-' + sites['Site Number']
    sites = sites.set_index('site-code')

    # Transform the site listing into a dictionary where keys are site
    # codes and values are dictionaries of type {column: value}
    # {site-code1: {column1: value1}, {column2: value2}...}
    site_list = sites.to_dict('index')

    return site_list


def preprocess_aqi(site_list, aqi_file):
    # Read daily AQI measurements from year XXXX
    aqi = pd.read_csv(aqi_file)

    # Add column containing the site information (including location
    # coordinates) to each AQI measurement
    aqi['site-information'] = aqi['Defining Site'].map(site_list)

    return aqi
