import bpy

from .. import config, ops, utils


class EditTimelinePanel(utils.CheckpointsPanelMixin, bpy.types.Panel):
    """Edit timeline name"""

    bl_idname = "CPS_PT_edit_timeline_panel"
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
                text="You cannot edit the original timeline",
                icon=utils.PROTECTED_ICON,
            )
        else:
            cps_context = context.window_manager.cps

            layout.label(text="Edit Timeline name", icon=utils.TIMELINE_ICON)

            layout.prop(cps_context, "newTimelineName")
            name = cps_context.newTimelineName

            row = layout.row()
            if not name:
                row.enabled = False

            operator = row.operator(ops.RenameTimeline.bl_idname, text="Rename")
            operator.name = name
