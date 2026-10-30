# Cancer, chronic disease, and health systems

Cancer and chronic disease models did cost-effectiveness analysis (CEA, comparing interventions on cost and health gained) long before most infectious disease models, because their main customers (screening guideline bodies, national agencies that assess whether health technologies are worth funding, insurers) ask for little else. Whole-health-system models are newer and ask a different question: not "what does this intervention cost per DALY averted" (a DALY is one healthy life-year lost) but "what does the health system actually use, and what happens to health when it runs out". This page covers seven exemplars: two individual-based whole-system or multi-disease platforms (Thanzi La Onse and Vivarium), the Starsim-family HPVsim, the closed-source cervical and colorectal cancer consortium models, the open IMPACT NCD microsimulation, and the WHO-CHOICE and OneHealth approaches. A section on health system capacity follows, then cross-cutting patterns. Metric definitions (DALY, QALY, ICER, net monetary benefit) are in [metrics.md](metrics.md); general cost-effectiveness software is in [cea-software.md](cea-software.md).

Snippets are verbatim from the linked sources. Code links are pinned to the commit or tag that was read.

## Thanzi La Onse (TLO)

| Disease(s) | Paradigm | Language | Code | Key papers |
|---|---|---|---|---|
| Essentially all major causes of burden in Malawi (HIV, TB, malaria, maternal and newborn, cancers, cardiometabolic, injuries, and more) | Individual-based, discrete-event, whole health system | Python (pandas population dataframe) | [UCL/TLOmodel](https://github.com/UCL/TLOmodel) | Hallett et al. (2025), [Estimates of resource use in the public-sector health-care system and the effect of strengthening health-care services in Malawi during 2015–19](https://doi.org/10.1016/S2214-109X(24)00413-3), *Lancet Global Health*; Molaro et al. (2024), [A new approach to Health Benefits Package design](https://doi.org/10.1371/journal.pcbi.1012462), *PLoS Comput Biol*; Mohan et al. (2025), [Method for costing a health system using a Health Systems Model](https://doi.org/10.1101/2025.01.22.25320881), medRxiv |

TLO is the most complete example anywhere of a disease model in which the health system is itself simulated. Every clinical contact is a *health system interaction* (HSI) event that requests specific health worker time, consumables, equipment, and beds, and those requests can fail. Costing then means adding up what the simulation says was used.

- **What is costed**: Four components, per the [costing README](https://github.com/UCL/TLOmodel/blob/3d8fdb7dcf8bf299204ee60710d964f2b84b0d52/src/scripts/costing/README.md): human resources for health (salary, pre-service training, recruitment to replace attrition, in-service training, supervision), medical consumables (dispensed plus excess stock to account for wastage), medical equipment (purchase cost annualized over lifespan, plus service, spare parts, and maintenance), and facility operating costs (electricity, water, cleaning, security, vehicles, inpatient food). The perspective (whose costs count) is the public-sector provider. Unit costs come from Malawi: the HR file cites Malawi HSSP-III annexes, consumables cite the Central Medical Stores Trust (`CMST 2023`) and the Malawi Essential Health Package, and equipment comes from HSSP-III. A separate file holds Resource Mapping budget and spending data, used to check the bottom-up estimate against actual spending.
- **How costs attach to the model**: During the run, each HSI declares its appointment footprint (types that map to minutes per cadre via `ResourceFile_Appt_Time_Table.csv`), requests consumables through `get_consumables()`, and declares equipment through `add_equipment()`. The health system logs what was requested, available, and used. Costing happens entirely after the run: `estimate_input_cost_of_scenarios()` in [`cost_estimation.py`](https://github.com/UCL/TLOmodel/blob/3d8fdb7dcf8bf299204ee60710d964f2b84b0d52/src/scripts/costing/cost_estimation.py) reads the logs for every draw and run and multiplies quantities by unit costs. Two cost logics coexist. Consumables are variable costs, which scale with use (quantity dispensed × unit cost, inflated by an empirical inflow-to-outflow ratio from OpenLMIS data). Human resources are largely fixed costs, paid regardless of use: salary × number of staff in post, with an option (`cost_only_used_staff`) to cost only cadre–level combinations ever used, not minutes consumed. Equipment is costed if it was ever used at a facility.
- **Health outcomes**: DALYs, computed in-simulation by the [`HealthBurden`](https://github.com/UCL/TLOmodel/blob/3d8fdb7dcf8bf299204ee60710d964f2b84b0d52/src/tlo/methods/healthburden.py) module. Each disease module declares its `CAUSES_OF_DISABILITY` (mapped to GBD cause names) and implements `report_daly_values()`, which returns a disability weight (0 for full health, 1 for death-equivalent) for every living person. A monthly event collects these from every module, rescales so that no person's total exceeds 1, multiplies by 1/12, and aggregates by sex, age, wealth, district, and year. YLL (years of life lost to early death) are computed at death against a frontier life expectancy (`Age_Limit_For_YLL = 90.0`) and stored three ways: spread over future calendar years up to the end of the simulation, "stacked by time" (all YLL assigned to the year of death), and "stacked by age and time". Disability weights come from a GBD-derived `ResourceFile_DALY_Weights.csv`, by sequela code. Discounting (counting future costs and health for less than present ones) of costs (fixed or year-specific rates) and of DALYs happens in post-processing.
- **Analyses supported**: Full health system cost by component, cadre, facility level, and year; scenario comparisons of health system strengthening (more staff, better consumable availability) versus vertical (single-disease) programs; ICERs (extra cost per extra unit of health) along a cost-effectiveness frontier and return on investment, using a Malawi-specific cost-effectiveness threshold and value of a statistical life (see [`roi_analysis_horizontal_vs_vertical.py`](https://github.com/UCL/TLOmodel/blob/3d8fdb7dcf8bf299204ee60710d964f2b84b0d52/src/scripts/comparison_of_horizontal_and_vertical_programs/economic_analysis_for_manuscript/roi_analysis_horizontal_vs_vertical.py#L759), which uses `chosen_cet = 191.4304166`); design of health benefits packages (the set of services a system funds) under constrained capacity; projections of total health spending against Dieleman et al. per-capita estimates. Uncertainty covers stochastic runs and parameter draws, summarized as means or medians with intervals.
- **Example**: An HSI declares its resource needs in the constructor and requests consumables when it runs; availability gates what happens next ([`cervical_cancer.py`](https://github.com/UCL/TLOmodel/blob/3d8fdb7dcf8bf299204ee60710d964f2b84b0d52/src/tlo/methods/cervical_cancer.py#L1140)):

  ```python
  class HSI_CervicalCancer_CINRemoval_Cryotherapy(HSI_Event, IndividualScopeEventMixin):
      ...
      def __init__(self, module, person_id):
          super().__init__(module, person_id=person_id)

          self.TREATMENT_ID = "CervicalCancer_CINRemoval_Cryotherapy"
          self.EXPECTED_APPT_FOOTPRINT = self.make_appt_footprint({"Over5OPD": 1})
          self.ACCEPTED_FACILITY_LEVEL = '1a'
          self.add_equipment('Cryotherapy unit')  # Essential Equipment

      def apply(self, person_id, squeeze_factor):
          ...
          cons_avail = self.get_consumables(
              item_codes=self.module.item_codes_cervical_can['cervical_cancer_cryotherapy'],
              optional_item_codes= self.module.item_codes_cervical_can['cervical_cancer_cryotherapy_optional'])

          if cons_avail:
              # Record date and stage of starting treatment
              df.at[person_id, "ce_date_cryotherapy"] = self.sim.date
  ```

  The same module reports disability per person each month ([`cervical_cancer.py`](https://github.com/UCL/TLOmodel/blob/3d8fdb7dcf8bf299204ee60710d964f2b84b0d52/src/tlo/methods/cervical_cancer.py#L712)):

  ```python
  def report_daly_values(self):

      # This must send back a dataframe that reports on the HealthStates for all individuals over the past month

      df = self.sim.population.props  # shortcut to population properties dataframe for alive persons

      disability_series_for_alive_persons = pd.Series(index=df.index[df.is_alive], data=0.0)

      # Assign daly_wt to those with cancer stages before stage4 and have either never been treated or are no longer
      # in the stage in which they were treated
      disability_series_for_alive_persons.loc[
          df.ce_hpv_cc_status.isin(['stage1', 'stage2a', 'stage2b', 'stage3'])
      ] = self.daly_wts['stage_1_3']
  ```

  And the central combiner caps per-person disability across modules ([`healthburden.py`](https://github.com/UCL/TLOmodel/blob/3d8fdb7dcf8bf299204ee60710d964f2b84b0d52/src/tlo/methods/healthburden.py#L742)):

  ```python
  # 3) Rescale the DALY weights
  # Create a scaling-factor (if total DALYS for one person is more than 1, all DALYS weights are scaled so that
  #   their sum equals one).
  scaling_factor = (disease_specific_daly_values_this_month.sum(axis=1).clip(lower=0, upper=1) /
                    disease_specific_daly_values_this_month.sum(axis=1)).fillna(1.0)
  ...
  # Multiply 1/12 as these weights are for one month only
  disease_specific_daly_values_this_month = disease_specific_daly_values_this_month * (1 / 12)
  ```

  Unit cost inputs are plain CSVs, for example [`ResourceFile_Costing_Consumables.csv`](https://github.com/UCL/TLOmodel/blob/3d8fdb7dcf8bf299204ee60710d964f2b84b0d52/resources/costing/ResourceFile_Costing_Consumables.csv):

  ```text
  Item_Code,Items,Unit,Price_per_unit,Data_source,Notes
  0,"Levonorgestrel 0.0375 mg, cycle",Tablet (Levonorgestrel 0.0375 mg/~30 micrograms),0.043909897,CMST 2023,
  1,"Levonorgestrel 0.15 mg + Ethinyl estradiol 30 mcg (Microgynon), cycle",Tablet (Levonorgestrel 0.15 mg + Ethinyl estradiol 30 mcg),0.0519511,CMST 2023,
  2,"Condom, male",Single condom,0.029480354,Malawi EHP 2021,
  ```

- **Strengths and limitations**:
  - The separation is clean: disease modules describe *what is used* (appointment types, item codes, equipment names) and never see a dollar figure; money comes afterwards from swappable country files. The README gives steps for adapting to another country.
  - Resource use comes from the simulation itself: if consumables are unavailable or staff time runs out, the care is not delivered, and both the cost and the health consequence follow automatically.
  - The fixed-versus-variable split is realistic for a whole system (most HR cost does not scale with appointments) but makes marginal costing (the added cost of one intervention) harder than in a single-disease model.
  - The cost layer is a set of analysis scripts outside the `tlo` package, tied closely to TLO's log format and to Malawi-specific facility-level assumptions that the README lists as hard-coded.

## Vivarium

| Disease(s) | Paradigm | Language | Code | Key papers |
|---|---|---|---|---|
| Any GBD cause; used mainly for chronic disease, nutrition, maternal and child health, risk factors | Agent-based microsimulation, discrete time, value pipelines | Python | [ihmeuw/vivarium_public_health](https://github.com/ihmeuw/vivarium_public_health) (archived at `v5.1.14`; development moved to [ihmeuw/vivarium-suite](https://github.com/ihmeuw/vivarium-suite)) | [Documentation](https://vivarium-public-health.readthedocs.io/) |

Vivarium (see the [architecture review](../approaches/vivarium.md)) builds disease models from GBD inputs, so its health outcomes are GBD's: every disease state carries a disability weight, every death carries a YLL value from a reference life table, and observers (components that record outputs) add up both per time step.

- **What is costed**: Nothing, in the public health library. A search of `vivarium_public_health` at `v5.1.14` finds no cost-related code. Costing in IHME's Vivarium analyses happens after the simulation, from observer outputs; we did not find a public, reusable cost component.
- **How costs attach to the model**: Not applicable inside the library. The natural place is the observers: `CategoricalInterventionObserver` and `CategoricalRiskObserver` already record person-time in each intervention or exposure category, exactly what a "cost per person-time on treatment" calculation needs, and `DiseaseObserver` records transition counts for "cost per event".
- **Health outcomes**: YLDs (years lived with disability, the other half of a DALY) and YLLs, accrued per agent during the simulation and aggregated by observers. Each `DiseaseState` registers a `{state_id}.disability_weight` pipeline (from GBD data via the artifact) and modifies an `all_causes.disability_weight` pipeline, which combines causes using `union_post_processor`, that is `1 - prod(1 - dw)` (multiplicative comorbidity, unlike TLO's additive-then-capped rule). `DisabilityObserver` sums each living agent's weight × step length. At death, `Mortality` looks up remaining life expectancy from `population.theoretical_minimum_risk_life_expectancy` (GBD's reference life table) and stores it in a `years_of_life_lost` column, which `MortalityObserver` sums. The library has no discounting or age weighting; results use the stratifications the model declares.
- **Analyses supported**: Averted YLDs, YLLs, and DALYs between scenarios, by age, sex, year, and custom strata; uncertainty via GBD input draws and random seeds. Project code handles cost-effectiveness.
- **Example**: The YLD observer ([`results/disability.py`](https://github.com/ihmeuw/vivarium_public_health/blob/v5.1.14/src/vivarium_public_health/results/disability.py#L118)):

  ```python
  def register_observations(self, builder: Builder) -> None:
      """Register an observation for years lived with disability."""
      cause_pipelines = [
          f"{cause.state_id}.disability_weight" for cause in self.causes_of_disability
      ]
      self.register_adding_observation(
          builder=builder,
          name="ylds",
          pop_filter="is_alive == True",
          when="time_step__prepare",
          requires_attributes=cause_pipelines,
          additional_stratifications=self.configuration.include,
          excluded_stratifications=self.configuration.exclude,
          aggregator=self.disability_weight_aggregator,
      )
  ...
  def disability_weight_aggregator(self, dw: pd.DataFrame) -> float | pd.Series:
      ...
      aggregated_dw = (dw * to_years(self.step_size)).sum().squeeze()
  ```

  And YLL ([`results/mortality.py`](https://github.com/ihmeuw/vivarium_public_health/blob/v5.1.14/src/vivarium_public_health/results/mortality.py#L186)), using the value written at death in [`population/mortality.py`](https://github.com/ihmeuw/vivarium_public_health/blob/v5.1.14/src/vivarium_public_health/population/mortality.py#L357) (`dead[self.years_of_life_lost_column_name] = life_expectancy`):

  ```python
  def calculate_ylls(self, x: pd.DataFrame) -> float:
      """Calculate the years of life lost during this time step."""
      died_of_cause = x["exit_time"] > self.clock()
      return x.loc[died_of_cause, "years_of_life_lost"].sum()
  ```

- **Strengths and limitations**:
  - Treating disability weight as a *pipeline* (a value that components can modify in turn) is elegant: an intervention that reduces severity can modify a cause's disability weight the same way a risk factor modifies an incidence rate, and the comorbidity rule is a declared policy (`union_post_processor`), not ad hoc code.
  - Observers with declared stratifications produce YLDs, YLLs, person-time, and counts the same way, which is all a cost layer needs.
  - The library has no built-in cost, utility (QALY), or discounting; every project rebuilds that layer.
  - YLL is assigned in full at the time step of death (incidence-of-death basis), so cutting off at a time horizon and discounting future life-years are left to the analyst.

## HPVsim (and other Starsim-family models)

| Disease(s) | Paradigm | Language | Code | Key papers |
|---|---|---|---|---|
| HPV infection, precancer, cervical cancer | Agent-based, network transmission (built on Starsim from v3) | Python | [starsimhub/hpvsim](https://github.com/starsimhub/hpvsim) | Stuart et al. (2024), [HPVsim: An agent-based model of HPV transmission and cervical disease](https://doi.org/10.1371/journal.pcbi.1012181), *PLoS Comput Biol*; Cohen et al. (2023), [Understanding the key determinants of an HPV therapeutic vaccine](https://doi.org/10.1101/2023.12.04.23299403), medRxiv |

HPVsim is the closest Starsim-family analogue to the cancer exemplars below. It ships a DALY analyzer but no cost layer; published analyses do costing in separate repositories by exporting resource-use counts and multiplying by unit costs.

- **What is costed**: In the core library, nothing. In the therapeutic vaccine analysis repository ([amath-idm/hpvsim_txvx_analyses](https://github.com/amath-idm/hpvsim_txvx_analyses)), an `econ_analyzer` exports yearly counts of HPV screens, prophylactic and therapeutic vaccine doses, thermal ablations, LEEPs, and cancer treatments, explicitly "for feeding into costing/health economic analysis". Unit costs and perspective are applied outside the simulation.
- **How costs attach to the model**: Unit cost × products delivered, after the run. HPVsim interventions deliver *products* (tests, vaccines, treatments), and in v2-era code each had an `n_products_used` result that the analyzer reads: "count events during the run, multiply later".
- **Health outcomes**: DALYs, incidence-based. The [`dalys` analyzer](https://github.com/starsimhub/hpvsim/blob/main/hpvsim/analyzers.py#L482) attributes both YLD and YLL to the year of cancer onset: at onset it knows each agent's scheduled cancer death time, so YLD = (death age − onset age) × a stage-averaged disability weight (GBD 2017 weights × time fractions per stage), and YLL = reference life expectancy (default 84) − death age. Weights are per agent (`people.scale`) and scaled to the real population at the end of the run. The analyzer does not discount; the txvx analysis discounts yearly counts afterwards at 3%.
- **Analyses supported**: DALYs averted between scenarios; resource-use streams for external CEA. No built-in ICER or PSA (probabilistic sensitivity analysis, which reruns the analysis over sampled inputs).
- **Example**: The current DALY analyzer ([`hpvsim/analyzers.py`](https://github.com/starsimhub/hpvsim/blob/main/hpvsim/analyzers.py#L502), v3.2.0):

  ```python
  # GBD2017 cervical-cancer disability weights and time fractions per stage.
  _DEFAULT_DISABILITY_WEIGHTS = dict(
      weights=[0.288, 0.049, 0.451, 0.54],
      time_fraction=[0.05, 0.85, 0.09, 0.01],
  )
  ...
  def _accumulate(self, year, cancer_age, death_age, weight):
      if year < self.start_year or year > self.end_year:
          return
      idx = year - self.start_year
      dur = death_age - cancer_age
      self.yld[idx] += float((weight * dur * self.av_disutility).sum())
      years_left = np.maximum(0.0, self.life_expectancy - death_age)
      self.yll[idx] += float((weight * years_left).sum())
  ```

  And the resource-use exporter from the analysis repository ([`analyzers.py`](https://github.com/amath-idm/hpvsim_txvx_analyses/blob/51a8b71b8c90ef0e05bb6b26666426999de83706/analyzers.py#L404)):

  ```python
  class econ_analyzer(hpv.Analyzer):
      '''
      Analyzer for feeding into costing/health economic analysis.
      
      Produces a dataframe by year storing:
          
          - Resource use: number of vaccines, screens, lesions treated, cancers treated
          - Cases/deaths: number of new cancer cases and cancer deaths
          - Average age of new cases, average age of deaths, average age of noncancer death
      '''
  ...
              if screen_scen_label != 'No screening':
                  # Resources
                  self.df.loc[li].new_hpv_screens += sim.get_intervention('screening').n_products_used.values[ltt]
                  self.df.loc[li].new_thermal_ablations += sim.get_intervention('ablation').n_products_used.values[ltt]
  ```

  In that repository's plotting scripts, DALYs were computed from yearly aggregates and *average* ages rather than per agent ([`plot_fig2.py`](https://github.com/amath-idm/hpvsim_txvx_analyses/blob/51a8b71b8c90ef0e05bb6b26666426999de83706/plot_fig2.py#L65)): `yld = np.sum(np.sum([0.54 * .1, 0.049 * .5, 0.451 * .3, 0.288 * .1]) * ca_years * cancers)`. The v3 analyzer replaces that with per-agent accrual, a useful before-and-after illustration of the aggregate-versus-agent choice.
- **Other Starsim-family NCD work**: [mighti](https://github.com/starsimhub/mighti) (HIV plus NCDs, early-stage per its README) has a [`life_expectancy.py`](https://github.com/starsimhub/mighti/blob/main/mighti/life_expectancy.py) that builds period life tables from simulated deaths, the input a YLL or life-years-gained calculation needs, but no DALY, QALY, or cost code.
- **Strengths and limitations**:
  - Products give a natural, already-counted unit for costing (a dose, a test, a treatment course).
  - Incidence-based DALYs computed at onset are cheap and exact given the scheduled death time, but they put all burden in the onset year, which fits poorly with discounting and with interventions (such as treatment) that change the death time after onset.
  - The weights are cancer-only; precancer treatment disutility (the health loss from the treatment itself) and other causes are not captured.
  - Each analysis repo rebuilds the cost layer, and the earlier aggregate DALY approximation (average ages × counts) shows how easily that layer drifts from what the simulation actually knows.

## WHO Cervical Cancer Elimination Modelling Consortium (Policy1-Cervix, HPV-ADVISE, Harvard)

| Disease(s) | Paradigm | Language | Code | Key papers |
|---|---|---|---|---|
| HPV, precancer, cervical cancer | Three independent models: dynamic transmission plus individual-based natural history (details vary by model) | Not public | Not public | Brisson et al. (2020), [Impact of HPV vaccination and cervical screening on cervical cancer elimination](https://doi.org/10.1016/S0140-6736(20)30068-4), *Lancet*; Canfell et al. (2020), [Mortality impact of achieving WHO cervical cancer elimination targets](https://doi.org/10.1016/S0140-6736(20)30157-4), *Lancet*; Simms et al. (2023), [Benefits, harms and cost-effectiveness of cervical screening, triage and treatment strategies](https://doi.org/10.1038/s41591-023-02600-4), *Nat Med* |

The consortium is the main comparative modeling exercise behind WHO's cervical cancer elimination strategy and its 2021 screening guidelines. The elimination papers report health outcomes only; the cost-effectiveness work behind the guidelines used Policy1-Cervix and is described in Simms et al. (2023). None of the three models' code is public, so this exemplar is reconstructed from the papers.

- **What is costed**: Per Simms et al. (2023), a health services/provider perspective, 2019 US dollars, across 78 LMICs. Costs fall into five PSA groups: cancer diagnosis, staging, and treatment; pre-cancer treatment; HPV testing; VIA; and cytology. HPV test costs drew on CHAI and WHO-CHOICE data, and other screening costs on WHO-CHOICE, applied country by country and then population-weighted. Invasive cancer treatment is costed by FIGO stage (one surgical episode with hospitalization, plus radiotherapy and chemotherapy episodes in the first year), with surveillance costs for up to five years and palliative care in the year of cervical cancer death. Productivity losses and out-of-pocket costs were excluded.
- **How costs attach to the model**: Per event and age, with access probabilities. Screening and pre-cancer costs fall at the age a simulated woman is screened; cancer treatment costs are "applied only in the instance that a woman receives cancer treatment", weighted by the proportion with access. Annual costs sum unit cost × probability of use at that age over resources, times the alive population. This is cost per event applied to model outputs, with phase-of-care elements (first-year treatment, surveillance, terminal palliative care).
- **Health outcomes**: Health-adjusted life-years (HALYs) saved, using disability weights in the base case, with sensitivity analyses using undiscounted life-years and adding pre-cancer treatment disutilities. The elimination papers report cases and deaths averted. The base case discounts costs at 3% but effects at 0%, with a 3%/3% sensitivity analysis.
- **Analyses supported**: Efficiency frontiers (the strategies that give the most health for their cost) and ICERs across screening, triage, and treatment strategies; cost-effectiveness acceptability curves (the chance each strategy is best at a given budget for health) across willingness-to-pay values of US$100–2,000 per HALY; PSA; harms (number of pre-cancer treatments) as a co-primary outcome; comparison of three models' projections for robustness.
- **Example**: No code is public. The cost-attachment rule is given in the Methods of [Simms et al. (2023)](https://pmc.ncbi.nlm.nih.gov/articles/PMC10719104/), which state that "Invasive cancer treatment was costed by stage (FIGO staging)" and that treatment costs "are applied only in the instance that a woman receives cancer treatment"; regional cost inputs are in its Supplementary Table 7.
- **Strengths and limitations**:
  - Multi-model comparison is the gold standard for structural uncertainty, and the consortium's protocol harmonized inputs and outputs across models.
  - Reporting harms (treatments, referrals) alongside costs and HALYs is a pattern a general library should make easy: they are just more event counts.
  - Closed code means the mechanism cannot be checked in detail or reused.
  - Differential discounting (0% effects, 3% costs) is a reminder to keep discount rates for costs and effects as separate settings.

## CISNET colorectal models (MISCAN-Colon, SimCRC, CRC-SPIN)

| Disease(s) | Paradigm | Language | Code | Key papers |
|---|---|---|---|---|
| Colorectal adenoma and cancer (CISNET also has breast, lung, prostate, cervical, esophageal, bladder groups) | Individual-level microsimulation of natural history plus screening | Not public | Not public; [model profiles](https://cisnet.cancer.gov/resources/model-registry/colorectal-models) | Nascimento de Lima et al. (2024), [Characteristics of a cost-effective blood test for colorectal cancer screening](https://doi.org/10.1093/jnci/djae124), *JNCI*; McFerran et al. (2022), [Colorectal Cancer Screening within Colonoscopy Capacity Constraints](https://doi.org/10.1177/23814683221097064), *MDM Policy & Practice*; Goede et al. (2017), [Harms, benefits and costs of fecal immunochemical testing versus guaiac fecal occult blood testing](https://doi.org/10.1371/journal.pone.0172864), *PLoS One* |

The NCI's Cancer Intervention and Surveillance Modeling Network (CISNET) runs multiple independent models per cancer site. Its colorectal group (MISCAN-Colon from Erasmus MC and MSK, SimCRC from Minnesota and MGH, CRC-SPIN from Fred Hutch) underpins USPSTF screening recommendations and many cost-effectiveness analyses. The models are closed source, but the costing structure is well documented and much the same across papers.

- **What is costed**: Screening tests (per invitation and per attendee for FIT; per test for blood tests), diagnostic and surveillance colonoscopy with and without polypectomy, colonoscopy complications, and CRC treatment by stage and phase of care. US analyses take a payer perspective (the insurer's costs) with Medicare-based costs; Dutch and Canadian analyses use national costs. Nascimento de Lima et al. (2024) inflate to 2021 US dollars; McFerran et al. (2022) use euros from earlier Dutch analyses; Goede et al. (2017) derive Ontario treatment costs from a matched cohort of administrative data.
- **How costs attach to the model**: Two mechanisms. Screening and diagnostic costs are unit cost × event count (each test, colonoscopy, complication). Treatment costs use the **phase-of-care** structure (a different cost rate for each stretch of treatment) near-universal in cancer CEA: Goede et al. define "three clinically relevant phases—initial, continuous and terminal care. The initial phase was defined as the first 12 months following diagnosis, the terminal phase was defined as the final 12 months of life, and the continuous phase was defined as all months between the initial and terminal phase." Terminal care is further split by whether death is from CRC or another cause. Because the terminal phase counts backward from death, it can only be assigned once the agent's death time is known: at death, or afterwards from the life history.
- **Health outcomes**: Life-years and QALYs (life-years weighted by quality of life) gained relative to no screening, over the remaining lifetime of a cohort (typically starting at age 45 or 50). Disutilities are subtracted for screening tests, colonoscopies (Goede et al. use the equivalent of two days of life per colonoscopy, 0.0055 QALYs), complications, and cancer treatment. Costs and effects are discounted at 3% in all three papers.
- **Analyses supported**: Efficiency frontiers of hundreds of strategies (McFerran et al. evaluate 525); ICERs for nondominated strategies (those no alternative beats on both cost and health); net monetary benefit (health gained valued in money, minus cost) at a willingness to pay of US$100,000/QALY, which ranks dominated strategies on one scale too; threshold analysis (what blood-test cost and sensitivity would make it cost-effective); one-way sensitivity analyses; multi-model comparison; and **capacity-constrained optimization**, which caps colonoscopies per 1,000 per year (undiscounted) and picks the strategies with the most QALYs under that cap.
- **Example**: No code is public. The cost input structure is shown in Table 3 of [McFerran et al. (2022)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9091364/) (MISCAN-Colon, euros), reproduced here as a stage × phase grid:

  | Stage | Initial treatment | Continuous care | Terminal care, death of CRC | Terminal care, death of other cause |
  |---|---|---|---|---|
  | Stage 1 | 12,500 | 340 | 17,500 | 4400 |
  | Stage 2 | 17,000 | 340 | 17,500 | 4000 |
  | Stage 3 | 21,000 | 340 | 18,500 | 5200 |
  | Stage 4 | 25,000 | 340 | 25,000 | 14,000 |

  with screening costs alongside (FIT €14.85 per invitation and €4.37 per attendee; colonoscopy €303 without and €393 with polypectomy; complications €1250).
- **Strengths and limitations**:
  - The stage × phase-of-care cost grid is the usual input format for cancer CEA and maps cleanly onto an agent's history (diagnosis date, stage, death date, cause of death).
  - Capacity limits the *choice* of strategy (a constrained optimization over model outputs), not the simulation itself; this differs from TLO.
  - Multi-model reporting gives structural uncertainty but no PSA in the papers reviewed here.
  - Closed source; reuse is through collaboration rather than code.

## IMPACT NCD (IMPACTncd_Engl)

| Disease(s) | Paradigm | Language | Code | Key papers |
|---|---|---|---|---|
| CVD, diabetes, COPD, several cancers, dementia, CKD, depression, and others, driven by risk factors (BMI, blood pressure, cholesterol, smoking, alcohol, diet, physical activity) | Discrete-time individual-level microsimulation of a synthetic population | R (with C++ and DuckDB) | [ChristK/IMPACTncd_Engl](https://github.com/ChristK/IMPACTncd_Engl) | Kypridemos et al. (2018), [Future cost-effectiveness and equity of the NHS Health Check cardiovascular disease prevention programme](https://doi.org/10.1371/journal.pmed.1002573), *PLoS Med* |

IMPACT NCD is the open, actively developed member of the "risk factor to chronic disease" microsimulation family (the CDC/RTI CVD Policy Model is the classic US counterpart but its code is not public). It is a good example of a cost layer that works entirely after the run, from a complete per-person-per-year life course output, and supports several perspectives at once.

- **What is costed**: Healthcare costs (an annual cost per prevalent disease plus a base cost for everyone), social care costs (age-based plus disease add-ons), informal care (from a regression on utility and comorbidity), and economic output (paid and unpaid work, adjusted for health), all for England in GBP. These combine into three perspectives: healthcare only; healthcare plus social care (the reference case, or standard method, of NICE, England's health technology assessor, for its NHS and Personal Social Services); and societal, where `total_cost = healthcare + socialcare + informalcare - economic_output`. User-defined `*_costs` columns (for example intervention program costs) can be added to each perspective.
- **How costs attach to the model**: Cost per person-time in a state, computed after the run. The simulation writes a per-person, per-year life course table with prevalence flags for every disease; the summary step in [`Simulation_class_summaries.R`](https://github.com/ChristK/IMPACTncd_Engl/blob/3c44cbf4a6ec974b0730c181381d6ebfcb0d0ba4/Rpackage/IMPACTncd_England_model_pkg/R/Simulation_class_summaries.R#L700) builds SQL expressions over that table in DuckDB, one additive term per prevalent condition, and then scales up by survey weights. Costs thus add across comorbidities.
- **Health outcomes**: QALYs, with utility (a quality-of-life score, here from the EQ-5D-5L questionnaire) per person-year computed from a regression-style expression: an age-specific population norm plus adjustments for income, education, number of chronic conditions, sex, and ethnicity, minus disease-specific decrements (sources: Janssen and Szende 2014; Sullivan et al. 2011). The year of death gets half utility, and the result is clamped to [0, 1]. Discounting is an argument of `export_tables()`, not a simulation setting: separate QALY and cost rates, each a vector (default `c(0, 3.5)`, undiscounted and NICE 3.5% side by side), and willingness-to-pay thresholds (default `c(25000, 35000)` GBP/QALY) per the comments in [`inputs/sim_design.yaml`](https://github.com/ChristK/IMPACTncd_Engl/blob/3c44cbf4a6ec974b0730c181381d6ebfcb0d0ba4/inputs/sim_design.yaml#L31).
- **Analyses supported**: Incremental QALYs and costs per Monte Carlo iteration versus a comparator scenario, ICER and NMB (net monetary benefit) at each threshold, quantiles across iterations (a PSA to the extent that iterations sample parameter as well as stochastic uncertainty; we did not check how the iterations are seeded), by perspective and stratum (including deprivation and ethnicity, so analyses of who benefits need no extra work).
- **Example**: The healthcare cost rule, written as a SQL expression over the life course table ([`Simulation_class_summaries.R`](https://github.com/ChristK/IMPACTncd_Engl/blob/3c44cbf4a6ec974b0730c181381d6ebfcb0d0ba4/Rpackage/IMPACTncd_England_model_pkg/R/Simulation_class_summaries.R#L841)):

  ```r
  # --- Healthcare cost expression (sum of disease-specific costs) ---
  healthcare_cost_expr <- "
    1254.0  -- base cost (no disease)
    + 124.0 * CASE WHEN htn_prvl > 0 THEN 1 ELSE 0 END
    + 1680.0 * CASE WHEN af_prvl > 0 THEN 1 ELSE 0 END
    + 1116.0 * CASE WHEN t2dm_prvl > 0 THEN 1 ELSE 0 END
    + 4756.0 * CASE WHEN t1dm_prvl > 0 THEN 1 ELSE 0 END
    + 5444.0 * CASE WHEN chd_prvl > 0 THEN 1 ELSE 0 END
    + 8673.0 * CASE WHEN stroke_prvl > 0 THEN 1 ELSE 0 END
  ```

  and the utility rule:

  ```r
  # Apply half EQ5D for year of death and clamp to [0, 1]
  # Divide by 2 if dead (all_cause_mrtl > 0), divide by 1 if alive
  eq5d5l_expr <- sprintf(
    "LEAST(GREATEST((%s) / (CASE WHEN all_cause_mrtl > 0 THEN 2.0 ELSE 1.0 END), 0.0), 1.0)",
    raw_eq5d_expr
  )
  ```

- **Strengths and limitations**:
  - Because the full life course is saved, costs, utilities, perspectives, discount rates, and thresholds can all be changed without rerunning the simulation; this is the strongest argument for post hoc costing.
  - Several perspectives from one run, with explicit rules for which components belong to which, is better than most models manage.
  - Unit costs and utility decrements are hard-coded in R source as SQL fragments, not read from an input file, so changing them means editing code.
  - Additive cost per prevalent condition ignores interactions (a person with both stroke and heart failure may cost less than the sum), and annual cost per prevalent case merges incident-year and ongoing costs that phase-of-care models separate.

## WHO-CHOICE and the OneHealth Tool

| Disease(s) | Paradigm | Language | Code | Key papers |
|---|---|---|---|---|
| All (sectoral) | WHO-CHOICE: generalized CEA using PopMod, a two-disease multistate cohort model. OneHealth: ingredients-based (quantity × price) planning and costing with linked impact modules | PopMod: not public; OneHealth: Spectrum desktop software | Not open source; OneHealth is distributed by [Avenir Health](https://www.avenirhealth.org/) | Bertram et al. (2021), [Methods for the Economic Evaluation of Health Care Interventions for Priority Setting in the Health System: An Update From WHO CHOICE](https://doi.org/10.34172/ijhpm.2020.244), *IJHPM*; Lauer et al. (2003), [PopMod: a longitudinal population model with two interacting disease states](https://doi.org/10.1186/1478-7547-1-6), *Cost Eff Resour Alloc* |

These get brief coverage because they are aggregate tools and likely discussed elsewhere in this review, but both supply inputs to the microsimulations above.

- **What is costed**: WHO-CHOICE estimates patient-level costs (drugs, tests, outpatient visits, inpatient bed-days) and program-level costs (management, training, media, monitoring) per intervention, with country-specific unit cost databases. Its unit cost estimates are inputs to other models; Simms et al. (2023) above use them for screening costs. OneHealth multiplies quantities by prices, with one central commodity database shared across modules (per the [WHO OneHealth Q&A](https://www.who.int/news-room/questions-and-answers/item/questions-and-answers-on-the-onehealth-tool)), plus health system modules for human resources, infrastructure, logistics, and financing.
- **How costs attach to the model**: Coverage × target population × ingredients per person covered. There is no individual-level simulation; impact comes from linked models (for example LiST for maternal and child health).
- **Health outcomes**: WHO-CHOICE uses DALYs averted relative to a *null scenario* (no interventions in place), the defining feature of generalized CEA: comparing against nothing, not current practice, lets whole packages be ranked.
- **Analyses supported**: League tables (interventions ranked by cost per DALY averted); expansion paths for building a benefits package; costed national strategic plans and budget projections (OneHealth).
- **Example**: No public code. Bertram et al. (2021) describe the null-scenario and package logic.
- **Strengths and limitations**:
  - The null-scenario comparator and package-level ranking are what TLO's health benefits package work does mechanistically.
  - The country unit cost databases are a widely reused input.
  - Being aggregate and closed, they cannot represent individual histories, queues, or intervention interactions beyond what the linked impact model provides.

## Health system capacity

Most of the models above treat resources as unlimited: a scheduled intervention happens, and its cost is counted. Two exemplars show alternatives, which differ in where the limit applies.

**Capacity inside the simulation (TLO).** TLO computes daily capability for each cadre at each facility as total patient-facing minutes, and each HSI's appointment footprint uses minutes from the relevant cadres via the appointment time table. Excerpt from [`ResourceFile_Appt_Time_Table.csv`](https://github.com/UCL/TLOmodel/blob/3d8fdb7dcf8bf299204ee60710d964f2b84b0d52/resources/healthsystem/human_resources/definitions/ResourceFile_Appt_Time_Table.csv):

```text
Appt_Type_Code,Facility_Level,Officer_Category,Time_Taken_Mins
ANCSubsequent,2,Clinical,2.0
ANCSubsequent,2,Nursing_and_Midwifery,18.0
ANCSubsequent,2,Pharmacy,1.0
```

The `mode_appt_constraints` parameter selects how capacity binds ([`healthsystem.py`](https://github.com/UCL/TLOmodel/blob/3d8fdb7dcf8bf299204ee60710d964f2b84b0d52/src/tlo/methods/healthsystem.py#L360)): "1: elastic constraints, all HSI events run, provided officers required to deliver the HSI have capabilities > 0" and "2: hard constraints, only HSI events for which capabilities are available run". In mode 2, events queue by priority (with configurable priority policies, used in the health benefits package work) and are dropped if not run before their `tclose` date, so unmet demand becomes health loss with no further modeling. Consumable, bed, and equipment availability are likewise probabilistic and configurable (`'default'`, `'all'`, `'none'`), with defaults derived from facility stock data.

TLO's earlier versions also had a **squeeze factor**. An older release defined it as "(call/available - 1). ie. the highest fractional over-demand among any type of officer that is called-for in the appt_footprint of an HSI event" ([`healthsystem.py` at `tara_htm_scaleup_v1.0`](https://github.com/UCL/TLOmodel/blob/tara_htm_scaleup_v1.0/src/tlo/methods/healthsystem.py#L1418)), passed to every HSI's `apply()` so a module could lower quality of care when the system was overloaded. The developers have since removed it ([issue #1661](https://github.com/UCL/TLOmodel/issues/1661), "The calculation of squeeze factors is unnecessary and can be removed"); the current code still passes `squeeze_factor=0.0` until removal is complete. The lesson: "run but worse" was harder to parameterize than "run or don't run".

**Capacity as an optimization constraint (MISCAN-Colon).** McFerran et al. (2022) and Goede et al. (2017) report colonoscopies per 1,000 per year for every strategy and pick the one with the most QALYs under a colonoscopy cap. The simulation itself is unconstrained; capacity applies when choosing among outputs.

The two are complementary. The TLO approach captures queueing, competition between diseases, and the health opportunity cost (the health forgone elsewhere) of using staff time for one condition instead of another; the CISNET approach is cheap and transparent when one resource dominates. A general library needs resource-use counts for both, and an optional in-simulation scheduler for the first.

## Cross-cutting patterns

- **Counts in, money out.** In every open exemplar (TLO, HPVsim analyses, IMPACT NCD), the simulation produces quantities (appointments, items, products, person-years in states) and money comes afterwards from swappable input tables. Only the cost *structure* (which events and states carry resource use) needs to be in the model; unit costs, currency year, perspective, and discount rates belong in post-processing. A general library should make it easy for any module to report labeled resource-use counts.
- **Four ways of attaching costs recur**: unit cost × event count (tests, doses, procedures); cost per person-time in a state (IMPACT NCD's annual cost per prevalent condition, Vivarium's person-time observers); phase-of-care costs keyed to diagnosis and death dates (CISNET, Policy1-Cervix); and resource use per health-system interaction with fixed costs for staff and facilities (TLO). The third needs each agent's death date and cause, so it is computed at death or from saved life histories.
- **Per-agent accrual versus aggregate post-processing.** TLO, Vivarium, and HPVsim v3 accrue disability weight × time (or YLL at death) per agent during the run; the HPVsim txvx analysis and many published models approximate from aggregate counts and average ages. Per-agent accrual is exact, cheap, and stratifiable in an agent-based model; aggregates are where errors creep in. IMPACT NCD shows a third option: save the full per-agent, per-year life course and do everything afterwards, which gives the most flexibility but takes more storage.
- **Comorbidity rules differ and should be explicit.** TLO sums module disability weights and rescales to a maximum of 1; Vivarium combines multiplicatively (`1 - prod(1 - dw)`); IMPACT NCD subtracts additive utility decrements and clamps; costs are additive everywhere. A library should make the rule a declared setting, as Vivarium does.
- **Burden attribution timing varies.** DALYs can be attributed to the year they are lived (TLO, Vivarium YLD), the year of death (Vivarium YLL, TLO's "stacked" YLL), or the year of onset (HPVsim). The choice changes discounted results and what a time horizon cuts off; TLO stores several versions side by side, a good default.
- **Discounting comes after the run and often differs between costs and effects.** They need separate rates (Policy1-Cervix used 3% and 0%; NICE uses 3.5% for both), sometimes year-specific (TLO), and often several at once (IMPACT NCD exports 0% and 3.5% together). No in-simulation DALY accumulator discounts, which seems right.
- **Fixed versus variable costs matter at system scale.** Single-disease CEAs treat almost everything as variable. TLO costs staff by headcount, not minutes used, and equipment by whether it was ever used, because health systems spend that way. A library should let a resource be costed per unit used or per unit of capacity.
- **Capacity is either a mechanism or a constraint.** TLO simulates queues and dropped care; CISNET optimizes unconstrained outputs under a cap. Both need resource use by type and time.
- **Harms, equity, and perspectives are just more outputs.** Pre-cancer treatments (Policy1-Cervix), colonoscopies (CISNET), and costs by deprivation quintile and perspective (IMPACT NCD) all come from the same stratified counts. The more a library standardizes stratified event and person-time outputs, the less each analysis has to build.
- **Closed code is the norm for the most influential models.** The consortium and CISNET models drive guidelines but cannot be inspected; the open exemplars (TLO, Vivarium, HPVsim, IMPACT NCD) are where reusable patterns can be read and borrowed.
