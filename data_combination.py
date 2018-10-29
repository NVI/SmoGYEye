import pandas as pd
import numpy as np
import sqlite3
import math

from sklearn import preprocessing
from pandas.tseries.offsets import DateOffset
from datetime import datetime
import sys

from preprocess_aqi import preprocess_site_list, preprocess_aqi

LON_AT_EQUATOR = 111
LAT_IN_KM = 111


def get_distance(lat1, lon1, lat2, lon2):
    dist = math.sqrt((lat1 - lat2)**2 + (lon1 - lon2)**2)
    return round(dist, 6)


def dist_as_lon_degree(distance, latitude):
    """A simplified conversion of a specified distance into degrees longitude
    at a specified latitude"""
    lon_deg_as_km = LON_AT_EQUATOR * math.cos(math.radians(latitude))
    return distance / lon_deg_as_km


def get_aqis_during_fire(year, start_date, end_date):
    # Narrow down search by getting measurements from the time of the fire.
    # Note that here the date range is defined as DISCOVERY_DATE + 1 to CONT_DATE + 1:
    # it seems likely that measurements from the discovery date might have been made before
    # the fire was discovered.
    # If either of the given dates is a null value, return an empty dataframe
    if pd.isnull(start_date) or pd.isnull(end_date):
        return pd.DataFrame()
    aqi_df = aqi[year]
    date_range = pd.date_range(start_date + DateOffset(days=1),
                               end_date + DateOffset(days=1))
    return aqi_df.loc[aqi_df['Date'].isin(date_range)]


def get_nearest_measurement(fire_lat, fire_lon, aqi_df):
    # Narrow down the search space by only including measurements that are +/- 0.5 degrees
    # from the fire coordinates (this translates to a square are with the fire in the
    # center: the square is approx. 110 km north-south, and the east-west length varies
    # between approx. 37 km and 105 km depending on the latitude)
    # If the dataframe is empty, return an empty Series
    if aqi_df.empty:
        return pd.Series()
    lon_degrees = dist_as_lon_degree(LAT_IN_KM, fire_lat)
    candidates = aqi_df.loc[(
        (abs(aqi_df['Latitude'] - fire_lat) <= 0.5)
        & (abs(aqi_df['Longitude'] - fire_lon) <= lon_degrees / 2))]
    # If no measurements are within defined range, return an empty Series
    if candidates.empty:
        return pd.Series()
    # Loop through the candidate measurements and get the nearest location
    nearest = np.argmin([
        get_distance(fire_lat, fire_lon, row.Latitude, row.Longitude)
        for row in candidates.itertuples()
    ])
    return candidates.iloc[nearest]


# Read wildfire data from SQLITE database
print("Reading SQL database...")
cnx = sqlite3.connect('data/wildfire/FPA_FOD_20170508.sqlite')
df = pd.read_sql_query(
    "SELECT FIRE_YEAR, DISCOVERY_TIME, STAT_CAUSE_DESCR, CONT_DATE," \
    "CONT_TIME, LATITUDE, LONGITUDE, STATE, DISCOVERY_DATE, FIRE_SIZE," \
    "FIRE_SIZE_CLASS FROM 'Fires'",
    cnx)
print("Done")

print("Converting data in wildfire data frame...")
# Convert fire discovery and containment dates to yyyy-mm-dd
df['DISCOVERY_DATE'] = pd.to_datetime(
    df['DISCOVERY_DATE'] - pd.Timestamp(0).to_julian_date(), unit='D')
df['CONT_DATE'] = pd.to_datetime(
    df['CONT_DATE'] - pd.Timestamp(0).to_julian_date(), unit='D')

# Add new columns for month, date, and weekday for discovery and containment dates
df['DISCOVERY_MONTH'] = pd.DatetimeIndex(df['DISCOVERY_DATE']).month
df['DISCOVERY_DAY'] = pd.DatetimeIndex(df['DISCOVERY_DATE']).day
df['DISCOVERY_DAY_OF_WEEK'] = df['DISCOVERY_DATE'].dt.weekday_name
df['CONT_MONTH'] = pd.DatetimeIndex(df['CONT_DATE']).month
df['CONT_DAY'] = pd.DatetimeIndex(df['CONT_DATE']).day
df['CONT_DAY_OF_WEEK'] = df['CONT_DATE'].dt.weekday_name

le = preprocessing.LabelEncoder()
df['STAT_CAUSE_DESCR'] = le.fit_transform(df['STAT_CAUSE_DESCR'])
df['STATE'] = le.fit_transform(df['STATE'])
df['DISCOVERY_DAY_OF_WEEK'] = le.fit_transform(df['DISCOVERY_DAY_OF_WEEK'])

df['CONT_DAY_OF_WEEK'] = df['CONT_DAY_OF_WEEK'].fillna("Unknown")
df['CONT_DAY'] = df['CONT_DAY'].fillna("0")
df['CONT_MONTH'] = df['CONT_MONTH'].fillna("0")
df['CONT_TIME'] = df['CONT_TIME'].fillna("0")
df['DISCOVERY_TIME'] = df['DISCOVERY_TIME'].fillna("0")

df['CONT_DAY_OF_WEEK'] = le.fit_transform(df['CONT_DAY_OF_WEEK'])
df['FIRE_SIZE_CLASS'] = le.fit_transform(df['FIRE_SIZE_CLASS'])

df['CONT_MONTH'] = df['CONT_MONTH'].astype('Float64')
df['CONT_DAY'] = df['CONT_DAY'].astype('Float64')
print("Done")

print("Getting AQI measurement site data...")
# Get dictionaries containing latitude and longitude coordinates for AQI measurement sites
sites_lat, sites_lon = preprocess_site_list('data/aqi/aqs_sites.csv')
print("Done")

# Generate a list of years 1992–2015
years = [str(y) for y in range(1992, 2016)]

print("Reading AQI data from CSV files...")
# Generate a dictionary where keys are years (as strings) and values are DataFrames
# containing the AQI data with coordinates added
aqi = {
    y: preprocess_aqi(sites_lat, sites_lon,
                      'data/aqi/daily_aqi_by_county_{}.csv'.format(y))
    for y in years
}
print("Done")

# Combine all AQI data into a single large DataFrame (~7 million rows)
# aqi_all = pd.concat([aqi[y] for y in aqi.keys()], axis=0, ignore_index=True)

# Test script using smaller data set
# df = df.iloc[:10234, :]

rows = df.shape[0]
cutoff = int(rows / 10)
percent = int(rows / 100)
nearest_measurements = np.array(np.zeros(rows), dtype=object)
aqi_readings = np.array(np.zeros(rows), dtype=np.float32)

t1 = datetime.now()

counter = 1

for row in df.itertuples():
    if row.Index % percent == 0:
        sys.stdout.write("Progress: {}%  \r".format(
            round((row.Index / rows) * 100, 2)))
        sys.stdout.flush()
    aqi_candidates = get_aqis_during_fire(
        str(row.FIRE_YEAR), row.DISCOVERY_DATE, row.CONT_DATE)
    nearest = get_nearest_measurement(row.LATITUDE, row.LONGITUDE,
                                      aqi_candidates)
    nearest_measurements[row.Index] = nearest.to_dict()
    if nearest.empty:
        aqi_readings[row.Index] = np.nan
    else:
        aqi_readings[row.Index] = nearest['AQI']

    # Save partial results in case script fails to run to the end
    if row.Index > 0 and row.Index % cutoff == 0:
        start = row.Index - cutoff
        stop = row.Index
        subframe = df.iloc[start:stop, :]
        subframe['AQI'] = aqi_readings[start:stop]
        subframe['AIR_QUALITY'] = nearest_measurements[start:stop]
        subframe.to_csv(
            'data/wildfire/wildfires_with_aqi_v2_{}.csv'.format(
                str(counter).zfill(2)))
        counter += 1

df['AQI'] = aqi_readings
df['AIR_QUALITY'] = nearest_measurements
df.to_csv('data/wildfire/wildfires_with_aqi_v2_all.csv')
t2 = datetime.now()

delta = t2 - t1

print()
print("Processing {} entries took {} minutes and {} seconds".format(
    rows, delta.seconds // 60, delta.seconds % 60))
