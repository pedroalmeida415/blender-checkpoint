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
            self.report(
                {"ERROR"}, f"A timeline with name {self.name} already exists")
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


class DeleteTimeline(Operator):
    """Delete current timeline"""

    bl_label = __doc__
    bl_idname = "cps.delete_timeline"

    def execute(self, context):
        filepath = bpy.path.abspath("//")
        state = helpers.get_state(filepath)

        to_delete_tl = state["current_timeline"]

        # switch to original timeline
        helpers.switch_timeline(filepath)

        # delete previous timeline
        helpers.delete_timeline(filepath, to_delete_tl)

        bpy.ops.wm.revert_mainfile()

        return {'FINISHED'}


class RenameTimeline(Operator):
    """Edit current timeline name"""

    bl_label = __doc__
    bl_idname = "cps.edit_timeline"

    name: StringProperty(
        name="",
        options={'TEXTEDIT_UPDATE'},
        description="New timeline name. (will be slugified)"
    )

    def execute(self, context):
        filepath = bpy.path.abspath("//")

        try:
            helpers.rename_timeline(filepath)
        except FileExistsError:
            self.report(
                {"ERROR"}, f"A timeline with name {self.name} already exists")
            return {'CANCELLED'}

        self.name = ""
        if context.window_manager.git.newBranchName:
            context.window_manager.git.newBranchName = ""

        self.report({"INFO"}, "Renamed timeline")

        return {'FINISHED'}


class LoadCheckpoint(Operator):
    """Load selected checkpoint"""

    bl_label = __doc__
    bl_idname = "cps.load_checkpoint"

    id: StringProperty(
        name="",
        description="ID of checkpoint to load"
    )

    def execute(self, context):
        filepath = bpy.path.abspath("//")

        activeCheckpointId = context.window_manager.cps.activeCheckpointId

        if activeCheckpointId == self.id:
            return {'CANCELLED'}

        helpers.load_checkpoint(filepath, self.id)

        bpy.ops.wm.revert_mainfile()

        return {'FINISHED'}


class AddCheckpoint(Operator):
    """Add checkpoint"""

    bl_label = __doc__
    bl_idname = "cps.add_checkpoint"

    description: StringProperty(
        name="",
        options={'TEXTEDIT_UPDATE'},
        description="A short description of the changes made"
    )

    def execute(self, context):
        filepath = bpy.path.abspath("//")

        gitHelpers.add_checkpoint(filepath, self.description)

        self.description = ""
        if context.window_manager.cps.checkpointDescription:
            context.window_manager.cps.checkpointDescription = ""

        return {'FINISHED'}


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


classes = (NewTimeline, DeleteTimeline, RenameTimeline, StartGame,
           LoadCheckpoint, AddCheckpoint, GitRemoveCommit)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
