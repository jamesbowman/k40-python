import svgwrite

def cross(dwg, x, y, r = 5):
    dwg.add(dwg.line((x - r, y), (x + r, y), stroke='red', stroke_width=.1))
    dwg.add(dwg.line((x, y - r), (x, y + r), stroke='red', stroke_width=.1))

if __name__ == '__main__':
    dwg = svgwrite.Drawing('test.svg', size=('150mm', '150mm'), viewBox=('0 0 150 150'))

    cross(dwg, 5, 5)
    cross(dwg, 145, 5)
    cross(dwg, 145, 145)
    cross(dwg, 5, 145)

    dwg.save()


