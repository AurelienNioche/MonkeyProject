from PIL import Image, ImageDraw  # PIL is package Pillow
from os.path import exists
from os import rename, remove
import numpy as np


if __name__ == "__main__":

    possibilities = np.arange(-3, 4)
    max_quantity = max(possibilities)
    condition = "gain"
    angle_unit = 90 / (max_quantity + 1)
    print("Angle unit", angle_unit)

    width = 2000
    height = 2000

    margin = 100

    for i in possibilities:

        print("X", i)

        image = Image.new("RGBA", (width, height), "#ddd")

        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, width, height), fill=(255, 255, 255), outline=None)

        line_color = (0, 0, 0)  # Black

        if i == 0:

            print("Line angle", 0)

            cursor = 0
            while cursor < height:

                x0, y0, x1, y1 = 0, cursor, width, cursor

                draw.line((x0, y0, x1, y1), fill=line_color, width=10)
                cursor += margin

        elif i > 0:

            cursor = 0
            line_angle = angle_unit * i

            print("Line angle", line_angle)

            deviation = margin / np.sin(np.deg2rad(90 - line_angle))

            line_height = - np.absolute(np.tan(np.deg2rad(line_angle)) * width)

            while cursor < height-line_height:

                x0, y0, x1, y1 = 0, cursor, width, cursor + line_height

                draw.line((x0, y0, x1, y1), fill=line_color, width=10)
                cursor += deviation

        else:

            cursor = 0
            line_angle = angle_unit * np.absolute(i)

            print("Line angle", line_angle)

            deviation = margin / np.sin(np.deg2rad(90 - line_angle))

            line_height = - np.absolute(np.tan(np.deg2rad(line_angle)) * width)

            while cursor < height - line_height:
                x0, y0, x1, y1 = 0, cursor + line_height, width, cursor

                draw.line((x0, y0, x1, y1), fill=line_color, width=10)
                cursor += deviation
                # break

        filename = "{condition}{size}.png".format(condition=condition, size=i)
        if exists(filename):

            if exists('OLD_{}'.format(filename)):

                remove('OLD_{}'.format(filename))

            rename(filename, 'OLD_{}'.format(filename))

        image.save(filename)

