# Author : sanjay@notsosecure.com
#
# main.py: Initiator file for the project.
#
# Project : Android Application Analyzer

import sqlite3
import os
from datetime import datetime
import urllib
import html
import webbrowser 
from gui import *
from banner import *
from logcat import *
from GlobalVariables import *
import shutil
import tarfile

class Main:
	def __init__(self, mainWin):
		self.mainWin=mainWin
		self.globalVariables=GlobalVariables()
		self.isSuNeeded = True
		self.device=""
		self.isSplitConfig = False

	def ComposeCmd(self, cmd):
		commandPath=""
		if self.isSuNeeded:
			commandPath="-s {} shell \"su -c {}\"".format(self.device, cmd)
		else:
			commandPath="-s {} shell {}".format(self.device, cmd)
		return commandPath
	
	def GetDeviceList(self):
		deviceList=[]
		isFirstElement=True
		for device in (self.globalVariables.ExecuteCommand("devices -l").strip()).split("\n"):
			try:
				iStart=device.find("model:")
				if iStart != -1:
					iEnd=device.find(" ", iStart)
					deviceList.append((device[iStart: iEnd]).strip())
			except:
				"No device found"
		return deviceList

	def GetApplicationList(self):
		self.isSuNeeded = True
		cmd=self.ComposeCmd("ls '/data/data/'")
		output=self.globalVariables.ExecuteCommand(cmd)
		if output.lower().find("unknown id")==0 or not output:
			self.isSuNeeded = False
		else:
			self.isSuNeeded = True
		cmd=self.ComposeCmd("ls '/data/data/'")
		appList=[]	
		for app in (self.globalVariables.ExecuteCommand(cmd).strip()).split("\n"):
			try:
				appList.append(app.strip())
			except:
				"App not found"
		return appList

	def ListApplication(self, isHide=False):
		self.device=self.mainWin.cmbDevice.currentText()
		appList=self.GetApplicationList()
		self.mainWin.cmbApp.clear()
		for app in appList:
			if isHide:
				if app.find("com.android") == 0 or app.find("com.google") == 0:
					continue
				else:
					self.mainWin.cmbApp.addItem(app)
			else:
				self.mainWin.cmbApp.addItem(app)

	def ApplicationSelectionChanged(self):
		if not self.mainWin.chkLogcat.isChecked():
			self.mainWin.chkLogcat.setChecked(True)

	def GetAllTables(self, dbPath):
		tables=[]
		con = sqlite3.connect(dbPath)
		cursor = con.cursor()
		cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
		for table_name in cursor.fetchall():
			tables.append(table_name[0])
		return tables

	def GetTableData(self, dbPath, tableName):
		rows=[]
		con = sqlite3.connect(dbPath)
		cursor = con.cursor()
		cursor.execute("SELECT * FROM " + tableName)

		colnames = cursor.description
		row=''
		for colname in colnames:
			row+=colname[0] + " | "
		rows.append(row)

		for row in cursor.fetchall():
			rows.append(row)
		return rows

	def HideDefaultApplication(self):
		if mainWin.chkHideDefaultApp.isChecked():
			self.ListApplication(True)
		else:
			self.ListApplication(False)

	def DisplayFileContent(self):
		mainWin.chkLogcat.setChecked(False)
		if len(self.mainWin.lstAppDirFiles.selectedItems()) == 1:
			filePath=(self.mainWin.lstAppDirFiles.selectedItems()[0].text())
			fileContent=self.GetFileContent(filePath).strip()
			if fileContent.find("SQLite format 3") == 0:
				if not os.path.exists("dbs"):
					os.makedirs("dbs")
				fileName=filePath[filePath.rfind('/')+1:]
				dbPath="./dbs/"+fileName
				self.DownloadDBFile(filePath, dbPath)
				tableList=self.GetAllTables(dbPath)
				self.mainWin.txtFileContent.setText("SQLiteDB : "+dbPath)
				for table in tableList:
					self.mainWin.txtFileContent.append("\n\n\nTable => " + table.format(type(str), repr(str)))
					rows=self.GetTableData(dbPath, table)
					isFirstRow=True
					for columns in rows:
						rowData=""
						for column in columns:
							try:
								rowData+=column.format(type(str), repr(str))
								if not isFirstRow:
									rowData+=" | "
							except:
								rowData+=str(column)
								if not isFirstRow:
									rowData+=" | "
						isFirstRow=False
						dataLen = len(rowData)
						if dataLen > 174:
							dataLen = 174
						self.mainWin.txtFileContent.append("-"*dataLen)
						self.mainWin.txtFileContent.append(rowData)
						self.mainWin.txtFileContent.append("-"*dataLen)
			elif fileContent.find("ELF") == 1:
				if not os.path.exists("lib"):
					os.makedirs("lib")
				fileName=filePath[filePath.rfind('/')+1:]
				libPath="./lib/"+fileName
				self.DownloadDBFile(filePath, libPath)
				self.mainWin.txtFileContent.setText("Performed \"strings\" command on : ELF lib :" + libPath + "\n\n")
				self.mainWin.txtFileContent.append(self.globalVariables.ExecuteCommand("strings " + libPath, False))
			else:
				self.mainWin.txtFileContent.setText(fileContent)
				
		else:
			print ("Multiple Item Selected")
		if mainWin.chkHtmlDecode.isChecked():
			text=html.unescape(self.mainWin.txtFileContent.toPlainText())
			self.mainWin.txtFileContent.setText(text)

		if mainWin.chkURLDecode.isChecked():
			text=self.mainWin.txtFileContent.toPlainText()
			text=text.encode('ascii', 'ignore') 
			self.mainWin.txtFileContent.setText(text)

	def ChangeSplitConfigValue(self):
		if mainWin.chkSplitConfig.isChecked():
			self.isSplitConfig = True
		else:
			self.isSplitConfig = False

	def DisplayLogcat(self):
		if mainWin.chkLogcat.isChecked():
			mainWin.chkURLDecode.setVisible(False)
			mainWin.chkHtmlDecode.setVisible(False)
			mainWin.txtFileContent.setVisible(False)
			mainWin.treeView.setVisible(False)
			mainWin.splitter.setVisible(False)
			mainWin.txtLogcat.setVisible(True)
			mainWin.lblFileContent.setText("Logcat Logs")
		else:
			mainWin.chkHtmlDecode.setVisible(True)
			mainWin.chkURLDecode.setVisible(True)
			mainWin.txtFileContent.setVisible(True)
			mainWin.treeView.setVisible(True)
			mainWin.splitter.setVisible(True)
			mainWin.txtLogcat.setVisible(False)
			self.PullApplicationData()

	def DecodeHTMLEntity(self):
		text=self.mainWin.txtFileContent.toPlainText()
		if mainWin.chkHtmlDecode.isChecked():
			text=html.unescape(text)
			self.mainWin.txtFileContent.setText(text) 
		else:
			self.DisplayFileContent()

	def DecodeURL(self):
		text=self.mainWin.txtFileContent.toPlainText()
		if mainWin.chkURLDecode.isChecked():
			text=text.encode('ascii', 'ignore') 
			self.mainWin.txtFileContent.setText(text)
		else:
			self.DisplayFileContent()

	def GetApplicationPath(self, apkName):
		cmd="{} | {} {}".format(self.ComposeCmd("ls '/data/app/'"), self.globalVariables.isWindowsOS and "findstr" or "grep", apkName)
		appDir=self.globalVariables.ExecuteCommand(cmd).strip()

		if appDir == "":
			cmd=self.ComposeCmd("pm list packages -f | grep {} | cut -d':' -f2".format(apkName))
			appDir=self.globalVariables.ExecuteCommand(cmd).strip()
			appDir = appDir[10:appDir.rfind("/")]
		return appDir

	def FetchAPK(self):
		apkName=self.mainWin.cmbApp.currentText()
		appDir=self.GetApplicationPath(apkName)
		self.globalVariables.ExecuteCommand("-s {} pull /data/app/{}/base.apk {}/{}.apk".format(self.device, appDir, self.globalVariables.outputDir, apkName))
		return apkName
		
	def RunAPKTool(self):
		apkName=self.FetchAPK()
		self.globalVariables.ExecuteCommand("java -jar {} d {}/{}.apk -f -o {}/{}".format(self.globalVariables.apktoolPath, self.globalVariables.outputDir, apkName, self.globalVariables.outputDir, apkName), False)

	def RunJDGUITool(self):
		apkName=self.FetchAPK()
		dex2jarPath = self.globalVariables.isWindowsOS and self.globalVariables.dex2jarPathWin or self.globalVariables.dex2jarPath
		self.globalVariables.ExecuteCommand("{} {}/{}.apk -o {}/{}.jar --force".format(dex2jarPath, self.globalVariables.outputDir, apkName, self.globalVariables.outputDir, apkName), False)
		self.globalVariables.ExecuteCommand("java -jar {} {}/{}.jar".format(self.globalVariables.jdGUIPath, self.globalVariables.outputDir, apkName), False, False)

	def RunMobSFTool(self):
		isSuccess=self.globalVariables.InitializeMobSFVariables()
		if isSuccess:
			apkName=self.FetchAPK()
			self.globalVariables.ExecuteCommand("curl -F 'file=@./apps/{}.apk' {}/api/v1/upload -H \"Authorization:{}\"".format(apkName, self.globalVariables.mobSFURL, self.globalVariables.mobSFAPIKey), False, False)
			webbrowser.open_new_tab("{}/recent_scans/".format(self.globalVariables.mobSFURL))

	def RunReinstallAPK(self):
		apkName=self.mainWin.cmbApp.currentText()
		self.globalVariables.ExecuteCommand("java -jar {} b {}/{}/".format(self.globalVariables.apktoolPath, self.globalVariables.outputDir, apkName), False)
		self.globalVariables.ExecuteCommand("java -jar {} -a {}/{}/dist/{}.apk".format(self.globalVariables.signJar, self.globalVariables.outputDir, apkName, apkName), False)
		
		if(self.isSplitConfig):
			appPath =  self.GetApplicationPath(apkName)
			cmd=self.ComposeCmd("rm '/data/app/{}/base.apk'".format(appPath))
			self.globalVariables.ExecuteCommand(cmd).strip()

			self.globalVariables.ExecuteCommand("-s {} push {}/{}/dist/{}-aligned-debugSigned.apk /data/local/tmp/base.apk".format(self.device, self.globalVariables.outputDir, apkName, apkName, appPath))

			cmd=self.ComposeCmd("mv '/data/local/tmp/base.apk /data/app/{}/base.apk'".format(appPath))
			self.globalVariables.ExecuteCommand(cmd).strip()
		else:
			self.globalVariables.ExecuteCommand("-s {} uninstall {}".format(self.device, apkName))
			self.globalVariables.ExecuteCommand("-s {} install {}/{}/dist/{}-aligned-debugSigned.apk".format(self.device, self.globalVariables.outputDir, apkName, apkName))
	
	def CopyFolderFromAndroidDevice(self, basePath, outputPath):
		apkName=self.mainWin.cmbApp.currentText()

		dirPath = "{}/{}".format(self.globalVariables.appDataDir, apkName)
		subDirPath="{}/{}".format(dirPath, outputPath)
		if os.path.exists(subDirPath):
			if self.mainWin.FolderExistPopup():
				shutil.rmtree(subDirPath)
		else:
			os.makedirs(subDirPath, exist_ok=True)

		output=self.globalVariables.ExecuteCommand(self.ComposeCmd("cp -r '{}' {}".format(basePath, self.globalVariables.androidTmpDir)), True, True, True)

		if "cp: bad" in output:
			return

		self.globalVariables.ExecuteCommand(self.ComposeCmd("tar -cf {}/{}.tar {}/{}".format(self.globalVariables.androidTmpDir, apkName, self.globalVariables.androidTmpDir, apkName)))
		
		self.globalVariables.ExecuteCommand("-s {} pull {}/{}.tar {}".format(self.device, self.globalVariables.androidTmpDir, apkName, dirPath))

		with tarfile.open("{}/{}.tar".format(dirPath, apkName), "r") as tar:
			tar.extractall(dirPath)


		shutil.copytree("{}{}/{}".format(dirPath, self.globalVariables.androidTmpDir, apkName), "{}/{}".format(dirPath, outputPath), dirs_exist_ok=True)

		tmpPath="{}/{}.tar".format(dirPath, apkName)
		if os.path.exists(tmpPath):
			os.remove(tmpPath)

		tmpPath="{}/data".format(dirPath)
		if os.path.exists(tmpPath):
			shutil.rmtree(tmpPath)

		self.globalVariables.ExecuteCommand(self.ComposeCmd("rm -rf  {}/{}*".format(self.globalVariables.androidTmpDir, apkName)))

	def PullApplicationData(self):
		apkName=self.mainWin.cmbApp.currentText()
		self.CopyFolderFromAndroidDevice("/data/data/{}".format(apkName), "data_data")
		self.CopyFolderFromAndroidDevice("/sdcard/Android/data/{}".format(apkName), "sdcard")
		self.mainWin.ShowDirectoryView("{}/{}".format(self.globalVariables.appDataDir, apkName))
		

	def StartFridaServer(self):
		cmd="{} | {} {}".format(self.ComposeCmd("ps"), self.globalVariables.isWindowsOS and "findstr" or "grep", self.globalVariables.fridaServer)
		output = self.globalVariables.ExecuteCommand(cmd)
		if output.find(self.globalVariables.fridaServer) < 0:
			self.globalVariables.ExecuteCommand("-s {} push {} {}".format(self.device, self.globalVariables.fridaServerFileName, self.globalVariables.androidtmpdir))
			self.globalVariables.ExecuteCommand(self.ComposeCmd("\"cd {} && chmod 755 {}\"".format(self.globalVariables.androidtmpdir, self.globalVariables.fridaServer)))
			self.globalVariables.ExecuteCommand(self.ComposeCmd("\"cd {} && ./{} &\"".format(self.globalVariables.androidtmpdir, self.globalVariables.fridaServer)), True, False)
		
	def RunFridump(self):
		self.StartFridaServer()
		try:
			self.globalVariables.ExecuteCommand("python {} -U -s {}".format(self.globalVariables.fridumpPath, self.mainWin.cmbApp.currentText()), False)

			mainWin.chkLogcat.setChecked(False)
			output=''
			with open(self.globalVariables.fridumpOutput) as f:
				for line in f:
					output += line
			self.mainWin.txtFileContent.setText(output)
		except:
			print ("Please check the application is running!!")

	def RunUniversalFridaSSLUnPinning(self):
		self.StartFridaServer()
		self.globalVariables.ExecuteCommand("-s {} push {} {}{}".format(self.device, self.globalVariables.burpCertPath, self.globalVariables.androidtmpdir, self.globalVariables.burpCertName))
		self.globalVariables.ExecuteCommand("frida -U -f {} -l {} --no-pause".format(self.mainWin.cmbApp.currentText(), self.globalVariables.fridasslunpinscript1), False, False)

	def ReloadApplications(self):
		self.HideDefaultApplication()

if __name__ == "__main__":
	app = QtWidgets.QApplication(sys.argv)
	app.setWindowIcon(QtGui.QIcon('./Usage/icon.png'))
	print (getBanner())
	mainWin = Gui()
	mainWin.show()

	main=Main(mainWin)
	deviceList=main.GetDeviceList()
	if len(deviceList) > 0:
		for device in deviceList:
			mainWin.cmbDevice.addItem(device)

		mainWin.cmbDevice.currentIndexChanged.connect(lambda: main.ListApplication())
		mainWin.cmbApp.currentIndexChanged.connect(lambda: main.ApplicationSelectionChanged())
		mainWin.chkHideDefaultApp.stateChanged.connect(lambda: main.HideDefaultApplication())
		mainWin.chkSplitConfig.stateChanged.connect(lambda: main.ChangeSplitConfigValue())
		mainWin.chkLogcat.stateChanged.connect(lambda: main.DisplayLogcat())
		mainWin.chkHtmlDecode.stateChanged.connect(lambda: main.DecodeHTMLEntity())
		mainWin.chkURLDecode.stateChanged.connect(lambda: main.DecodeURL())
		mainWin.btnAPKTool.clicked.connect(lambda: main.RunAPKTool())
		mainWin.btnJDGUI.clicked.connect(lambda: main.RunJDGUITool())
		mainWin.btnMobSF.clicked.connect(lambda: main.RunMobSFTool())
		mainWin.btnReinstall.clicked.connect(lambda: main.RunReinstallAPK())
		mainWin.btnFridaSSLUnPin.clicked.connect(lambda: main.RunUniversalFridaSSLUnPinning())
		mainWin.btnFridump.clicked.connect(lambda: main.RunFridump())
		mainWin.btnReloadApps.clicked.connect(lambda: main.ReloadApplications())
		mainWin.btnPullData.clicked.connect(lambda: main.PullApplicationData())
		mainWin.chkLogcat.setChecked(True)
		mainWin.chkHtmlDecode.setVisible(False)
		mainWin.chkURLDecode.setVisible(False)
		logcat=Logcat(mainWin, mainWin.cmbDevice.currentText())
		logcat.start()
		main.ListApplication()
		sys.exit( app.exec() )
	else:
		print ("No emulator found. Re-run the applicaiton after connecting device\n\n")





