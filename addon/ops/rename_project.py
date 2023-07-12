import bpy

from .. import config


class RenameProject(bpy.types.Operator):
    """Saves project new name to correctly manage checkpoints"""

    bl_idname = "checkpoint.rename_project"
    bl_label = "Confirm rename and continue"

    name: bpy.props.StringProperty(name="", description="new name of project")

    def execute(self, context):
        filepath = bpy.path.abspath("//")

        config.set_state(filepath, "filename", self.name)

        self.report({"INFO"}, "Renamed successfully, all set!")
        return {"FINISHED"}
