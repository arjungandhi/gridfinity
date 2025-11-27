import cadquery as cq

from gridfinity import baseplate, bin

output = bin(1, 1, 1)
# Export to STL file (for 3D printing)
cq.exporters.export(output, "outputs/output.stl")
