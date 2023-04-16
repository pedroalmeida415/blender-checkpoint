import os
import json
import uuid
import shutil

from datetime import datetime, timezone, timedelta

import pygit2 as git
from pygit2._pygit2 import GitError, GIT_SORT_TIME, GIT_SORT_REVERSE, GIT_RESET_HARD

# Format: Fri Sep  2 19:36:07 2022 +0530
CP_TIME_FORMAT = "%c %z"

CHECKPOINTS = ".checkpoints"
TIMELINES = "timelines"
SAVES = "saves"
PERSISTED_STATE = "_persisted_state.json"


def _get_paths(filepath):
    _checkpoints_folder_path = os.path.join(
        filepath, CHECKPOINTS)

    _timelines_folder_path = os.path.join(
        _checkpoints_folder_path, TIMELINES)

    _saves_folder_path = os.path.join(
        _checkpoints_folder_path, SAVES)

    _persisted_state_path = os.path.join(
        _checkpoints_folder_path, PERSISTED_STATE)

    return {CHECKPOINTS: _checkpoints_folder_path,
            TIMELINES: _timelines_folder_path,
            SAVES: _saves_folder_path,
            PERSISTED_STATE: _persisted_state_path}


def getLastModifiedStr(date):
    """
    Returns last modified string
    date: offset-aware datetime.datetime object
    """

    # Get time difference
    now = datetime.now(timezone.utc)
    delta = now - date

    output = ""

    days = delta.days
    if days <= 0:
        hours = delta.seconds // 3600
        if hours <= 0:
            mins = (delta.seconds // 60) % 60
            if mins <= 0:
                secs = delta.seconds - hours * 3600 - mins * 60
                if secs <= 0:
                    output = "now"

                # Secs
                elif secs == 1:
                    output = f"{secs} sec"
                else:
                    output = f"{secs} sec"

            # Mins
            elif mins == 1:
                output = f"{mins} min"
            else:
                output = f"{mins} mins"

        # Hours
        elif hours == 1:
            output = f"{hours} hr"
        else:
            output = f"{hours} hrs"

    # Days
    elif days == 1:
        output = f"{days} day"
    else:
        output = f"{days} days"

    return output


def commit(repo, message):
    """Add all and commit changes to current branch"""

    # Add all
    repo.index.add_all()
    repo.index.write()

    name = repo.config["User.name"]
    email = repo.config["User.email"]
    signature = git.Signature(name, email)
    tree = repo.index.write_tree()

    try:
        # Assuming prior commits exist
        ref = repo.head.name
        parents = [repo.head.target]
    except GitError:
        # Initial Commit
        ref = "HEAD"
        parents = []

    repo.create_commit(
        ref,
        signature,
        signature,
        message,
        tree,
        parents
    )


def getCommits(repo):
    """Returns a list commit objects"""

    commits = []
    last = repo[repo.head.target]
    for commit in repo.walk(last.id, GIT_SORT_TIME):
        timezoneInfo = timezone(timedelta(minutes=commit.author.offset))
        datetimeString = datetime.fromtimestamp(float(commit.author.time),
                                                timezoneInfo).strftime(CP_TIME_FORMAT)

        commitDict = {}
        commitDict["id"] = commit.hex
        commitDict["name"] = commit.author.name
        commitDict["email"] = commit.author.email
        commitDict["date"] = datetimeString
        commitDict["message"] = commit.message.strip(" \t\n\r")

        commits.append(commitDict)

    return commits


def makeGitIgnore(path):
    """Generates .gitignore file for Git project at given path"""

    content = (
        "*\n"
        "\n"
        "!*.blend\n"
        "!textures\n"
        "!textures/*\n"
        "textures/*.blend\n"
        "\n"
        "*.blend1\n"
    )

    with open(os.path.join(path, ".gitignore"), "w") as file:
        file.write(content)


def configUser(repo, name, email):
    """Set user.name and user.email to the given Repo object"""

    repo.config["user.name"] = name
    repo.config["user.email"] = email
    repo.config["user.currentCommit"] = ""
    repo.config["user.backupSize"] = "0"


def discover_repo(filepath):
    return git.discover_repository(filepath)


def getRepo(filepath):
   # Try to find repository path from subdirectory to make sure there is no repo above
    repo_path = discover_repo(filepath)

    if not repo_path:
        repo_path = filepath

    # Set up repository
    repo = git.Repository(repo_path)
    return repo


def initialize_version_control(filepath, filename):
    _paths = _get_paths(filepath)

    _checkpoints = _paths[CHECKPOINTS]
    _timelines = _paths[TIMELINES]
    _saves = _paths[SAVES]
    _persisted_state = _paths[PERSISTED_STATE]

    # generate folder structure
    if not os.path.exists(_checkpoints):
        os.mkdir(_checkpoints)

    if not os.path.exists(_timelines):
        os.mkdir(_timelines)

    if not os.path.exists(_saves):
        os.mkdir(_saves)

    _original_tl_name = "original.json"
    _original_tl_path = os.path.join(_timelines, _original_tl_name)
    if not os.path.exists(_original_tl_path):
        # generate first checkpoint
        _initial_checkpoint_id = uuid.uuid4().hex

        source_file = f"{filepath}{filename}"
        destination_file = f"{_saves}/{_initial_checkpoint_id}.blend"
        shutil.copy(source_file, destination_file)

        with open(_original_tl_path, "w") as file:
            first_checkpoint = [{
                "id": _initial_checkpoint_id,
                "description": f"{filename} - Initial checkpoint",
                "date": str(datetime.now(timezone.utc))
            }]
            json.dump(first_checkpoint, file)

    if not os.path.exists(_persisted_state):
        # generate initial state
        with open(_persisted_state, "w") as file:
            initial_state = [{
                "active_timeline": _original_tl_name,
                "active_commit": _initial_checkpoint_id,
                "disk_usage": 0
            }]
            json.dump(initial_state, file)


def removeCommitFromHistory(repo, commit_id):
    repo.reset(repo.head.target, GIT_RESET_HARD)

    previous_branch_ref = repo.branches[repo.head.shorthand]
    previous_branch_shorthand = previous_branch_ref.shorthand

    old_branch_name = f"remove_commit_{commit_id}"

    previous_branch_ref.rename(old_branch_name)

    old_branch_iter = repo.walk(
        previous_branch_ref.target, GIT_SORT_REVERSE).__iter__()

    initial_commit = next(old_branch_iter)

    new_branch_ref = repo.branches.local.create(
        previous_branch_shorthand, initial_commit)
    repo.checkout(new_branch_ref)

    remove_commit_parents = None

    for commit in old_branch_iter:
        if commit.hex == commit_id:
            remove_commit_parents = commit.parent_ids[:]
            continue

        index = repo.index

        if remove_commit_parents:
            index = repo.merge_commits(
                commit.id, remove_commit_parents[0], favor="ours")
        else:
            repo.cherrypick(commit.id)

        parents = remove_commit_parents if str(
            commit.parent_ids[0]) == commit_id else [repo.head.target]

        tree_id = index.write_tree()

        repo.create_commit(repo.head.name, commit.author, commit.committer,
                           commit.message, tree_id, parents)

        repo.state_cleanup()

    repo.reset(repo.head.target, GIT_RESET_HARD)
    repo.branches[old_branch_name].delete()


def listall_timelines(filepath):
    _paths = _get_paths(
        filepath)
    return os.listdir(_paths[TIMELINES])

def get_state(filepath):
    _paths = _get_paths(
        filepath)

    with open(_paths[PERSISTED_STATE]) as f:
        state = json.load(f)
        return state
