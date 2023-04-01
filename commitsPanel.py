import sys
import importlib
from datetime import datetime

import bpy
from bpy.types import Panel, PropertyGroup, UIList
from bpy.props import (CollectionProperty, EnumProperty, IntProperty,
                       PointerProperty, StringProperty)

from pygit2._pygit2 import GitError
from pygit2 import GIT_STATUS_CURRENT

# Local imports implemented to support Blender refreshes
modulesNames = ("gitHelpers", "sourceControl")
for module in modulesNames:
    if module in sys.modules:
        importlib.reload(sys.modules[module])
    else:
        parent = ".".join(__name__.split(".")[:-1])
        globals()[module] = importlib.import_module(f"{parent}.{module}")


# BRANCH_ICON = 'GRAPH'
# BRANCH_ICON = 'MOD_SIMPLIFY'
# BRANCH_ICON = 'EVENT_TAB'
# BRANCH_ICON = 'ORIENTATION_VIEW'
BRANCH_ICON = 'WINDOW'

# COMMENT_ICON = 'RADIOBUT_OFF'
# ACTIVE_COMMENT_ICON = 'RADIOBUT_ON'
# COMMENT_ICON = 'HIDE_ON'
# ACTIVE_COMMENT_ICON = 'HIDE_OFF'
COMMENT_ICON = 'KEYFRAME'
ACTIVE_COMMENT_ICON = 'KEYTYPE_KEYFRAME_VEC'

# SWITCH_ICON = 'LOOP_BACK'
# SWITCH_ICON = 'CON_TRACKTO'
# SWITCH_ICON = 'UV_SYNC_SELECT'
SWITCH_ICON = 'DECORATE_OVERRIDE'

NEW_BRANCH_ICON = 'ADD'
CLEAR_ICON = 'X'


class GitCommitsListItem(PropertyGroup):
    id: StringProperty(description="Unique ID of commit")
    name: StringProperty(description="Name of commiter")
    email: StringProperty(description="Email of commiter")
    date: StringProperty(description="Date of commit")
    message: StringProperty(description="Commit message")


class GitPanelData(PropertyGroup):
    def getBranches(self, context):
        filepath = bpy.path.abspath("//")
        try:
            repo = gitHelpers.getRepo(filepath)
        except GitError:
            return []

        branches = repo.listall_branches()
        activeBranch = repo.head.shorthand

        branchList = []
        for index, branch in enumerate(branches):
            if branch == activeBranch:
                index = -1
            branchList.append((branch, branch, f"Branch: '{branch}'",
                               BRANCH_ICON, index))

        return branchList

    def setActiveBranch(self, context):
        filepath = bpy.path.abspath("//")

        try:
            repo = gitHelpers.getRepo(filepath)
        except GitError:
            return

        # Ensure value is not active branch
        value = context.window_manager.git.branches
        activeBranch = repo.head.shorthand
        if value == activeBranch:
            return

        # Get branch fullname
        branch = repo.lookup_branch(value)
        if not branch:
            return

        # Checkout branch
        ref = repo.lookup_reference(branch.name)
        repo.checkout(ref)

        # Load the reverted file
        bpy.ops.wm.revert_mainfile()

    branches: EnumProperty(
        name="Branch",
        description="Current Branch",
        items=getBranches,
        default=-1,
        options={'ANIMATABLE'},
        update=setActiveBranch
    )

    newBranchName: StringProperty(
        name="Name",
        options={'TEXTEDIT_UPDATE'},
        description="Name of new Branch"
    )

    commitMessage: StringProperty(
        name="",
        options={'TEXTEDIT_UPDATE'},
        description="A short description of the changes made"
    )

    commitsList: CollectionProperty(type=GitCommitsListItem)

    commitsListIndex: IntProperty(default=0)

    currentCommitId: StringProperty(
        name="",
        description="Current active commit ID"
    )


class GitPanelMixin:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'


class GitPanel(GitPanelMixin, Panel):
    bl_idname = "GIT_PT_panel"
    bl_label = "Git"

    def draw(self, context):
        pass


class GitCommitsList(UIList):
    """List of Commits in project."""

    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):

        split = layout.split(factor=0.8)

        activeCommitId = context.window_manager.git.currentCommitId

        if activeCommitId:
            isActiveCommit = item.id == activeCommitId
        else:
            isActiveCommit = True if index == 0 else False

        col1 = split.column()
        col1.label(text=item.message,
                   icon=ACTIVE_COMMENT_ICON if isActiveCommit else COMMENT_ICON)

        # Get last mofied string
        commitTime = datetime.strptime(item.date, gitHelpers.GIT_TIME_FORMAT)
        lastModified = gitHelpers.getLastModifiedStr(commitTime)

        col2 = split.column()
        col2.label(text=lastModified)


class GitNewBranchPanel(GitPanelMixin, Panel):
    """Add New Branch"""

    bl_idname = "GIT_PT_new_branch_panel"
    bl_label = ""
    bl_options = {'INSTANCED'}

    def draw(self, context):
        layout = self.layout

        layout.label(text="New Branch", icon=BRANCH_ICON)

        layout.prop(context.window_manager.git, "newBranchName")
        name = context.window_manager.git.newBranchName

        row = layout.row()
        if not name:
            row.enabled = False

        branch = row.operator(sourceControl.GitNewBranch.bl_idname,
                              text="Create Branch")
        branch.name = name


class GitSubPanel1(GitPanelMixin, Panel):
    bl_idname = "GIT_PT_sub_panel_1"
    bl_parent_id = GitPanel.bl_idname
    bl_label = ""
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        layout = self.layout

        row = layout.row(align=True)
        row.prop(context.window_manager.git, "branches")

        col = row.column()
        col.scale_x = 0.8
        col.popover(GitNewBranchPanel.bl_idname, icon=NEW_BRANCH_ICON)

    def draw(self, context):
        filepath = bpy.path.abspath("//")
        filename = bpy.path.basename(bpy.data.filepath).split(".")[0]

        layout = self.layout
        git = context.window_manager.git

        # List of Commits
        row = layout.row()
        row.template_list(
            listtype_name="GitCommitsList",
            # "" takes the name of the class used to define the UIList
            list_id="",
            dataptr=git,
            propname="commitsList",
            active_dataptr=git,
            active_propname="commitsListIndex",
            item_dyntip_propname="message",
            sort_lock=True,
            rows=5,
            maxrows=10
        )

        if git.commitsList:
            try:
                repo = gitHelpers.getRepo(filepath)
            except GitError:
                return

            selectedCommit = repo.revparse_single(
                f'HEAD~{git.commitsListIndex}')

            isSelectedCommitCurrent = str(
                selectedCommit.id) == git.currentCommitId

            if git.currentCommitId:
                shouldRenderCommitButton = not isSelectedCommitCurrent
            else:
                if git.commitsListIndex == 0:
                    shouldRenderCommitButton = False
                else:
                    shouldRenderCommitButton = True

            if shouldRenderCommitButton:
                if bpy.data.is_dirty:
                    row = layout.row()
                    row.label(text="Unsaved will be lost.", icon='ERROR')

                if repo.status_file(f"{filename}.blend") != GIT_STATUS_CURRENT:
                    row = layout.row()
                    row.label(text="Uncommited will be lost.", icon='ERROR')

                row = layout.row()
                switch = row.operator(sourceControl.GitRevertToCommit.bl_idname,
                                      text="Switch to Commit", icon=SWITCH_ICON)
                switch.id = git.commitsList[git.commitsListIndex]["id"]

        # Add commits to list
        bpy.app.timers.register(addCommitsToList)


def addCommitsToList():
    """Add commits to list"""

    git_context = bpy.context.window_manager.git

    # Get list
    commitsList = git_context.commitsList

    # Clear list
    commitsList.clear()

    # Get commits
    filepath = bpy.path.abspath("//")
    try:
        repo = gitHelpers.getRepo(filepath)
    except GitError:
        return

    git_context.currentCommitId = repo.config["user.currentCommit"]

    commits = gitHelpers.getCommits(repo)
    for commit in commits:
        item = commitsList.add()
        item.id = commit["id"]
        item.name = commit["name"]
        item.email = commit["email"]
        item.date = commit["date"]
        item.message = commit["message"]


class GitSubPanel2(GitPanelMixin, Panel):
    bl_idname = "GIT_PT_sub_panel_2"
    bl_parent_id = GitPanel.bl_idname
    bl_label = ""
    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        layout = self.layout
        layout.alignment = 'CENTER'

        row = layout.row()

        col1 = row.column()
        col1.scale_x = 0.5
        col1.label(text="Message: ")

        col2 = row.column()
        col2.prop(context.window_manager.git, "commitMessage")

        row = layout.row()
        message = context.window_manager.git.commitMessage
        if not message:
            row.enabled = False

        commit = row.operator(sourceControl.GitCommit.bl_idname,
                              text="Commit Changes")
        commit.message = message

        # Another row, showing how much disk space is being used by all the versions


"""ORDER MATTERS"""
classes = (GitCommitsListItem, GitPanelData, GitPanel,
           GitCommitsList, GitNewBranchPanel, GitSubPanel1,
           GitSubPanel2)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.WindowManager.git = PointerProperty(type=GitPanelData)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
