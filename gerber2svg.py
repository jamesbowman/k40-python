import sys
import re

import shapely.geometry as sg
import shapely.affinity as sa
import shapely.ops as so

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
        self.apertures = {}

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
            elif c2 == 'AD':
                args = [self.scale * float(v) for v in c[7:].split('X')]
                self.apertures[c[3:5]] = (c[5], args)

    def inches(self, _):
        self.scale = 25.4

    def set_aperture(self, m):
        self.aperture = m.group(1)

    def draw_aperture(self, x, y):
        (name, mods) = self.apertures[self.aperture]
        if name == 'R':
            (w,h) = mods
            p = sa.translate(sg.box(-w / 2, -h / 2, w / 2, h / 2), x, y)
            self.polys.append(p)
        elif name == 'C':
            (r, ) = mods
            self.polys.append(sg.Point(x, y).buffer(r))
            assert 0

    def function_code(self, cmd):
        ignore = lambda(m): None
        
        def handle_xyd(m):
            x =  self.scale * int(m.group(1)) / (10. ** self.xprec)
            y = -self.scale * int(m.group(2)) / (10. ** self.yprec)
            d = m.group(3)
            p = Point(x, y)
            if d == '01':
                self.line(self.pos, p)
            elif d == '03':
                print('draw ap', self.apertures[self.aperture])
                self.draw_aperture(x, y)
            self.pos = p

        actions = [(re.compile(p), a) for (p, a) in [
            (r'G01X([0-9]*)Y([0-9]*)D(0[123])', handle_xyd),
            (r'X([0-9]*)Y([0-9]*)D(0[123])', handle_xyd),
            (r'G01', ignore),
            (r'G54D..', ignore),
            (r'G04.*', ignore),
            (r'G75', ignore),   # circular arcs
            (r'G70', self.inches),
            (r'D([1-9][0-9])', self.set_aperture),   # aperture
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
        self.polys = []

    def line(self, p0, p1):
        if self.poly == []:
            self.poly = [p0, p1]
        elif self.poly[-1] == p0:
            self.poly.append(p1)
        else:
            pp = [p.tuple() for p in self.poly]
            if len(pp) < 3:
                (name, mods) = self.apertures[self.aperture]
                if name == 'C':
                    self.polys.append(sg.LineString(pp).buffer(self.radius))
            else:
                self.polys.append(sg.Polygon(pp).buffer(self.radius))
            self.poly = [p0, p1]
        (name, mods) = self.apertures[self.aperture]
        if name == 'C':
            self.radius = mods[0] / 2
        else:
            self.radius = 0

    def finish(self, _):
        m = self.polys[0]
        for p in self.polys[1:]:
            m = m.union(p)
        self.p = m

class Shape:
    def dilate(self):
        self.p = self.p.buffer(0.10)

    def frame(self, r):
        (x0, y0, x1, y1) = self.p.bounds
        self.p = sg.Polygon(
            [(x0-r, y0-r), (x0-r, y1+r), (x1+r, y1+r), (x1+r, y0-r)],
            [self.p.exterior])
        for (x,y) in [(x0-r/2,y0-r/2), (x1+r/2,y0-r/2), (x1+r/2,y1+r/2), (x0-r/2,y1+r/2)]:
            drill = sg.Point(x, y).buffer(1.2)
            g.p = g.p.symmetric_difference(drill)

    def zero(self):
        (x0, y0, x1, y1) = self.p.bounds
        self.p = sa.translate(self.p, -x0, -y0)

    def write(self, filename):
        self.zero()
        (_, _, x1, y1) = self.p.bounds
        dwg = svgwrite.Drawing(filename, size=('%fmm' % x1, '%fmm' % y1), viewBox=('0 0 %f %f' % (x1, y1)))
        for p in [self.p]:
            for lr in [p.exterior] + list(p.interiors):
                dwg.add(dwg.polygon(list(lr.coords), stroke='red', fill_opacity=0.0, stroke_width=.1))
        dwg.save()

def sh_frame(sh, r):
    (x0, y0, x1, y1) = sh.bounds
    sh = sg.Polygon(
        [(x0-r, y0-r), (x0-r, y1+r), (x1+r, y1+r), (x1+r, y0-r)],
        [sh.exterior])
    return sh

def sh_frame_screws(sh, r):
    (x0, y0, x1, y1) = sh.bounds
    sh = sg.Polygon(
        [(x0-r, y0-r), (x0-r, y1+r), (x1+r, y1+r), (x1+r, y0-r)],
        [sh.exterior])
    for (x,y) in [(x0-r/2,y0-r/2), (x1+r/2,y0-r/2), (x1+r/2,y1+r/2), (x0-r/2,y1+r/2)]:
        drill = sg.Point(x, y).buffer(1.2)
        sh = sh.symmetric_difference(drill)
    return sh

def sh_zero(sh):
    (x0, y0, x1, y1) = sh.bounds
    return sa.translate(sh, -x0, -y0)

def sh_write(filename, sh, cutmode = 0):
    args = {
        0: {'stroke':'red', 'fill_opacity':0.0, 'stroke_width':.1},
        1: {'stroke':'blue', 'fill_opacity':0.0, 'stroke_width':.1},
        2: {'fill':'black', 'stroke_opacity':0.0, 'stroke_width':.0},
    }[cutmode]
        
    sh = sh_zero(sh)
    (_, _, x1, y1) = sh.bounds
    dwg = svgwrite.Drawing(filename, size=('%fmm' % x1, '%fmm' % y1), viewBox=('0 0 %f %f' % (x1, y1)))
    for p in sh:
        for lr in [p.exterior] + list(p.interiors):
            dwg.add(dwg.polygon(list(lr.coords), **args))
    dwg.save()

class GerberSVG(Gerber, GerberShape, Shape):
    pass

def plate(buf = None, usb_slot = False):
    if 0:
        g = GerberSVG()
        g.read(sys.argv[1])
        g.dilate()
    else:
        sh = sg.box(0, 0, 61.85, 48.50)
    sh = sh_zero(sh_frame_screws(sh, 9))
    if buf:
        i = list(sh.interiors)
        shrunk = sg.Polygon(i[0]).buffer(buf)
        sh = sg.Polygon(
            sh.exterior,
            [shrunk.exterior] + i[1:])
    if usb_slot:
        sh = sh.symmetric_difference(sg.box(0, 11, 6.5, 21))
    return sh

def sh_abut(a, b):
    (_, _, x1, y1) = a.bounds
    return sa.translate(b, 0, y1)

if False and __name__ == '__main__':
    if 0:
        l0 = plate(buf = .1, usb_slot = True)
        l1 = sh_abut(l0, plate(buf = -0.9))
        l2 = sh_abut(l1, plate(buf = -0.9))
        l3 = sh_abut(l2, plate(buf = .2))
        a = sg.MultiPolygon([l0, l1, l2, l3])
        a = sa.rotate(a, 90)
    else:
        g = GerberSVG()
        g.read(sys.argv[1])
        g.dilate()
        a = sg.MultiPolygon([sh_frame(g.p, 10.0)])
    sh_write('test.svg', a)

if True and __name__ == '__main__':
    g = GerberSVG()
    g.read(sys.argv[1])
    a = sg.MultiPolygon([g.p])
    sh_write('test.svg', g.p, 2)
