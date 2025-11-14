"""Utility functions for processing instrument footprints."""

import math
import re
from typing import List, Tuple, Dict, Any
from geoalchemy2.functions import ST_GeogFromText


def get_scale_factor(unit: str) -> float:
    """Get scaling factor for different units."""
    scale_factors = {
        "deg": 1.0,
        "arcmin": 1.0 / 60.0,
        "arcsec": 1.0 / (60.0 * 60.0)
    }
    return scale_factors.get(unit, 1.0)


def create_rectangular_footprint(height: float, width: float, scale: float) -> List[Tuple[float, float]]:
    """Create vertices for rectangular footprint."""
    half_h = round(0.5 * float(height) * scale, 4)
    half_w = round(0.5 * float(width) * scale, 4)
    
    vertices = [
        [-half_w, half_h],    # top left
        [half_w, half_h],     # top right  
        [half_w, -half_h],    # bottom right
        [-half_w, -half_h],   # bottom left
        [-half_w, half_h]     # close polygon
    ]
    return vertices


def create_circular_footprint(radius: float, scale: float, steps: int = 20) -> List[Tuple[float, float]]:
    """Create vertices for circular footprint."""
    r = float(radius) * float(scale)
    vertices = []
    
    steps = len(range(0, 360, int(360 / steps)))
    ang = float(360 / steps)
    
    for a in range(0, steps):
        a = float(a)
        x = r * math.cos(math.radians(90 - a * ang))
        y = r * math.sin(math.radians(90 - a * ang))
        
        # Clean up very small values
        if abs(x) < 1e-10:
            x = 0.0
        if abs(y) < 1e-10:
            y = 0.0
            
        x = round(x, 4)
        y = round(y, 4)
        vertices.append([x, y])
    
    # Close the polygon
    vertices.append(vertices[0])
    return vertices


def extract_polygon_coordinates(polygon_text: str, scale: float) -> Tuple[List[Tuple[float, float]], List[str]]:
    """Extract polygon coordinates from text format."""
    errors = []
    vertices = []
    
    try:
        # Remove extra whitespace and normalize
        polygon_text = polygon_text.strip()
        
        # Split lines and process each coordinate pair
        lines = [line.strip() for line in polygon_text.split('\n') if line.strip()]
        
        for line in lines:
            # Match coordinate patterns: (x, y) or x, y or x y
            coord_match = re.match(r'^\s*\(?\s*([+-]?\d*\.?\d+)\s*[,\s]\s*([+-]?\d*\.?\d+)\s*\)?\s*$', line)
            if coord_match:
                x = float(coord_match.group(1)) * scale
                y = float(coord_match.group(2)) * scale
                vertices.append([round(x, 4), round(y, 4)])
            else:
                errors.append(f"Invalid coordinate format: {line}")
        
        if len(vertices) < 3:
            errors.append("Polygon must have at least 3 vertices")
        
        # Ensure polygon is closed
        if vertices and vertices[0] != vertices[-1]:
            vertices.append(vertices[0])
            
    except Exception as e:
        errors.append(f"Error parsing polygon: {str(e)}")
    
    return vertices, errors


def parse_multi_polygon(polygon_text: str, scale: float) -> Tuple[List[List[Tuple[float, float]]], List[str]]:
    """Parse multi-polygon format with # delimiters and [] brackets."""
    errors = []
    all_polygons = []
    
    try:
        if "[" in polygon_text and "]" in polygon_text:
            # Multi-polygon format
            polygons = polygon_text.split("#")
            for poly_text in polygons:
                poly_text = poly_text.strip()
                if not poly_text:
                    continue
                
                try:
                    # Extract content between brackets
                    bracket_match = re.search(r'\[(.*?)\]', poly_text, re.DOTALL)
                    if bracket_match:
                        coord_text = bracket_match.group(1)
                        vertices, poly_errors = extract_polygon_coordinates(coord_text, scale)
                        if poly_errors:
                            errors.extend(poly_errors)
                        else:
                            all_polygons.append(vertices)
                    else:
                        errors.append(f"Invalid polygon bracket format: {poly_text}")
                        
                except Exception as e:
                    errors.append(f"Error parsing polygon section: {str(e)}")
        else:
            # Single polygon format
            vertices, poly_errors = extract_polygon_coordinates(polygon_text, scale)
            if poly_errors:
                errors.extend(poly_errors)
            else:
                all_polygons.append(vertices)
                
    except Exception as e:
        errors.append(f"Error parsing multi-polygon: {str(e)}")
    
    return all_polygons, errors


def create_geography_from_vertices(vertices: List[Tuple[float, float]]) -> Any:
    """Create PostGIS geography object from vertices."""
    if len(vertices) < 4:  # Need at least 3 vertices + closing vertex
        raise ValueError("Not enough vertices for polygon")
    
    # Format vertices as WKT POLYGON
    coord_pairs = [f"{v[0]} {v[1]}" for v in vertices]
    wkt = f"POLYGON(({', '.join(coord_pairs)}))"
    
    return ST_GeogFromText(wkt)


def validate_footprint_data(footprint_type: str, **kwargs) -> Tuple[bool, List[str]]:
    """Validate footprint data based on type."""
    errors = []
    
    if footprint_type == "Rectangular":
        height = kwargs.get('height')
        width = kwargs.get('width')
        if height is None or width is None:
            errors.append("Height and Width are required for Rectangular shape")
        elif height <= 0 or width <= 0:
            errors.append("Height and Width must be positive numbers")
            
    elif footprint_type == "Circular":
        radius = kwargs.get('radius')
        if radius is None:
            errors.append("Radius is required for Circular shape")
        elif radius <= 0:
            errors.append("Radius must be a positive number")
            
    elif footprint_type == "Polygon":
        polygon = kwargs.get('polygon')
        if not polygon:
            errors.append("Polygon coordinates are required for Polygon shape")
    
    return len(errors) == 0, errors