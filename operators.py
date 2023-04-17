import os
import sys
import importlib
import re
from unicodedata import normalize

import bpy
from bpy.types import Operator
from bpy.props import (StringProperty, BoolProperty)

# Local imports implemented to support Blender refreshes
modulesNames = ("helpers",)
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


class StartGame(Operator):
    '''Initialize addon on the current project'''

    bl_idname = "cps.start_game"
    bl_label = "Start"

    def execute(self, context):
        filepath = bpy.path.abspath("//")
        filename = bpy.path.basename(bpy.data.filepath)

        cps_context = context.window_manager.cps

        if cps_context.isInitialized:
            return {'CANCELLED'}

        helpers.initialize_version_control(filepath, filename)

        cps_context.isInitialized = True

        self.report({"INFO"}, "Game started!")
        return {'FINISHED'}


class NewTimeline(Operator):
    """Creates a new timeline from the selected checkpoint"""

    bl_label = __doc__
    bl_idname = "cps.new_timeline"

    name: StringProperty(
        name="",
        options={'TEXTEDIT_UPDATE'},
        description="Name of new timeline. (will be slugified)"
    )

    keep_history: BoolProperty(
        name="",
        description="Should keep previous checkpoints"
    )

    def execute(self, context):
        filepath = bpy.path.abspath("//")
        cps_context = context.window_manager.cps

        # Get selected commit
        selectedCheckpointId = cps_context.checkpoints[cps_context.selectedListIndex]["id"]

        new_tl_name = slugify(self.name)
        # Create new Branch from selected commit
        try:
            helpers.create_new_timeline(
                filepath, new_tl_name, selectedCheckpointId, self.keep_history)
        except FileExistsError:
            self.report({"ERROR"}, f"Timeline '{self.name}' already exists")
            return {'CANCELLED'}

        helpers.switch_timeline(filepath, new_tl_name)

        # Clean up
        cps_context.commitsListIndex = 0

        self.name = ""
        self.keep_history = False
        if context.window_manager.cps_context.newTimelineName:
            context.window_manager.cps_context.newTimelineName = ""

        bpy.ops.wm.revert_mainfile()

        return {'FINISHED'}


class GitDeleteBranch(Operator):
    """Delete current branch"""

    bl_label = __doc__
    bl_idname = "git.delete_branch"

    def execute(self, context):
        filepath = bpy.path.abspath("//")
        git = context.window_manager.git

        # Get repo
        try:
            repo = gitHelpers.getRepo(filepath)
        except GitError:
            return {'CANCELLED'}

        delete_branch = repo.branches[repo.head.shorthand]

        master_ref = repo.branches["master"]

        git.commitsListIndex = 0

        repo.checkout(master_ref)

        delete_branch.delete()

        repo.config["user.currentCommit"] = str(repo.head.target)

        bpy.ops.wm.revert_mainfile()

        return {'FINISHED'}


class GitEditBranch(Operator):
    """Edit current timeline name"""

    bl_label = __doc__
    bl_idname = "git.edit_branch"

    name: StringProperty(
        name="",
        options={'TEXTEDIT_UPDATE'},
        description="New timeline name. (will be slugified)"
    )

    def execute(self, context):
        filepath = bpy.path.abspath("//")

        # Get repo
        try:
            repo = gitHelpers.getRepo(filepath)
        except GitError:
            return {'CANCELLED'}

        try:
            repo.branches[repo.head.shorthand].rename(slugify(self.name))
        except AlreadyExistsError:
            self.report({"ERROR"}, "A timeline with that name already exists")
            return {'CANCELLED'}

        self.name = ""
        if context.window_manager.git.newBranchName:
            context.window_manager.git.newBranchName = ""

        self.report({"INFO"}, "Renamed timeline")

        return {'FINISHED'}


class GitRevertToCommit(Operator):
    """Restore selected backup"""

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
    """Save backup"""

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

        # Clean up
        self.id = ""
        git_context.commitsListIndex = 0

        # get index of the currentCommitId and set the commit of that index as the current when deleting commits below the current one
        # in order to preserve icons, since the all the commits above the deleted get assigned a new id
        # context.window_manager.git.currentCommitId

        self.report({"INFO"}, "Backup removed successfully!")
        return {'FINISHED'}


classes = (NewTimeline, GitDeleteBranch, GitEditBranch, StartGame,
           GitRevertToCommit, GitCommit, GitRemoveCommit)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
