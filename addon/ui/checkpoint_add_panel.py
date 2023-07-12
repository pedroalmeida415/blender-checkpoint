import bpy

from .. import ops, ui, utils


_DISK_USAGE_ICONS = ["PACKAGE", "FILE_BLEND"]


class SubPanelCheckpointAdd(utils.CheckpointsPanelMixin, bpy.types.Panel):
    bl_idname = "CHECKPOINT_PT_checkpoint_add"
    bl_parent_id = ui.MainPanel.bl_idname
    bl_label = ""
    bl_options = {"HIDE_HEADER"}

    @classmethod
    def poll(cls, context):
        return context.window_manager.checkpoint.isInitialized

    def draw(self, context):
        layout = self.layout
        layout.alignment = "CENTER"

        row = layout.row(align=True)

        col1 = row.column()
        col1.alignment = "LEFT"
        col1.label(text="Description: ")

        col2 = row.column()
        col2.alignment = "EXPAND"
        col2.prop(context.window_manager.checkpoint, "checkpointDescription")

        row = layout.row()
        row.scale_y = 2
        addCol = row.column()

        description = context.window_manager.checkpoint.checkpointDescription
        if not description:
            addCol.enabled = False

        checkpoint = addCol.operator(ops.AddCheckpoint.bl_idname)
        checkpoint.description = description

        layout.separator()

        diskUsage = context.window_manager.checkpoint.diskUsage

        row = layout.row()
        col1 = row.column()
        subRow = col1.row(align=True)
        subRow.label(text="", icon=_DISK_USAGE_ICONS[0])
        subRow.label(text="", icon=_DISK_USAGE_ICONS[1])

        col2 = row.column()
        col2.alignment = "RIGHT"
        col2.label(text=f"Disk space used: {_format_size(diskUsage)}")


def _format_size(size):
    if size < 999:
        return f"{size:.2f} MB"
    else:
        # Convert megabytes to gigabytes
        size = size / 1024
        return f"{size:.2f} GB"
