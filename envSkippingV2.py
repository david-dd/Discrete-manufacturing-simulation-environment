from base64 import encode
from cmath import inf
from enum import Flag
import time
import copy
import itertools
from xmlrpc.client import boolean
import random as rand
import numpy as np
np.random.seed(0)
from genericV4 import *
from heik import *


class myEnvironmentV2:
    
    def __init__(self, s1,s2,s3,s4,s5,s6,uncertainty, ammountOfCarriers, calcBestAndWorst=False):

        self.s1 = int(s1)
        self.s2 = int(s2)
        self.s3 = int(s3)
        self.s4 = int(s4)
        self.s5 = int(s5)
        self.s6 = int(s6)

        self.uncertainty = uncertainty
        self.ammountOfCarriers = ammountOfCarriers
        self.calcBestAndWorst = calcBestAndWorst

    def setUpEnv(self):
        
        #self.debugArrayAnfragenAntworten = {}


        self.log_probs = []
        self.values = []
        self.rewards = []

        self.stepCnt = 0
        self.operationTimesWithUncertainty = []
        self.operationTimesWithUncertainty.append(rand.randint(self.s1-self.uncertainty, self.s1+self.uncertainty))
        self.operationTimesWithUncertainty.append(rand.randint(self.s2-self.uncertainty, self.s2+self.uncertainty))
        self.operationTimesWithUncertainty.append(rand.randint(self.s3-self.uncertainty, self.s3+self.uncertainty))
        self.operationTimesWithUncertainty.append(rand.randint(self.s4-self.uncertainty, self.s4+self.uncertainty))
        self.operationTimesWithUncertainty.append(rand.randint(self.s5-self.uncertainty, self.s5+self.uncertainty))
        self.operationTimesWithUncertainty.append(rand.randint(self.s6-self.uncertainty, self.s6+self.uncertainty))

        self.stations = [
            [    #-----------------------------------------------------------
                                        # Station #1
                1,                      # 0 = Operation: A
                self.operationTimesWithUncertainty[0],      # 1 = Zeit
                1,                      # 2 = PosOnConveyor
                [],                     # 3 = StationNeighbours (index)
                False,                  # 4 = Responsible for decision polling
            ], [ #-----------------------------------------------------------
                                        # Station #2
                2,                      # Operation: B
                self.operationTimesWithUncertainty[1],      # Zeit
                7,                      # PosOnConveyor
                [2],                    # 3 = StationNeighbours (index)
                True,                   # 4 = Responsible for decision polling
            ], [ #-----------------------------------------------------------
                                        # Station #3
                2,                      # Operation: B
                self.operationTimesWithUncertainty[2],      # Zeit
                10,                     # PosOnConveyor
                [1],                    # 3 = StationNeighbours
                False,                  # 4 = Responsible for decision polling
            ], [ #-----------------------------------------------------------
                                        # Station #4
                3,                      # Operation: C
                self.operationTimesWithUncertainty[3],      # Zeit
                13,                     # PosOnConveyor
                [4],                    # 3 = StationNeighbours
                True,                   # 4 = Responsible for decision polling
            ], [ #-----------------------------------------------------------
                                        # Station #5
                3,                      # Operation: C
                self.operationTimesWithUncertainty[4],      # Zeit
                16,                     # PosOnConveyor
                [3],                    # 3 = StationNeighbours
                False,                  # 4 = Responsible for decision polling
            ], [ #-----------------------------------------------------------
                                        # Station #6
                4,                      # Operation: D
                self.operationTimesWithUncertainty[5],      # Zeit
                19,                     # PosOnConveyor
                [],                     # 3 = StationNeighbours
                False,                  # 4 = Responsible for decision polling
            ]
        ]

        self.carrier = []
        
        # Anzahl an Carriern festlegen
        #amount = rand.randint(self.ammountOfCarriers-self.uncertainty, self.ammountOfCarriers+self.uncertainty)
        amount = self.ammountOfCarriers

        # Entscheidungen für die Stationen initialiseren


        for x in range(amount):
            decisionStations = []
            for x in range(len(self.stations)):
                decisionStations.append(True)
            self.carrier.append(
                [           # Carrier #XX
                            1,                  # 0 = nextOp
                            0,                  # 1 = actPos 
                            0,                  # 2 = OpProgress
                            0,                  # 3 = stepCnt-ActionVonStation
                            (x+1),              # 4 = CarrierID
                            0,                  # 5 = CarSollWeiterbewegtWerden
                            0,                  # 6 = stepCnt-ActionVonTransportband
                            decisionStations,   # 7 = individuelle Entscheidungen für jeden Carrier
                ]
            )
    

        
        self.aadecisionForAParallelStationNeeded   = []
        self.iLastCheckDecisionsNeeded      = -1
        self.popedStationKey                = -1


        self.conveyor = [
            # Hier stehen, welche carrierIds sich in den Slots befinden...
            False,  # Pos =  1          Station 1
            False,  # Pos =  2
            False,  # Pos =  3
            False,  # Pos =  4
            False,  # Pos =  5
            False,  # Pos =  6
            False,  # Pos =  7          Station 2
            False,  # Pos =  8
            False,  # Pos =  9
            False,  # Pos =  10
            False,  # Pos =  11
            False,  # Pos =  12
            False,  # Pos =  13         Station 3
            False,  # Pos =  14
            False,  # Pos =  15
            False,  # Pos =  16
            False,  # Pos =  17
            False,  # Pos =  18
            False,  # Pos =  19         Station 4
            False,  # Pos =  20
            False,  # Pos =  21
            False,  # Pos =  22
            False,  # Pos =  23
            False,  # Pos =  24
        ]

        # Carrier zufällig auf das Transportband mappen
        # Zuerst Slots auf dem Transportband bestimmen -> diese erhaten den Wert "-1"
        for i in range(len(self.carrier)):
            foundFreeSlot = False
            while foundFreeSlot != True:
                slotID = rand.randint(1, len(self.conveyor))
                if self.conveyor[slotID-1] == False:
                    # Leeren Slot gefunden, Carrier zuweisen
                    self.conveyor[slotID-1] = -1
                    foundFreeSlot = True

        # Dann alle "-1" austausche durch CarrierID
        # Damit wird gewährleistet, das die Carrier in einer geordneten Reihenfolge sind
        for i in range(len(self.carrier)): 
            oneAdded = False
            for slotKey, slot in reversed(list((enumerate(self.conveyor)))): 
                if self.conveyor[slotKey] == -1 and oneAdded == False:
                    self.conveyor[slotKey] = i+1
                    self.carrier[i][1] = slotKey+1
                    oneAdded = True





        self.conveyorOrg = copy.deepcopy(self.conveyor) 
        self.carrierOrg = copy.deepcopy(self.carrier)
        self.stationsOrg = copy.deepcopy(self.stations)

        
        if self.calcBestAndWorst == True:
            executer = genericRunV2(self.conveyor, self.carrier, self.stations)
            self.CalculatedBestTime, self.CalculatedWorstTime = executer.getBestAndWorst()


    def exportStartingConfiguration(self):
        return [
            self.CalculatedBestTime,
            self.CalculatedWorstTime,
            self.conveyorOrg,
            self.carrierOrg,
            self.stationsOrg
        ]

    def productionFinished(self,carrier):
        retval = True
        for c in carrier:
            if (c[0] != 0):
                # nextOp ist nicht null, also müssen noch produkte gefertigt werden
                retval = False
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
    
    def calcReward(self,duration, best=False, worst=False):
        flag = False
        if best != False and worst != False:
            dividend = int(worst - duration)
            divisor = int(worst - best)
        else:
            flag = True
            dividend = int((self.CalculatedWorstTime) - duration)
            divisor = int((self.CalculatedWorstTime) - self.CalculatedBestTime)

        if divisor == int(0):
            quotient = 1.0
        else:
            quotient = dividend/divisor

        
        # Rand behandlung, weil wir die realen Zeiten nur Schätzen, und wir über den Rand gehen könnten
        if quotient >= 1:
            quotient = 1
        if quotient <= 0:
            quotient = 0
        
        if flag == True and (quotient == 0 or quotient ==1):
            dividend = int((self.CalculatedWorstTime) - duration)
            divisor = int((self.CalculatedWorstTime) - self.CalculatedBestTime)
        
            if divisor == int(0):
                quotient = 1.0
            else:
                quotient = dividend/divisor

            if quotient >= 1:
                quotient = 1
            if quotient <= 0:
                quotient = 0

        score = quotient*quotient*quotient
        reward = quotient

        return [score, reward]

    def getActualState(self):

        # 0000 conveyor slot is empty
        # 1000 carrier without a nextOp on slot
        # 1001 carrier with nextOp=1 in slot
        # 1010 carrier with nextOp=2 in slot
        # 1011 carrier with nextOp=3 in slot
        # 1100 carrier with nextOp=4 in slot

        retval = []
        for k, conv in enumerate(self.conveyor):
            if conv == False:
                # conveyor slot is empty
                retval.append(0)  # Car in Slot
                retval.append(0)  # nextOp -> 1. digit
                retval.append(0)  # nextOp -> 2. digit
                retval.append(0)  # nextOp -> 3. digit
            else:
                # der aktuelle Slot ist nicht leer -> also steht hier eine CarID drin
                # Dass wird durch das Erste Bit angezeigt
                retval.append(1)  # Car in Slot

                carID = conv
                # Nun muss in dem Array "carrier" nachgeschlagen werden, was die nächste OP ist
                nextOp = int(self.carrier[carID-1][0])  # 0 = nextOp
                strOp = intToBinary(nextOp, 3)    # Op die an der Station angeboten werden
                for x in strOp:
                    retval.append(int(x)) 

        retval = np.array(retval) #convert to np Array
        return retval
    
    def startAnEpisode(self):
        self.setUpEnv()
        return self.setpUntilNextDecision() #Finished, Reward, actualState

    def startATrainEpisode(self, conveyor, carrier, stations, best, worst):
        self.setUpEnv()
        self.conveyor = conveyor
        self.carrier = carrier
        self.stations = stations
        self.CalculatedBestTime = best
        self.CalculatedWorstTime = worst
        
        return self.setpUntilNextDecision() #Finished, Reward, actualState

    def startAnEvalEpisode(self, conveyor, carrier, stations):
        self.setUpEnv()
        self.conveyor = conveyor
        self.carrier = carrier
        self.stations = stations
        
        return self.setpUntilNextDecision() #Finished, Reward, actualState

    def step(self, action):
        # Entscheidung von der KI
        try:
            action = bool(action.item()) 
        except:
            pass
        #anfragende Station =  self.popedStationKey  
        
        #Nun muss bei der zugehörigen Station nachgeschlagen werden was diese Entscheidung bedeutet
        # 0 = ausführen bei der Anfragenden Station
        # 1 = ausführend bei der Nachbarstation mit index 0
        # ...
        # 10= ausführend bei der Nachbarstation mit index 9

        # Dnanch muss die Entscheidung zugewisen werden
        # True -> dort wo ausgeführt werden soll
        # False -> bei allen Nachbarn


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
            #exeStationKey = self.stations[self.popedStationKey][3][0] # Aktuell gibt es nur doppelte Stationen, aber keine mehrfachen Stationen, also einfach den ersten Nachbarn auswählen
            exeStationKey = stationKeys[1]
            self.carrier[carAtS][7][exeStationKey] = True


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

            if len(self.aadecisionForAParallelStationNeeded) > 0:
                self.popedStationKey = self.aadecisionForAParallelStationNeeded.pop()

                # eine Entscheidung wird benötigt, also aktuellen Zustand erfassen und Antwort abholen.
                envState = self.getActualState()
                encodeedStationKey = intToOneHotEncodedString(self.popedStationKey, len(self.stations)) 
                returnState = envState

                for x in encodeedStationKey:
                    if str(x) == str(0):
                        returnState = np.append(returnState, 0)
                    else:
                        returnState = np.append(returnState, 1)  
  
                return [False, 0, returnState]
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
                                        self.carrier[carKey][3] = self.stepCnt    # Carrier wurde behandelt...
                                else:
                                    # Auf dem Carrier wird noch keine Operation angeboten
                                    # Kann und soll die Station die nächste operation ausführen?

                                    executed = self.shouldTheNextOperationExecuted(nextOp, stationKey, carKey)                                  
                                    if executed == True:
                                        # Operation soll ausgeführt werden, also starten..
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
        
        returnState = self.getActualState() 
        for x in range(len(self.stations)):
            returnState = np.append(returnState, 0)           
        return [True, self.stepCnt, returnState] 
