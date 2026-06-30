# PyNWB default external-resource configuration

> **⚠️ WARNING:** This repository is a work in progress and is not intended for production use. The term sets and configuration provided here are subject to change.

This directory provides ontology-backed term sets and a loader-compatible `default_config.yaml` for PyNWB users who want to validate common metadata against shared ontologies and atlases.

The shipped defaults are intentionally conservative:

- **Enabled by default:** shared ontologies that work well as cross-project validators.
- **Provided but not enabled by default:** comprehensive atlas-specific exports for mouse and human workflows.
- **Documented only:** registries that are recommended for HERD annotations but are not practical as a single shared global term set.

## Included resources

| Resource | Recommended use | NWB field(s) | Shipped term set | Enabled in `default_config.yaml` |
| --- | --- | --- | --- | --- |
| NCBITaxon | subject species | `Subject.species` | Yes | Yes |
| UBERON | cross-species anatomical locations | `ElectrodeGroup.location`, `ImagingPlane.location`, `IntracellularElectrode.location`, `OptogeneticStimulusSite.location` | Yes | Yes |
| MBA | mouse atlas locations | same `location` fields as above | Yes | No |
| HBA | human atlas locations | same `location` fields as above | Yes | No |
| ORCID | experimenters / people | `NWBFile.experimenter` | No | No |
| ROR | institutions / organizations | `NWBFile.institution` | No | No |
| DANDI | dandiset identifiers | file- or dataset-level annotations | No | No |

## Why ORCID, ROR, and DANDI are not in the default config

PyNWB's current type configurator expects each configured field to point at a finite LinkML term set file. That works well for shared ontology-backed vocabularies such as species and anatomical locations, but it is not a good fit for global registries such as ORCID and ROR or for project-specific DANDI identifiers. Those are still recommended external resources; they are simply better added directly through HERD annotations or through lab-specific term sets.

## Files

- `default_config.yaml` wires the default term sets into PyNWB's type configuration.
- `term_sets/subject_species_ncbitaxon_termset.yaml` uses canonical NCBI Taxonomy labels for the species represented in the referenced public dataset table.
- `term_sets/brain_region_uberon_termset.yaml` contains the cross-species UBERON export used by the default configuration (`brain` plus descendants of `regional part of brain`).
- `term_sets/brain_region_mba_termset.yaml` contains the complete Allen Mouse Brain Atlas export.
- `term_sets/brain_region_hba_termset.yaml` contains the complete Allen Human Brain Atlas export.
- `scripts/generate_brain_region_termsets.py` regenerates the ontology-backed brain-region term sets.
- `scripts/README.md` documents the generator workflow and scope.

## Usage

```python
import nwb_termsets

nwb_termsets.load_termset_config()
```

The term-set paths in `default_config.yaml` are relative on purpose. PyNWB resolves them relative to the configuration file, so the directory can be copied as a self-contained bundle.

## Regenerating generated term sets

The brain-region term sets are generated files. To regenerate them:

```bash
python scripts/generate_brain_region_termsets.py
```

See `scripts/README.md` for the exact scope, requirements, and generation rules.

## Customizing atlas choice

`default_config.yaml` uses the UBERON export because it is the safest cross-species default. If your project is consistently mouse- or human-specific, replace the UBERON file in the relevant `location` entries with:

- `term_sets/brain_region_mba_termset.yaml` for Allen Mouse Brain Atlas labels
- `term_sets/brain_region_hba_termset.yaml` for Allen Human Brain Atlas labels

Alternatively, you can manually wrap specific fields with a `TermSetWrapper` in your code without modifying the default configuration. This is useful if you want to use a specific atlas for only certain fields or files.

```python
from hdmf.term_set import TermSetWrapper
import nwb_termsets

# Use the Mouse Brain Atlas for a specific electrode group
electrode_group.location = TermSetWrapper(
    value="primary motor cortex",
    termset=nwb_termsets.get_termset_path("brain_region_mba_termset.yaml")
)
```

## Scope note

These term sets are meant to be immediately usable and easy to extend. The location files are generated comprehensive ontology or atlas exports, while the species file is intentionally scoped to the species requested for this task and is maintained separately. They do not currently auto-configure table-column values such as the `electrodes.location` column. For those cases, extend the term set or annotate values directly with HERD.
