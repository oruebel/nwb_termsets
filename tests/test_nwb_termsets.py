import os
import pytest
from ruamel.yaml import YAML
import nwb_termsets
import pynwb

def test_get_available_termsets():
    termsets = nwb_termsets.get_available_termsets()
    assert isinstance(termsets, list)
    assert len(termsets) > 0
    assert "subject_species_ncbitaxon_termset.yaml" in termsets
    assert "brain_region_uberon_termset.yaml" in termsets

def test_get_termset_path():
    path = nwb_termsets.get_termset_path("subject_species_ncbitaxon_termset.yaml")
    assert os.path.exists(path)
    assert path.endswith("subject_species_ncbitaxon_termset.yaml")

def test_get_termset_path_invalid():
    with pytest.raises(FileNotFoundError):
        nwb_termsets.get_termset_path("invalid_termset.yaml")

def test_load_termset_config():
    nwb_termsets.load_termset_config()
    loaded_config = pynwb.get_loaded_type_config()
    assert loaded_config is not None
    assert "namespaces" in loaded_config
    assert "core" in loaded_config["namespaces"]
    assert "data_types" in loaded_config["namespaces"]["core"]
    assert "Subject" in loaded_config["namespaces"]["core"]["data_types"]

def test_default_config_exists():
    config_path = os.path.join(os.path.dirname(nwb_termsets.__file__), "default_config.yaml")
    assert os.path.exists(config_path)
    
    yaml = YAML(typ='safe')
    with open(config_path, "r") as f:
        config = yaml.load(f)
        
    assert "namespaces" in config
    assert "core" in config["namespaces"]
    assert "data_types" in config["namespaces"]["core"]
