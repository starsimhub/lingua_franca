"""
Stochastic metapopulation SEIR model of measles, with one patch per district.

The districts and every value are made up: see make_districts.py.
"""
import numpy as np
import pandas as pd
import sciris as sc

__all__ = ['load_districts', 'default_pars', 'distances', 'gravity', 'Sim']

folder = sc.thispath(__file__)

def load_districts():
    """ Load the districts as a dataframe indexed by ID, with region, name, population, lat and lon """
    df = pd.read_csv(folder/'districts.csv')
    df = df.rename(columns={'dotname':'id', 'pop':'population'}).set_index('id')
    df['region'] = df.index.str.split(':').str[0]
    df['name'] = df.index.str.split(':').str[1]
    return df[['region', 'name', 'population', 'lat', 'lon']]


default_pars = sc.objdict(
    # Simulation
    start       = '2010-01-01', # First day; before the years of interest, so the initial conditions wash out
    stop        = '2025-12-31', # Last day
    seed        = 1,     # Random seed
    pop_year    = 2020,  # Year the district populations are for

    # Transmission
    r0          = 15.0,  # Basic reproduction number
    dur_exp     = 6.0,   # Mean latent period (days)
    dur_inf     = 8.0,   # Mean infectious period (days)
    seasonality = 0.2,   # Relative amplitude of seasonal forcing
    peak_day    = 30,    # Day of the year when transmission peaks
    init_sus    = None,  # Initial fraction susceptible; if None, use the endemic equilibrium, 1/r0
    import_rate = 0.01,  # Imported infections per 1000 people per year

    # Mixing between districts
    gravity_k   = 0.01,  # Fraction of contacts made outside the home district
    gravity_c   = 2.0,   # Exponent of the decline in contact with distance

    # Demographics and vaccination
    birth_rate  = 20.0,  # Births per 1000 people per year
    death_rate  = 8.0,   # Deaths per 1000 people per year
    mcv1        = 0.8,   # Routine first-dose coverage (a single value, or one per district)
    vax_eff     = 0.9,   # Fraction of vaccinated infants who become immune

    # Observation
    report_prob = 0.01,  # Probability that an infection becomes a confirmed case
)


def distances(lat, lon):
    """ Great-circle distances in km between all pairs of points """
    lat, lon = np.radians(lat), np.radians(lon)
    dlat = lat[:, None] - lat[None, :]
    dlon = lon[:, None] - lon[None, :]
    a = np.sin(dlat/2)**2 + np.cos(lat[:, None])*np.cos(lat[None, :])*np.sin(dlon/2)**2
    return 2*6371*np.arcsin(np.sqrt(a))


def gravity(population, dist, k, c):
    """
    Gravity mixing matrix, where mix[i,j] is the fraction of their contacts that
    residents of patch i make in patch j.

    Contact with other patches is proportional to their population divided by
    distance**c, and adds up to k. The remaining 1-k is within the home patch.
    """
    mix = population[None, :] / np.maximum(dist, 1e-9)**c
    np.fill_diagonal(mix, 0)
    mix *= k / mix.sum(axis=1, keepdims=True)
    np.fill_diagonal(mix, 1-k)
    return mix


class Sim:
    """
    A measles simulation.

    Args:
        districts (df): one row per district, with columns population, lat and lon
        pars (dict): any parameters to change from default_pars

    **Example**::

        import measles_metapop as mm
        data = mm.load_districts()
        sim = mm.Sim(data.districts, r0=12).run()
        sim.plot()
    """

    def __init__(self, districts, **pars):
        unknown = set(pars) - set(default_pars)
        if unknown:
            raise KeyError(f'Unknown parameters {unknown}; choices are {list(default_pars)}')
        self.districts = districts
        self.pars = sc.mergedicts(default_pars, pars)
        self.results = None

    def run(self):
        """ Run the simulation and store the results """
        p = self.pars
        d = self.districts
        rng = np.random.default_rng(p.seed)
        dates = pd.date_range(p.start, p.stop)
        year = 365

        # Daily rates and probabilities
        beta      = p.r0 / p.dur_inf
        season    = 1 + p.seasonality*np.cos(2*np.pi*(dates.dayofyear.values - p.peak_day)/year)
        mix       = gravity(d['population'].values, distances(d['lat'].values, d['lon'].values), p.gravity_k, p.gravity_c)
        p_inf     = 1 - np.exp(-1/p.dur_exp)
        p_rec     = 1 - np.exp(-1/p.dur_inf)
        p_death   = 1 - np.exp(-p.death_rate/1000/year)
        p_immune  = np.asarray(p.mcv1) * p.vax_eff
        births    = p.birth_rate/1000/year
        imports   = p.import_rate/1000/year

        # Initial conditions: project the population back from pop_year to the start
        growth = (p.birth_rate - p.death_rate)/1000
        N = d['population'].values * np.exp(-growth*(p.pop_year - dates[0].year))
        init_sus = 1/p.r0 if p.init_sus is None else p.init_sus
        S = rng.binomial(N.astype(int), init_sus)
        E = np.zeros_like(S)
        I = np.zeros_like(S)
        R = N.astype(int) - S

        states = np.zeros((len(dates), 4), dtype=int)
        infections = np.zeros((len(dates), len(d)), dtype=int)

        for t in range(len(dates)):
            N = S + E + I + R

            # Transmission: residents of each district are exposed to the prevalence where they make contacts
            foi = beta * season[t] * (mix @ (I/N))
            new_exp = rng.binomial(S, 1 - np.exp(-foi))
            new_exp += np.minimum(rng.poisson(imports*N), S - new_exp)
            new_inf = rng.binomial(E, p_inf)
            new_rec = rng.binomial(I, p_rec)

            # Births, some of whom are immunized by routine vaccination
            new_births = rng.poisson(births*N)
            new_immune = rng.binomial(new_births, p_immune)

            S += new_births - new_immune - new_exp
            E += new_exp - new_inf
            I += new_inf - new_rec
            R += new_immune + new_rec
            for state in [S, E, I, R]:
                state -= rng.binomial(state, p_death)

            states[t] = [S.sum(), E.sum(), I.sum(), R.sum()]
            infections[t] = new_inf # Count infections when they become infectious, i.e. around symptom onset

        cases = rng.binomial(infections, p.report_prob)

        self.results = sc.objdict(
            states     = pd.DataFrame(states, index=dates, columns=['S', 'E', 'I', 'R']),
            infections = pd.DataFrame(infections, index=dates, columns=d.index),
            cases      = pd.DataFrame(cases, index=dates, columns=d.index),
        )
        return self

    def monthly(self, key='cases'):
        """ Return daily results ('cases' or 'infections') as a months x districts dataframe """
        df = self.results[key]
        return df.groupby(df.index.to_period('M')).sum()
