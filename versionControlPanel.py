import sys
import importlib
from datetime import datetime

import bpy
from bpy.types import Panel, PropertyGroup, UIList
from bpy.props import (CollectionProperty, EnumProperty, IntProperty,
                       PointerProperty, StringProperty, BoolProperty)

from pygit2._pygit2 import GitError
from pygit2 import GIT_STATUS_INDEX_MODIFIED

# Local imports implemented to support Blender refreshes
modulesNames = ("gitHelpers", "sourceControl")
for module in modulesNames:
    if module in sys.modules:
        importlib.reload(sys.modules[module])
    else:
        parent = ".".join(__name__.split(".")[:-1])
        globals()[module] = importlib.import_module(f"{parent}.{module}")


BRANCH_ICON = 'WINDOW'
COMMENT_ICON = 'KEYFRAME'
ACTIVE_COMMENT_ICON = 'KEYTYPE_KEYFRAME_VEC'
SWITCH_ICON = 'DECORATE_OVERRIDE'
NEW_BRANCH_ICON = 'ADD'
EDIT_BRANCH_ICON = 'OUTLINER_DATA_GP_LAYER' if (
    3, 0, 0) > bpy.app.version else 'CURRENT_FILE'
CLEAR_ICON = 'X'
BACKUP_SIZE_ICONS = ('IMPORT', 'FILE_BLEND')


class GitCommitsListItem(PropertyGroup):
    id: StringProperty(description="Unique ID of backup")
    name: StringProperty(description="Name of user")
    email: StringProperty(description="Email of user")
    date: StringProperty(description="Date of backup")
    message: StringProperty(description="Backup message")

# def errorPopupDraw(self, context):
#     self.layout.label(text="You have done something you shouldn't do!")
# bpy.context.window_manager.popup_menu(errorPopupDraw, title="Error", icon='ERROR')


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
            branchList.append((branch, branch, f"Timeline: '{branch}'",
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

        # InvalidSpecError: cannot locate local branch '', GitError: checkout conflict

        # Checkout branch
        ref = repo.lookup_reference(branch.name)
        repo.checkout(ref)

        repo.config["user.currentCommit"] = str(repo.head.target)

        # Load the reverted file
        bpy.ops.wm.revert_mainfile()

    branches: EnumProperty(
        name="Timeline",
        description="Current Timeline",
        items=getBranches,
        default=-1,
        options={'ANIMATABLE'},
        update=setActiveBranch
    )

    newBranchName: StringProperty(
        name="Name",
        options={'TEXTEDIT_UPDATE'},
        description="New Timeline name. (will be slugified)"
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
        description="Current active backup ID"
    )

    backupSize: IntProperty(default=0)

    isRepoInitialized: BoolProperty(
        name="Version Control Status",
        default=False,
    )

    squash_commits: BoolProperty(
        name=" Keep history",
        default=True,
        description="Carry previous backups over to the new timeline"
    )


class GitPanelMixin:
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_category = 'Scene'


class StartVersionControl(bpy.types.Operator):
    '''Initialize version control on the current folder'''

    bl_idname = "git.start_version_control"
    bl_label = "Start Version Control"

    def execute(self, context):
        filepath = bpy.path.abspath("//")
        filename = bpy.path.basename(bpy.data.filepath)

        git = context.window_manager.git

        if git.isRepoInitialized:
            return {'CANCELLED'}

        # Setup repo if not initiated yet
        gitHelpers.initialRepoSetup(filepath, filename)

        git.isRepoInitialized = True

        self.report({"INFO"}, "Version control initialized!")
        return {'FINISHED'}


class GitPanel(GitPanelMixin, Panel):
    bl_idname = "GIT_PT_panel"
    bl_label = "Version Control"

    def draw(self, context):
        filepath = bpy.path.abspath("//")
        git = context.window_manager.git

        if git.isRepoInitialized:
            pass

        try:
            gitHelpers.getRepo(filepath)
            git.isRepoInitialized = True
            pass
        except GitError:
            layout = self.layout

            row = layout.row()
            row.operator(StartVersionControl.bl_idname,
                         text="Start Version Control", icon="WINDOW")
            if not bpy.data.is_saved:
                row.enabled = False
                row = layout.row()
                row.alignment = "CENTER"
                row.label(text="You must save your project first")


class GitCommitsList(UIList):
    """List of backups of the current project."""

    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):

        split = layout.split(factor=0.8)

        currentCommitId = context.window_manager.git.currentCommitId

        if currentCommitId:
            isActiveCommit = item.id == currentCommitId
        else:
            isActiveCommit = True if index == 0 else False

        isActiveCommit = item.id == currentCommitId if currentCommitId else index == 0

        col1 = split.column()
        col1.label(text=item.message,
                   icon=ACTIVE_COMMENT_ICON if isActiveCommit else COMMENT_ICON)

        # Get last mofied string
        commitTime = datetime.strptime(item.date, gitHelpers.GIT_TIME_FORMAT)
        lastModified = gitHelpers.getLastModifiedStr(commitTime)

        col2 = split.column()
        col2.label(text=lastModified)


class GitNewBranchPanel(GitPanelMixin, Panel):
    """Add new timeline"""

    bl_idname = "GIT_PT_new_branch_panel"
    bl_label = ""
    bl_options = {'INSTANCED'}

    def draw(self, context):
        git = context.window_manager.git

        layout = self.layout
        layout.ui_units_x = 11

        layout.label(text="New Timeline from selected backup",
                     icon=BRANCH_ICON)

        layout.prop(git, "newBranchName")
        name = git.newBranchName

        row = layout.row()
        row.prop(git, "squash_commits")
        squash_commits = git.squash_commits

        row = layout.row()
        if not name:
            row.enabled = False

        branch = row.operator(sourceControl.GitNewBranch.bl_idname,
                              text="Create Timeline")
        branch.name = name
        branch.squash_commits = squash_commits


class GitDeleteBranchPanel(GitPanelMixin, Panel):
    """Deletes current Timeline"""

    bl_idname = "GIT_PT_delete_branch_panel"
    bl_label = ""
    bl_options = {'INSTANCED'}

    def draw(self, context):
        filepath = bpy.path.abspath("//")
        # Get repo
        try:
            repo = gitHelpers.getRepo(filepath)
        except GitError:
            return {'CANCELLED'}

        is_master_branch = repo.head.shorthand == "master"

        layout = self.layout

        if is_master_branch:
            layout.ui_units_x = 11.5
            row = layout.row()
            row.label(
                text='You cannot delete the master Timeline', icon="FAKE_USER_ON")
        else:
            layout.ui_units_x = 16.5
            layout.separator()

            row = layout.row()
            row.alignment = 'CENTER'
            row.label(text="ARE YOU SURE?")

            layout.separator()

            row = layout.row()
            row.label(
                text='This will delete the current timeline. There is no going back.', icon="TRASH")

            row = layout.row()
            row.operator(sourceControl.GitDeleteBranch.bl_idname,
                         text="Delete Timeline")


class GitEditBranchPanel(GitPanelMixin, Panel):
    """Edit Timeline name"""

    bl_idname = "GIT_PT_edit_branch_panel"
    bl_label = ""
    bl_options = {'INSTANCED'}

    def draw(self, context):
        filepath = bpy.path.abspath("//")
        # Get repo
        try:
            repo = gitHelpers.getRepo(filepath)
        except GitError:
            return {'CANCELLED'}

        is_master_branch = repo.head.shorthand == "master"

        layout = self.layout

        if is_master_branch:
            layout.ui_units_x = 11
            row = layout.row()
            row.label(
                text='You cannot rename master Timeline', icon="FAKE_USER_ON")
        else:
            git = context.window_manager.git

            layout.label(text="Edit Timeline name", icon=BRANCH_ICON)

            layout.prop(git, "newBranchName")
            name = git.newBranchName

            row = layout.row()
            if not name:
                row.enabled = False

            branch = row.operator(sourceControl.GitEditBranch.bl_idname,
                                  text="Rename")
            branch.name = name


class SwitchBranchErrorTooltip(GitPanelMixin, Panel):
    """You must save a backup of your changes before switching timelines."""

    bl_idname = "GIT_PT_switch_branch_error_panel"
    bl_label = ""
    bl_options = {'INSTANCED'}

    def draw(self, context):
        layout = self.layout
        layout.ui_units_x = 17.5

        row = layout.row()
        row.label(text=self.bl_description)


class GitSubPanel1(GitPanelMixin, Panel):
    bl_idname = "GIT_PT_sub_panel_1"
    bl_parent_id = GitPanel.bl_idname
    bl_label = ""
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.window_manager.git.isRepoInitialized

    def draw_header(self, context):
        filepath = bpy.path.abspath("//")
        filename = bpy.path.basename(bpy.data.filepath).split(".")[0]

        try:
            repo = gitHelpers.getRepo(filepath)
        except GitError:
            return

        layout = self.layout

        row = layout.row()
        row.prop(context.window_manager.git, "branches")

        row_button = layout.row(align=True)
        row_button.scale_x = 0.8

        isFileModified = str(
            GIT_STATUS_INDEX_MODIFIED) in str(repo.status_file(f"{filename}.blend"))

        if isFileModified:
            row.enabled = False
            row_button.popover(
                SwitchBranchErrorTooltip.bl_idname, icon="ERROR")
        else:
            row_button.popover(GitNewBranchPanel.bl_idname,
                               icon=NEW_BRANCH_ICON)
            row_button.popover(GitDeleteBranchPanel.bl_idname,
                               icon="REMOVE")
            row_button.popover(GitEditBranchPanel.bl_idname,
                               icon=EDIT_BRANCH_ICON)

    def draw(self, context):
        filepath = bpy.path.abspath("//")
        filename = bpy.path.basename(bpy.data.filepath).split(".")[0]

        git_context = context.window_manager.git

        layout = self.layout

        # List of Commits
        row = layout.row()
        row.template_list(
            listtype_name="GitCommitsList",
            # "" takes the name of the class used to define the UIList
            list_id="",
            dataptr=git_context,
            propname="commitsList",
            active_dataptr=git_context,
            active_propname="commitsListIndex",
            item_dyntip_propname="message",
            sort_lock=True,
            rows=5,
            maxrows=10
        )

        if git_context.commitsList:
            try:
                repo = gitHelpers.getRepo(filepath)
            except GitError:
                return

            selectedCommit = repo.revparse_single(
                f'HEAD~{git_context.commitsListIndex}')

            isSelectedCommitInitial = selectedCommit.hex == git_context.commitsList[-1]["id"]

            isSelectedCommitCurrent = selectedCommit.hex == git_context.currentCommitId

            isActionButtonsEnabled = not isSelectedCommitCurrent if git_context.currentCommitId else git_context.commitsListIndex != 0

            isBlenderDirty = bpy.data.is_dirty

            isFileModified = str(
                GIT_STATUS_INDEX_MODIFIED) in str(repo.status_file(f"{filename}.blend"))

            shouldShowError = (
                isActionButtonsEnabled and isFileModified) or isBlenderDirty
            if shouldShowError:
                row = layout.row()
                row.label(
                    text="Changes without backup will be lost.", icon='ERROR')

            row = layout.row()

            swtichCol = row.column()
            swtichCol.enabled = isActionButtonsEnabled
            switchOps = swtichCol.operator(sourceControl.GitRevertToCommit.bl_idname,
                                           text="Restore", icon="EXPORT")
            switchOps.id = selectedCommit.hex

            removeCol = row.column()
            removeCol.enabled = isActionButtonsEnabled and not isSelectedCommitInitial
            delOps = removeCol.operator(sourceControl.GitRemoveCommit.bl_idname,
                                        text="Remove", icon="CANCEL")
            delOps.id = selectedCommit.hex

            '''
            EDIT AND UNDO PREVIOUS COMMIT WIP
            '''
            # row = layout.row()

            # swtichCol = row.column()
            # swtichCol.enabled = isActionButtonsEnabled
            # switchOps = swtichCol.operator(sourceControl.GitRevertToCommit.bl_idname,
            #                                text="Undo last", icon="LOOP_BACK")
            # switchOps.id = selectedCommit.hex

            # removeCol = row.column()
            # removeCol.enabled = isActionButtonsEnabled and not isSelectedCommitInitial
            # delOps = removeCol.operator(sourceControl.GitRemoveCommit.bl_idname,
            #                             text="Edit", icon="CURRENT_FILE")
            # delOps.id = selectedCommit.hex

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
    git_context.backupSize = int(repo.config["user.backupSize"])

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

    @classmethod
    def poll(cls, context):
        return context.window_manager.git.isRepoInitialized

    def draw(self, context):
        layout = self.layout
        layout.alignment = 'CENTER'

        row = layout.row(align=True)

        col1 = row.column()
        col1.alignment = 'LEFT'
        col1.label(text="Description: ")

        col2 = row.column()
        col2.alignment = 'EXPAND'
        col2.prop(context.window_manager.git, "commitMessage")

        row = layout.row()
        row.scale_y = 2
        commitCol = row.column()

        message = context.window_manager.git.commitMessage
        if not message:
            commitCol.enabled = False

        commit = commitCol.operator(sourceControl.GitCommit.bl_idname)
        commit.message = message

        layout.separator()

        backupSize = context.window_manager.git.backupSize

        row = layout.row()
        col1 = row.column()
        subRow = col1.row(align=True)
        subRow.label(text="", icon=BACKUP_SIZE_ICONS[0])
        subRow.label(text="", icon=BACKUP_SIZE_ICONS[1])

        col2 = row.column()
        col2.alignment = 'RIGHT'
        col2.label(
            text=f"Backups total size: {format_size(backupSize)}")


def format_size(size):
    # Convert bytes to megabytes
    size = size / (1024 * 1024)
    if size < 999:
        return f"{size:.2f} MB"
    else:
        # Convert megabytes to gigabytes
        size = size / 1024
        return f"{size:.2f} GB"


"""ORDER MATTERS"""
classes = (GitCommitsListItem, GitPanelData, StartVersionControl, GitPanel,
           GitCommitsList, GitNewBranchPanel, GitDeleteBranchPanel, GitEditBranchPanel, SwitchBranchErrorTooltip, GitSubPanel1,
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
