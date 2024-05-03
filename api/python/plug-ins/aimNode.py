import sys
import math
import maya.api.OpenMaya as OpenMaya
import maya.api.OpenMaya as OpenMayaMPx
"""
import maya.cmds as cmds
nodePath="C:/Users/GG/Desktop/aimNode.py"
if cmds.pluginInfo('aimNode.py',q=True,registered=True):
    cmds.file(new=True, f=True)
    cmds.unloadPlugin('aimNode.py')  
cmds.loadPlugin(nodePath)
cmds.file("C:/Users/GG/Desktop/aim.ma", o=True, f=True)

'''
cmds.createNode("AimNode")
cmds.connectAttr('aimBase.worldMatrix[0]', 'AimNode1.inMatrix', f=True)
cmds.connectAttr('up.worldMatrix[0]', 'AimNode1.upVector', f=True)
cmds.connectAttr('aimTarget.worldMatrix[0]', 'AimNode1.driverMatrix', f=True)
cmds.connectAttr('AimNode1.outRotate', 'aimBase.rotate', f=True)
'''
"""
nodeName = 'AimNode'
nodeId = OpenMaya.MTypeId(0x100fff)
maya_useNewAPI = True


def maya_useNewAPI():
    """The presence of this function tells Maya that the plugin produces, and
       expects to be passed, objects created using the Maya Python API 2.0.   """
    pass


class AimNode(OpenMayaMPx.MPxNode):
    """"""
    # create attribte handle
    inMatrix = OpenMaya.MObject()
    inParentMatrix = OpenMaya.MObject()
    driverMatrix = OpenMaya.MObject()
    upVector = OpenMaya.MObject()

    outRotateX = OpenMaya.MObject()
    outRotateY = OpenMaya.MObject()
    outRotateZ = OpenMaya.MObject()
    outRotate = OpenMaya.MObject()

    def __init__(self):
        OpenMayaMPx.MPxNode.__init__(self)

    def compute(self, plug, dataBlock):
        """"""
        if (plug == AimNode.outRotate or plug == AimNode.outRotateX or plug == AimNode.outRotateY or plug == AimNode.outRotateZ):

            # GET INPUT VALUES
            driverMatrixDataHandle = dataBlock.inputValue(AimNode.driverMatrix)
            upVectorMatrixDataHandle = dataBlock.inputValue(
                AimNode.upVectorMatrix)
            inMatrixDataHandle = dataBlock.inputValue(AimNode.inMatrix)
            inParentMatrixDataHandle = dataBlock.inputValue(
                AimNode.inParentMatrix)
            driverMatrixV = driverMatrixDataHandle.asMatrix()
            upVectorMatrixV = upVectorMatrixDataHandle.asMatrix()
            inMatrixV = inMatrixDataHandle.asMatrix()
            inParentMatrixV = inParentMatrixDataHandle.asMatrix()

            # DO CALCULATION
            translateMatrix = inMatrixV * inParentMatrixV
            driverMatrixPos = OpenMaya.MVector(driverMatrixV.getElement(
                3, 0),  driverMatrixV.getElement(3, 1),  driverMatrixV.getElement(3, 2))
            upVectorMatrixPos = OpenMaya.MVector(upVectorMatrixV.getElement(
                3, 0), upVectorMatrixV.getElement(3, 1), upVectorMatrixV.getElement(3, 2))
            inMatrixPos = OpenMaya.MVector(translateMatrix.getElement(
                3, 0), translateMatrix.getElement(3, 1), translateMatrix.getElement(3, 2))
            # compute needed vectors
            aimVec = OpenMaya.MVector(driverMatrixPos - inMatrixPos)
            aimVec.normalize()
            upVec = OpenMaya.MVector(upVectorMatrixPos - inMatrixPos)
            upDot = aimVec * upVec
            upVec = upVec - aimVec * upDot
            upVec.normalize()
            cross = OpenMaya.MVector(aimVec ^ upVec)
            cross.normalize()
            # build a rotation matrix. At the end only need rotation so set translate all 0
            matrixList = [aimVec.x, aimVec.y, aimVec.z, 0,
                          upVec.x, upVec.y, upVec.z, 0,
                          cross.x, cross.y, cross.z, 0,
                          0, 0, 0, 1]
            rotMatrix = OpenMaya.MMatrix(matrixList)
            # extract euler
            euler = OpenMaya.MTransformationMatrix(
                rotMatrix).rotation(asQuaternion=False)  # as euler

            # SET OUTPUT VALUES
            dataHandleRotate = dataBlock.outputValue(AimNode.outRotate)
            dataHandleRotate.set3Double(euler[0], euler[1], euler[2])
            dataBlock.setClean(plug)
        else:
            return OpenMaya.kUnknownParameter


def nodeCreator():
    # return OpenMayaMPx.asMPxPtr( AimNode() ) #Python 1.0
    return AimNode()  # Python 2.0


def nodeInitializer():
    mFnNumAttr = OpenMaya.MFnNumericAttribute()
    mFnTypedAttr = OpenMaya.MFnTypedAttribute()
    mFnCompoundAttr = OpenMaya.MFnCompoundAttribute()
    mFnMatrixAtrr = OpenMaya.MFnMatrixAttribute()
    mFnUnitAttr = OpenMaya.MFnUnitAttribute()

    AimNode.driverMatrix = mFnMatrixAtrr.create('driverMatrix', 'drm')
    AimNode.upVectorMatrix = mFnMatrixAtrr.create('upVector', 'upvm')
    AimNode.inMatrix = mFnMatrixAtrr.create('inMatrix', 'im')
    AimNode.inParentMatrix = mFnMatrixAtrr.create('inParentMatrix', 'ipm')

    AimNode.addAttribute(AimNode.driverMatrix)
    AimNode.addAttribute(AimNode.upVectorMatrix)
    AimNode.addAttribute(AimNode.inMatrix)
    AimNode.addAttribute(AimNode.inParentMatrix)

    AimNode.outRotateX = mFnUnitAttr.create(
        'outRotateX', 'orx', OpenMaya.MFnUnitAttribute.kAngle, 0.0)
    mFnUnitAttr.readable = True
    mFnUnitAttr.writable = False
    mFnUnitAttr.storable = False
    mFnUnitAttr.keyable = False
    AimNode.addAttribute(AimNode.outRotateX)
    AimNode.outRotateY = mFnUnitAttr.create(
        'outRotateY', 'ory', OpenMaya.MFnUnitAttribute.kAngle, 0.0)
    mFnUnitAttr.readable = True
    mFnUnitAttr.writable = False
    mFnUnitAttr.storable = False
    mFnUnitAttr.keyable = False
    AimNode.addAttribute(AimNode.outRotateY)
    AimNode.outRotateZ = mFnUnitAttr.create(
        'outRotateZ', 'orz', OpenMaya.MFnUnitAttribute.kAngle, 0.0)
    mFnUnitAttr.readable = True
    mFnUnitAttr.writable = False
    mFnUnitAttr.storable = False
    mFnUnitAttr.keyable = False
    AimNode.addAttribute(AimNode.outRotateZ)
    AimNode.outRotate = mFnCompoundAttr.create('outRotate', 'or')
    mFnCompoundAttr.addChild(AimNode.outRotateX)
    mFnCompoundAttr.addChild(AimNode.outRotateY)
    mFnCompoundAttr.addChild(AimNode.outRotateZ)
    mFnCompoundAttr.readable = True
    mFnCompoundAttr.writable = False
    mFnCompoundAttr.storable = False
    mFnCompoundAttr.keyable = False
    AimNode.addAttribute(AimNode.outRotate)

    AimNode.attributeAffects(AimNode.inMatrix, AimNode.outRotate)
    AimNode.attributeAffects(AimNode.upVectorMatrix, AimNode.outRotate)
    AimNode.attributeAffects(AimNode.driverMatrix, AimNode.outRotate)


def initializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.registerNode(nodeName, nodeId, nodeCreator, nodeInitializer)
    except:
        sys.stderr.write("Failed to register node:" + nodeName)


def uninitializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.deregisterNode(nodeId)
    except:
        sys.stderr.write("Failed to unregister node:" + nodeName)
