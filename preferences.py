import bpy


def get_user_preferences(context=None):
    """Intermediate method for pre and post blender 2.8 grabbing preferences"""
    if not context:
        context = bpy.context
    prefs = None
    if hasattr(context, "user_preferences"):
        prefs = context.user_preferences.addons.get(__package__, None)
    elif hasattr(context, "preferences"):
        prefs = context.preferences.addons.get(__package__, None)
    if prefs:
        return prefs.preferences
    # To make the addon stable and non-exception prone, return None
    # raise Exception("Could not fetch user preferences")
    return None


class MyAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    shouldDisplayCommitDialog: bpy.props.BoolProperty(
        name="Commit Dialog",
        description="Should display commit dialog after save",
        default=False,
    )

    def draw(self, context):
        layout = self.layout

        layout.prop(self, "shouldDisplayCommitDialog")
        layout.separator()

        layout.prop(self, "commitDialog")


def register():
    bpy.utils.register_class(MyAddonPreferences)


def unregister():
    bpy.utils.unregister_class(MyAddonPreferences)


if __name__ == "__main__":
    register()
