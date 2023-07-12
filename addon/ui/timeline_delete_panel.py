import bpy

from .. import config, ops, utils


class DeleteTimelinePanel(utils.CheckpointsPanelMixin, bpy.types.Panel):
    """Deletes current Timeline"""

    bl_idname = "CHECKPOINT_PT_delete_timeline_panel"
    bl_label = ""
    bl_options = {utils.TIMELINE_ACTION_OPTIONS_2_83_POLYFILL}

    def draw(self, context):
        filepath = bpy.path.abspath("//")
        state = config.get_state(filepath)
        currentTimeline = state.get("current_timeline")

        is_original_timeline = currentTimeline == config.PATHS_KEYS.ORIGINAL_TL_FILE

        layout = self.layout

        if is_original_timeline:
            layout.ui_units_x = 11.5
            row = layout.row()
            row.label(
                text="You cannot delete the original timeline",
                icon=utils.PROTECTED_ICON,
            )
        else:
            layout.ui_units_x = 16.5
            layout.separator()

            row = layout.row()
            row.alignment = "CENTER"
            row.label(text="ARE YOU SURE?")

            layout.separator()

            row = layout.row()
            row.label(
                text="This will delete the current timeline. There is no going back.",
                icon=utils.DELETE_ICON,
            )

            row = layout.row()
            row.operator(ops.DeleteTimeline.bl_idname, text="Delete Timeline")
