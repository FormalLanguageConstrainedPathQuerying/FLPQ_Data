import pathlib

__all__ = [
    "VERSION",
    "DATASET_VERSION",
    "ROOT",
]

VERSION = "6.1.2"

#: The dataset version served on object storage: the package major version
#: with zeroed minor and patch (a minor/patch release does not move the
#: dataset).
DATASET_VERSION = f"{VERSION[0]}.0.0"

ROOT = pathlib.Path(__file__).parent
