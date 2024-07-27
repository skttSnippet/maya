import os
import json

from PySide2 import QtCore, QtGui, QtWidgets
import maya.cmds as cmds

import ktexporter.fbxexporter as fbxexp
import ktexporter.utils as utils

from ktexporter.qtutils import MAYA_WIN
from ktexporter.qtutils import UiLoader


class ModelExporterUi(QtWidgets.QWidget):
    
    WIN_TITLE = "Skeletal Mesh Exporter"
    WIN_NAME = "kt_skelmeshexporter"
    EXPORT_DEFAULTNAME = "newexport"
    
    def __init__(self, parent=None):
        super(ModelExporterUi, self).__init__(parent)
        self.setParent(MAYA_WIN)
        
        self.init_ui()
        self.create_actions()
        self.create_widgets()
        self.create_connections()
        
        self.sel_lw_exports_itemname = ""
        
        self.initialise_exportitems_for_listwidget()
        
    def init_ui(self):
        
        UiLoader().load_ui(os.path.join(os.path.dirname(__file__),
                                        "modelexporterui.ui"), self)
        self.setWindowFlags(QtCore.Qt.Window)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True) # UI will delete itself when closed
        
        self.setWindowTitle(self.WIN_TITLE)
        self.setObjectName(self.WIN_NAME)
        self.setGeometry(-1500, 700, 700, 500)
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)
        
    def create_actions(self):
        
        ########################################### NEW ACTIONS CREATING STARTS
        self.action_refresh = QtWidgets.QAction("Refresh the Exporter", self)
        self.action_refresh.setIcon(QtGui.QIcon(":refresh.png"))
        self.action_selectmetanode = QtWidgets.QAction("Select Metanode", self)
        self.action_selectmetanode.setIcon(QtGui.QIcon(":selectObject.png"))
        
        self.about_action = QtWidgets.QAction("About", self)
        ############################################# NEW ACTIONS CREATING DONE
        
    def create_widgets(self):
        
        ########################################### NEW WIDGETS CREATING STARTS
        self.menubar = QtWidgets.QMenuBar()
        self.menubar.setSizePolicy(QtWidgets.QSizePolicy.Expanding,# horizontal
                                   QtWidgets.QSizePolicy.Maximum)  # vertical
        self.menubar.setContextMenuPolicy(QtCore.Qt.PreventContextMenu) # no more RMB "whatsthis" popup menu on menubar
        self.menu_settings = QtWidgets.QMenu("Settings")
        self.menu_help = QtWidgets.QMenu("Help")
        self.menu_help.addAction(self.about_action)
        
        self.menubar.addMenu(self.menu_settings)
        self.menubar.addMenu(self.menu_help)
        
        self.menu_layout.insertWidget(0, self.menubar)

        self.toolbar = QtWidgets.QToolBar()
        self.toolbar.setIconSize(QtCore.QSize(20,20))
        self.toolbar.addAction(self.action_refresh)
        self.toolbar.addAction(self.action_selectmetanode)
        
        self.toolbar_layout.addWidget(self.toolbar)
        ############################################# NEW WIDGETS CREATING DONE
        self.tw_models.setIconSize(QtCore.QSize(20, 20))
        
        self.btn_exports_add.setIcon(QtGui.QIcon(":UVTBAdd.png"))
        self.btn_exports_remove.setIcon(QtGui.QIcon(":UVTBRemove.png"))

        self.btn_models_clear.setIcon(QtGui.QIcon(":trash.png"))
        self.btn_models_add.setIcon(QtGui.QIcon(":UVTBAdd.png"))
        self.btn_models_remove.setIcon(QtGui.QIcon(":UVTBRemove.png"))
        
        self.btn_exp_dir.setIcon(QtGui.QIcon(":fileOpen.png"))
        self.btn_prescript_f.setIcon(QtGui.QIcon(":fileOpen.png"))
        self.btn_postscript_f.setIcon(QtGui.QIcon(":fileOpen.png"))
        
        
        
    def lw_exports_ctxmenu(self, qpos):
        """ popup menu for thumbnail view items"""
        if not self.get_selected_lw_exports_item(): # no listwidgetitem selected
            return
        ctx_menu = QtWidgets.QMenu()
        ctx_menu.addAction(self.action_selectmetanode)
        ctx_menu.exec_(self.lw_exports.mapToGlobal(qpos))


    def create_connections(self):
        self.about_action.triggered.connect(self.about)
        self.action_selectmetanode.triggered.connect(self.select_metanode)

        self.btn_exports_add.clicked.connect(self._btn_exports_add_clicked)
        self.btn_exports_remove.clicked.connect(self._btn_exports_remove_clicked)
        
        self.btn_models_clear.clicked.connect(self._btn_models_clear_clicked)
        self.btn_models_add.clicked.connect(self._btn_models_add_clicked)
        self.btn_models_remove.clicked.connect(self._btn_models_remove_clicked)

        self.btn_exp_dir.clicked.connect(self._btn_exp_dir_clicked)
        self.btn_prescript_f.clicked.connect(self._btn_prescript_f_clicked)
        self.btn_postscript_f.clicked.connect(self._btn_postscript_f_clicked)
        
        self.btn_export_models.clicked.connect(self._btn_export_models_clicked)
        
        self.lw_exports.customContextMenuRequested[QtCore.QPoint].connect(self.lw_exports_ctxmenu)
        self.lw_exports.itemSelectionChanged.connect(self._lw_exports_itemselectionchanged)
        self.lw_exports.itemChanged.connect(self._lw_exports_itemchanged)
        
        self.le_exp_dir.textChanged.connect(self._le_exp_dir_textChanged)
        self.le_exp_dir.editingFinished.connect(self._le_exp_dir_textChanged)
        
    def _btn_exports_add_clicked(self,signal_val):
        exportitemname_ls = self.get_exportitemname_list()
        new_defaultname = fbxexp.incremental_defaultname_generator(
                                                self.EXPORT_DEFAULTNAME,
                                                exportitemname_ls)
        if not new_defaultname: #name_generator reaches capacity
            return
        item = self.create_export_listwidgetitem() # just an empty widget item
        item.metadata.set_new_metanode() # initiate metanode
        item.setText(new_defaultname)
        item.setToolTip(new_defaultname)
        self.lw_exports.addItem(item)
        item.setSelected(True)
        
    def _btn_exports_remove_clicked(self):
        pass
        
    def _btn_models_clear_clicked(self):
        pass
    def _btn_models_add_clicked(self):
        valid_sel_ls = utils.collect_models_n_modelgroups( cmds.ls(sl=True, l=True) )
        self.refresh_model_treewidget_items(valid_sel_ls)
        item = self.get_selected_lw_exports_item()
        item.metadata.models_and_groups = valid_sel_ls
        
    def _btn_models_remove_clicked(self):
        pass
    def _btn_exp_dir_clicked(self):
        self.filedialog_dir()
        
    def _btn_prescript_f_clicked(self):
        pass
    def _btn_postscript_f_clicked(self):
        pass
    
    def _btn_export_models_clicked(self):
        scene_exp_metanode_ls = fbxexp.get_scene_existed_export_metanode_ls()
        fbxexp.set_general_fbx_flags()
        fbxexp.set_model_fbx_flags()
        
        for node in scene_exp_metanode_ls:
            metadata = fbxexp.FbxExportMetaData()
            metadata.set_existed_metanode( cmds.getAttr(f"{node}.name_of_export") )
            model_ls = metadata.models_and_groups
            
            root_jnts = ["Pelvis_bind", "Pelvis_helper"]
            cmds.select(model_ls)
            cmds.select(root_jnts,add=True)
            
            exp_path = os.path.join(metadata.exportpath, metadata.name_of_export+".fbx")
            print(exp_path)
            
            fbxexp.do_fbx_export(exp_path)
            
    def _lw_exports_itemselectionchanged(self):
        if not self.get_selected_lw_exports_item():
            print("CURRSELECTION::None")
            self.ui_metadata_clear()
            return
        
        self.sel_lw_exports_itemname = self.get_selected_lw_exports_item().text()
        self.ui_metadata_refresh()
        print(f"CURRSELECTION::{self.sel_lw_exports_itemname}")

    def _lw_exports_itemchanged(self,sginal_item):
        self.post_item_renaming(sginal_item)
        
    def _le_exp_dir_textChanged(self):
        self.le_exp_dir.clearFocus()
        self.save_le_exp_dir_to_metadata()
        
    def initialise_exportitems_for_listwidget(self):
        self.build_scene_existed_exports_to_listwidget()
    
    def build_scene_existed_exports_to_listwidget(self):
        scene_exp_metanode_ls = fbxexp.get_scene_existed_export_metanode_ls()
        print(scene_exp_metanode_ls)
        for metanode in scene_exp_metanode_ls:
            name_of_export = metanode.replace("_fbxmetadata","")
            print(metanode)
            print(name_of_export)
            
            item = self.create_export_listwidgetitem() # just an empty widget item
            item.metadata.set_existed_metanode(name_of_export) # initiate metanode
            item.setText(name_of_export)
            item.setToolTip(name_of_export)
            self.lw_exports.addItem(item)
            item.setSelected(True)

    def get_exportitem_list(self):
        return [self.lw_exports.item(x) for x in range(self.lw_exports.count())]
    
    def get_exportitemname_list(self):
        return [self.lw_exports.item(x).text() for x in range(self.lw_exports.count())]

    def get_selected_lw_exports_item(self):
        sel_listwidgetitem_ls = self.lw_exports.selectedItems()
        
        if not sel_listwidgetitem_ls:
            return
        
        sel_lw_exports_item = sel_listwidgetitem_ls[0]
        return sel_lw_exports_item

    def create_export_listwidgetitem(self):
        item = ExportListItem()
        item.setTextAlignment(QtCore.Qt.AlignLeft)
        item.setFlags(QtCore.Qt.ItemIsEditable |
                      QtCore.Qt.ItemIsEnabled  |
                      QtCore.Qt.ItemIsSelectable) # for renaming listwidget
        return item

    def save_le_exp_dir_to_metadata(self):
        curr_exp_item = self.get_selected_lw_exports_item()
        if not curr_exp_item:
            return
        curr_exp_item.metadata.exportpath = self.le_exp_dir.text()
        print(f"_le_exp_dir_textChanged{curr_exp_item}")

    def refresh_model_treewidget_items(self, model_n_group_ls):
        self.tw_models.clear()
        modelgroup_ls = []
        model_ls = []
        for o in model_n_group_ls:
            print(f"OO{o}")
            if utils.is_model(o):
                model_ls.append(utils.validate_model(o))
            elif utils.is_modelgroup(o):
                modelgroup_ls.append(utils.validate_modelgroup(o))
        
        for model in model_ls:
            item = ModelTreeItem([model.rpartition("|")[-1]])
            item.set_appearance()
            self.tw_models.addTopLevelItem(item)
            
        for group in modelgroup_ls:
            item = ModelGroupTreeItem([group.rpartition("|")[-1]])
            item.set_appearance()
            childmodel_ls = utils.get_modelchildren(group)
            item.add_modelitems(childmodel_ls)
            self.tw_models.addTopLevelItem(item)

    def ui_metadata_refresh(self):
        curr_item = self.get_selected_lw_exports_item()
        self.le_exp_dir.setText(curr_item.metadata.exportpath)
        
        print(type(curr_item.metadata.models_and_groups))
        self.refresh_model_treewidget_items(curr_item.metadata.models_and_groups)
        
    def ui_metadata_clear(self):
        self.sel_lw_exports_itemname = ""
        self.tw_models.clear()
        self.le_exp_dir.setText("")
        
    def post_item_renaming(self, sginal_item):
        curr_item = sginal_item
        self.sel_lw_exports_itemname = curr_item.text()
        curr_item.set_nameofexport(curr_item.text())
        
    def filedialog_dir(self):
        exp_dir_dialog = QtWidgets.QFileDialog(parent=self, 
                                               directory=os.environ["USERPROFILE"], 
                                               options=QtWidgets.QFileDialog.DontResolveSymlinks | QtWidgets.QFileDialog.ShowDirsOnly)
        exp_dir_dialog.setFileMode(QtWidgets.QFileDialog.Directory)
        
        exp_dir = exp_dir_dialog.getExistingDirectory(caption="Select Export Folder")
        if exp_dir:
            print(exp_dir)
            self.le_exp_dir.setText(exp_dir)
            
            
    def select_metanode(self):
        curr_item = self.get_selected_lw_exports_item()
        if not curr_item:
            return
        
        curr_item.metadata.select_this_metanode()
        
    def about(self):
        QtWidgets.QMessageBox.about(self, "About Mesh Exporter", "Add About Text Here")


class ExportListItem(QtWidgets.QListWidgetItem):
    def __init__(self, *args, **kwargs):
        super(ExportListItem, self).__init__(*args, **kwargs)
        
        self.metadata = fbxexp.FbxExportMetaData()

    def set_nameofexport(self, new_name):
        self.metadata.name_of_export = new_name
        
    def setText(self,new_text):
        """ Overwritiing Qt method
            bind text assigning for listwidgetitem/metanode name/export name
        """
        super(ExportListItem, self).setText(new_text)
        self.set_nameofexport(new_text)

class ModelTreeItem(QtWidgets.QTreeWidgetItem):
    def __init__(self, *args, **kwargs):
        super(ModelTreeItem, self).__init__(*args, **kwargs)
        self.is_skinned = False
        self.is_grouped = False
        self.is_missing = False
        
        if utils.is_skinnedmodel(args[0]):
            self.is_skinned = True
        
    def set_appearance(self):
        if self.is_missing:
            self.setIcon(0, QtGui.QIcon(":question.png"))
            self.setToolTip(0, "Mesh does not exist - {}".format(self.text(0)))
        elif self.is_skinned:
            self.setIcon(0, QtGui.QIcon(":mesh.svg"))
        else:
            self.setIcon(0, QtGui.QIcon(":SP_MessageBoxWarning.png"))
            self.setToolTip(0, "Mesh is not skinned - {}".format(self.text(0)))

class ModelGroupTreeItem(QtWidgets.QTreeWidgetItem):
    def __init__(self, *args, **kwargs):
        super(ModelGroupTreeItem, self).__init__(*args, **kwargs)
        self.is_missing = False

    def set_appearance(self):
        if self.is_missing:
            self.setIcon(0, QtGui.QIcon(":question.png"))
            self.setToolTip(0, "Group node does not exist - {}".format(self.text(0)))
        else:
            self.setIcon(0, QtGui.QIcon(":transform.svg"))

    def add_modelitems(self, model_ls):
        for model in model_ls:
            item = ModelTreeItem([model])
            item.set_appearance()
            item.is_grouped = True
            self.addChild(item)

    @property
    def mesh_items(self):
        return [self.child(i) for i in range(self.childCount())]

if __name__ == "__main__":
    try:
        feui.close() # pylint: disable=E0601
        feui.deleteLater()
    except:
        pass
    feui = ModelExporterUi()
    feui.show()


