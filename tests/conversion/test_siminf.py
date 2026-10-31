"""
Test importing SimInf's examples against their reference results
"""
import pandas as pd
import sciris as sc
import paths
from starsim.converters.siminf import load_siminf, read_script, Unknown

examples = paths.root/'docs/models/siminf' # The originals
kw = dict(verbose=False)
script = '''
library(SimInf)
transitions <- c("@ -> mu*N -> S", "S -> beta*S*I/N -> I", "I -> gamma*I -> R",
                 "S -> mu*S -> @", "I -> mu*I -> @", "R -> mu*R -> @", "N <- S + I + R")
compartments <- c("S", "I", "R")
n <- 3
u0 <- data.frame(S = rep(990, n), I = c(10, 0, 0), R = rep(0, n))
u0$I[2] <- 5
model <- mparse(transitions = transitions, compartments = compartments,
                gdata = c(beta = 0.3, gamma = 0.1, mu = 1/(70*365)), u0 = u0, tspan = 1:200)
result <- run(model)
plot(result, I ~ .)
'''


def test_examples():
    sc.heading('Testing the SimInf examples ')
    folder = examples / 'sir_herds'
    script = folder/'original'/'events_SIR.R'
    assert [k for k,v in read_script(script).items() if isinstance(v, Unknown)] == ['u0', 'events'] # Computed in R, by u0_SIR() and events_SIR()
    sim = load_siminf(script, u0=folder/'reference'/'u0.csv', events=folder/'reference'/'events.csv.gz', stop=100, **kw) # So passed in, as R wrote them
    assert not sim.imported.incomplete
    sim.run()
    ref = pd.read_csv(folder/'reference'/'results.csv')
    ref = ref[(ref.series == 'S') & (ref.time == 100)].iloc[0]
    S = sim.results.events_SIR.S.values[100]
    assert ref.low - 50 <= S <= ref.high + 50, f'Expected S on day 100 near SimInf\'s {ref.low:n} to {ref.high:n}, not {S:n}'

    folder = examples / 'sise3'
    events = pd.read_csv(folder/'reference'/'events.csv.gz')
    events = events[events.time <= 20] # Only those in the run, since translating all 780k events takes ~15 s
    sim = load_siminf(folder/'original'/'events_SISe3.R', u0=folder/'reference'/'u0.csv', events=events, stop=20, **kw)
    sim.run()
    res = sim.results.events_SISe3
    assert res.phi.values[-1] > 0 # The infected shed into phi
    assert all(sim.diseases[0].states[s].people for s in ['S_2', 'I_3']) # People, though only aging joins them to S_1
    return sim
