import numpy as np

intersect_bezier_line(px, py, lx, ly):

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

        if ((lx[1]-lx[0])!=0)           # if not vertical line
            s=(X[0]-lx[0])/(lx[1]-lx[0])
        else
            s=(X[1]-ly[0])/(ly[1]-ly[0])

        # in bounds?
        if t >= 0 and t <= 1.0 and s >= 0 and s <= 1.0
        {
            intrsctn_x.append(X[0], X[1])
        }

    return intrsctn_x, intrsctn_y
