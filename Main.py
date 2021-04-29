import RPi.GPIO as GPIO

import time
from DB import *
import sys
#Imports MRC522 library
sys.path.append('/home/pi/AccessControlSystem/Lib/MFRC522-python')
from mfrc522 import SimpleMFRC522
import hashlib
#Imports LCD library
sys.path.append('/home/pi/AccessControlSystem/Lib')
import lcd_library
from pyfingerprint.pyfingerprint import PyFingerprint
import random
import string
import datetime

Door_Open = 5
Door_Close = 6


GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(Door_Open, GPIO.OUT)
GPIO.setup(Door_Close, GPIO.OUT)
#Creates LCD object
lcd = lcd_library.lcd()
#Creates object for MFRC522 RFID read/Writer
rfidReader = SimpleMFRC522()

#Creates object for fingerprint library, then verifys that it is working
try:
    fingerprintScanner = PyFingerprint('/dev/ttyUSB0', 57600, 0xFFFFFFFF, 0x00000000)

    if ( fingerprintScanner.verifyPassword() == False ):
        raise ValueError('The given fingerprint sensor password is wrong!')
except Exception as e:
    print('The fingerprint sensor could not be initialized!')
    print('Exception message: ' + str(e))
    exit(1)
	
#Goes through the DB to check if the finger is present
def CheckFingerprintPresent():
	fngrArry = getFingerprints()
	for row in fngrArry:
		#If row is empty break out of loop, means that if fingerprint coloumn in DB is empty, do no check
		if row is None:
			break
			
		if row[1] is None:
			pass
		else:
			#Takes the current template selected, and uploads it to the second charbuffer
			fingerprintScanner.uploadCharacteristics(0x02, eval(row[1]))
			#Compares the fingerprints, then returns result as int, if the result returns 0, then the prints do not match, if not it will return the accuracy score of the fingerprint
			result = fingerprintScanner.compareCharacteristics()
			
			#If the result shows that the prints match, then return true
			if result != 0:
				return row[0]
				break
	#If no matching prints are found, return false
	return None

#Prints all recorded logs on the terminal, and waits for the RFID and fingerprint sensor to pick up a user
def ControlSystemLoop():
	while True:
		print("------------------------\nAccess Control System Active\n------------------------")
		getAllLogs()
		DoorOpenClose(False)
		try:	
			#Does Loop until fingerprint is read
			while (fingerprintScanner.readImage() == False):
				#Waits for RFID to be present
				id, text = rfidReader.read_no_block()
				#Needed because there are a bunch of spaces at the end of the token import
				#cleaning up the text variable
				if id is None:
					os.system('clear')
					ControlSystemLoop()
					break
				else:
					text = text[:10]
					user = getUserByRFID(text)
					if user is None:
						LCDMessage("Access", "Denied")
						AddLog(0, 0,"Denied")
						time.sleep(5)
						os.system('clear')
						LCDMessage("Waiting for", "Identification")
					else:
						#Opens door for 5 seconds and prints message on LCD, then Logs entry in DB and resets loop
						DoorOpenClose(True)
						LCDMessage("Welcome", "%s %s" % (user[1], user[2]))
						AddLog(user[0], 0, "Granted")
						time.sleep(5)
						os.system('clear')
						LCDMessage("Waiting for", "Identification")
										
			fingerprintScanner.convertImage(0x01)
		
			userID = CheckFingerprintPresent()
			if userID is not None:
				user = getUserByID(userID)
				DoorOpenClose(True)
				LCDMessage("Welcome","%s %s" % (user[1], user[2]))
				AddLog(user[0], 1, "Granted")
				time.sleep(5)
				os.system('clear')
				LCDMessage("Waiting for", "Identification")
			else:
				LCDMessage("Access", "Denied")
				AddLog(0,0,"Denied")
				time.sleep(5)
				os.system('clear')
				LCDMessage("Waiting for", "Identification")
								
		except Exception as e:
			print('Error occured with devices Exception message:' + str(e))
			print("Returning to menu...")
			time.sleep(2)
			menu()

#Allows for the user to search the DB by name to find user ID of user to remove		
def removeByName():
		print("Number 1 selected: Name")
		Fname = raw_input('Enter users first name: ')
		Lname = raw_input('Enter users last name: ')
		users = getUserByName(Fname, Lname)
		userIDs = []
		if not users:
			print("User/s: %s %s does not exist, going back" % (Fname, Lname))
			time.sleep(5)
			os.system('clear')
			removeUser()
		else:
			for row in users:
				print("ID: %s Name: %s %s " % (row[0], row[1], row[2]))
				userIDs.append(row[0])
				
		while True:
			try:
				userID = int(raw_input("Please select user ID of user you want to remove\n"))
				if userID in userIDs:
					result = deleteUser(userID)
					if result:
						print("User number %s deleted from system" % userID)
						break
					else:
						print("Error: User does not exist, please try again")
				else:
					print("User not present in list")
		
			except ValueError:
				print("Please enter numbers only")
		while True:
			ExOrRet = raw_input('Please select option: \n1) Return to menu\n 2) Exit Application\n')
			if ExOrRet == '1':
				print("Option 1 selected, going back to menu")
				time.sleep(2)
				os.system('clear')
				menu()
				break
			elif ExOrRet == '2':
				print("Option 2 selected\nExiting Application...")
				time.sleep(2)
				break
			else:
				print("Please enter valid input")
				continue
	#Closes application when second option is selected, if put inside loop, application will loop forever without closing
		GPIO.cleanup() 		

#Removes user from database using user ID given by user, if user is found, then user is deleted, system will keep prompting user if Incorrect
def removeByID():
	users = getAllUsers()
	print("Listing all users in system:")
	for row in users:
		print("ID: %s Name: %s %s" % (row[0], row[1], row[2]))
	try:
		usrInput = int(raw_input("Please select ID of user to delete\n"))
		check = deleteUser(usrInput)
		if check:
			print("User: %s deleted" % usrInput)
		else:
			print("User not found, please try again")
			time.sleep(1)
			os.system('clear')
			removeByID()
	except ValueError:
		print("Please input valid value")
		time.sleep(1)
		os.system('clear')
		removeByID()
	while True:
		ExOrRet = raw_input('Please select option: \n1) Return to menu\n2) Exit Application\n')
		if ExOrRet == '1':
			print("Option 1 selected, going back to menu")
			time.sleep(2)
			os.system('clear')
			menu()
			break
		elif ExOrRet == '2':
			print("Option 2 selected\nExiting Application...")
			time.sleep(2)
			
			break
		else:
			print("Please enter valid input")
			continue
	#Closes application when second option is selected, if put inside loop, application will loop forever without closing
	GPIO.cleanup() 

#is called when user is to be removed from the system, prompts user	to select method of removal
def removeUser():
	usrInput = raw_input('Select method of removal (Please type number of option you would like to select) \n1) Name \n2) User ID \n3) Go back to menu\n')
	if usrInput == '1':
		time.sleep(1)
		os.system('clear')
		removeByName()
	elif usrInput == '2':
		print("Number 2 selected: User ID")
		time.sleep(1)
		os.system('clear')
		removeByID()
	elif usrInput == '3':
		print("Number 3 selected\nGoing back to menu...")
		time.sleep(2)
		os.system('clear')
		menu()
	else:
		print("Please enter valid responce, you entered: %s" % usrInput)
		removeUser()

#Is called when user is being enrolled into the system, will pass data into the DB to be stored once all infomation is gathered		
def enroll():
	#Takes the input of user and stores as variable for first name and last name
	Fname = raw_input('Enter users first name: ')
	Lname = raw_input('Enter users last name: ')
	#Infinate Loop
	while True:
		
		#Generates Random number using method in Fingerprint Library that generates 32-bit decimal number
		rand = genRandomString()
		print("Place RFID tag next to scanner")
		#Waits for RFID tag to write to, then writes to RFID tag
		try:
			id, rand = rfidReader.write(rand)
		except:
			print("Error interfacing RFID, trying again")
			enroll()
		print("RFID recorded with code '%s'" % rand)
		#Breaks out of loop
		break
	
	checkfng = enrollFingerCheck()
	if checkfng:
		print("Please place finger on fingerprint scanner...")
		
		#Waits for fingerprint to be read
		while (fingerprintScanner.readImage() == False):
			pass
		
		#Converts image into template and stores it in charBuffer 0x01
		fingerprintScanner.convertImage(0x01)
		
		#Compare loop here
		userid = CheckFingerprintPresent()
		#If true, fingerprint is already present
		if userid is not None:
			user = getUserByID(userid)
			print("Fingerprint Already detected in system for user %s %s, please try again" % (user[1], user[2]))
			enroll()
		else:
			#Downloads the Characteristics in charbuffer 0x01 and converts to a string
			print("Please Remove Finger from fingerprint scanner...")
			time.sleep(4)
			print("Please put same finger back on fingerprint scanner...")
			while (fingerprintScanner.readImage() == False):
				pass
				
			fingerprintScanner.convertImage(0x02)
			#Compare both fingerprints taken to see if they match
			if (fingerprintScanner.compareCharacteristics() == 0):
				print("Fingerprints do not match... please try again...")
				time.sleep(2)
				enroll()
				
			#Creates template based off of the two fingerprints
			fingerprintScanner.createTemplate()
			#Downloads the created template from the fingerprint charbuffer and converts to string
			FngrTmplate = str(fingerprintScanner.downloadCharacteristics(0x01)).encode('utf-8')
			#Saves details as new row in DB
			addUser(Fname, Lname, rand, FngrTmplate)
	else:
		addUser(Fname, Lname, rand, None)
	enrollEnd()

#Called when user is being enrolled, decides if the user wants to enrol a fingerprint or not	
def enrollFingerCheck():
	choice = raw_input('Record users fingerprint? y/n\n')
	if choice.lower() == 'y':
		return True
	elif choice.lower() == 'n':
		return False
	else:
		print("Please select valid option.")
		enrollFingerCheck()
		
def enrollEnd():
	choice = raw_input("\nFinished Enrolling, Please select option\n1)Go back to menu\n2)Enroll another user\n3)Exit appilication\n")
	if choice == '1':
		print("Going back to menu")
		time.sleep(3)
		os.system('clear')
		menu()
	elif choice == '2':
		print("Enrolling another student")
		time.sleep(3)
		os.system('clear')
		enroll()
	elif choice == '3':
		print("\nExiting Application")
		LCDMessage("Shutting Down...", "Goodbye")
		time.sleep(2)
		lcd.lcd_clear()
		GPIO.cleanup()
	else:
		print("Please select valid option")
		time.sleep(2)
		os.system('clear')
		enrollEnd()

#Generates and returns random 15 character string not present in the database	
def genRandomString():
	try:
		#Creates Random string
		rndmStr = ''.join(random.choice(string.ascii_letters) for i in range(10))
		#Checks to see if string is already stored in DB
		check = getUserByRFID(rndmStr)
		#If the string isn't in the DB, returns the random string, otherwise it creates another random string by recursing
		if check == None:
			return rndmStr
		else:
			genRandomString()
	#This method will sometimes cause an error, to prevent this call it again
	except:
		print("Encountered Error with creating string... Trying again...")
		genRandomString()

#Gives boolean, if true RED LED is off, Green LED turned on
def DoorOpenClose(b):
	if b:
		#If true, open door 
		GPIO.output(Door_Open, GPIO.HIGH)
		GPIO.output(Door_Close, GPIO.LOW)
	else:
		#else, close door
		GPIO.output(Door_Close, GPIO.HIGH)
		GPIO.output(Door_Open, GPIO.LOW)

#Takes two strings, first one applies to line one, second to line two Lines need to be limited to 16 characters
def LCDMessage(LineOne, LineTwo):
	#Clears any characters currently on LCD screen
	lcd.lcd_clear()
	#Prints message on LCD, first prints message on line 1, second prints on line 2
	lcd.lcd_display_string(LineOne, 1)
	lcd.lcd_display_string(LineTwo, 2)
	
#Contains CLI interface for when application is opened, checks for which functionality user wants to access	
def menu():
	while True:
		usrInput = raw_input('Access Control System using RFID and Fingerprint scanner:\nPlease select option: (Please type the number you want to select)\n------------------\n'
		'1) Add/Remove user to/from Database\n2) View Database\n3) Start Access Control System\n4) Exit\n------------------\n')
		if usrInput == '1':
			print("-> Option 1 selected | Going to: Add/Remove Users section")
			time.sleep(2)
			os.system('clear')
			addOrRemove()
			break
			
		elif usrInput == '2':
			print("-> Option 2 selected  | Going to: View Database")
			time.sleep(2)
			os.system('clear')
			viewDB()
			break
			
		elif usrInput == '3':
			print("-> Option 3 selected  | Going to: Access Control System Mode")
			time.sleep(2)
			os.system('clear')
			#LCD message needs to be printed here, else it will repeatedly print in the Access Control loop
			LCDMessage("Waiting for", "Identification")
			ControlSystemLoop()
			break
			
		elif usrInput == '4':
			print("-> Option 4 selected | Exiting System...")
			LCDMessage("Shutting Down...", "Goodbye")
			time.sleep(2)
			lcd.lcd_clear()
			break
			
		else:
			print("Please select valid option")
			time.sleep(2)
			os.system('clear')
			
	GPIO.cleanup()
#When system starts, menu function is called to display CLI interface, other methods accessed through this
#If application is closed through keyboard, system will go through exit process by waiting 2 seconds and closing the application

#CLI interface for when Add/Remove user is selected from menu, asks user which function to choose
def addOrRemove():
	usrInput = raw_input('Would you like to (Please type number of option you would like to select) \n1) Enroll a new user into the system \n2) Remove a user from the system \n3) Go back\n')
	if usrInput == '1':
		print("Option 1 selected\nAdding user, clearing terminal...")
		time.sleep(3)
		os.system('clear')
		enroll()
	elif usrInput == '2':
		print("Option 2 selected\nRemove user, clearing terminal...")
		time.sleep(2)
		os.system('clear')
		removeUser()
	elif usrInput == '3':
		print("Option 3 selected\nGoing back to menu...")
		time.sleep(2)
		os.system('clear')
		menu()
	else:
		print("Please enter valid responce, you entered: %s" % usrInput)
		addOrRemove()

def viewDB():
	usrInput = raw_input('What infomation would you like to view?(Please type the number of the option you would like to select)\n1) Users inside the system\n2) All attemped logins\n')
	if usrInput=='1':
		print("Option 1 Selected\nDisplaying users...")
		time.sleep(3)
		os.system('clear')
		usrs = getAllUsers()
		for row in usrs:
			if row[4] is None:
				finger = "No"
			else:
				finger = "Yes"
			print("User ID: %d | Name: %s %s | RFID password: %s | Fingeprint: %s" % (row[0], row[1], row[2], row[3], finger))
	elif usrInput == '2':
		print("Option 2 Selected\nDisplaying Attemped sign in's")
		time.sleep(3)
		os.system('clear')
		getAllLogs()
	
	raw_input("\n\nPress any Key to return to menu")
	os.system('clear')
	menu()
			
try:
	create_db_table()
	DoorOpenClose(False)
	menu()
except KeyboardInterrupt:
	print("\nExiting Application")
	LCDMessage("Shutting Down...", "Goodbye")
	time.sleep(2)
	lcd.lcd_clear()
	GPIO.cleanup()


