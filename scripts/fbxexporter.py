import json
import re

import maya.cmds as cmds

if not "fbxmaya" in cmds.pluginInfo( query=True, listPlugins=True ):
    try:
        cmds.loadPlugin("fbxmaya.mll")
    except RuntimeError:
        pass

def set_general_fbx_flags():
    cmds.FBXResetExport()
    
    cmds.FBXExportShapes("-v", True)
    cmds.FBXExportSkins("-v", True)
    cmds.FBXExportUpAxis( cmds.upAxis(q=True, axis=True) )
    cmds.FBXExportConstraints("-v", False)
    cmds.FBXExportCameras("-v", False)
    cmds.FBXExportLights("-v", False)
    cmds.FBXExportEmbeddedTextures("-v", False)
    cmds.FBXExportInputConnections("-v", False)

def set_model_fbx_flags():
    set_general_fbx_flags()

    cmds.FBXExportSmoothingGroups("-v", True)
    cmds.FBXExportSmoothMesh("-v", False)
    cmds.FBXExportTangents("-v", True)
    
    cmds.FBXExportInAscii("-v", True)
    
def set_anim_fbx_flags(clip_min_time,clip_max_time):
    set_general_fbx_flags()
    
    cmds.playbackOptions(minTime=clip_min_time, maxTime=clip_max_time)
    
    cmds.FBXExportBakeComplexAnimation("-v", True)
    cmds.FBXExportBakeComplexStart("-v", clip_min_time)
    cmds.FBXExportBakeComplexEnd("-v", clip_max_time)
    cmds.FBXExportReferencedAssetsContent("-v", False)
    cmds.FBXExportBakeComplexStep("-v", 1)
    cmds.FBXExportUseSceneName("-v", False)
    cmds.FBXExportFileVersion("-v", "FBX201800")

    cmds.FBXExportInAscii("-v", True)
    
def do_fbx_export(fpath):
    cmds.FBXExport("-file", fpath, "-s")
    
def get_scene_existed_export_metanode_ls():
    return [o for o in cmds.ls("*_fbxmetadata*", typ="network")
            if cmds.objExists(f"{o}.is_kt_fbxmeta") and cmds.getAttr(f"{o}.is_kt_fbxmeta")==0] # 0=model 1=anim

def incremental_defaultname_generator(defaultname, target_ls, increment_max=20):
    """ check a list of names and see if any matches with the default incremented names and spits out the smallest incremental number"""
    num_ls = list(range(1, increment_max+1))
    # the regular expression to extract trailing number digits
    regex = re.compile(r"(\d+)(?!.*\d)")
    for tgt in target_ls:
        matched = re.findall(r"(\d+)(?!.*\d)", tgt) # trailing numbers
        unmatched = regex.sub('', tgt)              # the rest of the string
        # the tgt string doesn't contain any numbers so skip
        if not matched:
            continue
        # if the tgt is part of the default name incremental collection
        if unmatched==defaultname:
            matched_int = int(matched[0])
            if matched_int > increment_max: # number too big so don't care
                continue
            num_ls.remove(matched_int)
    # name_generator reaches capacity
    if not num_ls:
        return
    
    smallest_num = num_ls[0]
    rtn_defaultname = f"{defaultname}{smallest_num}"
    return rtn_defaultname

class FbxExportMetaData(object):
    
    SUFFIX = "_fbxmetadata"
    
    def __init__(self):
        self._name = ""
        self._name_of_export =  ""
        self._exportpath =  ""
        self._models_and_groups =  []
    
    def set_new_metanode(self):
        self._name = cmds.rename(cmds.createNode("network"), f"{self._name_of_export}{self.SUFFIX}")
        self.add_string_attr(self._name, "name_of_export")
        self.add_string_attr(self._name, "exportpath")
        self.add_string_attr(self._name, "models_and_groups")
        cmds.setAttr(f"{self._name}.name_of_export", self._name_of_export, typ="string")
        cmds.setAttr(f"{self._name}.exportpath", self._exportpath, typ="string")
        cmds.setAttr(f"{self._name}.models_and_groups", json.dumps(self._models_and_groups), typ="string")
        
        self.add_enum_attr(self._name, "is_kt_fbxmeta", ['model', 'anim'], keyable=False, lock=False)
        cmds.setAttr(f"{self._name}.is_kt_fbxmeta", 0)
        cmds.setAttr(f"{self._name}.is_kt_fbxmeta", lock=True)
        
    def set_existed_metanode(self, exportname):
        self._name = f"{exportname}{self.SUFFIX}" # string_fbxmetadata
        self._name_of_export = cmds.getAttr(f"{self._name}.name_of_export")
        self._exportpath =  cmds.getAttr(f"{self._name}.exportpath")
        self._models_and_groups =  json.loads(cmds.getAttr(f"{self._name}.models_and_groups"))
            
    def add_string_attr(self,node, attr, keyable=True, lock=False):
        attrname = f"{node}.{attr}"
        cmds.addAttr(node, ln=attr, dt="string", keyable=keyable)
        if lock:
            cmds.setAttr(attrname , lock=lock)
        return attrname
    
    def add_bool_attr(self, node, attr, keyable=True, lock=False):
        attrname = f"{node}.{attr}"
        cmds.addAttr(node, ln=attr, at='bool', keyable=keyable)
        if lock:
            cmds.setAttr(attrname , lock=lock)
        return attrname
    
    def add_enum_attr(self, node, attr, enum_ls, keyable=True, lock=False):
        attrname = f"{node}.{attr}"
        cmds.addAttr(node, ln=attr, at="enum", en=":".join(enum_ls), keyable=keyable)
        if lock:
            cmds.setAttr(attrname , lock=lock)
        return attrname
        
    def select_this_metanode(self):
        if not self._name:
            print("no associated metadata node")
            return
        cmds.select(self._name)
        
    
    @property
    def name(self):
        return self._name
        
    @property
    def name_of_export(self):
        return self._name_of_export
    @name_of_export.setter
    def name_of_export(self, new_name):
        """combine name assigning for _name_of_export and _name"""
        self._name_of_export = new_name
        cmds.setAttr(f"{self._name}.name_of_export", new_name, typ="string")
        # combined setter for _name_of_export and _name
        self._name = cmds.rename(self._name, f"{new_name}{self.SUFFIX}")

    @property
    def exportpath(self):
        return self._exportpath
    @exportpath.setter
    def exportpath(self,path):
        self._exportpath = path
        cmds.setAttr(f"{self._name}.exportpath", path, typ="string")

    @property
    def models_and_groups(self):
        return self._models_and_groups
    @models_and_groups.setter
    def models_and_groups(self, models):
        self._models_and_groups = models
        cmds.setAttr(f"{self._name}.models_and_groups", json.dumps(models), typ="string")

