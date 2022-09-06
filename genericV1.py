from cmath import inf
import time
import copy
import itertools
from xmlrpc.client import boolean


class genericRunV1:


    def __init__(self, conv, car, stations):
       
        self.conveyorOrg = copy.deepcopy(conv)
        self.carrierOrg = copy.deepcopy(car)
        self.stationsOrg = copy.deepcopy(stations)
        self.fixedActions = self.generateAllPosibleActions(len(car))
        self.gantt=[]

    def getBestAndWorst(self):
        self.resultOfAllRuns = []
        
        for f in self.fixedActions:
            self.resetVars()
            duration = self.makeARun(f)
            self.resultOfAllRuns.append([duration,f])
     
        # Auswertung der Experimente
        worstTime = 0
        bestTime = inf
        for x in self.resultOfAllRuns:
            if x[0] < bestTime:
                bestTime = x[0]
            if x[0] > worstTime:
                worstTime = x[0]
        
        #print(self.gantt)
        return [bestTime,worstTime]

    def generateAllPosibleActions(self, amountOfProducts):
        l = [0, 1]
        res = list(itertools.product(l, repeat=amountOfProducts))
        return res

    
    def resetVars(self):

        self.stepCnt = 0

        self.conveyor = copy.deepcopy(self.conveyorOrg) 
        self.carrier = copy.deepcopy(self.carrierOrg)
        self.stations = copy.deepcopy(self.stationsOrg)


        self.executeOpForCarrier = []



    def productionFinished(self,carrier):
        retval = True
        for c in carrier:
            if (c[0] != 0):
                # nextOp ist nicht null, also müssen noch produkte gefertigt werden
                retval = False
                return retval

    def getExecutionActions(self, oldState, stepCnt, carrier, conveyor, stations, entscheidungen):
        # Init, soll die Operation auf dem Carrier ausgeführt werden?
        # Immer, ja, außer der Carrier ist an Station 2, dort bitte Nachfragen!
        
        decisionNeededForStation2 = False   
        keyForStation2 = 1
        carAtS2 = False # carKey, oder False  
        carKey = -99

        retVal = []
        for c in carrier:
            retVal.append(True)

        # Wir müssen erfahren, für welche Stationen eine Entscheidung getroffen werden muss 
        for k, carIdOnConveyor in (enumerate(conveyor)): 
            if carIdOnConveyor != False: 
                # Nur Slot betrachten, in denen sich auch Carrier befinden...
                slotID = k + 1
                carKey = carIdOnConveyor-1

                for stationKey, station in enumerate(stations): 
                    if (int(slotID) == int(station[2])):    # conveyorSlot == Position der Station
                        # Der Carrier befindet sich an einer Station
                        if stationKey == keyForStation2:
                            # Der Carrier befindet sich an der Station 2
                            carAtS2 = carKey

        if str(carAtS2) == "False":
            # An der Station befindet sich kein Carrier
            # alten Wert einfach wieder zurückgeben
            return retVal
        else:
            #Ermitteln, ob die Bearbeitung bereits begonenn hat        
            #               NextOp != 0 UND OpProgress == 0
            if self.carrier[carAtS2][0] != 0 and self.carrier[carAtS2][2] == 0:
                # mit NextOp:" , self.carrier[carAtS2][0])
                if self.carrier[carAtS2][0] == self.stations[1][0]: # Operation: B
                    decisionNeededForStation2 = True

    
        if decisionNeededForStation2 == True:
            retVal[carAtS2] = bool(entscheidungen[carAtS2])
        return retVal

    def getFollowingOperation(self,actOp):
        retVal = 0
        if actOp == 0:
            retVal = 0
        else:
            retVal = actOp + 1
            if retVal == 4:
                retVal = 0
        return retVal
    
    def shouldTheNextOperationExecuted(self, nextOp, stationKey, carrierKey, executeOpForCarrier, stations):
        # ANMERKUNG:
        # Diese Funktion ist eigentlich unnötig, da in getExecutionActions bereits auf die richtige Station gepürft wird... 
        if nextOp == 0:
            return False
        else: 
            # Prüfen, ob die Staion die Operation überhaupt ausführen kann
            #        Operation An Station == die nächste Operation laut Arbeitsplan
            if stations[stationKey][0]    == nextOp:
                # Die Operation kann an der Station ausgeführt werden, 
                # aber soll sie das auch?
                # Nachschlagen in der Entscheidungsliste-> executeOpForCarrier
                return executeOpForCarrier[carrierKey]
            else:
                # Die Operation kann hier nicht ausgeführt werden... 
                return False
    

    def makeARun(self,entscheidungen):   
        self.gantt.append([])
        ganttI = len(self.gantt)-1
        for c in self.carrier:
            self.gantt[ganttI].append("")

        while self.productionFinished(self.carrier) == False:
            self.stepCnt += 1
            self.executeOpForCarrier = self.getExecutionActions(self.executeOpForCarrier, self.stepCnt, self.carrier, self.conveyor, self.stations, entscheidungen)
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
                                    self.carrier[carKey][3] = self.stepCnt    # Carrier wurde behandelt...

                                    self.gantt[ganttI][carKey]=self.gantt[ganttI][carKey] + str(stationKey)
                            else:
                                # Auf dem Carrier wird noch keine Operation angeboten
                                # Kann und soll die Station die nächste operation ausführen?

                                executed = self.shouldTheNextOperationExecuted(nextOp, stationKey, carKey, self.executeOpForCarrier, self.stations)
                                if executed == True:
                                    # Operation soll ausgeführt werden, also starten..
                                    self.carrier[carKey][2] = 1
                                    self.carrier[carKey][3] = self.stepCnt    # Carrier wurde behandelt...
                                    
                                    self.gantt[ganttI][carKey]=self.gantt[ganttI][carKey] + str(stationKey)
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
                            nextConveyorID = nextConveyorKey +1
                            if nextConveyorKey > len(self.conveyor)-1:
                                nextConveyorKey = 0
                                nextConveyorID = 1


                            # den Carrier weitertransporieren, wenn gewünscht und Slot vor ihm nicht belegt ist ist.
                            if self.carrier[carKey][5] == True and self.conveyor[nextConveyorKey] == False:
                                self.conveyor[k]                 = False                # Aktuellen Slot leeren
                                self.conveyor[nextConveyorKey]   = carIdOnConveyor      # nächsten Slot mit dem Wert aus dem aktuellen Slot setzten
                                self.carrier[carKey][1] = nextConveyorID
                                self.carrier[carKey][6] = self.stepCnt                  # Carrier wurde behandelt...
                                self.gantt[ganttI][carKey]=self.gantt[ganttI][carKey] + "_"
                            elif self.carrier[carKey][5] == True and self.conveyor[nextConveyorKey] != False:
                                if len(self.gantt[ganttI][carKey])+1 < self.stepCnt:
                                    if self.carrier[carKey][0] == False:
                                        self.gantt[ganttI][carKey]=self.gantt[ganttI][carKey] + "_"
                                    else:
                                        self.gantt[ganttI][carKey]=self.gantt[ganttI][carKey] + "W"
    
        return self.stepCnt 


