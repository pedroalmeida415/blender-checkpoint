import os
import json
import textwrap

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
