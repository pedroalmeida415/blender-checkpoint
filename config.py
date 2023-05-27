import os
import json
import textwrap

from urllib.request import urlopen, Request
from urllib.error import HTTPError
import urllib.parse


class PATHS_KEYS:
    ROOT_FOLDER = ".checkpoints"
    TIMELINES_FOLDER = "timelines"
    CHECKPOINTS_FOLDER = "saves"
    OBJECTS_FOLDER = "objects"

    ORIGINAL_TL_FILE = "Original.json"
    PERSISTED_STATE_FILE = "_persisted_state.json"

    LICENSE_FILE = ".checkpoint"


class LICENSE_TYPES:
    TEN_SEATS_VERSION = "10_seats"
    STANDALONE_VERSION = "standalone"
    WRONG_VERSION_KEY = "wrong_version_key"


LICENSE_FILE_PATH = os.path.join(
    os.path.expanduser("~"), PATHS_KEYS.LICENSE_FILE)

# Singleton for storing global state
class _CheckpointState:
    __slots__ = (
        "has_license_key",
        )

    def __init__(self):
        self.has_license_key = os.path.exists(LICENSE_FILE_PATH)

# One state to rule them all (otherwise known as a singleton)
cp_state = _CheckpointState()
del _CheckpointState


def multiline_label(context, text, parent, icon="NONE"):
    chars = int(context.region.width / 8)   # 7 pix on 1 character
    wrapper = textwrap.TextWrapper(width=chars)
    text_lines = wrapper.wrap(text=text)
    for i, text_line in enumerate(text_lines):
        if i == 0:
            parent.label(text=text_line, icon=icon)
            continue
        parent.label(text=text_line)


def get_paths(filepath):
    _root_folder_path = os.path.join(
        filepath, PATHS_KEYS.ROOT_FOLDER)

    _timelines_folder_path = os.path.join(
        _root_folder_path, PATHS_KEYS.TIMELINES_FOLDER)

    _saves_folder_path = os.path.join(
        _root_folder_path, PATHS_KEYS.CHECKPOINTS_FOLDER)

    _objects_folder_path = os.path.join(
        _root_folder_path, PATHS_KEYS.OBJECTS_FOLDER)

    _persisted_state_path = os.path.join(
        _root_folder_path, PATHS_KEYS.PERSISTED_STATE_FILE)

    return {
        PATHS_KEYS.ROOT_FOLDER: _root_folder_path,
        PATHS_KEYS.TIMELINES_FOLDER: _timelines_folder_path,
        PATHS_KEYS.CHECKPOINTS_FOLDER: _saves_folder_path,
        PATHS_KEYS.OBJECTS_FOLDER: _objects_folder_path,
        PATHS_KEYS.PERSISTED_STATE_FILE: _persisted_state_path
    }


def get_state(filepath):
    _paths = get_paths(
        filepath)

    with open(_paths[PATHS_KEYS.PERSISTED_STATE_FILE]) as f:
        state = json.load(f)
        return state


def set_state(filepath, prop, value):
    _paths = get_paths(filepath)
    with open(_paths[PATHS_KEYS.PERSISTED_STATE_FILE], 'r+') as f:
        state = json.load(f)

        if prop in state:
            state[prop] = value
        else:
            raise ValueError(f"Property '{prop}' not found in state")

        f.seek(0)
        json.dump(state, f, indent=4)
        f.truncate()


def has_root_folder(filepath):
    _paths = get_paths(
        filepath)
    _root = _paths[PATHS_KEYS.ROOT_FOLDER]

    return os.path.exists(_root)


def check_license_key(license_key: str):
    def _parse_variant(variant: str):
        if not "supercharged" in variant.lower():
            return LICENSE_TYPES.WRONG_VERSION_KEY

        return LICENSE_TYPES.STANDALONE_VERSION

    params = {'product_id': '5VU7EnKLdJjqB_PHlWeJQw==',  # constant
              'license_key': license_key,
              'increment_uses_count': str(not cp_state.has_license_key).lower()}

    query_string = urllib.parse.urlencode(params)

    req = Request(
        f"https://api.gumroad.com/v2/licenses/verify?{query_string}", method='POST')

    try:
        # make request
        response_data = urlopen(req, None).read().decode()
        response = json.loads(response_data)

        parsed_variant = _parse_variant(response["purchase"]["variants"])

        if parsed_variant == LICENSE_TYPES.WRONG_VERSION_KEY:
            return "This key does not belong to this product version. If you think this is a mistake, contact us by email or discord."

        uses = response["uses"]

        if parsed_variant == LICENSE_TYPES.STANDALONE_VERSION and uses > 1:
            return "This key has already been claimed. If you think this is a mistake, contact us by email or discord."

        if parsed_variant == LICENSE_TYPES.TEN_SEATS_VERSION and uses > 10:
            return "You have reached the maximum ammount of users for this key. If you think this is a mistake, contact us by email or discord."

        with open(LICENSE_FILE_PATH, "w") as f:
            # Write your environment variables in key=value format
            f.write(f"LICENSE_KEY={license_key}\n")
        
        cp_state.has_license_key = True

    except HTTPError as e:
        error_data = e.read().decode()
        error = json.loads(error_data)

        return error["message"]
