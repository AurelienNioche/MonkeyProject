from PIL import Image, ImageDraw  # PIL is package Pillow
from os.path import exists
from os import rename, remove
import numpy as np

if __name__ == "__main__":

    possibilities = [-4, -3, -2, -1, 0, 1, 2, 3, 4]
    max_quantity = np.max(possibilities)
    condition = "gain"
    angle_unit = 90 / max_quantity
    print("Angle unit", angle_unit)

    width = 2000
    height = 2000

    margin = 100

    for i in possibilities:

        print("X", i)

        image = Image.new("RGBA", (width, height), "#ddd")

        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, width, height), fill=(255, 255, 255), outline=None)

        if i >= 0:
            line_color = (0, 0, 0)  # Black
        else:
            line_color = (255, 0, 0)  # Red

        if i == 0:

            print("Line angle", 0)

            cursor = 0
            while cursor < height:

                x0, y0, x1, y1 = 0, cursor, width, cursor

                draw.line((x0, y0, x1, y1), fill=line_color, width=10)
                cursor += margin

        elif np.absolute(i) == max_quantity:

            print("Line angle", 90)

            cursor = 0
            while cursor < height:
                x0, y0, x1, y1 = cursor, 0, cursor, height

                draw.line((x0, y0, x1, y1), fill=line_color, width=10)
                cursor += margin

        else:

            cursor = 0
            line_angle = angle_unit * np.absolute(i)

            print("Line angle", line_angle)

            deviation = margin / np.absolute(np.sin(np.deg2rad(90 - line_angle)))

            line_height = - np.absolute(np.tan(np.deg2rad(line_angle)) * width)

            while cursor < height-line_height:

                x0, y0, x1, y1 = 0, cursor, width, cursor + line_height

                draw.line((x0, y0, x1, y1), fill=line_color, width=10)
                cursor += deviation

            # line_angle = angle_unit * i
            # print("Line angle", line_angle)
            # raw_height = np.absolute(np.tan(np.deg2rad(line_angle)) * width)
            # print(raw_height)
            # height_1 = height - raw_height
            # print(height_1)
            #
            # x0, y0, x1, y1 = 0, height, width, height_1
            #
            # draw.line((x0, y0, x1, y1), fill=(0, 0, 0),  width=10)

        filename = "{condition}{size}.png".format(condition=condition, size=i)
        if exists(filename):

            if exists('OLD_{}'.format(filename)):

                remove('OLD_{}'.format(filename))

            rename(filename, 'OLD_{}'.format(filename))

        image.save(filename)
