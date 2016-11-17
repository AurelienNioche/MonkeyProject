import math
from pylab import plt, np
import ternary


def color_point(x, y, z, scale):
    w = 255
    x_color = x * w / float(scale)
    y_color = y * w / float(scale)
    z_color = z * w / float(scale)
    r = math.fabs(w - y_color) / w
    g = math.fabs(w - x_color) / w
    b = math.fabs(w - z_color) / w
    return (r, g, b, 1.)


def generate_heatmap_data(scale=5):
    from ternary.helpers import simplex_iterator
    d = dict()
    for (i, j, k) in simplex_iterator(scale):
        d[(i, j, k)] = np.random.random()
    return d


scale = 80
data = generate_heatmap_data(scale)
figure, tax = ternary.figure(scale=scale)
tax.boundary(linewidth=2.0)
tax.heatmap(data, scale=scale, style="triangular")  # Allow colors as rgba tuples
# tax.gridlines(color="blue", multiple=5)
# tax.boundary()
# tax.set_title("RGBA Heatmap")
fontsize = 14
tax.left_axis_label("Left label $\\alpha^2$", fontsize=fontsize)
tax.right_axis_label("Right label $\\beta^2$", fontsize=fontsize)
tax.bottom_axis_label("Bottom label $\\Gamma - \\Omega$", fontsize=fontsize)
tax.ticks(axis='lbr', multiple=5, linewidth=1)

tax.clear_matplotlib_ticks()
plt.show()
