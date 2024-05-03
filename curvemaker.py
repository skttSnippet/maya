import os
import gc
import math
import logging

import maya.cmds as cmds
import maya.api.OpenMaya as om

import ktcurvemaker.utils as utils

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)
_logger.disabled = True

TMP_DIR = utils.TMP_DIR

class CurveMaker(object):
    
    def __init__(self, catalog_dir=utils.crvtyp_dir):
        self.catalog_dir  =  catalog_dir
        self.catalog_dict = {}
        self.refresh_catalog()
        
        self.sel_crv_ls = []
        self.get_sel_crv_ls()
        
    def refresh_catalog(self):
        self.catalog_dict.clear()
        for f in os.listdir(self.catalog_dir):
            if f.endswith("nbscrvs"):
                crvtyp = f.replace(".nbscrvs","")
                crvtyp_data_f = os.path.join(self.catalog_dir, f)
                self.catalog_dict[ crvtyp] = crvtyp_data_f
    
    def get_sel_crv_ls(self):
        self.sel_crv_ls = [Curve(crv) for crv in utils.validate_selected_for_curves()]
    
    def refresh_curveshape_info_after_transform(self):
        for crv_inst in self.sel_crv_ls:
            crv_inst.refresh_nurbscurve_info_list()
        
    @utils.maya_undochunk
    def make_curve_from_lib(self, crvtyp):
        if not crvtyp in self.catalog_dict.keys():
            raise Exception("The curve shape type doesn't exist")
        
        crvtyp_f = self.catalog_dict[crvtyp]
        
        if not self.sel_crv_ls: # nothing selected so create one curve with target curve type
            crv_inst = Curve()
            crv_inst.set_curve_data(utils.load_json(crvtyp_f))
            
            return crv_inst
            
        for crv_inst in self.sel_crv_ls: # found curves in selection so convert them into curves of target curve type
            crv_inst.set_curve_data(utils.load_json(crvtyp_f))
            
        cmds.select( map(lambda instance: instance.name, self.sel_crv_ls))
        return self.sel_crv_ls
        
    def add_curvetype_to_lib(self, new_crvtype):
        one_sel_crv = utils.validate_selected_for_curves()[0] \
                      if utils.validate_selected_for_curves() else None
        if not one_sel_crv:
            print("Abort...please select a curve")
            return

        if new_crvtype in self.catalog_dict.keys():
            print(f"{new_crvtype} EXISTS. OVERWRITING THE SHAPE")
        else:
            print(f"{new_crvtype} ADDED.........")
        
        crvshp_data = Curve( one_sel_crv ).crv_data_ls
        new_crvtyp_f =os.path.join(self.catalog_dir, f"{new_crvtype}.nbscrvs")
        utils.save_json(new_crvtyp_f, crvshp_data)
        self.catalog_dict[new_crvtype] = new_crvtyp_f
        
    def remove_curvetype_from_lib(self, crvtyp):
        if not crvtyp in self.catalog_dict.keys():
            raise Exception(f"{crvtyp} TYPE DOEST NOT EXISTS IN THE LIBRARY")
            
        del_crvtyp_f = self.catalog_dict[crvtyp]
        os.remove(self.catalog_dict[crvtyp])
        del self.catalog_dict[crvtyp]
        
        return del_crvtyp_f
        
    def rename_curvetype_in_lib(self, crvtyp, new_crvtyp):
        crvtyp_f = self.catalog_dict[crvtyp]
        if not os.path.isfile(crvtyp_f):
            raise Exception(f"{crvtyp_f} DOES NOT EXIST")
        
        new_crvtyp_f = crvtyp_f.replace(crvtyp, new_crvtyp)
        
        os.rename(crvtyp_f, new_crvtyp_f)
        del self.catalog_dict[crvtyp]
        self.catalog_dict[new_crvtyp] = new_crvtyp_f
        
        return new_crvtyp_f
        
    @utils.maya_undochunk
    def curves_color(self, color_info):
        for crv_inst in self.sel_crv_ls:
            crv_inst.set_curve_override(True)
            crv_inst.set_curve_color(color_info)
            
    @utils.maya_undochunk
    def curves_rgb_blend(self, start_rgb=[], end_rgb=[]):
        """input more than 2 control curve shapes with RGB color,
        and color will blend based on selection order"""

        crvshp_bundle_ls = []
        for crv in self.sel_crv_ls:
            crvshp_bundle_ls.append(cmds.listRelatives(crv, s=True, typ='nurbsCurve'))
        
        if not start_rgb:
            start_rgb = cmds.getAttr(crvshp_bundle_ls[0][0] + '.overrideColorRGB')[0]
        if not end_rgb:
            end_rgb   = cmds.getAttr(crvshp_bundle_ls[-1][0] + '.overrideColorRGB')[0]
        
        num_seg = len(crvshp_bundle_ls[1:-1:])
        new_rgb_bundle_ls   = utils.num_ls_lerp(num_seg, start_rgb, end_rgb)
        
        # include the start_rgb and end_rgb in the rgb bundle list
        new_rgb_bundle_ls.insert(0, start_rgb)
        new_rgb_bundle_ls.append(end_rgb)
        _logger.debug(new_rgb_bundle_ls)
        for shp_bundle, rgb in zip(crvshp_bundle_ls, new_rgb_bundle_ls):
            _logger.debug(rgb)
            for shp in shp_bundle:
                cmds.setAttr(f'{shp}.overrideEnabled', True)
                cmds.setAttr(f"{shp}.overrideRGBColors", 1)
                cmds.setAttr(f"{shp}.overrideColorRGB", rgb[0], rgb[1], rgb[2])
            _logger.debug("BLENDED")
            
    @utils.maya_undochunk
    def curves_scale(self, val):
        for crv_inst in self.sel_crv_ls:
            crv_inst.set_curve_scale(val)
        
    @utils.maya_undochunk
    def curves_rotate(self, val, axis):
        for crv_inst in self.sel_crv_ls:
            crv_inst.set_curve_rotate(val, axis)

    @utils.maya_undochunk
    def curves_translate(self, val, axis):
        for crv_inst in self.sel_crv_ls:
            crv_inst.set_curve_translate(val, axis)
    
    def export_curves(self, exp_f=None):
        if not self.sel_crv_ls:
            print("No curves selected for export")
            return
        
        crv_bundle_data = []
        for crv_inst in self.sel_crv_ls:
            crv_bundle_data.append(crv_inst.crv_data_ls)
            
        if not (exp_f and os.path.isdir(os.path.dirname(exp_f)) ):
            exp_f = os.path.join(TMP_DIR, "tmp_curvebundle.json")
            
        utils.save_json(exp_f, crv_bundle_data)
        
        return(exp_f)
        
    def import_curves(self, imp_f=None):
        
        if not (imp_f and os.path.isfile(imp_f)):
            imp_f = os.path.join(TMP_DIR, "tmp_curvebundle.json")
            
        crv_bundle_data = utils.load_json(imp_f)
        
        if not self.sel_crv_ls:
            for data in crv_bundle_data:
                crv_inst = Curve()
                crv_inst.set_curve_data(data)
                self.sel_crv_ls.append(crv_inst)
            else:
                cmds.select([ crv_inst.dagpath for crv_inst in self.sel_crv_ls])
                
            return
        
        len_crv_bundle_data = len(crv_bundle_data)
        len_sel = len(self.sel_crv_ls)
        
        # make sure crv_tfm_ls and cv_shp_data_ls the same length if they are not
        if len_sel > len_crv_bundle_data:
            self.sel_crv_ls = self.sel_crv_ls[:len_crv_bundle_data:]
        elif len_crv_bundle_data > len_sel:
            crv_bundle_data  = crv_bundle_data [:len_sel:]
            
        for crv_inst, data in zip(self.sel_crv_ls, crv_bundle_data):
            crv_inst.set_curve_data(data)
        else:
            cmds.select([ crv_inst.dagpath for crv_inst in self.sel_crv_ls])
        
        return imp_f

class Curve(object):
    """Curve objects are transform's that contain 1 or more nurbsCurves"""
    def __init__(self, *args):
        
        self._name = ""
        self.dagpath = ""
        
        self.crvshp_ls = []
        
        self.color_info_ls = []
        self.override_info_ls = []
        self.crvshp_info_ls = []
        self.crv_data_ls = []# color, overrideEnabled, cv points
        
        if not args:
            self.crvshp_ls = [cmds.ls(cmds.createNode("nurbsCurve"), l=True)[0]]
            self.dagpath = cmds.listRelatives(self.crvshp_ls[0], p=True, fullPath=True)[0]
            self._name = utils.get_shortname_from_dagpath(self.dagpath)
        else:
            node = args[0]
            self.dagpath, self.crvshp_ls = utils.validate_curve(node)
            self._name = utils.get_shortname_from_dagpath(self.dagpath)
            
        self.refresh_curve_data_list()
    
    def __str__(self):
        return self._name
    
    @property
    def name(self):
        return self._name
    @name.setter
    def name(self, name):
        new_name = cmds.rename(self.dagpath, name)
        self._name = new_name
        self.dagpath, self.crvshp_ls = utils.validate_curve(self._name)
        
    def refresh_curve_data_list(self, skip_color=False):
        data_dict = dict()
        for s in self.crvshp_ls:
            dd = data_dict.setdefault(s,dict())
            
            if skip_color:
                dd.update( {"color":0} )
                dd.update( {"overrideEnabled": 0} )
            else:
                dd.update(self.get_nurbscurve_color_info(s))
                dd.update(self.get_nurbscurve_override_info(s))
                
            dd.update(self.get_nurbscurve_info(s))

        # trim off the keys() which are the curve shapes names
        self.crv_data_ls = list( data_dict.values() )
        # push the data to the other lists
        self.color_info_ls    = [info["color"] for info in self.crv_data_ls]
        self.override_info_ls = [ info["overrideEnabled"] for info in self.crv_data_ls]
        self.crvshp_info_ls  = [ info["nurbsCurve"] for info in self.crv_data_ls]

    def refresh_nurbscurve_info_list(self):
        """ for after Done with Translate, Rotate and Scale"""
        self.crvshp_info_ls = [self.get_nurbscurve_info(s)["nurbsCurve"] for s in self.crvshp_ls]
        
    def get_nurbscurve_color_info(self, node):
        """color info of a nurbsCurve node"""
        if cmds.getAttr(f"{node}.overrideRGBColors"):  # if colored by RGB
            color = [ round(n,3) for n in cmds.getAttr(f"{node}.overrideColorRGB")[0] ]
        else:                                          # if colored by index
            color = cmds.getAttr(f"{node}.overrideColor")
        return {"color":color}
    
    def get_nurbscurve_override_info(self, node):
        """override of a nurbsCurve node"""
        override_enabled = int(cmds.getAttr(node+".overrideEnabled"))
        return {'overrideEnabled':override_enabled}
    
    def get_nurbscurve_info(self, crvshp):
        """shape info of a nurbsCurve node"""
        d     = cmds.getAttr(f"{crvshp}.degree")
        form  = cmds.getAttr(f"{crvshp}.form")
        p     = []
        if cmds.objExists(f'{crvshp}.controlPoints[*]'):
            p = [(round(v[0],6), round(v[1],6), round(v[2],6))
                 for v in cmds.getAttr(f'{crvshp}.controlPoints[*]')]

        k = list(range(len(p) + d - 1))
        return { "nurbsCurve":{'d':d, 'k':k, 'p':p, 'per':form} }
    
    @utils.maya_undochunk
    def set_curve_data(self, crv_data_ls, skip_color=False):

        self.crv_data_ls      = crv_data_ls
        self.color_info_ls    = [info["color"] for info in crv_data_ls]
        self.override_info_ls = [ info["overrideEnabled"] for info in crv_data_ls]
        self.crvshp_info_ls  = [ info["nurbsCurve"] for info in crv_data_ls]
        
        if not self.crvshp_ls:
            raise Exception(f"{self._name} does't have any curve shapes. Skipping..." )
        
        cmds.delete(self.crvshp_ls)
        self.crvshp_ls = []
        
        for i, crvshp_info in enumerate(self.crvshp_info_ls):
            tmp_crvshp = self._set_curveshape(self._name, crvshp_info)
            print(f"{self._name}Shape{ str(i+1).zfill(2) }")
            new_crvshp = cmds.rename(tmp_crvshp, f"{self._name}Shape{ str(i+1).zfill(2) }")
            self.crvshp_ls.append(cmds.ls(new_crvshp, l=True)[0])

        if not skip_color:
            _logger.debug(f"self.color_info_ls:::{self.color_info_ls}")
            self.set_curve_color(self.color_info_ls)
            self.set_curve_override(self.override_info_ls)
        
    def set_curve_color(self, color_info_ls):
        # ACCOMODATE WHEN THERE'S ONLY JUST ONE COLOR VALUE PASSED IN . MAKE IT A LIST OF SAME COLOR VALUES
        if ( isinstance(color_info_ls, (list, tuple)) and
           all(isinstance(color, (float,int)) for color in color_info_ls) and
           len(color_info_ls)==3 ) or \
           ( isinstance(color_info_ls, int) ):
            color_info_ls = [color_info_ls for i in range(len(self.crvshp_ls))]
            
        
        for shp, color in zip(self.crvshp_ls, color_info_ls):
            self._set_nurbscurve_color(shp, color)
        
        self.color_info_ls = color_info_ls
        
    def set_curve_override(self, override_info_ls):
        # ACCOMODATE WHEN THERE'S ONLY JUST ONE BOOL VALUE PASSED IN. MAKE IT A LIST OF THE SAME BOOL VALUE
        if isinstance(override_info_ls, (bool, int)):
            override_info_ls = [override_info_ls for i in range(len(self.crvshp_ls))]
        
        
        for shp, bool_state in zip(self.crvshp_ls, override_info_ls):
            self._set_nurbscurve_override(shp, bool_state)
    
        self.override_info_ls = override_info_ls
    
    @utils.maya_undochunk
    def set_curve_scale(self, val):
        for crvshp, pt_ls in zip(self.crvshp_ls, [info["p"] for info in self.crvshp_info_ls]):
            self._set_nurbscurve_scale(crvshp, pt_ls, val)
            
    def set_curve_rotate(self, val, axis):
        for crvshp, pt_ls in zip(self.crvshp_ls, [info["p"] for info in self.crvshp_info_ls]):
            self._set_nurbscurve_rotate(crvshp, pt_ls, val, axis)

    def set_curve_translate(self, val, axis):
        for crvshp, pt_ls in zip(self.crvshp_ls, [info["p"] for info in self.crvshp_info_ls]):
            self._set_nurbscurve_translate(crvshp, pt_ls, val, axis)
            
    def _set_nurbscurve_color(self, crvshp, color):
        _logger.debug(f"COLOR:{color}")
        if isinstance(color, int):# index
            _logger.debug("ITS INDEX")
            cmds.setAttr(f"{crvshp}.overrideRGBColors", 0)
            cmds.setAttr(f"{crvshp}.overrideColor", color)
            
        if isinstance(color, (list, tuple)) and \
           all( isinstance(c, (float,int)) for c in color) and \
           len(color)==3:# RGB
            _logger.debug("ITS RGB")
            cmds.setAttr(f"{crvshp}.overrideRGBColors", 1)
            cmds.setAttr(f"{crvshp}.overrideColorRGB",
                         color[0],
                         color[1],
                         color[2])
    
    def _set_nurbscurve_override(self, crvshp, bool_state):
        cmds.setAttr(f'{crvshp}.overrideEnabled', bool_state)
        
    def _set_curveshape(self, crv_tfm, crvshp_info):
        crv_tmp = cmds.curve(**crvshp_info)
        new_crvshp = cmds.listRelatives(crv_tmp, s=True, typ='nurbsCurve')[0]
        
        cmds.parent(new_crvshp, crv_tfm, r=True, s=True)
        cmds.delete(crv_tmp)
        
        return new_crvshp
    
    def _set_nurbscurve_scale(self, crvshp, pt_ls, val):
        new_pt_ls = [ (pt[0]*val, pt[1]*val, pt[2]*val) for pt in pt_ls ]
        self._set_nurbscurve_cvpositions(crvshp, new_pt_ls)

    def _set_nurbscurve_rotate(self, crvshp, pt_ls, val, axis):
        new_pt_ls = []
        for pt in pt_ls:
            
            if axis=="x":
                euler_rot = om.MEulerRotation(math.radians(val), 0, 0)
            if axis=="y":
                euler_rot = om.MEulerRotation(0, math.radians(val), 0)
            if axis=="z":
                euler_rot = om.MEulerRotation(0, 0, math.radians(val))
            
            new_pt = om.MVector(pt[0], pt[1], pt[2]) * euler_rot.asMatrix()
            new_pt_ls.append( (new_pt[0], new_pt[1], new_pt[2]) )
        
        self._set_nurbscurve_cvpositions(crvshp, new_pt_ls)


    def _set_nurbscurve_translate(self, crvshp, pt_ls, val, axis):
        new_pt_ls = []
        for pt in pt_ls:
            
            if axis=="x":
                new_pt = (pt[0]+val, pt[1], pt[2])
            if axis=="y":
                new_pt = (pt[0], pt[1]+val, pt[2])
            if axis=="z":
                new_pt = (pt[0], pt[1], pt[2]+val)
            
            new_pt_ls.append( new_pt )
            
        self._set_nurbscurve_cvpositions(crvshp, new_pt_ls)
    
    def _set_nurbscurve_cvpositions(self, crvshp, pt_ls):
        
        # Maya API very fast but no undo
        mpoint_array = om.MPointArray([om.MPoint(pt[0], pt[1], pt[2]) for pt in pt_ls])
        nbscrv_mfn = om.MFnNurbsCurve(utils.get_mdagpath(crvshp))
        nbscrv_mfn.setCVPositions(mpoint_array, om.MSpace.kWorld)
        nbscrv_mfn.updateCurve()