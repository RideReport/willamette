import os
import requests
import dateutil.parser
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import pytz
import boto
import json
import os
pacific = pytz.timezone('US/Pacific')

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

def getrows(dt=None):
    if dt is None:
        dt = datetime.now(pacific)
    url = 'http://waterdata.usgs.gov/nwis/uv?cb_00010=on&cb_00060=on&cb_00065=on&cb_00095=on&cb_00055=on&cb_00300=on&cb_00400=on&cb_63680=on&cb_62361=on&cb_95204=on&cb_99137=on&cb_32295=on&format=rdb&site_no=14211720&period=&begin_date={:%Y-%m-%d}&end_date={:%Y-%m-%d}'.format(dt - timedelta(days=5), dt)
    response = requests.get(url)
    response.raise_for_status()
    header = None
    for line in response.text.splitlines():
        line = line.strip()
        if line.startswith('#'):
            continue

        parts = line.split('\t')
        if header is None:
            header = parts
            continue

        row = dict(zip(header, parts))
        if row['agency_cd'] != 'USGS':
            continue

        date = '{} {}'.format(row['datetime'], row['tz_cd'])
        dt = dateutil.parser.parse(date)
        row['dt'] = dt
        yield row

def get_most_recent_dt_and_value(rows, key):
    row = max([r for r in rows if r.get(key, '') != ''], key=lambda r: r['dt'])
    return row['dt'], row[key]

rows = list(getrows())


def gen_bes_ecoli(url, rank=0):
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    div = soup.find_all('div', {'class': 'contentHeaderWrap big'})[0]
    name = div.getText().strip()

    table = soup.find_all('table', attrs={'class':'rt'})[0]
    rows = table.find_all('tr')
    header_row = rows.pop(0)
    hcells = header_row.find_all('td')
    assert 'e. coli' in hcells[2].getText().lower()
    assert 'temperature' in hcells[1].getText().lower()
    assert 'collection date' in hcells[0].getText().lower()
    labels = ['date', 'tempf', 'ecoli']
    for row in rows:
        cells = row.find_all('td', {'class': 'bluecell'})
        if len(cells) != 3:
            continue

        date = cells[0].getText().strip()
        try:
            dt = dateutil.parser.parse(date)
        except ValueError:
            print date
            raise
        yield {
            'dt': pacific.localize(dt),
            'tempf': float(cells[1].getText().strip()),
            'ecoli': float(cells[2].getText().strip()),
            'rank': rank,
            'name': name,
        }

def get_nearby_algae_bloom_advisories():
    if datetime.now().year != 2016:
        return [{
            'issued_description': 'Unknown! API needs to be updated for curent year.',
        }]

    with open(os.path.join(SCRIPT_DIR, 'willamette-zone.wkt')) as f:
        poly_wkt = f.read()
    url = 'https://data.oregon.gov/resource/muwp-rr44.json'
    query = {
        '$where': 'within_polygon(location, "{}")'.format(poly_wkt),
    }
    response = requests.get(url, params=query)
    try:
        response.raise_for_status()
    except:
        print response.text
        raise
    results = response.json()
    return results

boathouse = list(gen_bes_ecoli('http://www.portlandoregon.gov/bes/waterquality/results.cfm?location_id=7131', 2))
morrison = list(gen_bes_ecoli('http://www.portlandoregon.gov/bes/waterquality/results.cfm?location_id=1727', 1))
marina = list(gen_bes_ecoli('http://www.portlandoregon.gov/bes/waterquality/results.cfm?location_id=7132', 0))

from itertools import chain
ecoli_history = sorted(chain(boathouse, morrison, marina), key=lambda r: (r['dt'], r['rank']), reverse=True)
ecoli = ecoli_history[0]


k_TC = '172755_00010'
k_tb = '172757_63680'
k_cy = '173554_95204'
TCdt, TC = get_most_recent_dt_and_value(rows, k_TC)
tbdt, tb = get_most_recent_dt_and_value(rows, k_tb)
cydt, cy = get_most_recent_dt_and_value(rows, k_cy)

data = {
    'temperature_celsius': float(TC),
    'temperature_date': str(TCdt),
    #'turbidity': float(tb),
    #'turbidity_date': str(tbdt),
    'ecoli': float(ecoli['ecoli']),
    'ecoli_date': str(ecoli['dt']),
    #'cyanobacteria': float(cy),
    #'cyanobacteria_date': str(cydt),
    'algae_bloom_advisories': get_nearby_algae_bloom_advisories(),

    'history': {
        'usgs_temperature':
            [
                {
                    'celsius': float(r[k_TC]),
                    'fahrenheit': 9./5. * float(r[k_TC]) + 32.,
                    'date': str(r['dt'])
                }
                for r in rows if r.get(k_TC, '') != ''
            ],
        #'usgs_turbidity':
        #    [
        #        {
        #            'turbidity': float(r[k_tb]),
        #            'date': str(r['dt']),
        #        }
        #        for r in rows if r.get(k_tb, '') != ''
        #    ],
        'bes_ecoli':
            [
                {
                    'date': str(r['dt']),
                    'temperature_fahrenheit': r['tempf'],
                    'organisms_per_100ml': r['ecoli'],
                    'weight': -r['rank'], # relevance to hawthorne bridge dock. lower numbers more relevant.
                    'location_name': r['name'],
                }
                for r in ecoli_history
            ],
    },

    'human_readable_source_links': [
        {
            'agency': 'USGS',
            'description': 'National Water Information System, Willamette River station',
            'url': 'http://waterdata.usgs.gov/nwis/uv?cb_00010=on&cb_00060=on&cb_00065=on&cb_00095=on&cb_00055=on&cb_00300=on&cb_00400=on&cb_63680=on&cb_62361=on&cb_95204=on&cb_99137=on&cb_32295=on&format=html&site_no=14211720&period=7',
        },
        {
            'agency': 'City of Portland, BES',
            'description': 'Environmental Services collects water samples from the river monthly at three locations to analyze long-term water quality trends for nutrients, metals and bacteria. From May to October, field staff also collect weekly samples from five  Willamette River public access points to give recreational users more frequent information about bacteria levels.',
            'url': 'https://www.portlandoregon.gov/bes/waterquality/results.cfm',
        },
        {
            'agency': 'Oregon Health Authority',
            'description': 'Blue-green algae advisories for the state of Oregon',
            'url': 'https://public.health.oregon.gov/HealthyEnvironments/Recreation/HarmfulAlgaeBlooms/Pages/Blue-GreenAlgaeAdvisories.aspx',
        },
    ]
}

with open('data.json', 'w') as f:
    json.dump(data, f)

s3 = boto.connect_s3()
key = s3.get_bucket('howsthewater').new_key('data.json')
key.set_contents_from_filename('data.json')
key.set_acl('public-read')
