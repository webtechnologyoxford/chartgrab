"""chartgrab: read bar-chart values from browser canvases and chart images."""
from .axis import LinearAxis, parse_number
from .bars import Bar, ColorClass, find_bars, parse_color
from .digitize import BarValue, auto_axes, digitize_bars
from .snapshot import Snapshot, collector_expression

__version__ = "0.1.0"
__all__ = ["LinearAxis", "parse_number", "Bar", "ColorClass", "find_bars", "parse_color",
           "BarValue", "auto_axes", "digitize_bars", "Snapshot", "collector_expression"]
