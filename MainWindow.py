from PySide6.QtWidgets import (
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QLineEdit,
    QLabel,
    QPushButton,
    QCheckBox,
    QTextEdit
)

from PySide6.QtCore import (
    Qt
)

from PySide6.QtGui import (
    QTextOption
)

from pathlib import Path
import requests
import json
import keyring
import csv

from ItemSlot import ItemSlot

class MainWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.baseURL = "https://api.warframe.market/v1"
        self.signedIn = False
        self.setWindowTitle("Warframe Stonks")

        mainLayout = QHBoxLayout()
        #mainLayout.setContentsMargins(10,10,10,10)
        leftLayout = QVBoxLayout()
        rightLayout = QVBoxLayout()

        #####Left Layout#####
        mainLayout.addLayout(leftLayout, 50)
        leftLayout.setAlignment(Qt.AlignmentFlag.AlignTop)

        #READ MEMORY FOR SAVED USER DATA
        remUser = False if keyring.get_credential("R1C3WF", "RemUser") == None else bool(keyring.get_credential("R1C3WF", "RemUser").password)
        remPass = False if keyring.get_credential("R1C3WF", "RemPass") == None else bool(keyring.get_credential("R1C3WF", "RemPass").password)
        hideUser = False if keyring.get_credential("R1C3WF", "HideUser") == None else keyring.get_credential("R1C3WF", "HideUser").password=="True"

        #Username
        layoutUsername = QHBoxLayout()
        labelUsername = QLabel("Email:")
        layoutUsername.addWidget(labelUsername, 20)
        self.inputUsername = QLineEdit(keyring.get_credential("R1C3WF", "User").password if remUser else "")
        self.inputUsername.setEchoMode(QLineEdit.Password if hideUser else QLineEdit.Normal)
        layoutUsername.addWidget(self.inputUsername, 80)
        leftLayout.addLayout(layoutUsername)

        #Password
        layoutPassword = QHBoxLayout()
        labelPassword = QLabel("Password:")
        layoutPassword.addWidget(labelPassword, 20)
        self.inputPassword = QLineEdit(keyring.get_credential("R1C3WF", "Pass").password if remPass else "")
        self.inputPassword.setEchoMode(QLineEdit.Password)
        layoutPassword.addWidget(self.inputPassword, 80)
        leftLayout.addLayout(layoutPassword)

        #remember
        layoutRemember = QHBoxLayout()

        layoutRememberUser = QVBoxLayout()
        self.checkBoxUser = QCheckBox("Remember User")
        self.checkBoxUser.clicked.connect(self.RememberUserClicked)
        self.checkBoxUser.setChecked(remUser)
        layoutRememberUser.addWidget(self.checkBoxUser)

        self.checkBoxHideUser = QCheckBox("Hide User")
        self.checkBoxHideUser.clicked.connect(self.RememberHideUserClicked)
        self.checkBoxHideUser.setChecked(hideUser)
        layoutRememberUser.addWidget(self.checkBoxHideUser)

        layoutRemember.addLayout(layoutRememberUser)

        layoutRememberPass = QVBoxLayout()
        self.checkBoxPass = QCheckBox("Remember Password")
        self.checkBoxPass.clicked.connect(self.RememberPassClicked)
        self.checkBoxPass.setChecked(remPass)
        layoutRememberPass.addWidget(self.checkBoxPass)

        self.checkboxAutoSignIn = QCheckBox("Auto Sign In")
        layoutRememberPass.addWidget(self.checkboxAutoSignIn)
        #TODO: implement auto sign in

        layoutRemember.addLayout(layoutRememberPass)

        leftLayout.addLayout(layoutRemember)

        #Login
        self.pushButtonSignIn = QPushButton("Sign In")
        self.pushButtonSignIn.pressed.connect(self.FunctionSignIn)
        leftLayout.addWidget(self.pushButtonSignIn)

        #Items To List
        labelItemsToCheck = QLabel("Items To Check")
        leftLayout.addWidget(labelItemsToCheck)

        self.textBoxSell = QTextEdit(self)
        self.textBoxSell.setWordWrapMode(QTextOption.NoWrap)
        self.textBoxSell.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        leftLayout.addWidget(self.textBoxSell)

        fileItemsTocheck = Path("ItemsToCheck.txt")
        if fileItemsTocheck.is_file():
            with open(fileItemsTocheck, 'r') as f:
                self.textBoxSell.append(f.read())

        #Check Item Prices
        pushButtonCheckPrices = QPushButton("Get Prices")
        pushButtonCheckPrices.clicked.connect(self.GetItemPrices)
        leftLayout.addWidget(pushButtonCheckPrices)

        #####Right Layout#####
        mainLayout.addLayout(rightLayout, 50)

        self.textBox = QTextEdit(self)
        self.textBox.setWordWrapMode(QTextOption.NoWrap)
        self.textBox.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        #self.textBox.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        rightLayout.addWidget(self.textBox)

        rightLayout.addWidget(ItemSlot())

        #Create Central Widget
        mainWidget = QWidget()
        mainWidget.setLayout(mainLayout)
        self.setCentralWidget(mainWidget)

    def FunctionSignIn(self):
        #CHECK SAVE USERDATA
        userStr = ""
        passStr = ""
        if self.checkBoxUser.isChecked() == True:
            keyring.set_password("R1C3WF", "RemUser", "True")
            userStr = self.inputUsername.text()

        if self.checkBoxPass.isChecked() == True:
            keyring.set_password("R1C3WF", "RemPass", "True")
            passStr = self.inputPassword.text()

        if self.checkBoxUser.isChecked() or self.checkBoxPass.isChecked():
            keyring.set_password("R1C3WF", "User", userStr)
            keyring.set_password("R1C3WF", "Pass", passStr)

        print("===== Sign In =====")
        self.pushButtonSignIn.setEnabled(False)
        cookie = requests.get(self.baseURL).cookies["JWT"]
        print("Cookie grabbed!", cookie, "\n")

        signInJson = {
            "auth_type": "cookie",
            "email": self.inputUsername.text(),
            "password": self.inputPassword.text(),
            "device_id": ""
        }

        signInHeaders = {"Authorization": cookie}

        print("Attempting to sign in...\n  username:", self.inputUsername.text(), "\n  password:", self.inputPassword.displayText())

        requestSignIn = requests.post(
            url=self.baseURL+"/auth/signin",
            json=signInJson,
            headers=signInHeaders)
        
        print("Status code:", requestSignIn.status_code)
        print("Reason:", requestSignIn.reason)
        print("Signed In Successfully!" if requestSignIn.ok == True else "FAILED TO SIGN IN!")

        if requestSignIn.ok == False:
            self.pushButtonSignIn.setEnabled(True)
            return
        
        self.requestAllItems = requests.get(self.baseURL+"/items")
        self.signedIn = True

    def GetItemPrices(self):
        if self.signedIn == False:
            print("Not Signed In!")
            return

        with open("ItemsToCheck.txt", 'w') as f:
            f.write(self.textBoxSell.toPlainText())

        listItemsToCheck = self.textBoxSell.toPlainText().split("\n")

        self.csvExportItems = []

        for item in listItemsToCheck:
            if item == "":
                continue

            itemOrderData = requests.get(self.baseURL+"/items/"+item+"/orders")

            filteredOrdersSell = [value for value in itemOrderData.json()["payload"]["orders"] if value["order_type"] == "sell"]
            filteredOrdersInGame = [value for value in filteredOrdersSell if value["user"]["status"] == "ingame"]

            platinumPrices = [listItem["platinum"] for listItem in filteredOrdersInGame]
            platinumPrices.sort()
            
            lowest = platinumPrices[0]
            highest = platinumPrices[-1]
            average = sum(platinumPrices)/len(platinumPrices)

            stringOutput = "\n    Lowest: "+str(lowest)+"\n    Highest: "+str(highest)+"\n    Average: "+str(round(average, 2))

            self.textBox.append(item+stringOutput+"\n")
            print(item,stringOutput)

            self.csvExportItems.append({"Item":item, "Minimum":lowest, "Maximum":highest, "Average":average})
        
        with open("ItemsToCheck.csv", "w", newline="") as csvfile:
            fieldNames = ["Item", "Minimum", "Maximum", "Average"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldNames)
            
            writer.writeheader()

            for item in self.csvExportItems:
                writer.writerow(item)

    def GenerateItemSlots(self, itemsJson, itemCount):
        print("\n===== Getting all items from warframe market =====")
        requestAllItems = requests.get(self.baseURL+"/items")
        self.GenerateItemSlots(requestAllItems.json(), 5)

        for item in range(itemCount):
            itemData = itemsJson["payload"]["items"][item]
            itemOrderData = requests.get(self.baseURL+"/items/"+itemData["url_name"]+"/orders")

            filteredOrdersSell = [value for value in itemOrderData.json()["payload"]["orders"] if value["order_type"] == "sell"]
            filteredOrdersInGame = [value for value in filteredOrdersSell if value["user"]["status"] == "ingame"]

            platinumPrices = [listItem["platinum"] for listItem in filteredOrdersInGame]
            platinumPrices.sort()
            
            lowest = platinumPrices[0]
            highest = platinumPrices[-1]
            average = sum(platinumPrices)/len(platinumPrices)

            stringOutput = "\n    Lowest: "+str(lowest)+"\n    Highest: "+str(highest)+"\n    Average: "+str(round(average, 2))

            self.textBox.append(itemData["url_name"]+stringOutput+"\n")
            print(itemData["url_name"],stringOutput)

    def RememberUserClicked(self):
        if self.checkBoxUser.isChecked() == False:
            keyring.set_password("R1C3WF", "User", "")
            keyring.set_password("R1C3WF", "RemUser", "")

    def RememberPassClicked(self):
        if self.checkBoxPass.isChecked() == False:
            keyring.set_password("R1C3WF", "Pass", "")
            keyring.set_password("R1C3WF", "RemPass", "")

    def RememberHideUserClicked(self):
        keyring.set_password("R1C3WF", "HideUser", self.checkBoxHideUser.isChecked())
        self.inputUsername.setEchoMode(QLineEdit.Password if self.checkBoxHideUser.isChecked() else QLineEdit.Normal)
