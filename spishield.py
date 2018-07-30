import shapely.geometry as sg
import shapely.affinity as sa
import shapely.ops as so

import svgwrite

def sh_zero(sh):
    (x0, y0, x1, y1) = sh.bounds
    return sa.translate(sh, -x0, -y0)

def sh_write(filename, reng, veng, cut):
    args = (
        {'fill':'black', 'stroke_opacity':0.0, 'stroke_width':.0},
        {'stroke':'blue', 'fill_opacity':0.0, 'stroke_width':.1},
        {'stroke':'red', 'fill_opacity':0.0, 'stroke_width':.1},
    )
        
    # sh = reng.union(veng).union(cut)
    sh = cut
    (x0, y0, x1, y1) = sh.bounds
    reng = sa.translate(reng, -x0, -y0)
    veng = sa.translate(veng, -x0, -y0)
    cut = sa.translate(cut, -x0, -y0)
    x1 -= x0
    y1 -= y0
    dwg = svgwrite.Drawing(filename, size=('%fmm' % x1, '%fmm' % y1), viewBox=('0 0 %f %f' % (x1, y1)))
    for args,mp in zip(args, [reng, veng, cut]):
        for p in mp:
            for lr in [p.exterior] + list(p.interiors):
                dwg.add(dwg.polygon(list(lr.coords), **args))
    dwg.save()

def mean(l):
    return sum(l) / float(len(l))

if True and __name__ == '__main__':
    eng = []
    cut = []

    h1 = [2.54 * i for i in range(6)]
    for y in h1:
        eng.append(sg.box(-7.5, y-.38, 3.5, y+.38))
    cut.append(sa.translate(sg.box(-1.25, -7.4, 1.25, 7.4), 0, mean(h1)))

    y = 2.54 * 5 + 13.25
    h2 = [y + 2.54 * i for i in range(3)]
    for y in h2:
        eng.append(sg.box(-7.5, y-.38, 3.5, y+.38))
    cut.append(sa.translate(sg.box(-1.25, -4.2, 1.25, 4.2), 0, mean(h2)))

    (x0, y0, x1, y1) = sg.MultiPolygon(eng).bounds
    r = 2.0
    cut.append(sg.box(x0 - r, y0 - r, x1 + r, y1 + r))

    eng = sg.MultiPolygon(eng)
    cut = sg.MultiPolygon(cut)
    sh_write('test.svg', eng, sg.MultiPolygon([]), cut)
