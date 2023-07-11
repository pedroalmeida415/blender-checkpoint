"""
Copyright (C) 2023 Flowerboy Studio
businessflowerboystudio@gmail.com

Created by Flowerboy Studio

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
bl_info = {
    "name": "Checkpoint - Supercharged",
    "author": "Flowerboy Studio",
    "description": "Backup and version control for Blender",
    "blender": (2, 80, 0),
    "category": "Development",
    "version": (0, 2, 0),
    "location": "Properties > Active Tool and Workspace settings > Checkpoints Panel",
}

import importlib
import sys

from . import addon_updater_ops

# Local imports implemented to support Blender refreshes
"""ORDER MATTERS"""
modulesNames = (
    "config",
    "project_helpers",
    "project_ops",
    "project_ui",
    "app_preferences",
    "app_handlers",
)
for module in modulesNames:
    if module in sys.modules:
        importlib.reload(sys.modules[module])
    else:
        globals()[module] = importlib.import_module(f"{__name__}.{module}")


def register():
    # Addon updater code and configurations.
    # In case of a broken version, try to register the updater first so that
    # users can revert back to a working version.
    addon_updater_ops.register(bl_info)

    for moduleName in modulesNames:
        if hasattr(globals()[moduleName], "register"):
            globals()[moduleName].register()


def unregister():
    addon_updater_ops.unregister()

    for module in reversed(modulesNames):
        if hasattr(globals()[module], "unregister"):
            globals()[module].unregister()
