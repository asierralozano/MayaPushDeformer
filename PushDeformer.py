'''
Created on Mar 28, 2017

@author: Alberto Sierra Lozano
'''
# PushDeformer
import sys
import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx
import math

nodeName = "PushDeformer"
nodeId = OpenMaya.MTypeId(0x103fff)


class Push(OpenMayaMPx.MPxDeformerNode):
    '''
    Commands ----> MPxCommand
    Custom   ----> MPxNode
    Deformer ----> MPxDeformerNode    
    '''
    mObj_Amplitude = OpenMaya.MObject()
    mObj_Displace = OpenMaya.MObject()
    mObj_Matrix = OpenMaya.MObject()

    def __init__(self):
        OpenMayaMPx.MPxDeformerNode.__init__(self)

    def deform(self, dataBlock, geoIterator, matrix, geometryIndex):
        """Function

        Main function of the deformer

        Arguments:
            dataBlock {MDataBlock} -- the node's datablock
            geoIterator {MItGeometry} -- an iterator for the current geometry being deformed. 
            matrix {MMatrix} -- the geometry's world space transformation matrix. 
            geometryIndex {int} -- the index corresponding to the requested output geometry.
        """
        input = OpenMayaMPx.cvar.MPxGeometryFilter_input
        # 1. Attach a handle to input Array Attribute.
        dataHandleInputArray = dataBlock.outputArrayValue(input)
        # 2. Jump to particular element
        dataHandleInputArray.jumpToElement(geometryIndex)
        # 3. Attach a handle to specific data block
        dataHandleInputElement = dataHandleInputArray.outputValue()
        # 4. Reach to the child - inputGeom
        inputGeom = OpenMayaMPx.cvar.MPxGeometryFilter_inputGeom
        dataHandleInputGeom = dataHandleInputElement.child(inputGeom)
        inMesh = dataHandleInputGeom.asMesh()

        # Envelope
        envelope = OpenMayaMPx.cvar.MPxGeometryFilter_envelope
        dataHandleEnvelope = dataBlock.inputValue(envelope)
        envelopeValue = dataHandleEnvelope.asFloat()

        # Amplitude
        dataHandleAmplitude = dataBlock.inputValue(Push.mObj_Amplitude)
        amplitudeValue = dataHandleAmplitude.asFloat()

        # Displace
        dataHandleDisplace = dataBlock.inputValue(Push.mObj_Displace)
        displaceValue = dataHandleDisplace.asFloat()

        # Matrix
        dataHandleMatrix = dataBlock.inputValue(Push.mObj_Matrix)
        matrixValue = dataHandleMatrix.asMatrix()

        # Read the translation from Matrix
        mTransMatrix = OpenMaya.MTransformationMatrix(matrixValue)
        translationValue = mTransMatrix.getTranslation(OpenMaya.MSpace.kObject)  # MVector

        mFloatVectorArray_normal = OpenMaya.MFloatVectorArray()
        mFnMesh = OpenMaya.MFnMesh(inMesh)
        mFnMesh.getVertexNormals(False, mFloatVectorArray_normal, OpenMaya.MSpace.kObject)

        mPointArray_meshVert = OpenMaya.MPointArray()
        # Itering over all the vertex of the geo to apply the deformer
        while(not geoIterator.isDone()):
            pointPosition = geoIterator.position() * matrix
            weight = self.weightValue(dataBlock, geometryIndex, geoIterator.index())
            direction = pointPosition - translationValue  # MPoint
            distance = OpenMaya.MVector(direction).length()
            distance_to_displace = max(0, displaceValue - distance)

            power = distance_to_displace * amplitudeValue * weight * envelopeValue
            # angle_between = mFloatVectorArray_normal[geoIterator.index()].angle(OpenMaya.MFloatVector(direction))
            angle_between = abs(mFloatVectorArray_normal[geoIterator.index()] * OpenMaya.MFloatVector(direction))

            push_power = power * angle_between
            normal_power = power - push_power

            pointPosition.x = pointPosition.x + direction[0] * push_power + mFloatVectorArray_normal[geoIterator.index()].x * normal_power
            pointPosition.y = pointPosition.y + direction[1] * push_power + mFloatVectorArray_normal[geoIterator.index()].y * normal_power
            pointPosition.z = pointPosition.z + direction[2] * push_power + mFloatVectorArray_normal[geoIterator.index()].z * normal_power

            mPointArray_meshVert.append(pointPosition)
            # geoIterator.setPosition(pointPosition)
            geoIterator.next()
        geoIterator.setAllPositions(mPointArray_meshVert)

    def accessoryNodeSetup(self, dagModifier):
        """Function

        This method is called by the deformer command. It allows to create "accesories" for the deformer

        Arguments:
            dagModifier {MDagModifier} -- the dag modifier to which the method will add commands

        Returns:
            MStatusCode -- Status of the connection
        """
        mObjLocator = dagModifier.createNode("locator")
        mFnDependLocator = OpenMaya.MFnDependencyNode(mObjLocator)
        mPlugWorld = mFnDependLocator.findPlug("worldMatrix")
        mObj_WorldAttr = mPlugWorld.attribute()

        mStatusConnect = dagModifier.connect(mObjLocator, mObj_WorldAttr, self.thisMObject(), Push.mObj_Matrix)
        return mStatusConnect

    def accessoryAttribute(self):
        """Function

        Function to return the attribute to which an accessory shape is connected

        Returns:
            MObject -- The accessory attribute 
        """
        return Push.mObj_Matrix


def deformerCreator():
    nodePtr = OpenMayaMPx.asMPxPtr(Push())
    return nodePtr


def nodeInitializer():
    """Function

    This function initialize the Node of the deformer, and set the attrs of the Deformer Attributes
    """
    mFnAttr = OpenMaya.MFnNumericAttribute()
    Push.mObj_Amplitude = mFnAttr.create("AmplitudeValue", "AmplitudeVal", OpenMaya.MFnNumericData.kFloat, 0.0)
    mFnAttr.setKeyable(1)
    mFnAttr.setMin(-10.0)
    mFnAttr.setMax(10.0)

    # Displace Attribute
    Push.mObj_Displace = mFnAttr.create("DisplaceValue", "DispVal", OpenMaya.MFnNumericData.kFloat, 0.0)
    mFnAttr.setKeyable(1)
    mFnAttr.setMin(-10.0)
    mFnAttr.setMax(10.0)

    # Matrix Attribute
    mFnMatrixAttr = OpenMaya.MFnMatrixAttribute()
    Push.mObj_Matrix = mFnMatrixAttr.create("MatrixAttribute", "matAttr")
    mFnMatrixAttr.setStorable(0)
    mFnMatrixAttr.setConnectable(1)

    # Connect with Deformer Node
    Push.addAttribute(Push.mObj_Amplitude)
    Push.addAttribute(Push.mObj_Displace)
    Push.addAttribute(Push.mObj_Matrix)

    outputGeom = OpenMayaMPx.cvar.MPxGeometryFilter_outputGeom
    Push.attributeAffects(Push.mObj_Amplitude, outputGeom)
    Push.attributeAffects(Push.mObj_Displace, outputGeom)
    Push.attributeAffects(Push.mObj_Matrix, outputGeom)


def initializePlugin(mobject):
    """Function

    Method for initialize Plugins in Maya

    Arguments:
        mobject {MObject} -- MObject of the plugin
    """
    mplugin = OpenMayaMPx.MFnPlugin(mobject, "Alberto Sierra Lozano", "1.0")
    try:
        mplugin.registerNode(nodeName, nodeId, deformerCreator, nodeInitializer, OpenMayaMPx.MPxNode.kDeformerNode)
    except:
        sys.stderr.write("Failed to register node: %s" % nodeName)
        raise


def uninitializePlugin(mobject):
    """Function

    Method for deregister Plugins in Maya

    Arguments:
        mobject {MObject} -- MObject of the plugin
    """
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.deregisterNode(nodeId)
    except:
        sys.stderr.write("Failed to deregister node: %s" % nodeName)
        raise
