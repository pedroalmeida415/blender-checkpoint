import os
import sys
import importlib
import re
from unicodedata import normalize

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


def slugify(text):
    """
    Simplifies a string, converts it to lowercase, removes non-word characters
    and spaces, converts spaces and apostrophes to hyphens.
    """
    text = normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
    text = re.sub(r'[^\w\s\'-]', '', text).strip().lower()
    text = re.sub(r'[-\s\'"]+', '-', text)
    return text


class GitNewBranch(Operator):
    """Create New Branch from selected commit."""

    bl_label = __doc__
    bl_idname = "git.new_branch"

    name: StringProperty(
        name="",
        options={'TEXTEDIT_UPDATE'},
        description="Name of new Branch. (will be slugified)"
    )

    def execute(self, context):
        filepath = bpy.path.abspath("//")
        git = context.window_manager.git

        # Get repo
        try:
            repo = gitHelpers.getRepo(filepath)
        except GitError:
            return {'CANCELLED'}

        # Get selected commit
        selectedCommit = repo.revparse_single(
            f'HEAD~{git.commitsListIndex}')

        # Create new Branch
        new_branch_ref = repo.branches.create(
            slugify(self.name), selectedCommit)

        repo.checkout(new_branch_ref)

        # Clear branch name property
        self.newBranchName = ""
        if context.window_manager.git.newBranchName:
            context.window_manager.git.newBranchName = ""

        return {'FINISHED'}


class GitRevertToCommit(Operator):
    """Switch to selected commit"""

    bl_label = __doc__
    bl_idname = "git.revert_to_commit"

    id: StringProperty(
        name="",
        description="ID of commit to switch to"
    )

    def execute(self, context):
        filepath = bpy.path.abspath("//")

        currentCommitId = context.window_manager.git.currentCommitId

        if currentCommitId == self.id:
            return {'CANCELLED'}

        # ABSTRACT IN A GITHELPER
        # Get repo
        try:
            repo = gitHelpers.getRepo(filepath)
        except GitError:
            return {'CANCELLED'}

        latestCommit = repo[repo.head.target]
        revertCommit = repo.get(self.id)

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
        # ABSTRACT IN A GITHELPER

        # Used to correctly identify the active commit after revert,
        # since there is no way to keep that after Blender's reload
        repo.config["user.currentCommit"] = self.id

        # Load the reverted file
        bpy.ops.wm.revert_mainfile()

        return {'FINISHED'}


class GitCommit(Operator):
    """Commit changes"""

    bl_label = __doc__
    bl_idname = "git.commit"

    message: StringProperty(
        name="",
        options={'TEXTEDIT_UPDATE'},
        description="A short description of the changes made"
    )

    def execute(self, context):
        filepath = bpy.path.abspath("//")

        try:
            repo = gitHelpers.getRepo(filepath)
        except GitError:
            return {'CANCELLED'}

        gitHelpers.commit(repo, self.message)

        # Clear commit message property
        repo.config["user.currentCommit"] = ""

        self.message = ""
        if context.window_manager.git.commitMessage:
            context.window_manager.git.commitMessage = ""

        backupSize = getBackupFolderSize(os.path.join(filepath, ".git"))
        repo.config["user.backupSize"] = str(backupSize)

        return {'FINISHED'}


def getBackupFolderSize(filepath):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(filepath):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)

    return total_size


class GitRemoveCommit(Operator):
    """Remove selected commit"""

    bl_label = __doc__
    bl_idname = "git.remove_commit"

    id: StringProperty(
        name="",
        description="ID of commit to remove"
    )

    def invoke(self, context, event):
        wm = context.window_manager

        return wm.invoke_props_dialog(self, width=290)

    def draw(self, context):
        layout = self.layout

        layout.separator()

        row = layout.row()
        row.alignment = 'CENTER'
        row.label(text="ARE YOU SURE?")

        layout.separator()

        row = layout.row()
        row.label(
            text="This will remove the selected commit from the list.", icon="UNLINKED")

    def execute(self, context):
        git_context = context.window_manager.git
        currentCommitId = git_context.currentCommitId

        if currentCommitId == self.id:
            return {'CANCELLED'}

        filepath = bpy.path.abspath("//")

        try:
            repo = gitHelpers.getRepo(filepath)
        except GitError:
            return {'CANCELLED'}

        gitHelpers.removeCommitFromHistory(repo, self.id)

        self.id = ""

        self.report({"INFO"}, "Commit removed successfully!")
        return {'FINISHED'}


# class GitAmmendCommit(Operator):
#     '''Edit selected commit's message'''
#     '''https://www.pygit2.org/repository.html#pygit2.Repository.amend_commit'''

classes = (GitNewBranch, GitRevertToCommit, GitCommit, GitRemoveCommit)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
