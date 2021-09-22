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
        self.fontScale = round(0.001 * (img.shape[0] + img.shape[1]) / 2) + 1
        self.fontThickness = max(self.fontScale - 1, 1)
        self.lineThickness = 2
        self.lineType = cv2.LINE_AA
        self.radius = 5
    
    def get_colors(self): 
        return self.colors

    def get_figure(self):
        return self.fontScale / 3, self.fontThickness, self.lineThickness, self.lineType, self.radius

class Person:
    def __init__(self, id, height, coord):
        self.id = id
        self.pid = id
        self.height = height
        self.coord = coord
        self.redCount = 0
        self.updated = False
        self.isYellow = False

    def get_id(self):
        return self.id

    def get_pid(self):
        return self.pid

    def set_pid(self, pid):
        self.pid = pid
        return

    def get_height(self):
        return self.height

    def get_coord(self):
        return self.coord

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

    def is_erasable(self, thres):
        x, y = self.coord
        low_x, low_y = (3, 3)
        high_x, high_y = thres
        return (x < low_x or x > high_x - 3  or y < low_y or y > high_y - 3)
    
    def is_definite_risk(self):
        return self.redCount > 30

class IdTable:
    def __init__(self, peopleList):
        self.personList = peopleList
        self.personIdList = [[person.get_id()] for person in self.personList]
        self.parentIdList = self.personIdList[:]

    def get_ids(self, person):
        index = self.personList.index(person)
        return self.personIdList[index], self.parentIdList[index]

    def get_parent(self, parentId):
        index = self.parentIdList.index(parentId)
        return self.personList[index]

    def set_parentId(self, person, parentId):
        index = self.personList.index(person)
        self.parentIdList[index] = parentId
        