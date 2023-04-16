import sys
import importlib
from datetime import datetime

import bpy
from bpy.types import Panel, PropertyGroup, UIList
from bpy.props import (CollectionProperty, EnumProperty, IntProperty,
                       PointerProperty, StringProperty, BoolProperty)

# Local imports implemented to support Blender refreshes
modulesNames = ("helpers", "sourceControl")
for module in modulesNames:
    if module in sys.modules:
        importlib.reload(sys.modules[module])
    else:
        parent = ".".join(__name__.split(".")[:-1])
        globals()[module] = importlib.import_module(f"{parent}.{module}")


TIMELINE_ICON = 'WINDOW'
CHECKPOINT_ICON = 'KEYFRAME'
ACTIVE_CHECKPOINT_ICON = 'KEYTYPE_KEYFRAME_VEC'
LOAD_ICON = 'DECORATE_OVERRIDE'
ADD_ICON = 'ADD'
EDIT_ICON = 'OUTLINER_DATA_GP_LAYER' if (
    3, 0, 0) > bpy.app.version else 'CURRENT_FILE'
CLEAR_ICON = 'X'
CHECKPOINTS_DISK_USAGE_ICONS = ('IMPORT', 'FILE_BLEND')
PROTECTED_ICON = "FAKE_USER_ON"
DELETE_ICON = "TRASH"


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

        activeTimeline = state.get("active_timeline")

        timelinesList = []
        for index, timeline in enumerate(timelines):
            if timeline == activeTimeline:
                index = -1
            timelinesList.append((timeline, timeline, f"Timeline: '{timeline}'",
                                  TIMELINE_ICON, index))

        return timelinesList

    def setActiveTimeline(self, context):
        filepath = bpy.path.abspath("//")

        # Ensure value is not active timeline
        value = context.window_manager.cps.timelines
        # TODO think about how to get current active timeline
        activeTimeline = repo.head.shorthand

        if value == activeTimeline:
            return

        # TODO Get timeline fullname
        timeline = repo.lookup_branch(value)
        if not timeline:
            return

        # TODO Checkout timeline
        ref = repo.lookup_reference(timeline.name)
        repo.checkout(ref)

        # TODO probably should have a file inside .checkpoints that refers to the current state of the addon "_persisted_state.json"
        # that will serve as what was being done through Git config
        # repo.config["user.currentCommit"] = str(repo.head.target)

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
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_category = 'Scene'


# Mover para "Source control"
class StartVersionControl(bpy.types.Operator):
    '''Initialize version control on the current project'''

    bl_idname = "cps.start_version_control"
    bl_label = "Start Version Control"

    def execute(self, context):
        filepath = bpy.path.abspath("//")
        filename = bpy.path.basename(bpy.data.filepath)

        cps = context.window_manager.cps

        if cps.isInitialized:
            return {'CANCELLED'}

        helpers.initialize_version_control(filepath, filename)

        cps.isInitialized = True

        self.report({"INFO"}, "Checkpoints initialized!")
        return {'FINISHED'}


class CheckpointsPanel(CheckpointsPanelMixin, Panel):
    bl_idname = "CPS_PT_checkpoints"
    bl_label = "Checkpoints"

    def draw(self, context):
        filepath = bpy.path.abspath("//")
        cps_context = context.window_manager.cps

        if cps_context.isInitialized:
            pass

        # TODO ajustart lógica
        try:
            helpers.getRepo(filepath)
            cps_context.isInitialized = True
            pass
        except GitError:
            layout = self.layout

            row = layout.row()
            row.operator(StartVersionControl.bl_idname,
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

        split = layout.split(factor=0.8)

        activeCheckpointId = context.window_manager.cps.activeCheckpointId

        isActiveCommit = item.id == activeCheckpointId if activeCheckpointId else index == 0

        col1 = split.column()
        col1.label(text=item.description,
                   icon=ACTIVE_CHECKPOINT_ICON if isActiveCommit else CHECKPOINT_ICON)

        # Get last mofied string
        commitTime = datetime.strptime(item.date, helpers.CP_TIME_FORMAT)
        lastModified = helpers.getLastModifiedStr(commitTime)

        col2 = split.column()
        col2.label(text=lastModified)


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

        tl_ops = row.operator(sourceControl.GitNewBranch.bl_idname,
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
        # TODO refatorar lógica
        try:
            repo = helpers.getRepo(filepath)
        except GitError:
            return {'CANCELLED'}

        # TODO refatorar lógica
        is_original_timeline = repo.head.shorthand == "original"

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
            # TODO refatorar operador
            row.operator(sourceControl.GitDeleteBranch.bl_idname,
                         text="Delete Timeline")


class EditTimelinePanel(CheckpointsPanelMixin, Panel):
    """Edit timeline name"""

    bl_idname = "CPS_PT_edit_timeline_panel"
    bl_label = ""
    bl_options = {'INSTANCED'}

    def draw(self, context):
        filepath = bpy.path.abspath("//")
        # TODO
        try:
            repo = helpers.getRepo(filepath)
        except GitError:
            return {'CANCELLED'}

        # TODO
        is_original_timeline = repo.head.shorthand == "original"

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

            # TODO
            operator = row.operator(sourceControl.GitEditBranch.bl_idname,
                                    text="Rename")
            operator.name = name


class SwitchTimelineErrorTooltip(CheckpointsPanelMixin, Panel):
    """You must save a checkpoint of your changes before switching timelines."""

    bl_idname = "CPS_PT_switch_timeline_error_panel"
    bl_label = ""
    bl_options = {'INSTANCED'}

    def draw(self, context):
        layout = self.layout
        layout.ui_units_x = 17.5

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
        filename = bpy.path.basename(bpy.data.filepath)

        # TODO
        try:
            repo = helpers.getRepo(filepath)
        except GitError:
            return

        layout = self.layout

        row = layout.row()
        row.prop(context.window_manager.cps, "timelines")

        row_button = layout.row(align=True)
        row_button.scale_x = 0.8

        isFileModified = str(
            GIT_STATUS_INDEX_MODIFIED) in str(repo.status_file(f"{filename}"))

        if isFileModified:
            row.enabled = False
            row_button.popover(
                SwitchTimelineErrorTooltip.bl_idname, icon="ERROR")
        else:
            row_button.popover(NewTimelinePanel.bl_idname,
                               icon=ADD_ICON)
            row_button.popover(DeleteTimelinePanel.bl_idname,
                               icon=DELETE_ICON)
            row_button.popover(EditTimelinePanel.bl_idname,
                               icon=EDIT_ICON)

    def draw(self, context):
        filepath = bpy.path.abspath("//")
        filename = bpy.path.basename(bpy.data.filepath)

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
            item_dyntip_propname="message",
            sort_lock=True,
            rows=5,
            maxrows=10
        )

        if cps_context.checkpoints:
            # TODO
            try:
                repo = helpers.getRepo(filepath)
            except GitError:
                return

            selectedCheckpoint = repo.revparse_single(
                f'HEAD~{cps_context.selectedListIndex}')

            isSelectedCommitInitial = selectedCheckpoint.hex == cps_context.checkpoints[-1]["id"]

            isSelectedCommitCurrent = selectedCheckpoint.hex == cps_context.activeCheckpointId

            isActionButtonsEnabled = not isSelectedCommitCurrent if cps_context.activeCheckpointId else cps_context.selectedListIndex != 0

            isBlenderDirty = bpy.data.is_dirty

            isFileModified = str(
                GIT_STATUS_INDEX_MODIFIED) in str(repo.status_file(f"{filename}.blend"))

            shouldShowError = (
                isActionButtonsEnabled and isFileModified) or isBlenderDirty
            if shouldShowError:
                row = layout.row()
                row.label(
                    text="Changes without backup will be lost.", icon='ERROR')

            row = layout.row()

            swtichCol = row.column()
            swtichCol.enabled = isActionButtonsEnabled
            # TODO Add Edit and Export methods
            # TODO change icon "export" of add method
            switchOps = swtichCol.operator(sourceControl.GitRevertToCommit.bl_idname,
                                           text="Load", icon="EXPORT")
            switchOps.id = selectedCheckpoint.hex

            removeCol = row.column()
            removeCol.enabled = isActionButtonsEnabled and not isSelectedCommitInitial
            delOps = removeCol.operator(sourceControl.GitRemoveCommit.bl_idname,
                                        text="Delete", icon=DELETE_ICON)
            delOps.id = selectedCheckpoint.hex

            '''
            EDIT AND UNDO PREVIOUS COMMIT WIP
            '''
            # row = layout.row()

            # swtichCol = row.column()
            # swtichCol.enabled = isActionButtonsEnabled
            # switchOps = swtichCol.operator(sourceControl.GitRevertToCommit.bl_idname,
            #                                text="Undo last", icon="LOOP_BACK")
            # switchOps.id = selectedCheckpoint.hex

            # removeCol = row.column()
            # removeCol.enabled = isActionButtonsEnabled and not isSelectedCommitInitial
            # delOps = removeCol.operator(sourceControl.GitRemoveCommit.bl_idname,
            #                             text="Edit", icon="CURRENT_FILE")
            # delOps.id = selectedCheckpoint.hex

        bpy.app.timers.register(addCheckpointsToList)


def addCheckpointsToList():
    """Add checkpoints to list"""

    cps_context = bpy.context.window_manager.cps

    # Get list
    checkpoints = cps_context.checkpoints

    # Clear list
    checkpoints.clear()

    filepath = bpy.path.abspath("//")
    # TODO
    try:
        repo = helpers.getRepo(filepath)
    except GitError:
        return

    # TODO consume JSON state
    cps_context.activeCheckpointId = repo.config["user.currentCommit"]
    cps_context.diskUsage = int(
        repo.config["user.diskUsage"])

    cps = helpers.getCommits(repo)
    for cp in cps:
        item = cps.add()
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
        commitCol = row.column()

        message = context.window_manager.cps.checkpointDescription
        if not message:
            commitCol.enabled = False

        # TODO
        commit = commitCol.operator(sourceControl.GitCommit.bl_idname)
        commit.message = message

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
            text=f"Checkpoints disk usage: {format_size(diskUsage)}")


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
classes = (CheckpointsListItem, CheckpointsPanelData, StartVersionControl, CheckpointsPanel,
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