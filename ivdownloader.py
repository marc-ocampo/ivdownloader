###################################################################################################
# 	Python Script for copying SW packages
# 	Author : Marc Stephen D. Ocampo
# 	Requires Python 3.4, BeautifulSoup library
#
#	CHANGELOG
#	v2.9 - 20150623 Modified regex to have additional branches
#	v2.8 - 20150603 Modified regex to have additional branches, add additional link
#		 - fixing 20150505_BUG_http.client.IncompleteRead; added exception handler in FetchHTMLFromURL
#		 - fixing 20150330_BUG_OSError_SemaphoreTimeoutExpired; added exception handler in FetchHTMLFromURL
#	v2.7 - 20150430 check first if zip file is in remote server (CheckIfSWPackageExistsInRemoteServer) before checking if SW is new (CheckIfSWIsNew)
#	v2.6 - 20150318 download packages that are only 1 day old; Modified regex to have additional branches
#	v2.5 - 20150317 Modified regex to have additional branches
#	v2.4 - 20150223 Removed regex for obsolete branch
#	v2.3 - 20140107 fixed bug SW released but zip not available in remote server
#	v2.2 - 20141218 changed URL to check in decreasing releaseTime
#	v2.1 - 20141023 Removed infinite loop on CheckIfThereIsEnoughLocalSpace
#	v2.0 - 20141021 Refactored
#	v1.4 - 20140930 Added hard drive check
#		   -------- rolled back
#		   20140912 No more errors crashing the script
#	v1.4 - 20140826 WN9.1 separated from TRUNK
#	v1.31- 20140818 modify URLError handling; from URLError to urllib.error.URLError
#	v1.3 - 20140811 made fix for URLError (FAILED)
#	v1.2 - 20140801 fixed IndexError due to low local server disk space (catch IndexError) (OK)
#	v1.1 - 20140725 downloads NotOk Trunk and download 1 SW per branch at a time
#	v1.0 - 20140620 fixed HTTP and Timeout error handling (BUG STILL PRESENT)
#		 - 20140604 file transfer total time
#	v0.1 - 20140603 draft
###################################################################################################

################################ MODULES ##########################################################
import bs4
import os
import time
import re
import urllib.request
import shutil
import http		# for urllib.request

import ctypes
import platform
###################################################################################################

################################ GLOBALS ##########################################################
EventLog = r'C:\Downloader\EventLog.log'                     # script logs for troubleshooting
LocalRepo = r'C:\Downloader\LocalRepo'                       # Local folder that will contain all released SW builds
RemoteRepo = r'C:\Downloader\RemoteRepo'                     # Remote folder containing list of SW builds

URL = [r"http://www.google.com", r"http://www.facebook.com"] # URL containing information on which SW builds are RELEASED, NOT RELEASED, etc.
regEx = ["build_\d{3,4}_\d{3,4}_\d{2,3}"]                    # regex pattern of SW build names
srcFolder = ["build"]                                        # source folder in the remote repo containing the builds matched with the regex pattern
destFolder = ["localbuild"]                                  # destination folder in the local repo to store the downloaded SW builds
###################################################################################################

def PrintLog(text, printBoth) :
    """
	Event logging function
	"""
    try :
        print (time.ctime()+" : "+text)
        if os.path.exists(EventLog) :
            mode = "a"
        else :
            mode = "w"
        if printBoth :
            logger = open(EventLog,mode)
            logger.write(time.ctime()+" : "+text+"\n")
            logger.close()
    except IOError :
        print (time.ctime()+" : "+"IO ERROR DURING EVENTLOGGING")
        Timeout(0.5)

def Timeout(t) :
    """
	time out function
	"""
    PrintLog("Timout for "+str(t)+" minute/s",0)		
    time.sleep(t*60)
		
def CheckLocalRepo() :
    """
	Check if local server is online
	"""
    while(True) :
        if os.path.exists(LocalRepo) :
            PrintLog("Local server in "+LocalRepo+" is online!",0)
            break
        else :
            PrintLog("Local server in "+LocalRepo+" is not yet available.",1)
            Timeout(1)

def CheckRemoteRepo() :
    """
	Check if remote server is online
	"""
    while(True) :
        if os.path.exists(RemoteRepo) :
            PrintLog("Remote server in "+RemoteRepo+" is online!",0)
            break
        else :
            PrintLog("Remote server in "+RemoteRepo+" is not yet available.",1)
            Timeout(1)

def HandleNetworkUnavailable() :
    """
	Handler when OSError is encountered due to disconnection to network
	"""
    PrintLog("Network unavailable.",0)
    Timeout(1)
    CheckLocalRepo()
    CheckRemoteRepo()	
	
def RemoveFromLocalDirectory(swPackage) :	
    """
	Remove corrupted SW package when problem is encountered during file transfer
	"""
    PrintLog("Deleting "+swPackage,1)
    try :
        os.remove(swPackage)
    except OSError :
        HandleNetworkUnavailable()
    if os.path.exists(swPackage) :
        PrintLog("Deleting "+swPackage+" UNSUCCESSFUL. Please delete manually.",1)
    else :
        PrintLog("Deleting "+swPackage+" successful.",1)
	
def DownloadBuild(swPackage,counter) :
    """
	Download SW package	
    """
    PrintLog("Copying "+swPackage+" started",1)
    try :
        startTime = time.time()
        with open(os.path.join(RemoteRepo,srcFolder[counter],swPackage,swPackage+".zip"),'rb') as fsrc:
            with open(os.path.join(LocalRepo,destFolder[counter],swPackage+".zip"),'wb') as fdst:
                shutil.copyfileobj(fsrc, fdst, 4096*5120)
	
        if os.path.exists(os.path.join(LocalRepo,destFolder[counter],swPackage+".zip")) :
            PrintLog("Copying "+swPackage+" successful!",1)
            PrintLog("Copy time: "+str((time.time() - startTime)/60)+" minutes",1)
        else :
            PrintLog("Copying "+swPackage+" FAILED.",1)
    except :
        PrintLog("Error occurred while copying "+swPackage,1)
        RemoveFromLocalDirectory(os.path.join(LocalRepo,destFolder[counter],swPackage+".zip"))
        Timeout(0.5)

def CheckIfSWIsNew(swPackage,counter) :
    """
	Checks if SW is new, will download SW package if less than a day old
    """
    if os.path.getmtime(os.path.join(RemoteRepo,srcFolder[counter],swPackage,swPackage+".zip")) >= time.time() - (60*60*24) :
        PrintLog(str(swPackage)+" is NEW",0)
        DownloadBuild(swPackage,counter)
    else :
        PrintLog(str(swPackage)+" is not new. Skipping...",0)
		
def CheckIfSWPackageExistsInRemoteServer(swPackage,counter) :
    """
    Checks if ZIP file is already in the remote server
    """
    if os.path.exists(os.path.join(RemoteRepo,srcFolder[counter],swPackage,swPackage+".zip")) :
        PrintLog("Zip file exists in remote server",0)
        CheckIfSWIsNew(swPackage,counter)
    else :
        PrintLog("Zip file does not exist in remote server, skipping",0)
		
def CheckIfThereIsEnoughLocalSpace(swPackage,counter) :
    """
	Checks if there is enough space in the local server for download
	REFERENCE: # http://anothergisblog.blogspot.com/2012/05/checking-hard-drive-space-using-python.html
	"""
    free_bytes = ctypes.c_ulonglong(0)
    ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(LocalRepo), None, None, ctypes.pointer(free_bytes))
    free_space = int(free_bytes.value/1073741824) # free_space in GB; 1048576 for MB; 1024 for kB; 1 for B
    if (free_space > 1) :
        PrintLog("Local free space is "+str(free_space)+"GB, check first if SW is new.",0)
        CheckIfSWPackageExistsInRemoteServer(swPackage,counter)
    else :
        PrintLog("Local free space is "+str(free_space)+"GB, CANNOT proceed with download",0)
        Timeout(0.5)
	
def FilterAlreadyExisting(build_list, counter) :
    """
	Remove from download list if already existing in local server
	"""
    if os.path.exists(os.path.join(LocalRepo,destFolder[counter])) :
        for i in range(len(build_list)) :
            for f in os.listdir(os.path.join(LocalRepo,destFolder[counter])) :
                if build_list[i] == f.strip(".zip") :
                    build_list[i] = None
    else :
	    PrintLog(os.path.join(LocalRepo,destFolder[counter])+" does not exist!",1)    
    for i in range(build_list.count(None)) :
        build_list.remove(None)
    if len(build_list) != 0 :
        PrintLog("Available for download: "+str(build_list[0]),0)
        CheckIfThereIsEnoughLocalSpace(build_list[0],counter)
    else :
        PrintLog("No new SW package to download for this branch",0)

def ParseHTML(HTMLFile,counter):
    """
	Parse HTML file to collect SW packages with Released status
	"""
    build_list = []
    released_build = []
    for row in HTMLFile.find_all('tr') :
        for td in row.find_all('td') :
            if 'Released' in td.getText() :
                build_list.append(str(row))
				
    all_build_on_page = re.findall(regEx[counter], str(build_list))
       			
    # removing duplicate entries
    for i in range(len(all_build_on_page)) :
	    if all_build_on_page.count(all_build_on_page[i]) > 1 :
		    all_build_on_page[i] = None
    for i in range(len(all_build_on_page)) :
	    if all_build_on_page[i] != None :
		    released_build.append(all_build_on_page[i])
    PrintLog("Parsing HTML file completed.",0)
    FilterAlreadyExisting(released_build,counter)	

def FetchHTMLFromURL(counter) :
    """
	Fetch HTML file from URL for parsing
	"""
    while(True) :
        PrintLog("Fetching HTML file for "+str(srcFolder[counter]),0)
        try :
            ht = urllib.request.urlopen(URL[counter]).read()
            HTMLFile = bs4.BeautifulSoup(ht)
            ParseHTML(HTMLFile,counter)
            break
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) :
            PrintLog("Error while fetching HTML from URL",0)
            Timeout(0.5)
        except (http.client.HTTPException) :			# 20150505_BUG_http.client.IncompleteRead		
            PrintLog("HTTP Exception occurred!",0)
            Timeout(0.5)
        except (OSError) :								# 20150330_BUG_OSError_SemaphoreTimeoutExpired
            PrintLog("Semaphore timeout expired!",0)
            Timeout(0.5)

################################ MAIN #############################################################
if __name__ == "__main__" :
    PrintLog("Booting up SW package downloader",0)
    while(1) :
        CheckLocalRepo()
        CheckRemoteRepo()
        for i in range(len(URL)) :
            FetchHTMLFromURL(i)
        Timeout(1)
###################################################################################################