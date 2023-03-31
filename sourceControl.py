import os
import sys
import importlib

import bpy
from bpy.types import Operator
from bpy.props import StringProperty

from pygit2._pygit2 import GitError
from pygit2 import GIT_RESET_SOFT, GIT_RESET_HARD

# Local imports implemented to support Blender refreshes
modulesNames = ("gitHelpers",)
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

        # Get repo
        try:
            repo = gitHelpers.getRepo(filepath)
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
    """Switch to Commit"""

    bl_label = __doc__
    bl_idname = "git.revert_to_commit"

    id: StringProperty(
        name="",
        description="ID of commit to switch to"
    )

    def invoke(self, context, event):
        filepath = bpy.path.abspath("//")

        # Get repo
        try:
            repo = gitHelpers.getRepo(filepath)
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

        # Used to correctly identify the active commit after revert,
        # since there is no way to keep that after Blender's reload
        repo.config["user.currentCommit"] = revertCommit.oid

        # Load the reverted file
        bpy.ops.wm.revert_mainfile()

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

        try:
            repo = gitHelpers.getRepo(filepath)
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
