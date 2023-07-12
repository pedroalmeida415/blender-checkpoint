import bpy

from ... import addon_updater_ops

from .. import ops, config, utils


class MainPanel(utils.CheckpointsPanelMixin, bpy.types.Panel):
    bl_idname = "CHECKPOINT_PT_main"
    bl_label = "Checkpoints"

    def draw(self, context):
        addon_updater_ops.check_for_update_background()

        layout = self.layout

        filepath = bpy.path.abspath("//")
        filename = bpy.path.basename(bpy.data.filepath)

        checkpoint_context = context.window_manager.checkpoint

        root_folder = config.has_root_folder(filepath)

        if not root_folder:
            checkpoint_context.isInitialized = False
            row = layout.row()
            row.operator(
                ops.StartVersionControl.bl_idname,
                text="Start Version Control",
                icon=utils.TIMELINE_ICON,
            )
            if not bpy.data.is_saved:
                row.enabled = False
                row = layout.row()
                row.alignment = "CENTER"
                row.label(text="You must save your project first")
            return

        state = config.get_state(filepath)
        if state["filename"] != filename:
            checkpoint_context.isInitialized = False

            row = layout.row()
            row.alignment = "CENTER"
            row.label(text="WARNING: Project name has changed", icon="ERROR")
            row = layout.row()
            row.alignment = "CENTER"
            row.label(text="If this is intentional, click the button below")
            row = layout.row()
            renameOps = row.operator(ops.RenameProject.bl_idname)
            renameOps.name = filename

            layout.separator()

            text = "This happens when you rename the project file, or when you have other projects in the same folder and one of them already initialized the addon before."
            config.multiline_label(
                context=context, text=text, parent=layout, icon="QUESTION"
            )

            layout.separator()

            text = "Keep in mind that separate projects need to have dedicated folders for each of them for the addon to work properly."
            config.multiline_label(
                context=context, text=text, parent=layout, icon="INFO"
            )
        else:
            checkpoint_context.isInitialized = True
            addCheckpointsToList()

        addon_updater_ops.update_notice_box_ui(self, context)


def addCheckpointsToList():
    """Add checkpoints to list"""
    filepath = bpy.path.abspath("//")
    state = config.get_state(filepath)

    checkpoint_context = bpy.context.window_manager.checkpoint

    # Get list
    checkpoints = checkpoint_context.checkpoints

    # Clear list
    checkpoints.clear()

    # TODO refatorar - não é mais necessário setar o active checkpoint aqui
    checkpoint_context.activeCheckpointId = state["active_checkpoint"]
    checkpoint_context.diskUsage = state["disk_usage"]

    current_timeline = state["current_timeline"]
    checkpoint = utils.get_checkpoints(filepath, current_timeline)
    for cp in checkpoint:
        item = checkpoints.add()
        item.id = cp["id"]
        item.date = cp["date"]
        item.description = cp["description"]
