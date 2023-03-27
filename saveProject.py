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


class GitPostSaveProject(bpy.types.Operator):
    """Save project Git settings"""

    bl_label = "Save Project"
    bl_idname = "object.post_save_commit"

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

            # Get global/default git config if .gitconfig or .git/config exists
            try:
                defaultConfig = git.Config.get_global_config()
            except OSError:
                defaultConfig = {}

            username = (defaultConfig["user.name"]
                        if "user.name" in defaultConfig else "Artist")

            email = (defaultConfig["user.email"]
                     if "user.email" in defaultConfig else "artist@example.com")

            # Configure git repo
            gitHelpers.configUser(repo, username, email)

            # Initial commit
            gitHelpers.commit(repo, "Initial commit - created project")

        return {'CANCELLED'}

    def draw(self, context):
        layout = self.layout
        layout.alignment = 'CENTER'

        row = layout.row()

        col1 = row.column()
        col1.scale_x = 0.5
        col1.label(text="Message: ")

        col2 = row.column()
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
    bpy.utils.register_class(GitPostSaveProject)


def unregister():
    bpy.utils.unregister_class(GitPostSaveProject)
