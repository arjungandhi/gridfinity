import cadquery as cq
from cadquery.vis import show
import math

# base dimensions and parameters
tolerance = 0.25
gridfinity_unit = 42
height_unit = 7
base_height = 4.75
outer_fillet = 7.5
# lip steps defined as (x, z) offsets
lip_steps = [(-2.6, 0), (0.7, 0.7), (0, 1.8), (1.9, 1.9)]
base_steps = [(-2.95, 0), (0.8, 0.8), (0, 1.8), (2.15, 2.15)]


def gridfinity_box(x=2, y=2, z=5, lip=True):
    """Creates a Gridfinity-compatible storage box."""
    print("Creating Gridfinity box:")
    print(f"  - Dimensions: {x} x {y} x {z} units")
    # main box body
    box = cq.Workplane("XY").box(
        x * gridfinity_unit - 2 * tolerance,
        y * gridfinity_unit - 2 * tolerance,
        z * height_unit - base_height,
    )
    box = box.edges("+Z").fillet(outer_fillet)
    print(f"  - Created main box body.")

    # lip
    if lip:
        lip = gridfinity_box_lip(box)
        # Add the lip to the box (no boolean operation)
        box = box.add(lip)
        print(f"  - Added lip to main box body.")

    # create a base for a single unit that we will pattern out
    base = gridfinity_box_base()

    # Pattern the base units to match the box footprint
    # Create an array of base units by translating and combining
    # Start with None and add all bases with proper offsets
    base_pattern = None
    for i in range(x):
        for j in range(y):
            # Calculate offset from center for a centered grid
            x_offset = (i - (x - 1) / 2) * gridfinity_unit
            y_offset = (j - (y - 1) / 2) * gridfinity_unit

            if base_pattern is None:
                base_pattern = base.translate((x_offset, y_offset, 0))
            else:
                base_pattern = base_pattern.add(base.translate((x_offset, y_offset, 0)))
    print(f"  - Patterned {x * y} base units.")

    # Position the base pattern at the bottom of the box
    base_z_offset = -(z * height_unit - base_height) / 2 - base_height / 2
    base_pattern = base_pattern.translate((0, 0, base_z_offset))

    # Combine the base with the box
    box = box.add(base_pattern)

    return box


def gridfinity_box_lip(box):
    """Adds a lip to an existing Gridfinity-compatible storage box."""
    # Get the outer wire from the top face (longest wire)
    wire = box.faces(">Z").wires(cq.selectors.LengthNthSelector(-1))

    # Select a single starting vertex to position the profile
    vert = wire.vertices(">X").vertices(">Y")

    # Create a workplane at that vertex
    # Use XZ plane so the profile sweeps correctly around the perimeter
    lip_profile = cq.Workplane("XZ", origin=vert.val().toTuple())

    # Build the lip profile using the gridfinity lip steps
    lip_profile = lip_profile.moveTo(0, 0)
    pos = [0, 0]
    for step in lip_steps:
        x = step[0] + pos[0]
        z = step[1] + pos[1]
        pos = [x, z]
        lip_profile = lip_profile.lineTo(pos[0], pos[1])

    lip_profile = lip_profile.close()

    # Sweep the profile along the wire with
    lip = lip_profile.sweep(wire, isFrenet=True)

    return lip


def gridfinity_box_base():
    """Returns a single base unit for a Gridfinity-compatible storage box."""
    # create a base for a single unit
    base = cq.Workplane("XY").box(
        gridfinity_unit - 2 * tolerance,
        gridfinity_unit - 2 * tolerance,
        base_height,
    )
    base = base.edges("+Z").fillet(outer_fillet)

    # cut the base steps out of the base unit
    base_wire = base.faces("<Z").wires(cq.selectors.LengthNthSelector(-1))
    base_vert = base_wire.vertices(">X").vertices(">Y")
    base_profile = cq.Workplane("XZ", origin=base_vert.val().toTuple())
    base_profile = base_profile.moveTo(0, 0)
    pos = [0, 0]
    for step in base_steps:
        x = step[0] + pos[0]
        z = step[1] + pos[1]
        pos = [x, z]
        base_profile = base_profile.lineTo(pos[0], pos[1])
    base_profile = base_profile.close()
    base_cut = base_profile.sweep(base_wire, isFrenet=True)
    base = base.cut(base_cut)

    return base
