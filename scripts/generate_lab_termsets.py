#!/usr/bin/env python
"""Generate lab-specific term sets from a manifest file.

This script reads a YAML manifest containing ORCID, ROR, and DANDI identifiers,
fetches canonical labels from their respective APIs, and generates LinkML term sets
and a PyNWB configuration snippet.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError

import yaml

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def fetch_json(url: str, headers: dict = None) -> dict:
    """Fetch a JSON document from the given URL."""
    req = Request(url, headers=headers or {})
    try:
        with urlopen(req) as response:
            return json.load(response)
    except HTTPError as e:
        logger.error(f"HTTP Error {e.code} fetching {url}")
        return {}
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        return {}

def resolve_orcid(orcid: str) -> tuple[str, str]:
    """Resolve an ORCID to a name and description."""
    url = f"https://pub.orcid.org/v3.0/{orcid}"
    headers = {"Accept": "application/json"}
    data = fetch_json(url, headers)
    
    if not data:
        return orcid, f"ORCID {orcid}"
        
    person = data.get("person", {})
    name_data = person.get("name", {})
    
    given_names = name_data.get("given-names", {}).get("value", "") if name_data.get("given-names") else ""
    family_name = name_data.get("family-name", {}).get("value", "") if name_data.get("family-name") else ""
    
    name = f"{given_names} {family_name}".strip()
    if not name:
        name = orcid
        
    return name, f"ORCID {orcid} for {name}"

def resolve_ror(ror: str) -> tuple[str, str]:
    """Resolve a ROR ID to an institution name and description."""
    # ROR IDs can be full URLs or just the ID part
    ror_id = ror.split("/")[-1] if "/" in ror else ror
    url = f"https://api.ror.org/organizations/https://ror.org/{ror_id}"
    data = fetch_json(url)
    
    if not data:
        return ror, f"ROR {ror}"
        
    name = data.get("name", ror)
    return name, f"ROR {ror} for {name}"

def resolve_dandi(dandiset_id: str) -> tuple[str, str]:
    """Resolve a DANDI set ID to a title and description."""
    url = f"https://api.dandiarchive.org/api/dandisets/{dandiset_id}/"
    data = fetch_json(url)
    
    if not data:
        return f"DANDI:{dandiset_id}", f"DANDI set {dandiset_id}"
        
    # Try to get the title from the most recent version
    most_recent_version = data.get("most_recent_published_version") or data.get("draft_version", {})
    title = most_recent_version.get("name", f"DANDI:{dandiset_id}")
    
    return title, f"DANDI set {dandiset_id}: {title}"

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
                        'meaning': meaning,
                    }
                    for label, meaning, description in entries
                }
            }
        },
    }
    with path.open('w', encoding='utf-8') as file:
        yaml.safe_dump(document, file, sort_keys=False, allow_unicode=False, width=1000)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path, help="Path to the lab resources manifest YAML file")
    parser.add_argument("--outdir", type=Path, default=Path("."), help="Directory to write generated files to")
    args = parser.parse_args()

    if not args.manifest.exists():
        logger.error(f"Manifest file not found: {args.manifest}")
        sys.exit(1)

    args.outdir.mkdir(parents=True, exist_ok=True)

    with args.manifest.open("r") as f:
        manifest = yaml.safe_load(f)

    config_entries = []

    # Process Experimenters (ORCID)
    if "experimenter" in manifest and manifest["experimenter"].get("source") == "orcid":
        logger.info("Processing ORCIDs...")
        entries = []
        for item in manifest["experimenter"].get("values", []):
            orcid = item.get("orcid")
            if not orcid:
                continue
            logger.info(f"  Resolving {orcid}...")
            name, desc = resolve_orcid(orcid)
            entries.append((name, f"ORCID:{orcid}", desc))
            
        if entries:
            termset_path = args.outdir / "lab_experimenter_termset.yaml"
            write_termset(
                termset_path,
                termset_id="termset/lab_experimenters",
                name="LabExperimenters",
                prefix_name="ORCID",
                prefix_reference="https://orcid.org/",
                enum_name="Experimenters",
                entries=entries,
            )
            logger.info(f"Wrote {termset_path}")
            
            config_entries.append({
                "data_type": "NWBFile",
                "field": "experimenter",
                "term_set": str(termset_path.name)
            })

    # Process Institutions (ROR)
    if "institution" in manifest and manifest["institution"].get("source") == "ror":
        logger.info("Processing RORs...")
        entries = []
        for item in manifest["institution"].get("values", []):
            ror = item.get("ror")
            if not ror:
                continue
            logger.info(f"  Resolving {ror}...")
            name, desc = resolve_ror(ror)
            entries.append((name, f"ROR:{ror}", desc))
            
        if entries:
            termset_path = args.outdir / "lab_institution_termset.yaml"
            write_termset(
                termset_path,
                termset_id="termset/lab_institutions",
                name="LabInstitutions",
                prefix_name="ROR",
                prefix_reference="https://ror.org/",
                enum_name="Institutions",
                entries=entries,
            )
            logger.info(f"Wrote {termset_path}")
            
            config_entries.append({
                "data_type": "NWBFile",
                "field": "institution",
                "term_set": str(termset_path.name)
            })

    # Process Dandisets
    if "dandiset" in manifest and manifest["dandiset"].get("source") == "dandi":
        logger.info("Processing Dandisets...")
        entries = []
        for item in manifest["dandiset"].get("values", []):
            dandiset_id = item.get("dandiset_id")
            if not dandiset_id:
                continue
            logger.info(f"  Resolving {dandiset_id}...")
            title, desc = resolve_dandi(dandiset_id)
            entries.append((title, f"DANDI:{dandiset_id}", desc))
            
        if entries:
            termset_path = args.outdir / "lab_dandiset_termset.yaml"
            write_termset(
                termset_path,
                termset_id="termset/lab_dandisets",
                name="LabDandisets",
                prefix_name="DANDI",
                prefix_reference="https://identifiers.org/DANDI:",
                enum_name="Dandisets",
                entries=entries,
            )
            logger.info(f"Wrote {termset_path}")
            
            config_entries.append({
                "data_type": "NWBFile",
                "field": "related_publications",
                "term_set": str(termset_path.name)
            })

    # Write config snippet
    if config_entries:
        config_path = args.outdir / "lab_config.yaml"
        
        # Build the nested dictionary structure expected by PyNWB
        data_types = {}
        for entry in config_entries:
            dt = entry["data_type"]
            field = entry["field"]
            term_set = entry["term_set"]
            
            if dt not in data_types:
                data_types[dt] = {}
            data_types[dt][field] = {"termset": term_set}
            
        config_doc = {
            "namespaces": {
                "core": {
                    "version": "2.10.0",
                    "data_types": data_types
                }
            }
        }
        with config_path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(config_doc, f, sort_keys=False)
        logger.info(f"Wrote {config_path}")
        
        logger.info("\nDone! You can load this configuration in PyNWB with:")
        logger.info(f"  from pynwb import load_type_config")
        logger.info(f"  load_type_config('{config_path}')")

if __name__ == "__main__":
    main()
