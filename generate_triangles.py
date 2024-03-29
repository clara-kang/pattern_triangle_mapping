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

threshold = 2.0

class Point:
    # 1 for vertex point, 2 for edge point, 3 for internal point
    timestamp = 0

    def __init__(self, type, loc, normal=np.array([1, 0])):
        self.type = type
        self.loc = loc
        self.normal = normal
        self.timestamp = Point.timestamp
        Point.timestamp += 1

    def __str__(self):
        if self.type == 1:
            type_str = "v"
        elif self.type == 2:
            type_str = "e"
        else:
            type_str = "i"
        return "type: " + type_str + ", loc" + str(self.loc)


def getSignedAngle(vec1, vec2):
    a = np.dot(vec1, vec2) / ( np.linalg.norm(vec1)  * np.linalg.norm(vec2))
    if a >= 1: # vector parallel, angle is 0
        return 0
    angle = math.acos(np.dot(vec1, vec2) / ( np.linalg.norm(vec1)  * np.linalg.norm(vec2)))
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

def getPathLen(path):
    if len(path) == 2:
        return np.linalg.norm(path[1] - path[0])
    else:
        return curve_utils.bezier_length(path)

def pathEval(path, t):
    if len(path) == 2:
        return path[0] + t * (path[1] - path[0])
    else:
        return curve_utils.bezier_eval(path, t)

def getTAtLen(path, st, length):
    if len(path) == 2:
        dt = length / getPathLen(path)
        return st + dt
    else:
        return curve_utils.get_t_at_length(path, st, length)

def getNormalAtT(path, t, ccw):
    if len(path) == 2:
        return curve_utils.line_normal(path, ccw)
    else:
        return curve_utils.bezier_normal(path, t, ccw)

def pointInPath(paths, pt_loc):
    ray_dir = np.array([1.0, 0.0])
    pt_end = pt_loc + 2.0 * ray_dir
    intrsctns = 0
    for path in paths:
        if len(path) == 2:
            intrsc_pts = curve_utils.intersect_line_ray(path, [pt_loc, pt_end])
        else:
            intrsc_pts = curve_utils.intersect_bezier_line(path, [pt_loc, pt_end], True)
        intrsctns += len(intrsc_pts)

    if intrsctns % 2 == 1:
        return True
    return False

def generateInternalPoints(paths, pts, spacing):
    Pm = spacing / math.sqrt(2) # min dist between any two points

    pw = [] # existing points
    pm = [] # to process later

    def genFront(point):
        pt_loc = point.loc + spacing * point.normal
        return Point(3, pt_loc, point.normal)

    def genLeft(point):
        left_dir = curve_utils.rotate90ccw(point.normal)
        pt_loc = point.loc + spacing * left_dir
        return Point(3, pt_loc, left_dir)

    def genRight(point):
        right_dir = curve_utils.rotate90cw(point.normal)
        pt_loc = point.loc + spacing * right_dir
        return Point(3, pt_loc, right_dir)

    def getClosestPt(point_loc):
        min_dist = float("inf")
        for pt in pm:
            dist_2_pt = np.linalg.norm(pt.loc - point_loc)
            if dist_2_pt < min_dist:
                min_dist = dist_2_pt
                closest_pt = pt
        if min_dist < Pm:
            return closest_pt
        return None

    def mergePoints(point1, point2): # point1 not yet added to pm or pw
        def delFromPmPw(point):
            try:
                pm.remove(point2)
                pw.remove(point2)
            except ValueError:
                pass
        def takeAvg(pt1, pt2):
            return Point(3, 0.5*(pt1.loc + pt2.loc))

        if point1.type == 3:
            if point2.type != 3:
                return None
            else:
                avgPoint = takeAvg(point1, point2)
                delFromPmPw(point2)
                return avgPoint
        else:
            delFromPmPw(point2)
            return point1

    for point in pts:
        if point.type == 2:
            pw.append(point)
        pm.append(point)

    while len(pw) > 0:
        pt = pw[0]
        pt_nbs = [genFront(pt), genLeft(pt), genRight(pt)]
        for pt_nb in pt_nbs:
            if pointInPath(paths, pt_nb.loc):
                closest_pt = getClosestPt(pt_nb.loc)
                if closest_pt == None: # point survives
                    pm.append(pt_nb)
                    pw.append(pt_nb)
                else:
                    merged_pt = mergePoints(pt_nb, closest_pt)
                    while closest_pt != None and merged_pt != None: # keep merging until no point nearby or point get eaten
                        closest_pt = getClosestPt(merged_pt.loc)
                        if closest_pt != None:
                            merged_pt = mergePoints(pt_nb, closest_pt)
                    if merged_pt != None:
                        pm.append(merged_pt)
        pw.pop(0)
    return pm

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

    def generatePoints(self, svg_path, spacing):
        # find orientation of paths
        sx, sy = svg_path[0][1][0], svg_path[0][1][1]
        self.paths = []

        for path in svg_path:
            # bezier curve
            if path[0] == 'C':
                px = [sx] + [path[1][i] for i in range(0, 5, 2)]
                py = [sy] + [path[1][i] for i in range(1, 6, 2)]
                self.paths.append(np.array([np.array(pt) for pt in zip(px, py)]))

                sx, sy = px[-1], py[-1]
                # curve_len = curve_utils.bezier_length(paths[-1])

            elif path[0] == 'L':
                ex, ey = path[1][0], path[1][1]
                self.paths.append(np.array([np.array([sx, sy]), np.array([ex, ey])]))
                sx, sy = ex, ey
            elif path[0] == 'Z' and (not np.isclose(self.paths[-1][-1], self.paths[0][0]).all()): # does not end at start, add segment connecting them
                self.paths.append(np.array([np.array([sx, sy]), np.array([svg_path[0][1][0], svg_path[0][1][1]])]))
        ccw = pathCCW(self.paths)

        points = []
        for path in self.paths:
            v_pt = Point(1, path[0]) # vertex points
            points.append(v_pt)

            path_len = getPathLen(path)
            segs_num = math.floor(path_len/spacing)

            if segs_num == 0:
                continue

            adj_spacing = path_len / segs_num
            last_t = 0
            for i in range (1, int(segs_num)):
                t = getTAtLen(path, last_t, adj_spacing)
                e_pt_loc = pathEval(path, t)
                e_pt_norm = getNormalAtT(path, t, ccw)
                e_pt = Point(2, e_pt_loc, e_pt_norm) # vertex points
                points.append(e_pt)
                last_t = t

        pm = generateInternalPoints(self.paths, points, spacing)
        return pm

    def display_pts(self, pts):
        # create new layer to contain all points
        points_layer = inkex.etree.SubElement(self.document.getroot(), inkex.addNS('g', 'svg'))
        points_layer.set('id', "points_layer" + str(random.randint(1, 9999)))
        points_layer.set("{%s}label" % inkex.NSS[u'inkscape'], "points_layer")
        points_layer.set("{%s}groupmode"  % inkex.NSS[u'inkscape'], "layer")

        # group for points
        points_group = inkex.etree.SubElement(points_layer, inkex.addNS('g', 'svg'))

        # display points
        for point in pts:
            if point.type == 1:
                style = "fill:#ff0000;fill-opacity:1;stroke:none;stroke-width:0.26458332;stroke-opacity:1"
            elif point.type == 2:
                style = "fill:#0000ff;fill-opacity:1;stroke:none;stroke-width:0.26458332;stroke-opacity:1"
            elif point.type == 3:
                style = "fill:#00ff00;fill-opacity:1;stroke:none;stroke-width:0.26458332;stroke-opacity:1"
            elif point.type == 4:
                style = "fill:#000000;fill-opacity:1;stroke:none;stroke-width:0.26458332;stroke-opacity:1"
            attribs = {'cx': str(point.loc[0]), 'cy': str(point.loc[1]), 'r':str(1.0), 'style': style}
            inkex.etree.SubElement(points_group, inkex.addNS('circle', 'svg'), attribs)

    def createElem(self, path, group, fillcolor):
        style = "fill:" + fillcolor + ";stroke:#000000;stroke-width:0.26458332px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1"
        attribs = {'d': path, 'style': style}
        elem_path = inkex.etree.SubElement(group, inkex.addNS('path', 'svg'), attribs)
        elem_path.set("{%s}connector-curvature" % inkex.NSS[u'inkscape'], "0")

    def createPath(self, verts):
        path = 'M'
        for vert in verts:
            coord_str = '%.3f,%.3f' % (vert.loc[0], vert.loc[1])
            path = path + ' ' + coord_str
        path = path + ' z'
        return path

    def display_triangles(self, pts, triangle_used, triangles):
        # create triangles layer
        triangle_layer = inkex.etree.SubElement(self.document.getroot(), inkex.addNS('g', 'svg'))
        triangle_layer.set('id', "triangle_layer" + str(random.randint(1, 9999)))
        triangle_layer.set("{%s}label" % inkex.NSS[u'inkscape'], "triangle_layer")
        triangle_layer.set("{%s}groupmode"  % inkex.NSS[u'inkscape'], "layer")

        # group for triangles
        triangles_group = inkex.etree.SubElement(triangle_layer, inkex.addNS('g', 'svg'))

        for trnl_id in range(len(triangles)):
            triangle = triangles[trnl_id]
            if not triangle_used[trnl_id]:
                verts = [pts[triangle[i]] for i in range(3)]
                path = self.createPath(verts)
                self.createElem(path, triangles_group, "#a6e2ff")

    def display_quads(self, pts, quads):
        # create triangles layer
        quad_layer = inkex.etree.SubElement(self.document.getroot(), inkex.addNS('g', 'svg'))
        quad_layer.set('id', "triangle_layer" + str(random.randint(1, 9999)))
        quad_layer.set("{%s}label" % inkex.NSS[u'inkscape'], "quad_layer")
        quad_layer.set("{%s}groupmode"  % inkex.NSS[u'inkscape'], "layer")

        # group for triangles
        # quad_group = inkex.etree.SubElement(quad_layer, inkex.addNS('g', 'svg'))

        for quad in quads:
            verts = [pts[quad[i]] for i in range(4)]
            path = self.createPath(verts)
            self.createElem(path, quad_layer, "#ffa4a4")

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

        # generate random pattern of points
        node = self.selected.values()[0]
        path_string = node.attrib[u'd']
        svg_path = simplepath.parsePath(path_string)

        pts = self.generatePoints(svg_path, self.options.size)
        self.display_pts(pts)

        c = voronoi.Context()
        pts_to_trig = []
        for point in pts:
            pts_to_trig.append(voronoi.Site(point.loc[0], point.loc[1]))

        # triangulate with library
        sl = voronoi.SiteList(pts_to_trig)
        c.triangulate = True
        voronoi.voronoi(sl, c)

        edge_to_triangle = {}
        triangle_timestamps = [0] * len(c.triangles)
        triangle_used = [False] * len(c.triangles)
        quads = []

        def getTriangularMidPoint(pt1, pt2, pt3):
            mid_2_3 = pt2.loc + 0.5 * (pt3.loc - pt2.loc)
            mid_1_3 = pt1.loc + 0.5 * (pt3.loc - pt1.loc)
            return curve_utils.intersect_line_line([pt1.loc, mid_2_3], [pt2.loc, mid_1_3])[0]

        def rejectOutofRangeTringl():
            for trngl_indx in range(len(c.triangles)):
                triangle = c.triangles[trngl_indx]
                if pts[triangle[0]].type != 3 and pts[triangle[1]].type != 3 and pts[triangle[2]].type != 3:
                    triangle_midpt = getTriangularMidPoint(pts[triangle[0]], pts[triangle[1]], pts[triangle[2]])
                    if not pointInPath(self.paths, triangle_midpt):
                        triangle_used[trngl_indx] = True

        rejectOutofRangeTringl()

        for trngl_indx in range(len(c.triangles)):
            triangle = c.triangles[trngl_indx]
            # compute timestamp for each triangle
            verts = [pts[triangle[i]] for i in range(3)]
            min_tstmp = min([vert.timestamp for vert in verts])
            triangle_timestamps[trngl_indx] = min_tstmp
            # build edge_to_triangle
            for j in range(0, 3):
                id1 = triangle[j]
                id2 = triangle[(j+1)%3]
                if id1 < id2:
                    edge = (id1, id2)
                else:
                    edge = (id2, id1)
                if edge in edge_to_triangle:
                    edge_to_triangle[edge].append(trngl_indx)
                else:
                    edge_to_triangle[edge] = [trngl_indx]

        def getThirdInkex(triangle, edge):
            for id in triangle:
                if id not in edge:
                    return id

        def getEdgeLen(pt1, pt2):
            return np.linalg.norm(pt1.loc - pt2.loc)

        def getAngle(pt1, pt2, pt3):
            vec1 = pt1.loc - pt2.loc
            vec2 = pt3.loc - pt2.loc
            angle = np.dot(vec1, vec2 ) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
            return math.acos(angle)

        def matchLongestEdge(matchTimestamp):
            # process triangles
            for edge in edge_to_triangle:
                if len(edge_to_triangle[edge]) == 2:
                    tringl1, tringl2 = edge_to_triangle[edge]
                    # skip if either triangle used
                    if triangle_used[tringl1] or triangle_used[tringl2]:
                        continue
                    if matchTimestamp and triangle_timestamps[tringl1] != triangle_timestamps[tringl2]:
                        continue

                    # get third index of triangle
                    third_id1 = getThirdInkex(c.triangles[tringl1], edge)
                    third_id2 = getThirdInkex(c.triangles[tringl2], edge)
                    # get edge length
                    edge_len = getEdgeLen(pts[edge[0]], pts[edge[1]])
                    # get other edges length
                    trigl1_edge_len = [getEdgeLen(pts[edge[0]], pts[third_id1]), getEdgeLen(pts[edge[1]], pts[third_id1])]
                    trigl2_edge_len = [getEdgeLen(pts[edge[0]], pts[third_id2]), getEdgeLen(pts[edge[1]], pts[third_id2])]
                    # check if the connecting edge is longest edge of both triangles
                    if all(edge_len >= el for el in trigl1_edge_len) and all(edge_len >= el for el in trigl2_edge_len):
                        # if yes, create quadrilateral
                        quads.append([edge[0], third_id1, edge[1], third_id2])
                        triangle_used[tringl1] = True
                        triangle_used[tringl2] = True

        def createNiceQuads(matchTimestamp):
            # process triangles
            for edge in edge_to_triangle:
                if len(edge_to_triangle[edge]) == 2:
                    tringl1, tringl2 = edge_to_triangle[edge]
                    # skip if either triangle used
                    if triangle_used[tringl1] or triangle_used[tringl2]:
                        continue
                    if matchTimestamp and triangle_timestamps[tringl1] != triangle_timestamps[tringl2]:
                        continue

                    # get third index of triangle
                    third_id1 = getThirdInkex(c.triangles[tringl1], edge)
                    third_id2 = getThirdInkex(c.triangles[tringl2], edge)
                    # get edge length
                    quad_lens = []
                    edge_len = getEdgeLen(pts[edge[0]], pts[edge[1]])
                    # get other edges length
                    quad_lens.extend([getEdgeLen(pts[edge[0]], pts[third_id1]), getEdgeLen(pts[edge[1]], pts[third_id1])])
                    quad_lens.extend([getEdgeLen(pts[edge[0]], pts[third_id2]), getEdgeLen(pts[edge[1]], pts[third_id2])])
                    avg_quad_len = sum(quad_lens)/len(quad_lens)
                    len_diff = 0
                    for quad_len in quad_lens:
                        len_diff += abs(quad_len - avg_quad_len)/avg_quad_len

                    angles = []
                    angles.append(getAngle(pts[edge[0]], pts[third_id1], pts[edge[1]]))
                    angles.append(getAngle(pts[third_id1], pts[edge[1]], pts[third_id2]))
                    angles.append(getAngle(pts[edge[1]], pts[third_id2], pts[edge[0]]))
                    angles.append(getAngle(pts[third_id2], pts[edge[0]], pts[third_id1]))

                    angle_diff = 0
                    for angle in angles:
                        angle_diff += abs(angle - 3.14159/2.0) / (3.14159/2)

                    # check if the connecting edge is longest edge of both triangles
                    if len_diff + angle_diff <= threshold:
                        # if yes, create quadrilateral
                        quads.append([edge[0], third_id1, edge[1], third_id2])
                        triangle_used[tringl1] = True
                        triangle_used[tringl2] = True


        matchLongestEdge(True)
        matchLongestEdge(False)
        createNiceQuads(True)
        createNiceQuads(False)

        self.display_triangles(pts, triangle_used, c.triangles)
        self.display_quads(pts, quads)

if __name__ == '__main__':
    e = Pattern()
    e.affect()

# vim: expandtab shiftwidth=4 tabstop=8 softtabstop=4 fileencoding=utf-8 textwidth=99
