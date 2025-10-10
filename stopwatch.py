"""Simple stopwatch tool"""

import curses
from curses import A_BOLD, A_NORMAL
from datetime import datetime, timedelta
import sys
import time


class StopwatchFormat:
    """Format handler for stopwatch display"""

    FORMAT_DECIMAL_SECONDS = "format_decimal_seconds"
    FORMAT_MINUTES_SECONDS = "format_minutes_seconds"
    FORMAT_HOURS_MINUTES_SECONDS = "format_hours_minutes_seconds"
    FORMATS = [
        FORMAT_DECIMAL_SECONDS,
        FORMAT_MINUTES_SECONDS,
        FORMAT_HOURS_MINUTES_SECONDS,
    ]

    def __init__(self) -> None:
        """Set the initial format to decimal seconds"""
        self.format = StopwatchFormat.FORMAT_DECIMAL_SECONDS

    def prev(self) -> None:
        """Switch to the prev format mode"""
        self.next(increment=-1)

    def next(self, increment: int = 1) -> None:
        """Switch to the next format mode"""
        icurrent = StopwatchFormat.FORMATS.index(self.format)
        inext = (icurrent + increment) % len(StopwatchFormat.FORMATS)
        self.format = StopwatchFormat.FORMATS[inext]

    def row_time(self, time: timedelta, column_width: int = 13, offset: int = 0) -> str:
        """Formatted times for the current and total timestamps"""

        def _ss(td: timedelta) -> str:
            """Convert timedelta to "ss.s" """
            return f"{td.total_seconds():.1f}"

        def _hh_mm_ss(td: timedelta) -> str:
            """Convert timedelta to "hh:mm:ss" """
            hh, remainder = divmod(int(td.total_seconds()), 3600)
            mm, ss = divmod(remainder, 60)
            return f"{hh:02}:{mm:02}:{ss:02}"

        def _mm_ss(td: timedelta) -> str:
            """Convert timedelta to "mm:ss" """
            mm, ss = divmod(int(td.total_seconds()), 60)
            return f"{mm:02}:{ss:02}"

        match self.format:
            case StopwatchFormat.FORMAT_DECIMAL_SECONDS:
                formatter = _ss
            case StopwatchFormat.FORMAT_MINUTES_SECONDS:
                formatter = _mm_ss
            case StopwatchFormat.FORMAT_HOURS_MINUTES_SECONDS:
                formatter = _hh_mm_ss
            case _:
                raise curses.error(" format error row {self.format}")

        return f"{formatter(time):>{column_width+offset}s}"

    @property
    def buffer_key(self) -> str:
        """Make the key for the buffer"""
        match self.format:
            case StopwatchFormat.FORMAT_DECIMAL_SECONDS:
                unit = "s"
                space = "        "
            case StopwatchFormat.FORMAT_MINUTES_SECONDS:
                unit = "mm:ss"
                space = "    "
            case StopwatchFormat.FORMAT_HOURS_MINUTES_SECONDS:
                unit = "hh:mm:ss"
                space = " "
            case _:
                raise curses.error("format error key {self.format}")
        return f"  #     Time {space}lap({unit}){space}total({unit})"


class StopwatchDisplay:
    """Class to handle the display of the stopwatch data"""

    def __init__(self, screen: curses.window) -> None:
        """Create a StopwatchDisplay object to write with"""
        self.screen = screen
        self.clear_buffer = False
        self.format = StopwatchFormat()
        self.verbose = False

        self.init_curses()
        self.set_screen_size()
        self.write_header()

    def init_curses(self) -> None:
        """Set curses settings"""
        curses.noecho()
        curses.cbreak()
        self.screen.nodelay(True)

    def set_screen_size(self) -> None:
        """Detect and record rows/cols counts"""
        screenrows, screencols = self.screen.getmaxyx()
        self.num_header_rows = len(self.header_rows)
        self.num_buffer_rows = screenrows - self.num_header_rows
        self.num_cols = screencols

    @property
    def blank_line(self) -> str:
        """Make a blank line"""
        return " " * (self.num_cols - 1)

    def exit_msg(self, timestamps) -> str | None:
        """Generate an exit message"""
        if self.verbose:
            header = self.format.buffer_key
            buffer = self.get_rows(timestamps, as_string=True)
            msg = f"{header}\n{buffer}"
        else:
            msg = None
        return msg

    @property
    def header_rows(self) -> list[str]:
        """Generate header text rows"""
        return [
            "Stopwatch:" + (" (verbose mode)" if self.verbose else ""),
            "  q to quit, space/j/n/m to mark a lap, u/k/p to undo a mark, ",
            "  slash/y (forward) Y/? (backward) to cycle display format ",
            "  (seconds / mm:ss / hh:mm:ss)",
            "  v to toggle verbosity (screen dump vs silent quit)",
            "",
            self.format.buffer_key,
        ]

    def write_header(self) -> None:
        """Write the header (above the display buffer)"""
        for i, header_row in enumerate(self.header_rows):
            self.screen.addstr(i, 0, self.blank_line)  # clear line
            self.screen.addstr(i, 0, header_row)

    def get_rows(
        self, timestamps: list[datetime], as_string: bool = False
    ) -> str | list[str]:
        """Get the rows to display"""

        def _row_text(time: datetime, previous: datetime, lap_num: int) -> str:
            time_str = f"{time.strftime('%H:%M:%S')}"
            lap_time = self.format.row_time(time - previous)
            total_time = self.format.row_time(time - timestamps[0], offset=2)
            return f"{lap_num:3} {time_str} {lap_time} {total_time}"

        rows = []

        # Recorded timestamps -> static updates. Skip first timestamp because
        # that's the zero point. Enumerated 'i' is zero-based, so timestamps[i]
        # is the previous timestamp to 'timestamp'.
        for i, timestamp in enumerate(timestamps[1:]):
            previous = timestamps[i]
            rows.append(_row_text(timestamp, previous, i + 1))

        # The bottom row is updated-live (so "time" is now and "previous" is the
        # last timestamp).
        time = datetime.now()
        previous = timestamps[-1]
        rows.append(_row_text(time, previous, len(timestamps)))

        return "\n".join(rows) if as_string else rows

    def write_buffer(self, timestamps: list[datetime]) -> None:
        """Write the lap info for each lap into the display buffer"""

        rows = self.get_rows(timestamps)

        # Write visible lines (the last num_buffer_rows timestamps) to buffer.
        # If the buffer has rotated, clear_buffer will be true, so erase each
        # line first, and erase the rest of the buffer if applicable.
        istop = len(timestamps)
        istart = max(istop - self.num_buffer_rows, 0)
        for i in range(istart, istop):
            row_num = i - istart
            if self.clear_buffer:
                self._clear_row(row_num)
            fmt = A_BOLD if i == istop - 1 else A_NORMAL
            self._write_buffer_row(row_num, rows[i], fmt)

        # Clear the bottom of the buffer, if requested:
        for i in range(istop, self.num_buffer_rows):
            if self.clear_buffer:
                self._clear_row(i - istart)

        # Turn off clear_buffer if it is on:
        if self.clear_buffer:
            self.clear_buffer = False

    def _write_buffer_row(self, lap_num: int, text: str, fmt: int = A_NORMAL) -> None:
        """Write formatted text to a line in the display buffer"""
        row = self.num_header_rows + (lap_num % self.num_buffer_rows)
        try:
            self.screen.addstr(row, 0, text, fmt)
        except curses.error:
            pass

    def _clear_row(self, lap_num: int) -> None:
        """Erase one row"""
        self._write_buffer_row(lap_num, self.blank_line)

    def check_clear(self, num_rows: int = 9999):
        """
        Set the toggle to clear the buffer if there are too many rows to
        display, or if called without args.
        """
        self.clear_buffer = num_rows > self.num_buffer_rows


class Stopwatch:
    """Class to emulate a stopwatch"""

    def __init__(self, screen: curses.window) -> None:
        """Create a Stopwatch object"""
        try:
            self.display = StopwatchDisplay(screen)
        except curses.error:
            self._quit("Display setup error (screen too small?), quitting")

        self.timestamps = [datetime.now()]

        self.keystroke_actions = {
            **dict.fromkeys(" jnm\n", self.add_timestamp),  # add a lap
            **dict.fromkeys("ukp", self.remove_timestamp),  # remove a lap
            **dict.fromkeys("/y", self._next_format),  # cycle display formats
            **dict.fromkeys("Y?", self._prev_format),  # cycle display formats
            "v": self._toggle_verbose,  # toggle verbosity
            "q": self._quit,  # quit
            str(curses.KEY_RESIZE): self._resize,  # handle a resize event
            '\x01': self._no_input, # ord(abs(-1)), where -1 is the "no input" curses code from getch
        }

    def _no_input(self) -> None:
        """Raise this specific error so that the buffer will get written"""
        raise curses.error("no keyboard input")

    def _quit(self, msg: str | None = None) -> None:
        if msg is None:
            msg = self.display.exit_msg(self.timestamps)
        sys.exit(msg)

    def _resize(self):
        self.display.set_screen_size()

    def _toggle_verbose(self):
        self.display.verbose = not self.display.verbose
        self.display.write_header()

    def _change_format(self, direction="next"):
        if direction == "next":
            self.display.format.next()
        else:
            self.display.format.prev()
        self.display.check_clear()
        self.display.write_header()

    def _prev_format(self):
        self._change_format("prev")

    def _next_format(self):
        self._change_format()

    def add_timestamp(self) -> None:
        """Add a new timestamp/lap"""
        self.timestamps.append(datetime.now())
        self.display.check_clear(len(self.timestamps))

    def remove_timestamp(self) -> None:
        """Remove the most recent timestamp; undo last mark"""
        if len(self.timestamps) > 1:
            self.timestamps.pop()
        self.display.check_clear()

    def run(self) -> None:
        """Run the stopwatch"""
        while True:
            try:
                key_input = chr(abs(self.display.screen.getch()))
                if action := self.keystroke_actions.get(key_input):
                    action()
            except curses.error:
                self.display.write_buffer(self.timestamps)
                time.sleep(0.1)


def main(screen: curses.window) -> None:
    """Main stopwatch function"""
    stopwatch = Stopwatch(screen)
    stopwatch.run()


if __name__ == "__main__":
    curses.wrapper(main)
