import sys
import os
import re
try:
    from subprocess import Popen, PIPE
    bsubprocess = True
except:
    bsubprocess = False
# local library
import inkex
import simplepath
import cubicsuperpath
import simpletransform
from ffgeom import *

# third party
try:
    import numpy
except:
    # Initialize gettext for messages outside an inkex derived class
    inkex.localize()
    inkex.errormsg(_("Failed to import the numpy or numpy.linalg modules. These modules are required by this extension. Please install them and try again.  On a Debian-like system this can be done with the command, sudo apt-get install python-numpy."))
    exit()

class Project(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)
        self.OptionParser.add_option("-p", "--pattern_name",
                                     action="store", type="string",
                                     dest="pattern_name", default="default",
                                     help="Pattern name")
    def effect(self):
        if len(self.options.ids) < 2:
            inkex.errormsg(_("This extension requires two selected paths."))
            exit()

        #obj is selected second
        scale = self.unittouu('1px')    # convert to document units
        obj = self.selected[self.options.ids[0]]
        envelope = self.selected[self.options.ids[1]]
        if obj.get(inkex.addNS('type','sodipodi')):
            inkex.errormsg(_("The first selected object is of type '%s'.\nTry using the procedure Path->Object to Path." % obj.get(inkex.addNS('type','sodipodi'))))
            exit()
        if obj.tag == inkex.addNS('path','svg') or obj.tag == inkex.addNS('g','svg'):
            if envelope.tag == inkex.addNS('path','svg'):
                mat = simpletransform.composeParents(envelope, [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
                path = cubicsuperpath.parsePath(envelope.get('d'))
                if len(path) < 1 or len(path[0]) < 4:
                    inkex.errormsg(_("This extension requires that the second selected path be four nodes long."))
                    exit()
                simpletransform.applyTransformToPath(mat, path)
                dp = numpy.zeros((4,2))
                for i in range(4):
                    dp[i][0] = path[0][i][1][0]
                    dp[i][1] = path[0][i][1][1]

                inkex.debug("dp: " + str(dp))
                #query inkscape about the bounding box of obj
                q = {'x':0,'y':0,'width':0,'height':0}
                file = self.args[-1]
                id = self.options.ids[0]
                for query in q.keys():
                    if bsubprocess:
                        p = Popen('inkscape --query-%s --query-id=%s "%s"' % (query,id,file), shell=True, stdout=PIPE, stderr=PIPE)
                        rc = p.wait()
                        q[query] = scale*float(p.stdout.read())
                        err = p.stderr.read()
                    else:
                        f,err = os.popen3('inkscape --query-%s --query-id=%s "%s"' % (query,id,file))[1:]
                        q[query] = scale*float(f.read())
                        f.close()
                        err.close()
                sp = numpy.array([[q['x'], q['y']+q['height']],[q['x'], q['y']],[q['x']+q['width'], q['y']],[q['x']+q['width'], q['y']+q['height']]])
                # inkex.debug("sp: " + str(sp))
            else:
                if envelope.tag == inkex.addNS('g','svg'):
                    inkex.errormsg(_("The second selected object is a group, not a path.\nTry using the procedure Object->Ungroup."))
                else:
                    inkex.errormsg(_("The second selected object is not a path.\nTry using the procedure Path->Object to Path."))
                exit()
        else:
            inkex.errormsg(_("The first selected object is not a path.\nTry using the procedure Path->Object to Path."))
            exit()

        self.q = q

        mat_y = numpy.array([[dp[0][1], dp[1][1]], [dp[3][1], dp[2][1]]])
        mat_x = numpy.array([[dp[0][0], dp[1][0]], [dp[3][0], dp[2][0]]])
        term1 = 1.0 / ( q['width'] * q['height'])
        inkex.debug("term1: " + str(term1))

        if obj.tag == inkex.addNS("path",'svg'):
            self.process_path(obj,mat_x, mat_y, term1)
        if obj.tag == inkex.addNS("g",'svg'):
            self.process_group(obj,mat_x, mat_y, term1)

    def process_group(self,group,mat_x, mat_y, term1):
        for node in group:
            if node.tag == inkex.addNS('path','svg'):
                self.process_path(node,mat_x, mat_y, term1)
            if node.tag == inkex.addNS('g','svg'):
                self.process_group(node,mat_x, mat_y, term1)

    def process_path(self,ipath,mat_x, mat_y, term1):
        mat = simpletransform.composeParents(ipath, [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
        path_string = ipath.get('d')
        svg_path = simplepath.parsePath(path_string)

        paths = []

        # for path in svg_path:
        # inkex.debug("svg_path: " + str(svg_path))
        for path in svg_path:
            if path[0] == 'M' or path[0] == 'L':
                paths.append([path[0], [path[1]]])
            elif path[0] == 'C':
                pts = []
                for i in range(0, 3):
                    pt = [path[1][2*i], path[1][2*i+1]]
                    pts.append(pt)
                paths.append(['C', pts])
            elif path[0] == 'Z':
                paths.append(['Z', []])


        # inkex.debug("paths: " + str(paths) + "\n\n")
        mat = simpletransform.invertTransform(mat)
        # simpletransform.applyTransformToPath(mat, p)
        for path in paths:
            for pt in path[1]:
                simpletransform.applyTransformToPoint(mat, pt)

        # do transformation
        for path in paths:
            for pt in path[1]:
                self.project_point(pt,mat_x, mat_y, term1)

        # back to original form
        res_paths = []
        for path in paths:
            if path[0] == 'C':
                flat_pts = []
                for pt in path[1]:
                    flat_pts.append(pt[0])
                    flat_pts.append(pt[1])
                res_paths.append(['C', flat_pts])
            elif path[0] == 'M' or path[0] == 'L':
                res_paths.append([path[0], path[1][0]])
            elif path[0] == 'Z':
                res_paths.append(path)
        # inkex.debug("res_paths: " + str(res_paths))
        res_svg_paths = simplepath.formatPath(res_paths)
        # inkex.debug("res_svg_paths: " + str(res_svg_paths))
        ipath.set('d', res_svg_paths)

    def project_point(self,p,mat_x, mat_y, term1):
        x = p[0]
        y = p[1]
        term2 = numpy.array([self.q['x']+self.q['width'] - x, x - self.q['x']])
        inkex.debug("term2: " + str(term2))
        term3 = numpy.array([y - self.q['y'], self.q['y']+self.q['height']-y])
        inkex.debug("term3: " + str(term3))
        x_map = term1 * numpy.matmul(numpy.matmul(term2, mat_x), term3.T)
        y_map = term1 * numpy.matmul(numpy.matmul(term2, mat_y), term3.T)
        inkex.debug("x_map: " + str(x_map))
        p[0] = x_map
        p[1] = y_map

if __name__ == '__main__':
    e = Project()
    e.affect()


# vim: expandtab shiftwidth=4 tabstop=8 softtabstop=4 fileencoding=utf-8 textwidth=99
