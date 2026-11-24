# Normalized Writing-System Vector Stroke Specification

Public writing-system datasets (`schemas/writing-system.schema.json`) represent character stroke trajectories on a canonical unit square canvas:

- **Coordinate Space:** Top-left origin `(0.0, 0.0)` to bottom-right `(1.0, 1.0)`.
- **Ordered Polyline Control Points:** Each stroke contains an ordered `points` list (`len >= 2`) ordered along writing direction, starting from `stroke_index: 1`.
- **Rendering Independence:** Proprietary interactive drawing evaluators remain outside public repositories; clean normalized points work uniformly across SVG, HTML5 Canvas, Flutter CustomPainter, and academic handwriting corpora.
