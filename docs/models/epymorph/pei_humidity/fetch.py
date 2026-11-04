"""
Write the data that epymorph bundles for this example as tables, in `original/states.csv` and `original/humidity.csv`

    python fetch.py

Run once, in epymorph's environment. The data are those of `epymorph.data.pei` (kept unchanged in
`original/pei_data.py`), copied by epymorph from the data files of Pei et al. (2018): the population of
each state, the commuters between each pair of states, and the humidity in each state on each day of 2015.
The notebook takes the first two from ADRIOs instead (see the README); the Starsim version reads these tables.
"""
import os
import numpy as np
import pandas as pd
from epymorph.data.pei import pei_scope, pei_population, pei_commuters, pei_humidity, pei_time_frame

here = os.path.dirname(os.path.abspath(__file__))
states = list(pei_scope.labels)
table = pd.DataFrame(pei_commuters, columns=states)
table.insert(0, 'population', pei_population)
table.insert(0, 'state', states)
table.to_csv(os.path.join(here, 'original', 'states.csv'), index=False) # The commuters from each state (rows) to each (columns)
dates = pd.date_range(str(pei_time_frame.start_date), periods=len(pei_humidity)).strftime('%Y-%m-%d')
pd.DataFrame(pei_humidity, columns=states, index=pd.Index(dates, name='date')).to_csv(os.path.join(here, 'original', 'humidity.csv'))
print(f'Wrote {len(states)} states and {len(dates)} days of humidity')
