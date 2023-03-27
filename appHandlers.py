import bpy
from bpy.app import handlers
from bpy.app.handlers import persistent


def regenFile():
    # Blender Revert (reload saved file)
    bpy.ops.wm.revert_mainfile()


@persistent
def savePostHandler(_):
    bpy.ops.object.post_save_commit('INVOKE_DEFAULT')


def register():
    print("Registering to Change Defaults")
    handlers.save_post.append(savePostHandler)


def unregister():
    print("Unregistering to Change Defaults")
    handlers.save_post.remove(savePostHandler)
