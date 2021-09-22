import cv2
import itertools
import numpy as np
from utils.distancing_class import Configs, Person, IdTable
from scipy.spatial import ConvexHull

def calculate_box(box):
    pLeft, pTop, pRight, pBot = box
    height = int(pBot - pTop)
    coord  = (int(pLeft + pRight) //2, int(pBot))  # bottom
    return height, coord

def is_valid(idTable, person1, person2):
    validHeights = abs(person1.get_height() - person2.get_height()) < 30 ## need to be fixed
    
    diffThres  = person1.get_height() + person2.get_height()
    validDistance = abs(person1.get_coord()[0] - person2.get_coord()[0]) < diffThres and \
                    abs(person1.get_coord()[1] - person2.get_coord()[1]) < diffThres

    parentId1 = idTable.find_parentId(person1.get_id())
    parentId2 = idTable.find_parentId(person2.get_id())
    validParents = parentId1 != parentId2

    return validHeights and validDistance and validParents

def calculate_distance(point1, point2):
    x1, y1 = point1
    x2, y2 = point2
    return ((x2 - x1)**2 + (y2 - y1)**2) **0.5

def calculate_distance_threshold(height1, height2):
    pixelRatio = (height1 + height2) / (170 + 170)
    distHighRisk = 200 * pixelRatio
    distLowRisk  = 250 * pixelRatio
    return distHighRisk, distLowRisk

def create_id_table(peopleList, invalidIdList):
    idTable = IdTable(peopleList)
    peopleList = idTable.check_id_validity(invalidIdList)
    return idTable, peopleList

def create_idx_combination(peopleList):
    peopleIdx = list(range(len(peopleList))) ## 0, 1, 2, ..... , peopleList length
    peopleIdxCombi = list(itertools.combinations(peopleIdx, 2))
    return peopleIdxCombi

def tracking_algorithm(height, coord, oldPeopleList, validIdList):
    minDistance = 150 * (height / 170)
    minDistanceIdx = -1

    # find closest person
    for idx, person in enumerate(oldPeopleList):
        distance = calculate_distance(coord, person.get_coord())
        if minDistance > distance:
            minDistance = distance
            minDistanceIdx = idx

    # (success tracking)
    # if found 
    if minDistanceIdx != -1:
        person = oldPeopleList[minDistanceIdx]
        del oldPeopleList[minDistanceIdx]
        person.set_height(height)
        person.set_coord(coord)
        person.clear_missCount()
        return person

    # (fail tracking)
    # if not found and has candidate 
    if len(validIdList) > 0:
        id = min(validIdList)
        validIdList.remove(id)
    # if not found and has no candidate
    else :
        id = -1
    
    return Person(id, height, coord)

def distancing_algorithm(idTable, person1, person2, frameTime):
    ## get distance info
    dist = calculate_distance(person1.get_coord(), person2.get_coord())
    distHighRisk, distLowRisk = calculate_distance_threshold(person1.get_height(), person2.get_height())  ## Calculate with Image Ratio

    ## high risk
    if dist < distHighRisk:
        idTable.merge_parentIds(person1.get_id(), person2.get_id())
        if not person1.is_updated():
            person1.inc_riskTime(frameTime)
            person1.set_updated(True)
        if not person2.is_updated():
            person2.inc_riskTime(frameTime)
            person2.set_updated(True)
    
    ## low risk
    elif distHighRisk < dist and dist < distLowRisk:
        person1.set_yellow(True)
        person2.set_yellow(True)

    return

def grouping_algorithm(img, config, groupCoordsList, peopleList, idTable, file, frameNumber):
    color = config.get_colors()
    imgRatio, fontScale, fontThickness, lineType, radius = config.get_figure()
    imgRatio = int(10 * imgRatio)

    for person in peopleList:
        x, y = person.get_coord()

        ## Show Height
        # x1 = x - imgRatio
        # y1 = y - int(person.get_height() / 2)
        # cv2.putText(img, str(person.get_height()), (x1, y1), 0, fontScale, color.blue, fontThickness, lineType)

        ## Show Person Id   
        #cv2.putText(img, str(person.get_id()), (x1, y1), 0, fontScale, color.blue, fontThickness, lineType)
        
        ## Draw Green Circle
        if not person.is_updated():
            person.clear_riskTime()
            if person.is_yellow():
                cv2.circle(img, person.get_coord(), radius, color.yellow, -1)
            else :
                cv2.circle(img, person.get_coord(), radius, color.green, -1)
            continue
        
        ## Red
        person.set_updated(False)

        ## Show Red Circle
        cv2.circle(img, person.get_coord(), radius, color.red, -1)

        ## Show Red Count
        # cv2.putText(img, str(person.get_redCount()), (x, y), 0, fontScale, color.red, fontThickness, lineType)
        
        ## Show Risk Time
        cv2.putText(img, str(person.get_riskTime()), (x, y), 0, fontScale, color.black, fontThickness, lineType)
        
        ## Show Definite Risk
        if person.is_definite_risk():
           x1 = x - imgRatio
           y1 = y - int(person.get_height() / 2)
           cv2.putText(img, "RISK", (x1, y1), 0, fontScale, color.red, fontThickness, lineType)
           file.write("frame : {fn} |".foramt(fn=frameNumber).rjust(5) + \
                      "person : {id} |".format(id=person.get_id()).rjust(5) + \
                      "risk time : {t}".format(t=person.get_riskTime()).rjust(10) + '\n')
        
        ## Set Group List
        parentId  = idTable.find_parentId(person.get_id())
        parentIdx = idTable.get_parentIdx(parentId)
        groupCoordsList[parentIdx].append(person.get_coord())

    return img

def draw_polygons(img, config, groupCoordsList):
    color = config.get_colors()
    lineInfo = config.get_figure_line()
    overlay = img.copy()
    opacity = 0.5

    for polyCoords in groupCoordsList:
        if len(polyCoords) >= 2:
            try:
                hull = ConvexHull(polyCoords)
            except:
                pass
            else:
                polyCoords = [[polyCoords[idx]] for idx in hull.vertices]
            cv2.fillConvexPoly(overlay, np.array(polyCoords), color.red)

    cv2.addWeighted(overlay, opacity, img, 1 - opacity, 0, img)
    return img

def show_distancing(img, boxes, frameData):
    oldPeopleList, validIdList, invalidIdList = frameData.get_info()

    if len(boxes) == 0:
        return img

    peopleList = []

    ## first frame
    if len(oldPeopleList) == 0:
        for id, box in enumerate(boxes):
            height, coord = calculate_box(box)
            peopleList.append(Person(id, height, coord))

    ## next frame
    else :
### Tracking Algorithm
        for box in boxes:
            height, coord = calculate_box(box)
            person = tracking_algorithm(height, coord, oldPeopleList, validIdList)
            peopleList.append(person)

### Check Untracked people
    invalidIdList = set([person.get_id() for person in oldPeopleList])

### Distancing Algorithm
    ## create id info table
    idTable, peopleList = create_id_table(peopleList, invalidIdList)

    ## make combinations of idx
    peopleIdxCombi = create_idx_combination(peopleList)

    ## frame time
    fps = frameData.get_fps()    
    frameTime = round(1 / fps, 2) if (fps > 0.0) else 0.0

    ## distancing between two people
    for index1, index2 in peopleIdxCombi:
        person1, person2 = peopleList[index1], peopleList[index2]
        if is_valid(idTable, person1, person2):
            distancing_algorithm(idTable, person1, person2, frameTime)

### Grouping Algorithm
    config = Configs(img)
    groupCoordsList = [[] for i in range(len(peopleList))]
    file = open(frameData.get_filePath(), 'w')
    frameNumber = frameData.get_counter()
    
    img = grouping_algorithm(img, config, groupCoordsList, peopleList, idTable, file, frameNumber)
    img = draw_polygons(img, config, groupCoordsList)

    file.close()

### Check Undetected people
    for person in oldPeopleList:
        if person.is_erasable(img.shape[:2]) or person.is_missable():
            invalidIdList.remove(person.get_id())
            validIdList.add(person.get_id())
        else :
            person.inc_missCount()
            peopleList.append(person)

    return img
