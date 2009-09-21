"""
Implementation of the univariate matrix polynomial.
The algebraic class is

M[t]/<t^D>

where M is the ring of matrices and t in R.

"""

import numpy.linalg
import numpy
from numpy import shape, dot, zeros, ndim, asarray, sum, trace

def combine_blocks(in_X):
    """
    expects an array or list consisting of entries of type UTPM, e.g.
    in_X = [[UTPM1,UTPM2],[UTPM3,UTPM4]]
    and returns
    UTPM([[UTPM1.tc,UTPM2.tc],[UTPM3.tc,UTPM4.tc]])

    """

    in_X = numpy.array(in_X)
    Rb,Cb = numpy.shape(in_X)

    # find the degree D and number of directions P
    D = 0; 	P = 0;

    for r in range(Rb):
        for c in range(Cb):
            D = max(D, in_X[r,c].tc.shape[0])
            P = max(P, in_X[r,c].tc.shape[1])

    # find the sizes of the blocks
    rows = []
    cols = []
    for r in range(Rb):
        rows.append(in_X[r,0].shape[0])
    for c in range(Cb):
        cols.append(in_X[0,c].shape[1])
    rowsums = numpy.array([ numpy.sum(rows[:r]) for r in range(0,Rb+1)],dtype=int)
    colsums = numpy.array([ numpy.sum(cols[:c]) for c in range(0,Cb+1)],dtype=int)

    # create new matrix where the blocks will be copied into
    tc = zeros((D, P, rowsums[-1],colsums[-1]))
    for r in range(Rb):
        for c in range(Cb):
            tc[:,:,rowsums[r]:rowsums[r+1], colsums[c]:colsums[c+1]] = in_X[r,c].tc[:,:,:,:]

    return UTPM(tc)

class UTPM:
    """
    UTPM == Univariate Taylor Polynomial of Matrices
    This class implements univariate Taylor arithmetic on matrices, i.e.
    [A] = \sum_{d=0}^D A_d t^d
    A_d = \frac{d^d}{dt^d}|_{t=0} \sum_{c=0}^D A_c t^c

    in vector forward mode
    Input:
    in the most general form, the input is a 4-tensor.
    We use the notation:
    D: degree of the Taylor series
    P: number of directions
    N: number of rows of A_0
    M: number of cols of A_0

    shape([A]) = (D,P,N,M)
    The reason for this choice is that the (N,M) matrix is the elementary type, so that memory should be contiguous. Then, at each operation, the code performed to compute
    v_d has to be repeated for every direction.
    E.g. a multiplication
    [w] = [u]*[v] =
    [[u_11, ..., u_1Ndir],
    ...
    [u_D1, ..., u_DNdir]]  +
    [[v11, ..., v_1Ndir],
    ...
    [v_D1, ..., v_DNdir]] =
    [[ u_11 + v_11, ..., u_1Ndir + v_1Ndir],
    ...
    [[ u_D1 + v_D1, ..., u_DNdir + v_DNdir]]

    For ufuncs this arrangement is advantageous, because in this order, memory chunks of size Ndir are used and the operation on each element is the same. This is desireable to avoid cache misses.
    See for example __mul__: there, operations of self.tc[:d+1,:,:,:]* rhs.tc[d::-1,:,:,:] has to be performed. One can see, that contiguous memory blocks are used for such operations.

    A disadvantage of this arrangement is: it seems unnatural, it is easier to regard each direction separately.
    """
    def __init__(self, X, Xdot = None):
        """ INPUT:	shape([X]) = (D,P,N,M)"""
        Ndim = ndim(X)
        if Ndim == 4:
            self.tc = numpy.asarray(X)
        else:
            raise NotImplementedError

    def __add__(self,rhs):
        if numpy.isscalar(rhs):
            retval = UTPM(numpy.copy(self.tc))
            retval.tc[0,:,:,:] += rhs
            return retval
        else:
            return UTPM(self.tc + rhs.tc)

    def __sub__(self,rhs):
        if numpy.isscalar(rhs):
            retval = UTPM(numpy.copy(self.tc))
            retval.tc[0,:,:,:] -= rhs
            return retval
        else:
            return UTPM(self.tc - rhs.tc)

    def __mul__(self,rhs):
        if numpy.isscalar(rhs):
            retval = UTPM(numpy.copy(self.tc))
            retval.tc[:,:,:,:] *= rhs
            return retval
        else:
            retval = UTPM(zeros(shape(self.tc)))
            (D,P,N,M) = shape(retval.tc)
            for d in range(D):
                retval.tc[d,:,:,:] = sum( self.tc[:d+1,:,:,:] * rhs.tc[d::-1,:,:,:], axis=0)
            return retval

    def __div__(self,rhs):
        if numpy.isscalar(rhs):
            retval = UTPM(numpy.copy(self.tc))
            retval.tc[:,:,:,:] /= rhs
            return retval

        else:
            retval = UTPM(zeros(shape(self.tc)))
            (D,P,N,M) = shape(retval.tc)
            for d in range(D):
                retval.tc[d,:,:,:] = 1./ rhs.tc[0,:,:,:] * ( self.tc[d,:,:,:] - sum(retval.tc[:d,:,:,:] * rhs.tc[d:0:-1,:,:,:], axis=0))
            return retval


    def __radd__(self,rhs):
        return self + rhs

    def __rsub__(self, other):
        return -self + other

    def __rmul__(self,rhs):
        return self * rhs

    def __rdiv__(self, rhs):
        tmp = self.zeros_like()
        tmp.tc[0,:,:,:] = rhs
        return tmp/self

    def __neg__(self):
        return UTPM(-self.tc)
    

    def dot(self,rhs):
        shp = list(shape(self.tc))
        shp[3] = shape(rhs.tc)[3]
        retval = UTPM(zeros(shp))
        (D,P,N,M) = shape(retval.tc)
        for d in range(D):
            for p in range(P):
                for c in range(d+1):
                    retval.tc[d,p,:,:] += numpy.dot(self.tc[c,p,:,:], rhs.tc[d-c,p,:,:])
        return retval

    def inv(self):
        retval = UTPM(zeros(shape(self.tc)))
        (D,P,N,M) = shape(retval.tc)

        # tc[0] element
        for p in range(P):
            retval.tc[0,p,:,:] = numpy.linalg.inv(self.tc[0,p,:,:])

        # tc[d] elements
        for d in range(1,D):
            for p in range(P):
                for c in range(1,d+1):
                    retval.tc[d,p,:,:] += numpy.dot(self.tc[c,p,:,:], retval.tc[d-c,p,:,:],)
                retval.tc[d,p,:,:] =  numpy.dot(-retval.tc[0,p,:,:], retval.tc[d,p,:,:],)
        return retval

    def solve(self,A):
        """
        A y = x  <=> y = solve(A,x)
        is implemented here as y = x.solve(A)
        """
        retval = UTPM(zeros(shape(self.tc)))
        (D,P,N,M) = shape(retval.tc)
        assert M == 1
        tmp = numpy.zeros((N,M),dtype=float)
        for d in range(D):
            for p in range(P):
                tmp[:,:] = self.tc[d,p,:,:]
                for k in range(1,d+1):
                    tmp[:,:] -= numpy.dot(A.tc[k,p,:,:],retval.tc[d-k,p,:,:])
                retval.tc[d,p,:,:] = numpy.linalg.solve(A.tc[0,p,:,:],tmp)
        return retval


    def trace(self):
        """ returns a new UTPM in standard format, i.e. the matrices are 1x1 matrices"""
        (D,P,N,M) = shape(self.tc)
        if N!=M:
            raise TypeError(' N == M is required')

        retval = zeros((D,P,1,1))
        for d in range(D):
            for p in range(P):
                retval[d,p,0,0] = trace(self.tc[d,p,:,:])
        return UTPM(retval)

    def __getitem__(self, key):
        return UTPM(self.tc[:,:,key[0]:key[0]+1,key[1]:key[1]+1])

    def copy(self):
        return UTPM(self.tc.copy())

    def get_shape(self):
        return numpy.shape(self.tc[0,0,:,:])

    shape = property(get_shape)

    def get_transpose(self):
        return self.transpose()
    def set_transpose(self,x):
        raise NotImplementedError('???')
    T = property(get_transpose, set_transpose)

    def transpose(self):
        return UTPM( numpy.transpose(self.tc,axes=(0,1,3,2)))

    def set_zero(self):
        self.tc[:,:,:,:] = 0.
        return self


    def zeros_like(self):
        return UTPM(numpy.zeros_like(self.tc))


    def __str__(self):
        return str(self.tc)

    def __repr__(self):
        return self.__str__()
