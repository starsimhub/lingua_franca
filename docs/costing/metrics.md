---
authorship:
  human: 0
  ai: 100
  note: Written by AI
---

# Health economic metrics

A short reference to the health economic indicators disease models are asked to compute, for modelers, not economists. Each entry gives a definition, a formula, what the model has to output, and common pitfalls. Almost every metric can be worked out after the run from a few model outputs (person-time in states, event counts, the ages and times of events, and each event's cause or intervention), plus outside inputs (weights, unit costs, life tables, discount rates, thresholds). The last section, [What a disease model needs to provide](#what-a-disease-model-needs-to-provide), lists those outputs. The sources cited were checked; where a number could not be, the text says so.

## Contents

- [Notation and conventions](#notation-and-conventions)
- [Health outcome measures](#health-outcome-measures)
- [Costs](#costs)
- [Discounting](#discounting)
- [Decision metrics](#decision-metrics)
- [Uncertainty and value of information](#uncertainty-and-value-of-information)
- [Equity](#equity)
- [Allocative efficiency and optimization](#allocative-efficiency-and-optimization)
- [Reference cases and reporting standards](#reference-cases-and-reporting-standards)
- [What a disease model needs to provide](#what-a-disease-model-needs-to-provide)

## Notation and conventions

- $t$ is calendar time measured in years from the analysis start (the discounting base year); $T$ is the time horizon.
- $a$ is age in years; $s$ indexes health states (or disease sequelae); $i$ indexes agents; $k$ indexes strategies (interventions, scenarios, packages); $k=0$ is the comparator (the option others are measured against).
- $P_s(t,a)$ is the number of people in state $s$ at time $t$ and age $a$ (prevalence); $\int P_s\,dt$ is person-time.
- $D(t,a)$ is the death count (optionally by cause) at time $t$ and age $a$.
- $r$ is an annual (discrete) discount rate, the yearly rate at which future values count for less; $\rho = \ln(1+r)$ is the equivalent continuous rate.
- $E_k$ and $C_k$ are total (discounted) health effect and cost under strategy $k$; $\Delta E = E_k - E_0$, $\Delta C = C_k - C_0$.
- $\lambda$ is a cost-effectiveness threshold (willingness to pay per unit of health).
- "Averted" always means a difference between two simulated worlds (comparator minus intervention), never an observed quantity. In a stochastic agent-based model it is well estimated only with common random numbers or many replicates.

## Health outcome measures

### Summary measures of population health (HALYs)

Health-adjusted life years (HALYs) combine mortality and morbidity into one number. The two main ones are the QALY (quality-adjusted life-year, a health "gain" from economic evaluation; utility, its quality-of-life score, is 1 for full health and 0 for dead) and the DALY (disability-adjusted life-year, a health "loss" from burden-of-disease studies; disability weight is 0 for full health and 1 for dead). [Gold, Stevenson and Fryback 2002](https://doi.org/10.1146/annurev.publhealth.23.100901.140513) review their history and differences, and warn against mixing them across decisions. For a modeler, both are a state-dependent weight integrated over person-time, plus a mortality part. They differ in the weights, how death counts, and what life is measured against.

### DALYs

**Definition.** One DALY is one lost year of healthy life. $\text{DALY} = \text{YLL} + \text{YLD}$, where YLL are years of life lost to premature mortality and YLD are years lived with disability. The measure was introduced for the GBD 1990 study by [Murray 1994](https://pmc.ncbi.nlm.nih.gov/articles/PMC2486718/) (Bull WHO 72(3):429–445).

**YLL.** For each death at age $a$, YLL is the remaining life expectancy at that age in a reference (standard) life table, $L^*(a)$:

$$\text{YLL} = \sum_{\text{deaths } j} L^*(a_j) = \sum_a D(a)\, L^*(a).$$

Life table choices:

- **GBD reference life table (standard expected years of life lost, SEYLL).** Since GBD 2010, IHME uses a single normative life table built from the lowest observed age-specific mortality rates across populations, the same for both sexes ([Murray et al. 2012, GBD 2010 DALYs](https://doi.org/10.1016/S0140-6736(12)61689-4)). The [GBD 2019 reference life table](https://ghdx.healthdata.org/record/ihme-data/global-burden-disease-study-2019-gbd-2019-reference-life-table) (the "theoretical minimum risk life table", TMRLT) was built from the lowest age-specific mortality rates by location and sex across all estimation years among locations with populations over 5 million, and tabulates life expectancy at ages 0 to 95+ in 5-year intervals. Its life expectancy at birth is in the high 80s; read the exact value from the table, not hard-coded (it was not verified for this note). GBD 1990 instead used model life table West Level 26, with different values for females (82.5 at birth) and males (80.0) ([Murray 1994](https://pmc.ncbi.nlm.nih.gov/articles/PMC2486718/)).
- **Local (period or cohort) life table.** Some national or program-level analyses use the country's own life table, which yields fewer YLL per death in low-life-expectancy settings. This is a value judgment (it implies a death in a poorer setting matters less) and should be reported. A model with its own background mortality can also compute YLL against its own counterfactual survival, which is closer to "life years lost" than to SEYLL; these quantities should not share a label.

**YLD.** Two formulations:

- **Prevalence-based (GBD 2010 onward):** $\text{YLD} = \sum_s DW_s \int P_s(t)\,dt$, i.e., person-time in each disabling sequela times its disability weight. This suits simulation: it is exactly a state-time integral.
- **Incidence-based (GBD 1990):** $\text{YLD} = \sum_s I_s\, DW_s\, L_s$, i.e., incident cases times disability weight times average duration $L_s$. This assigns all future disability to the year of onset. In a steady-state population with no discounting the two coincide; under changing incidence, discounting, or a finite horizon they do not.

**Disability weights.** GBD weights come from population surveys using paired comparisons, rescaled to 0–1 ([Salomon et al. 2015, GBD 2013 disability weights](https://doi.org/10.1016/S2214-109X(15)00069-8)). The [GBD 2019 disability weights](https://ghdx.healthdata.org/record/ihme-data/gbd-2019-disability-weights) cover 440 health states and are distributed as a spreadsheet on GHDx. A later release covering GBD 2021 is reported to exist; check GHDx for the current file. A library should treat weights as versioned external data (keyed by GBD round and sequela), not as constants.

**Comorbidity.** When someone is in several disabling states at once, summed weights can exceed 1. GBD combines them multiplicatively: $DW_{\text{combined}} = 1 - \prod_s (1 - DW_s)$. An agent-based model computes this per agent per timestep, which needs every disabling state an agent occupies, across disease modules.

**Historical variant: age weighting and discounting (GBD 1990).** The 1990 DALY weighted each year lived at age $x$ by $C x e^{-\beta x}$ (with $C = 0.1658$, $\beta = 0.04$) and discounted at 3%, so a death or disability spell starting at age $a$ and lasting $L$ years contributed (with modulation constant $K$, normally 1):

$$\int_a^{a+L} \left[K C x e^{-\beta x} + (1-K)\right] e^{-r(x-a)}\,dx,$$

which has the commonly quoted closed form

$$\frac{K C e^{ra}}{(r+\beta)^2}\Big[e^{-(r+\beta)(a+L)}\big(-(r+\beta)(a+L)-1\big) - e^{-(r+\beta)a}\big(-(r+\beta)a-1\big)\Big] + \frac{1-K}{r}\big(1-e^{-rL}\big).$$

Age weighting and discounting were dropped from the GBD base case starting with GBD 2010 ([Murray et al. 2012](https://doi.org/10.1016/S0140-6736(12)61689-4)). Economic evaluations that use DALYs as the effect measure (e.g., under the iDSI reference case) still discount DALYs at the evaluation's discount rate, but generally do not age-weight; WHO-CHOICE historically reported both variants. When a paper reports "DALYs (3,0)" or "(3,1)" it means discount 3%, age weighting off or on.

**DALYs averted.** $\Delta\text{DALY} = \text{DALY}_0 - \text{DALY}_k$, computed over the same horizon, population and discounting. DALYs averted by preventing a death include the full remaining standard life expectancy, much of which may lie beyond the simulation horizon; see the horizon pitfall below.

**What the model needs to output.** Deaths by age (ideally exact age at death, or at least fine age bins) and cause; person-time by age in each disabling state (and joint occupancy if comorbidity matters); event times for discounting.

**Pitfalls.**

- **Double counting in YLD after death.** Prevalence-based simulation avoids this because person-time stops at death; in incidence-based YLD, truncate the YLD of a case with duration $L_s$ who dies before $L_s$ elapses.
- **Age-bin coarseness.** Using 5-year bins for $L^*(a)$ with bin-start ages overstates YLL by up to about half a bin of life expectancy; interpolate $L^*$ at exact age.
- **Timestep dependence.** If deaths are recorded at the end of a step and age is incremented per step, YLL and person-time shift by up to one step; with monthly or yearly steps this matters for infant deaths.
- **Horizon truncation.** YLL assigns all future life lost at death, but simulated life-years gained accrue only within the horizon. Mixing the two (e.g., YLL for deaths, but YLD only within the horizon) is consistent only if stated; "simulated life-years gained" and "YLL averted" in one numerator is double counting.
- **Background-mortality competition.** An agent "saved" from a disease death may soon die of something else in the simulation; SEYLL ignores that, simulated life-years do not. Report which is used.
- **Cause attribution.** YLL by cause needs one underlying cause per death; with multiple diseases and connectors, use a documented attribution rule.

### QALYs and health-state utilities

**Definition.** A QALY is one year in full health. $\text{QALY} = \int_0^T \sum_s u_s P_s(t)\,dt$ in population form, or per individual $\int_0^{T_i} u(h_i(t))\,dt$, where $u_s$ is the health-state utility (1 = full health, 0 = dead; negative values are possible for states worse than dead). QALYs gained are $\Delta\text{QALY} = \text{QALY}_k - \text{QALY}_0$. Unlike the DALY, death enters implicitly: dead people accrue zero, so mortality effects appear only through simulated survival within the horizon (plus any terminal extrapolation), not through a reference life table.

**Utility weights.** Utilities are preference-based values for health states, typically obtained from a generic instrument with a country-specific value set (most commonly the [EQ-5D](https://euroqol.org/), in 3L or 5L versions), or by direct elicitation (time trade-off, standard gamble). Utilities are not $1 - DW$; they come from different elicitation methods and populations, so converting between them is approximate. Baseline (non-disease) utility should usually decline with age (population norms), not stay at 1.0, or QALYs gained from life extension at older ages are overstated.

**Multiple conditions.** Multiplicative ($u = \prod_s u_s$ relative to baseline), additive, or minimum methods are all used; the choice matters and should be explicit.

**What the model needs to output.** Same as YLD: person-time in each state by age (and joint occupancy), plus survival.

**Pitfalls.** Applying a utility decrement for an acute event (e.g., hospitalization) as a per-event QALY loss requires an assumed duration; store the duration with the decrement. Using utilities from one country with DW-based natural history from GBD mixes conventions.

### Life-years gained, deaths averted, cases averted

- **Life-years gained (LYG):** $\Delta \text{LY} = \int_0^T [N_k(t) - N_0(t)]\,dt$, where $N$ is the alive population (optionally discounted). Needs only population size over time, but the same cohort in both arms (whether to include births induced by the intervention is a separate decision).
- **Deaths averted:** $\sum_t [D_0(t) - D_k(t)]$ over the horizon. Over a long enough horizon all-cause deaths averted tends to zero (everyone dies eventually); it is meaningful only as "deaths within the horizon" or "cause-specific deaths". Prefer life-years or DALYs for long horizons.
- **Cases (infections) averted:** $\sum_t [I_0(t) - I_k(t)]$, where $I$ is incident events. Count events, not prevalence; one person can contribute several cases through reinfection. A transmission model includes indirect (herd) effects automatically, a key reason to use one instead of a static cohort model.
- **Cost per X averted** (e.g., per infection or death averted) is $\Delta C / \Delta X$. These intermediate-outcome ratios cannot be compared across diseases or with a threshold stated per DALY or QALY.

## Costs

### Perspectives

The perspective determines which costs and consequences count.

- **Health system / health care sector / payer:** costs borne by the health budget (government, insurer, donors, depending on definition). The [Second Panel](https://doi.org/10.1001/jama.2016.12195) "health care sector" perspective includes medical costs paid by third parties and patients out of pocket; a narrower "payer" perspective counts only one budget holder. These distinctions should be named explicitly.
- **Provider:** costs incurred by a facility or program, often used in costing studies (e.g., vaccine delivery).
- **Household / patient:** out-of-pocket (OOP) payments for care, transport, food and lodging, plus time and income losses.
- **Societal:** all costs regardless of who bears them, including productivity and non-health-sector effects. The Second Panel recommends reporting both a health care sector and a societal reference case, with an "impact inventory" listing which consequences are included ([Sanders et al. 2016](https://doi.org/10.1001/jama.2016.12195)). The iDSI reference case asks for a health system perspective with a "disaggregated societal perspective" for relevant non-health effects ([Wilkinson et al. 2016](https://doi.org/10.1016/j.jval.2016.04.015)).

**Catastrophic health expenditure (CHE).** A household incurs CHE when OOP health spending exceeds a threshold share of total household consumption or income; the SDG 3.8.2 indicator uses 10% and 25% thresholds ([WHO indicator metadata](https://www.who.int/data/gho/indicator-metadata-registry/imr-details/4844); global estimates in [Wagstaff et al. 2018](https://doi.org/10.1016/S2214-109X(17)30429-1)). Formally, household $h$ has CHE if $\text{OOP}_h / \text{consumption}_h > z$. Computing it needs per-household OOP spending and income or consumption, i.e., modeled households and an income distribution, which most disease models lack.

### Cost categories

- **Direct medical:** drugs, diagnostics, staff time, facility overhead, hospitalization, outpatient visits, vaccines and delivery.
- **Direct non-medical:** transport, food, lodging, caregiver time paid in cash.
- **Indirect / productivity:** paid and unpaid work time lost due to illness, caregiving, or premature death. Two valuation methods:
  - **Human capital method:** values all lost production at the wage rate (or a proxy) until the person would have stopped working: $C_{\text{prod}} = \sum_i \int w(a_i(t))\, \ell_i(t)\, dt$, where $\ell_i$ is the fraction of time lost. Large for deaths in working ages.
  - **Friction cost method:** production losses only last until the worker is replaced (the friction period, often a few months), so long-term absence and death contribute much less ([Koopmanschap et al. 1995](https://doi.org/10.1016/0167-6296(94)00044-5)).
- **Intangible:** pain and suffering, normally captured in the health outcome (QALY/DALY) and not costed separately.

**Pitfall: double counting productivity.** If respondents already factor income loss into utilities, adding productivity costs double counts; the Second Panel covers this in its impact inventory guidance. Likewise, do not add mortality-related productivity losses on top of a VSL-based valuation of the same deaths.

### Costing methods

- **Unit costs (bottom-up with off-the-shelf unit costs):** $C = \sum_e n_e \cdot c_e$, where $n_e$ is the count of resource-using event $e$ (visits, tests, doses, treatment-months) and $c_e$ its unit cost (e.g., from WHO-CHOICE or national tariffs). This is the default: the model counts events and person-time, and costs are multiplied in.
- **Ingredients / micro-costing:** builds $c_e$ itself from quantities of inputs (staff minutes, consumables, equipment depreciation, building space) times input prices. More precise and transparent; needed when the intervention is new.
- **Top-down (gross) costing:** divides total program expenditure by output volume to get an average cost per output; captures overheads but hides variation.
- **Annualization of capital:** capital items with useful life $n$ years and purchase cost $K$ are annualized as $K \cdot r / (1-(1+r)^{-n})$ (equivalent annual cost), not expensed in the purchase year, when the analysis wants economic rather than financial costs.

### Fixed vs variable costs, economies of scale, and cost functions

Average cost per person reached is rarely constant. Programs have fixed costs (management, training, cold chain, demand creation) that do not scale with volume, variable costs that scale roughly linearly, and marginal costs that can rise at high coverage (harder-to-reach populations) or fall (economies of scale). A general form is

$$C(n) = F + \int_0^n m(x)\,dx,$$

with $F$ fixed cost and $m(x)$ marginal cost at volume $x$. In allocative efficiency work this is often expressed inversely as a **cost-coverage curve**, coverage as a saturating function of spending, $\text{cov}(S)$, increasing and concave with an upper asymptote below 100%; Optima HIV uses such curves to map budgets to program coverage and then to outcomes ([Kerr et al. 2015](https://doi.org/10.1097/QAI.0000000000000605)). A **cost-outcome curve** further maps coverage to the model parameter changed by the program.

**Pitfall.** Using a constant unit cost from a small pilot to cost national scale-up, or using an average cost where a marginal cost is the correct concept (incremental analyses need marginal costs).

### Currency year, inflation, PPP and exchange rates

Express all costs in one currency and one price year. Inflation adjustment uses a price index (GDP deflator or CPI, preferably a health-specific index if available): $c_{\text{target}} = c_{\text{orig}} \cdot \frac{I_{\text{target}}}{I_{\text{orig}}}$. Conversion between currencies uses market exchange rates or purchasing power parity (PPP) conversion factors (international dollars). The order of operations matters: inflate in local currency then convert at the target-year rate, versus convert first then inflate in USD, versus splitting tradable and non-tradable inputs; [Turner et al. 2019](https://doi.org/10.1016/j.jval.2019.03.021) show these give materially different answers and recommend transparent reporting. A library should store each unit cost with its currency, price year and source, and convert at analysis time, not store converted numbers.

## Discounting

**Definition.** Discounting converts costs and health effects occurring at different times to present values. With annual rate $r$ and time $t$ in years from the base year:

$$\text{PV} = \sum_t \frac{X_t}{(1+r)^t} \quad \text{(discrete)}, \qquad \text{PV} = \int_0^T X(t)\, e^{-\rho t}\,dt,\ \rho=\ln(1+r) \quad \text{(continuous)}.$$

Note $\rho = \ln(1+r)$, not $\rho = r$; using $e^{-rt}$ with the discrete rate understates discounting slightly (about 0.04 percentage points at 3%).

**Discounting within a timestep.** A flow $X$ accrued uniformly over $[t, t+\Delta]$ has present value

$$X \cdot \frac{1}{\Delta}\int_t^{t+\Delta} e^{-\rho s}\,ds = X\, e^{-\rho t}\, \frac{1 - e^{-\rho \Delta}}{\rho \Delta}.$$

For annual steps at 3% the bracketed factor is about 0.985, so discounting all of a year's flow at the start of the year (factor 1) versus the end (factor $1/(1+r)$) changes results by roughly 1.5% per year of flow. Point events (deaths, doses) should be discounted at their own time stamp, not the start of their step.

**Discounted YLL.** For a death at time $t_d$ with remaining standard life expectancy $L$, continuous discounting of the lost years gives

$$\text{YLL}_{\text{disc}} = e^{-\rho t_d}\, \frac{1 - e^{-\rho L}}{\rho}.$$

The factor $e^{-\rho t_d}$ (discounting back to the base year) is frequently forgotten; the second factor is what GBD 1990 applied.

**Typical rates.**

- **iDSI reference case:** 3% per year for costs and effects, with sensitivity analysis at a rate reflecting government borrowing and lower rates for long horizons ([Wilkinson et al. 2016](https://doi.org/10.1016/j.jval.2016.04.015)).
- **WHO-CHOICE** ([Tan-Torres Edejer et al. 2003](https://iris.who.int/handle/10665/42699)) and the [WHO immunization guide (2019)](https://www.who.int/publications/i/item/who-guide-for-standardization-of-economic-evaluations-of-immunization-programmes-2nd-ed): 3% for costs and outcomes in the base case, with sensitivity analyses (the guide's exact sensitivity recommendations were not re-verified for this note).
- **Second Panel (US):** 3% for costs and health effects ([Sanders et al. 2016](https://doi.org/10.1001/jama.2016.12195)).
- **NICE (England):** 3.5% for costs and health effects, with 1.5% for both permitted in specific circumstances where long-term health benefits are likely (e.g., potentially curative treatments) under the [NICE health technology evaluations manual (PMG36)](https://www.nice.org.uk/process/pmg36). A 2026 methods update left the discount rate unchanged.

**Differential discounting** (lower rate for health than for costs, e.g., older Dutch and Belgian guidance) is a recurring debate; with a lower health rate, delaying any program indefinitely can look attractive (the Keeler–Cretin paradox). A library should allow separate rates for costs and for each health outcome, and for time-varying rates, without making either the default.

**Half-cycle (within-cycle) correction.** In discrete-time cohort (Markov) models, state membership is known only at cycle boundaries; counting at the start or end of each cycle over- or underestimates person-time. The classic correction is the trapezoidal rule; [Elbasha and Chhatwal 2016](https://doi.org/10.1177/0272989X15585121) compare it with other integration rules (Simpson's rule, life-table method) and show all improve with shorter cycles. In an agent-based model with event times, the analog is integrating person-time from actual entry and exit times within a step, not assuming membership for the whole step. **Pitfall:** applying a half-cycle correction to costs of point events (e.g., a one-time vaccination cost) is wrong; it applies to state-occupancy rewards only.

## Decision metrics

### ICER, dominance, and the efficiency frontier

**ICER.** The incremental cost-effectiveness ratio is the extra cost per extra unit of health. For strategy $k$ against the next-best non-dominated strategy $j$:

$$\text{ICER}_{k} = \frac{C_k - C_j}{E_k - E_j}.$$

With DALYs this is cost per DALY averted; with QALYs, cost per QALY gained.

**Algorithm for multiple mutually exclusive strategies.** (1) Sort by effect (or cost). (2) Remove strongly dominated strategies (higher cost and lower or equal effect than another). (3) Compute ICERs between successive remaining strategies. (4) Remove extendedly dominated strategies: any strategy whose ICER is higher than that of the next more effective strategy (it is dominated by a mix of its neighbors). (5) Repeat (3)–(4) until ICERs increase monotonically. The remaining strategies form the **efficiency frontier**; the optimal strategy at threshold $\lambda$ is the most effective frontier strategy with ICER $\le \lambda$.

**Pitfalls.** Negative ICERs cannot be read without the quadrant (cost saving and more effective is dominance, not "negative ICER"). Do not average ICERs across stochastic replicates; compute mean $\Delta C$ over mean $\Delta E$, or use net benefit. Comparing every strategy to "do nothing" (average cost-effectiveness ratios), not the next-best alternative, is a common error, though for sector-wide priority setting WHO-CHOICE's generalized CEA deliberately compares against a null scenario.

### Net monetary benefit and net health benefit

$$\text{NMB}_k = \lambda E_k - C_k, \qquad \text{NHB}_k = E_k - \frac{C_k}{\lambda}.$$

These restate health and cost on one scale, money (NMB) or health (NHB). The optimal strategy maximizes NMB (equivalently NHB) at the chosen $\lambda$. Net benefit is linear, so it averages correctly across replicates and PSA draws and handles any number of strategies without frontier logic ([Stinnett and Mullahy 1998](https://doi.org/10.1177/0272989X98018002S09), Med Decis Making 18(2 Suppl):S68–S80). NHB is the natural unit when $\lambda$ represents health opportunity cost: it is the net health gain after accounting for health forgone elsewhere in the system.

### Cost-effectiveness thresholds

- **GDP-per-capita rules.** The 2001 WHO Commission on Macroeconomics and Health suggested interventions under 1× GDP per capita per DALY averted are "very cost-effective" and under 3× "cost-effective"; WHO-CHOICE popularized these. They have been widely criticized as too permissive, not country specific, and disconnected from budget constraints ([Marseille et al. 2015](https://pmc.ncbi.nlm.nih.gov/articles/PMC4339959/); [Bertram et al. 2016](https://doi.org/10.2471/BLT.15.164418), the latter by WHO staff, recommending against using them on their own).
- **Opportunity-cost (supply-side) thresholds.** The threshold should reflect the health forgone when budget is displaced. [Claxton et al. 2015](https://pubmed.ncbi.nlm.nih.gov/25692211/) estimated about £12,936 per QALY for the English NHS. [Woods et al. 2016](https://doi.org/10.1016/j.jval.2016.02.017) extrapolated to other countries, finding thresholds well below 1× GDP per capita in many low-income settings; [Ochalek, Lomas and Claxton 2018](https://doi.org/10.1136/bmjgh-2018-000964) estimated cost per DALY averted from cross-country health spending elasticities, again generally below the 1–3× GDP range.
- **NICE.** The standard range was £20,000–£30,000 per QALY for about two decades; it rose to £25,000–£35,000 per QALY from April 2026 for technology appraisals ([OHE commentary](https://www.ohe.org/insights/nices-new-cost-effectiveness-threshold-significance-consequences-and-unanswered-questions/)). Severity modifiers (since 2022) weight QALYs for severe conditions.
- **Implementation note.** $\lambda$ should be a parameter swept over a range (for CEACs and NMB), never baked into a model.

### Benefit-cost analysis, ROI and VSL

In benefit-cost analysis (BCA), health gains are monetized. With present values $B$ (benefits) and $C$ (costs):

$$\text{BCR} = \frac{B}{C}, \qquad \text{NB} = B - C, \qquad \text{ROI} = \frac{B - C}{C}.$$

Benefits typically include averted treatment costs, productivity gains, and monetized mortality and morbidity. Mortality risk reductions are valued with the **value of a statistical life (VSL)**, the aggregate willingness to pay for small risk reductions summing to one expected death, or with a value per statistical life-year (VSLY). For LMICs, VSL is usually transferred from high-income estimates using an income elasticity, $\text{VSL}_c = \text{VSL}_{\text{US}}(Y_c/Y_{\text{US}})^{\eta}$, with standardized sensitivity analysis over $\eta$ ([Robinson, Hammitt and O'Keeffe 2019](https://doi.org/10.1017/bca.2018.26)). ROI is sometimes reported from a narrow fiscal perspective (only averted treatment costs as benefits), which is a different quantity from societal ROI; label which.

**Pitfall.** Adding VSL-based mortality benefits and human-capital productivity losses for the same deaths double counts.

### Budget impact analysis

Budget impact analysis (BIA) estimates the financial consequence of adopting an intervention for a specific budget holder over a short horizon (typically 1–5 years), as annual undiscounted costs: $\text{BI}(t) = C_{\text{new mix}}(t) - C_{\text{current mix}}(t)$, reported per year. It requires uptake and displacement assumptions and is presented as scenarios ([Sullivan et al. 2014, ISPOR BIA II](https://doi.org/10.1016/j.jval.2013.08.2291)). BIA complements CEA: a cost-effective intervention may be unaffordable. BIA needs the same cost outputs as CEA, but as an undiscounted annual time series for the paying perspective only, typically including the dynamics of who enters treatment over time.

## Uncertainty and value of information

### Deterministic sensitivity analysis

One-way analysis varies one parameter across its plausible range with others at base case and records the outcome (ICER or NMB); a **tornado diagram** sorts parameters by the width of the resulting outcome range. Multi-way and threshold analyses (find the parameter value at which the decision changes) are extensions. For stochastic models, each point needs enough replicates (or common random numbers) that Monte Carlo noise is small relative to the parameter effect.

### Probabilistic sensitivity analysis (PSA)

Draw $\theta^{(m)} \sim p(\theta)$, $m = 1..M$, run all strategies at each draw (with the same draw across strategies), and record $C_k^{(m)}, E_k^{(m)}$. Outputs: the cost-effectiveness plane scatter, mean incremental costs and effects, and distributions of NMB. In a stochastic ABM, PSA conflates parameter uncertainty with stochastic (first-order) noise unless replicates per draw are used or noise is otherwise controlled; the decision-relevant quantity is the expectation over stochasticity at each $\theta$.

**CEAC and CEAF.** The cost-effectiveness acceptability curve gives, for each $\lambda$, the probability each strategy has the highest NMB:

$$\text{CEAC}_k(\lambda) = \frac{1}{M}\sum_m \mathbb{1}\!\left[k = \arg\max_j \text{NMB}_j^{(m)}(\lambda)\right].$$

The cost-effectiveness acceptability frontier (CEAF) shows, at each $\lambda$, only the strategy with highest *expected* NMB and its probability of being optimal, which can differ from the strategy with highest CEAC ([Fenwick, Claxton and Sculpher 2001](https://doi.org/10.1002/hec.635)).

### Value of information

With net benefit $\text{NB}_k(\theta)$ in health or money units:

$$\text{EVPI} = \mathbb{E}_\theta\!\left[\max_k \text{NB}_k(\theta)\right] - \max_k \mathbb{E}_\theta\!\left[\text{NB}_k(\theta)\right].$$

**EVPPI** for a parameter subset $\phi$ (with the rest $\psi$):

$$\text{EVPPI}_\phi = \mathbb{E}_\phi\!\left[\max_k \mathbb{E}_{\psi|\phi}\,\text{NB}_k(\phi,\psi)\right] - \max_k \mathbb{E}_\theta\!\left[\text{NB}_k(\theta)\right].$$

**EVSI** replaces perfect knowledge of $\phi$ with data $X$ from a proposed study: $\text{EVSI} = \mathbb{E}_X[\max_k \mathbb{E}_{\theta|X}\text{NB}_k] - \max_k \mathbb{E}_\theta \text{NB}_k$. Population VOI multiplies per-person values by the discounted number of people affected by the decision over its lifetime. The nested expectation in EVPPI is expensive for simulation models; regression-based estimators that reuse a single PSA sample avoid the inner loop ([Strong, Oakley and Brennan 2014](https://doi.org/10.1177/0272989X13505910)). These estimators work directly from a table of $(\theta^{(m)}, \text{NB}_k^{(m)})$, which is what a library should make easy to export.

## Equity

### Distributional cost-effectiveness analysis (DCEA)

DCEA models how health gains and opportunity costs are distributed across equity-relevant subgroups (e.g., socioeconomic quintile, region, sex) and evaluates the resulting health distribution against both total health and inequality ([Asaria, Griffin and Cookson 2016](https://doi.org/10.1177/0272989X15583266)). Steps: (1) baseline distribution of health (e.g., quality-adjusted life expectancy) by group; (2) modeled change in health by group, including the distribution of health opportunity costs from displaced spending, $\Delta h_g = \Delta E_g - \Delta C \cdot w_g / \lambda$ where $w_g$ is group $g$'s share of displaced health; (3) apply a social welfare function. A common choice is the Atkinson equally distributed equivalent:

$$h_{\text{EDE}} = \left(\frac{1}{N}\sum_i h_i^{1-\epsilon}\right)^{\frac{1}{1-\epsilon}}, \quad \epsilon \ne 1,$$

with inequality aversion $\epsilon \ge 0$ ($\epsilon = 0$ is plain mean health); the Kolm index is an absolute-inequality alternative. Results are often shown on an equity-efficiency impact plane.

**What the model needs to output.** All health outcomes and costs by the equity-relevant attribute, so agents need that attribute and results need stratifying by it. Lifetime health measures (quality-adjusted life expectancy) per group are needed for step (1).

### Extended cost-effectiveness analysis (ECEA)

ECEA, developed for the Disease Control Priorities project, reports for a policy (often public finance of an intervention) health gains, private OOP expenditure averted, and financial risk protection, each broken down by income quintile ([Verguet, Kim and Jamison 2016](https://doi.org/10.1007/s40273-016-0414-z)). Financial risk protection metrics include cases of catastrophic health expenditure averted, cases of poverty averted (households pushed below a poverty line by OOP spending), and the money-metric value of insurance: under a utility function (often constant relative risk aversion) over income, the risk premium a household would pay to avoid the OOP spending risk, $\pi = \mathbb{E}[y] - y_{\text{CE}}$ where $u(y_{\text{CE}}) = \mathbb{E}[u(y)]$. ECEA requires per-agent (or per-household) income, OOP cost per event, and care-seeking probabilities that may depend on income.

## Allocative efficiency and optimization

Allocative efficiency analysis asks a different question from CEA: not "is intervention $k$ worth adopting?" but "how should a fixed budget $B$ be split across programs to maximize health (or minimize infections, deaths, or DALYs)?":

$$\max_{\mathbf{S}} \; E\big(\text{cov}_1(S_1), \dots, \text{cov}_n(S_n)\big) \quad \text{s.t.} \quad \sum_p S_p \le B, \; S_p \ge S_p^{\min}.$$

Here $\text{cov}_p(S_p)$ is a cost-coverage curve per program and $E$ is evaluated by running the epidemic model, so the objective is nonlinear, includes interactions between programs and indirect effects, and is typically optimized with derivative-free methods. Optima HIV is an example used in many countries ([Kerr et al. 2015](https://doi.org/10.1097/QAI.0000000000000605)). The inverse problem (minimum budget to reach a target) and sweeping $B$ to trace a health-budget curve are common variants. Compared with league tables of ICERs, optimization handles non-constant marginal costs, program interdependence and saturation, but its answers depend heavily on the cost-coverage curves and on the objective weights. A library therefore needs cheap re-runs over a vector of program budgets, with user-supplied curves linking costs and coverage.

## Reference cases and reporting standards

- **iDSI reference case** (Gates-commissioned): 11 principles for economic evaluation in LMICs; DALYs averted or QALYs gained, 3% discounting of costs and effects, health system perspective plus disaggregated societal effects, and thresholds that reflect health opportunity cost ([Wilkinson et al. 2016](https://doi.org/10.1016/j.jval.2016.04.015)). Described by its authors as "an aid to thought, not a substitute for it".
- **WHO-CHOICE / generalized CEA:** compares interventions against a counterfactual of no intervention ("null scenario") to allow sector-wide comparisons; uses DALYs and international dollars ([Tan-Torres Edejer et al. 2003, *Making choices in health*](https://iris.who.int/handle/10665/42699)).
- **WHO guide for economic evaluation of immunization programs** (2nd ed., 2019, WHO-IVB-19.10): what to include in vaccine evaluations, including herd effects (hence transmission models), delivery costs, and discounting ([WHO](https://www.who.int/publications/i/item/who-guide-for-standardization-of-economic-evaluations-of-immunization-programmes-2nd-ed)).
- **Second Panel on Cost-Effectiveness in Health and Medicine (US):** two reference cases (health care sector and societal), impact inventory, 3% discounting, QALYs ([Sanders et al. 2016](https://doi.org/10.1001/jama.2016.12195)).
- **NICE reference case (England):** NHS and personal social services perspective, QALYs from EQ-5D, 3.5% discounting, threshold range now £25,000–£35,000 per QALY ([PMG36](https://www.nice.org.uk/process/pmg36)).
- **CHEERS 2022:** a 28-item reporting checklist for health economic evaluations, applicable to any health intervention ([Husereau et al. 2022](https://doi.org/10.1136/bmj-2021-067975)). Items relevant to model software include currency and price year, discount rates, perspective, time horizon, model structure and uncertainty; a library can export these automatically from the analysis settings.
- **GBD methods:** prevalence-based YLD with GBD disability weights, YLL against the GBD reference life table, no age weighting or discounting ([Murray et al. 2012](https://doi.org/10.1016/S0140-6736(12)61689-4); weights and life tables on [GHDx](https://ghdx.healthdata.org/)).
- **ISPOR good practice for BIA** ([Sullivan et al. 2014](https://doi.org/10.1016/j.jval.2013.08.2291)).

A library should not build in a single reference case (a body's standard method); it should make the reference case a named, swappable, reported set of settings (rates, perspective, outcome measure, weights version, life table, currency year).

## What a disease model needs to provide

Nearly every metric above comes from a few basic outputs combined with outside tables. A library should support at least:

1. **Person-time.** For each health state (or sequela), person-time per step, by age, sex, and any user-defined group (equity attribute, region). Feeds YLD, QALYs, life-years, and state-based costs (e.g., treatment-months). Where possible, use actual entry and exit times within a step, which removes the need for half-cycle correction, and allow people to be in states of several modules at once, for comorbidity-adjusted weights.
2. **Event counts with time stamps.** Counts of incident events (infections, diagnoses, tests, doses, visits, hospitalizations, treatment initiations, deaths) per step, ideally with event times finer than the step for discounting. Feeds cases averted, unit-cost costing, BIA and incidence-based YLD.
3. **Deaths with exact age and cause.** For each death: time, exact age, sex, and a single underlying cause (with a documented attribution rule when multiple diseases are present). Feeds YLL against any life table, deaths averted, and productivity losses. Aggregating to 5-year age bins too early loses YLL accuracy.
4. **Attribution for each agent.** In agent-based models, linking costs and health events to (a) the intervention that caused the resource use, (b) the disease module, and (c) the agent's attributes (age, income group, household). This allows costing by perspective, DCEA and ECEA, and cost-coverage accounting by program. A running record for each agent (cost, utility-time, DW-time) is a general way to do this.
5. **Times relative to a discounting base year.** Each quantity needs the time it occurs, so that any discount rate (or several, separately for costs and each outcome) can be applied after the run. Storing only discounted totals means re-running the model to change the rate.
6. **Undiscounted time series.** BIA needs undiscounted annual costs and CEA needs discounted totals. Undiscounted flows per step, with times, support both.
7. **Paired counterfactual runs.** "Averted" quantities need the comparator and intervention run with common random numbers and the same population, and differenced per replicate. The library should make scenario pairs easy.
8. **A record of parameter draws.** For PSA and VOI, the sampled $\theta^{(m)}$ stored with each run's outputs, and the same draw applied to all strategies.
9. **Outside tables as versioned inputs.** Disability weights (with GBD round), utilities (with instrument and value set), reference life tables, unit costs (with currency, price year, source), price indices, exchange rates or PPP factors, and VSL inputs. These should not be hard-coded in disease modules.
10. **Running from budgets.** For allocative efficiency, a fast way to run the model for a vector of program budgets, through user-supplied cost-coverage curves.
11. **The horizon.** An analysis horizon separate from the end of the simulation, and an option to extrapolate (e.g., remaining discounted life expectancy for those alive at the horizon), so that life-years and QALYs are not cut off arbitrarily.

With these outputs, DALYs, QALYs, costs by perspective, ICERs, net benefit, CEACs, VOI, DCEA, ECEA, and BIA can all be computed by general functions that know nothing about a specific disease, which is the separation a lingua franca should aim for.
