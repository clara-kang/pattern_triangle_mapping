import numpy as np
import inkex

sample_per_len = 10

def bezier_eval(ctrl_pts, t):
    return (1-t)**3 * ctrl_pts[0] + 3*(1-t)**2*t * ctrl_pts[1] + 3 * t**2 * (1-t) * ctrl_pts[2] + t**3 * ctrl_pts[3]

def get_hull_len(ctrl_pts):
    hull_len = 0
    for i in range (0, 3):
        hull_len += np.linalg.norm(ctrl_pts[i+1]-ctrl_pts[0])
    return hull_len

def bezier_length(ctrl_pts):
    # estimate length
    hull_len = get_hull_len(ctrl_pts)
    sample_pts = hull_len * sample_per_len

    start = ctrl_pts[0]
    curve_len = 0
    for i in range(0, int(sample_pts)):
        t = i/sample_pts
        end = bezier_eval(ctrl_pts, t)
        curve_len += np.linalg.norm(end - start)
        start = end
    return curve_len

def get_t_at_length(ctrl_pts, st, length):
    hull_len = get_hull_len(ctrl_pts)
    sample_pts = hull_len * sample_per_len

    acc_len = 0
    start = bezier_eval(ctrl_pts, st)
    for i in range(1, int(sample_pts)):
        t = st + i/sample_pts
        end = bezier_eval(ctrl_pts, t)
        acc_len += np.linalg.norm(end - start)
        start = end
        if acc_len >= length:
            return t
    return -1

def rotate90cw(vec):
    return np.array([vec[1], -vec[0]])
def rotate90ccw(vec):
    return np.array([-vec[1], vec[0]])

def bezier_normal(ctrl_pts, t, ccw):
    tangent = 3.0 * (1.0-t)**2 * (ctrl_pts[1] - ctrl_pts[0]) + 6.0 * (1-t) * t * (ctrl_pts[2] - ctrl_pts[1]) + 3.0 * t**2 * (ctrl_pts[3] - ctrl_pts[2])
    tangent = tangent / np.linalg.norm(tangent)
    if ccw:
        return rotate90ccw(tangent)
    else:
        return rotate90cw(tangent)

def line_normal(pts, ccw):
    tangent = pts[1] - pts[0]
    tangent = tangent / np.linalg.norm(tangent)
    if ccw:
        return rotate90ccw(tangent)
    else:
        return rotate90cw(tangent)

def intersect_line_ray(pts1, pts2): # line 2 is ray
    line_dir = pts1[1] - pts1[0]
    ray_dir =  pts2[1] - pts2[0]
    A = np.array([ray_dir, -line_dir]).T
    B = pts1[0] - pts2[0]
    X = np.linalg.solve(A, B)
    dist, t = X[0], X[1]

    if t >= 0 and t <= 1 and dist >= 0:
        return [pts2[0]+dist*ray_dir]
    return []

def intersect_bezier_line(ctrl_pts, pts, isRay=False):

    A = pts[1][1] - pts[0][1]
    B = pts[0][0] - pts[1][0]
    C = pts[0][0] * (pts[0][1] - pts[1][1]) + pts[0][1] * (pts[1][0] - pts[0][0])

    P = np.zeros(4)
    coeffs = np.zeros([4, 2])

    coeffs[0] = -ctrl_pts[0] + 3*ctrl_pts[1] - 3*ctrl_pts[2] + ctrl_pts[3]
    coeffs[1] = 3 * ctrl_pts[0] - 6*ctrl_pts[1] + 3*ctrl_pts[2]
    coeffs[2] = -3 * ctrl_pts[0] + 3 * ctrl_pts[1]
    coeffs[3] = ctrl_pts[0]
    P = A * coeffs[:,0] + B * coeffs[:,1]
    P[3] += C

    r = np.roots(P)

    intrsctns = []

    for i in range (0, 3):
        t = r[i]
        if np.iscomplex(t) or t < 0 or t > 1:
            continue

        t = t.real
        X = bezier_eval(ctrl_pts, t)

        if ((pts[1][0]-pts[0][0])!=0):           # if not vertical line
            s=(X[0]-pts[0][0])/(pts[1][0]-pts[0][0])
        else:
            s=(X[1]-pts[0][1])/(pts[1][1]-pts[0][1])

        # in bounds?
        if ( s >= 0 and (( not isRay and s <= 1.0 ) or isRay) ):
            intrsctns.append(X)

    return intrsctns
