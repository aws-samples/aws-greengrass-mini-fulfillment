import picamera
import picamera.array
import png
import math
from pixel_object import PixelObject

"""
Image processor that can find the edges in a PNG image captured by a PiCamera.
"""


class ImageProcessor:

    def __init__(self, res_width=96, res_height=96):
        self.camera = picamera.PiCamera(resolution=(res_width, res_height))
        # TODO propagate configurable resolution through '96' logic below

        self.camera.hflip = True
        self.camera.vflip = True
        self.res_width = res_width
        self.res_height = res_height
        self.stream = picamera.array.PiYUVArray(self.camera)
        self.pixelObjList = []
        self.object_id_center = 0
        self.pixelObjList.append(PixelObject(self.next_obj_id()))
        self.max_pixel_count = 0
        self.largest_object_id = 0
        self.largest_X = 0
        self.largest_Y = 0
        self.filename = ''

    def close(self):
        print('[ImageProcessor.close] flushing')
        self.pixelObjList = []
        self.object_id_center = 0
        self.max_pixel_count = 0
        self.largest_object_id = 0
        self.largest_X = 0
        self.largest_Y = 0
        self.camera.close()

    def next_obj_id(self):
        self.object_id_center += 1
        return self.object_id_center

    def capture_frame(self):
        self.stream = picamera.array.PiYUVArray(self.camera)
        self.camera.capture(self.stream, 'yuv')
        self.camera._set_led(True)

        self.pixelObjList = []
        self.object_id_center = 0
        self.pixelObjList.append(PixelObject(self.next_obj_id()))

        rows = []
        for _ in range(self.res_height):
            rows.append(range(self.res_width))

        # flip image horizontally
        for j, j_ in enumerate(range(self.res_width-1, -1, -1)):
            # now flip vertically
            for i, i_ in enumerate(range(self.res_height-1, -1, -1)):
                rows[j][i] = self.stream.array[j_][i_][0]

        self.filename = self.save_PNG('raw.png', rows)
        self.spread_white_pixels(
            self.make_black_and_white(
                self.fuse_horizontal_and_vertical(
                    self.get_horizontal_edges(rows),
                    self.get_vertical_edges(rows)))
        )

    def get_horizontal_edges(self, raw_rows):
        # get horizontal edges
        rows = []
        for _ in range(96):
            rows.append(range(96))
        for j in range(96):
            for i in range(96):
                if i + 1 <= 95:
                    rows[j][i] = self.difference(raw_rows[j][i],
                                                 raw_rows[j][i + 1])
                else:
                    rows[j][i] = self.difference(raw_rows[j][i],
                                                 raw_rows[j][i - 1])

        self.save_PNG('processed_1.png', rows)
        return rows

    def get_vertical_edges(self, rawrows):
        # get vertical edges
        rows = []
        for _ in range(96):
            rows.append(range(96))
        for j in range(96):
            for i in range(96):
                if j + 1 <= 95:
                    rows[j][i] = self.difference(
                        rawrows[j][i], rawrows[j + 1][i])
                else:
                    rows[j][i] = self.difference(
                        rawrows[j][i], rawrows[j - 1][i])

        self.save_PNG('processed_2.png', rows)
        return rows

    def fuse_horizontal_and_vertical(self, hrows, vrows):
        # fuse the horizontal edge-image with the vertical edge-image
        rows = []
        for _ in range(96):
            rows.append(range(96))
        for j in range(96):
            for i in range(96):
                rows[j][i] = self.fusion(hrows[j][i], vrows[j][i])

        self.save_PNG('processed_3.png', rows)
        return rows

    def make_black_and_white(self, edge_rows):
        # make the image dual in color (black and white)
        threshold = 18

        rows = []
        for _ in range(96):
            rows.append(range(96))
        for j in range(96):
            for i in range(96):
                if edge_rows[j][i] >= threshold:
                    rows[j][i] = 255
                else:
                    rows[j][i] = 0

        self.save_PNG('processed_4.png', rows)
        return rows

    def spread_white_pixels(self, bw_rows):
        # make all the white pixels spread out one more pixel
        rows = []
        for _ in range(96):
            rows.append(range(96))
        for j in range(96):
            for i in range(96):
                if bw_rows[j][i] == 255:
                    tmp_list = self.neighbors((i, j), 96, 96)
                    for ent in tmp_list:
                        tmp_x, tmp_y = ent
                        rows[tmp_y][tmp_x] = 255
                else:
                    rows[j][i] = 0

        self.save_PNG('processed_4_5.png', rows)

        self.identify_pixel_objects(rows)

    def identify_pixel_objects(self, bw_rows):
        # make PixelObjects when pixels are direct 8-neighbours of each other
        for j in range(96):
            for i in range(96):
                if bw_rows[j][i] == 255:  # if the pixel is white
                    tmp_list = []
                    for ent in self.neighbors((i, j), 96, 96):
                        tmp_x, tmp_y = ent
                        if bw_rows[tmp_y][tmp_x] == 255:  # if pixel is white
                            tmp_list.append(ent)
                    # print tmp_list
                    flag = False
                    for obj in self.pixelObjList:
                        # make a new PixelObj whenever a Pixel isn't connected
                        # to an object
                        if obj.check_xy_set(tmp_list) is True:
                            flag = True
                    if flag is False:
                        self.pixelObjList.append(
                            PixelObject(self.next_obj_id()))
                        for obj in self.pixelObjList:
                            obj.check_xy_set(tmp_list)
        for obj in self.pixelObjList:
            rows = []
            for _ in range(96):
                rows.append(range(96))
            for j in range(96):
                for i in range(96):
                    if (i, j) in obj.XYset:
                        rows[j][i] = 255
                    else:
                        rows[j][i] = 0
                        # self.save_PNG(string.join([str(obj.id_), 'processed_5.png'], ''), rows)
        self.merge_overlapping_pixel_objects()

    def merge_overlapping_pixel_objects(self):
        # merge objects with overlapping x-y tuples together
        center = 0
        max_entry = len(self.pixelObjList) - 1
        # old_len = len(self.pixelObjList)
        # flag = False
        while center < max_entry:
            tmp = self.check_overlap(center)
            if tmp is False:
                center += 1
            else:
                for ent in self.pixelObjList[tmp].XYset:
                    self.pixelObjList[center].XYset.add(ent)
                del self.pixelObjList[tmp]
                max_entry = len(self.pixelObjList) - 1

        for obj in self.pixelObjList:
            object_pixels = obj.count_pixel()
            # if self.max_pixel_count == 0:
            #     results['max_pixel_count'] = object_pixels
            #     results['object_id'] = obj.id_
            if object_pixels > self.max_pixel_count:
                self.max_pixel_count = object_pixels
                self.largest_object_id = obj.id_
                x, y = obj.compute_mean_coord()
                self.largest_X = x
                self.largest_Y = y

            # print obj.XYset
            rows = []
            for _ in range(96):
                rows.append(range(96))
            for j in range(96):
                for i in range(96):
                    if (i, j) in obj.XYset:
                        rows[j][i] = 255
                    else:
                        rows[j][i] = 0
                        # self.save_PNG(string.join([str(obj.id_), 'pixpro.png'], ''), rows)

        # print("nmbr of pre Objects:{0}".format(old_len))
        self.new_one_pixel_png()

    def new_one_pixel_png(self):
        """
        make a new png with 1 pixel per object at their respective center
        :return:
        """
        tmp_pos_list = []

        for obj in self.pixelObjList:
            print("X:{0} Y:{1}".format(obj.coord_x, obj.coord_y))
            tmp_pos_list.append((obj.coord_x, obj.coord_real_y))

        rows = []
        for _ in range(96):
            rows.append(range(96))
        for j in range(96):
            for i in range(96):
                if (i, j) in tmp_pos_list:
                    rows[j][i] = 255
                else:
                    rows[j][i] = 0

        self.save_PNG('PixelObjectPos.png', rows)

    def check_overlap(self, counter):
        """
        check for overlapping x-y tuples in sets in 2 distinct objects
        return the listNumber for the object with overlapping pixels if there
        are overlapping pixels return False if not
        """
        max_entry = len(self.pixelObjList) - 1
        for ent1 in self.pixelObjList[counter].XYset:
            for i in range(counter + 1, max_entry + 1, 1):
                for ent2 in self.pixelObjList[i].XYset:
                    if ent1 == ent2:
                        return i
        return False

    def save_PNG(self, filename, rws):
        # print("[save_PNG] filename:{0} rws:{1}".format(filename, rws))
        name = 'img/{0}'.format(filename)
        f = open(name, 'wb')
        w = png.Writer(96, 96, greyscale=True)
        w.write(f, rws)
        f.close()
        return name

    def difference(self, a, b):
        if a >= b:
            return a - b
        else:
            return b - a

    def fusion(self, a, b):
        a_ = int(a)
        b_ = int(b)
        tmp = round(math.sqrt(a_ * a_ + b_ * b_))
        if tmp <= 255:
            return int(tmp)
        else:
            return 255

    def neighbors(self, (x, y), max_x, max_y):
        n_list = []
        xx, yy = (x, y)
        for y_ in range(-1, 2, 1):
            for x_ in range(-1, 2, 1):
                res_x = xx + x_
                res_y = yy + y_
                if max_x > res_x >= 0 and max_y > res_y >= 0:
                    n_list.append((res_x, res_y))
        return n_list
