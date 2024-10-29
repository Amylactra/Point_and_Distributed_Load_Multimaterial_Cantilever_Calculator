Solver for cantilever beam made of multiple materials with either point or distributed loads. Outputs figures of deflection in degrees for any arbitrary beam type, as well as a csv file for deflection along the length.
Requires Numpy and Matplotlib, I ran it in PyCharm but you could probably run it in Visual Studios or maybe in default Python IDLE. 
NOTE: The solver assumes that your transition point in material will be after your point load in the point load solver. If you enter a point load after your transition point, the equations will not be valid.
