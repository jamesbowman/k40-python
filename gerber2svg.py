import sys
import re

import shapely.geometry as sg
import shapely.affinity as sa

import svgwrite

class Point:
    def __init__(self, x, y):
        (self.x, self.y) = (x, y)
    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)
    def __sub__(self, other):
        return Point(self.x - other.x, self.y - other.y)
    def tuple(self):
        return (self.x, self.y)

class Gerber:
    def read(self, filename):
        f = open(filename, "rt")
        c = f.read().replace('\n', '').replace('\r', '')
        f.close()

        def data_block(c):
            a = c.index('*')
            return (c[:a], c[a + 1:])

        while c:
            if c.startswith('%'):
                c = c[1:]
                ec = []
                while not c.startswith('%'):
                    (r, c) = data_block(c)
                    ec.append(r)
                c = c[1:]
                self.extended_code(ec)
            else:
                (r, c) = data_block(c)
                self.function_code(r)

    def extended_code(self, ec):
        # print 'Extended', ec
        for c in ec:
            c2 = c[:2]
            if c2 == 'MO':
                self.scale = {'IN' : 25.4, 'MM' : 1.0}[c[2:]]
            elif c2 == 'FS':
                self.xprec = int(c[6])
                self.yprec = int(c[9])

    def function_code(self, cmd):
        ignore = lambda(m): None
        
        def handle_xyd(m):
            x = self.scale * int(m.group(1)) / (10. ** self.xprec)
            y = self.scale * int(m.group(2)) / (10. ** self.yprec)
            d = m.group(3)
            p = Point(x, y)
            if d == '01':
                self.line(self.pos, p)
            self.pos = p

        actions = [(re.compile(p), a) for (p, a) in [
            (r'G01X([0-9]*)Y([0-9]*)D(0[012])', handle_xyd),
            (r'G01', ignore),
            (r'G54D..', ignore),
            (r'G04.*', ignore),
            (r'M02', self.finish),
        ]]
        while cmd:
            for p,a in actions:
                m = p.match(cmd)
                if m:
                    a(m)
                    cmd = cmd[m.end():]
                    break
            if not m:
                print 'Nothing matched', cmd
                sys.exit(1)
    
class GerberShape(Gerber):
    def __init__(self):
        self.poly = []

    def line(self, p0, p1):
        self.poly.append(p0)

    def finish(self, _):
        self.p = sg.Polygon([p.tuple() for p in self.poly])

class GerberSVG(GerberShape):
    def dilate(self):
        self.p = self.p.buffer(0.1)

    def rect(self, p0, p1):
        a = Point(p1.x, p0.y)
        b = Point(p0.x, p1.y)
        self.line(p0, a)
        self.line(a, p1)
        self.line(p1, b)
        self.line(b, p0)

    def frame(self, r):
        (x0, y0, x1, y1) = self.p.bounds
        self.p = sg.Polygon(
            [(x0-r, y0-r), (x0-r, y1+r), (x1+r, y1+r), (x1+r, y0-r)],
            [self.p.exterior])

    def zero(self):
        (x0, y0, x1, y1) = self.p.bounds
        self.p = sa.translate(self.p, -x0, -y0)

    def write(self, filename):
        self.zero()
        (_, _, x1, y1) = self.p.bounds
        dwg = svgwrite.Drawing(filename, size=('%fmm' % x1, '%fmm' % y1), viewBox=('0 0 %f %f' % (x1, y1)))
        for lr in [self.p.exterior] + list(self.p.interiors):
            dwg.add(dwg.polygon(list(lr.coords), stroke='red', fill_opacity=0.0, stroke_width=.1))
        dwg.save()

if __name__ == '__main__':
    g = GerberSVG()
    g.read(sys.argv[1])
    g.dilate()
    g.frame(10)
    g.zero()
    # g.addframe()
    g.write('test.svg')
