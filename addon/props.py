import bpy

from . import config
from . import utils


class CheckpointsListItem(bpy.types.PropertyGroup):
    id: bpy.props.StringProperty(description="Unique ID of checkpoint")
    date: bpy.props.StringProperty(description="Date of checkpoint")
    description: bpy.props.StringProperty(description="Checkpoint description")


class CheckpointsPanelData(bpy.types.PropertyGroup):
    def getTimelines(self, context):
        filepath = bpy.path.abspath("//")
        state = config.get_state(filepath)
        timelines = utils.listall_timelines(filepath)

        currentTimeline = state["current_timeline"]

        timelinesList = []
        for index, timeline in enumerate(timelines):
            if timeline == currentTimeline:
                index = -1
            tl_format_name = timeline.replace(".json", "")
            timelinesList.append(
                (
                    timeline,
                    tl_format_name,
                    f"Timeline: '{tl_format_name}'",
                    utils.TIMELINE_ICON,
                    index,
                )
            )

        return timelinesList

    def setActiveTimeline(self, context):
        filepath = bpy.path.abspath("//")
        state = config.get_state(filepath)
        timelines = utils.listall_timelines(filepath)

        selectedTimeline = context.window_manager.checkpoint.timelines
        currentTimeline = state["current_timeline"]

        if not selectedTimeline in timelines or selectedTimeline == currentTimeline:
            return

        utils.switch_timeline(filepath, selectedTimeline)

        # Load the reverted file
        bpy.ops.wm.revert_mainfile()

    timelines: bpy.props.EnumProperty(
        name="Timeline",
        description="Current timeline",
        items=getTimelines,
        default=utils.TIMELINES_DEFAULT_POLYFILL_2_83,
        options={"ANIMATABLE"},
        update=setActiveTimeline,
    )

    newTimelineName: bpy.props.StringProperty(
        name="Name",
        options={"TEXTEDIT_UPDATE"},
        description="New timeline name (will be slugified)",
    )

    checkpointDescription: bpy.props.StringProperty(
        name="",
        options={"TEXTEDIT_UPDATE"},
        description="A short description of the changes made",
    )

    checkpoints: bpy.props.CollectionProperty(type=CheckpointsListItem)

    selectedListIndex: bpy.props.IntProperty(default=0)

    activeCheckpointId: bpy.props.StringProperty(
        name="", description="Current/last active checkpoint ID"
    )

    diskUsage: bpy.props.IntProperty(default=0)

    isInitialized: bpy.props.BoolProperty(
        name="Version Control Status",
        default=False,
    )

    new_tl_keep_history: bpy.props.BoolProperty(
        name=" Keep history",
        default=True,
        description="Carry previous checkpoints over to the new timeline",
    )

    should_display_dialog__: bpy.props.BoolProperty(
        name="Internal dialog control",
        default=True,
    )


"""ORDER MATTERS"""
classes = (
    CheckpointsListItem,
    CheckpointsPanelData,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.WindowManager.checkpoint = bpy.props.PointerProperty(
        type=CheckpointsPanelData
    )


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.WindowManager.checkpoint
