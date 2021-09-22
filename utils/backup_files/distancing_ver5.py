import cv2
import itertools
import numpy as np
from utils.distancing_class import Configs, Person, IdTable

def is_valid(person1, person2):
    diffThres  = person1.get_height() + person2.get_height()
    return  abs(person1.get_height()   - person2.get_height())   < 30        and \
            abs(person1.get_coord()[0] - person2.get_coord()[0]) < diffThres and \
            abs(person1.get_coord()[1] - person2.get_coord()[1]) < diffThres

def find_parent(peopleList, person):
    if person.get_pid() != person.get_id():
        pid = find_parent(peopleList, peopleList[person.get_pid()])
        peopleList[person.get_id()].set_pid(pid)
    return person.get_pid()

def find_parentId(idTable, person):
    personId, parentId = idTable.get_ids(person)
    if parentId == personId:
        return parentId
    else :
        parent = idTable.get_parent(parentId)
        parentId = find_parentId(idTable, parent)
        idTable.set_parentId(person, parentId)
        return parentId
        
def union_people(idTable, person1, person2):
    parentId1 = 

def union_parent(peopleList, person1, person2):
    pid1 = person1.get_pid()
    pid2 = person2.get_pid()
    peopleList[pid2].set_pid(pid1)
    return

def is_same_group(peopleList, person1, person2):
    return (find_parent(peopleList, person1) == find_parent(peopleList, person2))

def calculate_distance(point1, point2):
    x1, y1 = point1
    x2, y2 = point2
    return ((x2 - x1)**2 + (y2 - y1)**2) **0.5

def calculate_distance_threshold(height1, height2):
    pixelRatio = (height1 + height2) / (170 + 170)
    distHighRisk = 200 * pixelRatio
    distLowRisk  = 250 * pixelRatio
    return distHighRisk, distLowRisk

def show_distancing(img, boxes, oldPeopleList, idCandidate):
    config = Configs(img)
    color = config.get_colors()
    fontScale, fontThickness, lineThickness, lineType, radius = config.get_figure()

    print(len(oldPeopleList))
    peopleList = []

    ## first frame
    if len(oldPeopleList) == 0:
        for id, box in enumerate(boxes):
            pLeft, pTop, pRight, pBot = box
            height = int(pBot - pTop)
            newCoord = (int(pLeft + pRight) //2, int(pBot))  # bottom
            peopleList.append(Person(id, height, newCoord))

    ## next frame
    else :
        newId = len(oldPeopleList)

        for box in boxes:
            pLeft, pTop, pRight, pBot = box
            height = int(pBot - pTop)
            coord = (int(pLeft + pRight) //2, int(pBot))  # bottom

### Tracking Algorithm
            id = 0
            minDistance = 150 * (height / 170)
            minDistanceIdx = -1

            # find closest person
            for idx, person in enumerate(oldPeopleList):
                distance = calculate_distance(coord, person.get_coord())
                if minDistance > distance:
                    minDistance = distance
                    minDistanceIdx = idx
            
            # if found
            if minDistanceIdx != -1:
                id = oldPeopleList[minDistanceIdx].get_id()
                del oldPeopleList[minDistanceIdx]
                idTable[0][minDistanceIdx] = id
            # if not found and has candidate
            elif len(idCandidate) > 0:
                id = min(idCandidate)
                idCandidate.remove(id)
            # if not found and has no candidate
            else :
                id = newId
                newId += 1

            peopleList.append(Person(id, height, coord))

    ## make combinations of idx
    peopleIdx = list(range(len(peopleList))) ## 0, 1, 2, ..... , peopleList length
    peopleIdxCombi = list(itertools.combinations(peopleIdx, 2))

    idTable = IdTable(peopleList)

    for idx1, idx2 in peopleIdxCombi:
        person1, person2 = peopleList[idx1], peopleList[idx2]
        
        if not is_valid(person1, person2) or is_same_group(peopleList, person1, person2):
            continue

        ## get distance info
        dist = calculate_distance(person1.get_coord(), person2.get_coord())
        distHighRisk, distLowRisk = calculate_distance_threshold(person1.get_height(), person2.get_height())  ## Calculate with Image Ratio

        ## high risk
        if dist < distHighRisk:
            union_parent(idTable, person1, person2)
            if not person1.is_updated():
                person1.inc_redCount()
                person1.set_updated(True)
            if not person2.is_updated():
                person2.inc_redCount()
                person2.set_updated(True)
        
        if distHighRisk < dist and dist < distLowRisk:
            person1.set_yellow(True)
            person2.set_yellow(True)

### Grouping Algorithm
    groupCoordsList = [[] for i in range(len(peopleList))]

    for person in peopleList:
        x, y = person.get_coord()
        x -= 40
        y -= person.get_height() + 20 

        # Show Person Id   
        cv2.putText(img, str(person.get_id()), (x, y), 0, fontScale, color.blue, fontThickness, lineType)
        
        # Draw Green Circle
        if not person.is_updated():
            person.clear_redCount()
            if person.is_yellow():
                cv2.circle(img, person.get_coord(), radius, color.yellow, -1)
            else :
                cv2.circle(img, person.get_coord(), radius, color.green, -1)
            continue
        
        # Draw Red Circle and Show RedCount
        person.set_updated(False)
        pid = find_parent(peopleList, person)
        groupCoordsList[pid].append(person.get_coord())
        cv2.circle(img, person.get_coord(), radius, color.red, -1)
        #cv2.putText(img, str(person.get_redCount()), person.get_coord(), 0, fontScale, color.red, fontThickness, lineType)

        # x, y = person.get_coord()
        # x -= 40
        # y -= person.get_height() + 20 

        # Show Group Id   
        #cv2.putText(img, str(person.get_pid()), (x, y), 0, fontScale, color.yellow, fontThickness, lineType)
        
        # Show Definite Risk
        if person.is_definite_risk():
            cv2.putText(img, "RISK", (x, y), 0, fontScale, color.red, fontThickness, lineType)

### Draw Polygon                
    overlay = img.copy()
    opacity = 0.5
    for polyCoords in groupCoordsList:
        if len(polyCoords) >= 2:
            polyCoords = np.int32([np.array(polyCoords)])
            cv2.fillConvexPoly(overlay, polyCoords, color.red)
            #cv2.polylines(overlay, polyCoords, True, color.red)

    cv2.addWeighted(overlay, opacity, img, 1 - opacity, 0, img)

### Check Undetected people
    for person in enumerate(oldPeopleList):
        if person.is_erasable(img.shape[:2]):
            idCandidate.append(person.get_id())
        else :
            person.set_pid(person.get_id())
            peopleList.append(person)

    return img, peopleList, idCandidate
