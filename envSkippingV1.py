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

from genericV1 import *
from heik import *


class myEnvironmentV1:
    
    def __init__(self, s1,s2,s3,s4,uncertainty, ammountOfCarriers, calcBestAndWorst=False):
        self.s1 = int(s1)
        self.s2 = int(s2)
        self.s3 = int(s3)
        self.s4 = int(s4)

        self.uncertainty = uncertainty
        self.ammountOfCarriers = ammountOfCarriers
        self.calcBestAndWorst = calcBestAndWorst

    
    def setUpEnv(self):

        self.decisionOnStation2 = -1

        self.log_probs = []
        self.values = []
        self.rewards = []

        self.stepCnt = 0
        self.operationTimesWithUncertainty = []
        self.operationTimesWithUncertainty.append(rand.randint(self.s1-self.uncertainty, self.s1+self.uncertainty))
        self.operationTimesWithUncertainty.append(rand.randint(self.s2-self.uncertainty, self.s2+self.uncertainty))
        self.operationTimesWithUncertainty.append(rand.randint(self.s3-self.uncertainty, self.s3+self.uncertainty))
        self.operationTimesWithUncertainty.append(rand.randint(self.s4-self.uncertainty, self.s4+self.uncertainty))


        self.carrier = []
        amount = rand.randint(self.ammountOfCarriers-self.uncertainty, self.ammountOfCarriers+self.uncertainty)
        amount = self.ammountOfCarriers
        for x in range(amount):
            self.carrier.append(
                [           # Carrier #XX
                            1,      # 0 = nextOp
                            0,      # 1 = actPos 
                            0,      # 2 = OpProgress
                            0,      # 3 = stepCnt-ActionVonStation
                            (x+1),  # 4 = CarrierID
                            0,      # 5 = CarSollWeiterbewegtWerden
                            0,      # 6 = stepCnt-ActionVonTransportband
                ]
            )
    


        self.stations = [
            [                           # Station #1
                1,                      # 0 = Operation: A
                self.operationTimesWithUncertainty[0],      # 1 = Zeit
                1,                      # 2 = PosOnConveyor
            ], [                         # Station #2
                2,                      # Operation: B
                self.operationTimesWithUncertainty[1],      # Zeit
                7,                      # PosOnConveyor
            ], [                         # Station #3
                2,                      # Operation: B
                self.operationTimesWithUncertainty[2],      # Zeit
                13                      # PosOnConveyor
            ], [                         # Station #4
                3,                      # Operation: C
                self.operationTimesWithUncertainty[3],      # Zeit
                19                      # PosOnConveyor
            ]
        ]

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

        self.executeOpForCarrier = []

        for c in self.carrier:
            self.executeOpForCarrier.append(True)

        self.decisions = []
        self.decisionsEval = []

        self.fileName = str(self.s1) + "-" + str(self.s2) + \
            "-" + str(self.s3) + "-" + str(self.s4)

        self.tempReward = []

        # Carrier zufällig mappen
        for i in range(len(self.carrier)):
            foundFreeSlot = False
            while foundFreeSlot != True:
                slotID = rand.randint(1, len(self.conveyor))
                if self.conveyor[slotID-1] == False:
                    # Leeren Slot gefunden, Carrier zuweisen
                    self.conveyor[slotID-1] = -1
                    foundFreeSlot = True

        for i in range(len(self.carrier)): 
            oneAdded = False
            for slotKey, slot in reversed(list((enumerate(self.conveyor)))): 
                if self.conveyor[slotKey] == -1 and oneAdded == False:
                    self.conveyor[slotKey] = i+1
                    self.carrier[i][1] = slotKey+1
                    oneAdded = True

        for k, s in enumerate(self.stations): 
            self.operationTimesWithUncertainty[k] = s[1]

        self.conveyorOrg = copy.deepcopy(self.conveyor) 
        self.carrierOrg = copy.deepcopy(self.carrier)
        self.stationsOrg = copy.deepcopy(self.stations)

        if self.calcBestAndWorst == True:
            executer = genericRunV1(self.conveyor, self.carrier, self.stations)
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


    def getCarrierAtStation2(self):
        carAtS2 = False # carKey, oder False  
        carKey = -99
        keyForStation2 = 1
        # Wir müssen erfahren, für welche Stationen eine Entscheidung getroffen werden muss 
        for k, carIdOnConveyor in (enumerate(self.conveyor)): 
            if carIdOnConveyor != False: 
                # Nur Slot betrachten, in denen sich auch Carrier befinden...
                slotID = k + 1
                carKey = carIdOnConveyor-1

                for stationKey, station in enumerate(self.stations): 
                    if (int(slotID) == int(station[2])):    # conveyorSlot == Position der Station
                        # Der Carrier befindet sich an einer Station
                        if stationKey == keyForStation2:
                            # Der Carrier befindet sich an der Station 2
                            carAtS2 = carKey
        return carAtS2

    def decisionNeededForStation2Needed(self):
        decisionNeededForStation2 = False   

        carAtS2 = self.getCarrierAtStation2()
        if str(carAtS2) == "False":
            pass
        else:
            #Ermitteln, ob die Bearbeitung bereits begonenn hat        
            #               NextOp != 0 UND OpProgress == 0
            if self.carrier[carAtS2][0] != 0 and self.carrier[carAtS2][2] == 0:
                # mit NextOp:" , self.carrier[carAtS2][0])
                if self.carrier[carAtS2][0] == self.stations[1][0]: # Operation: B
                    decisionNeededForStation2 = True

        return decisionNeededForStation2
        


    def getFollowingOperation(self,actOp):
        retVal = 0
        if actOp == 0:
            retVal = 0
        else:
            retVal = actOp + 1
            if retVal == 4:
                retVal = 0
        return retVal
    
    def shouldTheNextOperationExecuted(self, nextOp, stationKey, carrierKey):
        if nextOp == 0:
            return False
        else: 
            # Prüfen, ob die Staion die Operation überhaupt ausführen kann
            #        Operation An Station == die nächste Operation laut Arbeitsplan
            if self.stations[stationKey][0]    == nextOp:
                # Die Operation kann an der Station ausgeführt werden, 
                # aber soll sie das auch?
                # Nachschlagen in der Entscheidungsliste-> executeOpForCarrier
                return self.executeOpForCarrier[carrierKey]
            else:
                # Die Operation kann hier nicht ausgeführt werden... 
                return False
    
    def calcReward(self,duration, best=False, worst=False):

        if best != False and worst != False:
            dividend = int(worst - duration)
            divisor = int(worst - best)
        else:
            dividend = int(self.CalculatedWorstTime - duration)
            divisor = int(self.CalculatedWorstTime - self.CalculatedBestTime)
            
        if divisor == int(0):
            quotient = 1.0
        else:
            quotient = dividend/divisor
        
        # Rand behandlung, weil wir die realen Zeiten nur Schätzen, und wir über den Rand gehen könnten
        if quotient >= 1:
            quotient = 1
        if quotient <= 0:
            quotient = 0

        score = quotient*quotient*quotient
        reward = quotient

        return [score, reward]

    def getActualState(self):

        # 000 conveyor slot is empty
        # 100 carrier without a nextOp on slot
        # 101 carrier with nextOp=1 in slot
        # 110 carrier with nextOp=2 in slot
        # 111 carrier with nextOp=3 in slot

        retval = []
        for conv in self.conveyor:
            if conv == False:
                # conveyor slot is empty
                retval.append(0)  # Car in Slot
                retval.append(0)  # nextOp -> 1. digit
                retval.append(0)  # nextOp -> 2. digit
            else:
                # der aktuelle Slot ist nicht leer -> also stht hier eine CarID drin
                # Dass wird durch das Erste Bit angezeigt
                retval.append(1)  # Car in Slot

                carID = conv
                # Nun muss in dem Array "carrier" nachgeschlagen werden, was die nächste OP ist
                nextOp = int(self.carrier[carID-1][0])  # 0 = nextOp
                if nextOp == int(0):
                    retval.append(0)  # nextOp -> 1. digit
                    retval.append(0)  # nextOp -> 2. digit
                elif nextOp == int(1):
                    retval.append(0)  # nextOp -> 1. digit
                    retval.append(1)  # nextOp -> 2. digit
                elif nextOp == int(2):
                    retval.append(1)  # nextOp -> 1. digit
                    retval.append(0)  # nextOp -> 2. digit
                elif nextOp == int(3):
                    retval.append(1)  # nextOp -> 1. digit
                    retval.append(1)  # nextOp -> 2. digit

        retval = np.array(retval) #vonvert to np Array
        return retval
    
    def startAnEpisode(self):
        self.setUpEnv()
        return self.setpUntilNextDecision(False)

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
        return self.setpUntilNextDecision(False)

    def step(self, action):
        self.decisionOnStation2 = action
        self.updateExecuteOpForCarrier()
        return self.setpUntilNextDecision(True)
        

    def updateExecuteOpForCarrier(self):
        retVal = []
        for c in self.carrier:
            retVal.append(True)

        if self.decisionOnStation2 != -1:
            carAtS2 = self.getCarrierAtStation2()    
            retVal[carAtS2] = self.decisionOnStation2
        self.executeOpForCarrier = retVal   
        
        
    def setpUntilNextDecision(self, decisionApplyed=False):
        #Gibt folgendes zurück
        # 0 = Finished
        # 1 = Reward
        # 2 = actualState
        while self.productionFinished(self.carrier) == False:
            isADecisionNeededForStation2Needed = self.decisionNeededForStation2Needed()

            if isADecisionNeededForStation2Needed == True and decisionApplyed == False:
                # eine Entscheidung wird benötigt, also aktuellen Zustand erfassen und Antwort abholen.
                envState = self.getActualState()
                return [False, 0, envState]
            else:

                if decisionApplyed == False:
                    # Das Array wurde für diesen Zeitschritt bereits zurückgesetzt
                    self.decisionOnStation2 = -1    
                    self.updateExecuteOpForCarrier() # Die Entscheidungen wieder zurücksetzten, damit andere Stationen die Aufgaben erfüllen können. 
                
                self.stepCnt += 1
                decisionApplyed = False
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
        
        envState = self.getActualState()                
        return [True, self.stepCnt, envState] 
