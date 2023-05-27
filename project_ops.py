import os

import bpy
from bpy.types import Operator
from bpy.props import (StringProperty, BoolProperty)

from . import config
from . import project_helpers


class StartVersionControl(Operator):
    '''Initialize addon on the current project'''

    bl_idname = "cps.start_version_control"
    bl_label = "Start Version Control"

    def execute(self, context):
        filepath = bpy.path.abspath("//")
        filename = bpy.path.basename(bpy.data.filepath)

        cps_context = context.window_manager.cps

        if cps_context.isInitialized:
            return {'CANCELLED'}

        bpy.ops.wm.save_mainfile()
        project_helpers.initialize_version_control(filepath, filename)

        cps_context.isInitialized = True
        cps_context.selectedListIndex = 0

        self.report({"INFO"}, "Version control started!")

        return {'FINISHED'}


class RenameProject(Operator):
    '''Saves project new name to correctly manage checkpoints'''

    bl_idname = "cps.rename_project"
    bl_label = "Confirm rename and continue"

    name: StringProperty(
        name="",
        description="new name of project"
    )

    def execute(self, context):
        filepath = bpy.path.abspath("//")

        config.set_state(filepath, "filename", self.name)

        self.report({"INFO"}, "Renamed successfully, all set!")
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

    new_tl_keep_history: BoolProperty(
        name="",
        description="Keep previous checkpoints"
    )

    def execute(self, context):
        filepath = bpy.path.abspath("//")
        cps_context = context.window_manager.cps

        slugfied_name = project_helpers.slugify(self.name)
        try:
            new_name = project_helpers.create_new_timeline(
                filepath, slugfied_name, cps_context.selectedListIndex, self.new_tl_keep_history)
        except FileExistsError:
            self.report(
                {"ERROR"}, f"A timeline with name {self.name} already exists")
            return {'CANCELLED'}

        # Clean up
        cps_context.selectedListIndex = 0

        project_helpers.switch_timeline(filepath, new_name)

        self.name = ""
        self.new_tl_keep_history = False
        if cps_context.newTimelineName:
            cps_context.newTimelineName = ""

        bpy.ops.wm.revert_mainfile()

        return {'FINISHED'}


class DeleteTimeline(Operator):
    """Delete current timeline"""

    bl_label = __doc__
    bl_idname = "cps.delete_timeline"

    def execute(self, context):
        filepath = bpy.path.abspath("//")
        state = config.get_state(filepath)
        cps_context = context.window_manager.cps

        # get current timeline's checkpoints that will be deleted
        tl_checkpoints_count = len(cps_context.checkpoints)

        to_delete_tl = state["current_timeline"]

        # delete previous timeline
        project_helpers.delete_timeline(
            filepath, to_delete_tl, tl_checkpoints_count)

        # switch to original timeline
        project_helpers.switch_timeline(filepath)

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
        cps_context = context.window_manager.cps

        slugified_name = project_helpers.slugify(self.name)

        try:
            project_helpers.rename_timeline(filepath, slugified_name)
        except FileExistsError:
            self.report(
                {"ERROR"}, f"A timeline with name {self.name} already exists")
            return {'CANCELLED'}

        self.name = ""
        if cps_context.newTimelineName:
            cps_context.newTimelineName = ""

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

        project_helpers.load_checkpoint(filepath, self.id)

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

        cps_context = context.window_manager.cps

        cps_context.should_display_dialog__ = False

        bpy.ops.wm.save_mainfile()

        project_helpers.add_checkpoint(filepath, self.description)

        self.description = ""
        cps_context.selectedListIndex = 0
        cps_context.should_display_dialog__ = True
        if cps_context.checkpointDescription:
            cps_context.checkpointDescription = ""

        return {'FINISHED'}


class DeleteCheckpoint(Operator):
    """Delete checkpoint"""

    bl_label = __doc__
    bl_idname = "cps.delete_checkpoint"

    def invoke(self, context, event):
        wm = context.window_manager

        return wm.invoke_props_dialog(self, width=385)

    def draw(self, context):
        layout = self.layout

        layout.separator()

        row = layout.row()
        row.alignment = 'CENTER'
        row.label(text="ARE YOU SURE?")

        layout.separator()

        row = layout.row()
        row.label(
            text="This will delete the selected checkpoint - (won't affect other timelines)", icon="UNLINKED")

    def execute(self, context):
        cps_context = context.window_manager.cps

        filepath = bpy.path.abspath("//")

        project_helpers.delete_checkpoint(
            filepath, cps_context.selectedListIndex)

        # Clean up
        self.id = ""
        cps_context.selectedListIndex = 0

        self.report({"INFO"}, "Checkpoint deleted successfully!")
        return {'FINISHED'}


class EditCheckpoint(Operator):
    """Edit checkpoint description"""

    bl_label = __doc__
    bl_idname = "cps.edit_checkpoint"

    def invoke(self, context, event):
        wm = context.window_manager

        return wm.invoke_props_dialog(self, width=300)

    def draw(self, context):
        cps_context = context.window_manager.cps

        layout = self.layout

        row = layout.row(align=True)

        col1 = row.column()
        col1.alignment = 'LEFT'
        col1.label(text="New description: ")

        col2 = row.column()
        col2.alignment = 'EXPAND'
        col2.prop(cps_context, "checkpointDescription")

    def execute(self, context):
        cps_context = context.window_manager.cps

        if not cps_context.checkpointDescription:
            return {'CANCELLED'}

        filepath = bpy.path.abspath("//")

        project_helpers.edit_checkpoint(
            filepath, cps_context.selectedListIndex, cps_context.checkpointDescription)

        # Clean up
        if cps_context.checkpointDescription:
            cps_context.checkpointDescription = ""

        self.report({"INFO"}, "Description edited successfully!")
        return {'FINISHED'}


class ExportCheckpoint(Operator):
    """Export checkpoint"""

    bl_label = __doc__
    bl_idname = "cps.export_checkpoint"

    id: StringProperty(
        name="",
        description="ID of checkpoint to export"
    )

    def execute(self, context):
        filepath = bpy.path.abspath("//")

        cps_context = context.window_manager.cps
        checkpointDescription = cps_context.checkpoints[cps_context.selectedListIndex]["description"]

        project_helpers.export_checkpoint(
            filepath, self.id, checkpointDescription)

        # Clean up
        self.id = ""
        self.report({"INFO"}, "Checkpoint exported successfully!")
        return {'FINISHED'}


class PostSaveDialog(bpy.types.Operator):
    """Dialog to quickly add checkpoints"""

    bl_label = "Add checkpoint"
    bl_idname = "cps.post_save_dialog"

    @classmethod
    def poll(cls, context):
        if not config.cp_state.has_license_key:
            return False

        filepath = bpy.path.abspath("//")
        filename = bpy.path.basename(bpy.data.filepath)

        cps_context = context.window_manager.cps

        try:
            state = config.get_state(filepath)
        except FileNotFoundError:
            return False

        return cps_context.isInitialized and cps_context.should_display_dialog__ and state["filename"] == filename

    def invoke(self, context, event):
        wm = context.window_manager
        filepath = bpy.path.abspath("//")

        try:
            config.get_state(filepath)
            return wm.invoke_props_dialog(self, width=400)
        except FileNotFoundError:
            return {'CANCELLED'}

    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)

        col1 = row.column()
        col1.alignment = "LEFT"
        col1.label(text="Description: ")

        col2 = row.column()
        col2.alignment = "EXPAND"
        col2.prop(context.window_manager.cps, "checkpointDescription")

    def execute(self, context):
        cps_context = context.window_manager.cps
        description = cps_context.checkpointDescription

        if not description:
            self.report({'ERROR_INVALID_INPUT'},
                        "Description cannot be empty.")
            return {'CANCELLED'}

        filepath = bpy.path.abspath("//")

        project_helpers.add_checkpoint(filepath, description)

        cps_context.selectedListIndex = 0
        if cps_context.checkpointDescription:
            cps_context.checkpointDescription = ""

        self.report({"INFO"}, "Successfully saved!")

        return {'FINISHED'}


classes = (NewTimeline, DeleteTimeline, RenameTimeline, StartVersionControl, RenameProject,
           LoadCheckpoint, AddCheckpoint, DeleteCheckpoint, ExportCheckpoint, EditCheckpoint,
           PostSaveDialog)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
