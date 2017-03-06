# 2017 - Antonio Carlon

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import resources
import threading
import qgis.utils

from qgis.core import *
from qgis.gui import *

class SplitPolygonShowingAreasPlugin:
	mapTool = None
	
	def __init__(self, iface):
		self.iface = iface

	def initGui(self):
		icon = QIcon(":/plugins/SplitPolygonShowingAreas/icon.png")
		self.action = QAction(icon, "Split Polygon Showing Areas", self.iface.mainWindow())
		self.action.setCheckable(True)
		QObject.connect(self.action, SIGNAL("triggered()"), self.onClick)

		self.iface.addPluginToMenu("Split Polygon Showing Areas", self.action)
		self.iface.addToolBarIcon(self.action)
		self.iface.currentLayerChanged.connect(self.currentLayerChanged)
		
		self.help_action = QAction("Help", self.iface.mainWindow())
		QObject.connect(self.help_action, SIGNAL("triggered()"), self.onHelp)
		self.iface.addPluginToMenu("Split Polygon Showing Areas", self.help_action)

		self.enableTool()

	def unload(self):
		self.iface.removePluginMenu("Split Polygon Showing Areas", self.action)
		self.iface.removePluginMenu("Split Polygon Showing Areas", self.help_action)
		self.iface.removeToolBarIcon(self.action)

	def onHelp(self):
		qgis.utils.showPluginHelp(filename="index")

	def onClick(self):
		if not self.action.isChecked():
			self.iface.mapCanvas().unsetMapTool(self.mapTool)
			self.mapTool = None
			return
		layer = self.iface.activeLayer()
		if layer == None or not isinstance(layer, QgsVectorLayer) or (layer.wkbType() != QGis.WKBPolygon and layer.wkbType() != QGis.WKBMultiPolygon):
			self.iface.messageBar().pushMessage("No Polygon Vectorial Layer Selected", "Select a Polygon Vectorial Layer first", level=QgsMessageBar.WARNING)
			self.action.setChecked(False)
			return
		selectedFeatures = layer.selectedFeatures()
		if selectedFeatures == None or len(selectedFeatures) == 0:
			self.iface.messageBar().pushMessage("No Features Selected", "Select some features first", level=QgsMessageBar.WARNING)
			self.action.setChecked(False)
			return

		self.action.setChecked(True)
		self.mapTool = SplitMapTool(self.iface.mapCanvas(), layer, selectedFeatures)
		self.mapTool.setAction(self.action)
		self.iface.mapCanvas().setMapTool(self.mapTool)

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

			if isinstance(layer, QgsVectorLayer):
				layer.editingStarted.connect(self.layerEditingChanged)
				layer.editingStopped.connect(self.layerEditingChanged)
			
		self.enableTool()		

	def layerEditingChanged(self):
		self.enableTool()	

	def enableTool(self):
		self.action.setEnabled(False)
		layer = self.iface.activeLayer()
		
		if layer != None and isinstance(layer, QgsVectorLayer):
			selectedFeatures = layer.selectedFeatures()
			if isinstance(layer, QgsVectorLayer) and (layer.wkbType() == QGis.WKBPolygon or layer.wkbType() == QGis.WKBMultiPolygon) and selectedFeatures != None and len(selectedFeatures) >= 0 and layer.isEditable():
				self.action.setEnabled(True)

class SplitMapTool(QgsMapToolEdit):
	def __init__(self, canvas, layer, selectedFeatures):
		super(SplitMapTool, self).__init__(canvas)
		self.canvas = canvas
		self.layer = layer
		self.layer.editingStopped.connect(self.stopCapturing)
		self.selectedFeatures = selectedFeatures
		self.rubberBand = None
		self.tempRubberBand = None
		self.capturedPoints = []
		self.capturing = False
		self.setCursor(Qt.CrossCursor)
		self.proj = QgsProject.instance()
		self.scene = canvas.scene()
		self.labels = []
		self.calculator = QgsDistanceArea()
		self.calculator.setSourceCrs(self.layer.dataProvider().crs())
		self.calculator.setEllipsoid(self.layer.dataProvider().crs().ellipsoidAcronym())
		self.calculator.setEllipsoidalMode(self.layer.dataProvider().crs().geographicFlag())

	def canvasMoveEvent(self, event):
		if self.tempRubberBand != None and self.capturing:
			mapPoint = self.toMapCoordinates(event.pos())
			self.tempRubberBand.movePoint(mapPoint)

			self.deleteLabels()

			for i in range(len(self.selectedFeatures)):
				geometry = QgsGeometry(self.selectedFeatures[i].geometry())
				movingPoints = list(self.capturedPoints)
				movingPoints.append(self.toLayerCoordinates(self.layer, event.pos()))
				result, newGeometries, topoTestPoints = geometry.splitGeometry(movingPoints, self.proj.topologicalEditing())

				self.addLabel(geometry)
				if newGeometries != None and len(newGeometries) > 0:
					for i in range(len(newGeometries)):
						self.addLabel(newGeometries[i])

	def addLabel(self, geometry):
		area = self.calculator.measureArea(geometry)
		labelPoint = geometry.pointOnSurface().vertexAt(0)
		label = QGraphicsTextItem("%.2f" % round(area,2))
		label.setHtml("<div style=\"color:#ffffff;background:#111111;padding:5px\"><b>"
			+ "%.2f" % round(area,2) 
			+ "</b> m<sup>2</sup></div>")
		label.setPos(self.toCanvasCoordinates(self.toMapCoordinates(self.layer, labelPoint)))

		self.scene.addItem(label)
		self.labels.append(label)

	def deleteLabels(self):
		for i in range(len(self.labels)):
			self.scene.removeItem(self.labels[i])

	def canvasReleaseEvent(self, event):
		if event.button() == Qt.LeftButton:
			if not self.capturing:
				self.startCapturing()
			self.addVertex(event.pos())
		elif event.button() == Qt.RightButton:
			self.doSplit()
			self.stopCapturing()

	def keyReleaseEvent(self, event):
		if event.key() == Qt.Key_Escape:
			self.stopCapturing()
		if event.key() == Qt.Key_Backspace or event.key() == Qt.Key_Delete:
			self.removeLastVertex()
			event.ignore()
		if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
			self.stopCapturing()
			self.doSplit()

	def doSplit(self):
		if self.capturedPoints != None:
			self.layer.splitFeatures(self.capturedPoints, self.proj.topologicalEditing())

	def startCapturing(self):
		self.prepareRubberBand()
		self.prepareTempRubberBand()

		self.capturing = True

	def prepareRubberBand(self):
		color = QColor("red")
		color.setAlphaF(0.78)

		self.rubberBand = QgsRubberBand(self.canvas, QGis.Line)
		self.rubberBand.setWidth(1)
		self.rubberBand.setColor(color)
		self.rubberBand.show()

	def prepareTempRubberBand(self):
		color = QColor("red")
		color.setAlphaF(0.78)

		self.tempRubberBand = QgsRubberBand(self.canvas, QGis.Line)
		self.tempRubberBand.setWidth(1)
		self.tempRubberBand.setColor(color)
		self.tempRubberBand.setLineStyle(Qt.DotLine)
		self.tempRubberBand.show()

	def stopCapturing(self):
		self.deleteLabels()
		if self.rubberBand:
			self.canvas.scene().removeItem(self.rubberBand)
			self.rubberBand = None
		if self.tempRubberBand:
			self.canvas.scene().removeItem(self.tempRubberBand)
			self.tempRubberBand = None
		self.capturing = False
		self.capturedPoints = []
		self.canvas.refresh()

	def addVertex(self, canvasPoint):
		mapPoint = self.toMapCoordinates(canvasPoint)
		layerPoint = self.toLayerCoordinates(self.layer, canvasPoint)

		self.rubberBand.addPoint(mapPoint)
		self.capturedPoints.append(layerPoint)

		self.tempRubberBand.reset(QGis.Line)
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