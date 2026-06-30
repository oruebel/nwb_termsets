# Scripts

This directory contains various Python scripts for generating term sets and demonstrating usage of the `nwb-termsets` package.

## Available Scripts

### 1. `generate_brain_region_termsets.py`

This script generates ontology-backed brain-region term sets by querying the EMBL-EBI OLS4 API.

**Generated files:**
- `../term_sets/brain_region_uberon_termset.yaml`
- `../term_sets/brain_region_mba_termset.yaml`
- `../term_sets/brain_region_hba_termset.yaml`

*(Note: It does **not** regenerate `../term_sets/subject_species_ncbitaxon_termset.yaml`. That file is intentionally maintained separately because it is scoped to a curated set of species required for this task rather than a full ontology export.)*

**Generation rules:**
- **UBERON** exports `brain` plus descendants of `regional part of brain`, which is the cross-species default used by `default_config.yaml`.
- **MBA** exports all non-obsolete `MBA:*` terms from the Allen Mouse Brain Atlas ontology.
- **HBA** exports all non-obsolete `HBA:*` terms from the Allen Human Brain Atlas ontology.
- Descriptions use ontology-provided description text when available.
- If an ontology term lacks a description, the script falls back to a term-specific description built from the label, identifier, and up to three synonyms.
- When HBA or MBA reuse the same visible label for multiple terms, the script disambiguates the exported label by appending the ontology identifier in brackets.

### 2. `generate_lab_termsets.py`

This script generates lab-specific term sets based on a template. It allows labs to define their own custom term sets for experimenters, devices, and other lab-specific metadata.

**Generated files:**
- `../lab_termsets/my_lab_termsets/my_lab_experimenter_termset.yaml`
- `../lab_termsets/my_lab_termsets/my_lab_device_termset.yaml`
- `../lab_termsets/my_lab_termsets/my_lab_config.yaml`

### 3. `example_usage.py`

This script demonstrates how to use the `nwb-termsets` package to create an NWB file with term sets applied. It shows how to load the default configuration, create NWB objects (like `Subject` and `NWBFile`), and write the file to disk.

**Generated files:**
- `example_termsets.nwb` (in the root directory, ignored by git)

## Requirements

- Python 3
- `PyYAML` (for generation scripts)
- `pynwb`, `hdmf`, `linkml-runtime` (for `example_usage.py`)
- Network access to the EMBL-EBI OLS4 API (for `generate_brain_region_termsets.py`)

## Usage

From the repository root:

```bash
# Generate brain region term sets
python scripts/generate_brain_region_termsets.py

# Generate lab term sets
python scripts/generate_lab_termsets.py

# Run the example usage script
python scripts/example_usage.py
```
