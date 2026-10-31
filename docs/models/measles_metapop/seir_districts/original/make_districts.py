"""
Write districts.csv: 260 made-up districts in 16 made-up regions

Places are scattered on an empty stretch of the map, with populations from a lognormal, so none of this describes anywhere.

    python make_districts.py
"""
import numpy as np
import pandas as pd
import sciris as sc

n_districts, n_regions, mean_pop = 260, 16, 100_000
rng = np.random.default_rng(1)
regions = rng.integers(n_regions, size=n_districts)
centers = rng.uniform(size=(n_regions, 2))*8
lat = 10 + centers[regions, 0] + rng.normal(scale=0.5, size=n_districts)
lon = -40 + centers[regions, 1] + rng.normal(scale=0.5, size=n_districts)
pop = np.round(mean_pop*rng.lognormal(sigma=0.6, size=n_districts)/np.exp(0.18)).astype(int)
ids = [f'region_{r:02d}:district_{i:03d}' for i,r in enumerate(regions)]
pd.DataFrame(dict(dotname=ids, lat=lat, lon=lon, pop=pop)).to_csv(sc.thispath(__file__)/'districts.csv', index=False)
