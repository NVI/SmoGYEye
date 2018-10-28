library(dplyr)
library(purrrlyr)

combined_data_1 <- read.csv("data/wildfire/wildfires_with_aqi_1.csv", stringsAsFactors = FALSE)
combined_data_2 <- read.csv("data/wildfire/wildfires_with_aqi_2.csv", stringsAsFactors = FALSE)
combined_data <- rbind(combined_data_1, combined_data_2)
combined_data$DEFINING_SITE <- gsub("^[^,]*,[^,]*,[^,]*,[^,]*,[^:]*:[ ']*([^,']*)',.*", "\\1", combined_data$AIR_QUALITY)
combined_data$FIRE_LENGTH_NO_TIME <- as.numeric(as.Date(combined_data$CONT_DATE) - as.Date(combined_data$DISCOVERY_DATE))
combined_data <- combined_data %>% mutate(CONT_DATE = as.Date(CONT_DATE), DISCOVERY_DATE = as.Date(DISCOVERY_DATE))

summaries <- NULL

for(year in 1992:2015) {
  aqi <- read.csv(paste0("data/aqi/daily_aqi_by_county_", as.character(year), ".csv"), stringsAsFactors = FALSE) %>% mutate(Date = as.Date(Date))
  combined_subset <- combined_data %>% filter(FIRE_YEAR == as.character(year))
  summary <-
    combined_subset %>%
    left_join(aqi, by = c("DEFINING_SITE" = "Defining.Site")) %>%
    filter(Date >= DISCOVERY_DATE - 1, Date <= CONT_DATE + 1) %>%
    group_by(X) %>%
    summarise(first_AQI = first(AQI.y), last_AQI = last(AQI.y), min_AQI = min(AQI.y), max_AQI = max(AQI.y), list_AQI = list(AQI.y))
  summaries <- rbind(summaries, summary)
}

data_with_time_series <-
  combined_data %>%
  inner_join(summaries, by = "X") %>%
  mutate(change_AQI = last_AQI - first_AQI, maxchange_AQI = max_AQI - first_AQI)
