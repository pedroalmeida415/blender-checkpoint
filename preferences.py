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

    my_bool_prop: bpy.props.BoolProperty(
        name="My Bool Prop",
        description="A bool property",
        default=False,
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "my_bool_prop")


class MYADDON_OT_my_operator(bpy.types.Operator):
    bl_idname = "myaddon.my_operator"
    bl_label = "My Operator"

    def execute(self, context):
        prefs = get_user_preferences(context)
        if prefs.my_bool_prop:
            print("My bool prop is True")
        else:
            print("My bool prop is False")
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        prefs = get_user_preferences(context)
        layout.prop(prefs, "my_bool_prop")


def register():
    bpy.utils.register_class(MyAddonPreferences)
    bpy.utils.register_class(MYADDON_OT_my_operator)


def unregister():
    bpy.utils.unregister_class(MyAddonPreferences)
    bpy.utils.unregister_class(MYADDON_OT_my_operator)


if __name__ == "__main__":
    register()
