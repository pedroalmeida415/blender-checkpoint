import bpy

from .main_panel import MainPanel
from .timeline_add_panel import NewTimelinePanel
from .timeline_delete_panel import DeleteTimelinePanel
from .timeline_edit_panel import EditTimelinePanel
from .checkpoints_list_panel import SubPanelCheckpointsList, CheckpointsList
from .checkpoint_add_panel import SubPanelCheckpointAdd
from .tooltip import SwitchTimelineErrorTooltip


"""ORDER MATTERS"""
classes = [
    MainPanel,
    CheckpointsList,
    NewTimelinePanel,
    DeleteTimelinePanel,
    EditTimelinePanel,
    SwitchTimelineErrorTooltip,
    SubPanelCheckpointsList,
    SubPanelCheckpointAdd,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
