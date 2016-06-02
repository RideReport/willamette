import os
import requests
import dateutil.parser
from bs4 import BeautifulSoup
import pytz
import boto
import json
pacific = pytz.timezone('US/Pacific')

def getrows():
    response = requests.get('http://waterdata.usgs.gov/nwis/uv?cb_00010=on&cb_00060=on&cb_00065=on&cb_00095=on&cb_00055=on&cb_00300=on&cb_00400=on&cb_63680=on&cb_62361=on&cb_95204=on&cb_99137=on&cb_32295=on&format=rdb&site_no=14211720&period=&begin_date=2016-06-01&end_date=2016-06-01')
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

boathouse = list(gen_bes_ecoli('http://www.portlandoregon.gov/bes/waterquality/results.cfm?location_id=7131', 2))
morrison = list(gen_bes_ecoli('http://www.portlandoregon.gov/bes/waterquality/results.cfm?location_id=1727', 1))
marina = list(gen_bes_ecoli('http://www.portlandoregon.gov/bes/waterquality/results.cfm?location_id=7132', 0))

from itertools import chain
ecoli = max(chain(boathouse, morrison, marina), key=lambda r: (r['dt'], r['rank']))

datafile = open('data.json', 'w')
TCdt, TC = get_most_recent_dt_and_value(rows, '01_00010')
tbdt, tb = get_most_recent_dt_and_value(rows, '38_63680')
cydt, cy = get_most_recent_dt_and_value(rows, '52_95204')

data = {
    'temperature_celcius': float(TC),
    'temperature_date': str(TCdt),
    'turbidity': float(tb),
    'turbidity_date': str(tbdt),
    'ecoli': float(ecoli['ecoli']),
    'ecoli_date': str(ecoli['dt']),
    'cyanobacteria': float(cy),
    'cyanobacteria_date': str(cydt),
}

json.dump(data, datafile)

s3 = boto.connect_s3()
key = s3.get_bucket('howsthewater').new_key('data.json')
key.set_contents_from_filename('data.json')
key.set_acl('public-read')
