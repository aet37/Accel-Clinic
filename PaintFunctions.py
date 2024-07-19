import sys
import os
import csv
from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel
from PyQt5.QtGui import QPainter, QPen, QPixmap, QImage
from PyQt5.QtCore import Qt, QPoint, QSize
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from datetime import datetime

class DrawingArea(QLabel):
	def __init__(self, image_path, parent=None, ):
		super(DrawingArea, self).__init__(parent)
		self.setAttribute(QtCore.Qt.WA_StaticContents)
		self.setAttribute(Qt.WA_OpaquePaintEvent)
		self.modified = False
		self.drawing = False
		self.myPenWidth = 4
		self.myPenColor = Qt.blue
		self.imagePath = image_path

		self.image = QPixmap(self.size())
		self.image.fill(Qt.white)
		self.setPixmap(self.image)  # Set the pixmap for the QLabel
		self.backgroundImage = QPixmap()

		self.lastPoint = QPoint()
		self.drawn_points = []  # To store the time and coordinates of drawn points

	def resizeEvent(self, event):
		if self.width() > self.image.width() or self.height() > self.image.height():
			new_image = QPixmap(self.size())
			new_image.fill(Qt.white)
			painter = QPainter(new_image)
			painter.drawPixmap(0, 0, self.image)
			self.image = new_image
			self.setPixmap(self.image)
		super().resizeEvent(event)

	def setImage(self):
		self.image = QPixmap(self.imagePath)
		self.image = self.image.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
		self.update()

	def mousePressEvent(self, event):
		if event.button() == Qt.LeftButton:
			self.lastPoint = event.pos()
			self.drawing = True

	def mouseMoveEvent(self, event):
		if (event.buttons() & Qt.LeftButton) & self.drawing:
			currentPoint = event.pos()
			currentTime = datetime.now()
			self.drawn_points.append((currentTime, currentPoint.x(), currentPoint.y()))

			painter = QPainter(self.image)
			pen = QPen(self.myPenColor, self.myPenWidth, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
			painter.setPen(pen)
			painter.drawLine(self.lastPoint, currentPoint)
			self.lastPoint = currentPoint
			self.update()
			#self.repaint()

	def mouseReleaseEvent(self, event):
		if event.button() == Qt.LeftButton and self.drawing:
			currentPoint = event.pos()
			currentTime = datetime.now()
			self.drawn_points.append((currentTime, currentPoint.x(), currentPoint.y()))

			painter = QPainter(self.image)
			pen = QPen(self.myPenColor, self.myPenWidth, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
			painter.setPen(pen)
			painter.drawLine(self.lastPoint, currentPoint)
			self.drawing = False
			self.update()
			#self.repaint()

	def paintEvent(self, event):
		QLabel.paintEvent(self, event)
		painter = QPainter(self)
		painter.drawPixmap(0, 0, self.image)

	def clearDrawing(self):
		self.image.fill(Qt.white)
		#painter = QPainter(self.image)
		#self.setPixmap(self.image)  # Set the pixmap for the QLabel
		#self.backgroundImage = QPixmap()
		self.setImage()
		#offset_x = (self.width() - self.background_image.width()) // 2
		#offset_y = (self.height() - self.background_image.height()) // 2
		offset_x = 0
		offset_y = 0
		#painter.drawImage(offset_x, offset_y, self.background_image)
		#painter.end()

		self.drawn_points = []
		#self.resizeWin()
		self.update()

	def saveDrawing(self, file_path):
		with open(file_path, 'w', newline='') as file:
			writer = csv.writer(file)
			writer.writerow(['Time', 'X', 'Y'])
			for point in self.drawn_points:
				writer.writerow([point[0].strftime("%Y-%m-%d %H:%M:%S.%f"), point[1], point[2]])

	def loadDrawing(self, file_path):
		self.clearDrawing()
		try:
			with open(file_path, 'r') as file:
				reader = csv.reader(file)
				next(reader)  # Skip header
				self.drawn_points = []
				previousPoint = None
				for row in reader:
					time_str, x, y = row
					point = QPoint(int(x), int(y))
					currentTime = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S.%f")
					self.drawn_points.append((currentTime, point.x(), point.y()))

					if previousPoint is not None:
						painter = QPainter(self.image)
						pen = QPen(self.myPenColor, self.myPenWidth, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
						painter.setPen(pen)
						painter.drawLine(previousPoint, point)
						painter.end()

					previousPoint = point
			self.update()
		except Exception as e:
			print(f"Error loading drawing: {e}")