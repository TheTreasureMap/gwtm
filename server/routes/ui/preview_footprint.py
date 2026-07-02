"""Preview footprint endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from server.db.database import get_db

router = APIRouter(tags=["UI"])


@router.get("/ajax_preview_footprint")
async def preview_footprint(
    ra: float,
    dec: float,
    radius: float = None,
    height: float = None,
    width: float = None,
    shape: str = "Circular",
    polygon: str = None,
    db: Session = Depends(get_db),
):
    """Generate a preview of an instrument footprint."""
    import math
    import plotly
    import plotly.graph_objects as go

    from server.utils.footprint_processing import parse_multi_polygon

    # This is a UI helper endpoint to visualize a footprint before saving
    # It generates the appropriate visualization for the given parameters
    vertices = []

    if shape == "Circular" and radius:
        # For circle, generate points around the circumference
        circle_points = []
        for i in range(36):  # 36 points for a smooth circle
            # Proper spherical coordinate calculation for circles
            # Convert angle to offset in RA/Dec using spherical trigonometry
            x = radius * math.cos(math.radians(90 - i * 10))
            y = radius * math.sin(math.radians(90 - i * 10))
            # Adjust for spherical coordinates
            if abs(x) < 1e-10:
                x = 0.0
            if abs(y) < 1e-10:
                y = 0.0
            point_ra = ra + x
            point_dec = dec + y
            circle_points.append([point_ra, point_dec])

        # Close the polygon
        circle_points.append(circle_points[0])
        vertices.append(circle_points)

    elif shape == "Rectangular" and height and width:
        # For rectangle, generate corners
        # Convert height/width in degrees to ra/dec coordinates
        # Proper calculation accounting for coordinate system
        half_width = width / 2
        half_height = height / 2

        # No cos(dec) correction needed for simple rectangular footprints
        ra_offset = half_width

        rect_points = [
            [ra - ra_offset, dec - half_height],  # bottom left
            [ra - ra_offset, dec + half_height],  # top left
            [ra + ra_offset, dec + half_height],  # top right
            [ra + ra_offset, dec - half_height],  # bottom right
            [ra - ra_offset, dec - half_height],  # close the polygon
        ]
        vertices.append(rect_points)

    elif shape == "Polygon" and polygon:
        # For custom polygon, parse the UI text format:
        #   [(x, y) ... ] # [(x, y) ... ]   (multi-polygon, "#"-delimited)
        # or a single newline-separated list of "(x, y)" coordinate pairs.
        # This is the same parser used by the instrument-submit path, so the
        # preview matches what will actually be stored.
        polygons, errors = parse_multi_polygon(polygon, scale=1.0)
        if errors:
            return {"error": "; ".join(errors)}
        if not polygons:
            return {"error": "Invalid polygon format"}

        for poly_points in polygons:
            # parse_multi_polygon already closes each ring; offset to ra/dec.
            vertices.append([[ra + v[0], dec + v[1]] for v in poly_points])
    else:
        return {"error": "Invalid shape type or missing required parameters"}

    # Create a plotly figure
    traces = []
    for vert in vertices:
        xs = [v[0] for v in vert]
        ys = [v[1] for v in vert]
        trace = go.Scatter(
            x=xs, y=ys, mode="lines", line_color="blue", fill="toself", fillcolor="violet"
        )
        traces.append(trace)

    fig = go.Figure(data=traces)
    fig.update_layout(
        showlegend=False,
        xaxis_title="degrees",
        yaxis_title="degrees",
        yaxis=dict(
            matches="x",
            scaleanchor="x",
            scaleratio=1,
            constrain="domain",
        ),
    )

    # Return the figure object directly - FastAPI will serialize it properly
    return fig.to_dict()
