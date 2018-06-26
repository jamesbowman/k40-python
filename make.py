import svgwrite

dwg = svgwrite.Drawing('test.svg', size=('50mm', '40mm'), viewBox=('0 0 50 40'))

def rect(x0, y0, x1, y1):
    dwg.add(dwg.polyline([(x0, y0), (x0, y1), (x1, y1), (x1, y0), (x0, y0)], stroke='red', fill_opacity=0.0, stroke_width=.1))

paragraph = dwg.add(dwg.g(font_size=14))
# paragraph.add(dwg.text("This is a Test!", (10,20), stroke='black', font_size = 1, stroke_width=.1))

for i in range(20):
    sz = 2.5 + .1 * i
    x = 10.0 * (i % 5)
    y = 10.0 * (i / 5)
    rect(x + 4, y + 4, x + 4 + sz, y + 4 + sz)
    paragraph.add(dwg.text("%.1f" % sz, (x + 2, y + 1.8), stroke='black', font_size = 2, stroke_width=.1))

dwg.save()


