import sys
import re

F0402 = (1.2, 0.7)
foots = {
    'NX3225' : (3.2, 2.5),
    'VQFN48' : (7.0, 7.0),
    'EFM8BB10F(2/4/8)G-A-QFN20' :  (3.0, 3.0),
    'SOT23-5' : (3.4, 3.2),
    'C0805' : (2.1, 1.35),
    'C0402K' : F0402,
    'R0402' : F0402,
}

class Point:
    def __init__(self, x, y):
        (self.x, self.y) = (x, y)
    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)
    def __sub__(self, other):
        return Point(self.x - other.x, self.y - other.y)
    def tuple(self):
        return (self.x, self.y)

def extents(pp):
    allx = [p.x for p in pp]
    ally = [p.y for p in pp]
    x0,y0 = (min(allx), min(ally))
    x1,y1 = (max(allx), max(ally))
    return (Point(x0, y0), Point(x1, y1))

class Mnt:
    def __init__(self, fn):
        self.lines = []
        self.allpoints = []
        for l in open(fn):
            ll = l.split()
            (part, x, y, angle) = ll[:4]
            foot = ll[-1]
            (x, y, angle) = [float(c) for c in (x, y, angle)]
            (w, h) = foots[foot]
            if angle in (90, 270):
                (w, h) = (h, w)
            self.part(Point(x, 70 - y), w, h)

    def line(self, p0, p1):
        self.allpoints += [p0, p1]
        self.lines.append((p0, p1))

    def part(self, p, w, h):
        a = Point(p.x - w / 2, p.y - h / 2)
        b = Point(p.x + w / 2, p.y - h / 2)
        c = Point(p.x + w / 2, p.y + h / 2)
        d = Point(p.x - w / 2, p.y + h / 2)
        self.line(a, b)
        self.line(b, c)
        self.line(c, d)
        self.line(d, a)

    def rect(self, p0, p1):
        a = Point(p1.x, p0.y)
        b = Point(p0.x, p1.y)
        self.line(p0, a)
        self.line(a, p1)
        self.line(p1, b)
        self.line(b, p0)

    def addframe(self, r = 10):
        (p0, p1) = extents(self.allpoints)
        p0.y =  7.0
        p1.y = 80.0
        ff = Point(r, 0)
        self.rect(p0 - ff, p1 + ff)

    def write(self, filename):
        import svgwrite
        (p0, p1) = extents(self.allpoints)
        size = p1 - p0
        dwg = svgwrite.Drawing(filename, size=('%fmm' % size.x, '%fmm' % size.y), viewBox=('0 0 %f %f' % (size.x, size.y)))
        for (a, b) in self.lines:
           dwg.add(dwg.line((a - p0).tuple(), (b - p0).tuple(), stroke='red', stroke_width=.1))
        dwg.save()

if __name__ == '__main__':
    m = Mnt(sys.argv[1])
    m.addframe()
    m.write('test.svg')
