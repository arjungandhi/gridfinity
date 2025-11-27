import cadquery as cq

from gridfinity import baseplate

output = baseplate(2, 3)

# Export to STL file (for 3D printing)
cq.exporters.export(output, "outputs/output.stl")
