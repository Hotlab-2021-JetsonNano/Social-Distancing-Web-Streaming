import cv2

class Colors:
    def __init__(self):
        self.blue   = (255, 0, 0)
        self.yellow = (0, 255, 255)
        self.red    = (0, 0, 255)
        self.green  = (0, 255, 0)

class Configs:
    def __init__(self, img):
        self.colors = Colors()
        self.imgRatio = img.shape[1] / 720
        self.fontScale = round(1 * self.imgRatio)
        self.fontThickness = round(1 * self.imgRatio)
        self.lineThickness = 2
        self.lineType = cv2.LINE_AA
        self.radius = round(3 * self.imgRatio)
    
    def get_colors(self): 
        return self.colors

    def get_figure(self):
        return self.imgRatio, self.fontScale / 3, self.fontThickness, self.lineType, self.radius

    def get_figure_line(self):
        return self.lineThickness, self.lineType
    

class Person:
    def __init__(self, id, height, coord):
        self.id = id
        self.height = height
        self.coord = coord
        self.redCount = 0
        self.updated = False
        self.isYellow = False
        self.missCount = 0

    def get_id(self):
        return self.id
    def set_id(self, id):
        self.id = id
        return

    def get_height(self):
        return self.height
    def set_height(self, height):
        self.height = height
        return

    def get_coord(self):
        return self.coord
    def set_coord(self, coord):
        self.coord = coord
        return

    def is_updated(self):
        return self.updated
    def set_updated(self, value):
        self.updated = value
        return

    def is_yellow(self):
        return self.isYellow
    def set_yellow(self, value):
        self.isYellow = value
        return

    def get_redCount(self):
        return self.redCount
    def inc_redCount(self):
        self.redCount += 1
        return
    def clear_redCount(self):
        self.redCount = 0
        return
    def is_definite_risk(self):
        return self.redCount > 30

    def is_erasable(self, thres):
        x, y = self.coord
        low_x, low_y = (3, 3)
        high_y, high_x = thres
        return (x < low_x or x > high_x - 3  or y < low_y or y > high_y - 3)

    def inc_missCount(self):
        self.missCount += 1
        return
    def clear_missCount(self):
        self.missCount = 0
        return
    def is_missable(self):
        return self.missCount > 10

class IdTable:
    def __init__(self, peopleList):
        self.peopleList = peopleList
        self.personIdList = [person.get_id() for person in self.peopleList]
        self.parentIdList = self.personIdList[:]

    def check_id_validity(self, invalidIdList):
        for index, personId in enumerate(self.personIdList):
            if personId == -1:
                newId = max(self.personIdList) + 1
                while newId in invalidIdList:
                    newId += 1
                self.peopleList[index].set_id(newId)
                self.personIdList[index] = newId
                self.parentIdList[index] = newId
        return self.peopleList

    def get_ids(self, person):
        index = self.personIdList.index(person.get_id())
        return self.personIdList[index], self.parentIdList[index]

    def get_parentIdx(self, parentId):
        return self.parentIdList.index(parentId)

    def set_parentId(self, personId, parentId):
        index = self.personIdList.index(personId)
        self.parentIdList[index] = parentId
        return

    def find_parentId(self, personId):
        index    = self.personIdList.index(personId)
        parentId = self.parentIdList[index]
        if personId == parentId:
            return parentId
        else :
            #personId = parentId
            parentId = self.find_parentId(parentId)
            #self.set_parentId(personId, parentId)
            return parentId

    def merge_parentIds(self, personId1, personId2):
        parentId1 = self.find_parentId(personId1)
        parentId2 = self.find_parentId(personId2)
        self.set_parentId(parentId1, parentId2)

