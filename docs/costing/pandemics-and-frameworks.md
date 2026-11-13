---
authorship:
  human: 0
  ai: 100
  note: Written by AI
---

# Pandemics, macroeconomics, and modeling frameworks

Most costing elsewhere in this folder is health-sector costing: a unit cost per test, dose, or treatment course, plus DALYs or QALYs (healthy life-years lost or gained) for the health effect. Pandemic modeling differs. When the intervention is closing schools or a third of the economy, the main costs are lost output, lost schooling, and the monetary value of lives lost, in trillions, not millions. These models couple an epidemic model to a (usually very simple) model of the economy, and some let the economy feed back into transmission. Part 1 reviews five such exemplars. Part 2 asks the narrower question that matters most for Starsim v4: which general epi frameworks in [approaches/](../approaches/README.md) support costs and health economic outputs at all, and how. Definitions of DALYs, QALYs, VSL (the value of a statistical life), net monetary benefit (NMB), and related terms are in [metrics.md](metrics.md); cost-effectiveness analysis (CEA) software is in [cea-software.md](cea-software.md).

Code snippets are verbatim from the linked sources, pinned to a commit where possible. Equations come from the cited papers or model descriptions.

# Part 1: Pandemic and macroeconomic epi-economic models

## DAEDALUS

| Disease(s) | Paradigm | Language | Code | Key papers |
|---|---|---|---|---|
| Directly transmitted respiratory pathogens (SARS-CoV-2, SARS-CoV-1, pandemic influenza, and others in a built-in pathogen library) | Deterministic compartmental (age × economic sector × vaccination strata), continuous time | R, with a C++ core on [dust2](https://github.com/mrc-ide/dust2) | [jameel-institute/daedalus](https://github.com/jameel-institute/daedalus) (v0.3.9; companion [daedalus.data](https://github.com/jameel-institute/daedalus.data) and [daedalus.compare](https://github.com/jameel-institute/daedalus.compare)) | Haw et al. (2022), [Optimizing social and economic activity while containing SARS-CoV-2 transmission using DAEDALUS](https://doi.org/10.1038/s43588-022-00233-0), *Nature Computational Science* 2:223–233 |

DAEDALUS is the cleanest public example of an integrated epidemic–economy model. The population is four age groups plus 45 economic sectors of working adults (49 age-sector classes in the package; the original paper used 63 UK sectors), each with its own contact rates and gross value added (GVA, the sector's economic output). Closing a sector reduces both its workers' contacts and its output, so one "openness" coefficient drives the epidemiology and the economics.

- **What is costed.** Three domains, all in US dollars: (1) **economic** losses, as lost GVA by sector, from mandated closures and from illness-related absence (symptomatic, hospitalized, and dead workers); (2) **education** losses, as school days lost × a value of a school day derived from GNI per capita, the lifetime earnings return to a year of schooling, and the (partial) effectiveness of remote teaching; (3) **lives lost**, both as life years lost (deaths × life expectancy by age) and as value of life lost (deaths × age-specific VSL). A separate `get_fiscal_costs()` computes government-side costs: economic support, vaccine doses, NPI implementation, interest, and tax revenue, as a public-debt trajectory.
- **How costs attach to the model.** After the run. `daedalus()` returns a `<daedalus_output>` with compartment trajectories and the NPI timing and openness used; `get_costs()` turns those into costs. Closures can be triggered by a hospital-occupancy threshold, so costs depend on the simulated epidemic, but the cost calculation does not feed back into the run. `get_costs()` also has a `data.frame` method that takes compartment names, sector workforce, daily GVA, VSL, and so on as arguments, so it works on another epidemic model's output, a rare standalone macroeconomic costing function.
- **Health outcomes.** Deaths and hospitalizations by age; life years lost; VSL-valued mortality. No DALYs or QALYs; survivors' morbidity is valued only through lost work.
- **Analyses supported.** Scenario comparison of response strategies (`"none"`, `"elimination"`, `"economic_closures"`, `"school_closures"`), timed versus threshold-triggered responses, vaccination investment scenarios, parameter uncertainty, and fiscal impact. The original 2022 paper optimized sector-by-sector closure configurations to maximize GDP subject to hospital capacity; its abstract describes the economic model as "reflecting sectoral heterogeneity in transmission and complex supply chains". The current R package's cost function, as read, values each sector's lost output independently from its GVA, with no input-output propagation between sectors.
- **Example.** From [`R/costs.R`](https://github.com/jameel-institute/daedalus/blob/152b06bf6405aa35de86895b1d2109b7e2cd003b/R/costs.R#L84-L100), absences and deaths:

  ```r
  sector_cost_absences <- worker_prod_loss %*% diag(gva / workforce)
  ```

  ```r
  life_years_lost <- x$country$life_expectancy * total_deaths

  # NOTE: in million $s
  life_value_lost <- x$country$vsl * total_deaths / 1e6
  ```

  and [closures and education](https://github.com/jameel-institute/daedalus/blob/152b06bf6405aa35de86895b1d2109b7e2cd003b/R/costs.R#L134-L140):

  ```r
      sector_cost_closures <- gva * sector_closures
      economic_cost_closures <- sum(sector_cost_closures)

      education_cost_closures <- vsd *
        n_students *
        sector_closures[i_EDUCATION_SECTOR] *
        (1 - EDU_EFFECTIVENESS_REMOTE)
  ```

  The user-facing call, from the [pandemic costs vignette](https://github.com/jameel-institute/daedalus/blob/152b06bf6405aa35de86895b1d2109b7e2cd003b/vignettes/pandemic_costs.Rmd), is one line per scenario: `cost_list <- lapply(output_list, get_costs, summarise_as = "domain")`.
- **Strengths and limitations.**
  - One parameter (sector openness) acts on both sides of the model, so a closure's epidemiological benefit and economic cost are not assumed separately.
  - Countries are data: switching `country = "United Kingdom"` to another ISO code swaps demography, contact matrices, sector GVA, workforce, VSL, and GNI together from `daedalus.data`.
  - Domains are reported separately (`summarise_as = "domain"`), so users need not accept one exchange rate between GDP and lives, though `total_cost` does add them.
  - The economy is static, with no recovery dynamics, behavior-driven demand loss, or inter-sector links in the current package, and education valuation rests on a few constants (for example `EDU_EFFECTIVENESS_REMOTE <- 0.33`, `EDU_ANNUAL_ROR <- 0.08` in [`R/constants.R`](https://github.com/jameel-institute/daedalus/blob/152b06bf6405aa35de86895b1d2109b7e2cd003b/R/constants.R)).

## Pandemic preparedness investment cases

| Disease(s) | Paradigm | Language | Code | Key papers |
|---|---|---|---|---|
| "SARS-X" (novel SARS-like pathogens); pandemic influenza | Stochastic pandemic-occurrence model over many DAEDALUS-style epidemic runs; static expected-loss calculation | MATLAB (epidemic runs), R (costing and aggregation) | [robj411/p2_drivers](https://github.com/robj411/p2_drivers) | Model description in the repository README ("Costs and impacts of vaccine preparedness investments for SARS-X pandemics"); Fan, Jamison & Summers (2018), [Pandemic risk: how large are the expected losses?](https://doi.org/10.2471/BLT.17.199588), *Bull WHO* 96:129–134 |

Preparedness investment cases ask a different question from outbreak response: what is the expected value, over uncertain future pandemics, of paying now for vaccine R&D, manufacturing capacity, or surveillance? Two exemplars mark the range.

**Fan, Jamison & Summers (2018)** is the static end. It fits an exceedance probability function for influenza pandemics of different severity and computes expected annual losses as the probability-weighted sum of income loss plus the "valuation of the lives lost", using a VSL. Its headline is about 720,000 expected pandemic deaths a year and expected annual losses of about US$500 billion, 0.6% of global income, ranging from a little over 0.3% of national income in high-income countries to 1.6% in lower-middle-income countries, with most of the expected loss coming from rare severe events (figures from the [abstract](https://dash.harvard.edu/entities/publication/73120379-37c8-6bd4-e053-0100007fdf3b)). It has no transmission model or code; it is here because every later preparedness case builds on "expected annual loss".

**`p2_drivers`** is the simulation end, cited by DAEDALUS's README as its other parent. It samples pandemics (pathogen parameters, country, timing), runs a DAEDALUS-type sectoral epidemic model for each under different vaccine-preparedness investments (a broadly protective "BPSV" stockpile, reserved "SSV" manufacturing capacity, enabling activities), and combines epidemic outcomes with a separate **costing model** for the investments themselves.

- **What is costed.** Societal losses from each epidemic (life years, GDP, school years, valued in dollars) and, separately, preparedness and response costs: risk-adjusted R&D cost per candidate (using phase-by-phase probabilities of success), procurement, delivery, and capacity reservation, by country income level.
- **How costs attach to the model.** After each epidemic run (`p2Cost.m`), then aggregated over the sampled pandemics in R. Investment costs come from a separate model ([`code/costing/`](https://github.com/robj411/p2_drivers/tree/51deebbabeca12b2df03567bc9d57dcd5a6634f6/code/costing)) whose outputs (vaccine delivery profiles) are also inputs to the epidemic runs.
- **Health outcomes.** Deaths, converted to life years lost using GBD remaining life expectancy weighted by the age distribution of deaths, then valued with a value of a life year (VLY) back-calculated from the VSL.
- **Analyses supported.** Expected societal loss averted per dollar of preparedness investment, by investment type and country income group, with probabilistic sampling of pathogen, country, and cost parameters.
- **Example.** The loss function, from the [README](https://github.com/robj411/p2_drivers/blob/51deebbabeca12b2df03567bc9d57dcd5a6634f6/README.md#1-societal-losses):

  $$\text{TSL} = K_1\text{VLY} + K_2 + K_3\text{VSY}$$

  "where $K_1$ is the number of life years lost and VLY the value of a life year; $K_2$ is the sum of lost GDP over the period due to reduced economic activity of sectors; and $K_3$ is the number of school years lost and VSY the value of one school year." The VLY is defined from the VSL as a population-weighted average, $\text{VSL}=\frac{\sum_g\tilde{N}_gl_g^{\text{(life)}}}{\sum_g\tilde{N}_g}\text{VLY}$. In code, from [`p2Cost.m`](https://github.com/robj411/p2_drivers/blob/51deebbabeca12b2df03567bc9d57dcd5a6634f6/code/functions/p2Cost.m#L37-L46):

  ```matlab
  %% value of life lost

  deaths    = deathmat;
  costs.deaths = deaths(end,:);

  lyl       = deaths(end,:).*data.yll;
  costs.life_years = lyl;

  vlyl      = lyl*data.vly;
  costs.value_YLL = vlyl;
  ```
- **Strengths and limitations.**
  - The only public exemplar found that separates the cost of *interventions* (R&D with attrition, capacity reservation, delivery) from the *losses* they avert, and models both stochastically.
  - Valuing deaths by remaining life years (not a flat VSL per death) makes the age profile of mortality matter, as it should for respiratory pandemics.
  - It is research code (MATLAB plus R scripts), not a library; reuse means treating the README as a specification.
  - The local `PandemicPreparednessValuation23` repository is not public on GitHub (the URL returns 404), so it is not reviewed here.

## SIR-macro (Eichenbaum, Rebelo & Trabandt)

| Disease(s) | Paradigm | Language | Code | Key papers |
|---|---|---|---|---|
| COVID-19 (generic SIR-type epidemic) | Deterministic SIRD embedded in a dynamic general-equilibrium macroeconomic model; optimal policy | MATLAB | Replication code from the authors' sites ([tinyurl.com/ERTcode](https://tinyurl.com/ERTcode), which resolves to a zip on Mathias Trabandt's site); not on GitHub | Eichenbaum, Rebelo & Trabandt (2021), [The Macroeconomics of Epidemics](https://www.nber.org/papers/w26882), *Review of Financial Studies* 34(11):5149–5187 (NBER WP 26882, 2020) |

This is the classic economist's epi-economic model and the opposite design from DAEDALUS: minimal epidemiology, and a full optimizing economic model in which people choose how much to consume and work. Consumption and work are where people meet, so those choices set the infection rate, which feeds back into the choices. There are hundreds of follow-on "SIR-macro" papers.

- **What is costed.** Lost consumption (the recession) and lost lives, both in household welfare (lifetime discounted utility), not separate dollar totals.
- **How costs attach to the model.** During simulation, inseparably: there is no costing step. Containment is a tax on consumption whose path the planner chooses to maximize welfare, so the "cost of the lockdown" and "value of deaths averted" are terms of one objective.
- **Health outcomes.** Deaths only. The value of a life is not an input: it is the discounted utility of a representative person's remaining life, and the authors calibrate the discount factor so it equals "9.3 million 2019 dollars", "consistent with the economic value of life used by U.S. government agencies" (with a sensitivity case at 6.1 million).
- **Analyses supported.** Competitive equilibrium versus optimal containment; effects of delaying or ending containment early; vaccines and treatments arriving at random times; capacity-constrained health care.
- **Example.** The transmission function, from the [NBER working paper](https://www.nber.org/system/files/working_papers/w26882/w26882.pdf) (Section 2.2), has one term per place people meet:

  $$T_t = \pi_1 (S_t C_t^s)(I_t C_t^i) + \pi_2 (S_t N_t^s)(I_t N_t^i) + \pi_3 S_t I_t$$

  where $C_t^s, C_t^i$ are consumption and $N_t^s, N_t^i$ hours worked by susceptible and infected people. The paper describes these as the three ways susceptible people can become infected: while purchasing consumption goods, at work, and through other contacts.
- **Strengths and limitations.**
  - The only exemplar here where economic behavior and the epidemic drive each other, which is why it predicts a recession even without mandates (people cut consumption voluntarily).
  - Costs and benefits share one unit by construction, so optimal-policy questions are well posed.
  - The epidemiology is one homogeneous SIR, with no age structure or contact heterogeneity, which limits its use for vaccine allocation or school policy.
  - Outputs are in welfare units and are hard to compare with a health-sector CEA.

## LSHTM CMMID COVID-19 vaccine valuation (covidm)

| Disease(s) | Paradigm | Language | Code | Key papers |
|---|---|---|---|---|
| COVID-19 | Age-structured deterministic/stochastic compartmental (covidm), with a separate economic model | C++/R (covidm) | covidm is described as available on the CMMID GitHub; public repositories include [nicholasdavies/covidm-alpha](https://github.com/nicholasdavies/covidm-alpha) and [cmmid/covid-uk](https://github.com/cmmid/covid-uk). The economic layer of the paper below does not appear to be public. | Sandmann et al. (2021), [The potential health and economic value of SARS-CoV-2 vaccination alongside physical distancing in the UK](https://doi.org/10.1016/S1473-3099(21)00079-7), *Lancet Infect Dis* ([PMC full text](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7972313/)) |

This is conventional health-economic evaluation (QALYs, a threshold, discounting of future values, PSA or probabilistic sensitivity analysis) applied to a pandemic, with a simple macroeconomic perspective added. It sits between health-sector CEA and DAEDALUS.

- **What is costed.** Two perspectives (whose costs count). From the NHS perspective: hospital and other health care costs, and vaccine doses ("a conservative long-run cost per vaccine dose of £15"). From a wider societal perspective: GDP losses from physical distancing, assumed at "2% of daily GDP (ie, around £115·1 million) for each day COVID-19 incidence exceeded 1000 new reported cases", with 2–15% explored for mandated distancing. Health-sector costs and patient productivity losses are not added to GDP losses, "to avoid double counting".
- **How costs attach to the model.** After the run: the transmission model produces cases, admissions, ICU stays, deaths, and days of distancing by scenario, and a separate economic model applies unit costs, QALY losses, and the GDP rule, with a PSA over the economic parameters.
- **Health outcomes.** QALYs lost by symptomatic cases, non-fatal admissions, ICU survivors, long COVID, adverse events following immunization, and premature deaths, discounted at 3.5% a year, valued at £20,000 per QALY.
- **Analyses supported.** Net monetary value of vaccination scenarios over 10 years, under several distancing regimes, vaccine efficacies, and durations of protection; sensitivity to the discount rate (0–10%) and GDP-loss assumptions.
- **Example.** From the abstract: "We expressed the health and economic benefits of each scenario with the net monetary value: QALYs × (monetary value per QALY) – costs."
- **Strengths and limitations.**
  - Standard metrics matching the UK reference case, or agreed method (QALYs, NMB, 3.5% discounting), so results compare with other UK appraisals.
  - The GDP perspective is a threshold rule, not a model of the economy; it makes the macroeconomic cost visible but rough.
  - Keeping NHS costs and GDP losses in separate perspectives is a good pattern for any library: perspectives are different sums, not one total.
  - Thunström et al. (2020), [The benefits and costs of using social distancing to flatten the curve for COVID-19](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7242774/), *J Benefit-Cost Anal* 11(2):179–195, is the parallel US exemplar on the VSL side: lives saved by distancing, valued with a VSL, against GDP losses, with a benchmark net benefit of about $5.2 trillion.

## PTTI (population-wide testing, tracing, and isolation)

| Disease(s) | Paradigm | Language | Code | Key papers |
|---|---|---|---|---|
| COVID-19 | SEIR-TTI ODE (primary), plus agent-based, network ([EoN](../approaches/eon.md)), and Kappa rule-based variants of the same model | Python | [ptti/ptti](https://github.com/ptti/ptti) (archived on [Zenodo](https://doi.org/10.5281/zenodo.4298798)) | Sturniolo et al. (2021), [Testing, tracing and isolation in compartmental models](https://doi.org/10.1371/journal.pcbi.1008633), *PLOS Comput Biol*; Colbourn et al. (2020), Modelling the health and economic impacts of population-wide testing, contact tracing and isolation (PTTI) strategies for COVID-19 in the UK, SSRN working paper ([UCL record](https://discovery.ucl.ac.uk/id/eprint/10128778/)) |

PTTI is the best public example found of operational costing of a test-trace-isolate program inside an epidemic model: not a cost per test, but how many tracers, supervisors, and labs a given trajectory requires, with hiring and contract-length rules.

- **What is costed.** Contact tracing (tracers, supervisors, team leads, hiring costs, a tracing app, public communications); testing (laboratory startup and staffing, sized to peak testing demand within each contract block, plus a cost per PCR test); NHS treatment costs per recovered case; and GDP loss, scaled by how far contact rates are below normal and by the fraction of the population in isolation.
- **How costs attach to the model.** After the run, on the full trajectory. `calcArgumentsODE()` reads daily compartment sizes and time-varying parameters (testing rate `theta`, contacts `c`, tracing success `chi`) from a run and derives daily tests, traces, and isolations; `calcEconOutputs()` turns those into costs. Capacity is "ratcheted": tracers and labs, once hired, are paid until the end of their contract block.
- **Health outcomes.** Deaths, ICU and hospital admissions, and cases, derived from cumulative recoveries using fixed fractions. No QALYs or DALYs.
- **Analyses supported.** Comparison of 31 UK scenarios combining lockdown, testing, tracing, and face coverings, reporting deaths, program cost, and GDP loss side by side (the working paper's best scenario had about 52,000 deaths, about £8 billion intervention cost, and about £500 billion GDP loss, according to the [UCL news release](https://www.ucl.ac.uk/news/2020/jun/urgent-testing-tracing-and-isolation-could-save-lives-and-economy)).
- **Example.** GDP as a function of contacts and isolation, from [`ptti/economic.py`](https://github.com/ptti/ptti/blob/f179763f9afdc903ff3ee2b355cda56be0af86b2/ptti/economic.py#L186-L199):

  ```python
      # Economy Scales with contacts
      # Economy minimum is: econ_inputs['Shutdown']['UK_Shutdown_GDP_Penalty'], with econ_inputs['Shutdown']['UK_Shutdown_Contacts']
      # Full strength is 0 penalty at econ_inputs['Shutdown']['UK_Open_Contacts']
      Daily_GDP = []
      Daily_GDP_Base = econ_inputs['Shutdown']['UK_GDP_Monthly'] / 30
      Isolated_Fraction = isolated / population # Each person in isolation is a fraction of the economy fully closed.
      # print(Isolated_Fraction)

      Shutdown_Fraction = 1 - (contacts-econ_inputs['Shutdown']['UK_Shutdown_Contacts'])/(
          econ_inputs['Shutdown']['UK_Open_Contacts'] - econ_inputs['Shutdown']['UK_Shutdown_Contacts'])

      Daily_GDP = (1 - Shutdown_Fraction *
                   econ_inputs['Shutdown']['UK_Shutdown_GDP_Penalty'])*(1-Isolated_Fraction)*Daily_GDP_Base
      No_Pandemic_GDP = days * Daily_GDP_Base
  ```
- **Strengths and limitations.**
  - Costs depend on capacity, not just volume: a program has fixed, step, and variable costs, and the *peak* of simulated demand sets the step costs. Almost no other disease model does this.
  - GDP loss is tied to the model's own contact-rate parameter, the same idea as DAEDALUS openness, in one line.
  - The economic inputs are one UK dictionary (`economic_data.py`) and the costing uses the ODE model's compartment names, so reuse takes adaptation, even across PTTI's own variants.
  - The repository has been inactive since November 2020.

We checked other candidates but gave them no full entries. The Imperial [`squire`](https://github.com/mrc-ide/squire) and [`nimue`](https://github.com/mrc-ide/nimue) packages, widely used for COVID-19 vaccine impact, contain no costing code (searched for cost, QALY, DALY, and GDP); that work did costing separately. Covasim has no built-in costing, and we found no public Covasim testing or tracing cost-effectiveness code in the IDM repositories checked. We found no One Health or zoonotic spillover economic models with public code of comparable maturity.

# Part 2: Costing and health economic outputs in general epi frameworks

The question is not whether someone has done a cost-effectiveness analysis with a framework (people have, with nearly all of them), but whether the framework itself supports costs or DALYs/QALYs. Mostly it does not. Support takes four forms: a cost on an intervention or product, tallied at delivery (EMOD, Starsim v4, STIsim); an analyzer or observer that adds up person-time or events into YLL/YLD, years of life lost and lived with disability (HPVsim, Vivarium); a user-written module that does both every step (EpiModel's gallery example); or costs as a direct optimization input (Atomica, and in a different sense MEmilio's optimal-control example).

## The Starsim family

**Starsim v3 (latest release, 3.7.2)** has no cost or DALY code. A search of [`starsim/`](https://github.com/starsimhub/starsim/tree/main/starsim) for cost, DALY, QALY, YLL, and YLD finds only comments about computational cost. Costing in Starsim-based projects has been done with custom analyzers.

**Starsim v4 (the [`v4` branch](https://github.com/starsimhub/starsim/tree/v4), in development)** adds a per-delivery `cost` to every product. `ss.Vaccine`, `ss.Treatment`, and `ss.Diagnostic` all accept `cost=`, and the delivery interventions (`ss.vaccinate()`, `ss.treat()`, `ss.screen()`) add a `cost` result when their product has one. Its library adds `ssl.Costs`, `ssl.DALYs`, `ssl.ICER`, and `ssl.discount()`; the docs show [how to use them](https://starsim.org/v4/user_guide/library_econ.html). From [`starsim/products.py`](https://github.com/starsimhub/starsim/blob/v4/starsim/products.py) (the `ss.Diagnostic` docstring):

````python
        cost (float): the cost of each delivery
        ...

    Examples:
        ```python
        pcr = ss.Diagnostic(sensitivity=0.9, specificity=0.98, cost=4.00, delay=ss.days(2))
````

and from [`starsim/interventions.py`](https://github.com/starsimhub/starsim/blob/8c10e9e5bf9b8b2ebfdb1fb103e14e202ea99631/starsim/interventions.py#L775-L785), the result is created only when a cost is given:

```python
    def init_results(self):
        super().init_results()
        abm = self.sim.solver == 'abm'
        results = [
            ss.Result('delivered', dtype=float, scale=abm, label='Number delivered', summarize_by='sum'),
            ss.Result('eligible', dtype=float, scale=abm, label='Number eligible', auto_plot=False),
            ss.Result('coverage', dtype=float, scale=False, label='Coverage of those eligible', auto_plot=False),
        ]
        if getattr(self.product, 'cost', None) is not None:
            results += [ss.Result('cost', dtype=float, scale=abm, label='Cost', summarize_by='sum')]
```

and is filled at delivery, using the same `tally()` as the delivered count ([`interventions.py#L1014-L1016`](https://github.com/starsimhub/starsim/blob/8c10e9e5bf9b8b2ebfdb1fb103e14e202ea99631/starsim/interventions.py#L1014-L1016)):

```python
        n = self.tally('delivered', chosen)
        if 'cost' in res:
            self.tally('cost', chosen, product.cost)
```

Two properties are worth noting. Because `tally()` also fills `res.strata` when the sim is stratified, costs come out by stratum (age, sex, risk group) automatically, like disease results. And the same code runs whether the sim is agent-based or compartmental (`self.selector.abm`), so the cost result means the same thing in both. What it does not do: costs are flat per delivery (no fixed, capacity, or per-person-time costs), and this core result has no discounting, currency/year metadata, or health-effect counterpart (no DALY or QALY result). [TBsim](https://github.com/starsimhub/tbsim) (on Starsim v4) passes `cost=` through its TB-specific tests, vaccines, and preventive therapy, for example in [`tbsim/interventions/care.py`](https://github.com/starsimhub/tbsim/blob/d3996bf4350d5b1968a7b9d09665a5b2ae8e6f7a/tbsim/interventions/care.py#L35): "kwargs (dict): passed to `ss.Test`, e.g. `cost=` or `delay=`".

**STIsim** has a [`logistics`](https://github.com/starsimhub/stisim/tree/f9af9e8be546a479db467a4360ecb06e38c5036d/stisim/logistics) subpackage that models finite supply, not just cost. A `Product` (name, `ProductCategory` such as `PREP` or `ART`, `DeliveryMode` such as `SHOT` or `PILL`, per-unit `cost`, and efficacy by time since delivery) is held in a `Supply` with a quantity (possibly `np.inf`), several supplies form a `Supplies` pool that can be shared across interventions, and an abstract `SuppliedIntervention` allocates limited stock across eligibility groups in proportion to their coverage gaps. Cost accrues when stock is used, from [`supply.py`](https://github.com/starsimhub/stisim/blob/f9af9e8be546a479db467a4360ecb06e38c5036d/stisim/logistics/supply.py#L36-L47):

```python
    def use(self, quantity):
        """uses a specified quantity of the product, returning the remaining quantity and cost of usage"""
        remaining = self.quantity - quantity
        if remaining < 0:
            raise self.InsufficientSupplyException(f"Attempted to use {quantity} {self.product.name}. "
                                                   f"Only {self.quantity} exists.")
        self.quantity = remaining

        cost = quantity * self.product.cost
        self.accrued_cost += cost

        return self.quantity, cost
```

Costs are tracked at two levels: `SuppliedIntervention.accrued_cost` (this intervention's own spend) and `Supplies.accrued_cost` (the total across every intervention drawing on the shared stock), making the attribution choice explicit. Limitations: `accrued_cost` is a running total, not a time series, so costs by year or stratum are not recorded; `Product` is separate from `ss.Product` (a TODO in the source says to reconcile them); and selection uses Python's `random.sample`, not Starsim's common random numbers (also marked TODO).

**HPVsim** (now on Starsim) has a [`dalys` analyzer](https://github.com/starsimhub/hpvsim/blob/9037e7b211771b6dc9696509b684f973dd68e2eb/hpvsim/analyzers.py#L482-L575) computing incidence-based DALYs for cervical cancer: at each cancer onset it adds YLL (reference life expectancy minus age at the scheduled cancer death) and YLD (duration with cancer times a stage-weighted average disability weight, GBD 2017 by default), weighted by agent scale and multiplied by `pop_scale` at the end of the run. The core, from [`analyzers.py#L535-L541`](https://github.com/starsimhub/hpvsim/blob/9037e7b211771b6dc9696509b684f973dd68e2eb/hpvsim/analyzers.py#L535-L541):

```python
    def _accumulate(self, year, cancer_age, death_age, weight):
        if year < self.start_year or year > self.end_year:
            return
        idx = year - self.start_year
        dur = death_age - cancer_age
        self.yld[idx] += float((weight * dur * self.av_disutility).sum())
        years_left = np.maximum(0.0, self.life_expectancy - death_age)
        self.yll[idx] += float((weight * years_left).sum())
```

It reads the scheduled `ti_dead_cancer` at onset, so DALYs are attributed to the onset year even when the death falls after the simulation ends; there is no discounting and no cost counterpart. The cancer/NCD page covers HPVsim's health-economic analyses in more depth.

**FPsim, Covasim, Rotasim, RSVsim**: no cost, DALY, or QALY code was found in their main branches. **LASER** ([laser-core](https://github.com/laser-base/laser-core)): none found.

## Other frameworks

**EMOD** has the oldest built-in cost mechanism in this review. Every intervention has a `Cost_To_Consumer` parameter (with intervention-specific defaults, for example 3.75 for `RTSSVaccine` and 8.0 for `Ivermectin` in the [source](https://github.com/EMOD-Hub/EMOD/tree/main/interventions)); when an intervention is distributed it notifies the node, which multiplies by the agent's Monte Carlo weight and accumulates a "Campaign Cost" channel in `InsetChart.json` (with units `"USD"` set in [`Report.cpp`](https://github.com/EMOD-Hub/EMOD/blob/01f8b6f20522ede55da11c208e24ef5c5207bb38/Eradication/Report.cpp#L365)). From [`NodeEventContext.cpp`](https://github.com/EMOD-Hub/EMOD/blob/01f8b6f20522ede55da11c208e24ef5c5207bb38/Eradication/NodeEventContext.cpp#L118-L130):

```cpp
    void NodeEventContextHost::notifyCampaignExpenseIncurred(float expenseIncurred, const IIndividualHumanEventContext * pIndiv)
    {
        release_assert( node );
        if( expenseIncurred > 0 )
        {
            LOG_DEBUG("Campaign expense was incurred\n");
        }
        float cost = expenseIncurred;
        if( pIndiv != nullptr )
        {
            cost *= float( pIndiv->GetMonteCarloWeight() );
        }
        IncrementCampaignCost( cost );
```

The schema describes the parameter this way: "Setting Cost_To_Consumer to zero for all other interventions, and to a non-zero amount for one intervention, provides a convenient way to track the number of times the intervention has been applied in a simulation." In practice it was used at least as often as a delivery counter as for costing, since all interventions sum into one channel. EMOD has no DALY or QALY reporter (searched the [EMOD-Hub/EMOD](https://github.com/EMOD-Hub/EMOD) source for DALY); burden was computed afterwards from event and age reports.

**EpiModel** has no costing in the core package, but the official [EpiModel Gallery](https://github.com/EpiModel/EpiModel-Gallery) includes a [cost-effectiveness example](https://github.com/EpiModel/EpiModel-Gallery/tree/5e4f50879f225a13a99a52932ce9b6d2d7f5f705/examples/cost-effectiveness): a custom module, run every step, that adds state costs, state- and age-dependent QALYs, and amortized intervention costs (spread over their useful life), discounts them, and records them as epidemic outputs; the script then calls `dampack::calculate_icers()`. From [`module-fx.R#L40-L64`](https://github.com/EpiModel/EpiModel-Gallery/blob/5e4f50879f225a13a99a52932ce9b6d2d7f5f705/examples/cost-effectiveness/module-fx.R#L40-L64):

```r
  # Account for costs of each sub-population
  pop.sus.cost <- length(idsSus) * sus.cost
  pop.inf.cost <- length(idsInf) * inf.cost
```

```r
  # Discount aggregated costs and effects
  t <- at - cea.start
  pop.cost.disc <- pop.cost * 1 / (1 + disc.rate) ^ (t / 52)
  pop.qaly.disc <- pop.qaly * 1 / (1 + disc.rate) ^ (t / 52)
```

This is the "state-cost" pattern from CEA software (cost and utility, or quality of life, per person-time in a state) written as a simulation module. Note the hard-coded `/ 52` weekly time step.

**Vivarium** ([vivarium_public_health](https://github.com/ihmeuw/vivarium_public_health)) has burden built in, as expected from IHME: a `MortalityObserver` for cause-specific deaths and YLLs, and a `DisabilityObserver` for YLDs from a `disability_weight` value pipeline fed by each disease state, both stratifiable. The package has no costs; the cancer/NCD page covers Vivarium simulations that add them.

**Atomica** is the one framework in the review where cost is a model input, not an output: programs in the `progbook` have unit costs, spending, and coverage functions, and `reconcile()` and the optimizers allocate a budget across programs to minimize an objective (see [atomica.md](../approaches/atomica.md); the HIV/optimization page has more). Burden metrics are user-defined framework parameters, not built-in DALYs.

**OpenMalaria** has no cost or DALY output in its current source ([SwissTPH/openmalaria](https://github.com/SwissTPH/openmalaria); the `cost` attributes in old schemas are fitness costs of drug-resistance mutations). It does output the resource-use counts costing needs: survey measures such as `nTreatments1`, `nTreatDiagnostics`, `nMassITNs`, `nEPIVaccinations`, and `expectedDirectDeaths`, which published evaluations cost afterwards. The malaria page has more.

**MEmilio** has no general cost or burden output, but its [`ode_seair_optimization.cpp`](https://github.com/SciCompMod/memilio/blob/main/cpp/examples/ode_seair_optimization.cpp) example solves an optimal-control problem in which "the socioeconomic costs are to be minmized using an objective functional which is the weighted integral of the nonpharmazeutical interventions and testing costs", using IPOPT with automatic differentiation. Cost here is an abstract weight on control effort, not money.

**flepiMoP** has a well-developed declarative outcomes model ([flepimop.md](../approaches/flepimop.md): source × probability × delay × duration, chainable from infections to cases, hospitalizations, and deaths) that produces exactly the event and occupancy series costing or DALYs need, but no costs or burden metrics (a search of [HopkinsIDD/flepiMoP](https://github.com/HopkinsIDD/flepiMoP) for cost finds only computational uses).

**odin/dust, summer2, epydemix, individual, epiworld, SimInf, EoN, EMULSION, epymorph, MetaCast, epipack, EpiHiper, camdl, epidemics**: no cost, DALY, or QALY support found. odin/dust2 is nonetheless the engine under DAEDALUS, so the macroeconomic costing above shows what can sit on an odin-family model.

## Summary table

| Framework | Costs | DALYs/QALYs | Mechanism | Notes |
|---|---|---|---|---|
| Starsim v3 | No | No | — | Custom analyzers only |
| Starsim v4 (`v4` branch) | Yes: per-delivery `cost=` on `ss.Vaccine`, `ss.Treatment`, `ss.Diagnostic`; `ssl.Costs` | DALYs: `ssl.DALYs` | Delivery intervention tallies a `cost` result, by stratum, in ABM and compartmental runs; library analyzers add them up | Flat unit cost; `ssl.discount()` and fixed costs in the library; no QALYs or currency metadata |
| STIsim | Yes: per-unit `Product.cost` with finite `Supply` | No | `SuppliedIntervention.use()` draws down stock and accrues cost | Per-intervention and pooled totals; scalar, not a time series |
| HPVsim | No built-in costs | DALYs (YLL + YLD) | `hpv.dalys` analyzer, incidence-based, GBD 2017 weights | Undiscounted; cervical cancer only |
| TBsim | Via Starsim v4 `cost=` | No | Pass-through to `ss.Test` / `ss.Vaccine` / `ss.Treatment` (`ss.Diagnostic` in current v4) | |
| FPsim, Covasim, Rotasim, RSVsim | No | No | — | |
| LASER | No | No | — | |
| EMOD | Yes: `Cost_To_Consumer` on every intervention | No | Accumulated into one "Campaign Cost" channel, Monte Carlo weighted | Single channel for all interventions; often used as a counter |
| EpiModel | Via extension | QALYs via extension | Gallery module accumulates state costs and QALYs each step, discounted; `dampack` for ICERs | Not in core; example hard-codes weekly steps |
| Vivarium | No | YLLs and YLDs | `MortalityObserver`, `DisabilityObserver`; disability weights as a value pipeline | Stratified burden; no costs |
| Atomica | Yes, as model inputs | User-defined | Programs with unit costs and coverage functions; budget optimization | Cost drives coverage rather than being tallied |
| OpenMalaria | No | No | Emits resource-use counts for post hoc costing | |
| MEmilio | Abstract control costs in one example | No | Optimal-control objective (IPOPT) | Not monetary |
| flepiMoP | No | No | Outcomes module produces the series costing needs | |
| DAEDALUS (for comparison) | Yes: GVA, education, VSL, fiscal | Life years lost | Post hoc `get_costs()`, also applicable to other models' output | Macroeconomic, not health-sector |
| odin/dust, summer2, epydemix, individual, epiworld, SimInf, others | No | No | — | |

## Cross-cutting patterns

- **Pandemic costing is dominated by what health-sector CEA leaves out.** In DAEDALUS, p2_drivers, PTTI, and the Sandmann analysis, GDP losses from closures far exceed treatment costs. "Cost = unit cost × deliveries" is not the whole story; a general library needs a way to cost *states of the world* (sector openness, contact reduction, isolation) per unit time, not just interventions per delivery.
- **The best epi-economic models use one parameter on both sides.** DAEDALUS sector openness, PTTI contact rates, and ERT consumption all drive transmission and output together. For Starsim this argues for interventions whose effect parameter (for example a network contact multiplier) is also a declared, recorded quantity a cost function can read, not a change buried in `step()`.
- **Costing after the run is the norm, which works if the outputs carry enough.** Every Part 1 model except ERT computes costs after the run. They need person-time by state, age, and sector; events by age; the actual timing and level of each intervention; and peaks (for capacity costs). DAEDALUS's `get_costs.data.frame()` shows the end point: a costing function that needs only named outputs, whatever model produced them.
- **Lives are valued in three incompatible ways.** VSL per death (DAEDALUS, Thunström), value of a life year × remaining life expectancy (p2_drivers), and QALYs at a threshold (Sandmann), plus the welfare value that emerges in ERT. A library should output the ingredients (deaths by age and time, remaining life expectancy, person-time in states) and leave valuation to configurable post-processing, as [metrics.md](metrics.md) argues.
- **Perspectives should be separate sums, not one total.** Sandmann keeps NHS costs and GDP losses apart to avoid double counting; DAEDALUS reports domains separately. A cost result should carry a perspective or category label (health system, household, government, society) so totals are a choice, not a default.
- **Capacity and supply matter.** PTTI sizes labs and tracers to peak demand; STIsim's `Supplies` limits stock and allocates it by coverage gap; Atomica makes budget the limit. Starsim v4 already has a `capacity` on delivery; adding fixed and step costs would cover most of the PTTI pattern.
- **The Starsim family has many of the building blocks.** Starsim v4 tallies per-delivery cost by stratum in both ABM and compartmental runs, and its library adds up costs, DALYs, and ICERs. STIsim adds finite supply and cost attribution across shared stock, and HPVsim's `dalys` analyzer shows the incidence-based YLL/YLD pattern. What is missing is shared, not disease-specific: currency metadata, per-time costs on states, and QALYs.
- **Built-in cost channels get used as counters.** EMOD's single "Campaign Cost" channel was often used to count deliveries. Starsim v4's separate `delivered` and `cost` results avoid that; keeping costs per intervention, product, and stratum, not summed into one channel, makes them usable.
- **Macroeconomic models are a different layer, not a different engine.** DAEDALUS runs on dust2 and its economics is a few hundred lines of R over the trajectory. A Starsim-family equivalent would be an analyzer plus country data (sector GVA, workforce, VSL, GNI), attached to a network or mixing-pool model with sectors as strata.
