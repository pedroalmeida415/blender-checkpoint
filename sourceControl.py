import os
import sys
import importlib

import bpy
from bpy.types import Operator
from bpy.props import StringProperty

import pygit2 as git
from pygit2._pygit2 import GitError
from pygit2 import GIT_RESET_SOFT, GIT_RESET_HARD

# Local imports implemented to support Blender refreshes
modulesNames = ("gitHelpers", "openProject")
for module in modulesNames:
    if module in sys.modules:
        importlib.reload(sys.modules[module])
    else:
        parent = ".".join(__name__.split(".")[:-1])
        globals()[module] = importlib.import_module(f"{parent}.{module}")


class GitNewBranch(Operator):
    """Create New Branch."""

    bl_label = __doc__
    bl_idname = "git.new_branch"

    name: StringProperty(
        name="",
        options={'TEXTEDIT_UPDATE'},
        description="Name of new Branch."
    )

    def invoke(self, context, event):
        filepath = bpy.path.abspath("//")
        filename = bpy.path.basename(bpy.data.filepath).split(".")[0]

        # Save .blend file (Writes commands to Python file and clears reports)
        bpy.ops.wm.save_mainfile(
            filepath=os.path.join(filepath, f"{filename}.blend"))

        # Get repo
        try:
            repo = git.Repository(filepath)
        except GitError:
            return {'CANCELLED'}

        # Get last commit
        commit = repo[repo.head.target]

        # Create new Branch
        repo.branches.create(self.name.strip(), commit)

        # Clear branch name property
        self.newBranchName = ""
        if context.window_manager.git.newBranchName:
            context.window_manager.git.newBranchName = ""

        return {'FINISHED'}


class GitRevertToCommit(Operator):
    """Revert to Commit"""

    bl_label = __doc__
    bl_idname = "git.revert_to_commit"

    id: StringProperty(
        name="",
        description="ID of commit to switch to"
    )

    def invoke(self, context, event):
        filepath = bpy.path.abspath("//")
        filename = bpy.path.basename(bpy.data.filepath).split(".")[0]

        # Save .blend file (Writes commands to Python file and clears reports)
        bpy.ops.wm.save_mainfile(
            filepath=os.path.join(filepath, f"{filename}.blend"))

        # Get repo
        try:
            repo = git.Repository(filepath)
        except GitError:
            return {'CANCELLED'}

        latestCommit = repo[repo.head.target]
        revertCommit = repo.get(self.id)
        if latestCommit.hex == revertCommit.hex:
            return {'CANCELLED'}

        """
            https://stackoverflow.com/a/1470452

            A <-- B <-- C <-- D            <-- master <-- HEAD
            
            Revert to A
            
            $ git reset A --hard
            $ git reset D --soft
            $ git commit
            
            A <-- B <-- C <-- D <-- A'     <-- master <-- HEAD
        """
        repo.reset(revertCommit.oid, GIT_RESET_HARD)
        repo.reset(latestCommit.oid, GIT_RESET_SOFT)
        gitHelpers.commit(repo, f"Reverted to commit: {revertCommit.hex[:7]}")

        # Regen file
        openProject.regenFile(filepath, filename)

        return {'FINISHED'}


class GitCommit(Operator):
    """Commit Changes."""

    bl_label = __doc__
    bl_idname = "git.commit"

    message: StringProperty(
        name="",
        options={'TEXTEDIT_UPDATE'},
        description="A short description of the changes made"
    )

    def invoke(self, context, event):
        filepath = bpy.path.abspath("//")
        filename = bpy.path.basename(bpy.data.filepath).split(".")[0]

        # Save .blend file (Writes commands to Python file and clears reports)
        bpy.ops.wm.save_mainfile(
            filepath=os.path.join(filepath, f"{filename}.blend"))

        # Commit changes
        try:
            # Find repository path from subdirectory
            repo_path = git.discover_repository(filepath)

            # Set up repository
            repo = git.Repository(repo_path)
        except GitError:
            return {'CANCELLED'}

        gitHelpers.commit(repo, self.message)

        # Clear commit message property
        self.message = ""
        if context.window_manager.git.commitMessage:
            context.window_manager.git.commitMessage = ""

        return {'FINISHED'}


classes = (GitNewBranch, GitRevertToCommit, GitCommit)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
