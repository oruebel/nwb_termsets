# Brain-region term-set generators

This directory contains the Python generator used for the ontology-backed brain-region term sets in `../term_sets/`.

## Generated files

Running `generate_brain_region_termsets.py` regenerates:

- `../term_sets/brain_region_uberon_termset.yaml`
- `../term_sets/brain_region_mba_termset.yaml`
- `../term_sets/brain_region_hba_termset.yaml`

It does **not** regenerate `../term_sets/subject_species_ncbitaxon_termset.yaml`. That file is intentionally maintained separately because it is scoped to a curated set of species required for this task rather than a full ontology export.

## Requirements

- Python 3
- `PyYAML`
- network access to the EMBL-EBI OLS4 API

## Usage

From the repository root:

```bash
python bbqs_config/scripts/generate_brain_region_termsets.py
```

The script writes the YAML files directly into `bbqs_config/term_sets/`.

## Generation rules

- **UBERON** exports `brain` plus descendants of `regional part of brain`, which is the cross-species default used by `default_config.yaml`.
- **MBA** exports all non-obsolete `MBA:*` terms from the Allen Mouse Brain Atlas ontology.
- **HBA** exports all non-obsolete `HBA:*` terms from the Allen Human Brain Atlas ontology.
- Descriptions use ontology-provided description text when available.
- If an ontology term lacks a description, the script falls back to a term-specific description built from the label, identifier, and up to three synonyms.
- When HBA or MBA reuse the same visible label for multiple terms, the script disambiguates the exported label by appending the ontology identifier in brackets.
