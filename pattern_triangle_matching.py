#!/usr/bin/env python

# Written by Jabiertxof
# V.06

import inkex, sys, re, os
from lxml import etree

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
            # append patter layer
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
                inkex.debug("bndry_trngle: " + str(bndry_trngle.keys()))


        for id,node in self.selected.iteritems():
            type_attr = node.xpath("@sodipodi:type", namespaces=inkex.NSS)
            side_attr = node.xpath("@sodipodi:sides", namespaces=inkex.NSS)
            if type_attr and type_attr[0] == "star" and side_attr[0] == "3":
                inkex.debug("triangle")
            else:
                inkex.debug("not triangle")

if __name__ == '__main__':
    c = C()
    c.affect()
