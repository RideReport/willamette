# How's the River?
A simple, single-serving site showing the current swimming conditions in the Willamette River in Portland, Oregon. This site is hosted at www.howstheriver.com.

# Components
- *poc.py* This Python script is responsible for fetching data from the USGS and the Portland Bureau of Environmental Services. The former has a simple queryable service that spits out a table of data, but for the latter we resort to screen-scraping with BeautifulSoup. The Python script is hosted on an Amazon EC2 micro instance and runs every 15 minutes, uploading the resulting JSON to Amazon S3.
- *Index.html* The website is hosted using Github Pages and consists of a single page which uses Ajax to fetch the JSON off S3 and render it appropriately.

# Data Sources:
**E. Coli counts:** https://www.portlandoregon.gov/bes/waterquality/results.cfm

**Temperature, cyanobacteria and turbidity** http://or.water.usgs.gov/will_morrison/monitors/will_morrison_t_7.html

**Algae bloom advisories** https://data.oregon.gov/resource/muwp-rr44.json

# Calculations
Water quality thresholds are based on the values given by the WHO for 'Very Good', 'Good', 'Poor' and 'Very Poor' for swimming. The 'Very Poor' value was lowered from 500 organisms per 100ml (given by the WHO) to 406 (the maximum allowed value for safe swimming according to Oregon DEQ). The resulting thresholds correspond to 'fresh', 'swimmable', 'a bit funky' and 'not fit for swimming' on the site.
- http://www.who.int/water_sanitation_health/bathing/srwe1-chap4.pdf
- http://www.portlandoregon.gov/bes/article/390127
 
Turbidity and cyanobacteria are not currently used. The Willamette occassionally experiences algae blooms, and when BES issues an advisory we display it on the site.
