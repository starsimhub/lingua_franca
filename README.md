# A lingua franca for epi modeling

**Version:** 1.9 | **Date:** 2026-11-06 | **Status:** [Prerelease](https://pypi.org/project/starsim/#history)

## Introduction

This project describes the design of a _lingua franca_ for epidemiological modeling (a.k.a. disease modeling or infectious disease dynamics). The vision for the lingua franca is to:

- Capture the best aspects of many existing epi modeling frameworks (in terms of flexibility, simplicity, and elegance), and improve upon them when possible. In other words, **a model should always be easier to write with the lingua franca than without it**. For example, compared to existing epi models, implementing a model in the lingua franca should require no more lines of code than the original, and be as fast or faster.
- Provide a unified representation across different modeling paradigms, including at least:
    - Compartmental/ODE models
    - Stochastic compartmental/SDE models
    - Metapopulation models
    - Agent-based models
- Allow low- to zero-effort interconversion between modeling frameworks (e.g. EpiModel to epydemix) and paradigms (e.g. compartmental to agent-based).
- Be AI-native, serving as a rigorous-yet-simple and deterministic representation of modeling concepts (as expressed via code with other modeling frameworks, or even as prose) into a single consistent code representation.

## Motivation

Why do we need a lingua franca? What's wrong with existing modeling frameworks? And why can't LLMs just write disease models directly?

- Unlike other fields such as neuroscience or astrophysics, epi modeling frameworks haven't captured a significant "market share". This is most likely because of the diversity of the epi modeling landscape, and because existing frameworks tend to work well for some things and poorly or not at all at others. A lingua franca would remove these barriers. (A humbling caveat is that there have been many previous attempts to do this, without much success.)
- While AI certainly _can_ write epi models, even quite complex ones, it does not necessarily do it quickly or rigorously. AI is most efficient and accurate as a thin wrapper for code that already provides most desired functionality; imagine an LLM trying to correctly do a dataframe merge without access to R or `pandas`: it probably could, but would be slow, expensive, and would likely mangle edge cases.
- A lingua franca serves as a rigorous source of truth for comparing other models to, and provides a robust platform for developing AI tools (e.g. skills, guardrails, evals, and harnesses). If a compartmental model written in R with EpiModel gives a different result than an agent-based model written in Python in Vivarium, currently it's extremely difficult to understand why. A lingua franca allows the differences between models to be clarified and explored.

## Standing on the shoulders of giants

We have been using AI tools to summarize and evaluate the existing disease modeling landscape. Because of this, the lingua franca owes its existence to the many years (and hundreds of thousands of hours) of human contributors; see [Influences](docs/approaches/influences.qmd) for where we have incorporated ideas from other models. We can be (somewhat) confident that a lingua franca based on existing models can do *at least as well* as them in terms of performance and brevity. While AI is not always very creative, it is the perfect tool for this task: it can impartially review all existing models, see who did it "best" (using human-specified criteria for what that means), and at minimum copy that implementation (and improve upon it where possible).

Because of this, we acknowledge our indebtedness to the broader disease modeling community, and inclusiveness is one of our core principles. (More bluntly: we do not want to be the AI jerks who steal other people's work and pass it off as our own!) We are in the process of reaching out to authors of the disease modeling frameworks we borrowed from, but please [get in touch](mailto:info@starsim.org) if we haven't written to you yet.

## Relationship to Starsim

Although the lingua franca aims to reflect a "consensus" view of disease modeling approaches, we needed a concrete basis to start from. We used Starsim as the basis for the lingua franca for two reasons. First, because we're biased (a downside of human involvement in these projects!). Second, because agent-based modeling is the most complex paradigm; all models can be expressed as agent-based models, and of course real diseases act on agents (humans and/or other animals), so in a sense agent-based models are already a disease modeling lingua franca, even though the majority of epi models are written as ODEs in practice.

The lingua franca will be released as Starsim v4 (so "lingua franca", "Starsim", and "v4" are all synonyms), planned for the end of 2026. You can see the [current code](https://github.com/starsimhub/starsim/tree/v4) and the draft [PR #1437](https://github.com/starsimhub/starsim/pull/1437). The prerelease version is also available on [PyPI](https://pypi.org/project/starsim/#history); you can try it out with `pip install starsim --pre`. We are also currently working on a publication. We enthusiastically invite the disease modeling community to [join us](mailto:info@starsim.org) as both code contributors and coauthors. 

## Project structure

The lingua franca was built up in stages:

| | Section | What it is |
|---|---|---|
| 1 | [Approaches](docs/approaches/) | A review of the current approaches used in the epi modeling landscape, based on the [disease modeling landscape](https://starsim.org/disease_modeling_landscape) |
| 2 | [Best practices](docs/best-practices/) | A distillation of the modeling landscape into best practices for each aspect of building disease models |
| 3 | [Design](docs/design/) | The design of the language, written as an extension of Starsim |
| 4 | [Models](docs/models/) | Other frameworks' own example models, and their translations into Starsim v4 |
| 5 | [Compare](docs/webapp/) | A tool for comparing example models between the original source and the lingua franca |
| 6 | [Benchmark](docs/benchmark/) | One script that regenerates every line count, run time, and check of agreement between the originals and the lingua franca |

## Development notes

To run the tests and benchmark, install this repo with `pip install -e . --group starsim` (or just `pip install -e .` to use a Starsim you already have), then:

- `lingua_franca test [conversion|switching|threading|all]` runs the tests.
- `lingua_franca benchmark` checks the north star: it counts each model's lines, times it against the original, checks that their results agree, and ends with a scorecard of what passes and fails. `--stages tables` prints the scorecard again from the last run, and `--out` saves it. See [the benchmark](docs/benchmark/README.md).
- `lingua_franca envs install` builds the frameworks' environments into `_envs/` from the recipes in `docs/models/<framework>`, and `python scripts/clean_envs.py` deletes them.

The site's source is in `docs/`, and is built with `quarto render docs`. `scripts/` holds what the pages call as they are rendered, `skills/` the skills that review v4, and `tests/reviews/` the targets they check and their reports.

The [status page](docs/admin/implementation.md) tracks how much has been implemented so far. This site explains how and why the design came about; to use Starsim v4, see its [documentation](https://starsim.org/v4/).

## The design record

This repo is the design record of Starsim v4, which moved here from the `v4_design/` folder of the Starsim repo on 2026-10-31; older text that mentions `v4_design/` means this record. What governs, and what is current:

1. [Constitution](docs/admin/constitution.md): the principles every choice is checked against.
2. [Targets](tests/reviews/targets.md): what v4 has to achieve, model by model.
3. [Design](docs/design/): the spec, kept in line with the code.
4. The working plan, now [docs/admin/oct31/plan.md](docs/admin/oct31/plan.md).
5. [Deferred](docs/admin/deferred.md): what was set aside, and "Won't do", what was decided against. What is done is recorded in each plan.

Starsim's code, tests, and user docs stay in the [Starsim repo](https://github.com/starsimhub/starsim/tree/v4). The dated folders of older plans and reviews (e.g. `v4_design/oct17/`) are not kept in either repo: the ones in git are at [this commit](https://github.com/starsimhub/starsim/tree/77adec1df60be8ebd30d6d65bd5c7cb2abafdbfb/v4_design) of Starsim, and links to them from [deferred.md](docs/admin/deferred.md) and elsewhere are left as a record.

## AI disclaimer

AI tools (mostly Claude) were used to summarize information, compare and assess frameworks, extract code examples, and create translations. Assessments and design decisions are owned by the humans. Authorship for each page is listed in a little note like this:

[*Authorship:* 🧠 95%, 🤖 5%](# "Humans wrote the text, AI wrote the lists")
