import bpy

from .. import utils


class SwitchTimelineErrorTooltip(utils.CheckpointsPanelMixin, bpy.types.Panel):
    """Tooltip for trying to create new timeline with uncomitted changes."""

    bl_idname = "CPS_PT_switch_timeline_error_panel"
    bl_label = ""
    bl_options = {utils.TIMELINE_ACTION_OPTIONS_2_83_POLYFILL}

    def draw(self, context):
        layout = self.layout
        layout.ui_units_x = 19

        row = layout.row()
        row.label(
            text="You must add a checkpoint with your changes before switching timelines."
        )


# def errorPopupDraw(self, context):
#     self.layout.label(text="You have done something you shouldn't do!")
# bpy.context.window_manager.popup_menu(errorPopupDraw, title="Error", icon='ERROR')
