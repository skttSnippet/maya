"""
import maya.cmds as cmds
import maya.mel as mel
sphere = cmds.polySphere(n="sphere",ch=False)[0]

sinenode = cmds.createNode("ktSine")
cmds.connectAttr(f'time1.outTime', f'{sinenode}.radians', f=True)
cmds.connectAttr(f'{sinenode}.outSine', f'{sphere}.ty', f=True)
cmds.setAttr(f"{sinenode}.frequency",0.050)

cmds.play( forward=True )

"""

import math
import sys

import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx

ID_BLOCKSTART= 0x81048
NODE_NAME = 'ktSine'
NODE_ID = OpenMaya.MTypeId( ID_BLOCKSTART )

class ktSine(OpenMayaMPx.MPxNode):
    

    a_radians = OpenMaya.MObject()
    
    a_amplitude = OpenMaya.MObject()
    a_frequency = OpenMaya.MObject()
    a_offset = OpenMaya.MObject()

    out_sine = OpenMaya.MObject()
    
    def __init__(self):
        super().__init__()
    
    def compute(self, plug, data):
        
        if plug != self.out_sine:
            return OpenMaya.kUnknownParameter
        
        v_a_rad = data.inputValue(self.a_radians).asFloat()
        v_a_amplitude = data.inputValue(self.a_amplitude).asFloat()
        v_a_frequency = data.inputValue(self.a_frequency).asFloat()
        v_a_offset = data.inputValue(self.a_offset).asFloat()
        h_out_sine = data.outputValue(self.out_sine)
        
        rslt = math.sin(v_a_rad * v_a_frequency) * v_a_amplitude + v_a_offset
        h_out_sine.setFloat( rslt )
        
        data.setClean(plug) 
    
    @classmethod
    def creator(cls):
        return OpenMayaMPx.asMPxPtr(cls())

    @classmethod
    def initializer(cls):        
        n_attr = OpenMaya.MFnNumericAttribute()
        
        cls.a_radians = n_attr.create("radians", "radians", OpenMaya.MFnNumericData.kFloat, 1)
        n_attr.setSoftMin(-10)
        n_attr.setSoftMax(10)
        
        cls.a_amplitude = n_attr.create("amplitude", "amplitude", OpenMaya.MFnNumericData.kFloat, 1)
        n_attr.setSoftMin(-10)
        n_attr.setSoftMax(10)
        
        cls.a_frequency = n_attr.create("frequency", "frequency", OpenMaya.MFnNumericData.kFloat, 1)
        n_attr.setSoftMin(0)
        n_attr.setSoftMax(5)
        
        cls.a_offset = n_attr.create("offset", "offset", OpenMaya.MFnNumericData.kFloat, 0)
        n_attr.setSoftMin(-10)
        n_attr.setSoftMax(10)
        
        cls.out_sine = n_attr.create("outSine","outSine", OpenMaya.MFnNumericData.kFloat, 0.0)
        n_attr.setWritable(False)
        
        cls.addAttribute(cls.a_radians)
        cls.addAttribute(cls.a_amplitude)
        cls.addAttribute(cls.a_frequency)
        cls.addAttribute(cls.a_offset)
        cls.addAttribute(cls.out_sine)
        
        cls.attributeAffects(cls.a_radians, cls.out_sine)
        cls.attributeAffects(cls.a_amplitude, cls.out_sine)
        cls.attributeAffects(cls.a_frequency, cls.out_sine)
        cls.attributeAffects(cls.a_offset,    cls.out_sine)


def initializePlugin(mobject):
    plugin=OpenMayaMPx.MFnPlugin(mobject, "Aaron Tzeng", "1.0.0", "Any")
    try:
        plugin.registerNode(
            NODE_NAME,
            NODE_ID,
            ktSine.creator,
            ktSine.initializer,
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


