from . import post_save


def register():
    post_save.register()


def unregister():
    post_save.unregister()
