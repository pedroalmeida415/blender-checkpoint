import bpy
from bpy.app import handlers
from bpy.app.handlers import persistent

from . import app_preferences


@persistent
def savePostHandler(_):
    prefs = app_preferences.get_user_preferences()
    if prefs.shouldDisplayPostSaveDialog and bpy.ops.cps.post_save_dialog.poll():
        bpy.ops.cps.post_save_dialog('INVOKE_DEFAULT')

    if prefs.shouldAutoStart:
        bpy.ops.cps.start_version_control('INVOKE_DEFAULT')


def register():
    handlers.save_post.append(savePostHandler)


def unregister():
    handlers.save_post.remove(savePostHandler)
