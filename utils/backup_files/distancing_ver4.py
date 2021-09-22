import cv2
import itertools
import numpy as np
from utils.distancing_class import Configs, Person, Group

def calculate_distance(point1, point2):
    x1, y1 = point1
    x2, y2 = point2
    return ((x2 - x1)**2 + (y2 - y1)**2) **0.5
    
def is_valid_comparison(person1, person2):
    diffHeight = abs(person1.get_height() - person2.get_height())
    diffCoordX = abs(person1.get_coord()[0] - person2.get_coord()[0])
    diffCoordY = abs(person1.get_coord()[1] - person2.get_coord()[1])
    diffThres  = 2 * person1.get_height()
    return diffHeight < 30 and diffCoordX < diffThres and diffCoordY < diffThres


def calculate_distance_threshold(height1, height2):
    imgRatio = (height1 + height2) / (170 + 170)
    distHighRisk = 200 * imgRatio
    distLowRisk = 250 * imgRatio
    return distHighRisk, distLowRisk

def show_distancing(img, boxes, peopleList):
    config = Configs(img)
    color = config.get_colors()
    fontScale, fontThickness, lineThickness, lineType, radius = config.get_figure()

    isFirstFrame = (len(peopleList) == 0)

    for box in boxes:
        ## new data
        pLeft, pTop, pRight, pBot = box
        height = int(pBot - pTop)
        newCoord = (int(pLeft + pRight) //2, int(pBot))  # bottom

        if isFirstFrame:
            peopleList.append(Person(height, newCoord))

        ## update coord
        else :
            minDistance = 30
            minDistanceIdx = -1

            for idx, person in enumerate(peopleList):
                if person.get_updated() is True:
                    continue

                distance = calculate_distance(newCoord, person.get_coord())
                if minDistance > distance:
                    minDistance = distance
                    minDistanceIdx = idx
            
            if minDistanceIdx == -1:
                newPerson = Person(height, newCoord)
                newPerson.set_updated(True)
                peopleList.append(newPerson)
            else :
                peopleList[minDistanceIdx].set_height(height)
                peopleList[minDistanceIdx].set_coord(newCoord)
                peopleList[minDistanceIdx].set_updated(True)
        
        cv2.circle(img, newCoord, config.radius, color.green, -1) ## bottom circle 2
        #cv2.putText(img, str(id), (pLeft, pTop), 0, fontScale, colorBlue, fontThickness, lineType) ##
        #cv2.putText(img, str(height), (pLeft, pTop), 0, tl / 3, colorBlue, thickness=tf, lineType=cv2.LINE_AA) ##

    ## remove people not updated
    newPeopleList = []
    notUpdateList = [] ## people undetected
    for person in peopleList:
        if person.get_updated() is True:
            person.set_updated(False)
            newPeopleList.append(person)
            cv2.putText(img, str(person.get_redCount()), person.get_coord(), 0, fontScale, color.red, fontThickness, lineType) 
        elif not person.is_erasable(img.shape[:2]):
            notUpdateList.append(person)
    peopleList = newPeopleList

    ## make combinations of idx
    peopleIdx = list(range(len(peopleList))) ## 0, 1, 2, ..... , peopleList length
    peopleIdxCombi = list(itertools.combinations(peopleIdx, 2))

    group = Group(len(peopleList))

    for idx1, idx2 in peopleIdxCombi:
        if group.is_same(idx1, idx2):
            continue

        person1 = peopleList[idx1]
        person2 = peopleList[idx2]

        ## Ignore Perspective
        if not is_valid_comparison(person1, person2):
            continue

        ## get distance info
        dist = calculate_distance(person1.get_coord(), person2.get_coord())
        distHighRisk, distLowRisk = calculate_distance_threshold(person1.get_height(), person2.get_height())  ## Calculate with Image Ratio

        ## high risk
        if dist < distHighRisk:
            group.attach(idx1, idx2)
            if not person1.get_updated():
                person1.inc_redCount()
                person1.set_updated(True)
            if not person2.get_updated():
                person2.inc_redCount()
                person2.set_updated(True)
            
            #cv2.line(img, person1.get_coord(), person2.get_coord(), color.red, lineThickness)
            cv2.circle(img, person1.get_coord(), radius, color.red, -1)
            cv2.circle(img, person2.get_coord(), radius, color.red, -1)

        ## low risk
        elif dist >= distHighRisk and dist < distLowRisk:
            if not person1.get_updated():
                group.detach(idx1)
                person1.clear_redCount()
            if not person2.get_updated():
                group.detach(idx2)
                person2.clear_redCount()
            
            cv2.line(img, person1.get_coord(), person2.get_coord(), color.yellow, lineThickness)
            if not person1.is_red():
                cv2.circle(img, person1.get_coord(), radius, color.yellow, -1)
            if not person2.is_red():
                cv2.circle(img, person2.get_coord(), radius, color.yellow, -1)

    for id in range(len(group.parent)):
        subGroup = group.get_sub(id)

        if len(subGroup) < 2:
            continue

        polyCoords = []
        for idx in subGroup:
            polyCoords.append(peopleList[idx].get_coord())


        polyCoords = np.int32([np.array(polyCoords)])

       # cv2.polylines(img, polyCoords, True, color.blue, lineThickness, lineType)
        #cv2.fillPoly(img, polyCoords, color.blue)
        overlay = img.copy()
        opacity = 0.3
        cv2.fillPoly(overlay, polyCoords, color.red)
        cv2.addWeighted(overlay, opacity, img, 1 - opacity, 0, img)

    for idx in peopleIdx:
        if not peopleList[idx].get_updated():
            peopleList[idx].clear_redCount()
        else :
            if peopleList[idx].is_definite_risk():
                x, y = peopleList[idx].get_coord()
                x -= 30
                y -= peopleList[idx].get_height()
                cv2.putText(img, "RISK", (x, y), 0, fontScale, color.red, fontThickness, lineType)
            peopleList[idx].set_updated(False)
    
    peopleList.append(notUpdateList)

    return img
