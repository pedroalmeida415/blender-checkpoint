import sys
import importlib

import bpy
import pygit2 as git

# Local imports implemented to support Blender refreshes
modulesNames = ("gitHelpers", "sourceControl")
for module in modulesNames:
    if module in sys.modules:
        importlib.reload(sys.modules[module])
    else:
        parent = ".".join(__name__.split(".")[:-1])
        globals()[module] = importlib.import_module(f"{parent}.{module}")


NEW_PROJECT_ICON = 'NEWFOLDER'


class GitPostSaveDialog(bpy.types.Operator):
    """Dialog to commit changes after saving file"""

    bl_label = "Commit changes"
    bl_idname = "git.post_save_dialog"

    def invoke(self, context, event):
        wm = context.window_manager
        filepath = bpy.path.abspath("//")

        try:
            git.Repository(filepath)
            return wm.invoke_props_dialog(self)
        except git.GitError:
            # Make .gitignore file
            gitHelpers.makeGitIgnore(filepath)

            # Init git repo
            repo = git.init_repository(filepath)

            # REFACTOR TO USE LOCAL USER, DEFINED IN THE SAVE WINDOW
            # Get global/default git config if .gitconfig or .git/config exists
            try:
                defaultConfig = git.Config.get_global_config()
            except OSError:
                defaultConfig = {}

            username = (defaultConfig["user.name"]
                        if "user.name" in defaultConfig else "Blender Version Control")

            email = (defaultConfig["user.email"]
                     if "user.email" in defaultConfig else "blenderversioncontrol.415@gmail.com")

            # Configure git repo
            gitHelpers.configUser(repo, username, email)

            # Initial commit
            gitHelpers.commit(repo, "Initial commit - created project")

        return {'CANCELLED'}

    def draw(self, context):
        layout = self.layout
        layout.alignment = 'CENTER'
        layout.ui_units_x = 20

        row = layout.row()
        row.ui_units_y = 3

        col1 = row.column()
        col1.scale_x = 0.5
        col1.label(text="Description: ")

        col2 = row.column()
        col2.scale_y = 2
        col2.prop(context.window_manager.git, "commitMessage")

    def execute(self, context):
        message = context.window_manager.git.commitMessage

        if not message:
            self.report({'ERROR_INVALID_INPUT'},
                        "Description cannot be empty.")
            return {'CANCELLED'}

        operatorName = sourceControl.GitCommit.bl_idname.split(".")

        commitOperator = getattr(
            getattr(bpy.ops, operatorName[0]), operatorName[1])

        commitOperator('INVOKE_DEFAULT', message=message)

        return {'FINISHED'}


def register():
    bpy.utils.register_class(GitPostSaveDialog)


def unregister():
    bpy.utils.unregister_class(GitPostSaveDialog)
