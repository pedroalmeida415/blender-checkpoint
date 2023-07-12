import bpy

from .start_version_control import StartVersionControl
from .rename_project import RenameProject
from .timeline_add import NewTimeline
from .timeline_delete import DeleteTimeline
from .timeline_edit import RenameTimeline
from .checkpoint_delete import DeleteCheckpoint
from .checkpoint_load import LoadCheckpoint
from .checkpoint_add import AddCheckpoint, PostSaveDialog
from .checkpoint_edit import EditCheckpoint
from .checkpoint_export import ExportCheckpoint


classes = [
    NewTimeline,
    DeleteTimeline,
    RenameTimeline,
    StartVersionControl,
    RenameProject,
    LoadCheckpoint,
    AddCheckpoint,
    DeleteCheckpoint,
    ExportCheckpoint,
    EditCheckpoint,
    PostSaveDialog,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
