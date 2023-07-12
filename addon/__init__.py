from . import ops
from . import ui
from . import props
from . import preferences
from . import handlers


def register():
    ops.register()
    props.register()
    ui.register()
    preferences.register()
    handlers.register()


def unregister():
    handlers.unregister()
    preferences.unregister()
    ui.unregister()
    props.unregister()
    ops.unregister()
