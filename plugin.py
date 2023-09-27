from __future__ import absolute_import
# 2017 - Antonio Carlon
from PyQt5.QtCore import pyqtSignal
from builtins import str
from builtins import range
from builtins import object
from qgis.PyQt.QtCore import QObject, Qt
from qgis.PyQt.QtGui import QIcon, QColor, QPen, QBrush
from qgis.PyQt.QtWidgets import QAction, QMessageBox, QGraphicsTextItem
from math import sqrt, sin, cos, pi, pow
from qgis.gui import *
from qgis.core import *
from PyQt5.QtGui import *
from PyQt5.QtCore import Qt
import sys, os
from . import resources
import threading
import qgis.utils

from qgis.core import QgsVectorLayer, QgsProject, QgsDistanceArea, QgsPoint, QgsPointXY, QgsGeometry, QgsWkbTypes
from qgis.gui import QgsMessageBar, QgsMapToolEdit, QgsRubberBand

name = "Split Features On Steroids"
moveVerticesName = "Move Vertices"
addVerticesName = "Add Vertices"
removeVerticesName = "Remove Vertices"
moveSegmentName = "Move segment"
closeLineName = "Close line"
openLineName = "Open line"
moveLineName = "Move line"
areaUnits = {0 :"ac" , 1 : "km<sup>2</sup>", 2 : "ft<sup>2</sup>", 3 : "sq yd", 4 : "sq mi", 5 : "ha", 6 : "m<sup>2</sup>", 7 : "M<sup>2</sup>", 8 : "deg<sup>2</sup>", 9 : ""}
maxDistanceHitTest = 5

class SplitFeaturesOnSteroidsPlugin(object):
	mapTool = None

	def __init__(self, iface):
		self.iface = iface

	def initGui(self):
		self.toolbar = self.iface.addToolBar(name)
		self.toolbar.setObjectName(name)
		
		icon = QIcon(":/plugins/SplitPolygonShowingAreas/icon.png")
		self.action = QAction(icon, name, self.iface.mainWindow())
		self.action.setCheckable(True)
		self.action.triggered.connect(self.onClick)
		self.toolbar.addAction(self.action)

		self.actionMoveVertices = QAction(QIcon(":/plugins/SplitPolygonShowingAreas/moveVertices.png"), moveVerticesName, self.iface.mainWindow())
		self.actionMoveVertices.setCheckable(True)
		self.actionMoveVertices.triggered.connect(self.onClickMoveVertices)
		self.toolbar.addAction(self.actionMoveVertices)

		self.actionAddVertices = QAction(QIcon(":/plugins/SplitPolygonShowingAreas/addVertices.png"), addVerticesName, self.iface.mainWindow())
		self.actionAddVertices.setCheckable(True)
		self.actionAddVertices.triggered.connect(self.onClickAddVertices)
		self.toolbar.addAction(self.actionAddVertices)

		self.actionRemoveVertices = QAction(QIcon(":/plugins/SplitPolygonShowingAreas/removeVertices.png"), removeVerticesName, self.iface.mainWindow())
		self.actionRemoveVertices.setCheckable(True)
		self.actionRemoveVertices.triggered.connect(self.onClickRemoveVertices)
		self.toolbar.addAction(self.actionRemoveVertices)

		self.actionMoveSegment = QAction(QIcon(":/plugins/SplitPolygonShowingAreas/moveSegment.png"), moveSegmentName, self.iface.mainWindow())
		self.actionMoveSegment.setCheckable(True)
		self.actionMoveSegment.triggered.connect(self.onClickMoveSegment)
		self.toolbar.addAction(self.actionMoveSegment)

		self.actionLineClose = QAction(QIcon(":/plugins/SplitPolygonShowingAreas/lineClose.png"), closeLineName, self.iface.mainWindow())
		self.actionLineClose.setCheckable(False)
		self.actionLineClose.triggered.connect(self.onClickLineClose)
		self.toolbar.addAction(self.actionLineClose)
		
		self.actionLineOpen = QAction(QIcon(":/plugins/SplitPolygonShowingAreas/lineOpen.png"), openLineName, self.iface.mainWindow())
		self.actionLineOpen.setCheckable(False)
		self.actionLineOpen.triggered.connect(self.onClickLineOpen)
		self.toolbar.addAction(self.actionLineOpen)

		self.actionMoveLine = QAction(QIcon(":/plugins/SplitPolygonShowingAreas/moveLine.png"), moveLineName, self.iface.mainWindow())
		self.actionMoveLine.setCheckable(True)
		self.actionMoveLine.triggered.connect(self.onClickMoveLine)
		self.toolbar.addAction(self.actionMoveLine)

		self.iface.addPluginToMenu(name, self.action)
		self.iface.addPluginToMenu(name, self.actionMoveVertices)
		self.iface.addPluginToMenu(name, self.actionAddVertices)
		self.iface.addPluginToMenu(name, self.actionRemoveVertices)
		self.iface.addPluginToMenu(name, self.actionMoveSegment)
		self.iface.addPluginToMenu(name, self.actionLineClose)
		self.iface.addPluginToMenu(name, self.actionLineOpen)
		self.iface.addPluginToMenu(name, self.actionMoveLine)
		self.help_action = QAction("Help", self.iface.mainWindow())
		self.help_action.triggered.connect(self.onHelp)
		self.iface.addPluginToMenu(name, self.help_action)

		self.iface.currentLayerChanged.connect(self.currentLayerChanged)

		self.enableTool()

	def disableAll(self):
		self.actionMoveVertices.setChecked(False)
		self.actionMoveVertices.setEnabled(False)
		self.actionAddVertices.setChecked(False)
		self.actionAddVertices.setEnabled(False)
		self.actionRemoveVertices.setChecked(False)
		self.actionRemoveVertices.setEnabled(False)
		self.actionMoveSegment.setChecked(False)
		self.actionMoveSegment.setEnabled(False)
		self.actionLineClose.setEnabled(False)
		self.actionLineOpen.setEnabled(False)
		self.actionMoveLine.setChecked(False)
		self.actionMoveLine.setEnabled(False)

	def unload(self):
		self.iface.removePluginMenu(name, self.action)
		self.iface.removePluginMenu(name, self.actionMoveVertices)
		self.iface.removePluginMenu(name, self.actionAddVertices)
		self.iface.removePluginMenu(name, self.actionRemoveVertices)
		self.iface.removePluginMenu(name, self.actionMoveSegment)
		self.iface.removePluginMenu(name, self.actionLineClose)
		self.iface.removePluginMenu(name, self.actionLineOpen)
		self.iface.removePluginMenu(name, self.actionMoveLine)
		self.iface.removePluginMenu(name, self.help_action)
		self.iface.removeToolBarIcon(self.action)
		self.iface.removeToolBarIcon(self.actionMoveVertices)
		self.iface.removeToolBarIcon(self.actionAddVertices)
		self.iface.removeToolBarIcon(self.actionRemoveVertices)
		self.iface.removeToolBarIcon(self.actionMoveSegment)
		self.iface.removeToolBarIcon(self.actionLineClose)
		self.iface.removeToolBarIcon(self.actionLineOpen)
		self.iface.removeToolBarIcon(self.actionMoveLine)

	def onHelp(self):
		qgis.utils.showPluginHelp(filename="index")

	def onClick(self):
		print("onclick")
		self.disableAll()
		if not self.action.isChecked():
			if self.mapTool != None and len(self.mapTool.capturedPoints) >= 2:
				reply = QMessageBox.question(self.iface.mapCanvas(), "Cancel splitting line?", "Your splitting line has " + str(len(self.mapTool.capturedPoints)) + " points. Do you want to remove it?", QMessageBox.Yes, QMessageBox.No)
				if reply == QMessageBox.No:
					self.action.setChecked(True)
					self.mapTool.restoreAction()
					return

			if self.mapTool != None:
				self.mapTool.stopCapturing()
			self.iface.mapCanvas().unsetMapTool(self.mapTool)
			self.mapTool = None
			return
		layer = self.iface.activeLayer()
		if layer == None or not isinstance(layer, QgsVectorLayer) or (layer.wkbType() != QgsWkbTypes.Polygon and layer.wkbType() != QgsWkbTypes.MultiPolygon and layer.wkbType() != QgsWkbTypes.Polygon25D and layer.wkbType() != QgsWkbTypes.MultiPolygon25D):
			self.iface.messageBar().pushMessage("No Polygon Vectorial Layer Selected", "Select a Polygon Vectorial Layer first", level=QgsMessageBar.WARNING)
			self.action.setChecked(False)
			return
		selectedFeatures = layer.selectedFeatures()
		if selectedFeatures == None or len(selectedFeatures) == 0:
			self.iface.messageBar().pushWarning( "No Features Selected", "Select some features first")
			self.action.setChecked(False)
			return
		
		self.action.setChecked(True)
		self.mapTool = SplitMapTool(self.iface.mapCanvas(), layer, self.actionMoveVertices, self.actionAddVertices, self.actionRemoveVertices, self.actionMoveSegment, self.actionLineClose, self.actionLineOpen, self.actionMoveLine)
		self.mapTool.setAction(self.action)
		self.iface.mapCanvas().setMapTool(self.mapTool)
		self.mapTool.redrawActions()

	def onClickMoveVertices(self):
		if not self.actionMoveVertices.isChecked():
			if self.mapTool != None:
				self.mapTool.stopMovingVertices()
			return

		self.mapTool.startMovingVertices()

	def onClickAddVertices(self):
		if not self.actionAddVertices.isChecked():
			if self.mapTool != None:
				self.mapTool.stopAddingVertices()
			return

		self.actionAddVertices.setChecked(True)
		self.mapTool.startAddingVertices()

	def onClickRemoveVertices(self):
		if not self.actionRemoveVertices.isChecked():
			if self.mapTool != None:
				self.mapTool.stopRemovingVertices()
			return

		self.actionRemoveVertices.setChecked(True)
		self.mapTool.startRemovingVertices()

	def onClickMoveSegment(self):
		if not self.actionMoveSegment.isChecked():
			if self.mapTool != None:
				self.mapTool.stopMovingSegment()
			return

		self.actionMoveSegment.setChecked(True)
		self.mapTool.startMovingSegment()

	def onClickLineClose(self):
		self.mapTool.lineClose()

	def onClickLineOpen(self):
		self.mapTool.lineOpen()

	def onClickMoveLine(self):
		if not self.actionMoveLine.isChecked():
			if self.mapTool != None:
				self.mapTool.stopMovingLine()
			return

		self.actionMoveLine.setChecked(True)
		self.mapTool.startMovingLine()

	def currentLayerChanged(self):
		if self.mapTool != None:
			self.mapTool.stopCapturing()

		layer = self.iface.activeLayer()
		if layer != None:
			try:
				layer.editingStarted.disconnect(self.layerEditingChanged)
			except:
				pass
			try:
				layer.editingStopped.disconnect(self.layerEditingChanged)
			except:
				pass
			try:
				layer.selectionChanged .disconnect(self.layerEditingChanged)
			except:
				pass
			
			if isinstance(layer, QgsVectorLayer):
				layer.editingStarted.connect(self.layerEditingChanged)
				layer.editingStopped.connect(self.layerEditingChanged)
				layer.selectionChanged.connect(self.layerSelectionChanged)
			
		self.enableTool()		

	def layerEditingChanged(self):
		if self.mapTool != None:
			self.mapTool.stopCapturing()
		self.enableTool()	

	def layerSelectionChanged(self):
		if self.mapTool != None:
			self.mapTool.stopCapturing()
		self.enableTool()

	def enableTool(self):
		self.disableAll()
		self.action.setEnabled(False)
		layer = self.iface.activeLayer()
		
		if layer != None and isinstance(layer, QgsVectorLayer):
			selectedFeatures = layer.selectedFeatures()
			if isinstance(layer, QgsVectorLayer) and (layer.wkbType() == QgsWkbTypes.Polygon or layer.wkbType() == QgsWkbTypes.MultiPolygon or layer.wkbType() == QgsWkbTypes.Polygon25D or layer.wkbType() == QgsWkbTypes.MultiPolygon25D) and selectedFeatures != None and len(selectedFeatures) > 0 and layer.isEditable():
				self.action.setEnabled(True)

class SplitMapTool(QgsMapToolEdit):
	snapClicked = pyqtSignal(QgsPointXY, Qt.MouseButton)
	def __init__(self, canvas, layer, actionMoveVertices, actionAddVertices, actionRemoveVertices, actionMoveSegment, actionLineClose, actionLineOpen, actionMoveLine):
		super(SplitMapTool, self).__init__(canvas)
		
        
		self.canvas = canvas
		self.snapIndicator = QgsSnapIndicator(canvas)
		self.snapper = self.canvas.snappingUtils()
		self.scene = canvas.scene()
		self.layer = layer
		self.actionMoveVertices = actionMoveVertices
		self.actionAddVertices = actionAddVertices
		self.actionRemoveVertices = actionRemoveVertices
		self.actionMoveSegment = actionMoveSegment
		self.actionLineClose = actionLineClose
		self.actionLineOpen = actionLineOpen
		self.actionMoveLine = actionMoveLine
		self.initialize()

	def initialize(self):
		try:
			self.canvas.renderStarting.disconnect(self.mapCanvasChanged)
		except:
			pass
		self.canvas.renderStarting.connect(self.mapCanvasChanged)
		try:
			self.layer.editingStopped.disconnect(self.stopCapturing)
		except:
			pass
		self.layer.editingStopped.connect(self.stopCapturing)

		self.selectedFeatures = self.layer.selectedFeatures()
		self.rubberBand = None
		self.tempRubberBand = None
		self.capturedPoints = []
		self.capturing = False
		self.setCursor(Qt.CrossCursor)
		self.proj = QgsProject.instance()
		self.labels = []
		self.vertices = []
		self.calculator = QgsDistanceArea()
		self.calculator.setSourceCrs(self.layer.dataProvider().crs(), QgsProject.instance().transformContext())
		self.calculator.setEllipsoid(None) #self.layer.dataProvider().crs().ellipsoidAcronym()
		self.drawingLine = False
		self.movingVertices = False
		self.addingVertices = False
		self.removingVertices = False
		self.movingSegment = False
		self.movingLine = False
		self.showingVertices = False
		self.movingVertex = -1
		self.movingSegm = -1
		self.movingLineInitialPoint = None
		self.lineClosed = False

	def restoreAction(self):
		self.addingVertices = False
		self.removingVertices = False
		self.movingVertices = False
		self.movingSegment = False
		self.movingLine = False
		self.showingVertices = False
		self.drawingLine = True
		self.movingVertex = -1
		self.movingLineInitialPoint = None
		self.deleteVertices()
		self.redrawRubberBand()
		self.redrawTempRubberBand()
		self.canvas.scene().addItem(self.tempRubberBand)
		self.redrawActions()

	def mapCanvasChanged(self):
		self.redrawAreas()
		if self.showingVertices:
			self.redrawVertices()

	def canvasMoveEvent(self, event):
		snapMatch = self.snapper.snapToMap(event.pos())
		self.snapIndicator.setMatch(snapMatch)

		if self.drawingLine and not self.lineClosed:
			if self.tempRubberBand is not None and self.capturing:
				if snapMatch.type():
					mapPoint = snapMatch.point()
				else:
					mapPoint = self.toMapCoordinates(event.pos())
				
				self.tempRubberBand.movePoint(mapPoint)
				self.redrawAreas(event.pos())

		if self.movingVertices and self.movingVertex >= 0:
			if snapMatch.type():
				layerPoint = snapMatch.point()
			else:
				layerPoint = self.toLayerCoordinates(self.layer, event.pos())
			
			self.capturedPoints[self.movingVertex] = layerPoint

			if self.lineClosed and self.movingVertex == 0:
				self.capturedPoints[len(self.capturedPoints) - 1] = layerPoint

			self.redrawRubberBand()
			self.redrawVertices()
			self.redrawAreas()

		if self.movingSegment and self.movingSegm >= 0:
			print('movingSegment')
			currentPoint = self.toLayerCoordinates(self.layer, event.pos())
			distance = self.distancePoint(currentPoint, self.movingLineInitialPoint)
			bearing = self.movingLineInitialPoint.azimuth(currentPoint)

			self.capturedPoints[self.movingSegm] = self.projectPoint(self.capturedPoints[self.movingSegm], distance, bearing)
			self.capturedPoints[self.movingSegm + 1] = self.projectPoint(self.capturedPoints[self.movingSegm + 1], distance, bearing)

			if self.lineClosed:
				if self.movingSegm == 0:
					self.capturedPoints[len(self.capturedPoints) - 1] = self.projectPoint(self.capturedPoints[len(self.capturedPoints) - 1], distance, bearing)
				elif self.movingSegm == len(self.capturedPoints) - 2:
					self.capturedPoints[0] = self.projectPoint(self.capturedPoints[0], distance, bearing)

			self.redrawRubberBand()
			self.redrawVertices()
			self.redrawAreas()
			self.movingLineInitialPoint = currentPoint

		if self.movingLine and self.movingLineInitialPoint != None:
			currentPoint = self.toLayerCoordinates(self.layer, event.pos())
			distance = self.distancePoint(currentPoint, self.movingLineInitialPoint)
			bearing = self.movingLineInitialPoint.azimuth(currentPoint)
			for i in range(len(self.capturedPoints)):
				self.capturedPoints[i] = self.projectPoint(self.capturedPoints[i], distance, bearing)
			self.redrawRubberBand()
			self.redrawAreas()
			self.movingLineInitialPoint = currentPoint

	def projectPoint(self, point, distance, bearing):
		rads = bearing * pi / 180.0
		dx = distance * sin(rads)
		dy = distance * cos(rads)
		return QgsPointXY(point.x() + dx, point.y() + dy)
 	
	def redrawAreas(self, mousePos=None):
		self.deleteLabels()

		if self.capturing and len(self.capturedPoints) > 0:
			for i in range(len(self.selectedFeatures)):
				geometry = QgsGeometry(self.selectedFeatures[i].geometry())
				movingPoints = list(self.capturedPoints)
				
				if mousePos != None:
					movingPoints.append(self.toLayerCoordinates(self.layer, mousePos))

				result, newGeometries, topoTestPoints = geometry.splitGeometry(movingPoints, self.proj.topologicalEditing())

				self.addLabel(geometry)
				if newGeometries != None and len(newGeometries) > 0:
					for i in range(len(newGeometries)):
						self.addLabel(newGeometries[i])

	def addLabel(self, geometry):
		
		area = self.calculator.measureArea(geometry)* 0.000247105381
		labelPoint = geometry.pointOnSurface().vertexAt(0)
		label = QGraphicsTextItem("%.2f" % round(area,2))
		label.setHtml("<div style=\"color:#ffffff;background:#111111;padding:5px\">"
			+ "%.2f" % round(area,2) + " ac"
			
			 "</div>")
		point = self.toMapCoordinatesV2(self.layer, labelPoint)
		label.setPos(self.toCanvasCoordinates(QgsPointXY(point.x(), point.y())))

		self.scene.addItem(label)
		self.labels.append(label)

	def deleteLabels(self):
		for i in range(len(self.labels)):
			self.scene.removeItem(self.labels[i])
		self.labels = []

	def canvasPressEvent(self, event):
		snapMatch = self.snapIndicator.match()
		print('canvaspsadsressevent')
		if self.movingVertices:
			print('movingvertices')
			snapMatch = self.snapIndicator.match()
			for i in range(len(self.capturedPoints)):
				
				if snapMatch.type():
					point = snapMatch.point()
				else:
					point = self.toMapCoordinates(self.layer, self.capturedPoints[i])
				currentVertex = self.toCanvasCoordinates(QgsPointXY(point.x(), point.y()))
				if self.distancePoint(event.pos(), currentVertex) <= maxDistanceHitTest:
						self.movingVertex = i
						break

		if self.movingSegment:
			
			for i in range(len(self.capturedPoints) - 1):
				vertex1 = self.toMapCoordinates(self.layer, self.capturedPoints[i])
				currentVertex1 = self.toCanvasCoordinates(QgsPointXY(vertex1.x(), vertex1.y()))
				vertex2 = self.toMapCoordinates(self.layer, self.capturedPoints[i + 1])
				currentVertex2 = self.toCanvasCoordinates(QgsPointXY(vertex2.x(), vertex2.y()))
				if self.distancePointLine(event.pos().x(), event.pos().y(), currentVertex1.x(), currentVertex1.y(), currentVertex2.x(), currentVertex2.y()) <= maxDistanceHitTest:
					self.movingSegm = i
					break

		self.movingLineInitialPoint = self.toLayerCoordinates(self.layer, event.pos())

	def distancePoint(self, eventPos, vertexPos):
		return sqrt((eventPos.x() - vertexPos.x())**2 + (eventPos.y() - vertexPos.y())**2)

	def canvasReleaseEvent(self, event):
		print("canvas relase event")
		if self.movingVertices or self.movingSegment or self.movingLine:
			if event.button() == Qt.RightButton:
				self.finishOperation()
		elif self.addingVertices:
			if event.button() == Qt.LeftButton:
				self.addVertex(event.pos())
			elif event.button() == Qt.RightButton:
				self.finishOperation()
		elif self.removingVertices:
			if event.button() == Qt.LeftButton:
				self.removeVertex(event.pos())
			elif event.button() == Qt.RightButton:
				self.finishOperation()
		else:
			if event.button() == Qt.LeftButton:
				if not self.lineClosed:
					if not self.capturing:
						self.startCapturing()
					self.addEndingVertex(event.pos())
			elif event.button() == Qt.RightButton:
				self.finishOperation()

		self.movingVertex = -1
		self.movingSegm = -1
		self.movingLineInitialPoint = None
		self.redrawActions()

	def keyReleaseEvent(self, event):
		if event.key() == Qt.Key_Escape:
			self.stopCapturing()
		if event.key() == Qt.Key_Backspace or event.key() == Qt.Key_Delete:
			self.removeLastVertex()
		if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
			self.finishOperation()

		event.accept()
		self.redrawActions()

	def finishOperation(self):
		self.doSplit()
		self.stopCapturing()
		self.initialize()
		self.startCapturing()

	def doSplit(self):
		if self.capturedPoints != None:
			self.layer.splitFeatures(self.capturedPoints, self.proj.topologicalEditing())

	def startCapturing(self):
		self.prepareRubberBand()
		self.prepareTempRubberBand()

		self.drawingLine = True
		self.capturing = True

		self.redrawActions()

	def prepareRubberBand(self):
		color = QColor("red")
		color.setAlphaF(0.78)

		self.rubberBand = QgsRubberBand(self.canvas, QgsWkbTypes.LineGeometry)
		self.rubberBand.setWidth(1)
		self.rubberBand.setColor(color)
		self.rubberBand.show()

	def prepareTempRubberBand(self):
		color = QColor("red")
		color.setAlphaF(0.78)

		self.tempRubberBand = QgsRubberBand(self.canvas, QgsWkbTypes.LineGeometry)
		self.tempRubberBand.setWidth(1)
		self.tempRubberBand.setColor(color)
		self.tempRubberBand.setLineStyle(Qt.DotLine)
		self.tempRubberBand.show()

	def redrawRubberBand(self):
		self.canvas.scene().removeItem(self.rubberBand)
		self.prepareRubberBand()
		for i in range(len(self.capturedPoints)):
			point = self.capturedPoints[i]
			if point.__class__ == QgsPoint:
				vertexCoord = self.toMapCoordinatesV2(self.layer, self.capturedPoints[i])
				vertexCoord = QgsPointXY(vertexCoord.x(), vertexCoord.y())
			else:
				vertexCoord = self.toMapCoordinates(self.layer, self.capturedPoints[i])

			self.rubberBand.addPoint(vertexCoord)

	def redrawTempRubberBand(self):
		if self.tempRubberBand != None:
			self.tempRubberBand.reset(QgsWkbTypes.LineGeometry)
			self.tempRubberBand.addPoint(self.toMapCoordinates(self.layer, self.capturedPoints[len(self.capturedPoints) - 1]))

	def stopCapturing(self):
		self.deleteLabels()
		self.deleteVertices()
		if self.rubberBand:
			self.canvas.scene().removeItem(self.rubberBand)
			self.rubberBand = None
		if self.tempRubberBand:
			self.canvas.scene().removeItem(self.tempRubberBand)
			self.tempRubberBand = None
		self.drawingLine = False
		self.movingVertices = False
		self.showingVertices = False
		self.capturing = False
		self.capturedPoints = []
		self.canvas.refresh()

		self.redrawActions()

	def addEndingVertex(self, canvasPoint):
		snapMatch = self.snapper.snapToMap(canvasPoint)  # Try to snap to the map

		if snapMatch.type():
			mapPoint = snapMatch.point()  # Use the snapped point if available
		else:
			mapPoint = self.toMapCoordinates(canvasPoint)  # Use the cursor position if no snap

		layerPoint = self.toLayerCoordinates(self.layer, mapPoint)

		self.rubberBand.addPoint(mapPoint)
		self.capturedPoints.append(layerPoint)

		self.tempRubberBand.reset(QgsWkbTypes.LineGeometry)
		self.tempRubberBand.addPoint(mapPoint)

	def removeLastVertex(self):
		if not self.capturing: return

		rubberBandSize = self.rubberBand.numberOfVertices()
		tempRubberBandSize = self.tempRubberBand.numberOfVertices()
		numPoints = len(self.capturedPoints)

		if rubberBandSize < 1 or numPoints < 1:
			return

		self.rubberBand.removePoint(-1)

		if rubberBandSize > 1:
			if tempRubberBandSize > 1:
				point = self.rubberBand.getPoint(0, rubberBandSize-2)
				self.tempRubberBand.movePoint(tempRubberBandSize-2, point)
		else:
			self.tempRubberBand.reset(self.bandType())

		del self.capturedPoints[-1]

	def addVertex(self, pos):
		print('addvertex')
		newCapturedPoints = []
		for i in range(len(self.capturedPoints) - 1):
			newCapturedPoints.append(self.capturedPoints[i])
			vertex1 = self.toMapCoordinates(self.layer, self.capturedPoints[i])
			currentVertex1 = self.toCanvasCoordinates(QgsPointXY(vertex1.x(), vertex1.y()))
			vertex2 = self.toMapCoordinates(self.layer, self.capturedPoints[i + 1])
			currentVertex2 = self.toCanvasCoordinates(QgsPointXY(vertex2.x(), vertex2.y()))

			distance = self.distancePointLine(pos.x(), pos.y(), currentVertex1.x(), currentVertex1.y(), currentVertex2.x(), currentVertex2.y())
			if distance <= maxDistanceHitTest:
				layerPoint = self.toLayerCoordinates(self.layer, pos)
				newCapturedPoints.append(layerPoint)

		newCapturedPoints.append(self.capturedPoints[len(self.capturedPoints) - 1])
		self.capturedPoints = newCapturedPoints

		self.redrawRubberBand()
		self.redrawVertices()
		self.redrawAreas()
		self.redrawActions()

	def removeVertex(self, pos):
		deletedFirst = False
		deletedLast = False
		newCapturedPoints = []
		for i in range(len(self.capturedPoints)):
			vertex = self.toMapCoordinates(self.layer, self.capturedPoints[i])
			currentVertex = self.toCanvasCoordinates(QgsPointXY(vertex.x(), vertex.y()))
			if not self.distancePoint(pos, currentVertex) <= maxDistanceHitTest:
				newCapturedPoints.append(self.capturedPoints[i])
			elif i == 0:
				deletedFirst = True
			elif i == len(self.capturedPoints) - 1:
				deletedLast = True

		self.capturedPoints = newCapturedPoints

		if deletedFirst and deletedLast:
			self.lineClosed = False

		self.redrawRubberBand()
		self.redrawVertices()
		self.redrawAreas()
		self.redrawActions()

		if len(self.capturedPoints) <=2:
			self.stopRemovingVertices()

	def startMovingVertices(self):
		self.stopMovingLine()
		self.stopAddingVertices()
		self.stopRemovingVertices()
		self.stopMovingSegment()

		self.actionMoveVertices.setChecked(True)
		self.movingVertices = True
		self.showingVertices = True
		self.drawingLine = False
		self.canvas.scene().removeItem(self.tempRubberBand)
		self.redrawVertices()
		self.redrawAreas()
		self.redrawActions()

	def stopMovingVertices(self):
		self.movingVertices = False
		self.actionMoveVertices.setChecked(False)
		self.restoreAction()

	def startAddingVertices(self):
		self.stopMovingVertices()
		self.stopRemovingVertices()
		self.stopMovingLine()
		self.stopMovingSegment()

		self.actionAddVertices.setChecked(True)
		self.addingVertices = True
		self.showingVertices = True
		self.drawingLine = False
		self.canvas.scene().removeItem(self.tempRubberBand)
		self.redrawVertices()
		self.redrawAreas()
		self.redrawActions()

	def stopAddingVertices(self):
		self.addVertices = False
		self.actionAddVertices.setChecked(False)
		self.restoreAction()

	def startRemovingVertices(self):
		self.stopMovingVertices()
		self.stopAddingVertices()
		self.stopMovingLine()
		self.stopMovingSegment()

		self.actionRemoveVertices.setChecked(True)
		self.removingVertices = True
		self.showingVertices = True
		self.drawingLine = False
		self.canvas.scene().removeItem(self.tempRubberBand)
		self.redrawVertices()
		self.redrawAreas()
		self.redrawActions()

	def stopRemovingVertices(self):
		self.removingVertices = False
		self.actionRemoveVertices.setChecked(False)
		self.restoreAction()

	def startMovingSegment(self):
		self.stopMovingVertices()
		self.stopMovingLine()
		self.stopAddingVertices()
		self.stopRemovingVertices()

		self.actionMoveSegment.setChecked(True)
		self.movingSegment = True
		self.showingVertices = False
		self.drawingLine = False
		self.canvas.scene().removeItem(self.tempRubberBand)
		self.redrawVertices()
		self.redrawAreas()
		self.redrawActions()

	def stopMovingSegment(self):
		self.movingSegment = False
		self.actionMoveSegment.setChecked(False)
		self.restoreAction()

	def startMovingLine(self):
		self.stopMovingVertices()
		self.stopAddingVertices()
		self.stopRemovingVertices()
		self.stopMovingSegment()

		self.actionMoveLine.setChecked(True)
		self.movingLine = True
		self.showingVertices = False
		self.drawingLine = False
		self.canvas.scene().removeItem(self.tempRubberBand)
		self.redrawAreas()
		self.redrawActions()

	def stopMovingLine(self):
		self.actionMoveLine.setChecked(False)
		self.restoreAction()

	def lineClose(self):
		self.lineClosed = True
		self.capturedPoints.append(self.capturedPoints[0])
		self.redrawRubberBand()
		self.redrawTempRubberBand()
		self.redrawAreas()
		self.redrawActions()

	def lineOpen(self):
		self.lineClosed = False
		del self.capturedPoints[-1]
		self.redrawRubberBand()
		self.redrawTempRubberBand()
		self.redrawAreas()
		self.redrawActions()

	def showVertices(self):
		for i in range(len(self.capturedPoints)):
			vertexc = self.toMapCoordinates(self.layer, self.capturedPoints[i])
			vertexCoords = self.toCanvasCoordinates(QgsPointXY(vertexc.x(), vertexc.y()))
			if i == self.movingVertex:
				vertex = self.scene.addRect(vertexCoords.x() - 5, vertexCoords.y() - 5, 10, 10, QPen(QColor("green")), QBrush(QColor("green")))
				self.vertices.append(vertex)
			elif i == len(self.capturedPoints) - 1 and self.movingVertex == 0 and self.lineClosed:
				vertex = self.scene.addRect(vertexCoords.x() - 5, vertexCoords.y() - 5, 10, 10, QPen(QColor("green")), QBrush(QColor("green")))
				self.vertices.append(vertex)
			else:
				vertex = self.scene.addRect(vertexCoords.x() - 4, vertexCoords.y() - 4, 8, 8, QPen(QColor("red")), QBrush(QColor("red")))
				self.vertices.append(vertex)

	def deleteVertices(self):
		for i in range(len(self.vertices)):
			self.scene.removeItem(self.vertices[i])
		self.vertices = []

	def lineMagnitude(self, x1, y1, x2, y2):
		return sqrt(pow((x2 - x1), 2) + pow((y2 - y1), 2))

	def distancePointLine(self, px, py, x1, y1, x2, y2):
		magnitude = self.lineMagnitude(x1, y1, x2, y2)
	
		if magnitude < 0.00000001:
			distance = 9999
			return distance

		u1 = (((px - x1) * (x2 - x1)) + ((py - y1) * (y2 - y1)))
		u = u1 / (magnitude * magnitude)

		if (u < 0.00001) or (u > 1):
			ix = self.lineMagnitude(px, py, x1, y1)
			iy = self.lineMagnitude(px, py, x2, y2)
			if ix > iy:
				distance = iy
			else:
				distance = ix
		else:
			ix = x1 + u * (x2 - x1)
			iy = y1 + u * (y2 - y1)
			distance = self.lineMagnitude(px, py, ix, iy)
	
		return distance

	def redrawVertices(self):
		self.deleteVertices()
		self.showVertices()

	def redrawActions(self):
		self.redrawActionMoveVertices()
		self.redrawActionAddVertices()
		self.redrawActionRemoveVertices()
		self.redrawActionMoveSegment()
		self.redrawActionLineClose()
		self.redrawActionLineOpen()
		self.redrawActionMoveLine()

	def redrawActionMoveVertices(self):
		self.actionMoveVertices.setEnabled(False)
		if len(self.capturedPoints) > 0:
			self.actionMoveVertices.setEnabled(True)

	def redrawActionAddVertices(self):
		self.actionAddVertices.setEnabled(False)
		if len(self.capturedPoints) >=2:
			self.actionAddVertices.setEnabled(True)

	def redrawActionRemoveVertices(self):
		self.actionRemoveVertices.setEnabled(False)
		if len(self.capturedPoints) > 2:
			self.actionRemoveVertices.setEnabled(True)

	def redrawActionMoveSegment(self):
		self.actionMoveSegment.setEnabled(False)
		if len(self.capturedPoints) > 2:
			self.actionMoveSegment.setEnabled(True)

	def redrawActionLineClose(self):
		self.actionLineClose.setEnabled(False)
		if not self.lineClosed and len(self.capturedPoints) >= 3:
			self.actionLineClose.setEnabled(True)

	def redrawActionLineOpen(self):
		self.actionLineOpen.setEnabled(False)
		if self.lineClosed:
			self.actionLineOpen.setEnabled(True)

	def redrawActionMoveLine(self):
		self.actionMoveLine.setEnabled(False)
		if len(self.capturedPoints) > 0:
			self.actionMoveLine.setEnabled(True)
