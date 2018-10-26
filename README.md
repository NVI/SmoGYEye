# Smoke Gets in Your Eyes: an Introduction to Data Science miniproject

## TODO

- [ ] prediction model / ML
    - [ ] determine if predicting wildfire severity works
    - [ ] look into correlation between wildfires and higher AQI

- [ ] visualize the results

- [ ] write the end user instructions / description of how end users will benefit from the project

- [ ] write the technical report


## Data

+ Data on wildfires in the US from https://www.kaggle.com/rtatman/188-million-us-wildfires
+ Data on air quality from https://aqs.epa.gov/aqsweb/airdata/download_files.html

## Slides

+ Precompiled slides: https://drive.google.com/open?id=1N69AJakomfIHxaRtY3bH071WKPjhyiVY

## Fire data -> air quality

### Predicted quantity: change in AQI

How to make robust? Maybe something along the lines:

+ Initial value AQI0: median of three days before the fire
+ Final value AQI1: second highest of the days during the fire
+ Change dAQI := AQI1 - AQI0

Is there a meaningful change with the smallest fires? Should they be omitted?

### Contributions of different fires

How to handle multiple simulataneous fires?

+ Without wind direction, weighting contribution by inverse squared distance or similar 
+ With wind direction (also available from EPA), more complicated (but most likely better) model

Does the above scheme make sense with multiple overlapping fires with different start and end dates?
