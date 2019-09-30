def multiply(A, B):
    def getEntry(row, col):
        # nonlocal A, B
        res = 0
        for k in range(0, 3):
            res += A[row][k] * B[k][col]
        return res
    res = [[0,0,0],[0,0,0],[0,0,0]]
    for i in range(0, 3):
        for j in range(0, 3):
            res[i][j] = getEntry(i, j)
    return res

def getDeterminant3(matrx):
    if len(matrx) != 3 or len(matrx[0]) != 3:
        raise Exception("matrix not of size 3x3")
    return float(matrx[0][0] * getMinor(matrx, 0, 0) - matrx[0][1] * getMinor(matrx, 0, 1) + matrx[0][2] * getMinor(matrx, 0, 2))

def getMinor(matrx, i, j):
    def get2x2det(mat2):
        return mat2[0][0]*mat2[1][1] - mat2[0][1]*mat2[1][0]
    if len(matrx) != 3 or len(matrx[0]) != 3:
        raise Exception("matrix not of size 3x3")
    mat2 = []
    for row in range (0, 3):
        if row == i:
            continue
        nums_on_row = []
        for col in range (0, 3):
            if col == j:
                continue
            nums_on_row.append(matrx[row][col])
        mat2.append(nums_on_row)
    return get2x2det(mat2)

def transpose(matrx):
    if len(matrx) != 3 or len(matrx[0]) != 3:
        raise Exception("matrix not of size 3x3")
    for i in range (0,3):
        for j in range (i, 3):
            tmp = matrx[i][j]
            matrx[i][j] = matrx[j][i]
            matrx[j][i] = tmp
        

def getInverse(matrx):
    det = getDeterminant3(matrx)
    res = [[0,0,0],[0,0,0],[0,0,0]]
    for i in range(0, 3):
        for j in range(0, 3):
            cofactor = 1
            if (i+j)%2 != 0:
                cofactor = -1
            res[i][j] = cofactor * getMinor(matrx, i, j) / det
    transpose(res)
    return res
