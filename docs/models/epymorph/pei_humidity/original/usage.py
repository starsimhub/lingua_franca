# epymorph's USAGE.ipynb, at tag v1.2.0 of https://github.com/NAU-CCL/epymorph: the cell that builds the RUME
# and the cell that runs it, unchanged, in order. The cells that draw the IPM, print, and plot are left out.

from epymorph.kit import *
from epymorph.adrio import acs5, commuting_flows, us_tiger
from epymorph.data.pei import pei_humidity


rume = SingleStrataRUME.build(
    # Load the Pei IPM
    ipm=ipm.Pei(),
    # Load the Pei MM
    mm=mm.Pei(),
    # Describe the geographic scope of our simulation:
    scope=StateScope.in_states(["FL", "GA", "MD", "NC", "SC", "VA"], year=2015),
    # Create a SingleLocation initializer
    init=init.SingleLocation(location=0, seed_size=10_000),
    # Set the time-frame to simulate
    time_frame=TimeFrame.of("2015-01-01", 150),
    # Provide model parameter values
    params={
        "theta": 0.1,
        "move_control": 0.9,
        "infection_duration": 4,
        "immunity_duration": 90,
        # Geographic data can be loaded using ADRIOs
        "centroid": us_tiger.InternalPoint(),
        "population": acs5.Population(),
        "commuters": commuting_flows.Commuters(),
        # Except this one...
        # We don't have a humidity ADRIO yet, so we need to load it another way.
        # For now, we have the Pei data files in the project as a convenience.
        "humidity": pei_humidity,
    },
)

# Construct a simulator for the RUME
sim = BasicSimulator(rume)

# Run inside a sim_messaging context to display a nice progress bar
with sim_messaging():
    # Run and save the simulation Output object for later
    out = sim.run(
        # Use a seeded RNG (for the sake of keeping this notebook's results consistent)
        # This parameter is optional; by default a new RNG is constructed for each run
        # using numpy's default_rng
        rng_factory=default_rng(1)
    )
