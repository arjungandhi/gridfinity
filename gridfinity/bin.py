import cadquery as cq
from cadquery.vis import show
import math


def gridfinity_bin(x=2, y=2, z=5, lip=True):
    """Creates a Gridfinity-compatible storage bin."""
    # base dimensions and parameters
    tolerance = 0.25
    gridfinity_unit = 42
    height_unit = 7
    base_height = 4.75
    outer_fillet = 7.5
    # lip steps
    lip_steps = [(-0.7 - 1.9, 0), (0.7, 0.7), (0, 1.8), (1.9, 1.9)]

    # create the main bin body
    bin = cq.Workplane("XY").box(
        x * gridfinity_unit - 2 * tolerance,
        y * gridfinity_unit - 2 * tolerance,
        z * height_unit - base_height,
    )
    bin = bin.edges("+Z").fillet(outer_fillet)

    # lip
    if lip:
        path = bin.faces(">Z").wires().vals()[0]

        show(path)

        # Create a profile on the YZ plane that we will sweep along the top edges
        lip_profile = cq.Workplane("YZ").moveTo(0, 0)
        pos = [0, 0]
        for step in lip_steps:
            y = step[0] + pos[0]
            z = step[1] + pos[1]
            pos = [y, z]
            lip_profile = lip_profile.lineTo(pos[0], pos[1])

        lip_profile = lip_profile.close()
        show(lip_profile)
        # Sweep the profile along the path to create the lip
        lip = lip_profile.sweep(path, isFrenet=True)
        show(lip)

        # Union the lip with the bin
        bin = bin.union(lip)

    return bin
