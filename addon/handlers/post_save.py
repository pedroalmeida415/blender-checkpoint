import bpy
from bpy.app.handlers import persistent

from .. import utils


@persistent
def postSaveHandler(_):
    prefs = utils.prefs()
    if prefs.shouldDisplayPostSaveDialog and bpy.ops.cps.post_save_dialog.poll():
        bpy.ops.cps.post_save_dialog("INVOKE_DEFAULT")

    if prefs.shouldAutoStart:
        bpy.ops.cps.start_version_control("INVOKE_DEFAULT")


def register():
    bpy.app.handlers.save_post.append(postSaveHandler)


def unregister():
    bpy.app.handlers.save_post.remove(postSaveHandler)
