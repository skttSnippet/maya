'''
================================================================
         NAME:  ktModule.py
      VERSION:  
       AUTHOR:  Aaron Kuolun Tzneg
LAST UPDATED :  12/01/2017

================================================================
'''



import pymel.core as pm
import maya.cmds as mc
import maya.api.OpenMaya as om
import os
import sys
import cPickle as pickle
import time


#
def addAttribute(node,attrName,attrType,maxValue=None,minValue=None,defaultValue=None):
    '''
    as title
    '''
    #preparing the command string to execute 
    string ="""mc.addAttr(node, ln=attrName, nn=attrName, at=attrType, max=maxValue, min=minValue, dv=defaultValue)"""
    if defaultValue==None:
        string = string.replace("dv=defaultValue","dv=0")
    else:
        string = string.replace("defaultValue",str(defaultValue))   
    if maxValue==None:
        string = string.replace("max=maxValue,","")
    else:
        string = string.replace("maxValue",str(maxValue))   
    if minValue==None:
        string = string.replace("min=minValue,","")
    else:
        string = string .replace("minValue",str(minValue))

    # ADDing the attribute!
    eval(string)
    mc.setAttr(node+'.'+attrName, e=True, keyable=True)

    #result
    resultAttr=node+'.'+attrName
    print "%s added!"%resultAttr
    return resultAttr

#
def saveCheck():
    '''pop up save file prompt window if file has unsaved changes
       return : int : 0 = save canceled. 1 = save not needed, scene saved, or user decided not to save.
    '''
    result = 1
    if mc.file(query=True, modified=True):
        result = pm.mel.saveChanges("")
    return result

#
def savedFileCheck():
    '''check if scene already has a saved file 
    '''
    result = True
    if not mc.file(query=True, sceneName=True):
        raise Exception ('no scene name.  Please save scene before proceeding.')
    return result

#
def vertsMorph(newMesh=None, oldMesh=None):
    '''between 2 mesh with identical vrt count and order, shape one into the other.
    '''
    newMesh = newMesh or mc.ls(sl=True)[0]
    oldMesh = oldMesh or mc.ls(sl=True)[1]
    
    vertCount = int(mc.polyEvaluate(oldMesh, vertex=True))
    vertStr =( ".vtx[0:" + str((vertCount - 1)) + "]") # temp_allVerts = selObj.vtx
    oldMeshVerts = pm.ls( oldMesh + vertStr, flatten=True)#convert to PyNode
    newMeshVerts = pm.ls( newMesh + vertStr, flatten=True)#convert to PyNode

    #save the postion of the vrts before blendshaping 
    oldVertPos = []
    for vtx in oldMeshVerts:
        oldVertPos.append(vtx.getPosition())
    # save the postion of the vrts after blendshaping
    newVertPos = []
    for vtx in newMeshVerts:
        newVertPos.append(vtx.getPosition())

    # get the value of offset position between before and after blendshaping
    offsetVec = []
    for v in range(len(oldMeshVerts)): 
        offsetVec.append(newVertPos[v] - oldVertPos[v])

    # combine vrt num list and offset value list into a dictionary
    offsetVertDict = dict(zip(oldMeshVerts,offsetVec))


    # apply the offset value to certian number of vrt in every selected model
    for k,v in  offsetVertDict.iteritems():
        pm.xform(k,t=v,r=True)

    sys.stdout.write('vertsMorph done\n')
    return

#
def mesh2Verts(mesh): 
    '''
    '''
    vertCount = int(mc.polyEvaluate(mesh, vertex=True))
    meshVerts = [ str(mesh) + ".vtx[" + str(i) + "]"  for i in range(vertCount)]
    return meshVerts
#    
def mesh2Edges(mesh): 
    '''
    '''
    edgeCount = int(mc.polyEvaluate(mesh, edge=True))
    meshEdges = [ str(mesh) + ".e[" + str(i) + "]"  for i in range(edgeCount)] 
    return meshEdges
#
def mesh2EdgeVertCoords(mesh):
    '''
    '''
    mSelList = om.MSelectionList()
    mDagPath = om.MDagPath()
    
    mesh = "%s"%mesh
    mSelList.add(mesh)
    meshDagP = mSelList.getDagPath(0)
    meshMfnSet = om.MFnMesh(meshDagP)
    edgeCount = int(mc.polyEvaluate(mesh, edge=True))
    edgeVerts = [ ( "%s.vtx[%s]"%( mesh, meshMfnSet.getEdgeVertices(i)[0] ),
                    "%s.vtx[%s]"%( mesh, meshMfnSet.getEdgeVertices(i)[1] ) )
                    for i in range(edgeCount) ] # get the 2 verts that make the edge
    edgeVertsCoord = [ ( tuple( mc.xform(d[0],ws=True,t=True,q=True) ),
                         tuple( mc.xform(d[1],ws=True,t=True,q=True) ) )
                    for d in edgeVerts ]# get coordinate of the 2 verts that make the edge

    return edgeVertsCoord      

#
def edges2vrts(edgeList=None):
    '''convert selected edges to vrts
    '''
    #flattens the edge so every component is identified individually
    edges = pm.ls(edgeList,flatten=True)
    #deal with the dups
    verts = list(set(sum(  [list( e.connectedVertices() )for e in edges],[]   )))
    #done with pymel. convert to unicode
    verts = [ str(v)for v in verts]
    return verts
#
def getCentroid(posList=None): 
    '''get the centroid for selected objects
    '''
    #return coordinate
    posList = posList or mc.ls(sl=True)
    vecSum = om.MVector(0,0,0)
    for pos in posList:
        vec =  om.MVector(pos)
        vecSum += vec
    centroid = vecSum/len(posList)

    return tuple(centroid)    
    #posList = [(1,2,3),(4,5,6),(7,8,9)]; getCentroid(posList)

#
def sel2Coord(sel=None):
    '''get world coordinates from selected
    '''
    sel = mc.ls(sel,flatten=True)
    posList = \
    [ mc.xform(obj,q=True,ws=True,rp=True) if mc.nodeType(obj) == "transform" 
    else( mc.xform(obj,q=True,ws=True,t=True) if mc.filterExpand(obj,sm=(28,30,31,32,34,35)) else None)
    for obj in sel]

    return posList
    #sel2Coord(pm.selected())

#
def sel2Curve(objs=None):
    '''create curve from selected transform nodes
    '''
    selObjs = objs or mc.ls(sl=True)
    ptPOSList = [ mc.xform(obj,q=1,ws=1,rp=1) for obj in selObjs]
    cv = mc.curve(p=ptPOSList,d=1)
    return cv

#
def curve2Joints(cv,jntSize=10):
    '''create joints along a curve on every control point
    '''
    
    cvDup = pm.PyNode( mc.duplicate(cv)[0] )
    #clean up the cvDup and setup the curve ready
    pm.delete(cvDup,ch=True)
    pm.makeIdentity(cvDup,apply=True, t=1, r=1, s=1, n=0)
    cvShape = cvDup.getShape()
    #get the position of all the CVs
    cvPosList = cvShape.getCVs()
    #get the position of one CV by index
    cv1 = cvShape.getCV(0)
    #get the number of CVs
    numCV = cvShape.numCVs()
    pm.select(d=True)
    jntList = []
    for pos in cvPosList:
        newJnt = pm.joint(p = pos,radius=jntSize)
        jntList.append( str(newJnt) )
        
    for jnt in jntList:
        pm.joint(jnt,sao='yup',zso=1,e=1,oj='xyz')
        
    pm.delete(cvDup)    
    
    return jntList

#
def meshIntersect(edgeVertsCoord=None, mesh2Intersect = None):
    '''see if a given edge(2 verts) interesects with mesh2Intersect
    '''

    # see if given mesh or edgeVertsCoord intersects with target mesh or not
    mSelList = om.MSelectionList()
    mDagPath = om.MDagPath()

    targetMesh = "%s"%mesh2Intersect 
    mSelList.add(targetMesh)
    targetDagP = mSelList.getDagPath(0)
    targetMfnSet = om.MFnMesh(targetDagP)
    
    edgeCount = len(edgeVertsCoord)
    hitCount = 0 
    for coord in edgeVertsCoord:
        rayStartPos = om.MFloatPoint( coord[0] )
        rayEndPos   = om.MFloatPoint( coord[1] )
        rayVec = om.MFloatVector(rayEndPos - rayStartPos)
        rayLen = rayVec.length()
        infoList = targetMfnSet.closestIntersection(rayStartPos, rayVec, om.MSpace.kWorld, 999, False)
        
        hitPos = infoList[0]
        hitParem = infoList[1]
        hitLen = om.MVector ( hitPos - rayStartPos ).length() 

        if hitParem == 0 : # not even hit at all
            continue
        elif hitParem != 0 :
            if hitLen <= rayLen: 
                #print True
                return True # once a function does return, it ends the function
            else: # hit point is further than the length of the edge, not intersecting
                hitCount += 1

        if hitCount == edgeCount:
            #print hitCount,edgeCount
            #print "inside geo or target too small"
            return False
            
    #print hitCount,edgeCount        
    #print False
    return False

#
def follicleCreateOnMesh(mesh=None, targetObjList=None, posList=None):
    '''create follicles on mesh or surface based on posList or targetObjectList
    '''

    #using cpom node determining the UV coordinate where follicles should be on a mesh
    if mc.nodeType(mesh) == 'mesh':
        mesh = mesh
        meshTfm = mc.listRelatives(mesh, parent=True, fullPath=True)[0]
    elif mc.nodeType(mesh) == 'transform':
        meshTfm = mesh
        mesh = mc.listRelatives(meshTfm, shapes=True, fullPath=True)[0]
    mc.makeIdentity(meshTfm,apply=True, t=1, r=1, s=1, n=0)
    
    targetObjList = targetObjList
    if targetObjList:
        posList = []
        for obj in targetObjList:
            pos = mc.xform(obj,q=True,ws=True,rp=True)
            posList.append(pos)
    else:
        posList = posList

    cpomNode = mc.createNode("closestPointOnMesh")
    mc.connectAttr( "%s.outMesh"%mesh,"%s.inMesh"%cpomNode,f=True )
    
    follicleList = []
    for pos in posList:
        
        follicle = mc.createNode("follicle")
        follicleTfm = mc.listRelatives(follicle, fullPath=True, parent=True)[0]  
        # connect follicle shape and follicle tfm node
        mc.connectAttr( "%s.outRotate"%follicle,"%s.rotate"%follicleTfm,f=True )
        mc.connectAttr( "%s.outTranslate"%follicle,"%s.translate"%follicleTfm,f=True )
        # connect mesh and follicle shape where all the attrs are.
        mc.connectAttr( "%s.outMesh"%mesh,"%s.inputMesh"%follicle,f=True )
        mc.connectAttr( "%s.worldMatrix[0]"%mesh,"%s.inputWorldMatrix"%follicle,f=True )

        mc.setAttr('%s.inPosition'%cpomNode, pos)

        parameterU = mc.getAttr('%s.parameterU'%cpomNode)
        parameterV = mc.getAttr('%s.parameterV'%cpomNode)

        mc.setAttr('%s.parameterU'%follicle,parameterU)
        mc.setAttr('%s.parameterV'%follicle,parameterV)

        follicleList.append(str(follicle))

    mc.select(cl=True)
    mc.delete(cpomNode)

    print follicleList
    return follicleList

#
def copyAnim(originObj,targetObj):
    '''copy animation from one to the other
       assuming they both have same attrs
    '''
    #if obj is connected with animCVs. Track them down
    animCVs= {}
    if isAnimCVConnected(originObj):
        animCVs = findAnimCV(originObj)
    else:
        raise Exception('no animation')

    animCVsCopy = {}
    for cv, origingFullAttr in animCVs.iteritems():
        #disconnect the animCVs
        mc.disconnectAttr(cv+'.output', origingFullAttr)
        #make a copy for every animCV
        #put them in a dict with corresponding attrs of targetObj. Then connectAttr them.
        animCVCopy     = mc.duplicate(cv, n= 'copied_'+cv )[0]
        targetFullAttr = origingFullAttr.replace(originObj, targetObj)
        animCVsCopy[animCVCopy ] = targetFullAttr
        mc.connectAttr(animCVCopy +'.output', targetFullAttr, f=True)
        #connect the animCVs back
        mc.connectAttr(cv+'.output', origingFullAttr, f=True)
    
    print animCVsCopy
    return animCVsCopy

#
def isAnimCVConnected(control):
    '''checks if a transform node has an animCurve node leading into one or more
    of its keyable channels'''

    keyableAttrs = mc.listAttr(control, k=True)
    for attr in keyableAttrs:
        inputs = mc.listConnections(control+'.'+attr, s=True, d=False)
        if inputs:
            if mc.nodeType(inputs[0]).startswith('animCurve'):
                return True

    return False

#
def findAnimCV(control):
    '''checks if a controller has an animCurve node leading into one or more
    of its keyable channels'''

    keyableAttrs = mc.listAttr(control, k=True)
    animCVsDict  = {}
    fullAttrName = ''
    for attr in keyableAttrs:
        fullAttrName = str(control) +'.'+ str(attr)
        inputs = mc.listConnections(fullAttrName, s=True, d=False)
        if inputs:
            if mc.nodeType(inputs[0]).startswith('animCurve'):
                animCVsDict[inputs[0]] = fullAttrName
                # { animCV node : control.attr }

    return animCVsDict

#
def flattenAnimCVs(animCurves):
    '''flatten anim graphes based on the value on the 1st key
    '''
    for cv in animCurves:
        values=mc.keyframe(cv, query=True, valueChange=True)
        keys  =mc.keyframe(cv, query=True, timeChange=True)
        mc.keyframe(cv,edit=True,absolute = True, valueChange = values[0], time=(keys[0]+1 , keys[-1]-1))
    return

#
def scaleAnimation(scaleValue=1):
    '''if the selected object is animated, tune up or down the value on every single key
    '''
    controls = mc.ls(sl=True)

    mc.undoInfo(openChunk=True)

    for con in controls:
        if isAnimCVConnected(con):
            keysFramesTime = mc.keyframe(con, query=True, timeChange=True)
            lastKeyTime = max( keysFramesTime )
            mc.scaleKey(con,
                        floatPivot=0, floatScale=1, includeUpperBound=False, 
                         timePivot=0,  timeScale=1, 
                        valuePivot=0, valueScale=scaleValue,time=(0,lastKeyTime+1))

    mc.undoInfo(closeChunk=True)
    return



#
def transferSkinweight(sourceMesh=None, targetMeshList=None):
    '''copy skinweight between geos, clear out existed skinClusters on targets
    '''
    sourceMesh =     sourceMesh     or mc.ls(sl=True)[0] # an mesh
    targetMeshList = targetMeshList or mc.ls(sl=True)[1:]# a list of meshes
    mc.select(cl=True)
    #get skinCluster from sourceMesh
    skinNodeSource = pm.mel.findRelatedSkinCluster(sourceMesh)  
    #query max influence number and influence joints
    maxInf = mc.skinCluster(skinNodeSource,q=True ,maximumInfluences=True)
    joints = mc.skinCluster(skinNodeSource,q=True ,inf=True)
    
    #loop through the targeMeshes
    skinNodeTargetList = []
    for targetMesh in targetMeshList:

        #if sourceMesh already bound, unbind it and clean up non deform history(tweaks node)
        if pm.mel.findRelatedSkinCluster(targetMesh):
            mc.skinCluster(targetMesh, e=True, ub=True)
           
            mc.select(targetMesh)
            pm.mel.doBakeNonDefHistory(1, ["prePost"])#delete non deform history
            mc.select(cl=True) 
            
        #bind new skin
        skinNodeTarget = mc.skinCluster(joints, targetMesh, 
                                        mi=maxInf,#maximumInfluences
                                        omi=False,#obeyMaxInfluences
                                        tsb=True,#toSelectedBones 
                                        bm=0,#bindMethod
                                        sm=0,#skinMethod
                                        nw=1,#normalizeWeights
                                        wd=0,#weightDistribution
                                        rui=False,#removeUnusedInfluence
                                        dr=4,#dropoffRate
                                        ihs=False#includeHiddenSelections
                                        )[0]
        mc.select(cl=True) 
        #perform copy skin weight
        mc.copySkinWeights(sourceSkin=skinNodeSource,destinationSkin=skinNodeTarget,
                           surfaceAssociation='closestPoint',
                           influenceAssociation=['oneToOne','closestJoint', 'closestBone'],
                           noMirror=True, #noMirror=False >> mirror skinweight mode
                           normalize=False
                           )
        
        skinNodeTargetList.append(skinNodeTarget)

    sys.stdout.write('skinweight transferred!\n')
    return skinNodeSource,skinNodeTargetList


#WIP. pretty slow
def exportSkinweight(oneMesh):
    '''export a skinweight json to exactly where the maya file saves with selected geo name
       a saved file needed for this func
    '''
    t0 = time.time()
    
    shapeTfm = oneMesh
    shapeTfmPy = pm.PyNode(oneMesh)
    shape = str( shapeTfmPy.getShape() )
    skClst = pm.mel.findRelatedSkinCluster(shapeTfm)  
    if not skClst:
        raise Exception ('no skincluster found')
        
    jntList = [str(jnt) for jnt in mc.skinCluster(skClst,query=True,inf=True)]

    vCount = int (mc.polyEvaluate( shapeTfm, vertex=True))
    vrts = (shape + ".vtx[0:" + str((vCount - 1)) + "]")
    allVrts = mc.ls(vrts , flatten=True)
    
    saveFileCheck()
    
    mayaProjCWD = os.path.split(pm.mel.file( q=True, l=True)[0])[0]
    fileName = shapeTfm + "_skinweights" +  '.sw'
    
    fullPathName = mayaProjCWD + "//"+fileName
    
    jntWeightDict = {}
    for vert in allVrts:
        infJntList = [jnt for jnt in mc.skinPercent(skClst, vert, query=True, transform=None) ]
        infSkWtList = mc.skinPercent(skClst, vert, q=True, v=True,ib=0.000000001)    
        jntWeightDict[ str(vert) ] = dict(zip(infJntList,infSkWtList))

    jntWeightDict['maxInf'] = mc.skinCluster(skClst,q=True,mi=True)
    
    with open( fullPathName, 'wb') as outfile:
        pickle.dump(jntWeightDict, outfile)

    t1 = time.time()
    print t1-t0
    sys.stdout.write('{}skinweight exported!\n'.format(shapeTfm))
    return fullPathName

#darn slow....WIP
def importSkin(oneMesh):
    '''look for and import the skinweight pickle file exported by exportSkinweight()
       a saved file needed for this func   
    '''
    t0 = time.time()

    shapeTfm = oneMesh
    shapeTfmPy = pm.PyNode(oneMesh)
    shape = str( shapeTfmPy.getShape() )

    vCount = int (mc.polyEvaluate(shapeTfm, vertex=True))
    vrts = (shape + ".vtx[0:" + str((vCount - 1)) + "]")
    allVrts = mc.ls( vrts , flatten=True)
    
    saveFileCheck()
    
    mayaProjCWD = os.path.split(pm.mel.file( q=True, l=True)[0])[0]
    fileName = shapeTfm + "_skinweights" +  '.sw'
    fullPathName = mayaProjCWD + "//"+fileName
    if not os.path.exists(fullPathName):# if file no exists
        raise Exception ('skinweight file not found')
    
    importDict = pickle.load(open( fullPathName ,"rb"))
    maxInf = importDict.pop("maxInf")
    jntWeightDict = importDict

    jntList = list ( set( [ str(key) for k,v in jntWeightDict.iteritems()  for key in v.keys()] ) )

    skClst=''
    if pm.mel.findRelatedSkinCluster( shapeTfm ):# if the mesh already has a skinCluster
        skClst2Remove = pm.mel.findRelatedSkinCluster(shapeTfm)
        mc.skinCluster(skClst2Remove, e=1, ub=1)
    
    skClst = mc.skinCluster(jntList , shapeTfm , mi=maxInf,tsb=True,normalizeWeights=1)[0]
    mc.select(d=True)
    
    #set vertex weights right from the dict
    for k,v in jntWeightDict.iteritems():
        pm.skinPercent( skClst , k, transformValue = v.items()) 
    
    
    t1 = time.time()
    print t1-t0
    sys.stdout.write('skinweight imported!\n')
    return skClst

    # # Assign weights to a large number of vertices,
    # # several at a time to reduce the number of calls
    # # to the skinPercent command.
    # #
    # for i in range(0,675,10):
    #   mc.select('pPlane1.vtx[%i]' % i,'pPlane1.vtx[%i]' % (i+1), 'pPlane1.vtx[%i]' % (i+2), 'pPlane1.vtx[%i]' % (i+3), 'pPlane1.vtx[%i]' % (i+4), 'pPlane1.vtx[%i]' % (i+5), 'pPlane1.vtx[%i]' % (i+6), 'pPlane1.vtx[%i]' % (i+7), 'pPlane1.vtx[%i]' % (i+8), 'pPlane1.vtx[%i]' % (i+9))
    #   mc.skinPercent( 'skinCluster1',transformValue=[('joint1', 0.5),('joint2', 0.5)] )

  



