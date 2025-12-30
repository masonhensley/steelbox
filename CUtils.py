# SPDX-License-Identifier: LGPL-3.0-or-later

__license__ = "LGPL 3"

# import FreeCAD modules

import FreeCAD
import FreeCADGui

from steelbox_config import addCommand

QT_TRANSLATE_NOOP = FreeCAD.Qt.QT_TRANSLATE_NOOP


# ---------------------------------------------------------------------------
# The command classes
# ---------------------------------------------------------------------------


class queryModel:
    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def Activated(self):
        import uForms

        form = uForms.QueryForm(FreeCADGui.Selection)

    def GetResources(self):
        return {
            "Pixmap": "SteelBox_QueryModel",
            "Accel": "Q,M",
            "MenuText": QT_TRANSLATE_NOOP("SteelBox_QueryModel", "Query the model"),
            "ToolTip": QT_TRANSLATE_NOOP("SteelBox_QueryModel", "Click objects to print infos"),
        }


class moveWorkPlane:
    """
    Tool to set the DraftWorkingPlane according existing geometry of
    the model.
    The normal of plane is set:
    * 1st according the selected face,
    * then according the plane defined by a curved edge,
    * at last according the plane defined by two straight edges.
    The origin is set:
    * 1st according the selected vertex,
    * then according the center of curvature of a curved edge,
    * at last according the intersection of two straight edges.
    """
    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def Activated(self):
        import uCmd

        uCmd.setWP()

    def GetResources(self):
        return {
            "Pixmap": "SteelBox_MoveWorkPlane",
            "Accel": "A,W",
            "MenuText": QT_TRANSLATE_NOOP("SteelBox_MoveWorkPlane", "Align workplane"),
            "ToolTip": QT_TRANSLATE_NOOP(
                "SteelBox_MoveWorkPlane",
                "Moves and rotates the drafting workplane with points, edges and faces",
            ),
        }


class rotateWorkPlane:

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def Activated(self):
        import uForms

        form = uForms.rotWPForm()

    def GetResources(self):
        return {
            "Accel": "R,W",
            "Pixmap": "SteelBox_RotateWorkPlane",
            "MenuText": QT_TRANSLATE_NOOP("SteelBox_RotateWorkPlane", "Rotate workplane"),
            "ToolTip": QT_TRANSLATE_NOOP(
                "SteelBox_RotateWorkPlane", "Spin the Draft working plane about one of its axes"
            ),
        }


class offsetWorkPlane:

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def Activated(self):
        if hasattr(FreeCAD, "DraftWorkingPlane") and hasattr(FreeCADGui, "Snapper"):
            import uCmd

            s = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Draft").GetInt("gridSize")
            sc = [float(x * s) for x in [1, 1, 0.2]]
            arrow = uCmd.arrow(FreeCAD.DraftWorkingPlane.getPlacement(), scale=sc, offset=s)
            from PySide.QtGui import QInputDialog as qid

            translate = FreeCAD.Qt.translate

            offset = qid.getInt(
                None,
                translate("SteelBox_OffsetWorkPlane", "Offset Work Plane"),
                translate("SteelBox_OffsetWorkPlane", "Offset: "),
            )
            if offset[1] > 0:
                uCmd.offsetWP(offset[0])
            # FreeCADGui.ActiveDocument.ActiveView.getSceneGraph().removeChild(arrow.node)
            arrow.closeArrow()

    def GetResources(self):
        return {
            "Pixmap": "SteelBox_OffsetWorkPlane",
            "Accel": "O,W",
            "MenuText": QT_TRANSLATE_NOOP("SteelBox_OffsetWorkPlane", "Offset workplane"),
            "ToolTip": QT_TRANSLATE_NOOP(
                "SteelBox_OffsetWorkPlane", "Shifts the WP along its normal."
            ),
        }


class hackedL:

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def Activated(self):
        import uCmd

        form = uCmd.hackedLine()

    def GetResources(self):
        return {
            "Pixmap": "SteelBox_HackedLine",
            "Accel": "H,L",
            "MenuText": QT_TRANSLATE_NOOP("SteelBox_HackedLine", "Draw a Draft wire"),
            "ToolTip": QT_TRANSLATE_NOOP(
                "SteelBox_HackedLine",
                "WP is re-positioned at each point. Possible to spin and offset it.",
            ),
        }


class moveHandle:

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def Activated(self):
        import uCmd

        FreeCADGui.Control.showDialog(uCmd.handleDialog())
        # form = uCmd.handleDialog()

    def GetResources(self):
        return {
            "Pixmap": "SteelBox_MoveHandle",
            "Accel": "M,H",
            "MenuText": QT_TRANSLATE_NOOP("SteelBox_MoveHandle", "Move objects"),
            "ToolTip": QT_TRANSLATE_NOOP(
                "SteelBox_MoveHandle", "Move quickly objects inside viewport"
            ),
        }


class dpCalc:

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def Activated(self):
        import uForms

        FreeCADGui.Control.showDialog(uForms.dpCalcDialog())

    def GetResources(self):
        return {
            "Pixmap": "SteelBox_PressureLossCalculator",
            "MenuText": QT_TRANSLATE_NOOP(
                "SteelBox_PressureLossCalculator", "Pressure loss calculator"
            ),
            "ToolTip": QT_TRANSLATE_NOOP(
                "SteelBox_PressureLossCalculator",
                "Calculate pressure loss in 'pypes' using ChEDL libraries.\n"
                "See __doc__ of the module for further information.",
            ),
        }


class selectSolids:

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def Activated(self):
        from fCmd import getSolids

        if FreeCADGui.Selection.getSelection():
            allDoc = False
        else:
            allDoc = True
        getSolids(allDoc)

    def GetResources(self):
        return {
            "Pixmap": "SteelBox_SelectSolids",
            "MenuText": QT_TRANSLATE_NOOP("SteelBox_SelectSolids", "Select solids"),
            "ToolTip": QT_TRANSLATE_NOOP(
                "SteelBox_SelectSolids",
                "Grab all solids or those partially selected\n to export in .step format",
            ),
        }


# ---------------------------------------------------------------------------
# Adds the commands to the FreeCAD command manager
# ---------------------------------------------------------------------------
addCommand("SteelBox_QueryModel", queryModel())
addCommand("SteelBox_MoveWorkPlane", moveWorkPlane())
addCommand("SteelBox_RotateWorkPlane", rotateWorkPlane())
addCommand("SteelBox_OffsetWorkPlane", offsetWorkPlane())
addCommand("SteelBox_HackedLine", hackedL())
addCommand("SteelBox_MoveHandle", moveHandle())
addCommand("SteelBox_PressureLossCalculator", dpCalc())
addCommand("SteelBox_SelectSolids", selectSolids())
