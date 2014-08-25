#!/usr/bin/env python
import random
from string import ascii_lowercase


def generate_colors(s, v):
    golden_ratio_conjugate = 0.618033988749895
    h = random.random()
    with open('colors.html', 'w') as f:
        for c in list(ascii_lowercase):
            h += golden_ratio_conjugate
            h %= 1
            r, g, b = hsv_to_rgb(h, s, v)

            color = "rgb({}, {}, {})".format(r, g, b)
            f.write('<div style="background-color:{}">{}: {}, hsv({}, {}, {})'
                    '</div>\n'.format(color, c, color, h, s, v))


def hsv_to_rgb(h, s, v):
    h_i = int(h * 6)
    f = h * 6 - h_i
    p = v * (1 - s)
    q = v * (1 - f * s)
    t = v * (1 - (1 - f) * s)

    if h_i == 0:
        r, g, b = v, t, p
    elif h_i == 1:
        r, g, b = q, v, p
    elif h_i == 2:
        r, g, b = p, v, t
    elif h_i == 3:
        r, g, b = p, q, v
    elif h_i == 4:
        r, g, b = t, p, v
    elif h_i == 5:
        r, g, b = v, p, q

    return int(r * 256), int(g * 256), int(b * 256)


if __name__ == '__main__':
    generate_colors(0.5, 0.95)
