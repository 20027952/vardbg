import abc
import copy
import sys
from typing import TYPE_CHECKING

import dictdiffer

from . import data

if TYPE_CHECKING:
    from .debugger import Debugger


class Tracer(abc.ABC):
    def __init__(self: "Debugger"):
        # Previous frame and its locals
        self.prev_frame_info = None
        self.prev_locals = {}
        # New frame's locals
        self.new_locals = {}

        # Propagate initialization to other mixins
        super().__init__()

    def trace_callback(self: "Debugger", frame, event, arg):
        """Frame execution callback"""

        # Ignore all other functions
        code = frame.f_code
        if code != self.func.__code__:
            return

        # Get new locals and copy them so they don't change on the next frame
        self.new_locals = copy.deepcopy(frame.f_locals)

        # Don't process the first frame since this callback runs *before*
        # frame execution, not after
        if self.prev_frame_info is not None:
            # Render output prefix for this frame
            self.update_cur_frame(self.prev_frame_info)

            # Diff and print changes
            diff = dictdiffer.diff(self.prev_locals, self.new_locals)
            self.process_locals_diff(diff, self.prev_frame_info)

        # Update previous frame info and locals in preparation for the next frame
        self.prev_frame_info = data.FrameInfo(frame)
        self.prev_locals = self.new_locals

        # Subscribe to the next frame, if any
        return self.trace_callback

    def run(self: "Debugger"):
        # Run function with trace callback registered
        sys.settrace(self.trace_callback)
        self.func()
        sys.settrace(None)

        self.print_summary()