import sys
import importlib
from datetime import datetime
import textwrap

import bpy
from bpy.types import Panel, PropertyGroup, UIList
from bpy.props import (CollectionProperty, EnumProperty, IntProperty,
                       PointerProperty, StringProperty, BoolProperty)

# Local imports implemented to support Blender refreshes
modulesNames = ("helpers", "operators")
for module in modulesNames:
    if module in sys.modules:
        importlib.reload(sys.modules[module])
    else:
        parent = ".".join(__name__.split(".")[:-1])
        globals()[module] = importlib.import_module(f"{parent}.{module}")


TIMELINE_ICON = 'WINDOW'
CHECKPOINT_ICON = 'KEYFRAME'
ACTIVE_CHECKPOINT_ICON = 'KEYTYPE_KEYFRAME_VEC'
LOAD_ICON = 'IMPORT'
ADD_ICON = 'ADD'
EDIT_ICON = 'OUTLINER_DATA_GP_LAYER' if (
    3, 0, 0) > bpy.app.version else 'CURRENT_FILE'
CLEAR_ICON = 'X'
CHECKPOINTS_DISK_USAGE_ICONS = ('PACKAGE', 'FILE_BLEND')
PROTECTED_ICON = "FAKE_USER_ON"
DELETE_ICON = "TRASH"
ERROR_ICON = "ERROR"


class CheckpointsListItem(PropertyGroup):
    id: StringProperty(description="Unique ID of checkpoint")
    date: StringProperty(description="Date of checkpoint")
    description: StringProperty(description="Checkpoint description")

# def errorPopupDraw(self, context):
#     self.layout.label(text="You have done something you shouldn't do!")
# bpy.context.window_manager.popup_menu(errorPopupDraw, title="Error", icon='ERROR')


class CheckpointsPanelData(PropertyGroup):
    def getTimelines(self, context):
        filepath = bpy.path.abspath("//")
        state = helpers.get_state(filepath)
        timelines = helpers.listall_timelines(filepath)

        currentTimeline = state["current_timeline"]

        timelinesList = []
        for index, timeline in enumerate(timelines):
            if timeline == currentTimeline:
                index = -1
            tl_format_name = timeline.replace(".json", "")
            timelinesList.append((timeline, tl_format_name, f"Timeline: '{tl_format_name}'",
                                  TIMELINE_ICON, index))

        return timelinesList

    def setActiveTimeline(self, context):
        filepath = bpy.path.abspath("//")
        state = helpers.get_state(filepath)
        timelines = helpers.listall_timelines(filepath)

        selectedTimeline = context.window_manager.cps.timelines
        currentTimeline = state["current_timeline"]

        if not selectedTimeline in timelines or selectedTimeline == currentTimeline:
            return

        helpers.switch_timeline(filepath, selectedTimeline)

        # Load the reverted file
        bpy.ops.wm.revert_mainfile()

    timelines: EnumProperty(
        name="Timeline",
        description="Current timeline",
        items=getTimelines,
        default=-1,
        options={'ANIMATABLE'},
        update=setActiveTimeline
    )

    newTimelineName: StringProperty(
        name="Name",
        options={'TEXTEDIT_UPDATE'},
        description="New timeline name (will be slugified)"
    )

    checkpointDescription: StringProperty(
        name="",
        options={'TEXTEDIT_UPDATE'},
        description="A short description of the changes made"
    )

    checkpoints: CollectionProperty(type=CheckpointsListItem)

    selectedListIndex: IntProperty(default=0)

    activeCheckpointId: StringProperty(
        name="",
        description="Current/last active checkpoint ID"
    )

    diskUsage: IntProperty(default=0)

    isInitialized: BoolProperty(
        name="Version Control Status",
        default=False,
    )

    new_tl_keep_history: BoolProperty(
        name=" Keep history",
        default=True,
        description="Carry previous checkpoints over to the new timeline"
    )


class CheckpointsPanelMixin:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'


def _label_multiline(context, text, parent, icon="NONE"):
    chars = int(context.region.width / 8)   # 7 pix on 1 character
    wrapper = textwrap.TextWrapper(width=chars)
    text_lines = wrapper.wrap(text=text)
    for i, text_line in enumerate(text_lines):
        if i == 0:
            parent.label(text=text_line, icon=icon)
            continue
        parent.label(text=text_line)


class CheckpointsPanel(CheckpointsPanelMixin, Panel):
    bl_idname = "CPS_PT_checkpoints"
    bl_label = "Checkpoints"

    def draw(self, context):
        filepath = bpy.path.abspath("//")
        filename = bpy.path.basename(bpy.data.filepath)

        cps_context = context.window_manager.cps

        if cps_context.isInitialized:
            pass

        layout = self.layout

        try:
            state = helpers.get_state(filepath)
            if state["filename"] != filename:
                row = layout.row()
                row.alignment = "CENTER"
                row.label(
                    text="WARNING: Project name has changed", icon="ERROR")
                row = layout.row()
                row.alignment = "CENTER"
                row.label(
                    text="If this is intentional, click the button below")
                row = layout.row()
                renameOps = row.operator(operators.RenameProject.bl_idname)
                renameOps.name = filename

                layout.separator()

                text = 'This happens when you rename the project file, or when you have other projects in the same folder and one of them already initialized the addon before.'
                _label_multiline(
                    context=context,
                    text=text,
                    parent=layout,
                    icon="QUESTION"
                )

                layout.separator()

                text = 'Keep in mind that separate projects need to have dedicated folders for each of them for the addon to work properly.'
                _label_multiline(
                    context=context,
                    text=text,
                    parent=layout,
                    icon="INFO"
                )
                return

            cps_context.isInitialized = True
            addCheckpointsToList()
            pass
        except FileNotFoundError:
            row = layout.row()
            row.operator(operators.StartGame.bl_idname,
                         text="Start", icon=TIMELINE_ICON)
            if not bpy.data.is_saved:
                row.enabled = False
                row = layout.row()
                row.alignment = "CENTER"
                row.label(text="You must save your project first")


class CheckpointsList(UIList):
    """List of checkpoints of the current project."""

    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):
        row = layout.row(align=True)

        activeCheckpointId = context.window_manager.cps.activeCheckpointId

        isActiveCheckpoint = item.id == activeCheckpointId if activeCheckpointId else index == 0

        col1 = row.column()
        col1.label(text=item.description,
                   icon=ACTIVE_CHECKPOINT_ICON if isActiveCheckpoint else CHECKPOINT_ICON)

        # Get last mofied string
        checkpoint_time = datetime.strptime(item.date, helpers.CP_TIME_FORMAT)
        lastModified = helpers.getLastModifiedStr(checkpoint_time)

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
                self.filter_name, self.bitflag_filter_item, checkpoints, "description",)

        return flt_flags, []


class NewTimelinePanel(CheckpointsPanelMixin, Panel):
    """Add new timeline"""

    bl_idname = "CPS_PT_new_timeline_panel"
    bl_label = ""
    bl_options = {'INSTANCED'}

    def draw(self, context):
        cps_context = context.window_manager.cps

        layout = self.layout
        layout.ui_units_x = 11.5

        layout.label(text="New Timeline from selected checkpoint",
                     icon=TIMELINE_ICON)

        layout.prop(cps_context, "newTimelineName")
        name = cps_context.newTimelineName

        row = layout.row()
        row.prop(cps_context, "new_tl_keep_history")
        new_tl_keep_history = cps_context.new_tl_keep_history

        row = layout.row()
        if not name:
            row.enabled = False

        tl_ops = row.operator(operators.NewTimeline.bl_idname,
                              text="Create Timeline")
        tl_ops.name = name
        tl_ops.new_tl_keep_history = new_tl_keep_history


class DeleteTimelinePanel(CheckpointsPanelMixin, Panel):
    """Deletes current Timeline"""

    bl_idname = "CPS_PT_delete_timeline_panel"
    bl_label = ""
    bl_options = {'INSTANCED'}

    def draw(self, context):
        filepath = bpy.path.abspath("//")
        state = helpers.get_state(filepath)
        currentTimeline = state.get("current_timeline")

        is_original_timeline = currentTimeline == helpers.ORIGINAL_TL

        layout = self.layout

        if is_original_timeline:
            layout.ui_units_x = 11.5
            row = layout.row()
            row.label(
                text='You cannot delete the original timeline', icon=PROTECTED_ICON)
        else:
            layout.ui_units_x = 16.5
            layout.separator()

            row = layout.row()
            row.alignment = 'CENTER'
            row.label(text="ARE YOU SURE?")

            layout.separator()

            row = layout.row()
            row.label(
                text='This will delete the current timeline. There is no going back.', icon=DELETE_ICON)

            row = layout.row()
            row.operator(operators.DeleteTimeline.bl_idname,
                         text="Delete Timeline")


class EditTimelinePanel(CheckpointsPanelMixin, Panel):
    """Edit timeline name"""

    bl_idname = "CPS_PT_edit_timeline_panel"
    bl_label = ""
    bl_options = {'INSTANCED'}

    def draw(self, context):
        filepath = bpy.path.abspath("//")
        state = helpers.get_state(filepath)
        currentTimeline = state.get("current_timeline")

        is_original_timeline = currentTimeline == helpers.ORIGINAL_TL

        layout = self.layout

        if is_original_timeline:
            layout.ui_units_x = 11.5
            row = layout.row()
            row.label(
                text='You cannot edit the original timeline', icon=PROTECTED_ICON)
        else:
            cps_context = context.window_manager.cps

            layout.label(text="Edit Timeline name", icon=TIMELINE_ICON)

            layout.prop(cps_context, "newTimelineName")
            name = cps_context.newTimelineName

            row = layout.row()
            if not name:
                row.enabled = False

            operator = row.operator(operators.RenameTimeline.bl_idname,
                                    text="Rename")
            operator.name = name


class SwitchTimelineErrorTooltip(CheckpointsPanelMixin, Panel):
    """You must add a checkpoint with your changes before switching timelines."""

    bl_idname = "CPS_PT_switch_timeline_error_panel"
    bl_label = ""
    bl_options = {'INSTANCED'}

    def draw(self, context):
        layout = self.layout
        layout.ui_units_x = 19

        row = layout.row()
        row.label(text=self.bl_description)


class SubPanelList(CheckpointsPanelMixin, Panel):
    bl_idname = "CPS_PT_sub_panel_list"
    bl_parent_id = CheckpointsPanel.bl_idname
    bl_label = ""
    bl_options = {'DEFAULT_CLOSED'}

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
        isFileModified = helpers.check_is_modified(filepath)

        if isFileModified:
            row.enabled = False
            row_button.popover(
                SwitchTimelineErrorTooltip.bl_idname, icon=ERROR_ICON)
        else:
            row_button.popover(NewTimelinePanel.bl_idname,
                               icon=ADD_ICON)
            row_button.popover(DeleteTimelinePanel.bl_idname,
                               icon=DELETE_ICON)
            row_button.popover(EditTimelinePanel.bl_idname,
                               icon=EDIT_ICON)

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
            maxrows=10
        )

        if cps_context.checkpoints:
            selectedCheckpointId = cps_context.checkpoints[cps_context.selectedListIndex]["id"]

            isSelectedCheckpointInitial = selectedCheckpointId == cps_context.checkpoints[-1]["id"]

            isSelectedCheckpointActive = selectedCheckpointId == cps_context.activeCheckpointId

            isActionButtonsEnabled = not isSelectedCheckpointActive if cps_context.activeCheckpointId else cps_context.selectedListIndex != 0

            isBlenderDirty = bpy.data.is_dirty

            isFileModified = helpers.check_is_modified(filepath)

            shouldShowError = (
                isActionButtonsEnabled and isFileModified) or isBlenderDirty
            if shouldShowError:
                row = layout.row()
                row.label(
                    text="Changes without a checkpoint will be lost.", icon=ERROR_ICON)

            row = layout.row()

            loadCol = row.column()
            loadCol.enabled = isActionButtonsEnabled
            loadOps = loadCol.operator(operators.LoadCheckpoint.bl_idname,
                                       text="Load", icon=LOAD_ICON)
            loadOps.id = selectedCheckpointId

            deleteCol = row.column()
            deleteCol.enabled = isActionButtonsEnabled and not isSelectedCheckpointInitial
            deleteCol.operator(operators.DeleteCheckpoint.bl_idname,
                               text="Delete", icon=DELETE_ICON)

            row = layout.row()

            exportCol = row.column()
            exportOps = exportCol.operator(operators.ExportCheckpoint.bl_idname,
                                           text="Export", icon="EXPORT")
            exportOps.id = selectedCheckpointId

            editCol = row.column()
            editCol.enabled = not isSelectedCheckpointInitial
            editCol.operator(operators.EditCheckpoint.bl_idname,
                             text="Edit", icon=EDIT_ICON)

        bpy.app.timers.register(addCheckpointsToList)


def addCheckpointsToList():
    """Add checkpoints to list"""
    filepath = bpy.path.abspath("//")
    state = helpers.get_state(filepath)

    cps_context = bpy.context.window_manager.cps

    # Get list
    checkpoints = cps_context.checkpoints

    # Clear list
    checkpoints.clear()

    # TODO refatorar - não é mais necessário setar o active checkpoint aqui
    cps_context.activeCheckpointId = state["active_checkpoint"]
    cps_context.diskUsage = state["disk_usage"]

    current_timeline = state["current_timeline"]
    cps = helpers.get_checkpoints(filepath, current_timeline)
    for cp in cps:
        item = checkpoints.add()
        item.id = cp["id"]
        item.date = cp["date"]
        item.description = cp["description"]


class SubPanelAdd(CheckpointsPanelMixin, Panel):
    bl_idname = "CPS_PT_sub_panel_add"
    bl_parent_id = CheckpointsPanel.bl_idname
    bl_label = ""
    bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        return context.window_manager.cps.isInitialized

    def draw(self, context):
        layout = self.layout
        layout.alignment = 'CENTER'

        row = layout.row(align=True)

        col1 = row.column()
        col1.alignment = 'LEFT'
        col1.label(text="Description: ")

        col2 = row.column()
        col2.alignment = 'EXPAND'
        col2.prop(context.window_manager.cps, "checkpointDescription")

        row = layout.row()
        row.scale_y = 2
        addCol = row.column()

        description = context.window_manager.cps.checkpointDescription
        if not description:
            addCol.enabled = False

        checkpoint = addCol.operator(operators.AddCheckpoint.bl_idname)
        checkpoint.description = description

        layout.separator()

        diskUsage = context.window_manager.cps.diskUsage

        row = layout.row()
        col1 = row.column()
        subRow = col1.row(align=True)
        subRow.label(text="", icon=CHECKPOINTS_DISK_USAGE_ICONS[0])
        subRow.label(text="", icon=CHECKPOINTS_DISK_USAGE_ICONS[1])

        col2 = row.column()
        col2.alignment = 'RIGHT'
        col2.label(
            text=f"Disk space used: {format_size(diskUsage)}")


def format_size(size):
    # Convert bytes to megabytes
    size = size / (1024 * 1024)
    if size < 999:
        return f"{size:.2f} MB"
    else:
        # Convert megabytes to gigabytes
        size = size / 1024
        return f"{size:.2f} GB"


"""ORDER MATTERS"""
classes = (CheckpointsListItem, CheckpointsPanelData, CheckpointsPanel,
           CheckpointsList, NewTimelinePanel, DeleteTimelinePanel, EditTimelinePanel, SwitchTimelineErrorTooltip, SubPanelList,
           SubPanelAdd)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.WindowManager.cps = PointerProperty(type=CheckpointsPanelData)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
