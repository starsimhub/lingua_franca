---
authorship:
  human: 0
  ai: 100
  note: Written by AI
---

# Health-economic modeling software

Disease models usually add costing at the end, but a separate family of tools exists to attach costs and utilities (quality-of-life scores from 0 to 1) to a model of disease progression. They turn the result into incremental cost-effectiveness ratios (ICERs, extra cost per extra unit of health), acceptability curves (the chance each option is best at a given willingness to pay), and value-of-information (VOI) estimates (what reducing uncertainty is worth). These cost-effectiveness analysis (CEA) tools (mostly R packages, plus a few GUIs and the Excel workbook tradition) have the most developed interfaces anywhere for saying "this state costs X per cycle", "this transition costs Y once", "discount costs at 3.5% and effects at 1.5%" (discounting counts the future for less than the present), and "draw this cost from a gamma distribution in the probabilistic sensitivity analysis (PSA)". Their disease engines are simple (cohort Markov chains, decision trees, sometimes individual-level multistate models), so what is worth borrowing is the economic layer: how it is declared, where it attaches, and what comes out. This page reviews eight exemplars and compares their interfaces. For definitions of QALYs, DALYs, ICERs, net monetary benefit (NMB), and EVPI, see [metrics.md](metrics.md).

Snippets are verbatim from the packages' vignettes, examples, or source, with links.

## heemod

| Language | Model types | Code | Docs | Key paper |
|---|---|---|---|---|
| R | Cohort Markov (homogeneous and time-inhomogeneous), partitioned survival | [pierucci/heemod](https://github.com/pierucci/heemod) | [CRAN vignettes](https://cran.r-project.org/package=heemod) | Filipović-Pierucci, Zarca, Durand-Zaleski (2017), [Markov Models for Health Economic Evaluations: The R Package heemod](https://arxiv.org/abs/1702.03252) |

heemod is the clearest example of "values attached to states". A model is a transition matrix plus states, each with a named list of values, and the user tells `run_model()` which value is the cost and which the effect.

**How costs and utilities are declared.** Every state gets arbitrary named values; cost and utility are two of them. From the [introduction vignette](https://github.com/pierucci/heemod/blob/master/vignettes/a_introduction.Rmd):

```r
state_A <- define_state(
  cost = 1234,
  utility = 0.85
)
```

```r
strat <- define_strategy(
  transition = mat_trans,
  state_A,
  state_B
)
```

```r
res_mod <- run_model(
  strat,
  cycles = 10,
  cost = cost,
  effect = utility
)
```

Values can be expressions of other values and parameters, so cost components combine easily, and `dispatch_strategy()` lets one state vary by strategy. From the [homogeneous model vignette](https://github.com/pierucci/heemod/blob/master/vignettes/c_homogeneous.Rmd):

```r
state_A <- define_state(
    cost_health = discount(2756, .06),
    cost_drugs = discount(dispatch_strategy(
      mono = cost_zido,
      comb = cost_zido + cost_lami
    ), .06),
    cost_total = cost_health + cost_drugs,
    life_year = 1
  )
```

One-off costs at the start of a strategy (for example, surgery) are declared with `define_starting_values()` on the strategy, from the [non-homogeneous vignette](https://github.com/pierucci/heemod/blob/master/vignettes/d_non_homogeneous.Rmd):

```r
  starting_values = define_starting_values(
    cost = 394
  )
```

There is no built-in transition cost. The introduction vignette says that "Transition costs between states can be defined by adding an additional state called a transition state. This is a special case of a tunnel state." (A tunnel state is a temporary state agents pass through in a fixed time.) Time-varying values use the built-in `model_time` (alias `markov_cycle`) and `state_time` variables, the latter by expanding states into tunnels ([time dependency vignette](https://github.com/pierucci/heemod/blob/master/vignettes/b_time_dependency.Rmd)).

**Discounting and timing conventions.** Discounting happens inside the value expression with `discount(x, r, first = FALSE, period = 1)` ([source](https://github.com/pierucci/heemod/blob/master/R/utils.R)), so each value can have its own rate. `run_model()` sets cycle timing by `method = c("life-table", "beginning", "end")`; the docstring explains that "beginning" overestimates costs, "end" underestimates them, and "life-table" (the default) is the trapezoidal/half-cycle-style correction, which averages across each cycle ([source](https://github.com/pierucci/heemod/blob/master/R/run_model_define.R)). The [reproduction vignette](https://github.com/pierucci/heemod/blob/master/vignettes/i_reproduction.Rmd) notes that with `method = "end"`, costs "should be discounted from the first cycle with the argument first = TRUE in discount()", so the two settings interact.

**Strategies and comparison.** Strategies are named arguments to `run_model(mono = strat_mono, comb = strat_comb, ...)`. `summary(res_mod, threshold = ...)` reports costs, effects, NMB at the given thresholds, and ICERs relative to the previous strategy on the efficiency frontier (the strategies that give the most health for their cost), computed in [`efficiency_frontier.R`](https://github.com/pierucci/heemod/blob/master/R/efficiency_frontier.R).

**Uncertainty.** PSA distributions are declared separately from the model, as formulas on parameter names. From the [probabilistic vignette](https://github.com/pierucci/heemod/blob/master/vignettes/e_probabilistic.Rmd):

```r
rsp <- define_psa(
  rr ~ lognormal(mean = .509, sdlog = .173),
  cost_A ~ gamma(mean = 2756, sd = sqrt(2756)),
  cost_B ~ gamma(mean = 3052, sd = sqrt(3052)),
  cost_C ~ gamma(mean = 9007, sd = sqrt(9007)),
  p_CD_mono ~ binomial(prob = .25, size = 40),
  p_AA_mono + p_AB_mono + p_AC_mono + p_AD_mono ~ multinomial(721, 202, 67, 10)
)
```

```r
pm <- run_psa(
  model = res_mod,
  psa = rsp,
  N = 100
)
```

Then `plot(pm, type = "ac", ...)` gives the acceptability curve (CEAC) and `plot(pm, type = "evpi", ...)` the EVPI curve (expected value of perfect information). `define_correlation()` declares correlation between parameters ([source](https://github.com/pierucci/heemod/blob/master/R/resamp_define.R)). Deterministic sensitivity analysis uses `define_dsa(rr, .4, .6, cost_zido, 1500, 3000, ...)` and `run_dsa()` ([sensitivity vignette](https://github.com/pierucci/heemod/blob/master/vignettes/f_sensitivity.Rmd)). A model can also come entirely from CSV/XLSX files: a states file has `.model`, `.state`, value columns, and `.discount.<value>` columns ([tabular vignette](https://github.com/pierucci/heemod/blob/master/vignettes/h_tabular.Rmd), [example file](https://github.com/pierucci/heemod/blob/master/inst/tabular/thr/THR_states.csv)).

**Strengths and limitations.**

- The cleanest declarative interface of the group: state values are named expressions, cost and effect are chosen at run time, and PSA is a separate object over parameter names.
- Arbitrary named values per state extend to any accumulated outcome (life-years, events, DALYs).
- Cohort-only, discrete-time; transition costs need a tunnel-state workaround, which adds states.
- Discounting sits inside each value expression, so it is easy to discount one cost and forget another.

## hesim

| Language | Model types | Code | Docs | Key paper |
|---|---|---|---|---|
| R (C++ backend) | Cohort discrete-time state transition (cDTSTM), N-state partitioned survival, individual continuous-time state transition (iCTSTM) | [hesim-dev/hesim](https://github.com/hesim-dev/hesim) | [hesim-dev.github.io/hesim](https://hesim-dev.github.io/hesim/) | Incerti and Jansen (2021), [hesim: Health Economic Simulation Modeling and Decision Analysis](https://arxiv.org/abs/2102.09437) |

hesim explicitly separates the disease engine from the economic layer. An economic model is an R6 object with three parts: a transition model, a utility model, and a named list of cost models, one per category. The transition model can be swapped (cohort, partitioned survival, or individual-level) while the cost and utility models stay the same.

**How costs and utilities are declared.** The simplest route is a `stateval_tbl()` (state value table) per category, giving a value by state (and optionally by strategy, patient, or time interval) plus a PSA distribution. From the [multistate vignette](https://github.com/hesim-dev/hesim/blob/master/vignettes/mstate.Rmd):

```r
utility_tbl <- stateval_tbl(data.table(state_id = states$state_id,
                                       mean = mstate3_exdata$utility$mean,
                                       se = mstate3_exdata$utility$se),
                            dist = "beta")
```

```r
drugcost_tbl <- stateval_tbl(data.table(strategy_id = strategies$strategy_id,
                                       est = mstate3_exdata$costs$drugs$costs),
                            dist = "fixed")
```

```r
utilitymod <- create_StateVals(utility_tbl, n = n_samples, hesim_data = hesim_dat)
```

```r
costmods <- list(Drug = drugcostmod,
                 Medical = medcostmod)
```

```r
econmod_cr <- IndivCtstm$new(trans_model = transmod_cr,
                             utility_model = utilitymod,
                             cost_models = costmods)
```

Alternatively, `define_tparams()` returns transition matrix, utility, and costs together as array expressions of parameters, input data, and a built-in `time` variable. From the [Markov cohort vignette](https://github.com/hesim-dev/hesim/blob/master/vignettes/markov-cohort.Rmd):

```r
    utility = u,
    costs = list(
        drug = ifelse(strategy_name == "Monotherapy" | time > 2,
                      c_zido, c_zido + c_lam),
        community_medical = c_cmed,
        direct_medical = c_dmed
    )
```

How a state value accrues is set on the cost model, not the state: `StateVals$new(method = c("wlos", "starting"), time_reset = FALSE)`. The [source docs](https://github.com/hesim-dev/hesim/blob/master/R/statevals.R) say: "If `wlos`, then costs and QALYs are simulated by weighting state values by the length of stay in a health state. If `starting`, then state values represent a one-time value that occurs when a patient enters a health state." In individual-level models `starting` values "accrue each time a patient enters a new state and are discounted based on time of entrance into that state", in effect an entry cost. The [inhomogeneous cohort vignette](https://github.com/hesim-dev/hesim/blob/master/vignettes/markov-inhomogeneous-cohort.Rmd) mixes the two:

```r
cost_args <- list(
  prosthesis = list(method = "starting"),
  medical = list(method = "wlos")
)
```

**Discounting and timing conventions.** Discounting happens at simulation time, not in the declaration: `econmod$sim_qalys(dr = .03)` and `econmod$sim_costs(dr = .03)`, and `dr` can be a vector (`dr = c(0,.03)`) for several rates in one pass. Half-cycle-type correction is the `integrate_method = c("trapz", "riemann_left", "riemann_right")` argument of `sim_qalys()`/`sim_costs()` ([source](https://github.com/hesim-dev/hesim/blob/master/R/dtstm.R)), since hesim treats accumulation as numerical integration of state values over occupancy. The individual-level model integrates in continuous time, so it needs no cycle correction.

**Strategies and comparison.** Strategies are rows of the input data (`hesim_data(strategies = ..., patients = ...)`), not separate model objects, so every component runs across strategy, patient, and PSA sample. After simulation:

```r
ce_sim <- econmod_cr$summarize()
format(summary(ce_sim, labels = labs))
cea_out <- cea(ce_sim, dr_qalys = .03, dr_costs = .03)
cea_pw_out <- cea_pw(ce_sim, comparator = 1, dr_qalys = .03, dr_costs = .03)
```

`cea()` treats all strategies at once (probability most cost-effective, CEAF, EVPI); `cea_pw()` compares each to a comparator, the option it is measured against (incremental costs and QALYs, CEAC, INMB), and `icer(cea_pw_out, k = 50000)` gives a tidy ICER table ([CEA vignette](https://github.com/hesim-dev/hesim/blob/master/vignettes/cea.Rmd)). The `ce` object is a long table of costs and QALYs by sample, strategy, group, category, and discount rate.

**Uncertainty.** PSA is built in: `create_StateVals(..., n = n_samples)` samples from the `dist` given in the table, and `define_rng()` declares random-number generation for arbitrary parameters ([Markov cohort vignette](https://github.com/hesim-dev/hesim/blob/master/vignettes/markov-cohort.Rmd)):

```r
rng_def <- define_rng({
  lrr_se <- (lrr_upper - lrr_lower)/(2 * qnorm(.975)) # Local object 
                                                      # not returned
  list( # Parameters to return
    p_mono = dirichlet_rng(alpha_mono),
    rr_comb = lognormal_rng(lrr_mean, lrr_se),
    c_zido = c_zido,
    c_lam = c_lam,
    c_dmed = gamma_rng(mean = c_dmed_mean, sd = c_dmed_mean),
    c_cmed = gamma_rng(mean = c_cmed_mean, sd = c_cmed_mean),
    u = u
  )
}, n = 1000)
```

Plots: `plot_ceplane()`, `plot_ceac()`, `plot_ceaf()`, `plot_evpi()`.

**Strengths and limitations.**

- The best model of a separate, swappable economic layer: the same cost and utility models plug into cohort, partitioned survival, and individual-level transition models.
- Cost categories are a named list, and the output keeps them separate, as budget-impact and perspective (whose costs count) analyses need.
- `wlos` versus `starting` cleanly separates per-time from per-entry costs; there is no general per-transition (from-to pair) cost, though in individual models `starting` on the destination state covers most uses.
- Everything runs across PSA samples by design, which is fast but makes the data-table setup (`hesim_data`, `expand()`, ID columns) heavy for small models.

## dampack and the DARTH tutorials

| Language | Model types | Code | Docs | Key paper |
|---|---|---|---|---|
| R | Model-agnostic analysis layer; tutorials cover cohort Markov and microsimulation | [DARTH-git/dampack](https://github.com/DARTH-git/dampack), [cohort tutorial](https://github.com/DARTH-git/cohort-modeling-tutorial-intro), [microsimulation tutorial](https://github.com/DARTH-git/Microsimulation-tutorial) | [dampack vignettes](https://github.com/DARTH-git/dampack/tree/master/vignettes) | Alarid-Escudero et al. (2023), [An Introductory Tutorial on Cohort State-Transition Models in R](https://doi.org/10.1177/0272989X221103163); Krijkamp et al. (2018), [Microsimulation modeling for health decision sciences using R](https://doi.org/10.1177/0272989X18754513) |

The Decision Analysis in R for Technologies in Health (DARTH) group takes the opposite approach to heemod: the model is plain R code the user writes to a published convention, and `dampack` handles only what comes after (ICERs, PSA objects, VOI). This is the closest analog to adding costing to a general simulation engine.

**How costs and utilities are declared.** As named vectors by state, one per strategy, multiplied by the cohort trace (state occupancy per cycle). From the [cohort tutorial](https://github.com/DARTH-git/cohort-modeling-tutorial-intro/blob/main/analysis/cSTM_time_indep.R):

```r
#* Vector of state costs under strategy A
v_c_strA   <- c(H  = c_H, 
                S1 = c_S1 + c_trtA,
                S2 = c_S2 + c_trtA, 
                D  = c_D)
```

```r
  v_qaly_str <- l_m_M[[i]] %*% v_u_str # sum the utilities of all states for each cycle
  v_cost_str <- l_m_M[[i]] %*% v_c_str # sum the costs of all states for each cycle
```

In the microsimulation tutorial, costs are a function of each individual's current state, evaluated every cycle ([Appendix A](https://github.com/DARTH-git/Microsimulation-tutorial/blob/master/Appendix%20A_online_supp.R)):

```r
Costs <- function (M_it, Trt = FALSE) {
  # M_it: health state occupied by individual i at cycle t (character variable)
  # Trt:  is the individual being treated? (default is FALSE) 
  
  c.it <- 0                                  # by default the cost for everyone is zero 
  c.it[M_it == "H"]  <- c.H                  # update the cost if healthy
  c.it[M_it == "S1"] <- c.S1 + c.Trt * Trt   # update the cost if sick conditional on treatment
  c.it[M_it == "S2"] <- c.S2 + c.Trt * Trt   # update the cost if sicker conditional on treatment
  return(c.it)        		                   # return the costs
}
```

The companion time-dependent tutorial ([arXiv:2108.13552](https://arxiv.org/abs/2108.13552)) adds transition rewards (a reward is any value accrued, such as cost or QALYs) by tracking a three-dimensional transition array (from, to, cycle), the general way to support per-transition costs in a cohort model.

**Discounting and timing conventions.** Discount weights are vectors multiplied element by element with per-cycle totals, with separate rates for costs and effects; a within-cycle correction (WCC) vector works the same way (cohort tutorial):

```r
v_dwc  <- 1 / ((1 + (d_c * cycle_length)) ^ (0:n_cycles))
v_dwe  <- 1 / ((1 + (d_e * cycle_length)) ^ (0:n_cycles))
```

```r
  v_tot_qaly[i] <- t(v_qaly_str) %*% (v_dwe * v_wcc)
```

The WCC vector comes from `gen_wcc(n_cycles, method = c("Simpson1/3", "half-cycle", "none"))` ([source](https://github.com/DARTH-git/cohort-modeling-tutorial-intro/blob/main/R/Functions.R)); DARTH recommends Simpson's 1/3 rule over the traditional half-cycle correction. A useful way to see it: correction and discounting are both per-timestep weights on an accumulated quantity.

**Strategies and comparison.** `calculate_icers()` takes vectors of costs, effects, and strategy names, sorts by cost, removes strategies that are strongly dominated (D, beaten on both cost and health) or extendedly dominated (ED, beaten by a mix of two others), and returns an `icer` data frame with incremental costs, effects, ICERs, and a `Status` column ([basic CEA vignette](https://github.com/DARTH-git/dampack/blob/master/vignettes/basic_cea.Rmd)):

```r
icer_hiv <- calculate_icers(cost = v_hiv_costs,
                            effect = v_hiv_qalys,
                            strategies = v_hiv_strat_names)
```

`plot(icer_obj)` draws the cost-effectiveness plane with the efficient frontier.

**Uncertainty.** PSA parameters are parallel vectors of names, distributions, parameterization types, and distribution parameters ([PSA generation vignette](https://github.com/DARTH-git/dampack/blob/master/vignettes/psa_generation.Rmd)):

```r
my_psa_params <- gen_psa_samp(params = my_params,
                              dists = my_dists,
                              parameterization_types = my_parameterization_types,
                              dists_params = my_dists_params,
                              n = 100)
```

where, for example, costs use `"gamma"` with `"shape, scale"` and utilities `"truncated-normal"` with `"mean, sd, ll, ul"`. The model is then run over the samples with `run_psa(psa_samp = my_psa_params, params_basecase = ..., FUN = simulate_strategies, outcomes = c("Cost", "QALY", "LY", "NMB"), strategies = ...)`. Alternatively, `make_psa_obj(cost, effectiveness, parameters, strategies)` wraps PSA output from any model, after which `ceac()`, `owsa()` / `twsa()` (regression metamodel sensitivity analysis), `calc_evpi()`, `calc_evppi()`, and `calc_evsi()` all work ([VOI vignette](https://github.com/DARTH-git/dampack/blob/master/vignettes/voi.Rmd)).

**Strengths and limitations.**

- Works with any model: `make_psa_obj()` accepts cost and effect matrices from any simulator, exactly the hand-off a disease-modeling library needs.
- Teaches explicit, checkable conventions (discount, WCC, and state reward vectors) that map directly onto array operations.
- No declarative cost layer; correctness depends on the user getting every matrix product and weight vector right.
- Four parallel PSA vectors are fragile (the order has to match across them) compared with heemod's `name ~ dist(...)` formulas.

## BCEA and voi

| Language | Model types | Code | Docs | Key paper |
|---|---|---|---|---|
| R | Post-processing of any PSA or Bayesian output | [giabaio/BCEA](https://github.com/giabaio/BCEA), [chjackson/voi](https://github.com/chjackson/voi) | [BCEA site](https://n8thangreen.github.io/BCEA/), [voi site](https://chjackson.github.io/voi/) | Baio, Berardi, Heath (2017), [Bayesian Cost-Effectiveness Analysis with the R package BCEA](https://doi.org/10.1007/978-3-319-55718-2); Heath, Kunst, Jackson (eds., 2024), [Value of Information for Healthcare Decision-Making](https://doi.org/10.1201/9781003156109) |

These two packages do not build models; they define the standard outputs a model's uncertainty analysis should produce. They show the minimal data a simulation's economic layer needs to output.

**How costs and utilities are declared.** They arrive as matrices. BCEA takes an `n_samples × n_interventions` matrix of effects and one of costs ([BCEA vignette](https://github.com/giabaio/BCEA/blob/master/vignettes/bcea.Rmd)):

```r
bcea_smoke <- bcea(eff, cost, ref = 4, interventions = treats, Kmax = 500)
```

voi accepts either net benefit form (a data frame, one column per treatment, one row per sample) or a cost-effectiveness list with `e`, `c`, and willingness-to-pay `k` ([voi vignette](https://github.com/chjackson/voi/blob/master/vignettes/voi.Rmd)):

```r
outputs_cea <- list( 
  e = data.frame(t1 = 0, t2 = inputs$p1), 
  c = data.frame(t1 = 0, t2 = inputs$p2), 
  k = c(1, 2, 3)
)
```

and the vignette notes that "objects returned by the `bcea` function in the BCEA package satisfy this 'cost-effectiveness analysis' format."

**Discounting and timing conventions.** Out of scope; inputs are already discounted totals.

**Strategies and comparison.** BCEA designates a reference intervention (`ref`) and computes pairwise increments; `ceplane.plot()`, `ceac.plot()`, `ceef.plot()` (efficiency frontier), and `multi.ce()` (multiple-comparison CEAC) work off the `bcea` object.

**Uncertainty.** This is their core. In voi, the inputs are a data frame with one column per parameter and one row per PSA sample, and EVPPI (the value of learning a subset of parameters) uses nonparametric regression of net benefit on those parameters:

```r
evppi(outputs_nb, inputs, pars=c("p1","p2"))
```

```r
evppi(outputs_nb, inputs, pars="p1", method="gp", nsim=1000)
```

EVSI (the value of a proposed study) uses built-in study designs or a user data-generating function, e.g. `evsi(outputs_nb, inputs, study = "normal_known", n=c(100,1000), pars = "p1")`. BCEA offers `BCEA::evppi(m, c("beta.1." , "beta.2."), inp$mat)` with GAM, Gaussian process, and INLA methods ([EVPPI vignette](https://github.com/giabaio/BCEA/blob/master/vignettes/evppi.Rmd)).

**Strengths and limitations.**

- They set the usual exchange format: (samples × strategies) costs, (samples × strategies) effects, and (samples × parameters) inputs. Any simulator that outputs these three tables gets all the VOI tools.
- voi's regression-based EVPPI/EVSI methods are the current state of the art and need only PSA samples, not model reruns.
- No model building, discounting, or cost declaration; analysis only.

## rdecision

| Language | Model types | Code | Docs | Key paper |
|---|---|---|---|---|
| R (R6 classes) | Decision trees, semi-Markov cohort models | [ajsims1704/rdecision](https://github.com/ajsims1704/rdecision) | [CRAN vignettes](https://cran.r-project.org/package=rdecision) | None found; cite the [CRAN package](https://CRAN.R-project.org/package=rdecision) |

rdecision is graph-based: states are nodes, transitions are edges, and costs can attach to either. It is the only R package reviewed with a built-in per-transition cost, and its `ModVar` objects attach uncertainty directly to the value, not via a parameter name.

**How costs and utilities are declared.** Occupancy costs and utilities are set on `MarkovState`, one-off costs on `Transition`. From the [total knee replacement vignette](https://github.com/ajsims1704/rdecision/blob/master/vignettes/SM02-TKR.Rmd):

```r
sA <- MarkovState$new(states["A"], utility = utility_A)
```

```r
tAD <- Transition$new(sA, sD, cost = cost_A)
tAC <- Transition$new(sA, sC, cost = cost_A)
tAB <- Transition$new(sA, sB, cost = cost_A)
tBC <- Transition$new(sB, sC)
```

Costs can be changed after creation (`sA$set_cost(cAm)`), and the model sees the change. In decision trees, costs attach to `Action` edges (choices) and `Reaction` edges (chance outcomes), and utilities to `LeafNode`s ([sumatriptan vignette](https://github.com/ajsims1704/rdecision/blob/master/vignettes/DT01-Sumatriptan.Rmd)):

```r
e17 <- Action$new(d1, c1, cost = c_sumatriptan, label = "Sumatriptan")
e18 <- Action$new(d1, c2, cost = c_caffeine, label = "Caffeine-Ergotamine")
```

**Discounting and timing conventions.** Discount rates are set on the model, separately for cost and utility, and half-cycle correction is chosen per run, separately for population, cost, and QALYs ([HIV vignette](https://github.com/ajsims1704/rdecision/blob/master/vignettes/SM01-HIV.Rmd)):

```r
m <- SemiMarkovModel$new(
  V = list(sA, sB, sC, sD),
  E = list(tAA, tAB, tAC, tAD, tBB, tBC, tBD, tCC, tCD, tDD),
  discount.cost = cDR / 100.0,
  discount.utility = oDR / 100.0
)
```

```r
  m$cycles(
    ncycles = 20L, hcc.pop = hcc, hcc.cost = FALSE, hcc.QALY = hcc
  )
```

`cycles()` returns a Markov trace table with per-cycle `Cost` and `QALY` columns. It can be called repeatedly, so a strategy that changes after two years means running two cycles, changing transition probabilities and costs, and running the remaining 18.

**Strategies and comparison.** In decision trees, a strategy is a choice at each `DecisionNode`, and `dt$evaluate()` returns expected cost and utility per strategy. The user computes ICERs from the results (the HIV vignette does it by hand); there is no built-in dominance or frontier function.

**Uncertainty.** Values can be `ModVar` objects with a distribution, and `ExprModVar` builds derived variables as expressions of other `ModVar`s ([HIV vignette](https://github.com/ajsims1704/rdecision/blob/master/vignettes/SM01-HIV.Rmd)):

```r
dmca <- GammaModVar$new("dmca", "GBP", shape = 1.0, scale = 1701.0)
```

```r
cAm <- ExprModVar$new("cA", "GBP", rlang::quo(dmca + ccca + cAZT))
```

The PSA is then a single call, `dt$evaluate(setvars = "random", by = "run", N = N)` ([decision tree tutorial](https://github.com/ajsims1704/rdecision/blob/master/vignettes/DT00-DecisionTreeTutorial.Rmd)). Each `ModVar` also carries a unit (here `"GBP"`).

**Strengths and limitations.**

- Costs attach to transitions and decision edges, not only states, matching how event-driven disease models produce costs.
- Uncertainty belongs to the value (`GammaModVar`), with units and derived expressions, not a separate lookup by name; this is close to how Starsim treats distributions as objects.
- Limited to cohort models and trees; ICER, frontier, and CEAC are done elsewhere (e.g., dampack or BCEA).

## TreeAge Pro and Amua

| Language | Model types | Code | Docs | Key paper |
|---|---|---|---|---|
| TreeAge: GUI (commercial); Amua: Java GUI (GPL-3) | Decision trees, Markov cohort and Monte Carlo microsimulation; TreeAge also DES | TreeAge: closed source; Amua: [zward/Amua](https://github.com/zward/Amua) | [TreeAge Pro user guide](https://www.treeage.com/help/Content/Home.htm); [Amua wiki](https://github.com/zward/Amua/wiki) | None for Amua; Amua is described by [Harvard CHDS](https://chds.hsph.harvard.edu/doctoral-student-develops-open-source-decision-analytic-software) |

TreeAge Pro is the dominant commercial GUI for decision trees and Markov models in health technology assessment (formal review of whether a treatment is worth funding), and its vocabulary (state rewards, transition rewards, half-cycle correction, `_stage`) is what many analysts think in. Amua is an open source Java tool in the same tradition, with a similar GUI and export to R and Java code.

**How costs and utilities are declared.** In TreeAge, each Markov state has three entries for each reward set (cost, effectiveness, and optional extras): initial, incremental, and final. The [state rewards help page](https://treeage.com/help/Content/3-Building-Markov-Models-Topics/4-Adding-State-Rewards.htm) defines them as "Initial: accumulated in the first cycle (_stage 0). Incremental: accumulated in all other cycles. Final: accumulated after the last cycle (typically 0)." Transition rewards go on the branches of the transition subtree under each state, and under within-cycle correction become "event rewards" ([Markov View](https://treeage.com/help/Content/70-Markov-Model-Tools/10-Markov-View.htm), [extra rewards](https://www.treeage.com/help/Content/70-Markov-Model-Tools/27-Extra-Rewards.htm)). Extra reward sets are commonly used as counters (a reward of 1 on a transition counts the cohort passing through it).

In Amua, costs are attached to any node, and the [Markov models wiki](https://github.com/zward/Amua/wiki/Markov-Models) says that "Costs (or transition rewards) can be added to nodes by clicking the cost button" and that "Cycle rewards for each Markov State can be defined for each dimension in the model." A model has a list of "dimensions" (e.g., cost and QALY) and every cost or reward field is a semicolon-separated tuple across those dimensions; the source stores them as `cost[]` and `rewards[]` arrays per node ([MarkovNode.java](https://github.com/zward/Amua/blob/master/src/markov/MarkovNode.java)).

**Discounting and timing conventions.** TreeAge provides a `Discount()` function taking "value, rate and time", used inside reward expressions with the `_stage` keyword as the time, and the docs note that `_stage` needs dividing or multiplying when the cycle length differs from the discount period ([discounting rewards](https://www.treeage.com/help/Content/70-Markov-Model-Tools/2-Discounting-Rewards.htm)). Half-cycle correction uses the three reward slots: the initial reward is half the incremental reward, and the final reward gives the half back to those still alive ([half-cycle correction](https://www.treeage.com/help/Content/70-Markov-Model-Tools/20-Half-cycle-correction.htm)); newer versions offer a within-cycle correction mode instead ([converting HCC to WCC](https://www.treeage.com/help/Content/70-Markov-Model-Tools/21a-Converting-HCC-to-WCC.htm)). Amua makes both global settings: a discount rate per dimension with discount factor `1/(1+r)^(t/n)` for `n` cycles per year, a discount start cycle, and a checkbox that "will apply a half-cycle correction to the rewards in the first and last cycle of the simulation" ([model properties](https://github.com/zward/Amua/wiki/Model-Properties); fields `halfCycleCorrection`, `discountRates[]`, and `discountStartCycle` in [Scenario.java](https://github.com/zward/Amua/blob/master/src/main/Scenario.java)).

**Strategies and comparison.** In both tools, strategies are the branches of the root decision node. Amua's analysis types are expected value, CEA ("Calculates the incremental cost-effectiveness ratio (ICER) of all strategies compared to the specified baseline strategy", with dimensions designated as "Cost" and "Effect"), and benefit-cost analysis by NMB at a willingness-to-pay threshold ([model properties](https://github.com/zward/Amua/wiki/Model-Properties)). TreeAge reports ICERs with dominance and extended dominance on a CE graph.

**Uncertainty.** Both define named distributions in a model-level table and reference them in any expression; PSA is a Monte Carlo sampling of those distributions, with CEAC and EVPI outputs in TreeAge. (We did not verify Amua's VOI support.)

**Strengths and limitations.**

- The "reward set" or "dimension" idea extends cost and utility to any number of accumulated quantities, each with its own discount rate.
- The three-slot reward is a historically important but error-prone way to encode half-cycle correction; explicit methods (as in heemod and DARTH) are clearer.
- GUIs make models easy to inspect but hard to track in version control, test, or couple to an external simulator; Amua's export to R/Java partly addresses this.

## PyHEOR

| Language | Model types | Code | Docs | Key paper |
|---|---|---|---|---|
| Python | Markov cohort, partitioned survival, microsimulation, discrete-event simulation | [lenardar/PyHEOR](https://github.com/lenardar/PyHEOR) | [PyPI page](https://pypi.org/project/pyheor/) | None |

A search for Python CEA libraries found little; this is the most complete one we could verify. It is very new (versions 0.4.0 and 0.4.1 were uploaded to PyPI in October 2026, AGPL-3.0), so it is here for its interface, not its track record. It is modeled on heemod ("State counts and event flows follow heemod conventions") but adds built-in transition, entry, and limited-duration costs, a useful sketch of the pattern in Python. (We could not verify the Python packages "pyhealth", "PyHE", or "OpenTREE" as CEA tools; PyHealth is a clinical machine learning library, not a CEA library.)

**How costs and utilities are declared.** Rewards are set on the model by name, per strategy and state, with a method for each accrual type. From the README quick start on [PyPI](https://pypi.org/project/pyheor/):

```python
model.set_state_cost("care", {
    "SOC": {"Alive": 1000}, "TRT": {"Alive": 1500},
})
model.set_state_qaly("health", {
    "Alive": lambda p, k: ph.qaly(p["u_alive"], cycle),
})
model.set_starting_cost("test", 200)
model.set_state_cost("loading", {"Alive": 500}, cycles=1)
model.set_transition_cost("terminal", "Alive", "Dead", 10000)
```

The README says: "Costs and QALYs have parallel state, starting, entry, transition and custom interfaces. State rewards accept `cycles=1` or a list of cycle numbers. Callbacks receive parameters and optionally a 1-based cycle index and patient attributes." In the DES engine, state rewards are rates integrated over time and "event rewards at actual times".

**Discounting and timing conventions.** Set on the model constructor with explicit, typed cycle units:

```python
cycle = ph.Cycle(1, "month")
model = ph.MarkovModel(
    states=["Alive", "Dead"], strategies=["SOC", "TRT"],
    n_cycles=120, cycle=cycle, method="life-table",
    dr_cost=ph.rescale_discount_rate(.03, ph.Cycle(1, "year"), cycle),
    dr_qaly=ph.rescale_discount_rate(.03, ph.Cycle(1, "year"), cycle),
)
```

The README is explicit that "State costs and QALYs are **per cycle**. Discount rates are effective rates **per cycle**, and the first cycle is undiscounted. Utility weights require an explicit conversion to QALYs", and `method` is `beginning`, `end`, or `life-table`.

**Strategies and comparison.** Strategies are declared on the model (`strategies=["SOC", "TRT"]`) and every reward is keyed by strategy. `base = model.run_base_case()` returns a result with `base.summary()` and `base.icer()`; the README advertises CE planes, CEACs, and CEAFs.

**Uncertainty.** Distributions are attached to named parameters: `model.add_param("u_alive", base=.8, dist=ph.Beta(mean=.8, sd=.05))`, and `psa = model.run_psa(n_sim=100, seed=42)`.

**Strengths and limitations.**

- The broadest coverage of accrual types in one interface: per state-cycle, starting (time zero), entry, per transition, limited-duration, and custom callbacks.
- Explicit time units (`Cycle(1, "month")`, `rescale_discount_rate()`, `qaly(utility, duration)`) guard against common unit errors, much like Starsim's typed time.
- Early-stage: two releases, one maintainer, and no publication or independent validation yet.

## Excel workbooks (NICE-style Markov models)

| Language | Model types | Code | Docs | Key paper |
|---|---|---|---|---|
| Excel (sometimes VBA) | Decision trees, Markov cohort, partitioned survival | Per-submission; no shared codebase | [NICE health technology evaluations manual (PMG36)](https://www.nice.org.uk/process/pmg36/chapter/economic-evaluation) | Briggs, Claxton, Sculpher (2006), *Decision Modelling for Health Economic Evaluation* (Oxford University Press) |

Most health technology assessment submissions to NICE (England's assessor) and similar agencies are still Excel workbooks; training and reviewer expectations, not software, set the conventions. The Briggs, Claxton, and Sculpher textbook and its spreadsheet exercises are the standard template, and most health economists will compare any new tool against them.

**How costs and utilities are declared.** A "parameters" sheet lists every input with its base-case value, distribution, and distribution parameters (e.g., gamma alpha and beta for costs, beta for utilities), each as a named range. A "trace" sheet has one row per cycle and one column per state with cohort occupancy; adjacent columns compute per-cycle costs as `SUMPRODUCT` of occupancy with state costs, plus transition costs from the inflow into a state (the difference between successive trace rows, or tracked flows). One-off costs (e.g., an intervention at time zero) go in a separate cell added to the total.

**Discounting and timing conventions.** A discount-factor column, `1/(1+r)^t` with `t` the cycle time in years, multiplies the cost and QALY columns, with separate rates allowed for costs and effects. The NICE reference case (its standard method) uses "The same annual rate for both costs and health effects (currently 3.5%)" ([PMG36](https://www.nice.org.uk/process/pmg36/chapter/economic-evaluation)); a 2022 consultation proposed 1.5% but NICE kept 3.5% for now ([OHE commentary](https://www.ohe.org/insights/nice-wind-change-what-and-so-what-nice-methods-consultation/)). Half-cycle correction is usually done by averaging adjacent trace rows (trapezoidal) or by subtracting half of the first-cycle and adding half of the last-cycle values.

**Strategies and comparison.** Typically one trace sheet per strategy (copied), with a results sheet computing total discounted costs and QALYs, incremental values, and ICERs, and a fully incremental table with dominance for more than two strategies.

**Uncertainty.** PSA replaces each parameter's base-case value with an `=GAMMA.INV(RAND(), alpha, beta)`-style draw switched on by a flag, and a VBA macro recalculates the workbook N times and copies results to a PSA sheet, from which CEACs and the cost-effectiveness plane are drawn.

**Strengths and limitations.**

- Transparent to reviewers and decision-makers: every number is visible in a cell, which is why agencies accept it.
- The parameter sheet (value, distribution, distribution parameters, source) is a good, familiar format for costing inputs.
- Copying sheets per strategy and macro-driven PSA are error-prone and slow, and cannot represent agent-level heterogeneity, transmission, or herd effects.

## API comparison

How each package spells the main costing concepts. "n/a" means the concept is out of scope; "manual" means the user writes it by hand.

| Concept | heemod | hesim | dampack / DARTH | BCEA / voi | rdecision | TreeAge / Amua | PyHEOR | Excel convention |
|---|---|---|---|---|---|---|---|---|
| Cost per state per cycle | `define_state(cost = ...)` | `stateval_tbl(...)` + `StateVals(method = "wlos")` | Named vector `v_c_str` × trace | n/a | `MarkovState$new(..., cost = )` | Incremental state reward (TreeAge); state cycle reward (Amua) | `set_state_cost(name, {strategy: {state: value}})` | `SUMPRODUCT(trace row, state costs)` |
| Utility per state | `define_state(utility = ...)` | `utility_model = StateVals` | Named vector `v_u_str` × trace | n/a | `MarkovState$new(..., utility = )`; `LeafNode$new(utility = )` | Effectiveness reward set / dimension | `set_state_qaly(name, {...})` | Same as cost column |
| Transition cost | Tunnel state workaround | Not general; `method = "starting"` gives per-entry cost | Transition array (time-dependent tutorial) | n/a | `Transition$new(from, to, cost = )` | Transition reward (event reward under WCC) | `set_transition_cost(name, from, to, value)` | Inflow column × cost |
| One-off / starting cost | `define_starting_values(cost = )` | `method = "starting"` (cohort: at time 0) | Manual | n/a | Cost on decision `Action` edge | Initial reward / cost on decision branch | `set_starting_cost(name, value)` | Separate cell |
| Time-limited cost | `model_time`, `state_time` in expressions | `define_tparams(..., times = )` with `time` | Manual (time-dependent arrays) | n/a | Rerun `cycles()` after `set_cost()` | `_stage` in expressions | `cycles=1` or list of cycles | Formula on cycle column |
| Cost categories | Multiple named state values | Named list `cost_models = list(Drug = , Medical = )` | Manual | n/a | One cost per state/edge | Extra reward sets / dimensions | Named rewards (`"care"`, `"loading"`) | Columns |
| Discount | `discount(x, r)` inside each value | `sim_costs(dr = )`, `sim_qalys(dr = )` at run time | Weight vectors `v_dwc`, `v_dwe` | n/a (inputs pre-discounted) | `discount.cost`, `discount.utility` on model | `Discount(value, rate, time)` (TreeAge); per-dimension rate (Amua) | `dr_cost`, `dr_qaly` per cycle | Discount factor column |
| Half-cycle / within-cycle | `run_model(method = "life-table")` | `integrate_method = "trapz"` | `gen_wcc(method = "Simpson1/3")` | n/a | `cycles(hcc.pop, hcc.cost, hcc.QALY)` | Initial = half of incremental (TreeAge); checkbox (Amua) | `method = "life-table"` | Average adjacent rows |
| Strategies | Named `define_strategy()` args to `run_model()`; `dispatch_strategy()` | Rows of `hesim_data(strategies = )` | Loop over strategy list | Columns of `e`, `c` | `DecisionNode` branches | Decision node branches | `strategies=[...]` on model | Copied sheets |
| PSA distributions | `define_psa(name ~ gamma(mean, sd))` | `stateval_tbl(dist = )`, `define_rng({...})` | `gen_psa_samp(params, dists, parameterization_types, dists_params)` | Supplied as input table | `GammaModVar$new(...)` objects | Distribution table | `add_param(name, base, dist=ph.Beta(...))` | `GAMMA.INV(RAND(), ...)` |
| ICER / frontier | `summary(res_mod)`; efficiency frontier | `cea_pw()`, `icer()` | `calculate_icers()` with D/ED status | `bcea(ref = )`, `ceef.plot()` | Manual | Built-in CE report | `result.icer()` | Manual table |
| CEAC | `plot(pm, type = "ac")` | `plot_ceac()`, `plot_ceaf()` | `ceac()` | `ceac.plot()`, `multi.ce()` | Manual | Built-in (TreeAge) | Built-in | Macro + chart |
| VOI | EVPI (`type = "evpi"`) | EVPI via `cea()` | `calc_evpi()`, `calc_evppi()`, `calc_evsi()` | `evppi()`, `evsi()`, `BCEA::evppi()` | n/a | EVPI (TreeAge) | Not documented | Rare |
| Output object | `run_model` / `psa` objects with `get_values()`, `get_counts()` | `ce` long table by sample, strategy, category, `dr` | `icer`, `psa`, `ceac`, `evpi` data frames | `bcea` object; voi data frames | Markov trace with `Cost`, `QALY` columns | Report tables | Result with `summary()`, `icer()` | Results sheet |

## Cross-cutting patterns

- **Costs and utilities are values attached to model structure, not code in the engine.** Every declarative tool (heemod, hesim, rdecision, TreeAge, PyHEOR) lets the user say "this state has cost X" or "this transition has cost Y" as data, and the engine accumulates it. A disease-modeling library should let users declare costs on its existing states (per unit time in state) and events (infection, diagnosis, treatment start, death), instead of writing analyzer code that multiplies counts by unit costs.
- **Four accrual types cover nearly everything.** Per unit time in a state (`wlos`, state rewards), per entry or event (`starting` in individual models, transition rewards), one-off per strategy or at time zero (`define_starting_values`, `set_starting_cost`), and time-limited versions of these (`cycles=1`, `times =`). Events are natural in agent-based models, since each has an exact time and agent, and are what cohort tools struggle with most (heemod's tunnel-state workaround).
- **Separate the economic layer from the epi engine.** hesim's `trans_model` + `utility_model` + `cost_models` split and dampack's `make_psa_obj()` both show that the economic layer needs only time in state and event counts or times from the engine. For Starsim, this suggests a costing module that reads states and event logs and attaches to any disease, not costing logic inside each disease.
- **Discounting and cycle correction are per-timestep weights, best applied after simulation.** DARTH writes them as weight vectors, and hesim applies `dr` at `sim_costs()` time, giving several discount rates from one simulation. heemod's per-value `discount()` is flexible but easy to get inconsistent. Discounting at accumulation time, with separate rates for costs and effects, matches NICE-style requirements and avoids rerunning simulations to test the discount rate. Agent-based and continuous-time models can discount at the exact event time and need no half-cycle correction.
- **Named outcome dimensions, not just "cost" and "utility".** heemod's named state values, TreeAge's reward sets, Amua's dimensions, and hesim's cost categories all extend to any number of accumulated quantities (drug cost, hospital cost, life-years, DALYs, events). The CEA step then picks which is the cost and which the effect (`run_model(cost = , effect = )`).
- **Uncertainty attaches to parameters, and the PSA is a separate declaration.** heemod's `define_psa(name ~ dist(...))` and rdecision's `GammaModVar` are the two good forms: a separate table of distributions by parameter name, or distribution objects used directly as values. Starsim already uses distribution objects for epi parameters, so making unit costs and utility weights the same kind of object would put them in the same PSA.
- **Standardize the outputs: (samples × strategies) costs and effects, plus (samples × parameters) inputs.** BCEA, voi, dampack, and hesim all read these. A disease-modeling library that outputs these three tables (with strategy, sample, and category labels) gets ICERs, frontiers, CEACs, and EVPPI/EVSI from existing tools.
- **Strategies as data, compared by a separate function.** Strategies appear as rows (hesim), named arguments (heemod), or branches (trees), but the comparison (sorting by cost, strong and extended dominance, frontier, ICERs) is always a separate post-processing step. Simulation scenarios map directly onto strategies; the dominance/frontier algorithm is well defined and should be borrowed (dampack's `calculate_icers()` is a clear reference), not rebuilt per disease.
- **Make units explicit.** PyHEOR's `Cycle(1, "month")`, `rescale_discount_rate()`, and `qaly(utility, duration)`, and rdecision's unit on each `ModVar` (`"GBP"`), guard against the most common costing errors (annual costs applied per month, utilities summed as if they were QALYs). Starsim's typed time (`ss.peryear`, `ss.dur`) fits well: a state cost is a rate (currency per year) and an event cost is an amount (currency per event).
- **Keep a tabular input format.** heemod's CSV states file (`.model`, `.state`, value columns, `.discount.*`) and the Excel parameter sheet (value, distribution, parameters, source) show that health economists expect to review costing inputs as a table. A cost declaration that converts to and from a table of unit costs by state or event, with distributions and sources, would ease review by agencies used to Excel submissions.
