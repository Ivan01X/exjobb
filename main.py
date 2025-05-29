import streamlit as sl
import scipy.io as sc

import matplotlib.pyplot as mpl
#import pandas as pd
import dymat as dy
import numpy as np
import json
import datetime as dtime


def mainView():
    sl.title("Welcome to the Dashboard")
    sl.header("To start visualization, choose simulation method from dashboard menu")

def initSidebar():
    sl.sidebar.markdown ("""
    <style>
        [data-testid=stLogoSpacer] 
        {
            display: block;
        }
        [data-testid=stLogoSpacer]:after 
        {
            content: 'Dashboard Menu';
        }
    </style>
    """,
        unsafe_allow_html=True)
    
    newDash = sl.sidebar.button('New visualization')
    loadDash = sl.sidebar.button('Load Dashboard')

    return newDash, loadDash


def uploadSim():
    sl.title("Create Dashboard")
    fileToUpload = sl.file_uploader("Upload .mat result file(s) and .txt filter file(s)", type=["mat","txt"], accept_multiple_files=True)

    if fileToUpload:
        matFiles = []
        matNames = []
        variables = dict()
        uploadedData = dict()
        
        if 'fileTimes' not in sl.session_state:      
            sl.session_state.fileTimes = dict()

        for file in fileToUpload:
            fileName = file.name.split('.')[0]
            if ".mat" in file.name:

                sl.session_state.fileTimes[fileName] = sc.loadmat(file)['data_2'][0,]
                uploadedData[fileName] = dict()  #Creating a 2D dictionary to store filtered variables and data for each file
                matFiles.append(dy.DyMatFile(file))
                matNames.append(fileName)
                
            elif ".txt" in file.name:  #assuming filter files will be .txt change if not
                file.seek(0) #begining of file 
                for line in file:
                    dLine = line.decode("utf-8").strip()
                    if dLine:
                        if not fileName in variables.keys():
                            variables[fileName] = []
                        variables[fileName].append(dLine)
        
        #check if corresponding filter file is uploaded
        for file in fileToUpload:
            fileName = file.name.split('.')[0]
            if not fileName in variables.keys():
                sl.write("Please upload a filter .txt file for "+fileName)
                clearSession()
                return None
            
        #check if corresponding result mat file is uploaded
        for var in variables.keys():
            if not var in matNames:
                sl.write("Please upload a result .mat file for "+var)
                clearSession()
                return None

        for matFile in matFiles:
            fileName = matFile.fileName.name.split('.')[0]
            for var in variables[fileName]:
                if var in matFile.names():
                    uploadedData[fileName][var] = matFile.data(var)
            if len(uploadedData[fileName]) == 0 and len(matFiles) !=0:
                sl.write("No Variables found matching for: " + matFile.fileName.name)
        
        if len(variables) != 0 and len(matFiles) == 0:
            sl.write("Filter is chosen, please select a .mat file")
        
        return uploadedData
            
            
def updateCheckbox(file, variable, isVar):
    if file in sl.session_state and not isVar:
        if sl.session_state[file] ==False and sl.session_state.fileCheckbox[file] == True:
            for var in sl.session_state.varCheckbox[file]:
                sl.session_state.varCheckbox[file][var] = False
        elif sl.session_state[file] ==True and sl.session_state.fileCheckbox[file] == False:
            for var in sl.session_state.varCheckbox[file]:
                sl.session_state.varCheckbox[file][var] = True

        sl.session_state.fileCheckbox[file] = sl.session_state[file]


    if variable+": "+file in sl.session_state and isVar:
        sl.session_state.varCheckbox[file][variable] = sl.session_state[variable+": "+file]


def showFilters(uploadedData):  
    sl.header("Filtering")

    if uploadedData:
        if 'fileCheckbox' not in sl.session_state:      
            sl.session_state.fileCheckbox = dict()
            for file in uploadedData.keys():
                sl.session_state.fileCheckbox[file]=True

        if 'varCheckbox' not in sl.session_state:   
            sl.session_state.varCheckbox = dict()
            for file in uploadedData.keys():
                sl.session_state.varCheckbox[file] = dict()
                for var in uploadedData[file]:
                    sl.session_state.varCheckbox[file][var]=True  

        
        #------------------- Filter for files -----------------------
        fileNames = []
        with sl.expander("Select file(s)"):
            searchFiles = sl.text_input("Search files")
            with sl.container(height=150):
                for file in uploadedData.keys():    #search for files
                    fileNames.append(file)
                fileNames = sorted(fileNames, key=lambda s: searchFiles.lower() in s.lower(), reverse=True)
                           
                for file in fileNames:          #show files in list
                    if not file in sl.session_state.fileCheckbox.keys():
                        sl.session_state.fileCheckbox[file]=True
                    if not file in sl.session_state.varCheckbox.keys():
                        sl.session_state.varCheckbox[file] = dict()
                        for var in uploadedData[file]:
                            sl.session_state.varCheckbox[file][var]=True  
                    sl.checkbox(file, key=file, value=True, on_change=updateCheckbox(file, "", False))  
        

        #------------------- Filter for variables -------------------
        varNames = []
        with sl.expander("Select variable(s)"):
            searchVars = sl.text_input("Search variables")
            with sl.container(height=150):
                oldSessionFile = []
                for file in sl.session_state.fileCheckbox.keys():    
                    if not file in uploadedData.keys():
                        oldSessionFile.append(file)

                for file in oldSessionFile:
                    sl.write(file)
                    del sl.session_state.fileCheckbox[file]
                    del sl.session_state.varCheckbox[file]
                
                if len(sl.session_state.fileCheckbox) == 0:
                    for file in uploadedData.keys():
                        sl.session_state.fileCheckbox[file]=True
                
                    
                if len(sl.session_state.varCheckbox) == 0:
                    for file in uploadedData.keys():
                        sl.session_state.varCheckbox[file] = dict()
                        for var in uploadedData[file]:
                            sl.session_state.varCheckbox[file][var]=True 
                
                for file in sl.session_state.fileCheckbox.keys():    #search for variables
                    if sl.session_state.fileCheckbox[file] == True:
                            vars = uploadedData[file]
                            for var in vars.keys():
                                varNames.append(var+":"+file)
                
                varNames = sorted(varNames, key=lambda s: searchVars.lower() in s.lower(), reverse=True)
                for var in varNames:
                    tmp = var.split(':')
                    variable = tmp[0]
                    fileName = tmp[1]
                    sl.checkbox(variable+": "+fileName, value=True, key=variable+": "+fileName, on_change=updateCheckbox(fileName, variable, True))

        #sl.write(sl.session_state.fileCheckbox)
        #sl.write(sl.session_state.varCheckbox)

        filteredData = dict()
        for file in sl.session_state.varCheckbox:
            if sl.session_state.fileCheckbox[file] == True:
                filteredData[file] = dict()
            for variable in sl.session_state.varCheckbox[file]:
                if sl.session_state.varCheckbox[file][variable] == True:
                    filteredData[file][variable] = uploadedData[file][variable]     #insert data
        return filteredData
    else:
        return None

#def getSimTime(filePath): #Dymat does not read in time 
#    return sc.loadmat(filePath)['data_2'][0,]
    
def findTimeViolations(fileName, data):
    timeList = []
    prev = -1
    counter = 0
    fileTime = sl.session_state.fileTimes[fileName]
    for val in data:
        if prev !=-1: #skip initial value 
            if val == 3 and prev != 3:
                #append simulation time when the violation occoured in float, rounded to two decimals
                timeList.append(round(float(fileTime[counter]),2))
            elif val < 1 or val > 4:
                print("Data_error")
        prev = val
        counter += 1
    timeStr = ""
    for time in timeList:
        timeStr += str(time) + "s, "
    timeStr = timeStr[:-2]

    #return in format of list and string
    return timeList, timeStr

def summaryReport(filteredData):
    #scenarioPV = 0.0
    #scenarioName = ""
    reqNr = 0
    reqU = 0
    reqS = 0
    reqV = 0
    reqVlist = []
    simTime = 0.0

    for file in filteredData:
        #scenarioName = file
        simTime = sl.session_state.fileTimes[file][-1]
        for requirement in filteredData[file]:
            reqNr += 1
            match filteredData[file][requirement][-1]:
                case 1:
                    reqU += 1
                #case 2: #ASK!
                case 3:
                    reqV += 1
                    timeList,when = findTimeViolations(file, filteredData[file][requirement])
                    
                    reqVlist.append(requirement+' from '+file + " is violated at time frame(s): "+when)
                case 4:
                    reqS += 1 #if last value true bot has beeen false at least once, then what?
    #TO DO
    # calc PV, what is it?

    sl.subheader("Batch summary")
    
    cont = sl.container(border=True)
    with cont:
        col1, col2 = sl.columns(2)
        with col1:
            #sl.write(scenarioName + ": ")
            #sl.write("Simulation duration: ")
            sl.write("Total number of requirements: ")
            sl.write("Total number of violated requirements: ")
            sl.write("Total number of untested requirements: ")
            sl.write("Total number of satisfied requirements: ")
        sl.write("List of violated requirements: ")
        with sl.container(height=150):
            sl.markdown("\n".join(f"{i+1}. {req}" for i, req in enumerate(reqVlist)))
        with col2:
            #sl.markdown(f'**{scenarioPV}% PV**')
            sl.markdown(f'**{reqNr}**')
            sl.markdown(f'**:red[{reqV}]**')
            sl.markdown(f'**:orange[{reqU}]**')
            sl.markdown(f'**:green[{reqS}]**')
            
def makeIndividualReport(file, filteredData):
    
    color = ["orange","yellow","red","green"]
    values = [1.0, 2.0, 3.0, 4.0]
    simTime = 0.0

    with sl.expander("Report for: "+file):
        with sl.container(border=False, height=590):
            for requirement in filteredData[file]:
                with sl.container(border=True):
                    col1, col2 = sl.columns(2, gap="large")
                    #scenarioPV = 0.0
                    finalState = ""
                    finalValue = 0
                    finalMargin = 0
                    counter = 0

                    simTime = sl.session_state.fileTimes[file][-1]
                    timeList,when = findTimeViolations(file, filteredData[file][requirement])
                    
                    counter = len(timeList)

                    with col1:
                        count = {val: np.count_nonzero(filteredData[file][requirement] == val) for val in values}
                        count = np.array(list(count.values()))
                        totnum = len(filteredData[file][requirement])
                        lab = ["Undefined "+str(round((count[0]/totnum*100),2))+"%","Undecided "+str(round((count[1]/totnum*100),2))+"%","False "+str(round((count[2]/totnum*100),2))+"%","True "+str(round((count[3]/totnum*100),2))+"%"]
                            
                        fig, ax = mpl.subplots()
                        ax.pie(count, colors=color, radius=0.8)
                        ax.legend(lab, loc="best", fontsize=9)
                        sl.pyplot(fig)


                    with col2:
                        match filteredData[file][requirement][-1]:
                            case 1:
                                finalState = '''Final state:<span style="color:orange"> **Untested**</span>'''
                            case 2:
                                finalState = '''Final state:<span style="color:#FFDB58"> **Undecided**</span>'''
                            case 3:
                                finalState = '''Final state:<span style="color:red"> **Violated**</span>'''
                            case 4:
                                finalState = '''Final state:<span style="color:green"> **Satisfied**</span>'''
                        
                        sl.markdown(f"**{requirement}**")
                        #sl.write("Scenarios: " + str(scenarioPV) + "% PV")
                        sl.write("Simulation duration: "+str(simTime) + "s")
                        sl.markdown(finalState, unsafe_allow_html=True)
                        sl.write("Final value: " + str(finalValue))
                        sl.write("Final margin: " + str(finalMargin))
                        if counter != 0:
                            sl.write("Violation count: " + str(counter)+ " time(s) at "+when)
                        else:
                            sl.write("Violation count: -")
                    
                    x = sl.session_state.fileTimes[file] #getSimTime(file)
                    y = filteredData[file][requirement]
                    
                    fig, ax = mpl.subplots()
                    ax.set_yticks([1, 2, 3, 4], ["Undefined", "Undecided", "False", "True"])
                    ax.plot(x, y)
                    ax.set_xlabel("Time [s]")
                    ax.set_ylabel("4-valued Boolean")
                    fig.set_figheight(2)
                    sl.pyplot(mpl)


def makeAllIndividualReports(filteredData):
    sl.subheader("Individual reports per simulation")
    for file in filteredData:
        makeIndividualReport(file, filteredData)

def visualizeData(filteredData):
    sl.header("Visualization")
    if sl.session_state.dashOption['new']:
        saveButton(filteredData)
    summaryReport(filteredData)
    makeAllIndividualReports(filteredData)

def saveButton(filteredData):
    dataToSave = dict()
    timeToSave = dict()
    name = sl.text_input("Dashboard name: (Press Enter to apply)", placeholder="MyDashboard")
    
    if not name:
        name = "MyDashboard"
    
    for file in filteredData:
        dataToSave[file] = dict()
        timeToSave[file] = sl.session_state.fileTimes[file].tolist()
        for req in filteredData[file]:
            dataToSave[file][req] = filteredData[file][req].tolist()

    dateTime = dtime.datetime.now().strftime("%d-%m-%Y_%H-%M")
    sl.download_button(
        label = "Download Dashboard",
        data = json.dumps([dataToSave, timeToSave]),
        file_name = name+"_"+dateTime+".json",
        on_click= "ignore",
        type = "primary",
        icon = ":material/download:"
        )  
        
def loadDashboard():
    sl.title("Load Dashboard")
    file = sl.file_uploader("Upload dashboard file", type=["json"])
    if 'fileTimes' not in sl.session_state:      
        sl.session_state.fileTimes = dict()

    if file:
        loadedData = dict()
        obj = json.load(file)
        for index, value in enumerate(obj):
            if index == 0:
                for fileName in value:
                    loadedData[fileName] = dict()
                    for req in value[fileName]:
                        loadedData[fileName][req] = np.array(value[fileName][req])
            elif index == 1:
                for fileName in value:
                    sl.session_state.fileTimes[fileName] = value[fileName]
        return loadedData

def clearSession():
    for key in sl.session_state.keys():
        if key != 'dashOption':
            sl.session_state.pop(key)

def main():#det som finns i main ska läggas i funktioner
    sl.set_page_config(initial_sidebar_state='collapsed')

    if 'dashOption' not in sl.session_state:
        sl.session_state.dashOption = {}
    page = sl.empty()
    
    newDash, loadDash = initSidebar()

    if newDash or loadDash:
        sl.session_state.dashOption = {'new': newDash, 'load': loadDash}

    if sl.session_state.dashOption:
        if sl.session_state.dashOption['new']:
            if 'fileTimes' in sl.session_state:
                sl.session_state.pop('fileTimes')
            uploadedData = uploadSim()
            if uploadedData:
                filteredData = showFilters(uploadedData)
                if filteredData:
                    visualizeData(filteredData)
        elif sl.session_state.dashOption['load']:
            clearSession()
            uploadedData = loadDashboard()
            if uploadedData:
                visualizeData(uploadedData)

        page.empty()
    elif not sl.session_state.dashOption:
        with page.container():
            mainView()
    

if __name__ == "__main__":
    main()