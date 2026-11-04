# epymorph demo vignette "Intro to Movement Models" (G2.L0.1-MM_intro), https://www.docs.epimorph.org/demo/G2.L0.1-MM_intro.html
# The cells of exercise 1 that set up the model, and those of exercise 2 that use the centroids movement model, unchanged, in order;
# the cells of exercise 1 that only run and plot the flat movement model, and exercise 3, are left out.

import matplotlib.pyplot as plt
import numpy as np

from epymorph.kit import *
from epymorph.adrio import acs5

my_scope = CountyScope.in_states(['AZ'], year=2022)
my_scope.labels
# You can also see their FIPS code:
# my_scope.node_ids

from epymorph.data.ipm.sirs import SIRS
sirs_ipm = SIRS()

sirs_ipm.diagram()

# Maricopa is the 8th node in the scope (i.e., index 7)
my_init = init.SingleLocation(location=7, seed_size=5)

time = TimeFrame.of("2022-01-01", duration_days=190)

comm_prop = 0.15

beta = 0.4
gam = 1 / 4
xi = 1 / 200

# From the choropleth cell of exercise 1, which that of exercise 2 also uses
def log10_transform(data_df):
    # we have to be careful to avoid log(0)!
    log_value = data_df["data"].apply(lambda x: np.log10(x) if x > 0 else nan)
    return data_df.assign(data=log_value)

from epymorph.data.mm.centroids import Centroids
from epymorph.adrio import us_tiger

rume = SingleStrataRUME.build(
    scope=my_scope,
    ipm=sirs_ipm,
    mm=Centroids(),
    init=my_init,
    time_frame=time,
    params={
        #For IPM
        'beta': beta,
        'gamma': gam,
        'xi': xi,
        #For MM
        'population': acs5.Population(),
        'commuter_proportion': comm_prop,
        'centroid': us_tiger.InternalPoint(),
        'phi': 20.0,
    }
)

print(rume.params_description())

sim = BasicSimulator(rume)
with sim_messaging(live = False):
    out = sim.run(
        rng_factory=default_rng(5),
    )

out.plot.line(
    geo=out.rume.scope.select.all(),
    time=out.rume.time_frame.select.all().group("day").agg(),
    quantity=out.rume.ipm.select.compartments("I"),
    title="Infectious in AZ Counties",
    legend="outside",
)

out.map.choropleth(
    geo=rume.scope.select.all(),
    time=rume.time_frame.select.rangex("2022-04-01", "2022-05-01").agg(compartments="max"),
    quantity=rume.ipm.select.compartments("I"),
    transform=log10_transform,
    vmax = 6.0,
    vmin = 2.5,
)
