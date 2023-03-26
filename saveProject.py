import os
import sys
import importlib

import bpy
from bpy.props import StringProperty

import pygit2 as git

# Local imports implemented to support Blender refreshes
modulesNames = ("gitHelpers", "reports", "sourceControl", "gitHelpers")
for module in modulesNames:
    if module in sys.modules:
        importlib.reload(sys.modules[module])
    else:
        parent = ".".join(__name__.split(".")[:-1])
        globals()[module] = importlib.import_module(f"{parent}.{module}")


class SimpleOperator(bpy.types.Operator):
    bl_idname = "object.simple_operator"
    bl_label = "Simple Object Operator"

    # Define a custom property
    try:
        defaultConfig = git.Config.get_global_config()
    except OSError:
        defaultConfig = {}

    defaultUser = (defaultConfig["user.name"]
                   if "user.name" in defaultConfig else "Artist")

    defaultEmail = (defaultConfig["user.email"]
                    if "user.email" in defaultConfig else "artist@example.com")

    username: StringProperty(
        name="User",
        default=defaultUser,
        description="Username of the artist",
        options={'TEXTEDIT_UPDATE'},
    )

    email: StringProperty(
        name="Email",
        default=defaultEmail,
        description="Email of the artist. Should be the same email as the one used in their version control platform account",
        options={'TEXTEDIT_UPDATE'},
    )

    description: StringProperty(
        name="Description",
        description="Short description of the changes you made",
        options={'TEXTEDIT_UPDATE'},
    )

    def execute(self, context):
        # Verificar helpers e funções de source control para ver se já não está implementado

        # Get the current .blend file name in order to add it to "Staged" on git
        # Commit changes using the "description" field as commmit message

        # The above is currently implemented with the GitCommit Operator, functioning on the GitPanel
        bpy.ops.git.commit(message=self.description)

        # Push changes to master after commit

        print(f"The value of description is: {self.description}")
        return {'FINISHED'}

    def invoke(self, context, event):
        # Display the dialog box

        return context.window_manager.invoke_props_dialog(self)

# Invoke the operator and display the dialog box


def register():
    bpy.utils.register_class(SimpleOperator)


def unregister():
    bpy.utils.unregister_class(SimpleOperator)
