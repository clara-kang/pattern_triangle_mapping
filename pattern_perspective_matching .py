#!/usr/bin/env python

# Written by Clara Kang

import inkex, simplepath, simplestyle, simpletransform
import three_transform as three
from lxml import etree

def pathIsTriangle(svg_path):
    if len(svg_path) == 4 and svg_path[1][0] == 'L' and svg_path[2][0] == 'L' and svg_path[3][0] == 'Z':
        return True
    return False

def isPath(node):
    return node.attrib[u'id'].startswith("path")

def getTriangleVerts(svg_path):
    verts = []
    for i in range (0, 3):
        verts.append(svg_path[i][1])
    return verts

def formMatrix(trngle_verts):
    matrx = []
    for i in range (0, 2):
        row = []
        for j in range(0, 3):
            row.append(trngle_verts[j][i])
        matrx.append(row)
    matrx.append([1, 1, 1])
    return matrx


class C(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)
        self.OptionParser.add_option("-p", "--pattern_name",
                                     action="store", type="string",
                                     dest="pattern_name", default="default",
                                     help="Pattern name")

    def createLayer(self, id, label):
        layer = etree.Element("{%s}g" % inkex.NSS[u'svg'])
        layer.attrib[u'id'] = id
        layer.attrib["{%s}label"  % inkex.NSS[u'inkscape']] = label
        layer.attrib["{%s}groupmode"  % inkex.NSS[u'inkscape']] = "layer"
        return layer

    def effect(self):
        pattern = self.selected[self.options.ids[0]]
        paths = [self.selected[self.options.ids[i]] for i in range(0, len(self.options.ids))]
        

if __name__ == '__main__':
    c = C()
    c.affect()
