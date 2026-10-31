import geopandas as gpd
from shapely import Point
import math

# We will create a central city of 1,000,000 population with five surrounding towns of 100,000 population each 150 kilometers away.
# Each surrounding town will have two intermediate population centers of 25,000 between it and the central city.
nodes = []
nodeid = 0
# Add central city node at 0,0 with a circle geometry of radius 10 km
nodes.append({"name": "Central City", "population": 1_000_000, "geometry": Point(0, 0).buffer(10_000), "nodeid": nodeid})
nodeid += 1
# Surrounding towns
NTOWNS  = 5
for i in range(NTOWNS):
    angle = (i * 2 * math.pi / NTOWNS)
    tx = 150_000 * (cos := math.cos(angle))
    ty = 150_000 * (sin := math.sin(angle))
    nodes.append({"name": f"Town {i+1}", "population": 100_000, "geometry": Point(tx, ty).buffer(10_000), "nodeid": nodeid})
    nodeid += 1
    # Intermediate population centers
    ix1 = 50_000 * cos
    iy1 = 50_000 * sin
    nodes.append({"name": f"Interim {i+1}a", "population": 25_000, "geometry": Point(ix1, iy1).buffer(5_000), "nodeid": nodeid})
    nodeid += 1
    ix2 = 100_000 * cos
    iy2 = 100_000 * sin
    nodes.append({"name": f"Interim {i+1}b", "population": 25_000, "geometry": Point(ix2, iy2).buffer(5_000), "nodeid": nodeid})
    nodeid += 1

scenario = gpd.GeoDataFrame(nodes, crs="EPSG:3857") # Mark as 3857 since we're working in meters/metres.
scenario.head()

from laser.core import PropertySet
from laser.generic import Model
import laser.generic.SEIR as SEIR
from laser.core.distributions import normal

exp_mean = 7.0
exp_stddev = 1.0
inf_mean = 14.0
inf_stddev = 2.0
R0 = 2.0
beta = R0 / inf_mean

parameters = PropertySet({"nticks": 365, "beta": beta, "gravity_c": 2.5})
scenario["S"] = scenario.population
scenario["E"] = 0
scenario["I"] = 0
scenario["R"] = 0
scenario.loc[scenario.name == "Town 1", "S"] -= 100
scenario.loc[scenario.name == "Town 1", "I"] += 100
prj = scenario.to_crs(4326)
model = Model(prj, parameters)
incubation_distribution = normal(loc=exp_mean, scale=exp_stddev)
infectious_distribution = normal(loc=inf_mean, scale=inf_stddev)
model.components = [
    SEIR.Susceptible(model),
    SEIR.Recovered(model),
    SEIR.Infectious(model, infectious_distribution, 1),
    SEIR.Exposed(model, incubation_distribution, infectious_distribution, 1, 1),
    SEIR.Transmission(model, incubation_distribution, 1)
]
model.run()

import matplotlib.pyplot as plt

fig, axes = plt.subplots(4, 1, figsize=(14, 18), sharex=True)
compartments = ['S', 'E', 'I', 'R']

for idx, comp in enumerate(compartments):
    for node in scenario.index:
        axes[idx].plot(getattr(model.nodes, comp)[:, node], label=scenario.loc[node, "name"])
    axes[idx].set_ylabel(comp)
    axes[idx].legend(loc='upper right', fontsize='small')
axes[-1].set_xlabel("Time (days)")
plt.tight_layout()
plt.show()
