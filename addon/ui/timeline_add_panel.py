import bpy

from .. import ops, utils


class NewTimelinePanel(utils.CheckpointsPanelMixin, bpy.types.Panel):
    """Add new timeline"""

    bl_idname = "CHECKPOINT_PT_new_timeline_panel"
    bl_label = ""
    bl_options = {utils.TIMELINE_ACTION_OPTIONS_2_83_POLYFILL}

    def draw(self, context):
        checkpoint_context = context.window_manager.checkpoint

        layout = self.layout
        layout.ui_units_x = 11.5

        layout.label(
            text="New Timeline from selected checkpoint",
            icon=utils.TIMELINE_ICON,
        )

        layout.prop(checkpoint_context, "newTimelineName")
        name = checkpoint_context.newTimelineName

        row = layout.row()
        row.prop(checkpoint_context, "new_tl_keep_history")
        new_tl_keep_history = checkpoint_context.new_tl_keep_history

        row = layout.row()
        if not name:
            row.enabled = False

        tl_ops = row.operator(ops.NewTimeline.bl_idname, text="Create Timeline")
        tl_ops.name = name
        tl_ops.new_tl_keep_history = new_tl_keep_history
