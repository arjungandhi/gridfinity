import cadquery as cq
from gridfinity.bin import gridfinity_bin
from cadquery.vis import show

# Create a 10mm x 10mm x 10mm cube
bin = gridfinity_bin()
show(bin)


# Export to STL file (for 3D printing)
cq.exporters.export(bin, "outputs/output.stl")
