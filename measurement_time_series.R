library(dplyr)
library(ggplot2)
library(reshape2)

# Data processed in data_combination.py as starting point
# Not really UTC, but time zone doesn't matter with time differences
# Default behavior is weird https://stackoverflow.com/questions/50116692/weird-as-posixct-behavior-depending-on-daylight-savings-time
combined_data <-
  read.csv("data/wildfire/wildfires_with_aqi_1.csv", stringsAsFactors = FALSE, colClasses = c(CONT_TIME="character", DISCOVERY_TIME="character")) %>%
  rbind(read.csv("data/wildfire/wildfires_with_aqi_2.csv", stringsAsFactors = FALSE, colClasses = c(CONT_TIME="character", DISCOVERY_TIME="character"))) %>%
  mutate(
    DEFINING_SITE = gsub("^[^,]*,[^,]*,[^,]*,[^,]*,[^:]*:[ ']*([^,']*)',.*", "\\1", AIR_QUALITY),
    CONT_DATE = as.Date(CONT_DATE),
    CONT_TIME = gsub("[.].*","",CONT_TIME),
    CONT_TIME = case_when(
      nchar(CONT_TIME) == 1 ~ paste0("000", CONT_TIME),
      nchar(CONT_TIME) == 2 ~ paste0("00", CONT_TIME),
      nchar(CONT_TIME) == 3 ~ paste0("0", CONT_TIME),
      TRUE ~ CONT_TIME
    ),
    CONT_DATE_TIME = as.POSIXct(strptime(paste(CONT_DATE, CONT_TIME), format = "%Y-%m-%d %H%M"), tz = "UTC"),
    DISCOVERY_DATE = as.Date(DISCOVERY_DATE),
    DISCOVERY_TIME = case_when(
      nchar(DISCOVERY_TIME) == 1 ~ paste0("000", DISCOVERY_TIME),
      nchar(DISCOVERY_TIME) == 2 ~ paste0("00", DISCOVERY_TIME),
      nchar(DISCOVERY_TIME) == 3 ~ paste0("0", DISCOVERY_TIME),
      TRUE ~ DISCOVERY_TIME
    ),
    DISCOVERY_DATE_TIME = as.POSIXct(strptime(paste(DISCOVERY_DATE, DISCOVERY_TIME), format = "%Y-%m-%d %H%M"), tz = "UTC"),
    FIRE_LENGTH_DAYS = as.numeric(difftime(CONT_DATE_TIME, DISCOVERY_DATE_TIME, units = "days"))
  )

summarise_measurements <- function(combined_data, reader) {
  summaries <- NULL
  for(year in 1992:2015) {
    measurement_data <- reader(year)
    wildfire_data <- combined_data %>% filter(FIRE_YEAR == as.character(year))
    summary <-
      wildfire_data %>%
      left_join(measurement_data, by = "DEFINING_SITE") %>%
      filter(measurement_date >= DISCOVERY_DATE - 1, measurement_date <= CONT_DATE + 1) %>%
      group_by(X) %>%
      summarise(
        first_measurement = first(measurement),
        last_measurement = last(measurement),
        min_measurement = min(measurement),
        max_measurement = max(measurement),
        mean_measurement = mean(measurement),
        list_measurement = list(measurement)
      )
    summaries <- rbind(summaries, summary)
  }

  combined_data %>%
    left_join(summaries, by = "X") %>%
    mutate(change = last_measurement - first_measurement, max_change = max_measurement - first_measurement, min_change = min_measurement - first_measurement)
}

aqi_time_series <- summarise_measurements(combined_data, function(year) {
  read.csv(paste0("data/aqi/daily_aqi_by_county_", as.character(year), ".csv"), stringsAsFactors = FALSE) %>%
    mutate(DEFINING_SITE = Defining.Site, measurement = AQI, measurement_date = as.Date(Date))
})

aqi_time_series %>%
  group_by(FIRE_SIZE_CLASS) %>%
  summarise(change = mean(change), max_change = mean(max_change), min_change = mean(min_change), fire_length_weeks = mean(FIRE_LENGTH_DAYS)/7) %>%
  melt(id.vars = "FIRE_SIZE_CLASS") %>%
  ggplot(aes(x = FIRE_SIZE_CLASS, y = value)) +
  geom_bar(aes(fill = variable), position="dodge", stat="identity") +
  labs(x = "Fire size class", y = "Average index") +
  ggtitle("Air quality")

ggsave("report/aqi_time_series.png")

co_time_series <- summarise_measurements(combined_data, function(year) {
  read.csv(paste0("data/co/daily_42101_", as.character(year), ".csv"), stringsAsFactors = FALSE, colClasses = c(State.Code="character", County.Code="character", Site.Num="character")) %>%
    mutate(DEFINING_SITE = paste(State.Code, County.Code, Site.Num, sep="-"), measurement = Arithmetic.Mean, measurement_date = as.Date(Date.Local))
})

co_time_series %>%
  filter(!is.na(change)) %>% # not every station measures CO
  group_by(FIRE_SIZE_CLASS) %>%
  summarise(change = mean(change), max_change = mean(max_change), min_change = mean(min_change), fire_length_weeks = mean(FIRE_LENGTH_DAYS)/7) %>%
  melt(id.vars = "FIRE_SIZE_CLASS") %>%
  ggplot(aes(x = FIRE_SIZE_CLASS, y = value)) +
  geom_bar(aes(fill = variable), position="dodge", stat="identity") +
  labs(x = "Fire size class", y = "Average concentration") +
  ggtitle("CO")

ggsave("report/co_time_series.png")

so2_time_series <- summarise_measurements(combined_data, function(year) {
  read.csv(paste0("data/so2/daily_42401_", as.character(year), ".csv"), stringsAsFactors = FALSE, colClasses = c(State.Code="character", County.Code="character", Site.Num="character")) %>%
    mutate(DEFINING_SITE = paste(State.Code, County.Code, Site.Num, sep="-"), measurement = Arithmetic.Mean, measurement_date = as.Date(Date.Local))
})

so2_time_series %>%
  filter(!is.na(change)) %>% # not every station measures SO2
  group_by(FIRE_SIZE_CLASS) %>%
  summarise(change = mean(change), max_change = mean(max_change), min_change = mean(min_change), fire_length_weeks = mean(FIRE_LENGTH_DAYS)/7) %>%
  melt(id.vars = "FIRE_SIZE_CLASS") %>%
  ggplot(aes(x = FIRE_SIZE_CLASS, y = value)) +
  geom_bar(aes(fill = variable), position="dodge", stat="identity") +
  labs(x = "Fire size class", y = "Average concentration") +
  ggtitle(expression("SO"[2]))

ggsave("report/so2_time_series.png")
