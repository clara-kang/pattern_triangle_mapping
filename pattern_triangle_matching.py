#!/usr/bin/env python

# Written by Jabiertxof
# V.06

import inkex, simplepath, simplestyle, simpletransform, sys, re, os
import numpy as np
from lxml import etree

def pathIsTriangle(svg_path):
    # inkex.debug("svg_path[1]: "+ str(svg_path[1][0]))
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

def getTriangleSize(trngle_verts):
    xs = [v[0] for v in trngle_verts]
    ys = [v[1] for v in trngle_verts]
    width = max(xs) - min(xs)
    height = max(ys) - min(ys)
    return width,height

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

    def createLayer(self, id, label):
        layer = etree.Element("{%s}g" % inkex.NSS[u'svg'])
        layer.attrib[u'id'] = id
        layer.attrib["{%s}label"  % inkex.NSS[u'inkscape']] = label
        layer.attrib["{%s}groupmode"  % inkex.NSS[u'inkscape']] = "layer"
        return layer

    def effect(self):
        # search for pattern layer
        pattern_top_layer = self.document.xpath('//svg:g[@id="pattern_layer"]', namespaces=inkex.NSS)
        if len(pattern_top_layer) == 0:
            # append pattern layer
            pattern_top_layer = self.createLayer("pattern_layer", "Pattern Layer")
            triangle_layer = self.createLayer("triangle_sublayer", "Triangle Boundary")
            pattern_layer = self.createLayer("pattern_sublayer", "Pattern")
            pattern_top_layer.append(triangle_layer)
            pattern_top_layer.append(pattern_layer)
            self.document.getroot().append(pattern_top_layer)
        else:
            pattern_top_layer = pattern_top_layer[0]
            triangle_layer = pattern_top_layer.xpath('//svg:g[@id="triangle_sublayer"]', namespaces=inkex.NSS)[0]
            # find triangle in the triangle_layer
            trngl_lyr_children = triangle_layer.getchildren()
            # inkex.debug("trngl_lyr_children"+str(trngl_lyr_children))
            if not len(trngl_lyr_children) == 1:
                inkex.debug("more than 1 element in Triangle Boundary layer: " + str(len(trngl_lyr_children)))
            else:
                bndry_trngle = triangle_layer.getchildren()[0]
                # seems like a path
                if isPath(bndry_trngle):
                    path_string = bndry_trngle.attrib[u'd']
                    svg_path = simplepath.parsePath(path_string)

                    # verified to be triangle
                    if pathIsTriangle(svg_path):
                        self.bndry_trngle_verts = getTriangleVerts(svg_path)
                        self.bndry_trngle_matrx = formMatrix(self.bndry_trngle_verts)
                        inkex.debug("self.bndry_trngle_verts: " + str(self.bndry_trngle_verts))
                        inkex.debug("self.bndry_trngle_matrx: " + str(self.bndry_trngle_matrx))

                        # find pattern
                        self.defs = self.document.xpath('//svg:defs', namespaces=inkex.NSS)[0]
                        patterns = self.defs.xpath('//svg:defs/svg:pattern', namespaces=inkex.NSS)
                        if len(patterns) > 0:
                            self.pattern = patterns[0]
                            pattern_trnsfrm = simpletransform.parseTransform(self.pattern.attrib[u'patternTransform'])
                            scale_x = pattern_trnsfrm[0][0]
                            scale_y = pattern_trnsfrm[1][1]
                            w,h = getTriangleSize(self.bndry_trngle_verts)
                            inkex.debug("w: " + str(w) + ", h: " + str(h))
                            self.pattern.attrib[u'width'] = str(w / scale_x)
                            self.pattern.attrib[u'height'] = str(h / scale_y)
                            # self.pattern.attrib[u'patternTransform' ] = simpletransform.formatTransform([[1, 0, 0],[0, 1, 0]])
                            inkex.debug("pattern: " + str(self.pattern))


        for id,node in self.selected.iteritems():
            if isPath(node):
                path_string = node.attrib[u'd']
                svg_path = simplepath.parsePath(path_string)
                if pathIsTriangle(svg_path):
                    trngle_verts = getTriangleVerts(svg_path)
                    trngle_matrx = formMatrix(trngle_verts)
                    pattern_trnsform = np.matmul(trngle_matrx, np.linalg.inv(self.bndry_trngle_matrx))
                    # pattern_trnsform = [[0.5, 0, 0], [0, 0.5, 0]]
                    initial_trnsform = simpletransform.parseTransform(self.pattern.attrib[u'patternTransform'])
                    final_trnsform = simpletransform.composeTransform(pattern_trnsform[0:3], initial_trnsform)
                    # create transformed pattern
                    pattern_transformed = etree.Element("{%s}pattern" % inkex.NSS[u'svg'])
                    pattern_transformed.attrib[u'id'] = "pattern_for_" + str(id)
                    pattern_transformed.attrib["{%s}collect"  % inkex.NSS[u'inkscape']] = "always"
                    pattern_transformed.attrib["{%s}href"  % inkex.NSS[u'xlink']] = '#' + self.pattern.attrib[u'id']
                    pattern_transformed.attrib[u'patternTransform'] = simpletransform.formatTransform(final_trnsform)
                    # append transformed pattern
                    self.defs.append(pattern_transformed)
                    # fill triangle with pattern
                    trngle_styles = simplestyle.parseStyle(node.attrib[u'style'])
                    trngle_styles[u'fill'] = u'url(#' + str(pattern_transformed.attrib[u'id']) + ')'
                    node.attrib[u'style'] = simplestyle.formatStyle(trngle_styles)

                    inkex.debug("pattern_trnsform: " + str(pattern_trnsform))
                else:
                    inkex.debug("not triangle")

if __name__ == '__main__':
    c = C()
    c.affect()
