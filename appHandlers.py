import bpy
from bpy.app import handlers
from bpy.app.handlers import persistent


@persistent
def savePostHandler(_):
    bpy.ops.git.post_save_dialog('INVOKE_DEFAULT')


def register():
    print("Registering to Change Defaults")
    handlers.save_post.append(savePostHandler)


def unregister():
    print("Unregistering to Change Defaults")
    handlers.save_post.remove(savePostHandler)
