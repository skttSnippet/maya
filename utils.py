# turn off recursive for all hierarchy traverse for now
import maya.cmds as cmds
import maya.api.OpenMaya as om

TMP_DIR = os.environ["TMP"]

_DIR = os.path.dirname(__file__)
crvtyp_dir = os.path.join(_DIR, "curvecollection")

def validate_dagnode(node):
    return "dagNode" in cmds.nodeType(node, inherited=True)

def validate_transform(node):
    if not validate_dagnode(node):
        return

    if cmds.nodeType(node) == "transform":
        return node
        
    return

def validate_grouptransform(node):
    if not validate_dagnode(node):
        return

    if validate_transform(node) and not cmds.listRelatives(node, s=True):
        return node
        
    return

def validate_mesh(node):
    if not validate_dagnode(node):
        return
        
    if cmds.nodeType(node) == "mesh":
        return node

    return

def validate_skinnedmesh(node):
    if not validate_mesh(node):
        return
        
    if any (cmds.nodeType(history)== "skinCluster"
            for history in cmds.listHistory(node)):
        return node

    return

def validate_model(node):
    """validate for a transfomr that contains mesh"""
    if validate_transform(node) and cmds.listRelatives(node, s=True, typ='mesh'):
        return node
        
    if validate_mesh(node) and cmds.listRelatives(node, p=True):
        tfm = cmds.listRelatives(node, p=True)[0]
        return tfm
    
    return

def validate_skinnedmodel(node):
    if not validate_model(node):
        return
        
    mesh = cmds.listRelatives(node, s=True, typ='mesh')[0]
    if validate_skinnedmesh(mesh):
        return node

    return

def is_dagnode(node):
    return bool(validate_dagnode(node))

def is_transform(node):
    return bool(validate_transform(node))

def is_grouptransform(node):
    return bool(validate_grouptransform(node))

def is_mesh(node):
    return bool(validate_mesh(node))

def is_skinnedmesh(node):
    return bool(validate_skinnedmesh(node))

def is_model(node):
    return bool(validate_model(node))

def is_skinnedmodel(node):
    return bool(validate_skinnedmodel(node))

def get_alldagchildren(node,recur=False):
    """recursively traverse a hierarchy to collect dag nodes
    """
    children = cmds.listRelatives(node,children=True) or []
    if not children:
        return []
    
    rtn_nodes = []
    for child in children:
        rtn_nodes.append(child)
        
        if cmds.listRelatives(child, children=True) and recur==True:
                rtn_nodes.extend(get_alldagchildren(child))
            
    return rtn_nodes

def get_modelchildren(node, recur=False):
    """ collect geometries under the node
    """
    return [ validate_model(o) for o in get_alldagchildren(node, recur=recur)
            if is_model(o) and is_transform(o)]
    
def validate_modelgroup(node, recur=False):
    
    if not is_grouptransform(node):
        return
    
    if not get_alldagchildren(node, recur=recur):
        return
        
    childmodel_count = 0
    for o in get_alldagchildren(node, recur=recur):
        if (is_model(o)):
            childmodel_count += 1
            continue
        elif (is_grouptransform(o)):
            continue
        else:
            return
    else:
        if not childmodel_count==0: # meaning meaning at least one child is model
            return node
        else: # meaning the children are all group nodes
            return
        
def is_modelgroup(node, recur=False):
    return bool(validate_modelgroup(node, recur=recur))

def find_groupparent_for_model(node, recur=False):
    if not is_model(node):
        return
    
    grpparent = cmds.listRelatives(node, p=True)[0]
    if is_modelgroup(grpparent, recur):
        return grpparent
    
    return

def model_has_groupparent(node, recur=False):
    return bool(find_groupparent_for_model(node, recur=recur))

def collect_models_n_modelgroups(object_ls):
    if not object_ls:
        return
    return [o for o in object_ls if ( is_model(o) or is_modelgroup(o) )]
    

def is_intermediateobject(node):
    if not cmds.objExists(f"{node}.intermediateObject"):
        return
    return cmds.getAttr(f"{node}.intermediateObject")



def num_ls_lerp(num_segment, start_ls, end_ls):
    """blend numbers between 2 same length lists of numbers
       each list in same_idx_new_val_ls contain numbers of the same index
       among the newly interpolated lists
       rotate it like a matrx of by 90 degree using zip() to cheat
       ex:
       [8.0,  6.0, 4.0],           \\   (8.0, 1.75, 3.5, 3.25),
       [1.75, 2.5, 3.25],     ------\\   (6.0, 2.5,  4.0, 4.5),
       [3.5,  4.0, 4.5],      ------//  (4.0, 3.25, 4.5, 5.75)
       [3.25, 4.5, 5.75]           //
    """
    # if num_segment is not interger, return
    if not isinstance(num_segment, int):
        print('num_to_interpolate not valid')
        return
    # if start_list and end_list not list or tuple type, return
    if not all( isinstance(ls, (list,tuple)) for ls in [start_ls, end_ls]):
        print('start and end list have to be tuples or lists')
        return
    # start_list and end_list don't just contain floats
    if not all(isinstance(n, (float,int)) for n in start_ls) or \
       not all(isinstance(n, (float,int)) for n in end_ls):
        print('start and end list can only contain numbers')
        return

    same_idx_new_val_ls = []
    for start, end in zip(start_ls, end_ls):
        step_val = (end - start)/(num_segment + 1)
        newNumbers = [start + (step_val*(i+1)) for i in range(num_segment)]
        same_idx_new_val_ls.append(newNumbers)

def maya_undochunk(function):
    @functools.wraps(function)
    def wrap(*args, **kwargs):
        try:
            cmds.undoInfo(openChunk=True, chunkName=function.__name__)
            return function(*args, **kwargs)
        finally:
            cmds.undoInfo(closeChunk=True)
    
    wrap.unwrapped = function # for turning on/off for decorator
    return wrap

def mdagpath(dagnode):
    m_sel = om.MSelectionList()
    m_sel.add(dagnode)
    return m_sel.getDagPath(0)

def shortname_from_dagpath(dagpath):
    return dagpath.rpartition("|")[-1]
