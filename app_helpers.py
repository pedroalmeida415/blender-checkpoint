import os
import json
import textwrap

from urllib.request import urlopen, Request
from urllib.error import HTTPError
import urllib.parse


# File constants
ROOT = ".checkpoints"
TIMELINES = "timelines"
CHECKPOINTS = "saves"
PERSISTED_STATE = "_persisted_state.json"
ORIGINAL_TL = "Original.json"

# License constants
CHECKPOINT_KEY_FILE_PATH = os.path.join(
    os.path.expanduser("~"), ".checkpoint")
CHECKPOINT_KEY = os.path.exists(CHECKPOINT_KEY_FILE_PATH)
TEN_SEATS_VERSION = "10_seats"
STANDALONE_VERSION = "standalone"
WRONG_KEY_VERSION = "wrong_key_version"


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
        filepath, ROOT)

    _timelines_folder_path = os.path.join(
        _root_folder_path, TIMELINES)

    _saves_folder_path = os.path.join(
        _root_folder_path, CHECKPOINTS)

    _persisted_state_path = os.path.join(
        _root_folder_path, PERSISTED_STATE)

    return {ROOT: _root_folder_path,
            TIMELINES: _timelines_folder_path,
            CHECKPOINTS: _saves_folder_path,
            PERSISTED_STATE: _persisted_state_path}


def get_state(filepath):
    _paths = get_paths(
        filepath)

    with open(_paths[PERSISTED_STATE]) as f:
        state = json.load(f)
        return state


def set_state(filepath, prop, value):
    _paths = get_paths(filepath)
    with open(_paths[PERSISTED_STATE], 'r+') as f:
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
    _root = _paths[ROOT]

    return os.path.exists(_root)


def check_license_key(license_key: str):
    def _parse_variant(variant: str):
        if not "supercharged" in variant.lower():
            return WRONG_KEY_VERSION

        return STANDALONE_VERSION

    params = {'product_id': '5VU7EnKLdJjqB_PHlWeJQw==',  # constant
              'license_key': license_key,
              'increment_uses_count': str(not CHECKPOINT_KEY).lower()}

    query_string = urllib.parse.urlencode(params)

    req = Request(
        f"https://api.gumroad.com/v2/licenses/verify?{query_string}", method='POST')

    try:
        # make request
        response_data = urlopen(req, None).read().decode()
        response = json.loads(response_data)

        parsed_variant = _parse_variant(response["purchase"]["variants"])

        if parsed_variant == WRONG_KEY_VERSION:
            return "This key does not belong to this product version. If you think this is a mistake, contact us by email or discord."

        uses = response["uses"]

        if parsed_variant == STANDALONE_VERSION and uses > 1:
            return "This key has already been claimed. If you think this is a mistake, contact us by email or discord."

        if parsed_variant == TEN_SEATS_VERSION and uses > 10:
            return "You have reached the maximum ammount of users for this key. If you think this is a mistake, contact us by email or discord."

        with open(CHECKPOINT_KEY_FILE_PATH, "w") as f:
            # Write your environment variables in key=value format
            f.write(f"LICENSE_KEY={license_key}\n")

    except HTTPError as e:
        error_data = e.read().decode()
        error = json.loads(error_data)

        return error["message"]
