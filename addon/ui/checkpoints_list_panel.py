import bpy
from datetime import datetime

from .. import ops, ui, utils

_CHECKPOINT_ICON = "KEYFRAME"
_ACTIVE_CHECKPOINT_ICON = "KEYTYPE_KEYFRAME_VEC"
_ADD_ICON = "ADD"
_ERROR_ICON = "ERROR"
_LOAD_ICON = "IMPORT"
_EDIT_ICON = "OUTLINER_DATA_GP_LAYER" if (3, 0, 0) > bpy.app.version else "CURRENT_FILE"


class SubPanelCheckpointsList(utils.CheckpointsPanelMixin, bpy.types.Panel):
    bl_idname = "CPS_PT_checkpoints_list"
    bl_parent_id = ui.MainPanel.bl_idname
    bl_label = ""
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        return context.window_manager.cps.isInitialized

    def draw_header(self, context):
        filepath = bpy.path.abspath("//")

        layout = self.layout

        row = layout.row()
        row.prop(context.window_manager.cps, "timelines")

        row_button = layout.row(align=True)
        row_button.scale_x = 0.8

        # TODO melhorar para não travar mais as ações, e sim exibir aviso de que alterações serão perdidas
        isFileModified = utils.check_is_modified(filepath)

        if isFileModified:
            row.enabled = False
            row_button.popover(
                ui.SwitchTimelineErrorTooltip.bl_idname, icon=_ERROR_ICON
            )
        else:
            row_button.popover(ui.NewTimelinePanel.bl_idname, icon=_ADD_ICON)
            row_button.popover(ui.DeleteTimelinePanel.bl_idname, icon=utils.DELETE_ICON)
            row_button.popover(ui.EditTimelinePanel.bl_idname, icon=_EDIT_ICON)

    def draw(self, context):
        filepath = bpy.path.abspath("//")
        cps_context = context.window_manager.cps

        layout = self.layout

        # List of Checkpoints
        row = layout.row()
        row.template_list(
            listtype_name="CheckpointsList",
            # "" takes the name of the class used to define the UIList
            list_id="",
            dataptr=cps_context,
            propname="checkpoints",
            active_dataptr=cps_context,
            active_propname="selectedListIndex",
            item_dyntip_propname="description",
            sort_lock=True,
            rows=5,
            maxrows=10,
        )

        if cps_context.checkpoints:
            selectedCheckpointId = cps_context.checkpoints[
                cps_context.selectedListIndex
            ]["id"]

            isSelectedCheckpointInitial = (
                selectedCheckpointId == cps_context.checkpoints[-1]["id"]
            )

            isSelectedCheckpointActive = (
                selectedCheckpointId == cps_context.activeCheckpointId
            )

            isActionButtonsEnabled = (
                not isSelectedCheckpointActive
                if cps_context.activeCheckpointId
                else cps_context.selectedListIndex != 0
            )

            isBlenderDirty = bpy.data.is_dirty

            isFileModified = utils.check_is_modified(filepath)

            shouldShowError = (
                isActionButtonsEnabled and isFileModified
            ) or isBlenderDirty
            if shouldShowError:
                row = layout.row()
                row.label(
                    text="Changes without a checkpoint will be lost.", icon=_ERROR_ICON
                )

            row = layout.row()

            loadCol = row.column()
            loadCol.enabled = isActionButtonsEnabled
            loadOps = loadCol.operator(
                ops.LoadCheckpoint.bl_idname, text="Load", icon=_LOAD_ICON
            )
            loadOps.id = selectedCheckpointId

            deleteCol = row.column()
            deleteCol.enabled = (
                isActionButtonsEnabled and not isSelectedCheckpointInitial
            )
            deleteCol.operator(
                ops.DeleteCheckpoint.bl_idname,
                text="Delete",
                icon=utils.DELETE_ICON,
            )

            row = layout.row()

            exportCol = row.column()
            exportOps = exportCol.operator(
                ops.ExportCheckpoint.bl_idname, text="Export", icon="EXPORT"
            )
            exportOps.id = selectedCheckpointId

            editCol = row.column()
            editCol.enabled = not isSelectedCheckpointInitial
            editCol.operator(ops.EditCheckpoint.bl_idname, text="Edit", icon=_EDIT_ICON)


class CheckpointsList(bpy.types.UIList):
    """List of checkpoints of the current project."""

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        row = layout.row(align=True)

        activeCheckpointId = context.window_manager.cps.activeCheckpointId

        isActiveCheckpoint = (
            item.id == activeCheckpointId if activeCheckpointId else index == 0
        )

        col1 = row.column()
        col1.label(
            text=item.description,
            icon=_ACTIVE_CHECKPOINT_ICON if isActiveCheckpoint else _CHECKPOINT_ICON,
        )

        # Get last mofied string
        checkpoint_time = datetime.strptime(item.date, utils.CP_TIME_FORMAT)
        lastModified = utils.getLastModifiedStr(checkpoint_time)

        col2 = row.column()
        col2.alignment = "RIGHT"
        col2.ui_units_x = 2.5
        col2.label(text=lastModified)

    def draw_filter(self, context, layout):
        row = layout.row()

        subrow = row.row(align=True)
        subrow.prop(self, "filter_name", text="Search")
        subrow.prop(self, "use_filter_invert", text="", icon="ARROW_LEFTRIGHT")

    def filter_items(self, context, data, propname):
        checkpoints = getattr(data, propname)
        helper_funcs = bpy.types.UI_UL_list

        flt_flags = []

        # Filtering by name
        if self.filter_name:
            flt_flags = helper_funcs.filter_items_by_name(
                self.filter_name,
                self.bitflag_filter_item,
                checkpoints,
                "description",
            )

        return flt_flags, []
