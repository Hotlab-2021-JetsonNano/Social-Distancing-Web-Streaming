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
        self.radius = 4
    
    def get_colors(self): 
        return self.colors

    def get_figure(self):
        return self.fontScale / 3, self.fontThickness, self.lineThickness, self.lineType, self.radius

class Person:
    def __init__(self, id, height, coord):
        self.id = id
        self.group = id
        self.height = height
        self.coord = coord
        self.redCount = 0
        self.updated = False

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

    def get_updated(self):
        return self.updated

    def set_updated(self, value):
        self.updated = value
        return

    def get_redCount(self):
        return self.redCount
    
    def inc_redCount(self):
        self.redCount += 1
        return

    def is_red(self):
        return self.redCount > 0

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

class Group: # disjoint set
    def __init__(self, N):
        self.parent = [0] * N
        for i in range(len(self.parent)):
            self.parent[i] = i

    def find(self, id):
        if id != self.parent[id]:
            self.parent[id] = self.find(self.parent[id])
        return self.parent[id]
            
    def attach(self, id1, id2):
        pid1 = self.find(id1)
        pid2 = self.find(id2)
        self.parent[pid2] = pid1
        return

    def detach(self, id):
        self.parent[id] = id

    def is_same(self, id1, id2):
        return self.find(id1) == self.find(id2)

    def get_sub(self, groupId):
        subGroup = []
        for id, pid in enumerate(self.parent):
            if pid == groupId:
                subGroup.append(id)
        return subGroup
