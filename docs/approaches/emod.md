---
authorship:
  human: 0
  ai: 100
  note: Written by AI
---

# EMOD

|  |  |
|---|---|
| **Language** | C++ engine; models specified entirely in JSON; Python tooling (`emod-api`, `emodpy-*`) |
| **Paradigms** | Agent-based (individual-based), with node-level metapopulation structure and migration |
| **Specification style** | Three JSON documents against a published schema: `config.json`, `campaign.json`, `demographics.json` |
| **Version reviewed** | EMOD-Hub community fork |
| **License** | MIT |
| **Code** | <https://github.com/EMOD-Hub/EMOD> |
| **Docs** | <https://emod-hub.github.io/> |
| **Paper** | [10.1093/femspd/fty059](https://doi.org/10.1093/femspd/fty059) |
| **Status** | **Retired by IDM**; maintained by the community EMOD-Hub organization |

## What it's for

EMOD is a multi-disease individual-based transmission platform (malaria, HIV, TB, typhoid, polio, and generic respiratory) in which the *entire model is data*. There is one C++ program, and a model is three JSON files. Adding a vaccination campaign, changing the demographics, or switching disease means editing JSON, not writing code.

It is included despite being retired because it is **the largest and longest-running experiment in writing models entirely as checked data files** in infectious disease modeling, and this project owes much to what it showed, both good and bad.

## How a model is specified

**`config.json`**: simulation parameters, validated against a published schema.

**`demographics.json`**: nodes, populations, age distributions, and *Individual Properties*, which are user-defined categories (`Risk: HIGH/MEDIUM/LOW`, `Accessibility: YES/NO`) that agents carry and that interventions can target.

**`campaign.json`**: everything that happens to people. This is the interesting one:

```json
{
  "Events": [{
    "class": "CampaignEvent",
    "Start_Day": 10,
    "Nodeset_Config": { "class": "NodeSetAll" },
    "Event_Coordinator_Config": {
      "class": "StandardInterventionDistributionEventCoordinator",
      "Number_Repetitions": 5,
      "Timesteps_Between_Repetitions": 20,
      "Target_Demographic": "Everyone",
      "Demographic_Coverage": 0.2,
      "Targeting_Config": {
        "class": "TargetingLogic",
        "Logic": [
          [ { "class": "HasIntervention", "Is_Equal_To": 0, "Intervention_Name": "MyVaccine" } ],
          [ { "class": "HasIP", "Is_Equal_To": 1, "IP_Key_Value": "Risk:HIGH" } ]
        ]
      },
      "Intervention_Config": {
        "class": "SimpleVaccine",
        "Intervention_Name": "MyVaccine",
        "Vaccine_Take": 1,
        "Vaccine_Type": "AcquisitionBlocking",
        "Waning_Config": { "class": "WaningEffectConstant", "Initial_Effect": 1.0 }
      }
    }
  }]
}
```

## The campaign grammar

This is EMOD's main contribution, and the reason it is in this review. A campaign event has four independent parts:

| Part | Question it answers | Examples |
|---|---|---|
| **Nodeset_Config** | *Where?* | `NodeSetAll`, `NodeSetNodeList`, `NodeSetPolygon` |
| **Event_Coordinator_Config** | *When, to how many, how often?* | `Start_Day`, `Number_Repetitions`, `Timesteps_Between_Repetitions`, `Demographic_Coverage`, `Target_Demographic`; coordinators include `NChooser` (target a number, not a fraction), triggered coordinators, and reference-tracking coordinators |
| **Targeting_Config** | *To whom?* | `TargetingLogic`, which combines conditions with AND and OR: `HasIntervention`, `HasIP`, `IsPregnant`, `HasRelationship`, … |
| **Intervention_Config** | *What is delivered?* | `SimpleVaccine`, `OutbreakIndividual`, `SimpleDiagnostic`, `AntimalarialDrug`, plus a `Waning_Config` describing how efficacy decays |

Each part can be swapped alone. Change `Targeting_Config` and the same vaccine goes to a different group; change `Intervention_Config` and the same schedule delivers a different product.

Two pieces stand out.

**`Targeting_Config` states who is eligible, as data.** `Logic` is a list of lists: each inner list is a set of alternatives (OR), and all the lists have to hold (AND), using named conditions that can be checked. "People who do not already have MyVaccine, AND are Risk:HIGH" is data that can be read, saved, and compared. Starsim 3's `eligibility` function and EpiModel's scenario tables could not express this, and both reviews flag the gap.

**`Waning_Config` separates efficacy from its decay.** A vaccine's initial effect and its waning profile are separate named objects (`WaningEffectConstant`, `WaningEffectExponential`, or `WaningEffectMapPiecewise` with a `Durability_Map` of times and values). Starsim 4's products (`ss.Vaccine(waning=...)`) do this too, and owe the idea to EMOD among others; EMOD's version is the more complete.

## Core abstractions

| Concept | EMOD name | Notes |
|---|---|---|
| Agent | Individual | Age, sex, and disease state fixed by the C++ build |
| Agent attribute | Individual Property (IP) | User-defined categorical, declared in demographics, targetable and transition-able |
| Node attribute | Node Property (NP) | Same, for nodes |
| Disease | compiled into the executable | **Not** specifiable in JSON: this is the boundary |
| Node | entry in demographics | Population, geography, and migration links |
| Campaign event | `CampaignEvent` | Nodeset × coordinator × targeting × intervention |
| Product | `Intervention_Config` class | With `Waning_Config` and `Cost_To_Consumer` |
| Eligibility | `Targeting_Config` | Conditions written as data |
| Trigger | broadcast/observe event strings | Interventions can listen for events (`NewInfectionEvent`) and fire in response |
| Schema | published JSON schema | `emod-api` reads it; tooling is generated from it |

## The boundary: what is data and what is not

The disease model itself is C++. Compartments, progression, and transmission for malaria or HIV are compiled in, and JSON sets their parameters. So in EMOD everything above the disease is data and the disease is fixed in code. This is the reverse of camdl, odin, and summer2, where the disease structure is what the modeler writes and interventions are absent.

This split runs through the whole review, and EMOD sits at one end of it.

## Strengths

- **The model is data.** Three JSON documents and a published schema (a formal list of what the files may contain), with no compiling to run a new scenario. Tools, checks, and generated files all follow from that.
- **The four-part campaign structure** (where × when and how many × to whom × what) is the fullest breakdown of an intervention in the review.
- **`Targeting_Config`**: eligibility as data, from named conditions on agent state combined with AND and OR.
- **`Waning_Config`**: a separate, named efficacy decay, including piecewise maps.
- **Individual Properties**: user-defined categories, declared in demographics, that interventions can target and that agents can move between. They add a stratifying attribute without touching the engine.
- **Event broadcast and observation**, so model events can trigger interventions, as well as schedules.
- **A published schema**, which made the `emod-api` / `emodpy` Python layer possible.
- **Multi-disease from one engine**, with shared configuration terms.
- **National-scale deployment** in real program planning.

## Limitations

- **Retired by its originating institution.** IDM has confirmed it is no longer supported; commits since come from the community EMOD-Hub organization.
- **The disease model is not specifiable.** New disease structure means C++ and a rebuild. The schema covers everything except the thing this project most wants to specify.
- **JSON is hard to write by hand.** It has no comments (the regression files use `"COMMENT1"` keys) and no expressions, nesting runs deep, and each object's kind is a `"class"` string. A three-level campaign event is hard to read and harder to review. EMULSION has the same problem with YAML, and here the documents are bigger.
- **A very large number of parameters.** The config schema runs to hundreds of parameters with subtle interdependencies, and `"Use_Defaults": 1` means much of a model's behavior is not visible in its files.
- **No dimensional types.** `Start_Day`, `Timesteps_Between_Repetitions`, and rates are all bare numbers.
- **Verbose.** The two-event campaign quoted above is 60 lines of JSON for "seed an outbreak and vaccinate 20% of high-risk people who are not already vaccinated, five times, twenty days apart".
- **No observation model** in the specification; reporters are configured separately.
- **Heavy build and run**, with a C++ executable, MPI, and a substantial Python workflow layer.

## Implications for the lingua franca

1. **Adopt the four-part intervention structure.** *Where* (nodes) × *when and how much* (schedule and coverage) × *to whom* (eligibility) × *what* (product with efficacy and waning). EMOD has the fullest version. Starsim's delivery/product split covers parts two and four, and camdl's `transfer` covers part four. This should go into the design essentially as EMOD has it.
2. **Eligibility should be a declared condition, and EMOD shows what that looks like.** Named conditions on agent state (`HasIntervention`, `HasIP`, `IsPregnant`), combined with explicit logic. This closes the gap in the Starsim and EpiModel reviews, and lets an intervention be compared, drawn, and generated from prose, which a Python function does not.
3. **Efficacy and its waning are separate objects.** `Vaccine_Take`, `Vaccine_Type` (acquisition-, transmission-, or mortality-blocking), and `Waning_Config` are three independent facts about a vaccine. Any set of products should have this shape.
4. **User-defined agent categories are the right way to extend a model.** Individual Properties let a modeler add `Risk`, `Accessibility`, or `Insurance` without touching the engine, and target them. This is the agent-based counterpart to a stratification, and the lingua franca should treat the two as one concept at different levels of aggregation, as MetaCast and EMULSION also suggest.
5. **Triggered interventions need a place in the vocabulary.** With EMOD's broadcast and observe events, "when a new infection is observed, trigger contact tracing" can be written as data. Most frameworks make this a function called from the code. camdl has scheduled and reactive interventions, and the lingua franca needs both.
6. **EMOD is the cautionary half of the model-as-data argument.** What works follows from the schema, and what is painful follows from writing JSON by hand. With EMULSION's YAML, the lesson is the same twice over: **a data format is a good thing to generate and a hard thing to write.** The lingua franca needs a readable language with a standard data form underneath, as camdl has.
7. **Note where the boundary fell, and why.** EMOD made everything data except the disease model, because that is where the performance and the complexity are. This project has to cross that boundary, and EMOD's history suggests that crossing it is the hard part.
