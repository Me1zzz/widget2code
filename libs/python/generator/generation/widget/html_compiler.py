"""Compile WidgetDSL specs to HTML."""

from __future__ import annotations

import json
import math
import secrets
import time
from typing import Any


def compile_widget_dsl_to_html(widget_dsl: dict) -> str:
    if not widget_dsl.get("widget", {}).get("root"):
        raise ValueError("Invalid widget spec: missing widget.root")

    lines: list[str] = []
    scripts: list[str] = []
    styles: list[str] = []
    component_counter = {"chart": 0, "sparkline": 0}

    def write(line: str) -> None:
        lines.append(line)

    def write_script(script: str) -> None:
        scripts.append(script)

    def write_style(style: str) -> None:
        styles.append(style)

    def format_css_value(value: Any) -> Any:
        if isinstance(value, str):
            return value
        if isinstance(value, (int, float)):
            return f"{value}px"
        return value

    def format_style_object(style_entries: list[str]) -> str:
        formatted: list[str] = []
        for style in style_entries:
            property_name, value = style.split(":", 1)
            clean_value = value.replace("'", "").replace('"', "")
            formatted.append(f"{property_name}: {format_css_value(clean_value)}")
        return "; ".join(formatted)

    def unique_id(prefix: str) -> str:
        return f"{prefix}-{int(time.time() * 1000)}-{secrets.token_hex(4)}"

    def render_node(node: dict, depth: int = 0) -> None:
        indent = "  " * depth

        if node.get("type") == "container":
            direction = node.get("direction", "row")
            gap = node.get("gap", 8)
            padding = node.get("padding")
            align_main = node.get("alignMain")
            align_cross = node.get("alignCross")
            flex = node.get("flex")
            width = node.get("width")
            height = node.get("height")
            background_color = node.get("backgroundColor")
            border_radius = node.get("borderRadius")
            children = node.get("children", [])

            css_styles: list[str] = []
            css_styles.append("display: flex")
            css_styles.append(
                f"flex-direction: {'column' if direction == 'col' else 'row'}"
            )
            if gap:
                css_styles.append(f"gap: {gap}px")
            if padding:
                css_styles.append(f"padding: {padding}px")
            if flex is not None:
                css_styles.append(f"flex: {flex}")
            if width is not None:
                css_styles.append(f"width: {format_css_value(width)}")
            if height is not None:
                css_styles.append(f"height: {format_css_value(height)}")
            if background_color:
                css_styles.append(f"background-color: {background_color}")
            if border_radius is not None:
                css_styles.append(f"border-radius: {border_radius}px")
            if align_main:
                align_map = {
                    "start": "flex-start",
                    "end": "flex-end",
                    "center": "center",
                    "between": "space-between",
                }
                css_styles.append(
                    f"justify-content: {align_map.get(align_main, align_main)}"
                )
            if align_cross:
                align_map = {
                    "start": "flex-start",
                    "end": "flex-end",
                    "center": "center",
                }
                css_styles.append(
                    f"align-items: {align_map.get(align_cross, align_cross)}"
                )

            write(f"{indent}<div style=\"{format_style_object(css_styles)}\">")
            for child in children:
                render_node(child, depth + 1)
            write(f"{indent}</div>")
            return

        if node.get("type") == "leaf":
            component_name = node.get("component")
            props = node.get("props", {})
            flex = node.get("flex")
            width = node.get("width")
            height = node.get("height")
            content = node.get("content")

            if not component_name:
                raise ValueError("Invalid leaf node: missing component")

            merged_props = dict(props)

            uses_content_prop = {"Button", "ProgressRing"}
            if content and component_name in uses_content_prop:
                merged_props["content"] = content

            if component_name == "Text":
                render_text_component(merged_props, content, depth, flex, width, height)
            elif component_name == "Button":
                render_button_component(merged_props, depth, flex, width, height)
            elif component_name == "Icon":
                render_icon_component(merged_props, depth, flex, width, height)
            elif component_name == "Image":
                render_image_component(merged_props, depth, flex, width, height)
            elif component_name == "Checkbox":
                render_checkbox_component(merged_props, depth, flex, width, height)
            elif component_name == "Divider":
                render_divider_component(merged_props, depth, flex, width, height)
            elif component_name == "Indicator":
                render_indicator_component(merged_props, depth, flex, width, height)
            elif component_name == "ProgressBar":
                render_progress_bar_component(merged_props, depth, flex, width, height)
            elif component_name == "ProgressRing":
                render_progress_ring_component(merged_props, depth, flex, width, height)
            elif component_name == "Sparkline":
                render_sparkline_component(merged_props, depth, flex, width, height)
            elif component_name in {
                "LineChart",
                "BarChart",
                "StackedBarChart",
                "RadarChart",
                "PieChart",
            }:
                render_chart_component(
                    component_name, merged_props, depth, flex, width, height
                )
            else:
                render_generic_component(
                    component_name, merged_props, content, depth, flex, width, height
                )

    def render_text_component(
        props: dict, content: str | None, depth: int, flex: Any, width: Any, height: Any
    ) -> None:
        indent = "  " * depth
        style_entries = get_text_styles(props, flex, width, height)
        text_content = content or props.get("content") or ""
        write(
            f"{indent}<div style=\"{format_style_object(style_entries)}\">"
            f"{text_content}</div>"
        )

    def render_button_component(
        props: dict, depth: int, flex: Any, width: Any, height: Any
    ) -> None:
        indent = "  " * depth
        icon = props.get("icon")
        content = props.get("content")
        icon_size = props.get("iconSize")
        icon_color = props.get("iconColor")
        style_entries = get_button_styles(props, flex, width, height)

        button_id = unique_id("button")

        write(
            f"{indent}<div id=\"{button_id}\" style=\""
            f"{format_style_object(style_entries)}\" role=\"button\" tabindex=\"0\">"
        )

        if icon:
            icon_class = map_to_icon_class(icon)
            icon_styles = [
                "display: flex",
                "align-items: center",
                "justify-content: center",
                f"width: {icon_size or props.get('fontSize', 14) * 1.2 or 16.8}px",
                f"height: {icon_size or props.get('fontSize', 14) * 1.2 or 16.8}px",
                f"color: {icon_color or props.get('color') or 'white'}",
            ]
            write(
                f"{indent}  <i class=\"{icon_class}\" style=\""
                f"{format_style_object(icon_styles)}\"></i>"
            )
        elif content:
            write(
                f"{indent}  <span style=\"display: flex; align-items: center; "
                f"justify-content: center;\">{content}</span>"
            )
        else:
            write(
                f"{indent}  <span style=\"display: flex; align-items: center; "
                f"justify-content: center;\">Button</span>"
            )

        write(f"{indent}</div>")

        write_script(
            f"""
      (function() {{
        const button = document.getElementById('{button_id}');
        if (!button) return;

        // Add hover effects
        button.addEventListener('mouseenter', function() {{
          this.style.transform = 'scale(1.02)';
          this.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
          this.style.transition = 'all 0.2s ease';
        }});

        button.addEventListener('mouseleave', function() {{
          this.style.transform = 'scale(1)';
          this.style.boxShadow = 'none';
        }});

        // Add active state
        button.addEventListener('mousedown', function() {{
          this.style.transform = 'scale(0.98)';
        }});

        button.addEventListener('mouseup', function() {{
          this.style.transform = 'scale(1.02)';
        }});

        // Keyboard support
        button.addEventListener('keydown', function(e) {{
          if (e.key === 'Enter' || e.key === ' ') {{
            e.preventDefault();
            this.style.transform = 'scale(0.98)';
          }}
        }});

        button.addEventListener('keyup', function(e) {{
          if (e.key === 'Enter' || e.key === ' ') {{
            e.preventDefault();
            this.style.transform = 'scale(1)';
          }}
        }});
      }})();
    """
        )

    def render_icon_component(
        props: dict, depth: int, flex: Any, width: Any, height: Any
    ) -> None:
        indent = "  " * depth
        name = props.get("name")
        size = props.get("size", 20)
        color = props.get("color", "rgba(255, 255, 255, 0.85)")

        style_entries = [
            "display: inline-flex",
            "align-items: center",
            "justify-content: center",
            f"width: {size}px",
            f"height: {size}px",
            f"color: {color}",
        ]

        if flex is not None:
            style_entries.append(f"flex: {flex}")
        if width is not None:
            style_entries.append(f"width: {format_css_value(width)}")
        if height is not None:
            style_entries.append(f"height: {format_css_value(height)}")

        icon_class = map_to_icon_class(name)

        write(
            f"{indent}<i class=\"{icon_class}\" style=\""
            f"{format_style_object(style_entries)}\"></i>"
        )

    def render_image_component(
        props: dict, depth: int, flex: Any, width: Any, height: Any
    ) -> None:
        indent = "  " * depth
        src = props.get("src")
        alt = props.get("alt", "")

        style_entries = ["display: block", "max-width: 100%", "max-height: 100%"]

        if flex is not None:
            style_entries.append(f"flex: {flex}")
        if width is not None:
            style_entries.append(f"width: {format_css_value(width)}")
        if height is not None:
            style_entries.append(f"height: {format_css_value(height)}")

        write(
            f"{indent}<img src=\"{src}\" alt=\"{alt}\" style=\""
            f"{format_style_object(style_entries)}\" />"
        )

    def render_checkbox_component(
        props: dict, depth: int, flex: Any, width: Any, height: Any
    ) -> None:
        indent = "  " * depth
        checked = props.get("checked", False)

        style_entries = [
            "width: 20px",
            "height: 20px",
            "border: 2px solid #ccc",
            "border-radius: 4px",
            "display: flex",
            "align-items: center",
            "justify-content: center",
            f"background-color: {'#007AFF' if checked else 'white'}",
        ]

        if flex is not None:
            style_entries.append(f"flex: {flex}")
        if width is not None:
            style_entries.append(f"width: {format_css_value(width)}")
        if height is not None:
            style_entries.append(f"height: {format_css_value(height)}")

        checkmark = "✓" if checked else ""
        write(
            f"{indent}<div style=\"{format_style_object(style_entries)}\">"
            f"{checkmark}</div>"
        )

    def render_divider_component(
        props: dict, depth: int, flex: Any, width: Any, height: Any
    ) -> None:
        indent = "  " * depth
        orientation = props.get("orientation", "horizontal")
        color = props.get("color", "#e0e0e0")
        thickness = props.get("thickness", 1)

        style_entries = [
            f"background-color: {color}",
            f"{'height' if orientation == 'horizontal' else 'width'}: {thickness}px",
            f"{'width' if orientation == 'horizontal' else 'height'}: 100%",
        ]

        if flex is not None:
            style_entries.append(f"flex: {flex}")
        if width is not None and orientation == "vertical":
            style_entries.append(f"width: {format_css_value(width)}")
        if height is not None and orientation == "horizontal":
            style_entries.append(f"height: {format_css_value(height)}")

        write(f"{indent}<div style=\"{format_style_object(style_entries)}\"></div>")

    def render_indicator_component(
        props: dict, depth: int, flex: Any, width: Any, height: Any
    ) -> None:
        indent = "  " * depth
        color = props.get("color", "#34C759")
        size = props.get("size", 8)

        style_entries = [
            f"width: {size}px",
            f"height: {size}px",
            "border-radius: 50%",
            f"background-color: {color}",
        ]

        if flex is not None:
            style_entries.append(f"flex: {flex}")
        if width is not None:
            style_entries.append(f"width: {format_css_value(width)}")
        if height is not None:
            style_entries.append(f"height: {format_css_value(height)}")

        write(f"{indent}<div style=\"{format_style_object(style_entries)}\"></div>")

    def render_progress_bar_component(
        props: dict, depth: int, flex: Any, width: Any, height: Any
    ) -> None:
        indent = "  " * depth
        progress = props.get("progress", 0.5)
        color = props.get("color", "#007AFF")
        background_color = props.get("backgroundColor", "#e0e0e0")

        container_id = unique_id("progress")

        container_styles = [
            "width: 100%",
            "height: 8px",
            f"background-color: {background_color}",
            "border-radius: 4px",
            "overflow: hidden",
        ]

        if flex is not None:
            container_styles.append(f"flex: {flex}")
        if width is not None:
            container_styles.append(f"width: {format_css_value(width)}")
        if height is not None:
            container_styles.append(f"height: {format_css_value(height)}")

        write(
            f"{indent}<div id=\"{container_id}\" style=\""
            f"{format_style_object(container_styles)}\">"
        )
        write(
            f"{indent}  <div style=\"width: {progress * 100}%; height: 100%; "
            f"background-color: {color}; transition: width 0.3s ease;\"></div>"
        )
        write(f"{indent}</div>")

    def render_progress_ring_component(
        props: dict, depth: int, flex: Any, width: Any, height: Any
    ) -> None:
        indent = "  " * depth
        percentage = props.get("percentage", 0)
        color = props.get("color", "#34C759")
        background_color = props.get("backgroundColor", "#d1d1d6")
        size = props.get("size", 80)
        stroke_width = props.get("strokeWidth", 6)
        icon_name = props.get("iconName")
        icon_size = props.get("iconSize", 32)
        icon_color = props.get("iconColor", "#000000")
        content = props.get("content")
        text_color = props.get("textColor", "#000000")
        font_size = props.get("fontSize", 14)
        font_weight = props.get("fontWeight", 500)

        progress_ring_id = unique_id("progressring")

        normalized_percentage = min(max(percentage, 0), 100)
        radius = (size - stroke_width) / 2
        circumference = 2 * math.pi * radius
        stroke_dashoffset = circumference - (normalized_percentage / 100) * circumference

        container_styles = [
            "position: relative",
            f"width: {size}px",
            f"height: {size}px",
            "display: flex",
            "align-items: center",
            "justify-content: center",
            "flex: 0 0 auto",
            "flex-shrink: 0",
        ]

        if flex is not None:
            container_styles.append(f"flex: {flex}")
        if width is not None:
            container_styles.append(f"width: {format_css_value(width)}")
        if height is not None:
            container_styles.append(f"height: {format_css_value(height)}")

        write(
            f"{indent}<div id=\"{progress_ring_id}\" style=\""
            f"{format_style_object(container_styles)}\">"
        )
        write(
            f"{indent}  <svg width=\"{size}\" height=\"{size}\" "
            f"style=\"transform: rotate(-90deg);\">"
        )
        write(f"{indent}    <circle")
        write(f"{indent}      cx=\"{size / 2}\"")
        write(f"{indent}      cy=\"{size / 2}\"")
        write(f"{indent}      r=\"{radius}\"")
        write(f"{indent}      fill=\"none\"")
        write(f"{indent}      stroke=\"{background_color}\"")
        write(f"{indent}      stroke-width=\"{stroke_width}\"")
        write(f"{indent}    />")
        write(f"{indent}    <circle")
        write(f"{indent}      id=\"{progress_ring_id}-progress\"")
        write(f"{indent}      cx=\"{size / 2}\"")
        write(f"{indent}      cy=\"{size / 2}\"")
        write(f"{indent}      r=\"{radius}\"")
        write(f"{indent}      fill=\"none\"")
        write(f"{indent}      stroke=\"{color}\"")
        write(f"{indent}      stroke-width=\"{stroke_width}\"")
        write(f"{indent}      stroke-dasharray=\"{circumference}\"")
        write(f"{indent}      stroke-dashoffset=\"{stroke_dashoffset}\"")
        write(f"{indent}      stroke-linecap=\"round\"")
        write(
            f"{indent}      style=\"transition: stroke-dashoffset 0.3s ease;\""
        )
        write(f"{indent}    />")
        write(f"{indent}  </svg>")

        if icon_name or content:
            write(
                f"{indent}  <div style=\"position: absolute; top: 50%; left: 50%; "
                f"transform: translate(-50%, -50%);\">"
            )

            if icon_name:
                icon_class = map_to_icon_class(icon_name)
                icon_styles = [
                    f"width: {icon_size}px",
                    f"height: {icon_size}px",
                    f"color: {icon_color}",
                    "display: flex",
                    "align-items: center",
                    "justify-content: center",
                ]
                write(
                    f"{indent}    <i class=\"{icon_class}\" style=\""
                    f"{format_style_object(icon_styles)}\"></i>"
                )
            elif content:
                text_styles = [
                    f"color: {text_color}",
                    f"font-size: {font_size}px",
                    f"font-weight: {font_weight}",
                    "white-space: nowrap",
                    "display: flex",
                    "align-items: center",
                    "justify-content: center",
                ]
                write(
                    f"{indent}    <span style=\"{format_style_object(text_styles)}\">"
                    f"{content}</span>"
                )

            write(f"{indent}  </div>")

        write(f"{indent}</div>")

        write_script(
            f"""
      (function() {{
        const progressRing = document.getElementById('{progress_ring_id}');
        const progressCircle = document.getElementById('{progress_ring_id}-progress');
        if (!progressRing || !progressCircle) return;

        // Animate on load
        setTimeout(() => {{
          const targetOffset = {stroke_dashoffset};
          progressCircle.style.strokeDashoffset = targetOffset;
        }}, 100);

        // Add hover effect
        progressRing.addEventListener('mouseenter', function() {{
          this.style.transform = 'scale(1.05)';
          this.style.transition = 'transform 0.2s ease';
        }});

        progressRing.addEventListener('mouseleave', function() {{
          this.style.transform = 'scale(1)';
        }});

        // Function to update progress (can be called externally)
        progressRing.updateProgress = function(newPercentage) {{
          const normalizedPercentage = Math.min(Math.max(newPercentage, 0), 100);
          const newOffset = {circumference} - (normalizedPercentage / 100) * {circumference};
          progressCircle.style.strokeDashoffset = newOffset;
        }};
      }})();
    """
        )

    def render_sparkline_component(
        props: dict, depth: int, flex: Any, width: Any, height: Any
    ) -> None:
        indent = "  " * depth
        sparkline_id = f"sparkline-{component_counter['sparkline']}"
        component_counter["sparkline"] += 1
        data = props.get("data", [])
        color = props.get("color", "#34C759")
        w = props.get("width", 80)
        h = props.get("height", 40)

        style_entries = ["display: block", f"width: {w}px", f"height: {h}px"]

        if flex is not None:
            style_entries.append(f"flex: {flex}")
        if width is not None:
            style_entries.append(f"width: {format_css_value(width)}")
        if height is not None:
            style_entries.append(f"height: {format_css_value(height)}")

        write(
            f"{indent}<canvas id=\"{sparkline_id}\" style=\""
            f"{format_style_object(style_entries)}\"></canvas>"
        )

        write_script(
            f"""
      (function() {{
        const canvas = document.getElementById('{sparkline_id}');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        const dpr = window.devicePixelRatio || 1;
        const width = {w};
        const height = {h};
        const data = {json.dumps(data)};
        const color = {json.dumps(color)};

        canvas.width = width * dpr;
        canvas.height = height * dpr;
        ctx.scale(dpr, dpr);

        // Clear canvas
        ctx.clearRect(0, 0, width, height);

        if (data.length < 2) return;

        const max = Math.max(...data);
        const min = Math.min(...data);
        const range = max - min || 1;

        // Draw line
        ctx.beginPath();
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;

        data.forEach((value, index) => {{
          const x = (index / (data.length - 1)) * width;
          const y = height - ((value - min) / range) * height;

          if (index === 0) {{
            ctx.moveTo(x, y);
          }} else {{
            ctx.lineTo(x, y);
          }}
        }});

        ctx.stroke();
      }})();
    """
        )

    def render_chart_component(
        chart_type: str,
        props: dict,
        depth: int,
        flex: Any,
        width: Any,
        height: Any,
    ) -> None:
        indent = "  " * depth
        chart_id = f"chart-{component_counter['chart']}"
        component_counter["chart"] += 1

        style_entries = ["width: 100%", "height: 100%", "min-height: 200px"]

        if flex is not None:
            style_entries.append(f"flex: {flex}")
        if width is not None:
            style_entries.append(f"width: {format_css_value(width)}")
        if height is not None:
            style_entries.append(f"height: {format_css_value(height)}")

        write(
            f"{indent}<div id=\"{chart_id}\" style=\""
            f"{format_style_object(style_entries)}\"></div>"
        )

        chart_option = generate_chart_option(chart_type, props)

        write_script(
            f"""
      (function() {{
        const chartDom = document.getElementById('{chart_id}');
        if (!chartDom) return;

        const myChart = echarts.init(chartDom);
        const option = {json.dumps(chart_option)};

        myChart.setOption(option);
      }})();
    """
        )

    def render_generic_component(
        component_name: str,
        props: dict,
        content: str | None,
        depth: int,
        flex: Any,
        width: Any,
        height: Any,
    ) -> None:
        indent = "  " * depth
        style_entries = get_generic_styles(flex, width, height)

        component_content = content or component_name
        write(
            f"{indent}<div style=\"{format_style_object(style_entries)}\">"
            f"{component_content}</div>"
        )

    def get_text_styles(
        props: dict, flex: Any, width: Any, height: Any
    ) -> list[str]:
        font_size = props.get("fontSize", 14)
        font_weight = props.get("fontWeight", "normal")
        color = props.get("color", "#333333")
        text_align = props.get("textAlign", "left")
        line_height = props.get("lineHeight", 1.4)

        style_entries = [
            f"font-size: {font_size}px",
            f"font-weight: {font_weight}",
            f"color: {color}",
            f"text-align: {text_align}",
            f"line-height: {line_height}",
        ]

        if flex is not None:
            style_entries.append(f"flex: {flex}")
        if width is not None:
            style_entries.append(f"width: {format_css_value(width)}")
        if height is not None:
            style_entries.append(f"height: {format_css_value(height)}")

        return style_entries

    def get_button_styles(
        props: dict, flex: Any, width: Any, height: Any
    ) -> list[str]:
        background_color = props.get("backgroundColor", "rgba(59, 130, 246, 1)")
        color = props.get("color", "rgba(255, 255, 255, 1)")
        border_radius = props.get("borderRadius", 8)
        font_size = props.get("fontSize", 14)
        font_weight = props.get("fontWeight", 500)
        padding = props.get("padding", 12)
        border = props.get("border", "none")

        style_entries = [
            "display: flex",
            "align-items: center",
            "justify-content: center",
            f"background-color: {background_color}",
            f"color: {color}",
            f"border-radius: {border_radius}px",
            f"font-size: {font_size}px",
            f"font-weight: {font_weight}",
            f"padding: {padding}px",
            f"border: {border}",
            "cursor: pointer",
            "user-select: none",
            "outline: none",
            "transition: all 0.2s ease",
        ]

        if flex is not None:
            style_entries.append(f"flex: {flex}")
        if width is not None:
            style_entries.append(f"width: {format_css_value(width)}")
        if height is not None:
            style_entries.append(f"height: {format_css_value(height)}")

        return style_entries

    def get_generic_styles(flex: Any, width: Any, height: Any) -> list[str]:
        style_entries = [
            "display: flex",
            "align-items: center",
            "justify-content: center",
        ]

        if flex is not None:
            style_entries.append(f"flex: {flex}")
        if width is not None:
            style_entries.append(f"width: {format_css_value(width)}")
        if height is not None:
            style_entries.append(f"height: {format_css_value(height)}")

        return style_entries

    def map_to_icon_class(name: str | None) -> str:
        icon_map = {
            "sf:paperplane.fill": "fas fa-paper-plane",
            "sf:sun.max.fill": "fas fa-sun",
            "sf:heart.fill": "fas fa-heart",
            "sf:house.fill": "fas fa-home",
            "sf:star.fill": "fas fa-star",
            "sf:person.fill": "fas fa-user",
            "sf:gear": "fas fa-cog",
            "sf:trash.fill": "fas fa-trash",
            "sf:plus.circle.fill": "fas fa-plus-circle",
            "sf:minus.circle.fill": "fas fa-minus-circle",
            "sf:checkmark.circle.fill": "fas fa-check-circle",
            "sf:xmark.circle.fill": "fas fa-times-circle",
            "sf:arrow.clockwise": "fas fa-sync",
            "sf:play.circle.fill": "fas fa-play-circle",
            "sf:pause.circle.fill": "fas fa-pause-circle",
            "sf:stop.circle.fill": "fas fa-stop-circle",
            "lu:LuDownload": "fas fa-download",
            "lu:LuUpload": "fas fa-upload",
            "lu:LuSettings": "fas fa-cog",
            "lu:LuUser": "fas fa-user",
            "lu:LuMail": "fas fa-envelope",
            "lu:LuPhone": "fas fa-phone",
            "lu:LuCalendar": "fas fa-calendar",
            "lu:LuClock": "fas fa-clock",
            "lu:LuSearch": "fas fa-search",
            "lu:LuBell": "fas fa-bell",
            "lu:LuHeart": "fas fa-heart",
            "lu:LuStar": "fas fa-star",
            "lu:LuTrash": "fas fa-trash",
            "lu:LuPlus": "fas fa-plus",
            "lu:LuMinus": "fas fa-minus",
            "lu:LuCheck": "fas fa-check",
            "lu:LuX": "fas fa-times",
            "lu:LuArrowRight": "fas fa-arrow-right",
            "lu:LuArrowLeft": "fas fa-arrow-left",
            "lu:LuArrowUp": "fas fa-arrow-up",
            "lu:LuArrowDown": "fas fa-arrow-down",
            "ai:AiDownload": "fas fa-download",
            "ai:AiUpload": "fas fa-upload",
            "ai:AiSetting": "fas fa-cog",
            "ai:AiUser": "fas fa-user",
            "ai:AiMail": "fas fa-envelope",
            "fa:FaDownload": "fas fa-download",
            "fa:FaUpload": "fas fa-upload",
            "fa:FaCog": "fas fa-cog",
            "fa:FaUser": "fas fa-user",
            "fa:FaEnvelope": "fas fa-envelope",
            "fa:FaPhone": "fas fa-phone",
            "fa:FaCalendar": "fas fa-calendar",
            "fa:FaClock": "fas fa-clock",
            "fa:FaSearch": "fas fa-search",
            "fa:FaBell": "fas fa-bell",
            "fa:FaHeart": "fas fa-heart",
            "fa:FaStar": "fas fa-star",
            "fa:FaTrash": "fas fa-trash",
            "fa:FaPlus": "fas fa-plus",
            "fa:FaMinus": "fas fa-minus",
            "fa:FaCheck": "fas fa-check",
            "fa:FaTimes": "fas fa-times",
            "fa:FaArrowRight": "fas fa-arrow-right",
            "fa:FaArrowLeft": "fas fa-arrow-left",
            "fa:FaArrowUp": "fas fa-arrow-up",
            "fa:FaArrowDown": "fas fa-arrow-down",
        }

        return icon_map.get(name, "fas fa-question")

    def generate_chart_option(chart_type: str, props: dict) -> dict:
        base_option = {
            "backgroundColor": "transparent",
            "tooltip": {"show": False},
            "animation": False,
        }

        if chart_type == "LineChart":
            return {
                **base_option,
                "xAxis": {"type": "category", "data": props.get("labels", [])},
                "yAxis": {"type": "value"},
                "series": [
                    {
                        "type": "line",
                        "data": props.get("data", []),
                        "smooth": props.get("smooth", True) is not False,
                        "itemStyle": {"color": props.get("color", "#6DD400")},
                    }
                ],
            }
        if chart_type == "BarChart":
            return {
                **base_option,
                "xAxis": {"type": "category", "data": props.get("labels", [])},
                "yAxis": {"type": "value"},
                "series": [
                    {
                        "type": "bar",
                        "data": props.get("data", []),
                        "itemStyle": {"color": props.get("color", "#6DD400")},
                    }
                ],
            }
        if chart_type == "PieChart":
            return {
                **base_option,
                "series": [
                    {
                        "type": "pie",
                        "data": props.get("data", []),
                        "radius": ["50%", "70%"]
                        if props.get("innerRadius")
                        else "70%",
                        "itemStyle": {"color": props.get("color", "#6DD400")},
                    }
                ],
            }

        return base_option

    render_node(widget_dsl["widget"]["root"], 0)

    widget = widget_dsl["widget"]
    background_color = widget.get("backgroundColor")
    border_radius = widget.get("borderRadius")
    padding = widget.get("padding")
    width = widget.get("width")
    height = widget.get("height")

    widget_styles = [
        f"background-color: {background_color or '#f2f2f7'}",
        f"border-radius: {border_radius if border_radius is not None else 20}px",
        f"padding: {padding if padding is not None else 16}px",
        "overflow: hidden",
        "display: inline-flex",
        "flex-direction: column",
        "box-sizing: border-box",
    ]

    if width is not None:
        widget_styles.append(f"width: {format_css_value(width)}")
    if height is not None:
        widget_styles.append(f"height: {format_css_value(height)}")

    html = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>Widget</title>

    <!-- CDN Libraries -->
    <script src=\"https://cdn.jsdelivr.net/npm/echarts@5.6.0/dist/echarts.min.js\"></script>
    <link rel=\"stylesheet\" href=\"https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css\">

    <style>
        body {{
            margin: 0;
            padding: 20px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #f5f5f5;
        }}

        .widget-container {{
            {format_style_object(widget_styles)}
        }}

        {"\n        ".join(styles)}
    </style>
</head>
<body>
    <div class=\"widget-container\">
{"\n        ".join(lines)}
    </div>

    <script>
        {"\n        ".join(scripts)}
    </script>
</body>
</html>"""

    return html
