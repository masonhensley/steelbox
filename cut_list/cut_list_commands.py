# SPDX-License-Identifier: LGPL-3.0-or-later

import os

import FreeCAD
import FreeCADGui

QT_TRANSLATE_NOOP = FreeCAD.Qt.QT_TRANSLATE_NOOP

from . import RESOURCE_PATH, cut_list_ui


class cutListCommand:
    toolbarName = "Cut List"
    commandName = "createCutList"

    def GetResources(self):
        return {
            "MenuText": QT_TRANSLATE_NOOP("SteelBox_CreateCutList", "createCutList"),
            "ToolTip": QT_TRANSLATE_NOOP(
                "SteelBox_CreateCutList", "Create a new Cut List from SteelBox Beams"
            ),
            "Pixmap": "SteelBox_CreateCutList",
        }

    def Activated(self):
        cut_list_ui.openCutListDialog()

    def IsActive(self):
        """If there is no active document we can't do anything."""
        return FreeCAD.ActiveDocument is not None


FreeCADGui.addCommand("SteelBox_CreateCutList", cutListCommand())
