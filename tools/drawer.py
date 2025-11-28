#!/usr/bin/env python3
"""Generate Gridfinity baseplates to fill a drawer with optimal printer bed usage."""

import argparse
import logging
import math
from pathlib import Path
from typing import Optional

import cadquery as cq

from gridfinity import baseplate
from gridfinity.config import GridfinityConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Printer bed size in mm (can be adjusted for your printer)
PRINTER_BED_WIDTH = 256.0  # mm
PRINTER_BED_DEPTH = 256.0  # mm

# Output directory
OUTPUT_DIR = Path("outputs/drawer")


def calculate_baseplates(
    drawer_width: float,
    drawer_depth: float,
    config: Optional[GridfinityConfig] = None,
) -> dict:
    """Calculate the optimal baseplate layout for a drawer.

    Uses a hybrid algorithm that:
    1. Tries to fit whole drawer in one plate if possible
    2. Splits along one dimension if possible
    3. Falls back to optimized 2D grid with minimal pieces

    Args:
        drawer_width: Width of drawer in mm
        drawer_depth: Depth of drawer in mm
        config: GridfinityConfig instance (uses default if None)

    Returns:
        Dictionary containing:
            - baseplates: List of (x_units, y_units) tuples for each baseplate
            - gaps: Dictionary with 'x' and 'y' gap dimensions
            - drawer_units: Dictionary with 'x' and 'y' unit counts
    """
    cfg = config or GridfinityConfig()

    # Calculate how many gridfinity units fit in each dimension
    units_x = int(drawer_width // cfg.unit_size)
    units_y = int(drawer_depth // cfg.unit_size)

    logger.info(f"Drawer: {drawer_width}mm x {drawer_depth}mm")
    logger.info(f"Total units that fit: {units_x} x {units_y}")

    # Calculate remaining gaps
    gap_x = drawer_width - (units_x * cfg.unit_size)
    gap_y = drawer_depth - (units_y * cfg.unit_size)

    logger.info(f"Remaining gaps: {gap_x:.2f}mm x {gap_y:.2f}mm")

    # Calculate how many units fit on the printer bed
    max_units_x = int(PRINTER_BED_WIDTH // cfg.unit_size)
    max_units_y = int(PRINTER_BED_DEPTH // cfg.unit_size)

    logger.info(
        f"Max units per print: {max_units_x} x {max_units_y} "
        f"(bed: {PRINTER_BED_WIDTH}mm x {PRINTER_BED_DEPTH}mm)"
    )

    # Generate optimal baseplate layout
    baseplates = _optimize_baseplate_layout(units_x, units_y, max_units_x, max_units_y, cfg)

    logger.info(f"Generated {len(baseplates)} baseplates:")
    for i, (x, y) in enumerate(baseplates, 1):
        logger.info(
            f"  Baseplate {i}: {x} x {y} units ({x * cfg.unit_size}mm x {y * cfg.unit_size}mm)"
        )

    return {
        "baseplates": baseplates,
        "gaps": {"x": gap_x, "y": gap_y},
        "drawer_units": {"x": units_x, "y": units_y},
    }


def _optimize_baseplate_layout(
    units_x: int,
    units_y: int,
    max_units_x: int,
    max_units_y: int,
    config: GridfinityConfig,
) -> list[tuple[int, int]]:
    """Optimize baseplate layout to minimize piece count and maximize size.

    Strategy:
    1. If whole drawer fits on bed → single plate
    2. If one dimension fits → split along other dimension only
    3. Otherwise → use optimized 2D grid approach

    Args:
        units_x: Total units in X dimension
        units_y: Total units in Y dimension
        max_units_x: Max units that fit on bed in X
        max_units_y: Max units that fit on bed in Y
        config: GridfinityConfig instance

    Returns:
        List of (x_units, y_units) tuples for each baseplate
    """
    baseplates = []

    # Strategy 1: Single plate if drawer fits on bed
    if units_x <= max_units_x and units_y <= max_units_y:
        logger.info("Optimization: Drawer fits on single baseplate")
        return [(units_x, units_y)]

    # Strategy 2: Split along X dimension only (Y fits)
    if units_y <= max_units_y:
        logger.info("Optimization: Splitting along X dimension only")
        remaining_x = units_x
        while remaining_x > 0:
            plate_x = min(remaining_x, max_units_x)
            baseplates.append((plate_x, units_y))
            remaining_x -= plate_x
        return baseplates

    # Strategy 3: Split along Y dimension only (X fits)
    if units_x <= max_units_x:
        logger.info("Optimization: Splitting along Y dimension only")
        remaining_y = units_y
        while remaining_y > 0:
            plate_y = min(remaining_y, max_units_y)
            baseplates.append((units_x, plate_y))
            remaining_y -= plate_y
        return baseplates

    # Strategy 4: Both dimensions need splitting - use optimized grid
    logger.info("Optimization: Using 2D grid layout with minimal pieces")

    # Calculate optimal split: prefer fewer, larger plates
    # Try to create plates as close to square as possible for stability

    # Determine how many plates we need in each dimension
    num_plates_x = math.ceil(units_x / max_units_x)
    num_plates_y = math.ceil(units_y / max_units_y)

    # Calculate base size and remainder for each dimension
    base_size_x = units_x // num_plates_x
    remainder_x = units_x % num_plates_x

    base_size_y = units_y // num_plates_y
    remainder_y = units_y % num_plates_y

    # Generate plates row by row, distributing remainders evenly
    for row in range(num_plates_y):
        # Calculate Y size for this row (distribute remainder in first rows)
        y_size = base_size_y + (1 if row < remainder_y else 0)

        for col in range(num_plates_x):
            # Calculate X size for this column (distribute remainder in first columns)
            x_size = base_size_x + (1 if col < remainder_x else 0)
            baseplates.append((x_size, y_size))

    return baseplates


def generate_spacer(
    width: float,
    depth: float,
    thickness: float = 5.0,
) -> cq.Workplane:
    """Generate a simple spacer piece to fill gaps.

    Args:
        width: Width of spacer in mm
        depth: Depth of spacer in mm
        thickness: Thickness of spacer in mm

    Returns:
        CadQuery Workplane containing the spacer geometry
    """
    logger.info(f"Creating spacer: {width:.1f}mm x {depth:.1f}mm x {thickness}mm")
    spacer = cq.Workplane("XY").box(width, depth, thickness)
    # Add small fillet to edges for easier printing
    spacer = spacer.edges("|Z").fillet(1.0)
    return spacer


def calculate_spacer_dimensions(
    gap: float,
    length: float,
    max_length: float = 150.0,
    max_aspect_ratio: float = 5.0,
) -> list[tuple[float, float]]:
    """Calculate optimal spacer dimensions with reasonable aspect ratios.

    Splits long spacers into multiple pieces to avoid awkward dimensions.

    Args:
        gap: The gap width (smaller dimension) in mm
        length: The full length to fill in mm
        max_length: Maximum length for a single spacer piece (default: 150mm)
        max_aspect_ratio: Maximum aspect ratio length:gap (default: 5:1)

    Returns:
        List of (width, depth) tuples for each spacer piece
    """
    spacers = []

    # Calculate how many pieces we need based on constraints
    # Constraint 1: Max length
    num_pieces_length = math.ceil(length / max_length)

    # Constraint 2: Max aspect ratio
    max_length_by_ratio = gap * max_aspect_ratio
    num_pieces_ratio = math.ceil(length / max_length_by_ratio)

    # Use the more restrictive constraint
    num_pieces = max(num_pieces_length, num_pieces_ratio)

    if num_pieces == 1:
        # Single spacer is fine
        spacers.append((gap, length))
    else:
        # Split into multiple pieces
        base_length = length / num_pieces

        for i in range(num_pieces):
            spacers.append((gap, base_length))

        logger.info(
            f"  Split {length:.1f}mm length into {num_pieces} pieces "
            f"of {base_length:.1f}mm each (aspect ratio: {base_length/gap:.1f}:1)"
        )

    return spacers


def generate_drawer_files(
    drawer_width: float,
    drawer_depth: float,
    thickness: float = 5.0,
    output_dir: Path = OUTPUT_DIR,
) -> None:
    """Generate all baseplates and spacers needed for a drawer.

    Args:
        drawer_width: Width of drawer in mm
        drawer_depth: Depth of drawer in mm
        thickness: Thickness of baseplates/spacers in mm
        output_dir: Directory to save STL files
    """
    # Create a subfolder named after the drawer dimensions
    drawer_folder = output_dir / f"drawer_{int(drawer_width)}_{int(drawer_depth)}"
    drawer_folder.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 60)
    logger.info("DRAWER BASEPLATE GENERATOR")
    logger.info("=" * 60)

    # Calculate layout
    layout = calculate_baseplates(drawer_width, drawer_depth)

    # Generate baseplate STL files
    logger.info("\nGenerating baseplate files...")
    for i, (x_units, y_units) in enumerate(layout["baseplates"], 1):
        logger.info(f"Generating baseplate {i}/{len(layout['baseplates'])}...")
        plate = baseplate(x_units, y_units, thickness)
        output_file = drawer_folder / f"baseplate_{i}_{x_units}x{y_units}.stl"
        cq.exporters.export(plate, str(output_file))
        logger.info(f"  Saved: {output_file}")

    # Generate spacer files if needed
    gaps = layout["gaps"]
    units = layout["drawer_units"]
    cfg = GridfinityConfig()

    spacers_generated = []

    logger.info("\nGenerating spacer files...")

    # X-direction spacers (gap in X, running along Y/depth of drawer)
    if gaps["x"] > 0.5:  # Only create if gap is significant
        logger.info(f"X-direction gap: {gaps['x']:.1f}mm")
        spacer_dims = calculate_spacer_dimensions(
            gaps["x"],
            units["y"] * cfg.unit_size
        )

        for i, (width, depth) in enumerate(spacer_dims, 1):
            spacer = generate_spacer(width, depth, thickness)
            output_file = drawer_folder / f"spacer_x_{i}_{width:.1f}x{depth:.1f}mm.stl"
            cq.exporters.export(spacer, str(output_file))
            spacers_generated.append(output_file)
            logger.info(f"  Saved: {output_file}")

    # Y-direction spacers (gap in Y, running along X/width of drawer)
    if gaps["y"] > 0.5:  # Only create if gap is significant
        logger.info(f"Y-direction gap: {gaps['y']:.1f}mm")
        spacer_dims = calculate_spacer_dimensions(
            gaps["y"],
            drawer_width
        )

        for i, (width, depth) in enumerate(spacer_dims, 1):
            # Note: width and depth are swapped here because we're orienting along X
            spacer = generate_spacer(depth, width, thickness)
            output_file = drawer_folder / f"spacer_y_{i}_{depth:.1f}x{width:.1f}mm.stl"
            cq.exporters.export(spacer, str(output_file))
            spacers_generated.append(output_file)
            logger.info(f"  Saved: {output_file}")

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("GENERATION COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Baseplates generated: {len(layout['baseplates'])}")
    logger.info(f"Spacers generated: {len(spacers_generated)}")
    logger.info(f"Output directory: {drawer_folder}")


def main():
    """Command-line interface for drawer baseplate generator."""
    parser = argparse.ArgumentParser(
        description="Generate Gridfinity baseplates to fill a drawer"
    )
    parser.add_argument(
        "width",
        type=float,
        help="Drawer width in mm",
    )
    parser.add_argument(
        "depth",
        type=float,
        help="Drawer depth in mm",
    )
    parser.add_argument(
        "--thickness",
        type=float,
        default=5.0,
        help="Baseplate thickness in mm (default: 5.0)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_DIR,
        help=f"Output directory (default: {OUTPUT_DIR})",
    )
    parser.add_argument(
        "--bed-width",
        type=float,
        default=PRINTER_BED_WIDTH,
        help=f"Printer bed width in mm (default: {PRINTER_BED_WIDTH})",
    )
    parser.add_argument(
        "--bed-depth",
        type=float,
        default=PRINTER_BED_DEPTH,
        help=f"Printer bed depth in mm (default: {PRINTER_BED_DEPTH})",
    )

    args = parser.parse_args()

    # Update global bed size if provided
    global PRINTER_BED_WIDTH, PRINTER_BED_DEPTH
    PRINTER_BED_WIDTH = args.bed_width
    PRINTER_BED_DEPTH = args.bed_depth

    generate_drawer_files(args.width, args.depth, args.thickness, args.output)


if __name__ == "__main__":
    main()
