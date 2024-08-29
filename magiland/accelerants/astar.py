import ctypes
from .load import load_lib
from numpy.ctypeslib import ndpointer
import os

LIB = load_lib(os.path.join(os.path.dirname(__file__), "astar"))

if LIB != None:
    aStarSearch = LIB.aStarSearch
    aStarSearch.restype = None
    aStarSearch.argtypes = [ndpointer(ctypes.c_int, flags="C_CONTIGUOUS"),
                            ctypes.c_int,
                            ctypes.c_int,
                            ctypes.c_int,
                            ctypes.c_int,
                            ctypes.c_int,
                            ctypes.c_int]

else:
    aStarSearch = None
