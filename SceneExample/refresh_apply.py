'''
Created on Mar 28, 2017

@author: Alberto Sierra Lozano
'''
# PushDeformer
import os
from maya import cmds, mel
import getpass


def apply_deformer_selection():
    deformer = 'PushDeformer'
    objs = cmds.ls(sl=True, type='transform')
    if not len(objs):
        cmds.warning('No objects selected.')
        return
    for x in objs:
        cmds.select(x)
        name = str(x) + '_' + deformer
        name = mel.eval('formValidObjectName(\"{0}\");'.format(name))
        cmds.deformer(name=name, type=deformer)


def getUserName():
    return getpass.getuser()


def refreshScene(createTorus=True):
    module_path = r'C:\Users\{}\Documents\maya\2017\plug-ins'.format(getUserName())
    path = os.path.join(module_path, 'PushDeformer.py')
    if cmds.pluginInfo(path, q=1, l=1):
        cmds.file(new=True, f=1)
        cmds.unloadPlugin(os.path.basename(path))
    cmds.loadPlugin(path)
    cmds.file(new=1, f=1)
    if createTorus:
        polyTorus = cmds.polyTorus()
        cmds.select(polyTorus)

refreshScene()
apply_deformer_selection()
