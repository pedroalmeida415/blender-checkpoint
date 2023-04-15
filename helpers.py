import os
import json
import uuid
import shutil

from datetime import datetime, timezone, timedelta

import pygit2 as git
from pygit2._pygit2 import GitError, GIT_SORT_TIME, GIT_SORT_REVERSE, GIT_RESET_HARD

# Format: Fri Sep  2 19:36:07 2022 +0530
GIT_TIME_FORMAT = "%c %z"

CHECKPOINTS_FOLDER_NAME = ".checkpoints"
TIMELINES_FOLDER_NAME = "timelines"
SAVES_FOLDER_NAME = "saves"
ORIGINAL_TIMELINE_NAME = "original.json"


def get_data_folders_path(filepath):
    CHECKPOINTS_FOLDER_PATH = os.path.join(
        filepath, CHECKPOINTS_FOLDER_NAME)

    TIMELINES_FOLDER_PATH = os.path.join(
        CHECKPOINTS_FOLDER_PATH, TIMELINES_FOLDER_NAME)

    SAVES_FOLDER_PATH = os.path.join(
        CHECKPOINTS_FOLDER_PATH, SAVES_FOLDER_NAME)

    ORIGINAL_TIMELINE_PATH = os.path.join(
        TIMELINES_FOLDER_PATH, ORIGINAL_TIMELINE_NAME)

    return CHECKPOINTS_FOLDER_PATH, TIMELINES_FOLDER_PATH, SAVES_FOLDER_PATH, ORIGINAL_TIMELINE_PATH


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
                                                timezoneInfo).strftime(GIT_TIME_FORMAT)

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
    CHECKPOINTS_FOLDER_PATH, TIMELINES_FOLDER_PATH, SAVES_FOLDER_PATH, ORIGINAL_TIMELINE_PATH = get_data_folders_path(
        filepath)

    # generate folder structure
    if not os.path.exists(CHECKPOINTS_FOLDER_PATH):
        os.mkdir(CHECKPOINTS_FOLDER_PATH)

    if not os.path.exists(TIMELINES_FOLDER_PATH):
        os.mkdir(TIMELINES_FOLDER_PATH)

    if not os.path.exists(SAVES_FOLDER_PATH):
        os.mkdir(SAVES_FOLDER_PATH)

    if not os.path.exists(ORIGINAL_TIMELINE_PATH):
        # generate first checkpoint
        checkpoint_id = uuid.uuid4().hex

        source_file = f"{filepath}{filename}"
        destination_file = f"{SAVES_FOLDER_PATH}/{checkpoint_id}.blend"
        shutil.copy(source_file, destination_file)

        with open(ORIGINAL_TIMELINE_PATH, "w") as file:
            first_checkpoint = [{
                "id": checkpoint_id,
                "message": f"{filename} - Initial checkpoint",
                "date": str(datetime.now(timezone.utc))
            }]
            json.dump(first_checkpoint, file)


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
