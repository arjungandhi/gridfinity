import cadquery as cq
from gridfinity.box import gridfinity_box
from cadquery.vis import show

box = gridfinity_box()
show(box)


# Export to STL file (for 3D printing)
cq.exporters.export(box, "outputs/output.stl")
