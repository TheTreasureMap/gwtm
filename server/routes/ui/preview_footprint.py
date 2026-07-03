"""Preview footprint endpoint."""

from fastapi import APIRouter
from pydantic import BaseModel

from server.utils.footprint_processing import (
    get_scale_factor,
    create_circular_footprint,
    create_rectangular_footprint,
    parse_multi_polygon,
)

router = APIRouter(tags=["UI"])


class FootprintPreviewRequest(BaseModel):
    """Parameters for a footprint preview.

    Sent as a POST body rather than a query string: multi-polygon footprints
    (e.g. the ~170-CCD LSST camera) can produce very large payloads that would
    exceed URL/request-line length limits and fail with a 414.
    """

    shape: str = "Circular"
    unit: str = "deg"
    ra: float = 0.0
    dec: float = 0.0
    radius: float | None = None
    height: float | None = None
    width: float | None = None
    polygon: str | None = None


@router.post("/ajax_preview_footprint")
async def preview_footprint(request: FootprintPreviewRequest):
    """Generate a preview of an instrument footprint.

    Uses the same footprint parsing/scaling helpers as instrument creation, so
    the preview is faithful to what will be stored — including unit scaling.
    This lets a user spot a mistake (wrong unit or dimensions) before
    submitting, since the axes are in real degrees.
    """
    import plotly.graph_objects as go

    # Scale raw inputs to degrees using the selected unit, matching the
    # conversion applied on instrument creation (get_scale_factor).
    scale = get_scale_factor(request.unit)
    vertices = []

    if request.shape == "Circular" and request.radius:
        vertices.append(create_circular_footprint(request.radius, scale))

    elif request.shape == "Rectangular" and request.height and request.width:
        vertices.append(
            create_rectangular_footprint(request.height, request.width, scale)
        )

    elif request.shape == "Polygon" and request.polygon:
        # Parse the UI text format:
        #   [(x, y) ... ] # [(x, y) ... ]   (multi-polygon, "#"-delimited)
        # or a single newline-separated list of "(x, y)" coordinate pairs.
        polygons, errors = parse_multi_polygon(request.polygon, scale)
        if errors:
            return {"error": "; ".join(errors)}
        if not polygons:
            return {"error": "Invalid polygon format"}
        vertices.extend(polygons)

    else:
        return {"error": "Invalid shape type or missing required parameters"}

    # The helpers produce origin-centered rings; offset them to the preview
    # ra/dec so the axes read as sky coordinates.
    vertices = [
        [[request.ra + v[0], request.dec + v[1]] for v in ring] for ring in vertices
    ]

    # Create a plotly figure
    traces = []
    for vert in vertices:
        xs = [v[0] for v in vert]
        ys = [v[1] for v in vert]
        trace = go.Scatter(
            x=xs,
            y=ys,
            mode="lines",
            line_color="blue",
            fill="toself",
            fillcolor="violet",
        )
        traces.append(trace)

    fig = go.Figure(data=traces)
    # Lock a 1:1 data aspect ratio so footprints render true to shape.
    # constrain="domain" must sit on the axis with excess space; the preview
    # container is wider than tall, so it belongs on x. Setting it on both is
    # robust to either orientation.
    fig.update_layout(
        showlegend=False,
        xaxis_title="degrees",
        yaxis_title="degrees",
        xaxis=dict(constrain="domain"),
        yaxis=dict(
            scaleanchor="x",
            scaleratio=1,
            constrain="domain",
        ),
    )

    # Return the figure object directly - FastAPI will serialize it properly
    return fig.to_dict()
