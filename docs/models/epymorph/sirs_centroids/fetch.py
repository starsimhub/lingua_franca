"""
Fetch the two inputs that the vignette takes from ADRIOs, and keep them in `original/arizona_counties.csv`

    python fetch.py

Run once, in epymorph's environment, with a network connection; `run.py` then needs neither. The vignette
gets each county's population from `acs5.Population()` (variable B01001_001E of the ACS 5-year data for
2022) and its centroid from `us_tiger.InternalPoint()` (the internal point of the TIGER county shapes for
2022). The ACS ADRIO needs a Census API key, so the population is read from the Census Bureau's table-based
summary file of the same release, which holds the same estimates; the centroids come from epymorph's own
ADRIO, which needs no key.
"""
import os
import io
import csv
import urllib.request
from epymorph.kit import *
from epymorph.adrio import us_tiger

here = os.path.dirname(os.path.abspath(__file__))
acs_url = 'https://www2.census.gov/programs-surveys/acs/summary_file/2022/table-based-SF/data/5YRData/acsdt5y2022-b01001.dat'

scope = CountyScope.in_states(['AZ'], year=2022)
centroids = us_tiger.InternalPoint().with_context(scope=scope).evaluate()

pop = dict()
with urllib.request.urlopen(acs_url) as response: # About 200 MB, read a line at a time
    for line in io.TextIOWrapper(response, encoding='utf-8'):
        fields = line.split('|')
        if fields[0].startswith('0500000US04'): # The counties of Arizona
            pop[fields[0][9:]] = int(fields[1]) # B01001_E001, the total population

with open(os.path.join(here, 'original', 'arizona_counties.csv'), 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['geoid', 'name', 'population', 'longitude', 'latitude'])
    for geoid, name, (lon, lat) in zip(scope.node_ids, scope.labels, centroids):
        writer.writerow([geoid, name, pop[geoid], lon, lat])
print(f'Wrote {len(scope.node_ids)} counties')
