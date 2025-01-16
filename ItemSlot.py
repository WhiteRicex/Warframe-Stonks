from PySide6.QtWidgets import (
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QTextEdit,
    QLineEdit,
    QLabel,
    QPushButton
)

import requests
import json

class ItemSlot(QWidget):
    def __init__(self):
        super().__init__()
        mainLayout = QHBoxLayout()

        exportData = QPushButton("export all data")
        exportData.clicked.connect(self.ExportData)
        mainLayout.addWidget(exportData)

        mainLayout.setContentsMargins(0,0,0,0)
        self.setLayout(mainLayout)

    def ExportData(self):
        allItems = requests.get("https://api.warframe.market/v1/items")

        with open("AllItemsExport.json", 'w') as file:
            file.write(json.dumps(allItems.json()))