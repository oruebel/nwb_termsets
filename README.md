> **⚠️ WARNING:** This repository is a work in progress and is not intended for production use. The term sets and configuration provided here are subject to change.

# PyNWB default external-resource configuration

This directory provides ontology-backed term sets and a loader-compatible `default_config.yaml` for PyNWB users who want to validate common metadata against shared ontologies and atlases and automatically populate HERD annotations. 

## Installation

You can install this package directly using pip:

```bash
pip install -e .
```

## Usage

See `scripts/example_usage.py` for a complete example of how to use the termsets and generate a HERD table.

```python
import nwb_termsets
from pynwb import NWBFile
from pynwb.file import Subject

# Load the termset configuration into PyNWB
nwb_termsets.load_termset_config()

# Now when you create a Subject, the species will be validated against the NCBITaxon termset
subject = Subject(
    subject_id="sub-001",
    age="P90D",
    description="Example subject",
    species="Mus musculus",  # This is validated
    sex="M",
)
```

## Included resources

The shipped defaults are intentionally conservative:

- **Enabled by default:** shared ontologies that work well as cross-project validators.
- **Provided but not enabled by default:** comprehensive atlas-specific exports for mouse and human workflows.
- **Documented only:** registries that are recommended for HERD annotations but are not practical as a single shared global term set.


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

To support these resources, this package provides a script (`scripts/generate_lab_termsets.py`) that allows labs to generate their own custom term sets and configuration files based on a simple YAML manifest. This approach ensures that labs can validate their specific experimenters, institutions, and related publications without needing to maintain a massive, global list of all possible values.

## Files

- `default_config.yaml` wires the default term sets into PyNWB's type configuration. The term-set paths in `default_config.yaml` are relative on purpose. PyNWB resolves them relative to the configuration file, so the directory can be copied as a self-contained bundle.
- `term_sets/subject_species_ncbitaxon_termset.yaml` uses canonical NCBI Taxonomy labels for the species represented in the referenced public dataset table.
- `term_sets/brain_region_uberon_termset.yaml` contains the cross-species UBERON export used by the default configuration (`brain` plus descendants of `regional part of brain`).
- `term_sets/brain_region_mba_termset.yaml` contains the complete Allen Mouse Brain Atlas export.
- `term_sets/brain_region_hba_termset.yaml` contains the complete Allen Human Brain Atlas export.
- `scripts/generate_brain_region_termsets.py` regenerates the ontology-backed brain-region term sets.
- `scripts/README.md` documents the generator workflow and scope.

## Generating Lab-Specific Term Sets

For global registries like ORCID, ROR, and DANDI, it is recommended to generate lab-specific term sets rather than relying on a shared, exhaustive list. This package provides a command-line tool to generate these term sets from a simple YAML manifest.

1. Create a manifest file (e.g., `my_lab_resources.yaml`) based on the provided `lab_termsets/lab_resources_template.yaml`. You can look up identifiers at the following registries:
   - **ORCID** (Experimenters): [https://orcid.org/](https://orcid.org/)
   - **ROR** (Institutions): [https://ror.org/search](https://ror.org/search)
   - **DANDI** (Dandisets): [https://dandiarchive.org/](https://dandiarchive.org/)

```yaml
experimenter:
  source: orcid
  values:
    - orcid: 0000-0001-9902-1984

institution:
  source: ror
  values:
    - ror: 02jbv0t02

dandiset:
  source: dandi
  values:
    - dandiset_id: "001417"
```

2. Run the generator script:

```bash
python scripts/generate_lab_termsets.py --manifest my_lab_resources.yaml --outdir lab_termsets/my_lab_termsets
```

This will fetch canonical labels from the respective APIs and generate LinkML term set YAML files, along with a `lab_config.yaml` snippet.

### Using Lab-Specific Term Sets

You can use the generated lab-specific term sets in two ways:

**1. Loading the generated configuration:**

The generator creates a `lab_config.yaml` file that maps the term sets to the appropriate PyNWB fields. You can load this alongside the default configuration:

```python
import nwb_termsets
from pynwb import load_type_config

# Load default configuration
nwb_termsets.load_termset_config()

# Load lab-specific configuration
load_type_config('lab_termsets/my_lab_termsets/lab_config.yaml')
```

**2. Manually wrapping specific fields:**

If you prefer not to use the configuration file, you can manually wrap specific fields with a `TermSetWrapper` in your code:

```python
from hdmf.term_set import TermSetWrapper

# Use the generated experimenter term set
nwbfile.experimenter = [
    TermSetWrapper(
        value="Oliver Ruebel",
        termset="lab_termsets/my_lab_termsets/lab_experimenter_termset.yaml"
    )
]
```

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
