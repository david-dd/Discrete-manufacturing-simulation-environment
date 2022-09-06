import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import mysql.connector              # MYSQL
import random
from collections import OrderedDict
import json
import ast


###########################################################
### MySQL Setting
###########################################################

mysqlHost = "localhost"
mysqlUser = "root"
mysqlPassword = ""
mysqlDatabase = "rlskipping"


def plot_learning_curve(x, scores, figure_file):
    running_avg = np.zeros(len(scores))
    for i in range(len(running_avg)):
        running_avg[i] = np.mean(scores[max(0, i-100):(i+1)])
    plt.plot(x, running_avg)
    plt.title('Running average of previous 100 scores')
    plt.savefig(figure_file)
    plt.close('all')


def die(text = ""):
    print("############################################################################")
    print()
    print()
    print()
    raise ValueError(text)

def getCurrentTime():
    now = datetime.now()
    current_time = now.strftime("%Y-%m-%d-%H-%M_%S")
    return str(current_time + "")

def intToBinary(input, lenght):
    output = str(bin(int(input))).replace("0b", "")

    while len(output)<lenght:
        output = "0" + output 

    if output.endswith("-1"):
        output = output[:len(output) - 2]
        output = "1" + str(output) + "0"

    return output

def intToOneHotEncodedString(input, lenght):
    input = int(input)

    output = ""
    while len(output)<lenght:
        output = "0" + output 

    output = replace_str_index(output, input, "1")

    return output[::-1] # reverse

def replace_str_index(text,index=0,replacement=''):
    return '%s%s%s'%(text[:index],replacement,text[index+1:])

#####################################################################
#####################################################################
# MySQL Functions
#####################################################################
#####################################################################


def openMySQL(mysqlHost, mysqlUser, mysqlPassword, mysqlDatabase):

    mydb = mysql.connector.connect(
        host=mysqlHost,
        user=mysqlUser,
        password=mysqlPassword,
        database=mysqlDatabase
    )
    mycursor = mydb.cursor(prepared=True)
    return [mydb, mycursor]


def closemySQL(mydb):
    mydb.close()


def storeSampelInMySQL(mydb, mycursor, best, worst, conveyor, carrier, stations, uncertainty):
    s1 = stations[0][1]
    s2 = stations[1][1]
    s3 = stations[2][1]
    s4 = stations[3][1]



    sql = "INSERT INTO `calculatedsamples`(`ammountOfCarriers`, `s1`, `s2`, `s3`, `s4`, `best`, `worst`, `conveyor`, `carrier`, `stations`, `uncertainty` ) VALUES (" + str(len(carrier)) + ", " + str(s1) + ", " + str(
        s2) + ", " + str(s3) + ", " + str(s4) + ", " + str(best) + ", " + str(worst) + ", '" + str(conveyor) + "', '" + str(carrier) + "', '" + str(stations) + "', " + str(uncertainty) + ")"

    print(sql)
    mycursor.execute(sql)
    mydb.commit()
    print(mycursor.rowcount, "record inserted.")

def storeSampelInMySQLv2(mydb, mycursor, best, worst, conveyor, carrier, stations, uncertainty):
    s1 = stations[0][1]
    s2 = stations[1][1]
    s3 = stations[2][1]
    s4 = stations[3][1]
    s5 = stations[4][1]
    s6 = stations[5][1]

    v = 2


    sql = "INSERT INTO `calculatedsamples`(`ammountOfCarriers`, `s1`, `s2`, `s3`, `s4`, `s5`, `s6`,`version`, `best`, `worst`, `conveyor`, `carrier`, `stations`, `uncertainty` ) VALUES (" + str(len(carrier)) + ", " + str(s1) + ", " + str(
        s2) + ", " + str(s3) + ", " + str(s4) + ", " + str(s5) + ", " + str(s6) + ", " + str(v) + ", " + str(best) + ", " + str(worst) + ", '" + str(conveyor) + "', '" + str(carrier) + "', '" + str(stations) + "', " + str(uncertainty) + ")"

    print(sql)
    mycursor.execute(sql)
    mydb.commit()
    print(mycursor.rowcount, "record inserted.")


def storeEvalResultInMySQL(\
    algoName,algoVersion,envVersion,envSettings,hyperparameter,
    uncertainty,ammountOfCarriers,
    earlyStoppingMethode,neededEpisods,avg_eval_score,ammountOfDatasets,
    figure_file,
    model1="", model1des="",
    model2="", model2des="",
    model3="", model3des="",
    model4="", model4des=""):


    global mysqlHost, mysqlUser, mysqlPassword, mysqlDatabase
    #Open MySql
    mydb, mycursor = openMySQL(mysqlHost, mysqlUser, mysqlPassword, mysqlDatabase)
    
    sql = "INSERT INTO `evaluierung`(\
        `algo`, `algo_version`, `env_version`, `envSettings`, `hyperparameter`, \
        `uncertainty`, `ammountOfCarriers`, \
        `earlyStoppingMethode`, `traindEpisods`, `evalValue`, `ammountOfDatasets`, \
        `plotName`, \
        `model1`, `model1des`, \
        `model2`, `model2des`, \
        `model3`, `model3des`, \
        `model4`, `model4des`) \
            VALUES (\
            %s,%s,%s,%s,%s,\
            %s,%s,\
            %s,%s,%s,%s,\
            %s,\
            %s,%s,\
            %s,%s,\
            %s,%s,\
            %s,%s )"

    mycursor.execute(sql, (
        algoName,algoVersion,envVersion,envSettings,hyperparameter,
        uncertainty,ammountOfCarriers,
        earlyStoppingMethode,neededEpisods,avg_eval_score,ammountOfDatasets,
        figure_file,
        str(model1),str(model1des), 
        str(model2),str(model2des),
        str(model3),str(model3des), 
        str(model4),str(model4des)))

    mycursor.execute(sql)
    mydb.commit()

    # DB wieder schließen        
    closemySQL(mydb)


#####################################################################
#####################################################################
# Eval-Funktionen
#####################################################################
#####################################################################

def createRandomSortedList(num, start = 1, end = 100): 
    arr = [] 
    tmp = random.randint(start, end) 
      
    for x in range(num):           
        while tmp in arr: 
            tmp = random.randint(start, end)               
        arr.append(tmp)           
    arr.sort() 
      
    return arr 
   

def getEvalDatasets(mydb, mycursor, ammountOfCarriers, ammountOfDatasets, uncertainty):

    sql = "SELECT COUNT(id) AS count FROM calculatedsamples WHERE `version` = 1 and `ammountOfCarriers` = " +str(ammountOfCarriers) + " and `uncertainty` = " + str(uncertainty)

    mycursor.execute(sql)
    myresult = mycursor.fetchall()

    count = myresult[0][0]
    print("Lade die der Evaluierungssampels")


    # zufällig EvalDatensätze laden erzeugen
    ids = createRandomSortedList(ammountOfDatasets, 1, count) 

    retVal = []
    for i in ids: 
        sql = "SELECT `s1`,`s2`,`s3`,`s4`,`conveyor`,`carrier`,`stations`,`best`,`worst` FROM `calculatedsamples` WHERE `version` = 1 and  `ammountOfCarriers` = " + str(ammountOfCarriers) + " and `uncertainty` = " + str(uncertainty) +  " ORDER BY `calculatedsamples`.`id` ASC LIMIT " + str(i) + ",1"
        mycursor.execute(sql)
        myresult = mycursor.fetchall()
        if str(myresult) == "[]":
            print("Fehler beim Laden:", sql)
        else:
            retVal.append(myresult[0])

    return retVal



def getDatasets(ammountOfCarriers, ammountOfDatasets, uncertainty, version = 1, traning=True):
    global mysqlHost, mysqlUser, mysqlPassword, mysqlDatabase

    #Open MySql
    mydb, mycursor = openMySQL(mysqlHost, mysqlUser, mysqlPassword, mysqlDatabase)

    if traning == True:
        traning = 1
    else:
        traning = 0

    sql = "SELECT `conveyor`,`carrier`,`stations`,`best`,`worst` FROM `calculatedsamples` WHERE `version` = " + str(version) + " and `ammountOfCarriers` = " + str(ammountOfCarriers) + " and `uncertainty` = " + str(uncertainty) +  " and `onlyForTraining` = " + str(traning) + " ORDER BY RAND() LIMIT "+ str(ammountOfDatasets) +";"
    mycursor.execute(sql)
    retVal = mycursor.fetchall()

    # DB wieder schließen        
    closemySQL(mydb)

    return retVal


def getDataForBoxPlot(algo,  envVersion, uncertainty, ammountOfCarriers, earlyStoppingMethode):
    global mysqlHost, mysqlUser, mysqlPassword, mysqlDatabase

    #Open MySql
    mydb, mycursor = openMySQL(mysqlHost, mysqlUser, mysqlPassword, mysqlDatabase)


    sql = "SELECT `evalValue`,`traindEpisods` FROM `evaluierung` WHERE `algo` like '"+ str(algo) +"' and env_version = "+ str(envVersion) +" and `uncertainty` = " + str(uncertainty)+ " and `ammountOfCarriers` = " + str(ammountOfCarriers) +" and `earlyStoppingMethode` like '"+ str(earlyStoppingMethode) +"' ORDER BY `evalValue` ASC" + ";"
    mycursor.execute(sql)
    retVal = mycursor.fetchall()

    # DB wieder schließen        
    closemySQL(mydb)

    return retVal