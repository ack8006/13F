from xmlScraper import UpdateChecker, Form13FUpdater
import MySQLdb
from contextlib import closing
from datetime import date
import multiprocessing as mp
import keys
from time import sleep

#Bugs
#*******There is some request per second rate from the SEC that will shut me down. so now i'm pausing for 50ms between every request


def checkAndUpdate(cik, lastDate):
	entries = upCheck.get13FList(cik, lastDate)
	formUpdate = Form13FUpdater(cik, entries)
	formUpdate.entryParser()

db = MySQLdb.connect(host = keys.sqlHost, user = keys.sqlUsername, passwd = keys.sqlPassword, db="Quarterly13Fs")

cikList = []

with closing(db.cursor()) as cur:
	#*****sort this by importance so the imporant ones go first...
	cur.execute("SELECT CIK FROM CIKList")
	cikList = [x[0] for x in cur.fetchall()]	

db.close()

upCheck = UpdateChecker()
#DAYS_TO_CHECK_FOR_UPDATES = 82
DAYS_TO_CHECK_FOR_UPDATES =85

#************RREAAAAAALLLLLYYY This should be multithreading,
#might need to be multiple instances of UpdateChecker as opposed to just the one currently

processes = []
for cik in cikList:
	lastDate = upCheck.mostRecentForm13F(cik)
	print cik + ": " + str(lastDate)
	if not lastDate or (lastDate and abs(date.today()-lastDate).days > DAYS_TO_CHECK_FOR_UPDATES):
		processes.append(mp.Process(target=checkAndUpdate, args=(cik, lastDate)))

for p in processes:
	p.start()
	#slows shit down so that not massively overloading SEC.  There is some SEC requests per second
	#this seems to be fixing things, but it is not like i'm only hitting evry 500ms instead, this adds a new process 
	#which starts a whole new list of numbers.  only really important on first loads, after that, assuming this is 
	#run regularly, should only be a few each time.
	sleep(0.5)

