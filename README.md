# How's the River?
A simple, single-serving site showing the current swimming conditions in the Willamette River in Portland, Oregon. The site displays temperature and swimming suitability for the water, as well as any algae advisories that are currently in effect.

This site is hosted at www.howstheriver.com.

# Components
- *poc.py* This Python script is responsible for fetching data from the USGS and the Portland Bureau of Environmental Services. The former has a simple queryable service that spits out a table of data, but for the latter we resort to screen-scraping with BeautifulSoup. The Python script is hosted on an Amazon EC2 micro instance and runs every 15 minutes, uploading the resulting JSON to Amazon S3.
- *Index.html* The website is hosted using Github Pages and consists of a single page which uses Ajax to fetch the JSON off S3 and render it appropriately.

# Data Sources:
**E. Coli counts:** https://www.portlandoregon.gov/bes/waterquality/results.cfm

**Temperature, cyanobacteria and turbidity** http://or.water.usgs.gov/will_morrison/monitors/will_morrison_t_7.html

**Algae bloom advisories** https://public.health.oregon.gov/HealthyEnvironments/Recreation/HarmfulAlgaeBlooms/Pages/Blue-GreenAlgaeAdvisories.aspx

# Calculations
Water quality thresholds are based on the values given by the WHO for 'Very Good', 'Good', 'Poor' and 'Very Poor' for swimming. The 'Very Poor' value was lowered from 500 organisms per 100ml (given by the WHO) to 406 (the maximum allowed value for safe swimming according to Oregon DEQ). The resulting thresholds correspond to 'fresh', 'swimmable', 'a bit funky' and 'not fit for swimming' on the site.
- http://www.who.int/water_sanitation_health/bathing/srwe1-chap4.pdf
- http://www.portlandoregon.gov/bes/article/390127
 
Turbidity and cyanobacteria are not currently used. The Willamette occassionally experiences algae blooms, and when the Oregon Health Authority issues an advisory we display it on the site.

# License
Source code for How's the River is made available under the MIT License.

Copyright (c) 2016 Knock Software, Inc

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
