# SPDX-License-Identifier: LGPL-3.0-or-later

__title__ = "pypeTools toolbar"
__author__ = "oddtopus"
__url__ = "github.com/oddtopus/dodo"
__license__ = "LGPL 3"

# import FreeCAD modules
import FreeCAD
import FreeCADGui
import SteelBox_tooltips

from steelbox_config import addCommand

QT_TRANSLATE_NOOP = FreeCAD.Qt.QT_TRANSLATE_NOOP
# translate = FreeCAD.Qt.translate

def updatesPL(dialogqm):
    if FreeCAD.activeDocument():
        pypelines = [
            o.Label
            for o in FreeCAD.activeDocument().Objects
            if hasattr(o, "PType") and o.PType == "PypeLine"
        ]
    else:
        pypelines = []
    if pypelines:  # updates pypelines in combo
        dialogqm.QM.comboPL.clear()
        dialogqm.QM.comboPL.addItems(pypelines)


# ---------------------------------------------------------------------------
# The command classes
# ---------------------------------------------------------------------------


class insertPipe:
    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def Activated(self):
        import pForms

        pipForm = pForms.insertPipeForm()

    def GetResources(self):
        return {
            "Pixmap": "SteelBox_InsertPipe",
            "MenuText": QT_TRANSLATE_NOOP("SteelBox_InsertPipe", "Insert a tube"),
            "ToolTip": QT_TRANSLATE_NOOP("SteelBox_InsertPipe",  SteelBox_tooltips.insert_tube_tooltip),
        }


class insertElbow:
    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def Activated(self):
        import pForms

        elbForm = pForms.insertElbowForm()

    def GetResources(self):
        return {
            "Pixmap": "SteelBox_InsertElbow",
            "MenuText": QT_TRANSLATE_NOOP("SteelBox_InsertElbow", "Insert a elbow"),
            "ToolTip": QT_TRANSLATE_NOOP("SteelBox_InsertElbow", SteelBox_tooltips.elbow_tooltip),
        }


class insertTerminalAdapter:
    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def Activated(self):
        # import pCmd
        # pCmd.makeTerminalAdapter()
        import pForms
        TerminalA=pForms.insertTerminalAdapterForm()
        TerminalA.show()
        # FreeCAD.activeDocument().recompute()

    def GetResources(self):
        return {
            "Pixmap": "SteelBox_TerminalAdapter",
            "MenuText": QT_TRANSLATE_NOOP("SteelBox_InsertTerminalAdapter", "Insert Terminal adapter"),
            "ToolTip": QT_TRANSLATE_NOOP("SteelBox_InsertTerminalAdapter", "Insert Terminal adapter"),
        }


class insertReduct:
    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def Activated(self):
        import pForms

        pipeFormObj = pForms.insertReductForm()

    def GetResources(self):
        return {
            "Pixmap": "SteelBox_InsertReduct",
            "MenuText": QT_TRANSLATE_NOOP("SteelBox_InsertReduct", "Insert a reduction"),
            "ToolTip": QT_TRANSLATE_NOOP("SteelBox_InsertReduct", "Insert a reduction"),
        }


class insertCap:
    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def Activated(self):
        import pForms

        pipeFormObj = pForms.insertCapForm()

    def GetResources(self):
        return {
            "Pixmap": "SteelBox_InsertCap",
            "MenuText": QT_TRANSLATE_NOOP("SteelBox_InsertCap", "Insert a cap"),
            "ToolTip": QT_TRANSLATE_NOOP("SteelBox_InsertCap", "Insert a cap"),
        }


class insertFlange:
    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def Activated(self):
        import pForms

        pipeFormObj = pForms.insertFlangeForm()

    def GetResources(self):
        return {
            "Pixmap": "SteelBox_InsertFlange",
            "MenuText": QT_TRANSLATE_NOOP("SteelBox_InsertFlange", "Insert a flange"),
            "ToolTip": QT_TRANSLATE_NOOP("SteelBox_InsertFlange", "Insert a flange"),
        }


class insertUbolt:
    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def Activated(self):
        import pForms

        pipeFormObj = pForms.insertUboltForm()

    def GetResources(self):
        return {
            "Pixmap": "SteelBox_InsertUBolt",
            "MenuText": QT_TRANSLATE_NOOP("SteelBox_InsertUbolt", "Insert a U-bolt"),
            "ToolTip": QT_TRANSLATE_NOOP("SteelBox_InsertUbolt", "Insert a U-bolt"),
        }


class insertPypeLine:
    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def Activated(self):
        import pForms

        pipeFormObj = pForms.insertPypeLineForm()

    def GetResources(self):
        return {
            "Pixmap": "SteelBox_InsertPypeLine",
            "MenuText": QT_TRANSLATE_NOOP("SteelBox_InsertPypeLine", "PypeLine Manager"),
            "ToolTip": QT_TRANSLATE_NOOP("SteelBox_InsertPypeLine", "Open PypeLine Manager"),
        }


class insertBranch:
    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def Activated(self):
        import pForms

        # pCmd.makeBranch()
        pipeFormObj = pForms.insertBranchForm()

    def GetResources(self):
        return {
            "Pixmap": "SteelBox_InsertBranch",
            "MenuText": QT_TRANSLATE_NOOP("SteelBox_InsertBranch", "Insert a branch"),
            "ToolTip": QT_TRANSLATE_NOOP("SteelBox_InsertBranch", "Insert a PypeBranch"),
        }


class breakPipe:
    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def Activated(self):
        import pForms

        pipeFormObj = pForms.breakForm()

    def GetResources(self):
        return {
            "Pixmap": "SteelBox_BreakPipe",
            "MenuText": QT_TRANSLATE_NOOP("SteelBox_BreakPipe", "Break the pipe"),
            "ToolTip": QT_TRANSLATE_NOOP(
                "SteelBox_BreakPipe", "Break one pipe at point and insert gap"
            ),
        }


class mateEdges:

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def Activated(self):
        import pCmd
        result=pCmd.translate("Transaction", "Mate")
        FreeCAD.activeDocument().openTransaction(result)
        pCmd.alignTheTube()
        FreeCAD.activeDocument().commitTransaction()
        FreeCAD.activeDocument().recompute()

    def GetResources(self):
        return {
            "Accel": "M,E",
            "Pixmap": "SteelBox_MateEdges",
            "MenuText": QT_TRANSLATE_NOOP("SteelBox_MateEdges", "Mate pipes edges"),
            "ToolTip": QT_TRANSLATE_NOOP(
                "SteelBox_MateEdges", "Mate two terminations through their edges"
            ),
        }


class flat:

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def Activated(self):
        import pCmd

        pCmd.flatten()

    def GetResources(self):
        return {
            "Pixmap": "SteelBox_Flat",
            "MenuText": QT_TRANSLATE_NOOP("SteelBox_Flat", "Fit one elbow"),
            "ToolTip": QT_TRANSLATE_NOOP(
                "SteelBox_Flat", "Place a existing elbow between two pipes adjusting lenght pipes"
            ),
        }


class extend2intersection:

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def Activated(self):
        import pCmd
        result=pCmd.translate("Transaction", "Extend pipes to intersection")
        FreeCAD.activeDocument().openTransaction(result)
        pCmd.extendTheTubes2intersection()
        FreeCAD.activeDocument().recompute()
        FreeCAD.activeDocument().commitTransaction()

    def GetResources(self):
        return {
            "Pixmap": "SteelBox_ExtendIntersection2",
            "MenuText": QT_TRANSLATE_NOOP(
                "SteelBox_ExtendIntersection2", "Extend pipes to intersection"
            ),
            "ToolTip": QT_TRANSLATE_NOOP(
                "SteelBox_ExtendIntersection2", "Extends pipes to intersection"
            ),
        }


class extend1intersection:

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def Activated(self):
        import pCmd
        result=pCmd.translate("Transaction", "Extend pipe to intersection")
        FreeCAD.activeDocument().openTransaction(result)
        pCmd.extendTheTubes2intersection(both=False)
        FreeCAD.activeDocument().recompute()
        FreeCAD.activeDocument().commitTransaction()

    def GetResources(self):
        return {
            "Pixmap": "SteelBox_ExtendIntersection1",
            "MenuText": QT_TRANSLATE_NOOP(
                "SteelBox_ExtendIntersection1", "Extend pipe to intersection"
            ),
            "ToolTip": QT_TRANSLATE_NOOP(
                "SteelBox_ExtendIntersection1", "Extends pipe to intersection"
            ),
        }


class laydown:

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def Activated(self):
        import pCmd
        import fCmd
        from Part import Plane

        refFace = [f for f in fCmd.faces() if isinstance(f.Surface, Plane)][0]
        result=pCmd.translate("Transaction", "Lay-down the pipe")
        FreeCAD.activeDocument().openTransaction(result)
        for b in fCmd.beams():
            if pCmd.isPipe(b):
                pCmd.laydownTheTube(b, refFace)
        FreeCAD.activeDocument().recompute()
        FreeCAD.activeDocument().commitTransaction()

    def GetResources(self):
        return {
            "Pixmap": "SteelBox_Laydown",
            "MenuText": QT_TRANSLATE_NOOP("SteelBox_Laydown", "Lay-down the pipe"),
            "ToolTip": QT_TRANSLATE_NOOP(
                "SteelBox_Laydown", "Lay-down the pipe on the support plane"
            ),
        }


class raiseup:

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True
    
    def Activated(self):
        import pCmd
        import fCmd
        from Part import Plane

        selex = FreeCADGui.Selection.getSelectionEx()
        for sx in selex:
            sxFaces = [f for f in fCmd.faces([sx]) if isinstance(f.Surface, Plane)]
            if len(sxFaces) > 0:
                refFace = sxFaces[0]
                support = sx.Object
        result=pCmd.translate("Transaction", "Raise-up the support")
        FreeCAD.activeDocument().openTransaction(result)
        for b in fCmd.beams():
            if pCmd.isPipe(b):
                pCmd.laydownTheTube(b, refFace, support)
                break
        FreeCAD.activeDocument().recompute()
        FreeCAD.activeDocument().commitTransaction()

    def GetResources(self):
        return {
            "Pixmap": "SteelBox_Raiseup",
            "MenuText": QT_TRANSLATE_NOOP("SteelBox_Raiseup", "Raise-up the support"),
            "ToolTip": QT_TRANSLATE_NOOP("SteelBox_Raiseup", "Raise the support to the pipe"),
        }


class joinPype:
    """ """

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def Activated(self):
        import FreeCADGui
        import pForms  # pObservers

        # s=pObservers.joinObserver()
        FreeCADGui.Control.showDialog(pForms.joinForm())  # .Selection.addObserver(s)

    def GetResources(self):
        return {
            "Pixmap": "SteelBox_JoinPype",
            "MenuText": QT_TRANSLATE_NOOP("SteelBox_JoinPype", "Join pipes"),
            "ToolTip": QT_TRANSLATE_NOOP("SteelBox_JoinPype", "Select the part-pype and the port"),
        }


class insertValve:
    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def Activated(self):
        import pForms

        # pipeFormObj=pForms.insertValveForm()
        # FreeCADGui.Control.showDialog(pForms.insertValveForm())
        pipeFormObj = pForms.insertValveForm()

    def GetResources(self):
        return {
            "Pixmap": "SteelBox_InsertValve",
            "MenuText": QT_TRANSLATE_NOOP("SteelBox_InsertValve", "Insert a valve"),
            "ToolTip": QT_TRANSLATE_NOOP("SteelBox_InsertValve", "Insert a valve"),
        }


class attach2tube:

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def Activated(self):
        import pCmd
        result=pCmd.translate("Transaction", "Attach to tube")
        FreeCAD.activeDocument().openTransaction(result)
        pCmd.attachToTube()
        FreeCAD.activeDocument().recompute()
        FreeCAD.activeDocument().commitTransaction()

    def GetResources(self):
        return {
            "Pixmap": "SteelBox_Attach2Tube",
            "MenuText": QT_TRANSLATE_NOOP("SteelBox_Attach2Tube", "Attach to tube"),
            "ToolTip": QT_TRANSLATE_NOOP(
                "SteelBox_Attach2Tube", "Attach one pype to the nearest port of selected pipe"
            ),
        }


class point2point:

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True


    def Activated(self):
        import pForms

        form = pForms.point2pointPipe()

    def GetResources(self):
        return {
            "Pixmap": "SteelBox_Point2Point",
            "MenuText": QT_TRANSLATE_NOOP("SteelBox_Point2Point", "Draw a tube point by point"),
            "ToolTip": QT_TRANSLATE_NOOP(
                "SteelBox_Point2Point", "A new body is created on each click on subsequent points"
            ),
        }


class insertAnyz:
    """
    Dialog to insert any object saved as .STEP, .IGES or .BREP in folder ../Mod/dodo/shapez or subfolders.
    """

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True


    def Activated(self):
        import anyShapez

        FreeCADGui.Control.showDialog(anyShapez.shapezDialog())

    def GetResources(self):
        return {
            "Pixmap": "SteelBox_InsertAnyShape",
            "MenuText": QT_TRANSLATE_NOOP("SteelBox_InsertAnyShape", "Insert any shape"),
            "ToolTip": QT_TRANSLATE_NOOP("SteelBox_InsertAnyShape", "Insert a STEP, IGES or BREP"),
        }


class insertTank:

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def Activated(self):
        import FreeCADGui
        import pForms

        FreeCADGui.Control.showDialog(pForms.insertTankForm())

    def GetResources(self):
        return {
            "Pixmap": "SteelBox_InsertTank",
            "MenuText": QT_TRANSLATE_NOOP("SteelBox_InsertTank", "Insert a tank"),
            "ToolTip": QT_TRANSLATE_NOOP("SteelBox_InsertTank", "Create tank and nozzles"),
        }


class insertRoute:

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def Activated(self):
        import FreeCADGui
        import pForms

        FreeCADGui.Control.showDialog(pForms.insertRouteForm())

    def GetResources(self):
        return {
            "Pixmap": "SteelBox_InsertRoute",
            "MenuText": QT_TRANSLATE_NOOP("SteelBox_InsertRoute", "Insert a pipe route"),
            "ToolTip": QT_TRANSLATE_NOOP(
                "SteelBox_InsertRoute", "Create a sketch attached to a circular edge"
            ),
        }


class makeHeader:

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def Activated(self):
        import pCmd
        result=pCmd.translate("Transaction", "Connect to header")
        FreeCAD.activeDocument().openTransaction(result)
        FreeCAD.activeDocument().recompute()
        FreeCAD.activeDocument().commitTransaction()
        pCmd.header()

    def GetResources(self):
        return {
            "Pixmap": "SteelBox_MakeHeader",
            "MenuText": QT_TRANSLATE_NOOP("SteelBox_MakeHeader", "Connect to header"),
            "ToolTip": QT_TRANSLATE_NOOP(
                "SteelBox_MakeHeader",
                "Connect branches to one header pipe\nBranches and header's axes must be ortho",
            ),
        }


# ---------------------------------------------------------------------------
# Adds the commands to the FreeCAD command manager
# ---------------------------------------------------------------------------
addCommand("SteelBox_InsertPipe", insertPipe())
addCommand("SteelBox_InsertElbow", insertElbow())
addCommand("SteelBox_InsertReduct", insertReduct())
addCommand("SteelBox_InsertCap", insertCap())
addCommand("SteelBox_InsertValve", insertValve())
addCommand("SteelBox_InsertFlange", insertFlange())
addCommand("SteelBox_InsertUBolt", insertUbolt())
addCommand("SteelBox_InsertPypeLine", insertPypeLine())
addCommand("SteelBox_InsertBranch", insertBranch())
addCommand("SteelBox_InsertTank", insertTank())
addCommand("SteelBox_InsertRoute", insertRoute())
addCommand("SteelBox_BreakPipe", breakPipe())
addCommand("SteelBox_MateEdges", mateEdges())
addCommand("SteelBox_JoinPype", joinPype())
addCommand("SteelBox_Attach2Tube", attach2tube())
addCommand("SteelBox_Flat", flat())
addCommand("SteelBox_ExtendIntersection2", extend2intersection())
addCommand("SteelBox_ExtendIntersection1", extend1intersection())
addCommand("SteelBox_Laydown", laydown())
addCommand("SteelBox_Raiseup", raiseup())
addCommand("SteelBox_Point2Point", point2point())
addCommand("SteelBox_InsertAnyShape", insertAnyz())
addCommand("SteelBox_MakeHeader", makeHeader())
addCommand("SteelBox_InsertTerminalAdapter", insertTerminalAdapter())


### QkMenus ###
class pipeQM:

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def Activated(self):
        import dodoPM

        # dodoPM.pqm.updatePL()
        dodoPM.pqm.show()

    def GetResources(self):
        return {
            "Pixmap": "SteelBox_InsertPipe",
            "MenuText": QT_TRANSLATE_NOOP("SteelBox_PipeQM", "QM for pipes"),
        }


addCommand("SteelBox_PipeQM", pipeQM())


# Quick Menu section


class elbowQM:

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def Activated(self):
        import dodoPM

        dodoPM.eqm.show()

    def GetResources(self):
        return {
            "Pixmap": "SteelBox_InsertElbow",
            "MenuText": QT_TRANSLATE_NOOP("SteelBox_ElbowQM", "QM for elbows"),
        }


addCommand("SteelBox_ElbowQM", elbowQM())


class flangeQM:

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def Activated(self):
        import dodoPM

        dodoPM.fqm.show()

    def GetResources(self):
        return {
            "Pixmap": "SteelBox_InsertFlange",
            "MenuText": QT_TRANSLATE_NOOP("SteelBox_FlangeQM", "QM for flanges"),
        }


addCommand("SteelBox_FlangeQM", flangeQM())


class valveQM:

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def Activated(self):
        import dodoPM

        dodoPM.vqm.show()

    def GetResources(self):
        return {
            "Pixmap": "SteelBox_InsertValve",
            "MenuText": QT_TRANSLATE_NOOP("SteelBox_ValveQM", "QM for valves"),
        }


addCommand("SteelBox_ValveQM", valveQM())


class capQM:

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def Activated(self):
        import dodoPM

        dodoPM.cqm.show()

    def GetResources(self):
        return {
            "Pixmap": "SteelBox_InsertCap",
            "MenuText": QT_TRANSLATE_NOOP("SteelBox_CapQM", "QM for caps"),
        }


addCommand("SteelBox_CapQM", capQM())
