import sys
import os
from PyQt5.QtCore import *
from PyQt5.QtGui import *
# from PyQt5.QtWidgets import (QAction, QApplication, QFileDialog, QLabel,
#         QMainWindow, QMenu, QMessageBox, QScrollArea, QSizePolicy, QWidget)
from PyQt5.QtWidgets import *
import numpy as np
import skimage.morphology, skimage.color, skimage.transform, skimage.io, skimage.filters
import cv2
import csv


class FundusFAG_Tool(QMainWindow):
    def __init__(self):
        super(FundusFAG_Tool, self).__init__()
        self.imageLabel = QLabel()
        self.imageLabel.setBackgroundRole(QPalette.Base)
        self.imageLabel.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.imageLabel.setScaledContents(True)

        self.imageLabel.setMouseTracking(True)
        self.setMouseTracking(True)

        self.scrollArea = QScrollArea()
        self.scrollArea.setBackgroundRole(QPalette.Dark)
        self.scrollArea.setWidget(self.imageLabel)
        self.scrollArea.setMouseTracking(True)
        self.setCentralWidget(self.scrollArea)
        self.createActions()
        self.createMenus()
        self.setWindowTitle("Image Viewer")
        self.menuBarRect = [self.menuBar().rect().x(),self.menuBar().rect().y(),\
                            self.menuBar().rect().width(),self.menuBar().rect().height()]
        # self.resize(2000, 1000+self.menuBarRect[3]) # default size
        self.fixed_image_size = [1500/4, 2000/4] # resize all of images
        self.scaleFactor = 1.0 # default scale factor
        self.isRunning = False # state of program
        self.bytesPerComponent = 3 # RGB

        self.nFile = 0 # number of files
        self.cur_fidx = 0 # selected file index
        self.cur_dir_idx = 0 # current subdirectory index
        self.cols = 4 # default columns of canvas
        self.rows = -1 # declare rows of canvas
        self.idx_label = None # declare index image
        self.need2DrawCanvas = True # for drawing canvas
        self.curMousePt = [0, 0] # declare current cursor point
        self.pressCtrl = False # (do no operating) state for pressing control key

        self.information = [] # (to do)

        # radio button dock for selecting information
        self.set_radio_button()
        self.group1.buttonClicked.connect(self.kind_toggled) # connect radio button click event to function
        self.group2.buttonClicked.connect(self.laterality_toggled) # connect radio button click event to function
        self.group3.buttonClicked.connect(self.available_toggled) # connect radio button click event to function

        # list dock for subdirectory
        self.set_subdirectory_list()

        # put information as text
        self.font = cv2.FONT_HERSHEY_SIMPLEX

        self.inform_file = 'inform.csv'
        self.cur_inform_file_path = ''

        # show full screen
        self.showFullScreen()
        # open directory browser
        self.openDirectory()

        if os.path.exists(self.cur_inform_file_path):
            self.read_existing_inform()

    def update_information(self, do_write = True):
        if self.information[self.cur_fidx]['kind'] == 0:
            self.button_kind1.setChecked(True)
            self.button_kind2.setChecked(False)
            self.button_kind3.setChecked(False)
            self.button_kind4.setChecked(False)
        elif self.information[self.cur_fidx]['kind'] == 1:
            self.button_kind1.setChecked(False)
            self.button_kind2.setChecked(True)
            self.button_kind3.setChecked(False)
            self.button_kind4.setChecked(False)
        elif self.information[self.cur_fidx]['kind'] == 2:
            self.button_kind1.setChecked(False)
            self.button_kind2.setChecked(False)
            self.button_kind3.setChecked(True)
            self.button_kind4.setChecked(False)
        elif self.information[self.cur_fidx]['kind'] == 3:
            self.button_kind1.setChecked(False)
            self.button_kind2.setChecked(False)
            self.button_kind3.setChecked(False)
            self.button_kind4.setChecked(True)
        else:
            self.group1.setExclusive(False)
            self.button_kind1.setChecked(False)
            self.button_kind2.setChecked(False)
            self.button_kind3.setChecked(False)
            self.button_kind4.setChecked(False)
            self.group1.setExclusive(True)

        if self.information[self.cur_fidx]['laterality'] == 0:
            self.button_laterality1.setChecked(True)
            self.button_laterality2.setChecked(False)
        elif self.information[self.cur_fidx]['laterality'] == 1:
            self.button_laterality1.setChecked(False)
            self.button_laterality2.setChecked(True)
        else:
            self.group2.setExclusive(False)
            self.button_laterality1.setChecked(False)
            self.button_laterality2.setChecked(False)
            self.group2.setExclusive(True)

        if self.information[self.cur_fidx]['available'] == True:
            self.button_available1.setChecked(True)
            self.button_available2.setChecked(False)
        elif self.information[self.cur_fidx]['available'] == False:
            self.button_available1.setChecked(False)
            self.button_available2.setChecked(True)
        else:
            self.group3.setExclusive(False)
            self.button_available1.setChecked(False)
            self.button_available2.setChecked(False)
            self.group3.setExclusive(True)

        if do_write:
            self.write_inform_file()

    def read_existing_inform(self):
        f = open(self.cur_inform_file_path, 'r')
        csv_reader = csv.reader(f)
        for i, read_data in enumerate(csv_reader):
            self.information[i]['kind'] = int(read_data[0])
            self.information[i]['laterality'] = int(read_data[1])

            if read_data[2] == 'True':
                self.information[i]['available'] = True
            else:
                self.information[i]['available'] = False
        self.update_information()
        f.close()

    def write_inform_file(self):
        f = open(self.cur_inform_file_path, 'w')
        csv_writer = csv.writer(f)
        for i, inform_dict in enumerate(self.information):
            csv_writer.writerow([inform_dict['kind'], inform_dict['laterality'],
             inform_dict['available'], self.file_path_list[i][0], self.file_path_list[i][1]])
        f.close()

    # to do
    def kind_toggled(self):
        if not self.isRunning:
            return

        if self.button_kind1.isChecked():
            self.information[self.cur_fidx]['kind'] = 0 # Fundus_gray
        elif self.button_kind2.isChecked():
            self.information[self.cur_fidx]['kind'] = 1 # Fundus_color
        elif self.button_kind3.isChecked():
            self.information[self.cur_fidx]['kind'] = 2 # FAG
        else:
            self.information[self.cur_fidx]['kind'] = 2 # mask

        self.write_inform_file()

    def laterality_toggled(self):
        if not self.isRunning:
            return

        if self.button_laterality1.isChecked():
            self.information[self.cur_fidx]['laterality'] = 0 # left
        else:
            self.information[self.cur_fidx]['laterality'] = 1 # right

        self.write_inform_file()

    def available_toggled(self):
        if not self.isRunning:
            return

        if self.button_available1.isChecked():
            self.information[self.cur_fidx]['available'] = True # available
        else:
            self.information[self.cur_fidx]['available'] = False # unavailable

        self.write_inform_file()

    def set_subdirectory_list(self):
        self.widget1 = QDockWidget("sub directory", self)
        self.listWidget = QListWidget()
        self.listWidget.clear()
        self.widget1.setWidget(self.listWidget)
        self.widget1.setFloating(False)
        self.addDockWidget(Qt.RightDockWidgetArea, self.widget1)
        self.listWidget.itemDoubleClicked.connect(self.item_double_click)

    def set_radio_button(self):
        self.group1 = QButtonGroup()
        self.group2 = QButtonGroup()
        self.group3 = QButtonGroup()
        self.button_kind1 = QRadioButton("Fundus_gray(shortcut:'1')")
        self.button_kind2 = QRadioButton("Fundus_color(shortcut:'2')")
        self.button_kind3 = QRadioButton("FAG(shortcut:'3')")
        self.button_kind4 = QRadioButton("Mask(shortcut:'M')")
        self.button_laterality1 = QRadioButton("Left(shortcut:'4')")
        self.button_laterality2 = QRadioButton("Right(shortcut:'5')")
        self.button_available1 = QRadioButton("Available(shortcut:'6')")
        self.button_available2 = QRadioButton("Unavailable(shortcut:'7')")
        self.group1.addButton(self.button_kind1)
        self.group1.addButton(self.button_kind2)
        self.group1.addButton(self.button_kind3)
        self.group1.addButton(self.button_kind4)
        self.group2.addButton(self.button_laterality1)
        self.group2.addButton(self.button_laterality2)
        self.group3.addButton(self.button_available1)
        self.group3.addButton(self.button_available2)

        self.widget2 = QDockWidget("button", self)
        buttonWidget = QLabel()
        buttonWidget.setAlignment(Qt.AlignCenter)
        buttonWidget.setFrameShape(QFrame.StyledPanel)

        button_layout = QVBoxLayout()

        kind_widget = QLabel()
        laterality_widget = QLabel()
        available_widget = QLabel()
        kind_widget.setAlignment(Qt.AlignCenter)
        kind_widget.setFrameShape(QFrame.StyledPanel)
        laterality_widget.setAlignment(Qt.AlignCenter)
        laterality_widget.setFrameShape(QFrame.StyledPanel)
        available_widget.setAlignment(Qt.AlignCenter)
        available_widget.setFrameShape(QFrame.StyledPanel)

        kind_layout = QVBoxLayout()
        laterality_layout = QVBoxLayout()
        available_layout = QVBoxLayout()
        kind_layout.addWidget(self.button_kind1)
        kind_layout.addWidget(self.button_kind2)
        kind_layout.addWidget(self.button_kind3)
        kind_layout.addWidget(self.button_kind4)
        laterality_layout.addWidget(self.button_laterality1)
        laterality_layout.addWidget(self.button_laterality2)
        available_layout.addWidget(self.button_available1)
        available_layout.addWidget(self.button_available2)

        kind_widget.setLayout(kind_layout)
        laterality_widget.setLayout(laterality_layout)
        available_widget.setLayout(available_layout)

        button_layout.addWidget(kind_widget)
        button_layout.addWidget(laterality_widget)
        button_layout.addWidget(available_widget)

        buttonWidget.setLayout(button_layout)
        self.widget2.setWidget(buttonWidget)
        self.widget2.setMinimumSize(200, 100)

        self.widget2.setFloating(False)
        self.addDockWidget(Qt.RightDockWidgetArea, self.widget2)

        ## if you want to set default, remove annotation
        # self.button_kind3.setChecked(True)
        # self.button_laterality1.setChecked(True)

    # add item into list viewer
    def addSubDirIntoListViewer(self):
        self.listWidget.clear()
        for i, cur_dir in enumerate(self.sub_dir_list['name']):
            if self.cur_dir_idx == i:
                self.listWidget.addItem(cur_dir+'<---')
            else:
                self.listWidget.addItem(cur_dir)

    # list item double click event
    def item_double_click(self, item):
        if not self.isRunning:
            return

        self.write_inform_file()
        self.cur_dir_idx = self.listWidget.currentRow()
        self.openChangedDirectory()

    # mouse button press event
    def mousePressEvent(self, QMouseEvent):
        if self.nFile == 0:
            return

        # get mouse position
        cursor = [int(np.round((QMouseEvent.pos().y() - self.menuBarRect[3]))), \
                  int(np.round(QMouseEvent.pos().x()))]

        # prevent Null(None)
        if self.idx_label[int(cursor[0]/self.scaleFactor), int(cursor[1]/self.scaleFactor)] != -1:
            # get selected image index
            self.cur_fidx = self.idx_label[int(cursor[0]/self.scaleFactor),
                                           int(cursor[1]/self.scaleFactor)]
            self.update_information()
            self.paint() # draw selected image

    # mouse button release event
    def mouseReleaseEvent(self, QMouseEvent):
        if self.nFile ==0:
            return

    # mouse move event
    def mouseMoveEvent(self, QMouseEvent):
        if self.nFile ==0:
            return

        # # get mouse position
        # cursor = [int(np.round((QMouseEvent.pos().y() - self.menuBarRect[3]))), \
        #           int(np.round(QMouseEvent.pos().x()))]
        # self.curMousePt = cursor # record current mouse position
        # self.paint() # draw current mouse position

    # key press event
    def keyPressEvent(self, event):
        # get key
        key = event.key()

        # pressed control key
        if key == Qt.Key_Control:
            self.pressCtrl = True
        # pressed [ key
        elif key == Qt.Key_BracketLeft:
            self.zoomOut()
        # pressed ] key
        elif key ==Qt.Key_BracketRight:
            self.zoomIn()
        # pressed W key(move up)
        elif key == Qt.Key_W:
            tmp_cur_fidx = self.cur_fidx - self.cols
            if tmp_cur_fidx >= 0:
                self.cur_fidx = tmp_cur_fidx
            self.update_information()
            self.paint()
        # pressed S key(move down)
        elif key == Qt.Key_S:
            tmp_cur_fidx = self.cur_fidx + self.cols
            if tmp_cur_fidx < self.nFile:
                self.cur_fidx = tmp_cur_fidx
            self.update_information()
            self.paint()
        # pressed A key(move left)
        elif key == Qt.Key_A:
            tmp_cur_fidx = self.cur_fidx - 1
            if tmp_cur_fidx >= 0:
                self.cur_fidx = tmp_cur_fidx
            self.update_information()
            self.paint()
        # pressed D key(move right)
        elif key == Qt.Key_D:
            tmp_cur_fidx = self.cur_fidx + 1
            if tmp_cur_fidx < self.nFile:
                self.cur_fidx = tmp_cur_fidx
            self.update_information()
            self.paint()
            # pressed D key(move right)
        elif key == Qt.Key_1:# fundus gray
            self.information[self.cur_fidx]['kind'] = 0
            self.update_information()
        elif key == Qt.Key_2:# fundus RGB
            self.information[self.cur_fidx]['kind'] = 1
            self.update_information()
        elif key == Qt.Key_3:# FAG
            self.information[self.cur_fidx]['kind'] = 2
            self.update_information()
        elif key == Qt.Key_M:  # mask
            self.information[self.cur_fidx]['kind'] = 3
            self.update_information()
        elif key == Qt.Key_4:# left
            self.information[self.cur_fidx]['laterality'] = 0
            self.update_information()
        elif key == Qt.Key_5:# right
            self.information[self.cur_fidx]['laterality'] = 1
            self.update_information()
        elif key == Qt.Key_6:# available
            self.information[self.cur_fidx]['available'] = True
            self.update_information()
        elif key == Qt.Key_7:# unavailable
            self.information[self.cur_fidx]['available'] = False
            self.update_information()


    # key release event
    def keyReleaseEvent(self, event):
        # get key
        key = event.key()
        if key == Qt.Key_Control:
            self.pressCtrl = False

    ## wheel event
    # def wheelEvent(self, event):
    #     if self.pressCtrl:
    #         dgree = event.angleDelta()
    #         print(dgree)

    # zoom in
    def zoomIn(self):
        self.scaleImage(1.25)

    # zoom out
    def zoomOut(self):
        self.scaleImage(0.8)

    # restore scale to original image
    def normalSize(self):
        self.imageLabel.adjustSize()
        self.scaleFactor = 1.0

    # fit to window frame size
    def fitToWindow(self):
        fitToWindow = self.fitToWindowAct.isChecked()
        self.scrollArea.setWidgetResizable(fitToWindow)
        if not fitToWindow:
            self.normalSize()

        self.updateActions()

    # resize event
    def resizeEvent(self, event):
        if self.isRunning == True:
            self.paint()

    # draw
    def paint(self):
        # get rows of current subdirectory image set
        if self.rows == -1:
            self.rows = int(np.ceil((len(self.img_list))/float(self.cols)))

        # draw all of image into canvas
        if self.need2DrawCanvas:
            self.need2DrawCanvas = False
            # declare canvas
            self.canvas = np.ones([self.fixed_image_size[0]*self.rows, self.fixed_image_size[1]*self.cols, 3], dtype=np.ubyte)*255

            # declare index image for record and initialize to -1
            self.idx_label = np.zeros([self.fixed_image_size[0]*self.rows, self.fixed_image_size[1]*self.cols], dtype=np.int16)
            self.idx_label[:, :] = -1

            # record to all of image position at canvas
            self.drawPosition = []
            for i in range(len(self.img_list)):
                appear_boundary = self.img_list[i]
                appear_boundary = skimage.transform.resize(appear_boundary, self.fixed_image_size)*255
                appear_boundary = appear_boundary.astype(np.ubyte)
                appear_boundary[0:2, :] = [255, 255, 255]
                appear_boundary[-2:, :] = [255, 255, 255]
                appear_boundary[:, 0:2] = [255, 255, 255]
                appear_boundary[:, -2:] = [255, 255, 255]

                self.drawPosition.append([self.fixed_image_size[0]*int(i/self.cols),self.fixed_image_size[0]*(int(i/self.cols)+1),
                    self.fixed_image_size[1]*int(i%self.cols),self.fixed_image_size[1]*(int(i%self.cols)+1)])

                self.canvas[self.drawPosition[-1][0]:self.drawPosition[-1][1],
                self.drawPosition[-1][2]:self.drawPosition[-1][3]] = appear_boundary
                self.idx_label[self.drawPosition[-1][0]:self.drawPosition[-1][1],
                self.drawPosition[-1][2]:self.drawPosition[-1][3]] = i

        ## draw additional information like selected image, current cursor
        # copy canvas
        cur_canvas = self.canvas.copy()
        # for i in range(len(self.drawPosition)):
        #     cur_img = cur_canvas[self.drawPosition[i][0]:self.drawPosition[i][1],
        #     self.drawPosition[i][2]:self.drawPosition[i][3]]
        #     cv2.putText(cur_img, 'Fundus/FAG', (cur_img.shape[1] / 4, 20), self.font, 1/self.scaleFactor,
        #                 (255, 255, 255), 1, cv2.LINE_AA)
        #     cv2.putText(cur_img, 'L/R', (cur_img.shape[1] / 4 * 3, 20), self.font, 1/self.scaleFactor, (255, 255, 255),
        #                 1, cv2.LINE_AA)

        # draw selected image differently
        cur_canvas[self.drawPosition[self.cur_fidx][0]:self.drawPosition[self.cur_fidx][1],
        self.drawPosition[self.cur_fidx][2]:self.drawPosition[self.cur_fidx][3], 2] = 128

        # # draw current curcor point
        # cv2.circle(cur_canvas, (int((self.curMousePt[1]-4)/self.scaleFactor), int((self.curMousePt[0]-4)/self.scaleFactor)), 2, (255,0,0), -1)

        # update viewing layer(similar to update device context in MFC)
        self.bytesPerLine = self.bytesPerComponent * cur_canvas.shape[1]
        image_q = QImage(cur_canvas.data, cur_canvas.shape[1], cur_canvas.shape[0], self.bytesPerLine, QImage.Format_RGB888)
        self.imageLabel.setPixmap(QPixmap.fromImage(image_q))
        self.imageLabel.resize(self.scaleFactor * self.imageLabel.pixmap().size())
        self.adjustScrollBar(self.scrollArea.horizontalScrollBar(), 1)
        self.adjustScrollBar(self.scrollArea.verticalScrollBar(), 1)
        self.updateActions()

    # open directory from selected path
    def openDirectory(self):
        self.need2DrawCanvas = True
        self.sub_dir_list = {}
        self.file_path_list = []
        self.img_list = []
        self.sub_dir_list['name'] = []
        self.sub_dir_list['path'] = []

        root_dir_path = QFileDialog.getExistingDirectory(self, "Open Directory",QDir.currentPath())
        if root_dir_path == "":
            return False

        root_dir_path = root_dir_path+'/'
        for sub_dir_name in sorted(os.listdir(root_dir_path)):
            path = root_dir_path + sub_dir_name + '/'
            if os.path.isdir(path):
                self.sub_dir_list['path'].append(root_dir_path + sub_dir_name + '/')
                self.sub_dir_list['name'].append(sub_dir_name)

        self.cur_inform_file_path = self.sub_dir_list['path'][self.cur_dir_idx] + self.inform_file
        self.addSubDirIntoListViewer()

        for fname in sorted(os.listdir(self.sub_dir_list['path'][self.cur_dir_idx])):
            is_dcm = fname.find('.dcm') != -1
            is_csv = fname.find('.csv') != -1
            if not is_dcm and not is_csv:
                self.file_path_list.append([self.sub_dir_list['path'][self.cur_dir_idx] + fname, fname])

        # read all images
        for fpath, fname in self.file_path_list:
            img = skimage.io.imread(fpath)
            if len(img.shape)==2:
                img = skimage.color.gray2rgb(img)
            self.img_list.append(img)
            self.information.append({'kind': -1, 'laterality': -1, 'available': False})

            if fpath.find('GRAY') is not -1:
                self.information[-1]['kind'] = 0
            elif img[:, :, 0].sum() != img[:, :, 1].sum() or fpath.find('RGB') is not -1:
                self.information[-1]['kind'] = 1
            elif fpath.find('FAG') is not -1:
                self.information[-1]['kind'] = 2

        self.nFile = len(self.file_path_list)
        if self.nFile != 0:
            self.isRunning = True
            self.menuBarRect = [self.menuBar().rect().x(), self.menuBar().rect().y(), \
                                self.menuBar().rect().width(), self.menuBar().rect().height()]
            self.paint()
            self.update_information(False)

    # when Debugging or update code, open directory from prefixed path.
    # if you do not edit, must annotation!
    def openFixedDirectory(self):
        self.need2DrawCanvas = True
        self.sub_dir_list = {}
        self.file_path_list = []
        self.img_list = []
        self.information = []

        # search directory
        root_dir_path = './data/'
        self.sub_dir_list['name'] = []
        self.sub_dir_list['path'] = []
        for sub_dir_name in sorted(os.listdir(root_dir_path)):
            path = root_dir_path + sub_dir_name + '/'
            if os.path.isdir(path):
                self.sub_dir_list['path'].append(root_dir_path + sub_dir_name + '/')
                self.sub_dir_list['name'].append(sub_dir_name)

        self.cur_inform_file_path = self.sub_dir_list['path'][self.cur_dir_idx] + self.inform_file

        # add subdirectory into list viewer
        self.addSubDirIntoListViewer()

        for fname in sorted(os.listdir(self.sub_dir_list['path'][self.cur_dir_idx])):
            is_dcm = fname.find('.dcm') != -1
            if is_dcm is False:
                self.file_path_list.append([self.sub_dir_list['path'][self.cur_dir_idx] + fname, fname])

        # read all images
        for fpath, fname in self.file_path_list:
            img = skimage.io.imread(fpath)
            if len(img.shape)==2:
                img = skimage.color.gray2rgb(img)
            self.img_list.append(img)
            self.information.append({'kind': -1, 'laterality': -1, 'available': False})

        if os.path.exists(self.cur_inform_file_path):
            self.read_existing_inform()

        self.nFile = len(self.file_path_list)
        if self.nFile != 0:
            self.isRunning = True
            self.menuBarRect = [self.menuBar().rect().x(), self.menuBar().rect().y(), \
                                self.menuBar().rect().width(), self.menuBar().rect().height()]
            self.paint()
            self.update_information(False)

    # if changing subdirectory, reload image or path, etc
    def openChangedDirectory(self):
        self.need2DrawCanvas = True
        self.cur_fidx = 0
        self.rows = -1
        self.file_path_list = []
        self.img_list = []
        self.information = []

        self.cur_inform_file_path = self.sub_dir_list['path'][self.cur_dir_idx] + self.inform_file

        # add subdirectory into list viewer
        self.addSubDirIntoListViewer()

        # reload image path
        for fname in sorted(os.listdir(self.sub_dir_list['path'][self.cur_dir_idx])):
            is_dcm = fname.find('.dcm') != -1
            is_csv = fname.find('.csv') != -1
            if not is_dcm and not is_csv:
                self.file_path_list.append([self.sub_dir_list['path'][self.cur_dir_idx] + fname, fname])

        # read all images
        for fpath, fname in self.file_path_list:
            img = skimage.io.imread(fpath)
            if len(img.shape) == 2:
                img = skimage.color.gray2rgb(img)
            self.img_list.append(img)
            self.information.append({'kind': -1, 'laterality': -1, 'available': False})

            if fpath.find('GRAY') is not -1:
                self.information[-1]['kind'] = 0
            elif img[:, :, 0].sum() != img[:, :, 1].sum() or fpath.find('RGB') is not -1:
                self.information[-1]['kind'] = 1
            elif fpath.find('FAG') is not -1:
                self.information[-1]['kind'] = 2

        if os.path.exists(self.cur_inform_file_path):
            self.read_existing_inform()

        self.nFile = len(self.file_path_list)
        if self.nFile != 0:
            self.isRunning = True
            self.menuBarRect = [self.menuBar().rect().x(), self.menuBar().rect().y(), \
                                self.menuBar().rect().width(), self.menuBar().rect().height()]
            self.paint()
            self.update_information(False)

    def createActions(self):
        self.exitAct = QAction("E&xit", self, shortcut="Ctrl+Q",
                triggered=self.close)

        self.zoomInAct = QAction("Zoom &In (25%)", self, shortcut="Ctrl++ or ]",
                enabled=False, triggered=self.zoomIn)

        self.zoomOutAct = QAction("Zoom &Out (25%)", self, shortcut="Ctrl+- or [",
                enabled=False, triggered=self.zoomOut)

        self.normalSizeAct = QAction("&Normal Size", self, shortcut="Ctrl+S",
                enabled=False, triggered=self.normalSize)

        self.fitToWindowAct = QAction("&Fit to Window", self, enabled=False,
                checkable=True, shortcut="Ctrl+F", triggered=self.fitToWindow)

        self.aboutQtAct = QAction("About &Qt", self,
                triggered=QApplication.instance().aboutQt)

        self.openDirectoyAct = QAction("&Open Directory...", self, triggered=self.openDirectory) # added by kjNoh 170714

        self.openFixedDirectoyAct = QAction("&Open Fixed Directory...", self,
                                       triggered=self.openFixedDirectory)  # added by kjNoh 171027

    def createMenus(self):
        self.fileMenu = QMenu("&File", self)
        self.fileMenu.addAction(self.openDirectoyAct)  # added by kjNoh 170714
        self.fileMenu.addAction(self.openFixedDirectoyAct)  # added by kjNoh 171027
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)

        self.viewMenu = QMenu("&View", self)
        self.viewMenu.addAction(self.zoomInAct)
        self.viewMenu.addAction(self.zoomOutAct)
        self.viewMenu.addAction(self.normalSizeAct)
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.fitToWindowAct)

        self.helpMenu = QMenu("&Help", self)
        self.helpMenu.addAction(self.aboutQtAct)

        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addMenu(self.viewMenu)
        self.menuBar().addMenu(self.helpMenu)

    def updateActions(self):
        # self.zoomInAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.zoomOutAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.normalSizeAct.setEnabled(not self.fitToWindowAct.isChecked())

    # image scaling
    def scaleImage(self, factor):
        self.scaleFactor *= factor
        self.imageLabel.resize(self.scaleFactor * self.imageLabel.pixmap().size())

        self.adjustScrollBar(self.scrollArea.horizontalScrollBar(), factor)
        self.adjustScrollBar(self.scrollArea.verticalScrollBar(), factor)

        self.zoomInAct.setEnabled(self.scaleFactor < 3.0)
        self.zoomOutAct.setEnabled(self.scaleFactor > 0.333)

    def adjustScrollBar(self, scrollBar, factor):
        scrollBar.setValue(int(factor * scrollBar.value()
                                + ((factor - 1) * scrollBar.pageStep()/2)))

## main call ##
if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = FundusFAG_Tool()
    gui.show()
sys.exit(app.exec_())

