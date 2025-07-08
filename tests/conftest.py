import pytest
import json
import os
import sys

# Ensure src directory is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from planner import Planner

@pytest.fixture(scope="session")
def planner_config():
    cfg_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config.json'))
    with open(cfg_path) as f:
        return json.load(f)

@pytest.fixture(scope="session")
def planner(planner_config):
    # Write a temporary config file if needed, but use config directly
    # Planner expects a path, so write planner_config to a temp file
    tmp_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'temp_config.json'))
    with open(tmp_path, 'w') as f:
        json.dump(planner_config, f)
    return Planner(config_path=tmp_path)
