import svgwrite

dwg = svgwrite.Drawing('test.svg', size=('80mm', '70mm'), viewBox=('0 0 80 70'))

def rect(x0, y0, x1, y1):
    dwg.add(dwg.polyline([(x0, y0), (x0, y1), (x1, y1), (x1, y0), (x0, y0)], stroke='red'))

kerf = 0.20
(w, h) = (62.4 - kerf, 49.2 - kerf)
(x0, y0) = (10, 10)
(x1, y1) = (x0 + w, y0 + h)

rect(0, 0, 80, 70)
rect(x0, y0, x1, y1)

dwg.save()
