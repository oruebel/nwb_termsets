"""
nwb_termsets
"""
import os

__version__ = "0.1.0"

def get_config_path():
    """Return the path to the default configuration file."""
    return os.path.join(os.path.dirname(__file__), "default_config.yaml")

def load_termset_config():
    """Load the default term set configuration into PyNWB."""
    from pynwb import load_type_config
    load_type_config(config_path=get_config_path())

def get_available_termsets():
    """Return a list of available term set files."""
    term_sets_dir = os.path.join(os.path.dirname(__file__), "term_sets")
    if not os.path.exists(term_sets_dir):
        return []
    return [f for f in os.listdir(term_sets_dir) if f.endswith(".yaml")]

def get_termset_path(termset_name):
    """Return the path to a specific term set file."""
    path = os.path.join(os.path.dirname(__file__), "term_sets", termset_name)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Term set '{termset_name}' not found. Available term sets: {get_available_termsets()}")
    return path
