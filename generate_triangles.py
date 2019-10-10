#!/usr/bin/env python

# standard library
import random
# local library
import inkex
import simplestyle, simpletransform
import voronoi

try:
    from subprocess import Popen, PIPE
except:
    inkex.errormsg(_("Failed to import the subprocess module. Please report this as a bug at: https://bugs.launchpad.net/inkscape."))
    inkex.errormsg(_("Python version is: ") + str(inkex.sys.version_info))
    exit()

def clip_line(x1, y1, x2, y2, w, h):
    if x1 < 0 and x2 < 0:
        return [0, 0, 0, 0]
    if x1 > w and x2 > w:
        return [0, 0, 0, 0]
    if x1 < 0:
        y1 = (y1*x2 - y2*x1)/(x2 - x1)
        x1 = 0
    if x2 < 0:
        y2 = (y1*x2 - y2*x1)/(x2 - x1)
        x2 = 0
    if x1 > w:
        y1 = y1 + (w - x1)*(y2 - y1)/(x2 - x1)
        x1 = w
    if x2 > w:
        y2 = y1 + (w - x1)*(y2 - y1)/(x2 - x1)
        x2 = w
    if y1 < 0 and y2 < 0:
        return [0, 0, 0, 0]
    if y1 > h and y2 > h:
        return [0, 0, 0, 0]
    if x1 == x2 and y1 == y2:
        return [0, 0, 0, 0]
    if y1 < 0:
        x1 = (x1*y2 - x2*y1)/(y2 - y1)
        y1 = 0
    if y2 < 0:
        x2 = (x1*y2 - x2*y1)/(y2 - y1)
        y2 = 0
    if y1 > h:
        x1 = x1 + (h - y1)*(x2 - x1)/(y2 - y1)
        y1 = h
    if y2 > h:
        x2 = x1 + (h - y1)*(x2 - x1)/(y2 - y1)
        y2 = h
    return [x1, y1, x2, y2]

class Pattern(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)
        self.OptionParser.add_option("--size",
                        action="store", type="int",
                        dest="size", default=10,
                        help="Average size of cell (px)")
        self.OptionParser.add_option("--border",
                        action="store", type="int",
                        dest="border", default=0,
                        help="Size of Border (px)")
        self.OptionParser.add_option("--tab",
                        action="store", type="string",
                        dest="tab",
                        help="The selected UI-tab when OK was pressed")

    def effect(self):
        inkex.debug("here")
        if not self.options.ids:
            inkex.errormsg(_("Please select an object"))
            exit()
        scale = self.unittouu('1px')            # convert to document units
        self.options.size *= scale
        self.options.border *= scale
        q = {'x':0,'y':0,'width':0,'height':0}  # query the bounding box of ids[0]

        for query in q.keys():
            p = Popen('inkscape --query-%s --query-id=%s "%s"' % (query, self.options.ids[0], self.args[-1]), shell=True, stdout=PIPE, stderr=PIPE)
            rc = p.wait()
            q[query] = scale*float(p.stdout.read())
        mat = simpletransform.composeParents(self.selected[self.options.ids[0]], [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
        defs = self.xpathSingle('/svg:svg//svg:defs')
        pattern = inkex.etree.SubElement(defs ,inkex.addNS('pattern','svg'))
        pattern.set('id', 'Voronoi' + str(random.randint(1, 9999)))
        pattern.set('width', str(q['width']))
        pattern.set('height', str(q['height']))
        pattern.set('patternTransform', 'translate(%s,%s)' % (q['x'] - mat[0][2], q['y'] - mat[1][2]))
        pattern.set('patternUnits', 'userSpaceOnUse')

        # generate random pattern of points
        c = voronoi.Context()
        pts = []
        b = float(self.options.border)          # width of border
        for i in range(-1, int(q['width']/self.options.size + 2)):
            for j in range(-1, int(q['height']/self.options.size + 2)):
                offset_x = random.random() * self.options.size
                offset_y = random.random() * self.options.size
                pts.append(voronoi.Site(self.options.size * i + offset_x, self.options.size* j + offset_y))
        if len(pts) < 3:
            inkex.errormsg("Please choose a larger object, or smaller cell size")
            exit()

        # plot Voronoi diagram
        sl = voronoi.SiteList(pts)
        c.triangulate = True
        voronoi.voronoi(sl, c)
        path = ""
        for triangle in c.triangles:
            inkex.debug("triangle: " + str(triangle[0]) + ", " + str(triangle[1]) + ", " + str(triangle[2]))
            for i in range(0,3):
                pt1 = triangle[i]
                pt2 = triangle[(i+1)%3]    # two vertices
                [x1, y1, x2, y2] = clip_line(pts[pt1].x, pts[pt1].y, pts[pt2].x, pts[pt2].y, q['width'], q['height'])
                # [x1, y1, x2, y2] = clip_line(c.vertices[pt1][0], c.vertices[pt1][1], c.vertices[pt2][0], c.vertices[pt2][1], q['width'], q['height'])
                path += 'M %.3f,%.3f %.3f,%.3f' % (x1, y1, x2, y2)

        patternstyle = {'stroke': '#000000', 'stroke-width': str(scale)}
        attribs = {'d': path, 'style': simplestyle.formatStyle(patternstyle)}
        inkex.etree.SubElement(pattern, inkex.addNS('path', 'svg'), attribs)

        # link selected object to pattern
        obj = self.selected[self.options.ids[0]]
        style = {}
        if obj.attrib.has_key('style'):
            style = simplestyle.parseStyle(obj.attrib['style'])
        style['fill'] = 'url(#%s)' % pattern.get('id')
        obj.attrib['style'] = simplestyle.formatStyle(style)
        if obj.tag == inkex.addNS('g', 'svg'):
            for node in obj:
                style = {}
                if node.attrib.has_key('style'):
                    style = simplestyle.parseStyle(node.attrib['style'])
                style['fill'] = 'url(#%s)' % pattern.get('id')
                node.attrib['style'] = simplestyle.formatStyle(style)

if __name__ == '__main__':
    e = Pattern()
    e.affect()

# vim: expandtab shiftwidth=4 tabstop=8 softtabstop=4 fileencoding=utf-8 textwidth=99
