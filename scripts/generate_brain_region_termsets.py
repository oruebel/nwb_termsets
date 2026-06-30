#!/usr/bin/env python
"""Generate ontology-backed brain-region term sets for ``bbqs_config``.

This script regenerates the three ontology/atlas-backed term sets in
``bbqs_config/term_sets``:

* ``brain_region_uberon_termset.yaml``
* ``brain_region_mba_termset.yaml``
* ``brain_region_hba_termset.yaml``

The species term set is intentionally maintained separately because it is
scoped to a curated species list rather than a full ontology export.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Iterator
from urllib.request import urlopen

import yaml


ROOT = Path(__file__).resolve().parent.parent
TERMSET_DIR = ROOT / 'term_sets'


def fetch_json(url: str) -> dict:
    """Fetch a JSON document from the given URL."""
    with urlopen(url) as response:
        return json.load(response)


def iter_ols_pages(url: str) -> Iterator[dict]:
    """Yield OLS term records across all pages starting from ``url``."""
    while url:
        data = fetch_json(url)
        for term in data.get('_embedded', {}).get('terms', []):
            yield term
        url = data.get('_links', {}).get('next', {}).get('href')


def normalize_text(text: str) -> str:
    """Normalize whitespace in ontology-provided text fields."""
    return ' '.join(str(text).split()).strip()


def fallback_description(source_name: str, label: str, obo_id: str) -> str:
    """Build a term-specific fallback description when no ontology text exists."""
    return f"{source_name} region '{label}' ({obo_id})."


def get_description(term: dict, source_name: str) -> str:
    """Return a useful per-term description from ontology metadata.

    Preference order:
    1. First non-empty ontology description.
    2. A label/identifier-based fallback with up to three synonyms.
    3. A label/identifier-based fallback without synonyms.
    """
    for description in term.get('description') or []:
        description = normalize_text(description)
        if description:
            return description

    label = term['label']
    obo_id = term['obo_id']
    synonyms = [normalize_text(s) for s in (term.get('synonyms') or []) if normalize_text(s)]
    if synonyms:
        return f"{fallback_description(source_name, label, obo_id)} Synonyms: {', '.join(synonyms[:3])}."
    return fallback_description(source_name, label, obo_id)


def write_termset(
    path: Path,
    *,
    termset_id: str,
    name: str,
    prefix_name: str,
    prefix_reference: str,
    enum_name: str,
    entries: list[tuple[str, str, str]],
) -> None:
    """Write a LinkML enum schema to ``path`` from prepared term entries."""
    document = {
        'id': termset_id,
        'name': name,
        'version': '0.1.0',
        'prefixes': {prefix_name: prefix_reference},
        'imports': ['linkml:types'],
        'default_range': 'string',
        'enums': {
            enum_name: {
                'permissible_values': {
                    label: {
                        'description': description,
                        'meaning': obo_id,
                    }
                    for label, obo_id, description in entries
                }
            }
        },
    }
    with path.open('w', encoding='utf-8') as file:
        yaml.safe_dump(document, file, sort_keys=False, allow_unicode=False, width=1000)


def generate_uberon_termset() -> None:
    """Generate the cross-species UBERON brain-region term set.

    The export includes the root ``brain`` term plus descendants of
    ``regional part of brain``, which is the cross-species default used by
    ``bbqs_config/default_config.yaml``.
    """
    source_name = 'UBERON'
    entries_by_label: dict[str, tuple[str, str]] = {}

    for url in (
        'https://www.ebi.ac.uk/ols4/api/ontologies/uberon/terms/'
        'http%253A%252F%252Fpurl.obolibrary.org%252Fobo%252FUBERON_0000955',
        'https://www.ebi.ac.uk/ols4/api/ontologies/uberon/terms/'
        'http%253A%252F%252Fpurl.obolibrary.org%252Fobo%252FUBERON_0002616',
    ):
        term = fetch_json(url)
        obo_id = term.get('obo_id', '')
        if obo_id.startswith('UBERON:'):
            entries_by_label[term['label']] = (obo_id, get_description(term, source_name))

    descendants_url = (
        'https://www.ebi.ac.uk/ols4/api/ontologies/uberon/terms/'
        'http%253A%252F%252Fpurl.obolibrary.org%252Fobo%252FUBERON_0002616/descendants?size=500'
    )
    for term in iter_ols_pages(descendants_url):
        if term.get('is_obsolete'):
            continue
        obo_id = term.get('obo_id', '')
        if not obo_id.startswith('UBERON:'):
            continue
        entries_by_label.setdefault(term['label'], (obo_id, get_description(term, source_name)))

    entries = [
        (label, obo_id, description)
        for label, (obo_id, description) in sorted(entries_by_label.items(), key=lambda item: item[0].casefold())
    ]
    write_termset(
        TERMSET_DIR / 'brain_region_uberon_termset.yaml',
        termset_id='termset/nwb_brain_regions_uberon',
        name='NWBBrainRegionsUberon',
        prefix_name='UBERON',
        prefix_reference='http://purl.obolibrary.org/obo/UBERON_',
        enum_name='BrainRegions',
        entries=entries,
    )


def generate_atlas_termset(
    *,
    ontology: str,
    source_name: str,
    id_prefix: str,
    prefix_name: str,
    prefix_reference: str,
    output_name: str,
    termset_id: str,
    schema_name: str,
    enum_name: str,
) -> None:
    """Generate a complete atlas export for MBA or HBA.

    Labels are disambiguated with ``[OBO_ID]`` when the ontology reuses the
    same visible label for multiple atlas terms.
    """
    terms = []
    for term in iter_ols_pages(f'https://www.ebi.ac.uk/ols4/api/ontologies/{ontology}/terms?size=500'):
        if term.get('is_obsolete'):
            continue
        obo_id = term.get('obo_id', '')
        if obo_id.startswith(id_prefix):
            terms.append(term)

    duplicate_labels = {
        label for label, count in Counter(term['label'] for term in terms).items()
        if count > 1
    }
    entries = []
    for term in terms:
        label = term['label']
        if label in duplicate_labels:
            label = f"{label} [{term['obo_id']}]"
        entries.append((label, term['obo_id'], get_description(term, source_name)))
    entries.sort(key=lambda item: item[0].casefold())

    write_termset(
        TERMSET_DIR / output_name,
        termset_id=termset_id,
        name=schema_name,
        prefix_name=prefix_name,
        prefix_reference=prefix_reference,
        enum_name=enum_name,
        entries=entries,
    )


def main() -> None:
    """Parse arguments and regenerate all ontology-backed brain-region term sets."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()

    generate_uberon_termset()
    generate_atlas_termset(
        ontology='mba',
        source_name='Allen Mouse Brain Atlas',
        id_prefix='MBA:',
        prefix_name='MBA',
        prefix_reference='https://purl.brain-bican.org/ontology/mbao/MBA_',
        output_name='brain_region_mba_termset.yaml',
        termset_id='termset/nwb_brain_regions_mba',
        schema_name='NWBBrainRegionsMBA',
        enum_name='MouseBrainRegions',
    )
    generate_atlas_termset(
        ontology='hba',
        source_name='Allen Human Brain Atlas',
        id_prefix='HBA:',
        prefix_name='HBA',
        prefix_reference='https://purl.brain-bican.org/ontology/hbao/HBA_',
        output_name='brain_region_hba_termset.yaml',
        termset_id='termset/nwb_brain_regions_hba',
        schema_name='NWBBrainRegionsHBA',
        enum_name='HumanBrainRegions',
    )


if __name__ == '__main__':
    main()
