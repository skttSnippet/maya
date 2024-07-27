"""
import maya.cmds as cmds
parent = cmds.group(n="parent",em=True)
aimbase = cmds.polyCone(n="aimBase",ch=False)[0]
cmds.setAttr(f"{aimbase}.rz",-90)
cmds.setAttr(f"{aimbase}.tx",1)
cmds.makeIdentity(aimbase,apply=True,t=True,r=True,s=True)
cmds.xform(aimbase,rp=[0,0,0,],ws=True)
cmds.xform(aimbase,sp=[0,0,0,],ws=True)
aimtarget = cmds.polySphere(n="aimTarget",ch=False)[0]
cmds.setAttr(f"{aimtarget}.tz",10)
up = cmds.spaceLocator(n="up")[0]
cmds.setAttr(f"{up}.ty",10)

cmds.parent(aimbase, parent)

aimnode = cmds.createNode("ktAim")
cmds.connectAttr(f'aimBase.worldMatrix[0]', f'{aimnode}.baseMatrix', f=True)
cmds.connectAttr('up.worldMatrix[0]', f'{aimnode}.upMatrix', f=True)
cmds.connectAttr('aimTarget.worldMatrix[0]',f'{aimnode}.aimMatrix', f=True)
cmds.connectAttr(f'{aimnode}.outRotate', 'aimBase.rotate', f=True)
"""
import sys
import math
import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx

ID_BLOCKSTART= 0x100fff
NODE_NAME = 'ktAim'
NODE_ID = OpenMaya.MTypeId( ID_BLOCKSTART )

class ktAim(OpenMayaMPx.MPxNode):
    
    a_aim_mtx = OpenMaya.MObject()
    a_upvec_mtx = OpenMaya.MObject()
    a_base_mtx = OpenMaya.MObject()
    a_parent_mtx = OpenMaya.MObject()
    
    out_rx = OpenMaya.MObject()
    out_ry = OpenMaya.MObject()
    out_rz = OpenMaya.MObject()
    out_rotate = OpenMaya.MObject()

    def __init__(self):
        super().__init__()

    def compute(self, plug, data):
        if plug != self.out_rotate and plug.parent() != self.out_rotate:
            return OpenMaya.kUnknownParameter

        v_a_aim_mtx = data.inputValue(self.a_aim_mtx).asMatrix()
        v_a_upvec_mtx = data.inputValue(self.a_upvec_mtx).asMatrix()
        v_a_base_mtx = data.inputValue(self.a_base_mtx).asMatrix()
        v_a_parent_mtx = data.inputValue(self.a_parent_mtx).asMatrix()

        translate_mtx = v_a_base_mtx * v_a_parent_mtx
        aim_mtx_pos = OpenMaya.MVector(v_a_aim_mtx(3, 0),
                                       v_a_aim_mtx(3, 1),
                                       v_a_aim_mtx(3, 2))
        upvec_mtx_pos = OpenMaya.MVector(v_a_upvec_mtx(3, 0),
                                         v_a_upvec_mtx(3, 1),
                                         v_a_upvec_mtx(3, 2))
        base_mtx_pos = OpenMaya.MVector(translate_mtx(3, 0),
                                        translate_mtx(3, 1),
                                        translate_mtx(3, 2))

        aimvec = OpenMaya.MVector(aim_mtx_pos - base_mtx_pos)
        upvec = OpenMaya.MVector(upvec_mtx_pos - base_mtx_pos)
        crossprod = OpenMaya.MVector(aimvec ^ upvec)
        upvec = crossprod ^ aimvec
        upvec.normalize()
        aimvec.normalize()
        crossprod.normalize()

        rotate_mtx = OpenMaya.MMatrix()
        mtx_ls = [aimvec.x,    aimvec.y,    aimvec.z,    0,
                  upvec.x,     upvec.y,     upvec.z,     0,
                  crossprod.x, crossprod.y, crossprod.z, 0,
                  0, 0, 0, 1]  
        OpenMaya.MScriptUtil.createMatrixFromList(mtx_ls, rotate_mtx)
        euler = OpenMaya.MTransformationMatrix(rotate_mtx).eulerRotation()

        print( 'matrix:')
        print( '{},{},{},{},'.format(rotate_mtx(0, 0), rotate_mtx(0, 1), rotate_mtx(0, 2), rotate_mtx(0, 3)))
        print( '{},{},{},{},'.format(rotate_mtx(1, 0), rotate_mtx(1, 1), rotate_mtx(1, 2), rotate_mtx(1, 3)))
        print( '{},{},{},{},'.format(rotate_mtx(2, 0), rotate_mtx(2, 1), rotate_mtx(2, 2), rotate_mtx(2, 3)))
        print( '{},{},{},{} '.format(rotate_mtx(3, 0), rotate_mtx(3, 1), rotate_mtx(3, 2), rotate_mtx(3, 3)))
        print( 'euler-->')
        print( '{},{},{}'.format(euler[0], euler[1], euler[2]))

        h_out_rotate = data.outputValue(self.out_rotate)
        h_out_rotate.set3Double(euler[0], euler[1], euler[2])
        data.setClean(plug)
        
    @classmethod
    def creator(cls):
        return OpenMayaMPx.asMPxPtr(cls())
    
    @classmethod
    def initializer(cls):
        m_attr = OpenMaya.MFnMatrixAttribute()
        n_attr = OpenMaya.MFnNumericAttribute()
        u_attr = OpenMaya.MFnUnitAttribute()

        cls.a_aim_mtx = m_attr.create('aimMatrix', 'aimMatrix')
        cls.a_upvec_mtx = m_attr.create('upMatrix', 'upMatrix')
        cls.a_base_mtx = m_attr.create('baseMatrix', 'baseMatrix')
        cls.a_parent_mtx = m_attr.create('parentMatrix', 'parentMatrix')

        cls.out_rx = u_attr.create(
            "outRotateX", "outRotateX", OpenMaya.MFnUnitAttribute.kAngle
        )
        u_attr.setWritable(False)
        u_attr.setStorable(False)
        cls.out_ry = u_attr.create(
            "outRotateY", "outRotateY", OpenMaya.MFnUnitAttribute.kAngle
        )
        u_attr.setWritable(False)
        u_attr.setStorable(False)
        cls.out_rz = u_attr.create(
            "outRotateZ", "outRotateZ", OpenMaya.MFnUnitAttribute.kAngle
        )
        u_attr.setWritable(False)
        u_attr.setStorable(False)
        cls.out_rotate = n_attr.create("outRotate", "outRotate",
                                        cls.out_rx,
                                        cls.out_ry,
                                        cls.out_rz)
        n_attr.setWritable(False)
        n_attr.setStorable(False)

        cls.addAttribute(cls.a_aim_mtx)
        cls.addAttribute(cls.a_upvec_mtx)
        cls.addAttribute(cls.a_base_mtx)
        cls.addAttribute(cls.a_parent_mtx)
        cls.addAttribute(cls.out_rotate)
    

        cls.attributeAffects(cls.a_base_mtx, cls.out_rotate)
        cls.attributeAffects(cls.a_upvec_mtx, cls.out_rotate)
        cls.attributeAffects(cls.a_aim_mtx, cls.out_rotate)


def initializePlugin(mobject):
    plugin=OpenMayaMPx.MFnPlugin(mobject, "Aaron Tzeng", "1.0.0", "Any")
    try:
        plugin.registerNode(
            NODE_NAME,
            NODE_ID,
            ktAim.creator,
            ktAim.initializer,
            OpenMayaMPx.MPxNode.kDependNode
                           )
    except:
        sys.stderr.write( "Failed to register node: %s" % NODE_NAME)
        raise Exception

def uninitializePlugin(mobject):
    plugin=OpenMayaMPx.MFnPlugin(mobject)
    try:
        plugin.deregisterNode(NODE_ID)
    except:
        sys.stderr.write( "Failed to deregister node: %s" % NODE_NAME)
