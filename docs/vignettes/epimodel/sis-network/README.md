# EpiModel SIS on a dynamic network, in Starsim

The translation of [models/epimodel/sis-network](../../../models/epimodel/sis-network). The model is `model.py`; `compare.py` checks it against the original's reference results.

## Comparison

| Measure | Original | Starsim | |
|---|---|---|---|
| Lines of model code | 13 | 9 |  |
| One run | first 8 s, rerun 7 s | first 0.45 s, rerun 0.43 s (Rust) | The first run of the original includes estimating the network (`netest`), which is done once; a rerun uses the fitted network |
| Results | | | **Agree, once the order within a step is allowed for** (within 5% at equilibrium): 11.7 new infections a step at equilibrium, against 12.0 (means of 100 runs each). Over the last 200 steps 240 of 500 are infected, against 227.5: EpiModel lets people recover in the step in which they are infected and counts them after that, which makes its count 5% lower for the same epidemic (240 × 0.95 = 228). With the same allowance, 118 are infected after step 50, against 113, where the runs vary most |

Measured on 31 October 2026 with Starsim 4.0.0 (the `v4` branch, commit `4473e253`), on a 20-core Linux machine.

## What was declared and what was not

Everything is declared: two transitions and a network, described by the same targets as the original (`ss.DegreeNet(n_contacts=0.7, concurrency=0.22, max_contacts=3, dur=50, acts=ss.freqperday(2))`). The chance of transmission is per act, as in EpiModel, and the probabilities per step are written as `ss.prob`.

## Findings

- **Described the way EpiModel describes it, but not an ERGM.** The original fits a network to target statistics: 175 partnerships, 110 people with two or more partners, nobody with four or more. `ss.DegreeNet` takes the same targets: people look for partners at a rate that depends on how many they have, chosen so that the targets are the network's stable state, and partnerships end at a constant rate. It has 176 partnerships and 109 people with two or more (EpiModel's network has 177 and 111). It matches the number of partners people have, and not other structure an ERGM can target, such as triangles. EpiModel's approach is the more general one.
- **Network diagnostics.** The original reports the edges, mean degree, concurrency, and partnership duration of the simulated network over time. `ss.DegreeNet` records the mean number of partners and the share with two or more as results, and `net.check()` compares them with the targets over a few runs, as `netdx()` does.
- **Fixed: acts in a partnership.** The first version worked out a probability per partnership by hand; `acts=` on the network now says it directly. In this sim, with no unit, a day is a step, so `ss.freqperday(2)` reads a little oddly for "two acts a step".
