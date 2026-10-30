# HIV and budget optimization

HIV is where disease modeling and health economics have been tied together longest. Two decades of donor-funded antiretroviral therapy (ART) scale-up, national plans, Global Fund applications, and "investment cases" have produced three costing traditions: (1) program-budget models (Optima, Goals plus the Resource Needs Model, OneHealth), where spending is an *input* that drives coverage and the model is optimized over allocations; (2) individual-based models (HIV Synthesis, EMOD-HIV), where costs add up as unit cost × resource use per agent, usually after the run, and feed into incremental cost-effectiveness ratios (ICERs, extra cost per extra unit of health) against a threshold; and (3) multi-model comparisons (the HIV Modelling Consortium) that applied a *common costing framework* to structurally different models so their economic outputs could be compared. This page reviews seven exemplars, focusing on how costs attach to the model. For metric definitions (DALYs, ICERs, net DALYs, allocative efficiency) see [metrics.md](metrics.md), especially [allocative efficiency and optimization](metrics.md#allocative-efficiency-and-optimization); for general-purpose cost-effectiveness analysis (CEA) packages see [cea-software.md](cea-software.md).

Snippets are verbatim from the linked sources. Where a detail could not be verified from a primary source, the text says so.

## Atomica (and Optima TB)

| Disease(s) | Paradigm | Language | Code | Key papers |
|---|---|---|---|---|
| Disease-agnostic; used for HIV, TB, hepatitis C, diabetes, hypertension, cervical cancer, malaria, and more | Compartmental, cascade, stratified by population | Python + Excel workbooks | [atomicateam/atomica](https://github.com/atomicateam/atomica) | Goscé et al. (2021), [Optima TB: A tool to help optimally allocate tuberculosis spending](https://doi.org/10.1371/journal.pcbi.1009255); see also [atomica.md](../approaches/atomica.md) |

Atomica is the general engine extracted from Optima HIV and now underlies Optima TB and several other Optima tools. Its costing layer is the cleanest available version of the **spending → coverage → parameter value** chain, and unlike most costing here it runs *inside* the simulation, not after it.

- **What is costed**: program spending only. Each program (e.g. "Testing - clinics", "Client tracing") has a time series of annual spend, a unit cost, and optional capacity constraint and saturation. There is no ingredients breakdown (itemized quantities × prices), no perspective (whose costs count), and no non-program health-system costs; unit costs come from country program spending data entered by analysts.
- **How costs attach to the model**: a third workbook, the *program book*, has three sheets. "Program targeting" says which populations and compartments each program reaches; "Spending data" gives spend and unit cost per program per year; "Program effects" gives, for each targetable parameter and population, a baseline value, the value at full coverage of each program, and how programs interact. Each time step, the model computes capacity = spend / unit cost ([`Program.get_capacity`](https://github.com/atomicateam/atomica/blob/main/atomica/programs.py#L1266)), divides by the current size of the targeted compartments to get fractional coverage, optionally applies a saturating curve ([`Program.get_prop_covered`](https://github.com/atomicateam/atomica/blob/main/atomica/programs.py#L1311)), and a [`Covout`](https://github.com/atomicateam/atomica/blob/main/atomica/programs.py#L1345) object maps the coverages of all programs reaching that parameter to one parameter value, overwritten in [`Model.update_pars`](https://github.com/atomicateam/atomica/blob/main/atomica/model.py#L2728) between the program start and stop years. Because the denominator is the live compartment size, coverage and impact for a fixed budget respond to epidemic dynamics, the main reason this costing cannot happen after the run.
- **One-off versus continuous programs**: units carry meaning. A unit cost in `$/person` marks a one-off program (e.g. a test), one in `$/person/year` a continuous program (e.g. ART), and the code multiplies spending by `dt` only for one-off programs ([`Program.is_one_off`](https://github.com/atomicateam/atomica/blob/main/atomica/programs.py#L1205)).
- **Program interactions**: `Covout` supports `additive`, `random`, and `nested` coverage interactions, plus "impact interaction" strings such as `'Prog1+Prog2=10'` giving the outcome when two programs reach the same person. The default for overlapping coverage is "best": the program with the largest effect wins.
- **Health outcomes**: none built in. Atomica has no DALY, QALY, or discounting (counting the future for less than the present) code; an objective is any model quantity (compartment, characteristic, flow, or program spending) named in a `Measurable`. DALYs have to be defined as a framework quantity (e.g. a parameter summing disability-weighted compartments).
- **Analyses supported**: budget and coverage scenarios (`ProgramInstructions` can override spending or coverage), allocative optimization with `Adjustment`s (spending bounds per program and year), `Measurable`s (`MinimizeMeasurable`, `MaximizeMeasurable`, `AtLeastMeasurable`, `DecreaseByMeasurable`, cascade-stage objectives), and `Constraint`s ([`TotalSpendConstraint`](https://github.com/atomicateam/atomica/blob/main/atomica/optimization.py#L870), with optional `budget_factor` for scaled budgets). Optimizers are adaptive stochastic descent (ASD), particle swarm, and hyperopt. "Money minimization" (cheapest allocation meeting a target) minimizes spending measurables subject to `AtLeastMeasurable` targets. For uncertainty, `ProgramSet.sample()` perturbs spend, unit cost, saturation, and effect sizes.
- **Example**: the core of the cost-coverage chain, from [`programs.py`](https://github.com/atomicateam/atomica/blob/main/atomica/programs.py#L1291-L1336):

```python
unit_cost = self.unit_cost.interpolate(tvec, method="previous")
if self.is_one_off:
    # The spending is $/year, and the /year gets eliminated if the unit cost is also per year. For one-off programs, the unit cost is not
    # /year, therefore we need to multiply the spending by the timestep to the capacity as people rather than people/year
    spending *= dt

capacity = spending / unit_cost
```

```python
if self.saturation.has_data:
    # If the coverage denominator (eligible) is 0, then we need to use the saturation value
    prop_covered = np.divide(capacity, eligible, out=np.full(capacity.shape, np.inf), where=eligible != 0)
    saturation = self.saturation.interpolate(tvec, method="previous")
    prop_covered = 2 * saturation / (1 + exp(-2 * prop_covered / saturation)) - saturation
```

The bundled HIV demo program book ([`hiv_progbook.xlsx`](https://github.com/atomicateam/atomica/blob/main/atomica/library/hiv_progbook.xlsx)) has this shape (cells abridged; the "Program effects" row gives the diagnosis rate for females at zero coverage and at full coverage of each testing program):

| Sheet | Row | Columns |
|---|---|---|
| Spending data | `Testing - clinics` | `Units`, `Uncertainty`, `Assumption`, `2015`…`2018` |
| | `Annual spend` | `$/year`, …, `15000000` |
| | `Unit cost` | `$/person`, …, `100` |
| | `Capacity constraint`, `Saturation`, `Coverage` | `people/year`, `N.A.`, `people/year` |
| Program effects | `Diagnosis rate` / `Females` | `Baseline value` `0`, `Coverage interaction` `Additive`, `Testing - clinics` `1`, `Testing - outreach` `1` |

And an optimization, from the Atomica [test suite](https://github.com/atomicateam/atomica/blob/main/tests/test_tox_optimization.py#L45-L53):

```python
instructions = at.ProgramInstructions(alloc=alloc, start_year=2020)  # Instructions for default spending
adjustments = list()
adjustments.append(at.SpendingAdjustment("Treatment 1", 2020, "abs", 0.0, 100.0))
adjustments.append(at.SpendingAdjustment("Treatment 2", 2020, "abs", 0.0, 100.0))
measurables = at.MaximizeMeasurable("ch_all", [2020, np.inf])
constraints = at.TotalSpendConstraint()  # Cap total spending in all years
optimization = at.Optimization(name="default", adjustments=adjustments, measurables=measurables, constraints=constraints)  # Evaluate from 2020 to end of simulation
```

- **Strengths and limitations**:
    - The cleanest separation here between epidemic model (framework + data book), program costs (program book), and decision problem (`Optimization`); the same epidemic model can run with or without programs.
    - Units on unit costs and capacities do real work (one-off versus continuous), which is rare.
    - Costs are program budgets, not economic costs: no perspective, no discounting, no costs of illness or treatment cascade outside programs, and no built-in DALYs, so standard CEA (cost-effectiveness analysis) outputs take extra work.
    - The "Program effects" sheet asks for the parameter value at full coverage, which is where most of the evidence (and arbitrariness) lies.

## Optima HIV

| Disease(s) | Paradigm | Language | Code | Key papers |
|---|---|---|---|---|
| HIV | Compartmental (population × CD4 × cascade stage) | Python (legacy versions MATLAB) | [optimamodel/optima](https://github.com/optimamodel/optima) | Kerr et al. (2015), [Optima: A Model for HIV Epidemic Analysis, Program Prioritization, and Resource Optimization](https://doi.org/10.1097/QAI.0000000000000605), JAIDS |

Optima HIV predates Atomica and still has its own codebase. It has been used in World Bank–supported allocative efficiency studies (how best to split a fixed budget) and HIV investment cases in dozens of countries. The typical question is "given this year's HIV budget, how should it be split across testing, ART, PrEP, key-population programs, and so on to minimize new infections and deaths by 2030?", and the inverse, "what is the minimum budget to hit these targets?".

- **What is costed**: program spending, as in Atomica. Each `Program` has cost-coverage parameters (unit cost, saturation, population factor) by year, historical cost-coverage data, target populations and parameters, and a `nonhivdalys` field for DALYs averted outside HIV (e.g. by programs with wider health benefits).
- **How costs attach to the model**: the same three-link chain as Atomica, with named objects: `Costcov` maps spending to number covered, and `Covout` maps coverage to parameter values. The `Costcov` curve is linear up to a lower saturation and logistic above it ([`Costcov.function`](https://github.com/optimamodel/optima/blob/main/optima/programs.py#L1406)). Program outputs overwrite model parameters (testing rates, condom use, ART initiation, PrEP use) and the epidemic model reruns, so costs are inputs and outcomes follow from simulation.
- **Health outcomes**: `Resultset.make()` computes DALYs as years of life lost (YLL: deaths × discounted remaining years to a fixed life expectancy, by mean population age) plus years lived with disability (person-time in each CD4 state × disability weight, a 0–1 severity score, with a separate weight on ART). Defaults are an 80-year life expectancy and 3% discounting of YLL only ([`results.py`](https://github.com/optimamodel/optima/blob/main/optima/results.py#L493-L541)).
- **Analyses supported**: budget scenarios, coverage scenarios, outcome minimization with a weighted objective over deaths, infections, DALYs, and undiagnosed people (plus cascade targets), money minimization to reach fractional reductions, time-varying allocations, budget scale-up curves (`budgetscale`), and multi-region "portfolio" (geospatial) optimization in which a national budget is split across regions using per-region budget-outcome curves.
- **Example**: the DALY calculation, verbatim from [`results.py`](https://github.com/optimamodel/optima/blob/main/optima/results.py#L514-L541) (abridged):

```python
if discountrate>0 and discountrate<1: # Make sure it has reasonable bounds
    denominator = log(1-discountrate) # Start calculating the integral of (1-discountrate)**potentialyearslost
    numerator = (1-discountrate)**potentialyearslost - 1 # Minus 1 for t=0
    discountedyearslost = numerator/denominator # See https://en.wikipedia.org/wiki/Lists_of_integrals#Exponential_functions
...
## Years lived with disability
disutiltx = self.pars['disutiltx'].y
disutils = [self.pars['disutil'+key].y for key in self.settings.hivstates]
yldpops = allpeople[:,alltx,:,:].sum(axis=1)     * disutiltx
```

and the default objective weights, from [`optimization.py`](https://github.com/optimamodel/optima/blob/main/optima/optimization.py#L261-L264):

```python
objectives['deathweight'] = 5    # "Relative weight per death"
objectives['inciweight']  = 1    # "Relative weight per new infection"
objectives['dalyweight']  = 0    # "Relative weight per DALY"
objectives['undiagweight']= 0    # "Relative weight per undiagnosed person"
```

- **Strengths and limitations**:
    - Answers the question policymakers actually ask (splitting a fixed budget), and the inverse (minimum budget for a target), with one model.
    - The cost-coverage curve has an explicit form, and its inverse turns coverage targets into budgets.
    - The objective is a weighted sum of counts with ad hoc weights (5 per death, 1 per infection by default), not a welfare measure; DALYs exist but are off by default, and costs outside program budgets do not enter.
    - Results are sensitive to saturation and full-coverage effect inputs, often expert judgment instead of data.

### Related: Optima Nutrition

Optima Nutrition ([optimamodel/Nutrition](https://github.com/optimamodel/Nutrition); Pearson et al. 2018, [BMC Public Health](https://doi.org/10.1186/s12889-018-5294-z)) reimplements the idea outside Atomica with more curve shapes: [`CostCovCurve`](https://github.com/optimamodel/Nutrition/blob/main/nutrition/programs.py#L411) supports linear and logistic curves with increasing, decreasing, or mixed marginal costs, and programs can run at "fixed budget" or "fixed coverage" as population changes. This is the clearest sign in the Optima family that the *shape* of the cost function should be a declared choice, not hard-coded.

## Spectrum: Goals, the Resource Needs Model, and the OneHealth Tool

| Disease(s) | Paradigm | Language | Code | Key papers |
|---|---|---|---|---|
| HIV (Goals, AIM, RNM); all health programs (OneHealth) | Compartmental risk-group transmission model (Goals); deterministic projection plus costing spreadsheets | Windows desktop and web application; RNM historically Excel | Closed source, free download from [Avenir Health](https://www.avenirhealth.org/) | Stover et al. (2016), [What Is Required to End the AIDS Epidemic as a Public Health Threat by 2030? The Cost and Impact of the Fast-Track Approach](https://doi.org/10.1371/journal.pone.0154893), PLOS ONE; [WHO OneHealth Tool](https://www.who.int/tools/onehealth) |

Spectrum, maintained by Avenir Health, is the most widely used HIV planning suite: AIM produces the official UNAIDS HIV estimates, Goals adds transmission dynamics and intervention impact, and the Resource Needs Model (RNM) computes costs. The UNAIDS global resource-needs estimates (including the Fast-Track targets) are produced this way.

- **What is costed**: service delivery costs for each prevention, treatment, and enabling intervention, plus "Program Enablers" (planning, administration, supply chain, training, M&E), "Social Enablers", and "Development Synergies". In the Fast-Track analysis ART unit costs are broken into service delivery, labs, first-line ARVs, second-line ARVs, and pre-ART by region, and unit costs for key-population programs fall over time with economies of scale ([Stover et al. 2016](https://doi.org/10.1371/journal.pone.0154893)).
- **How costs attach to the model**: target population × coverage × unit cost, a separate costing layer on the coverage scenario that drives the epidemic model. In the paper's words: "For most interventions the resources are estimated by multiplying the size of the target population (such as young women and girls, sex workers or men with multiple partners) by the coverage (the percentage reached with the intervention) and the unit cost (the cost to provide the service to one person for one year)" ([Stover et al. 2016](https://doi.org/10.1371/journal.pone.0154893)). Coverage is the input; costs are computed from it (the reverse of Optima, where spending is the input). The 2010 [Resource Needs Model presentation](https://www.aidsdatahub.org/sites/default/files/resource/resource-needs-model-2010.pdf) shows the same structure (target population, people reached, coverage, cost per person reached). Intervention *effects* in Goals act on behaviors (condom use, partner numbers) and on biomedical cofactors (circumcision, ART, PrEP), with effect sizes taken from trials.
- **OneHealth Tool**: the WHO-endorsed, Avenir-built tool for costing national health plans across all programs. It uses ingredients-based costing (quantities × prices of drugs, commodities, staff time, and health-system inputs) and links to impact modules: the Lives Saved Tool (maternal and child health, including malaria), AIM for HIV, and a TB model ([WHO Q&A](https://www.who.int/news-room/questions-and-answers/item/questions-and-answers-on-the-onehealth-tool)). We could not verify from public documentation how costs and impact pass between OneHealth and each module.
- **Health outcomes**: infections averted, AIDS deaths averted, and life-years gained; cost per infection averted appears in older Goals manuals. Published applications do not show DALYs as the primary Goals/RNM output.
- **Analyses supported**: budget estimation for strategic plans and global targets, scenario comparison, cost per infection averted, and investment cases. Goals has also been used for allocation analyses, but any optimization algorithm is not publicly documented.
- **Example**: no public code. The Fast-Track paper's Table 3 gives the input structure: "Current cost per patient per year for ART and pre-ART services (2015 USD$)" with columns "Service Delivery | Labs | ARVs—1st line | ARVs—2nd line | Pre-ART" and a row per UNAIDS region (e.g. Sub-Saharan Africa: $222 | $71 | $136 | $332 | $182) ([Stover et al. 2016](https://doi.org/10.1371/journal.pone.0154893)).
- **Strengths and limitations**:
    - UNAIDS, ministries, and Global Fund applications all use this costing structure, so its categories are the usual vocabulary for HIV budgets.
    - The population × coverage × unit cost form is simple, easy to check, and separate from the epidemic model.
    - Closed source; manuals document the equations, but the code cannot be inspected or reused.
    - Linear in coverage by construction (constant unit cost at any scale, except for time trends set from outside), so diminishing returns enter only through the epidemic model.

## HIV Synthesis

| Disease(s) | Paradigm | Language | Code | Key papers |
|---|---|---|---|---|
| HIV (heterosexual sub-Saharan Africa; versions for MSM), with drug resistance, PrEP, VL monitoring, and some non-communicable disease | Individual-based stochastic simulation, 3-month time step | SAS | Published per paper, e.g. [figshare 10.6084/m9.figshare.24072609](https://doi.org/10.6084/m9.figshare.24072609.v1) (CC BY 4.0); [project site](https://github-pages.ucl.ac.uk/hiv-synthesis) | Phillips et al., community tenofovir-lamivudine-dolutegravir (TLD) cost-effectiveness, Lancet Global Health (code at the figshare link); many Lancet HIV and Nature CEA papers on ART monitoring, drug resistance, and PrEP |

HIV Synthesis (Andrew Phillips and colleagues, UCL) is one of the HIV models most used for policy cost-effectiveness analysis, including analyses commissioned for WHO guidance. It is the archetype of **per-agent cost accumulation inside the simulation**: every 3-month step, each agent adds up the costs of its drugs, tests, clinic visits, and conditions.

- **What is costed**: health-system costs in fine detail: each antiretroviral drug, ART initiation, line switches, viral load tests (lab versus point of care), CD4 tests, resistance tests, drug-level tests, clinic visits (with reduced visit costs for those stably suppressed), cotrimoxazole, TB and WHO stage 3/4 and AIDS-defining condition care, HIV testing by testing channel and population, PrEP (oral, injectable, vaginal ring) drugs and visits, circumcision, condom distribution, sex-worker programs, adherence interventions, child HIV costs, and antihypertensive drugs. Unit costs are hard-coded constants in the model program.
- **How costs attach to the model**: unit cost × indicator, per agent, per step. Each agent's per-step `cost` sums component costs, each non-zero only if the agent used that resource that period. Costs and DALYs are discounted per agent at 3% from the intervention year, then summed across agents and rescaled to the national population in a separate program. Costs therefore come from the simulation run itself, but as component-level discounted sums that can be re-weighted afterward.
- **Health outcomes**: per-agent utility, a 0–1 quality-of-life score, each step (`util`: 1 if HIV-negative, lower for HIV, toxicity, TB, WHO stage 3 conditions, and AIDS-defining conditions), giving QALYs and DALYs for living agents as `(1 - util) * 0.25`, plus YLL for those who died before age 80 (accumulated as time that would have been lived). An "Optima-style" YLL using a fixed 80-year life expectancy is also computed (`dyll_Optima80`) for comparison. Published analyses typically report DALYs averted and "net DALYs averted" (DALYs averted minus incremental cost divided by a cost-effectiveness threshold, commonly $500 per DALY), choosing the policy that maximizes net DALYs across many sampled settings.
- **Analyses supported**: ICERs and net-health-benefit comparisons, often across hundreds of sampled "setting scenarios" that span parameter uncertainty and epidemic types; threshold analyses (maximum cost at which an intervention is cost-effective); budget impact over 50-year horizons.
- **Example**: unit costs and per-agent cost accumulation, verbatim from `hiv_synthesis_community_tld.sas` on [figshare](https://doi.org/10.6084/m9.figshare.24072609.v1). The unit costs appear to be in thousands of US dollars per year, divided by 4 for the 3-month step, with a 1.2 multiplier on drugs (presumably a supply-chain mark-up); this reading is inferred from the code, not from documentation.

```sas
* COSTS;

cost_zdv_a=(0.068/4)*1.2; 
cost_3tc_a=(0.015/4)*1.2; 
cost_ten_a=(0.028/4)*1.2; 
...
vis_cost_a=(.020); 
redn_in_vis_cost_vlm_supp = 0.010 ;
```

```sas
	art_cost=0;

    art_cost=(o_zdv*cost_zdv) + (o_ten*cost_ten) + (o_3tc*cost_3tc) + (o_nev*cost_nev) +
    (o_lpr*cost_lpr) + (o_dar*cost_dar) + (o_taz*cost_taz) + (o_efa*cost_efa) + (o_dol*cost_dol) ;

	if yrart=caldate{t} then art_cost = art_cost + art_init_cost;
```

```sas
discount = 1;
if caldate_never_dot ge &year_interv+1 then discount = 1/(1.03**(caldate_never_dot-(&year_interv+1)));
...
live_ddaly = (1 - util)*0.25*discount; 
...
_dcost = cost* discount;
_dart_cost = art_cost*discount ;
```

- **Strengths and limitations**:
    - Resource use is tracked as a costing study measures it (drug, test, visit), so new unit costs need no re-simulation if component sums are kept.
    - Utility is a per-agent state that combines conditions (the minimum across them), a reasonable pattern for multi-morbidity.
    - Costs, utilities, and discounting are mixed with disease logic in one ~19,000-line SAS program, and unit costs are constants in the code.
    - Not on a public version-control host; code is released as per-paper snapshots.

## EMOD-HIV

| Disease(s) | Paradigm | Language | Code | Key papers |
|---|---|---|---|---|
| HIV (network model with age-structured partnerships, cascade, PrEP, VMMC) | Agent-based, network | C++ engine, JSON configuration, Python/R analysis | [EMOD-Hub/EMOD](https://github.com/EMOD-Hub/EMOD) (see [emod.md](../approaches/emod.md)) | Meyer-Rath, Over, Klein, Bershteyn (2015), [CGD Working Paper 401](https://www.cgdev.org/publication/cost-and-cost-effectiveness-alternative-strategies-expand-treatment-hiv-positive-south); Sharma et al. (2021), [Lancet HIV](https://doi.org/10.1016/S2352-3018(20)30279-4); Wu et al. (2024), [Lancet HIV](https://doi.org/10.1016/S2352-3018(24)00239-x) |

EMOD-HIV (originally IDM, now community-maintained) has been used for South African treatment-expansion costing, point-of-care monitoring, PrEP, and lenacapavir analyses. Its costing has two layers: a minimal built-in mechanism, and the costing after the run that published analyses actually use.

- **What is costed**: in published analyses, health-system costs of testing, ART (drugs, labs, and service delivery), monitoring, PrEP, and related services, with unit costs from trial costing (e.g. the STREAM trial for point-of-care testing in [Sharma et al. 2021](https://doi.org/10.1016/S2352-3018(20)30279-4)) or bottom-up South African costing studies. Meyer-Rath et al. (2015) "separate outpatient cost into non-scale-dependent costs (drugs and laboratory tests) and scale-dependent cost (staff, space, equipment and overheads)", model the cost of production according to the expected number and size of clinics, and add the cost of creating and sustaining demand for testing and treatment ([CGD WP 401](https://www.cgdev.org/publication/cost-and-cost-effectiveness-alternative-strategies-expand-treatment-hiv-positive-south)).
- **How costs attach to the model**: built in, every intervention has a `Cost_To_Consumer` parameter ([`AntiretroviralTherapy.cpp`](https://github.com/EMOD-Hub/EMOD/blob/main/interventions/AntiretroviralTherapy.cpp#L92)), charged once each time the intervention is distributed to an agent ([`campaign/Interventions.cpp`](https://github.com/EMOD-Hub/EMOD/blob/main/campaign/Interventions.cpp#L164)) and summed into a "Campaign Cost" channel of the InsetChart report ([`Report.cpp`](https://github.com/EMOD-Hub/EMOD/blob/main/Eradication/Report.cpp#L101)). This per-distribution cost does not suit per-person-year costs of a continuous intervention like ART. In practice, EMOD-HIV analyses export person-time and event counts (people on ART by age, sex, and CD4; tests; initiations; deaths) from reports such as `ReportHIVByAgeAndGender` and apply unit costs and disability weights afterwards in R or Python. The analysis scripts for the cited papers do not appear to be public.
- **Health outcomes**: DALYs averted (disability weights by CD4/ART state and YLL), infections averted, and life-years; 3% discounting is typical. Wu et al. (2024) report infections averted, 5-year budget impact, and the maximum per-dose lenacapavir price at which it is cost-effective at a $500 per DALY threshold relative to oral PrEP only.
- **Analyses supported**: ICERs against thresholds; threshold-price analysis (solving for the unit cost that makes the ICER equal the threshold); budget impact; scale-dependent cost functions (Meyer-Rath et al.); stochastic variability reported as model-run intervals (e.g. "mean and 90% model variability of 250 runs" in Sharma et al.).
- **Example**: the built-in mechanism, verbatim from [`campaign/Interventions.cpp`](https://github.com/EMOD-Hub/EMOD/blob/main/campaign/Interventions.cpp#L158-L167):

```cpp
if( ic->GiveIntervention(this) )
{
    // Need to get Individual pointer from interventions container pointer. Try parent.
    IIndividualHumanEventContext * pIndiv = (context->GetParent())->GetEventContext();
    if( pICCO )
    {
        pICCO->notifyCampaignExpenseIncurred( cost_per_unit, pIndiv );
    }
    wasDistributed = true;
}
```

- **Strengths and limitations**:
    - A cost on the shared intervention code is the right place for per-event costs, and it is automatic once declared.
    - The built-in cost is per distribution only, with no per-person-time costs, no discounting, and a single output channel, so real analyses bypass it.
    - The Meyer-Rath work is the clearest HIV example of economies of scale in delivery (clinic size), which neither Optima nor Spectrum captures.
    - Costing scripts are typically project-specific and unpublished, so the economic layer is not reusable.

## HIV Modelling Consortium: common costing across models

| Disease(s) | Paradigm | Language | Code | Key papers |
|---|---|---|---|---|
| HIV (ART eligibility, treatment as prevention) | Twelve models: STDSIM, EMOD, Synthesis, Goals, PopART, and others; ABM and compartmental | Various | Not public as a set | Eaton et al. (2012), [HIV treatment as prevention: systematic comparison of mathematical models](https://doi.org/10.1371/journal.pmed.1001245), PLOS Medicine; Eaton, Menzies, Stover et al. (2014), [Health benefits, costs, and cost-effectiveness of earlier eligibility for adult antiretroviral therapy and expanded treatment coverage: a combined analysis of 12 mathematical models](https://doi.org/10.1016/S2214-109X(13)70172-4), Lancet Global Health; Hontelez et al. (2013), [elimination comparison of nine models](https://pmc.ncbi.nlm.nih.gov/articles/PMC3805487) |

The HIV Modelling Consortium is the best example of separating the *economic layer* from the *disease model* out of necessity: to compare twelve structurally different models, the costing had to be identical for each model's outputs.

- **What is costed**: health-system perspective, 2012 US dollars, four categories: service delivery to identify and link people to care; service delivery for people on ART or in pre-ART care; savings from reduced wider health-system use; and programmatic support and supply chain ([Eaton et al. 2014](https://pmc.ncbi.nlm.nih.gov/articles/PMC4114402)). Mark-ups were 20% on ARV drug costs for supply chain and 50% on all other costs for programmatic support; infrastructure costs were annualized over useful life. Country-specific unit costs accounted for price-level differences.
- **How costs attach to the model**: each model reported standardized outputs (person-years by CD4 and care state, tests, initiations), and a central team applied a common table of unit costs per person-year or per event: "Model outputs describing changes in healthcare utilisation were used to estimate changes in costs" ([Eaton et al. 2014](https://pmc.ncbi.nlm.nih.gov/articles/PMC4114402)). Costing is entirely after the run and works for any model.
- **Health outcomes**: DALYs from disability weights by state (untreated CD4 >350: 0.053; 200–350: 0.221; ≤200: 0.547; on ART: 0.053; TB: 0.331), compounded multiplicatively for comorbidity; 3% discounting of costs and benefits for ICERs. The 2012 treatment-as-prevention comparison used a cruder efficiency metric, person-years of ART per infection averted (5.8 to 18.7 across models over 8 years; [Eaton et al. 2012](https://doi.org/10.1371/journal.pmed.1001245)), a resource-use ratio, not a cost.
- **Analyses supported**: ICERs per DALY averted compared with 1× and 3× GDP per capita thresholds; cross-model ranges of cost and effect. Hontelez et al. (2013) compared projected costs of universal test and treat across nine models.
- **Example**: there is no code; the input structure is the unit-cost table (Table 2 of [Eaton et al. 2014](https://pmc.ncbi.nlm.nih.gov/articles/PMC4114402)): rows of "ARV drugs", "non-ARV ART costs", "pre-ART care (CD4 >350, 200–350, ≤200)", "healthcare utilisation for people not in care", "HIV testing and linkage" (general population and key populations), "end-of-life care", and "TB treatment"; columns by country; units per person-year or per event. The key piece of design is the *output contract*: the list of person-time and event counts every model had to produce.
- **Strengths and limitations**:
    - Shows that a standard output contract (person-time by state, event counts) plus a shared unit-cost table is enough for credible cross-model CEA, exactly the separation a general library should support.
    - Makes structural uncertainty visible, which single-model CEAs hide.
    - The HIV Modelling Consortium's later "fit-for-purpose" review noted that the big planning models (AEM, Goals, Optima) assume interventions act independently, so "interactions between programmes or technical and production efficiencies [could not] be adequately explored" (quoted in [Chiu et al. 2017](https://doi.org/10.1186/s12889-017-4023-3)).
    - Costing after the run cannot represent spending or capacity limits feeding back into the epidemic.

## South African HIV Investment Case (Thembisa + custom optimization)

| Disease(s) | Paradigm | Language | Code | Key papers |
|---|---|---|---|---|
| HIV and TB | Compartmental (Thembisa) with a separate cost model | Excel/C++ (Thembisa) plus custom cost and optimization models | Thembisa is distributed via [thembisa.org](https://www.thembisa.org/); the cost and optimization models are not public | Chiu, Johnson, Jamieson, Larson, Meyer-Rath (2017), [Designing an optimal HIV programme for South Africa](https://doi.org/10.1186/s12889-017-4023-3), BMC Public Health; Meyer-Rath et al. (2019), [The per-patient costs of HIV services in South Africa](https://doi.org/10.1371/journal.pone.0210497), PLOS ONE |

The South African Investment Case is a counterpoint to Optima: instead of a cost-coverage curve per program, it used a calibrated epidemic model, a bottom-up cost model, and a greedy optimization that adds the best option at each step.

- **What is costed**: per-patient costs of HIV services from a systematic review and South African costing studies (Meyer-Rath et al. 2019), including ART, testing, condoms, circumcision, PrEP, and other interventions, from a provider perspective.
- **How costs attach to the model**: a "custom cost model" applied to Thembisa outputs (patients on ART, tests, circumcisions, and so on) post hoc, with the epidemic model rerun for each intervention combination.
- **Health outcomes**: life-years saved and infections averted; cost per HIV or TB infection averted.
- **Analyses supported**: ICERs and an optimization that "iteratively added the most cost-effective intervention onto a rolling baseline before evaluating all remaining options" ([Chiu et al. 2017](https://doi.org/10.1186/s12889-017-4023-3)). Compared with a conventional league table (a ranking with each intervention against the same baseline), ICERs were on average 437% higher under the rolling-baseline method, showing substantial diminishing marginal returns from interaction and saturation.
- **Example**: no code is public. The method is a greedy expansion path: at each step, simulate every remaining intervention added to the current package, compute its ICER relative to the current package, add the best, repeat.
- **Strengths and limitations**:
    - Captures diminishing returns through the epidemic model itself (interactions and saturation), not an assumed cost-coverage curve.
    - Directly comparable to the standard league table, so it measures the bias from assuming independence.
    - Needs many full simulations (one per candidate per step), and each intervention is on or off at a fixed coverage, not continuously funded.

## STIsim logistics (Starsim)

| Disease(s) | Paradigm | Language | Code | Key papers |
|---|---|---|---|---|
| HIV and other STIs | Agent-based (Starsim) | Python | [starsimhub/stisim, `stisim/logistics`](https://github.com/starsimhub/stisim/tree/main/stisim/logistics) | None yet |

STIsim, the Starsim-based STI and HIV library, recently added a small logistics layer: products with a per-unit cost, finite or unlimited supplies, and a `SuppliedIntervention` class that draws down supply and accrues cost. It is the closest existing code to what a Starsim costing layer could build on.

- **What is costed**: per-dose or per-item product costs (e.g. doses of lenacapavir PrEP), with a `ProductCategory` (e.g. `PREP`) and a `DeliveryMode` (e.g. `SHOT`). No personnel, facility, or overhead costs; no health outcomes.
- **How costs attach to the model**: unit cost × quantity used, accrued during the simulation each time an intervention calls `use()`. Supplies can be shared across interventions, in which case the pool's `accrued_cost` is the total and each intervention's `accrued_cost` is its own share. Finite supplies also limit distribution: when supply runs short, it is split across eligibility groups in proportion to each group's coverage gap. This is the only exemplar here where a *quantity* (stock), not a *budget*, limits delivery.
- **Health outcomes**: none; DALYs or QALYs would come from separate analyzers.
- **Analyses supported**: accrued cost by intervention and by supply pool; supply-constrained scenarios.
- **Example**: verbatim from [`supply.py`](https://github.com/starsimhub/stisim/blob/main/stisim/logistics/supply.py):

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

- **Strengths and limitations**:
    - Costs attach where resources are used inside the intervention, attributed to the intervention and shared pool, the right level of detail for an agent-based model.
    - Stock-outs (finite supply) are a real logistics limit that budget-based models cannot express.
    - Accrued cost is one running total: no time series, discounting, cost categories, or per-person-time costs for continuous interventions.

## Others worth knowing

- **Back-of-envelope CEA dashboards.** The [herbeck/Lenacapavir](https://github.com/herbeck/Lenacapavir) Shiny app computes $/DALY averted for lenacapavir PrEP from incidence, product cost, lifetime treatment cost averted, and DALYs per infection, with the formula `daly_value <- ( ( (1 / incidence) * cost_len)  - cost_treatment) / dalys` (verbatim from [`app.R`](https://github.com/herbeck/Lenacapavir/blob/main/app.R)). This "number needed to treat × cost minus averted treatment cost" form is how many PrEP price thresholds are first estimated; some economic questions need no transmission model.
- **DRIVE (Barnabas group).** A deterministic compartmental model in MATLAB with health-economic analysis in R, applying unit costs per test and per patient-year on clinic or community ART and CD4-stratified hospitalization costs, with GBD 2019 disability weights, 80-year life expectancy, 3% discounting, and uncertainty propagated by repeating every calculation across the 25 best-fitting parameter sets ([Sahu et al. 2023](https://doi.org/10.1371/journal.pgph.0000610)). A typical example of costing after the run with calibration uncertainty carried through.
- **Open R HIV CEA models.** We found no widely used open-source R HIV CEA model with a reusable economic layer; EpiModelHIV ([EpiModel/EpiModelHIV](https://github.com/EpiModel/EpiModelHIV)) is the main open R HIV network model, but we did not verify whether it has cost or utility modules.

## Cross-cutting patterns

- **Two opposite directions of causality.** In Optima and Atomica, spending is the input and coverage is derived (spend → capacity → coverage → parameter); in Spectrum/RNM, HIV Synthesis, EMOD-HIV, and the Consortium work, coverage is the input and cost is derived (coverage × population × unit cost, or per-agent resource use × unit cost). A general library needs both, ideally from one declared unit cost, so a coverage scenario reports its cost and a budget scenario its coverage.
- **The cost function's shape is a modeling choice and should be declared.** Linear (RNM, Consortium, HIV Synthesis), linear-then-logistic saturation (Optima HIV, Atomica), increasing, decreasing, or S-shaped marginal cost (Optima Nutrition), and scale-dependent fixed costs by clinic size (Meyer-Rath et al.) all appear. Diminishing returns can sit in the cost function or emerge from epidemic dynamics (Chiu et al.); mixing them up double-counts.
- **One-off versus continuous costs.** Every model separates per-event costs (a test, an initiation, a circumcision) from per-person-time costs (ART per year). Atomica puts this in the units of the unit cost; EMOD natively supports only the per-event kind, so its analyses cost after the run. A general library should support both, with units checked against the time step.
- **After the run versus during it.** Costing after the run from a standard output contract (person-time by state, event counts) is enough for ICERs and enabled the twelve-model Consortium comparison; costing during the run is needed only when spending or supply limits delivery (Optima budgets, STIsim stock). The default should be after the run, with during-run costing as an option for constrained interventions.
- **Fine-grained resource use pays off.** HIV Synthesis records each drug, test, and visit separately, so unit costs can change without re-running; the Consortium had to define its outputs in advance. Recording resource *quantities* by category (not just total cost) is cheap and lets analyses be re-costed.
- **Health outcomes are usually state-based weights plus a YLL rule.** Disability weights or utilities by CD4/ART/comorbidity state (Optima, Consortium, DRIVE) or per-agent utility (HIV Synthesis); YLL against a fixed life expectancy (80 years in Optima, DRIVE, and HIV Synthesis's comparison metric), not a life table. Discounting at 3% is near-universal, but Optima HIV discounts only YLL by default. Comorbidity rules differ (multiplicative in the Consortium, minimum utility in HIV Synthesis) and should be explicit.
- **Optimization needs a budget-outcome interface, not just ICERs.** Allocative optimization (Optima, Atomica) needs adjustables (spending per program and year with bounds), objectives (weighted outcomes or cascade targets), constraints (total spend, possibly by year), and an inverse mode (minimum spend to hit a target). Greedy expansion paths (Chiu et al.) and threshold-price searches (Wu et al.) are the other two common decision procedures; all three loop over simulations with a cost function and could share code.
- **Program interactions are where models differ most.** Atomica's additive, random, and nested coverage interactions and combination effects are the most developed; Spectrum and the Consortium largely assume independence; agent-based models get interactions automatically because one agent receives several interventions. An agent-based library should use this instead of reimplementing Covout-style interaction rules.
- **Uncertainty comes from re-running.** Optima samples program parameters; HIV Synthesis samples hundreds of setting scenarios and reports net DALYs; DRIVE repeats costing across best-fitting parameter sets; EMOD reports run-to-run variability. Cost inputs should be distributions sampled jointly with epidemiological parameters, and "averted" quantities should use common random numbers.
- **Attribution matters for budgets.** STIsim attributes cost to intervention and shared supply pool; Spectrum to intervention and enabler categories with mark-ups; Optima to program. Costs should carry labels (intervention, category, payer, population) so one run can produce a program budget, a CEA cost total, and a budget-impact table.
