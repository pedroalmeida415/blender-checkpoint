import bpy
from bpy.types import Panel, PropertyGroup, UIList
from bpy.props import (CollectionProperty, IntProperty,
                       PointerProperty, StringProperty)


class IconsListItem(PropertyGroup):
    icon: StringProperty(description="Unique Name of icon")


class IconsPanelData(PropertyGroup):
    iconsList: CollectionProperty(type=IconsListItem)

    iconsListIndex: IntProperty(default=0)


class IconsPanelMixin:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'


class IconsPanel(IconsPanelMixin, Panel):
    bl_idname = "ICONS_PT_panel"
    bl_label = "Icons"

    def draw(self, context):
        pass


class IconsList(UIList):
    """List of Icons"""

    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):

        split = layout.split(factor=0.8)

        col1 = split.column()
        # different Icon for active commit
        col1.label(text=f" - {str(item.icon)}",
                   icon=item.icon)


class IconsSubPanel1(IconsPanelMixin, Panel):
    bl_idname = "ICONS_PT_sub_panel_1"
    bl_parent_id = IconsPanel.bl_idname
    bl_label = ""

    def draw_header(self, context):
        layout = self.layout

        row = layout.row(align=True)
        row.label(text="Icons")

    def draw(self, context):
        layout = self.layout
        icons = context.window_manager.icons

        if icons.iconsListIndex:
            print(icons.iconsList[icons.iconsListIndex].icon)

        # List of Commits
        row = layout.row()
        row.template_list(
            listtype_name="IconsList",
            # "" takes the name of the class used to define the UIList
            list_id="",
            dataptr=icons,
            propname="iconsList",
            active_dataptr=icons,
            active_propname="iconsListIndex",
            sort_lock=False,
            type="GRID",
            rows=20
        )

        # Add commits to list
        bpy.app.timers.register(addIconsToList)


def addIconsToList():
    """Add icons to list"""

    icons_context = bpy.context.window_manager.icons

    # Get list
    iconsList = icons_context.iconsList

    iconsList.clear()

    for icon in icons:
        item = iconsList.add()
        item.icon = icon


"""ORDER MATTERS"""
classes = (IconsListItem, IconsPanelData, IconsPanel,
           IconsList, IconsSubPanel1,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.WindowManager.icons = PointerProperty(type=IconsPanelData)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()

# https://blender.stackexchange.com/questions/224015/is-there-a-way-to-get-icon-value-for-the-uilist-using-icon-name-from-enum
icons = bpy.types.UILayout.bl_rna.functions["prop"].parameters["icon"].enum_items.keys(
)
