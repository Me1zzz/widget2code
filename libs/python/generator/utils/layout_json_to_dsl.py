"""Convert layout analysis JSON into WidgetDSL JSON for html_compiler.

This module focuses on layout-related properties (flex direction, alignment,
spacing, bounds) and estimates font sizes from text bounds using device
metrics (physical vs. virtual pixels).
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from statistics import median
from typing import Any, Iterable, Optional


@dataclass(frozen=True)
class Rect:
    """Simple rectangle helper for bounds math."""

    left: float
    top: float
    right: float
    bottom: float

    @property
    def width(self) -> float:
        return max(0.0, self.right - self.left)

    @property
    def height(self) -> float:
        return max(0.0, self.bottom - self.top)

    @property
    def center_x(self) -> float:
        return self.left + self.width / 2

    @property
    def center_y(self) -> float:
        return self.top + self.height / 2


def _rect_from_bounds(bounds: Iterable[float]) -> Rect:
    left, top, right, bottom = bounds
    return Rect(left=left, top=top, right=right, bottom=bottom)


def _node_children(node: dict[str, Any]) -> list[dict[str, Any]]:
    return node.get("subNodes", []) or []


def estimate_font_size(
    bounds: Rect,
    physical_size: tuple[float, float],
    virtual_size: tuple[float, float],
    num_lines: int = 1,
    line_height_ratio: float = 1.2,
) -> int:
    """Estimate a font size from bounds + device metrics.

    Args:
        bounds: Text bounds in physical pixels.
        physical_size: (width, height) in physical pixels from the device.
        virtual_size: (width, height) in virtual/logical pixels from the device.
        num_lines: Number of lines for the text node (defaults to 1).
        line_height_ratio: Typical line-height multiplier used for text.

    Returns:
        Estimated font size in virtual pixels (rounded to int).
    """

    physical_width, physical_height = physical_size
    virtual_width, virtual_height = virtual_size

    # Prefer width-based scale because most UI specs anchor to width.
    if virtual_width > 0:
        scale = physical_width / virtual_width
    elif virtual_height > 0:
        scale = physical_height / virtual_height
    else:
        scale = 1.0

    # Convert physical height into virtual height.
    virtual_text_height = bounds.height / scale
    per_line_height = virtual_text_height / max(1, num_lines)

    # Estimate font size from line height; clamp to a sensible minimum.
    estimated_size = per_line_height / line_height_ratio
    return max(10, int(round(estimated_size)))


def _infer_gap(children: list[dict[str, Any]], direction: str) -> int:
    """Infer average gap between children along the main axis."""

    if len(children) < 2:
        return 0

    axis = "x" if direction == "row" else "y"
    rects = [
        _rect_from_bounds(child["bounds"]) for child in children if child.get("bounds")
    ]
    if len(rects) < 2:
        return 0

    rects.sort(key=lambda rect: rect.left if axis == "x" else rect.top)
    gaps: list[float] = []
    for prev, curr in zip(rects, rects[1:]):
        gap = (curr.left - prev.right) if axis == "x" else (curr.top - prev.bottom)
        if gap > 0:
            gaps.append(gap)

    if not gaps:
        return 0
    return int(round(median(gaps)))


def _align_main(
    container: Rect, children: list[Rect], direction: str
) -> Optional[str]:
    """Infer alignMain based on child placement along main axis."""

    if not children:
        return None

    axis_start = container.left if direction == "row" else container.top
    axis_end = container.right if direction == "row" else container.bottom
    axis_size = container.width if direction == "row" else container.height
    axis_center = container.center_x if direction == "row" else container.center_y

    child_start = min(child.left if direction == "row" else child.top for child in children)
    child_end = max(child.right if direction == "row" else child.bottom for child in children)
    child_center = (child_start + child_end) / 2

    tolerance = max(8, axis_size * 0.08)

    if len(children) > 1:
        near_start = abs(child_start - axis_start) <= tolerance
        near_end = abs(axis_end - child_end) <= tolerance
        if near_start and near_end:
            return "between"

    if abs(child_center - axis_center) <= tolerance:
        return "center"

    if abs(child_start - axis_start) <= tolerance:
        return "start"

    if abs(axis_end - child_end) <= tolerance:
        return "end"

    return "start"


def _align_cross(container: Rect, children: list[Rect], direction: str) -> Optional[str]:
    """Infer alignCross based on child placement along the cross axis."""

    if not children:
        return None

    axis_start = container.top if direction == "row" else container.left
    axis_end = container.bottom if direction == "row" else container.right
    axis_size = container.height if direction == "row" else container.width
    axis_center = container.center_y if direction == "row" else container.center_x

    centers = [child.center_y if direction == "row" else child.center_x for child in children]
    average_center = sum(centers) / len(centers)

    tolerance = max(8, axis_size * 0.08)

    if abs(average_center - axis_center) <= tolerance:
        return "center"

    min_edge = min(child.top if direction == "row" else child.left for child in children)
    max_edge = max(child.bottom if direction == "row" else child.right for child in children)

    if abs(min_edge - axis_start) <= tolerance:
        return "start"

    if abs(axis_end - max_edge) <= tolerance:
        return "end"

    return "start"


def _map_direction(value: str | None) -> str:
    """Map source direction strings to DSL direction values."""

    if not value:
        return "col"
    lowered = value.lower()
    if "row" in lowered:
        return "row"
    if "col" in lowered:
        return "col"
    if "stack" in lowered:
        # WidgetDSL doesn't have stack. Treat as column to preserve layout order.
        return "col"
    return "col"


def _leaf_component(node: dict[str, Any]) -> Optional[str]:
    """Return component name for leaf nodes, or None if it should be a container."""

    node_type = node.get("type", "").lower()
    if node_type in {"text", "paragraph"}:
        return "Text"
    if node_type == "icon":
        return "Icon"
    if node_type == "image":
        return "Image"
    return None


def _convert_leaf(
    node: dict[str, Any],
    rect: Rect,
    physical_size: tuple[float, float],
    virtual_size: tuple[float, float],
) -> dict[str, Any]:
    """Convert a leaf node into WidgetDSL leaf representation."""

    component = _leaf_component(node)
    if component is None:
        raise ValueError(f"Unsupported leaf node type: {node.get('type')}")

    dsl_node: dict[str, Any] = {
        "type": "leaf",
        "component": component,
    }

    if component == "Text":
        num_lines = int(node.get("num_line", 1) or 1)
        dsl_node["content"] = node.get("text", "")
        dsl_node["props"] = {
            "fontSize": estimate_font_size(
                rect,
                physical_size=physical_size,
                virtual_size=virtual_size,
                num_lines=num_lines,
            )
        }
        if num_lines > 1:
            dsl_node["props"]["maxLines"] = num_lines
    elif component == "Icon":
        dsl_node["props"] = {
            "name": node.get("content", ""),
            "size": max(12, int(round(rect.height))),
        }
    elif component == "Image":
        # Placeholder source; replace at rendering time.
        dsl_node["props"] = {"src": ""}
        dsl_node["width"] = int(round(rect.width))
        dsl_node["height"] = int(round(rect.height))

    return dsl_node


def _infer_flex(
    rect: Rect, parent_rect: Optional[Rect], parent_direction: Optional[str]
) -> Optional[float]:
    """Infer flex value based on bounds relative to parent bounds."""

    if not parent_rect or not parent_direction:
        return None

    parent_size = (
        parent_rect.width if parent_direction == "row" else parent_rect.height
    )
    if parent_size <= 0:
        return None

    child_size = rect.width if parent_direction == "row" else rect.height
    ratio = max(0.0, child_size / parent_size)
    return round(ratio, 3)


def _convert_container(
    node: dict[str, Any],
    rect: Rect,
    physical_size: tuple[float, float],
    virtual_size: tuple[float, float],
    parent_rect: Optional[Rect],
    parent_direction: Optional[str],
) -> dict[str, Any]:
    """Convert a container node to WidgetDSL container representation."""

    direction = _map_direction(node.get("direction"))
    children = [
        _convert_node(child, physical_size, virtual_size, rect, direction)
        for child in _node_children(node)
    ]

    child_rects = [
        _rect_from_bounds(child["bounds"])
        for child in _node_children(node)
        if child.get("bounds")
    ]

    dsl_node: dict[str, Any] = {
        "type": "container",
        "direction": direction,
        "gap": _infer_gap(_node_children(node), direction),
        "alignMain": _align_main(rect, child_rects, direction),
        "alignCross": _align_cross(rect, child_rects, direction),
        "flex": _infer_flex(rect, parent_rect, parent_direction),
        "children": children,
    }

    # Remove null alignment fields to keep output clean.
    if dsl_node["alignMain"] is None:
        dsl_node.pop("alignMain")
    if dsl_node["alignCross"] is None:
        dsl_node.pop("alignCross")
    if dsl_node["flex"] is None:
        dsl_node.pop("flex")

    return dsl_node


def _convert_node(
    node: dict[str, Any],
    physical_size: tuple[float, float],
    virtual_size: tuple[float, float],
    parent_rect: Optional[Rect],
    parent_direction: Optional[str],
) -> dict[str, Any]:
    """Convert a layout node into WidgetDSL recursively."""

    rect = _rect_from_bounds(node.get("bounds", [0, 0, 0, 0]))
    children = _node_children(node)

    component = _leaf_component(node)
    if component and not children:
        return _convert_leaf(node, rect, physical_size, virtual_size)

    # Treat nodes with children as containers (including wrapper/list/relative/stack nodes).
    return _convert_container(
        node,
        rect,
        physical_size,
        virtual_size,
        parent_rect,
        parent_direction,
    )


def layout_json_to_widget_dsl(
    layout_json: dict[str, Any],
    physical_size: tuple[float, float],
    virtual_size: tuple[float, float],
) -> dict[str, Any]:
    """Convert layout-analysis JSON into WidgetDSL JSON.

    Args:
        layout_json: The layout analysis JSON (root node expected).
        physical_size: Device physical size (width, height).
        virtual_size: Device virtual/logical size (width, height).

    Returns:
        WidgetDSL JSON dictionary compatible with html_compiler.py.
    """

    root_rect = _rect_from_bounds(layout_json.get("bounds", [0, 0, 0, 0]))
    root_node = _convert_node(layout_json, physical_size, virtual_size, None, None)

    return {
        "widget": {
            "padding": 0,
            "aspectRatio": [int(round(root_rect.width)), int(round(root_rect.height))],
            "root": root_node,
        }
    }


def main() -> None:
    """CLI entry point for quick conversions.

    Example:
        python layout_json_to_dsl.py input.json 672 1317 360 720
    """

    import argparse

    parser = argparse.ArgumentParser(
        description="Convert layout-analysis JSON to WidgetDSL JSON."
    )
    parser.add_argument("input", help="Path to layout JSON file")
    parser.add_argument("physical_width", type=float, help="Physical width")
    parser.add_argument("physical_height", type=float, help="Physical height")
    parser.add_argument("virtual_width", type=float, help="Virtual/logical width")
    parser.add_argument("virtual_height", type=float, help="Virtual/logical height")
    parser.add_argument("-o", "--output", help="Output JSON path")

    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as handle:
        layout_json = json.load(handle)

    widget_dsl = layout_json_to_widget_dsl(
        layout_json,
        physical_size=(args.physical_width, args.physical_height),
        virtual_size=(args.virtual_width, args.virtual_height),
    )

    output = json.dumps(widget_dsl, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(output)
    else:
        print(output)


if __name__ == "__main__":
    main()
