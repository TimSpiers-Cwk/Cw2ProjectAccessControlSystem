import sqlite3
import os
import datetime
#Creates Filepath to SQLite DB
Default_Path = os.path.join(os.path.dirname(__file__), '/home/pi/AccessControlSystem/Data/AccessControlDB.sqlite3')
#Connects to DB
def db_connect(path=Default_Path):
    Connect = sqlite3.connect(path)
    return Connect
#Creates cursor to execute SQLite Querys
con = db_connect()
cur = con.cursor()
#Creates the DB and tables if they do not already exist
def create_db_table():
    users_sql = """
    CREATE TABLE IF NOT EXISTS users (
    id integer PRIMARY KEY,
    first_name text NOT NULL,
    last_name text NOT NULL,
    rfid_tag text NOT NULL,
    fingerprint_template blob)"""
    cur.execute(users_sql)
    sign_in_log = """
    CREATE TABLE IF NOT EXISTS sign_in_log(
    log_id integer PRIMARY KEY,
    user_id integer,
    date_time text NOT NULL,
    rfid_or_finger integer NOT NULL,
    Access_Denied_or_Granted text NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id))"""
    cur.execute(sign_in_log)

#Adds  A user to the users table
def addUser(firstName, lastName, RFIDTag, FingerprintTemplate):
    insert_user = "INSERT INTO users (first_name, last_name, rfid_tag, fingerprint_template) VALUES (?, ?, ?, ?)"
    cur.execute(insert_user, (firstName, lastName, RFIDTag, FingerprintTemplate))
    user_id = cur.lastrowid
    print("User: %s %s Added to the system with User ID: %d" % (firstName, lastName, user_id))
    con.commit()
    
def getUserByID(userID):
    cur.execute("SELECT * FROM users WHERE id = '%s'" % (userID))
    result = cur.fetchone()

    return result

def getUserByName(firstName, lastName):
    
    cur.execute("SELECT id, first_name, last_name FROM users WHERE first_name = '%s' AND last_name = '%s'" % (firstName, lastName))
    result = cur.fetchall()

        
    return result
    
def getUserByRFID(RFID):
    cur.execute("SELECT * FROM users WHERE rfid_tag = '%s'" % (RFID))
    result = cur.fetchone()
    return result

def getFingerprints():
    cur.execute("SELECT id, fingerprint_template FROM users")
    result = cur.fetchall()
    return result
   
def getAllUsers():
    cur.execute("SELECT * FROM users")
    result = cur.fetchall()
    return result
    
def deleteUser(userID):
    check = getUserByID(userID)
    if check == None:
        return False
    else:
        try:
            cur.execute("DELETE FROM users WHERE id = %d" % (userID))
            cur.execute("DELETE FROM sign_in_log WHERE user_id = %d" % (userID))
            con.commit()
            return True
        except:
            print("Error: User could not be deleted")

def AddLog(userID, RFIDorFinger, PassOrFail):
    insertLog = "INSERT INTO sign_in_log (user_id, date_time, rfid_or_finger, Access_Denied_or_Granted) VALUES (?,?,?,?)"
    date = datetime.datetime.now()
    cur.execute(insertLog, (userID, date, RFIDorFinger, PassOrFail))
    con.commit()
    
def getAllLogs():
    #Select query gets all info relating to sign in log with an inner join to the users table with relavent info, then order it by Log ID
    cur.execute("SELECT * FROM sign_in_log")
    result = cur.fetchall()
    #If no results returned from sign in log different messgae is printed
    if not result:
        print("------------------\nNo Sign-in's recorded\n------------------")
    #if results are fond this is executed
    else:
        #Loops through all rows in results
        for row in result:
            #If 0 then RFID was used for verification
            if row[3] == 0:
                RFIDorFing = "RFID"
            #If 1 then Fingerprint is used
            else:
                RFIDorFing = "Fingerprint"
                #If the user ID does not equal 0 (Non-existing user), then find that user
            if row[1] != 0:
                #Gets users first and last name
                cur.execute("SELECT users.first_name, users.last_name FROM sign_in_log INNER JOIN users ON sign_in_log.user_ID = users.id WHERE user_id = '%d'" % (row[1]))
                SuccessfulResult = cur.fetchone()
                print("-> Log No. %s | Access: %s | User ID: %s | Name: %s %s | Using: %s | Date & Time: %s" % (row[0], row[4], row[1], SuccessfulResult[0], SuccessfulResult[1], RFIDorFing, row[2]))
            else:
                print("-> Log No. %s | Access: %s | User not found | UsingL %s | Date & Time: %s" % (row[0], row[4], RFIDorFing, row[2]))
     

    
