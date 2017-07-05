from __future__ import print_function

"""
A class that can both count the pixels contained within an instance and 
determine the mean x, y coordinates of the instance.
"""


class PixelObject:

    def __init__(self, id_):
        self.XYset = set()
        self.id_ = id_
        self.numberOfPixels = 0
        self.coord_x = 0
        self.coord_y = 0
        self.coord_real_y = 0
        print("new object made with id: ", self.id_)

    def check_xy_set(self, entry_list):
        flag = False
        for entry in entry_list:
            if len(self.XYset) is 0:
                self.XYset.add(entry)
            if entry in self.XYset:
                flag = True
        if flag is True:
            for entry in entry_list:
                self.XYset.add(entry)
        return flag

    def count_pixel(self):
        self.numberOfPixels = len(self.XYset)
        print("Object ID:{0}".format(self.id_))
        print("Number of Pixels:{0}".format(self.numberOfPixels))

        return self.numberOfPixels

    def compute_mean_coord(self):
        # This code assumes only one object.
        print('my current object id is:{0}'.format(self.id_))
        if len(self.XYset) is 0:
            return
        temp_x = 0
        temp_y = 0
        for ent in self.XYset:
            x, y = ent
            temp_x += x
            temp_y += y

        self.coord_x = int(temp_x / len(self.XYset))
        tmp = int(temp_y / len(self.XYset))
        self.coord_real_y = tmp
        self.coord_y = 96 - tmp  # currently assumes 96 pixel wide images

        print("X coord:{0}".format(self.coord_x))
        print("Y coord:{0}".format(self.coord_y))
        return self.coord_x, self.coord_y
