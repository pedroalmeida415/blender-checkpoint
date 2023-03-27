import bpy
from bpy.app import handlers
from bpy.app.handlers import persistent


def regenFile(_):
    # Load new blend file
    bpy.ops.wm.read_homefile()
    # Regenerate blend file
    window = bpy.context.window_manager.windows[0]
    area = window.screen.areas[0]
    with bpy.context.temp_override(window=window, area=area):
        # Current area type
        currentType = area.type

        # Change area type to INFO and delete all content
        area.type = 'VIEW_3D'

        # Restore area type
        area.type = currentType


@persistent
def savePostHandler(_):
    bpy.ops.object.post_save_commit('INVOKE_DEFAULT')


def register():
    print("Registering to Change Defaults")
    handlers.save_post.append(savePostHandler)


def unregister():
    print("Unregistering to Change Defaults")
    handlers.save_post.remove(savePostHandler)
