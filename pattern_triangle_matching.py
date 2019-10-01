#!/usr/bin/env python

# Written by Clara Kang

import inkex, simplepath, simplestyle, simpletransform, sys, re, os
# import numpy as np
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
        # search for pattern layer
        triangle_layer = self.document.xpath('//svg:g[@id="triangle_layer"]', namespaces=inkex.NSS)
        if len(triangle_layer) == 0:
            # append pattern layer
            triangle_layer = self.createLayer("triangle_layer", "Triangle Boundary")
            self.document.getroot().append(triangle_layer)
            inkex.debug("1. draw exactly one triangle in Triangle Boundary layer\n"
                "2. create a pattern composed of only paths\n"
                "3. select triangles that you want to apply pattern to\n"
                "4. enter pattern id (or default to use first pattern), then apply")
        else:
            triangle_layer = triangle_layer[0]
            # find triangle in the triangle_layer
            trngl_lyr_children = triangle_layer.getchildren()
            if not len(trngl_lyr_children) == 1:
                inkex.debug("more or less than 1 element in Triangle Boundary layer: " + str(len(trngl_lyr_children)))
                return
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

                        # find pattern
                        self.defs = self.document.xpath('//svg:defs', namespaces=inkex.NSS)[0]
                        # get first pattern is default
                        if self.options.pattern_name == "default":
                            patterns = self.defs.xpath('./svg:pattern', namespaces=inkex.NSS)
                        # find pattern with name
                        else:
                            patterns = self.defs.xpath('./svg:pattern[@id="' + self.options.pattern_name + '"]', namespaces=inkex.NSS)

                        if len(patterns) > 0:
                            self.pattern = patterns[0]
                            # calculate the size of the pattern so that the pattern repeats exactly once in the bounding triangle
                            # get the union of all paths in pattern and boundary triangle
                            pattern_trngle_union = self.pattern.xpath('.//svg:path', namespaces=inkex.NSS)
                            pattern_trngle_union.append(bndry_trngle)
                            # get bounding box of the union
                            bb_x_min, bb_x_max, bb_y_min, bb_y_max = simpletransform.computeBBox(pattern_trngle_union)
                            # calculate size of union
                            pattern_width = bb_x_max - bb_x_min
                            pattern_height = bb_y_max - bb_y_min
                            # get scaling factor of pattern
                            pattern_trnsfrm = simpletransform.parseTransform(self.pattern.attrib[u'patternTransform'])
                            scale_x = pattern_trnsfrm[0][0]
                            scale_y = pattern_trnsfrm[1][1]
                            # set size of pattern
                            self.pattern.attrib[u'width'] = str(pattern_width / scale_x)
                            self.pattern.attrib[u'height'] = str(pattern_height / scale_y)
                        else:
                            inkex.debug("cannot find pattern")
                            return
                else:
                    inkex.debug("the shape in triangle boundary layer is not a triangle")
                    return

        for id,node in self.selected.iteritems():
            if isPath(node):
                path_string = node.attrib[u'd']
                svg_path = simplepath.parsePath(path_string)
                if pathIsTriangle(svg_path):
                    trngle_verts = getTriangleVerts(svg_path)
                    trngle_matrx = formMatrix(trngle_verts)
                    # apply affine transform
                    pattern_trnsform = three.multiply(trngle_matrx, three.getInverse(self.bndry_trngle_matrx))
                    # compose with initial transform of pattern
                    initial_trnsform = simpletransform.parseTransform(self.pattern.attrib[u'patternTransform'])
                    final_trnsform = simpletransform.composeTransform(pattern_trnsform, initial_trnsform)
                    # if pattern for triangle exists, use it
                    pattern_name = "pattern_for_" + str(id)
                    existing_patterns = self.defs.xpath('./svg:pattern[@id="' + pattern_name + '"]', namespaces=inkex.NSS)
                    if len(existing_patterns) > 0:
                        pattern_transformed = existing_patterns[0]
                    else:
                        # create transformed pattern
                        pattern_transformed = etree.Element("{%s}pattern" % inkex.NSS[u'svg'])
                    # fill in the attributes for pattern
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
                else:
                    inkex.debug("not triangle")

if __name__ == '__main__':
    c = C()
    c.affect()
