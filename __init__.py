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
    "name": "Checkpoint - Full",
    "author": "Flowerboy Studio",
    "description": "Backup and version control for Blender",
    "blender": (2, 80, 0),
    "category": "Development",
    "version": (1, 1, 1),
    "location": "Properties > Active Tool and Workspace settings > Checkpoints Panel",
}

from . import addon_updater_ops
from . import addon


def register():
    # Addon updater code and configurations.
    # In case of a broken version, try to register the updater first so that
    # users can revert back to a working version.
    addon_updater_ops.register(bl_info)

    addon.register()


def unregister():
    addon.unregister()

    addon_updater_ops.unregister()
