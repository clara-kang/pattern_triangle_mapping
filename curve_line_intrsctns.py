import numpy as np

sample_per_len = 10

def bezier_length(ctrl_pts):
    # estimate length
    hull_len = 0

    for i in range (0, 3):
        hull_len += np.linalg.norm(ctrl_pts[i+1]-ctrl_pts[0])

    sample_pts = hull_len * sample_per_len

    start = ctrl_pts[0]
    curve_len = 0
    for i in range(0, int(sample_pts)):
        t = i/sample_pts
        end = (1-t)**3 * ctrl_pts[0] + 3*(1-t)**2*t * ctrl_pts[1] + 3 * t**2 * (1-t) * ctrl_pts[2] + t**3 * ctrl_pts[3]
        curve_len += np.linalg.norm(end - start)
        start = end
    return curve_len

def bezier_normal(ctrl_pts, cw, t):
    def rotate90cw(vec):
        return np.array(vec[1], -vec[0])
    def rotate90ccw(vec):
        return np.array(-vec[1], vec[0])
    tangent = 3 * (1-t)**2 * (ctrl_pts[1] - ctrl_pts[0]) + 6 * (1-t) * t * (ctrl_pts[2] - ctrl_pts[1]) + 3 * t**2 * (ctrl_pts[3] - ctrl_pts[2])
    tangent = tangent / np.linalg.norm(tangent)
    if cw:
        return rotate90ccw(tangent)
    else:
        return rotate90cw(tangent)

def intersect_bezier_line(px, py, lx, ly):

    A=ly[1]-ly[0]	    # A=y2-y1
    B=lx[0]-lx[1]	    # B=x1-x2
    C=lx[0]*(ly[0]-ly[1]) +  ly[0]*(lx[1]-lx[0])	# C=x1*(y1-y2)+y1*(x2-x1)

    P[0] = A*bx[0]+B*by[0]		# t^3
    P[1] = A*bx[1]+B*by[1]		# t^2
    P[2] = A*bx[2]+B*by[2]		# t
    P[3] = A*bx[3]+B*by[3] + C	 # 1

    r = np.roots(P)

    intrsctn_x = []
    intrsctn_y = []

    for i in range (0, 3):
        t = r[i]

        X[0]=bx[0]*t*t*t+bx[1]*t*t+bx[2]*t+bx[3]
        X[1]=by[0]*t*t*t+by[1]*t*t+by[2]*t+by[3]

        if ((lx[1]-lx[0])!=0):           # if not vertical line
            s=(X[0]-lx[0])/(lx[1]-lx[0])
        else:
            s=(X[1]-ly[0])/(ly[1]-ly[0])

        # in bounds?
        if t >= 0 and t <= 1.0 and s >= 0 and s <= 1.0:
            intrsctn_x.append(X[0], X[1])

    return intrsctn_x, intrsctn_y
