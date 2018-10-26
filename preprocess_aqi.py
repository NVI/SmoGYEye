import pandas as pd


def preprocess_site_list(site_file):
    """Get the location of air quality measurement sites.
        
    Return the latitude and longitude coordinates in two dictionaries. 
    The keys are site codes as strings and the values are coordinates as floats.
    """

    # Make sure that state, county, and site codes are read as strings
    # instead of numbers
    col_types = {'State Code': str, 'County Code': str, 'Site Number': str}

    sites = pd.read_csv(site_file, dtype=col_types)

    # Columns that can be dropped from the site listing
    cols_to_drop = [
        'Land Use', 'Location Setting', 'Met Site State Code',
        'Met Site County Code', 'Met Site Site Number', 'Met Site Type',
        'Met Site Distance', 'Met Site Direction', 'GMT Offset',
        'Owning Agency', 'Local Site Name', "Address", "Zip Code",
        "State Name", "County Name", "City Name", "CBSA Name", "Tribe Name",
        "Extraction Date"
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

    # Divide the data into two Series: one with latitude coordinates and one
    # with longitude coordinates
    sites_lat = sites['Latitude']
    sites_lon = sites['Longitude']

    # Transform the site listings into a dictionary where keys are site
    # codes and values are coordinates}
    sites_lat = sites_lat.to_dict()
    sites_lon = sites_lon.to_dict()

    # Return the two dictionaries with the coordinates
    return sites_lat, sites_lon


def preprocess_aqi(sites_lat, sites_lon, aqi_file):
    """Convert a CSV file with AQI data into a pandas DataFrame.

    Get the following columns from an AQI data file: Date, AQI, Category,
    Defining Parameter, and Defining Site. Ensure that dates are parsed as 
    datetime objects.

    This function also adds coordinate data for the defining site to the data 
    frame.
    """

    # Specify used column names and types to make CSV parsing more efficient
    col_types = {
        'AQI': int,
        'Category': str,
        'Defining Parameter': str,
        'Defining Site': str
    }

    col_names = list(col_types.keys()) + ['Date']

    aqi = pd.read_csv(
        aqi_file, usecols=col_names, dtype=col_types, parse_dates=['Date'])

    # Add column containing the site information (including location
    # coordinates) to each AQI measurement
    aqi['Latitude'] = aqi['Defining Site'].map(sites_lat)
    aqi['Longitude'] = aqi['Defining Site'].map(sites_lon)

    return aqi
