from cmath import inf
import time
import copy
import itertools
from xmlrpc.client import boolean
from heik import *

class genericRunV2:

    def __init__(self, conv, car, stations):
        #print("INIT GernericV2")
        
        self.conveyorOrg = copy.deepcopy(conv)
        self.carrierOrg = copy.deepcopy(car)
        self.stationsOrg = copy.deepcopy(stations)

        self.fixedActions = self.generateAllPosibleActions(len(car))
        #print("länge",len(self.fixedActions))
        #print(self.fixedActions)
        #die()

    def getBestAndWorst(self):
        self.resultOfAllRuns = []
        
        for f in self.fixedActions:
            self.resetVars()
            duration = self.makeARun(f)
            self.resultOfAllRuns.append([duration,f])
            #print(duration, f)
       


        # Auswertung der Experimente
        worstTime = 0
        bestTime = inf
        for x in self.resultOfAllRuns:
            #print(x[0])
            if x[0] < bestTime:
                bestTime = x[0]
            if x[0] > worstTime:
                worstTime = x[0]
        
        #print("Durchlaufzeiten der Maschienen", self.stations[0][1],self.stations[1][1],self.stations[2][1],self.stations[3][1], "Beste Zeit", bestTime, "Schlimmste Zeit",worstTime)
        return [bestTime,worstTime]

    def generateAllPosibleActions(self, amountOfProducts):
        l = [0,1]
        res = list(itertools.product(l, repeat=2))
        res2 = list(itertools.product(res, repeat=amountOfProducts))
    
        return res2

    
    def resetVars(self):

        self.stepCnt = 0

        self.conveyor = copy.deepcopy(self.conveyorOrg) 
        self.carrier = copy.deepcopy(self.carrierOrg)
        self.stations = copy.deepcopy(self.stationsOrg)

        self.aadecisionForAParallelStationNeeded   = []
        self.iLastCheckDecisionsNeeded      = -1
        self.popedStationKey                = -1


    def productionFinished(self,carrier):
        retval = True
        for c in carrier:
            if (c[0] != 0):
                # nextOp ist nicht null, also müssen noch produkte gefertigt werden
                retval = False
                #print("NOT FINISHED")
                return retval


    def getCarrierAtStation(self, keyForStation):
        # Return CarKey
        
        carAtS = False # carKey, oder False  

        # Wir müssen erfahren, für welche Stationen eine Entscheidung getroffen werden muss 
        for k, carIdOnConveyor in (enumerate(self.conveyor)): 
            if carIdOnConveyor != False: 
                # Nur Slot betrachten, in denen sich auch Carrier befinden...
                slotID = k + 1
                carKey = carIdOnConveyor-1

                for stationKey, station in enumerate(self.stations): 
                    if (int(slotID) == int(station[2])):    # conveyorSlot == Position der Station
                        # Der Carrier befindet sich an einer Station
                        if stationKey == keyForStation:
                            # Der Carrier befindet sich an der Station 2
                            carAtS = carKey
        return carAtS

    def decisionForAParallelStationNeeded(self):

        retVal = []

        for k, station in (enumerate(self.stations)): 
            carAtS = self.getCarrierAtStation(k) # get carKey at Station
            if str(carAtS) == "False":
                # Kein Carrier an der Station, also wird hier auch keine Entscheidung benötigt
                pass
            else:
                if station[4] == True:
                    #      4 = Responsible for decision polling
                    # Die Station darf eine Entscheidung von der KI anfodern 
                    


                    #Ermitteln, ob die Bearbeitung noch nicht begonenn hat        
                    #               NextOp != 0 UND OpProgress == 0
                    if self.carrier[carAtS][0] != 0 and self.carrier[carAtS][2] == 0:
                        # Ermitteln, ob die nächste op auf dem Carrier auch von der Station angeboten wird
                        if self.carrier[carAtS][0] == station[0]: # Operation: B
                            #print("Nicht weiter simulieren, wir brauchen eine Entscheidung!" , "Carrier#" , carAtS2," an Station2 mit NextOp:" , self.carrier[carAtS2][0])
                            #print("stationKey", k, "carAtS", carAtS, "nextOP", self.carrier[carAtS][0], "Progress", self.carrier[carAtS][2]) 
                            retVal.append(k) # Stationkeys
        return retVal
        


    def getFollowingOperation(self,actOp):
        retVal = 0
        if actOp == 0:
            retVal = 0
        else:
            retVal = actOp + 1
            if retVal == 5:
                retVal = 0
        return retVal
    
    def shouldTheNextOperationExecuted(self, nextOp, stationKey, carrierKey):
        #print(self.executeOpForCarrier)
        if nextOp == 0:
            return False
        else: 
            # Prüfen, ob die Staion die Operation überhaupt ausführen kann
            #        Operation An Station   == die nächste Operation die auf dem Carrier ausgeführt werden soll
            if self.stations[stationKey][0] == nextOp:
                # Die Operation kann an der Station ausgeführt werden, 
                # aber soll sie das auch?
                # Nachschlagen in der Entscheidungsliste (hängt am Carrier)                
                return self.carrier[carrierKey][7][stationKey]
            else:
                # Die Operation kann hier nicht ausgeführt werden... 
                return False

    def getActionFromStaticDecisions(self, entscheidungen, stationK,carK):        
        #print(entscheidungen)
        stationIndex = 99
        if stationK == 1:
            stationIndex = 0
        elif stationK == 3:
            stationIndex = 1

        action = entscheidungen[carK][0]

        return action

    def makeARun(self,entscheidungen):   
        done, duration, stationK,carK = self.startAnEpisode()

        while not done:
            action = self.getActionFromStaticDecisions(entscheidungen, stationK,carK)    
            done, duration, stationK,carK = self.step(action)    
        
        #print("entscheidungen:" , entscheidungen, "Dauer:" , self.stepCnt)
        return self.stepCnt 

    def startAnEpisode(self):
        self.resetVars()
        return self.setpUntilNextDecision() #Finished, Reward, actualState

    def step(self, action):
        # action = Entscheidung von der KI

        # 1 # Erfassen aller StationKeys, die die Operation ausführen könenn 
        stationKeys = [self.popedStationKey]
        for x in self.stations[self.popedStationKey][3]:
            stationKeys.append(x)
                
        # 2 # alle Stationen die die Operation auch ausführen sollen nun erstmal zurücksetzten
        carAtS = self.getCarrierAtStation(self.popedStationKey) 
        for x in stationKeys:
            self.carrier[carAtS][7][x] = False

        # 3 # die richtige Station setzten
        if action == False:
            self.carrier[carAtS][7][self.popedStationKey] = True  # Die anfragende Station soll die Operation ausführen
        else:
            exeStationKey = self.stations[self.popedStationKey][3][0] # Aktuell gibt es nur doppelte Stationen, aber keine mehrfachen Stationen, also einfach den ersten Nachbarn auswählen
            self.carrier[carAtS][7][exeStationKey] = True

        #print("die Entscheiudngen für den Carrier mit Key=", carAtS, "Entscheidungen", str(self.carrier[carAtS][7]))
        return self.setpUntilNextDecision() #Finished, Reward, actualState
        
    def setpUntilNextDecision(self):
        #Gibt folgendes zurück
        # 0 = Finished
        # 1 = Reward
        # 2 = actualState

        while self.productionFinished(self.carrier) == False:     

            # Abfrage, ob neue Entscheidungen benötigt werden
            if self.stepCnt >= self.iLastCheckDecisionsNeeded:
                self.aadecisionForAParallelStationNeeded = self.decisionForAParallelStationNeeded()
                self.iLastCheckDecisionsNeeded = self.stepCnt+1
                #print("self.aadecisionForAParallelStationNeeded", self.aadecisionForAParallelStationNeeded)

            if len(self.aadecisionForAParallelStationNeeded) > 0:
                self.popedStationKey = self.aadecisionForAParallelStationNeeded.pop()
                """
                # eine Entscheidung wird benötigt, also aktuellen Zustand erfassen und Antwort abholen.
                envState = self.getActualState()
                encodeedStationKey = intToOneHotEncodedString(self.popedStationKey, len(self.stations)) 
                returnState = envState
                #print("self.popedStationKey", self.popedStationKey)
                #print("returnState", returnState)
                for x in encodeedStationKey:
                    if str(x) == str(0):
                        returnState = np.append(returnState, 0)
                    else:
                        returnState = np.append(returnState, 1)        
                #return [False, 0, returnState]
                """
                #Anpassung an Generic
                actCarKey = self.getCarrierAtStation(self.popedStationKey) 
                return [False, 0, self.popedStationKey, actCarKey]
            else:
                 
                
                self.stepCnt += 1
                # Update der Stationen
                for k, carIdOnConveyor in (enumerate(self.conveyor)): 
                    if carIdOnConveyor != False:             
                        # Nur Slot betrachten, in denen sich auch Carrier befinden...    
                        carKey = carIdOnConveyor-1       
                        lastCarUpdate = self.carrier[carKey][3]


                        if lastCarUpdate < self.stepCnt:
                            slotID = k + 1
                            nextSlotID = slotID +1
                            # In diesem Schritt wurde noch keine Aktionfür den Carrier ausgeführt
                            

                            self.carrier[carKey][5] = False         # CarSollWeiterbewegtWerden
                            if nextSlotID > len(self.conveyor):
                                nextSlotID = 1
                            

                            # befindet sich der Carrier an einer Station?
                            carAtStation = False 
                            for stationKey, station in enumerate(self.stations): 
                                if (int(slotID) == int(station[2])):
                                    carAtStation = True
                                    break # Wir haben eine Station gefunden, an weiteren Stationen kann der Carrier nicht sein

                            
                            if carAtStation == True:
                                # Der Carrer befindet sich an einer Station
                                nextOp = self.carrier[carKey][0]
                                # wird gerade eine Operation auf dne Carrier angewendet?
                                if self.carrier[carKey][2] > 0:
                                    # Auf dem Carrier wird eine Operation ausgeführt!
                                    # Ist die Operation vorbei?
                                    if self.carrier[carKey][2] >= station[1]:
                                        # Operation ist vollendet, der Carrier kann die Station verlassen...
                    

                                        opFinished = True                        
                                        nextOp = self.getFollowingOperation(nextOp)
                                        self.carrier[carKey][0] = nextOp            # Set the following operation
                                        self.carrier[carKey][2] = 0                 # Reset Progress
                                        self.carrier[carKey][3] = self.stepCnt      # Carrier wurde behandelt...
                                        self.carrier[carKey][5] = True              # CarSollWeiterbewegtWerden
                                        
                                    else:
                                        # Operation noch nicht vollendet, also Progress erhöhen...
                                        self.carrier[carKey][2] = self.carrier[carKey][2]+1               
                                        #print("Carrier:",car, "Ausführen der Operation" , nextOp, "Fortschritt" , carrier[carKey][2])             
                                        self.carrier[carKey][3] = self.stepCnt    # Carrier wurde behandelt...
                                else:
                                    # Auf dem Carrier wird noch keine Operation angeboten
                                    # Kann und soll die Station die nächste operation ausführen?

                                    executed = self.shouldTheNextOperationExecuted(nextOp, stationKey, carKey)
                                    if executed == True:
                                        # Operation soll ausgeführt werden, also starten..
                                        #print("Carrier:",car, "Ausführen der Operation" , nextOp, "Fortschritt" , 1)
                                        self.carrier[carKey][2] = 1
                                        self.carrier[carKey][3] = self.stepCnt    # Carrier wurde behandelt...
                                    else:
                                        # operation, soll nicht ausgeführt werden, also weiterschicken... 
                                        self.carrier[carKey][3] = self.stepCnt      # Carrier wurde behandelt...
                                        self.carrier[carKey][5] = True              # CarSollWeiterbewegtWerden

                            else:
                                # Der Carrier befindt sich an keiner Stationm, also einfach weitertransporieren...
                                self.carrier[carKey][3] = self.stepCnt      # Carrier wurde behandelt...
                                self.carrier[carKey][5] = True              # CarSollWeiterbewegtWerden

                # Update des Transportbandes
                for a in range(2):
                    for k, carIdOnConveyor in (enumerate(self.conveyor)): 
                        if carIdOnConveyor != False: 
                            carKey = carIdOnConveyor-1
                            lastConveyorUpdate = self.carrier[carKey][6]    

                            if lastConveyorUpdate < self.stepCnt:

                                nextConveyorKey = k + 1
                                if nextConveyorKey > len(self.conveyor)-1:
                                    nextConveyorKey = 0


                                # den Carrier weitertransporieren, wenn gewünscht und Slot vor ihm nicht belegt ist ist.
                                if self.carrier[carKey][5] == True and self.conveyor[nextConveyorKey] == False:
                                    self.conveyor[k]                 = False                # Aktuellen Slot leeren
                                    self.conveyor[nextConveyorKey]   = carIdOnConveyor      # nächsten Slot mit dem Wert aus dem aktuellen Slot setzten
                                    self.carrier[carKey][6] = self.stepCnt                  # Carrier wurde behandelt...
        
        #envState = self.getActualState()   
        #for x in range(len(self.stations)):
        #    returnState = np.append(returnState, 0)
        # Anpassung           
        return [True, self.stepCnt, 0, 0] 
