#!/usr/bin/env python

# standard library
import random
import numpy as np
import math
# local library
import inkex
import simplestyle, simpletransform, simplepath
import voronoi
import curve_line_intrsctns as curve_utils

try:
    from subprocess import Popen, PIPE
except:
    inkex.errormsg(_("Failed to import the subprocess module. Please report this as a bug at: https://bugs.launchpad.net/inkscape."))
    inkex.errormsg(_("Python version is: ") + str(inkex.sys.version_info))
    exit()

# global variables, remove remove later

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

def getSignedAngle(vec1, vec2):
    # inkex.debug("vec1: " + str(vec1))
    # inkex.debug("vec2: " + str(vec2))
    a = np.dot(vec1, vec2) / ( np.linalg.norm(vec1)  * np.linalg.norm(vec2))
    angle = math.acos(np.dot(vec1, vec2) / ( np.linalg.norm(vec1)  * np.linalg.norm(vec2)))
    # inkex.debug("angle: " + str(angle * 180 / 3.14159))
    vec1_3d = np.append(vec1, 0)
    vec2_3d = np.append(vec2, 0)

    cross_prdct = np.cross(vec1_3d, vec2_3d)
    if (cross_prdct[2] <= 0):
        return -angle
    else:
        return angle

# return true if ccw, false if cw
def pathCCW(paths):
    angle_sum = 0
    vec1 = paths[-1][1] - paths[-1][0]
    for path in paths:
        # inkex.debug("path----")
        # bezier curve
        if (len(path) == 4):
            for i in range(0, 3):
                # overlapping points
                if np.array_equal(path[i+1], path[i]):
                    continue
                vec2 = path[i+1] - path[i]
                angle_sum += getSignedAngle(vec1, vec2)
                vec1 = vec2
        else:
            if np.array_equal(path[1], path[0]):
                continue
            vec2 = path[1] - path[0]
            angle_sum += getSignedAngle(vec1, vec2)
            vec1 = vec2

    if angle_sum >= 0:
        return True
    return False


def generatePoints(svg_path):
    # find orientation of paths
    sx, sy = svg_path[0][1][0], svg_path[0][1][1]
    paths = []

    # for path in svg_path:
    #     inkex.debug("svg_path: " + str(path))
    for path in svg_path:
        # bezier curve
        if path[0] == 'C':
            px = [sx] + [path[1][i] for i in range(0, 5, 2)]
            py = [sy] + [path[1][i] for i in range(1, 6, 2)]
            paths.append(np.array([np.array(pt) for pt in zip(px, py)]))

            sx, sy = px[-1], py[-1]
            curve_len = curve_utils.bezier_length(paths[-1])
            # inkex.debug("curve_len: " + str(curve_len))

        elif path[0] == 'L':
            ex, ey = path[1][0], path[1][1]
            paths.append(np.array([np.array([sx, sy]), np.array([ex, ey])]))
            sx, sy = ex, ey

        elif path[0] == 'Z' and len(paths[-1]) == 2:
            paths.append(np.array([np.array([sx, sy]), np.array([svg_path[0][1][0], svg_path[0][1][1]])]))

    if pathCCW(paths):
        inkex.debug("path ccw")
    else:
        inkex.debug("path cw")


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
        node = self.selected.values()[0]
        path_string = node.attrib[u'd']
        svg_path = simplepath.parsePath(path_string)

        pts = generatePoints(svg_path)

        # c = voronoi.Context()
        # pts = []
        # b = float(self.options.border)          # width of border
        # for i in range(-1, int(q['width']/self.options.size + 2)):
        #     for j in range(-1, int(q['height']/self.options.size + 2)):
        #         offset_x = random.random() * self.options.size * 0.25
        #         offset_y = random.random() * self.options.size * 0.25
        #         pts.append(voronoi.Site(self.options.size * i + offset_x, self.options.size* j + offset_y))
        # if len(pts) < 3:
        #     inkex.errormsg("Please choose a larger object, or smaller cell size")
        #     exit()

        # # plot Voronoi diagram
        # sl = voronoi.SiteList(pts)
        # c.triangulate = True
        # voronoi.voronoi(sl, c)
        # path = ""
        # for triangle in c.triangles:
        #     inkex.debug("triangle: " + str(triangle[0]) + ", " + str(triangle[1]) + ", " + str(triangle[2]))
        #     for i in range(0,3):
        #         pt1 = triangle[i]
        #         pt2 = triangle[(i+1)%3]    # two vertices
        #         [x1, y1, x2, y2] = clip_line(pts[pt1].x, pts[pt1].y, pts[pt2].x, pts[pt2].y, q['width'], q['height'])
        #         # [x1, y1, x2, y2] = clip_line(c.vertices[pt1][0], c.vertices[pt1][1], c.vertices[pt2][0], c.vertices[pt2][1], q['width'], q['height'])
        #         path += 'M %.3f,%.3f %.3f,%.3f' % (x1, y1, x2, y2)
        #
        # patternstyle = {'stroke': '#000000', 'stroke-width': str(scale)}
        # attribs = {'d': path, 'style': simplestyle.formatStyle(patternstyle)}
        # inkex.etree.SubElement(pattern, inkex.addNS('path', 'svg'), attribs)
        #
        # # link selected object to pattern
        # obj = self.selected[self.options.ids[0]]
        # style = {}
        # if obj.attrib.has_key('style'):
        #     style = simplestyle.parseStyle(obj.attrib['style'])
        # style['fill'] = 'url(#%s)' % pattern.get('id')
        # obj.attrib['style'] = simplestyle.formatStyle(style)
        # if obj.tag == inkex.addNS('g', 'svg'):
        #     for node in obj:
        #         style = {}
        #         if node.attrib.has_key('style'):
        #             style = simplestyle.parseStyle(node.attrib['style'])
        #         style['fill'] = 'url(#%s)' % pattern.get('id')
        #         node.attrib['style'] = simplestyle.formatStyle(style)

if __name__ == '__main__':
    e = Pattern()
    e.affect()

# vim: expandtab shiftwidth=4 tabstop=8 softtabstop=4 fileencoding=utf-8 textwidth=99
