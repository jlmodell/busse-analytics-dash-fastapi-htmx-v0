import yaml
import os


def load_config():
    with open(os.path.join(os.path.dirname(__file__), "config.yaml"), "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return config


config = load_config()
