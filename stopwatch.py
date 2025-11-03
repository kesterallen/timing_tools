"""Simple stopwatch tool"""

import curses
import sys
import time
from curses import A_BOLD, A_NORMAL
from datetime import datetime, timedelta
from itertools import pairwise

KEY_NO_INPUT = "\x01"  # No input key (ord(abs(-1)))
COLUMN_WIDTH = 13
OFFSET = 0


class Formatter:
    """Format handler for stopwatch display"""

    FORMAT_DECIMAL_SECONDS = "format_decimal_seconds"
    FORMAT_MINUTES_SECONDS = "format_minutes_seconds"
    FORMAT_HOURS_MINUTES_SECONDS = "format_hours_minutes_seconds"
    FORMAT_HOURS_MINUTES_SECONDS_START = "format_hours_minutes_seconds_start"
    FORMATS = [
        FORMAT_DECIMAL_SECONDS,
        FORMAT_MINUTES_SECONDS,
        FORMAT_HOURS_MINUTES_SECONDS,
        FORMAT_HOURS_MINUTES_SECONDS_START,
    ]

    def __init__(self) -> None:
        """Set the initial format to decimal seconds"""
        self.current_format = Formatter.FORMAT_DECIMAL_SECONDS
        self.month_day = False

    @property
    def is_long_format(self):
        """Flag property for the longest format, which requires different fstrings"""
        return self.current_format == Formatter.FORMAT_HOURS_MINUTES_SECONDS_START

    def prev(self) -> None:
        """Switch to the prev format mode"""
        self.next(increment=-1)

    def next(self, increment: int = 1) -> None:
        """Switch to the next format mode"""
        icurrent = Formatter.FORMATS.index(self.current_format)
        inext = (icurrent + increment) % len(Formatter.FORMATS)
        self.current_format = Formatter.FORMATS[inext]

    @classmethod
    def _ss(cls, td: timedelta) -> str:
        """Convert timedelta to "ss.s" """
        return f"{td.total_seconds():.1f}"

    @classmethod
    def _hh_mm_ss(cls, td: timedelta) -> str:
        """Convert timedelta to "hh:mm:ss" """
        hh, remainder = divmod(int(td.total_seconds()), 3600)
        mm, ss = divmod(remainder, 60)
        return f"{hh:02}:{mm:02}:{ss:02}"

    @classmethod
    def _mm_ss(cls, td: timedelta) -> str:
        """Convert timedelta to "mm:ss" """
        mm, ss = divmod(int(td.total_seconds()), 60)
        return f"{mm:02}:{ss:02}"

    def row_time(self, td: timedelta, offset: int = OFFSET) -> str:
        """Formatted times for the current and total timestamps"""
        match self.current_format:
            case Formatter.FORMAT_DECIMAL_SECONDS:
                formatter = Formatter._ss
            case Formatter.FORMAT_MINUTES_SECONDS:
                formatter = Formatter._mm_ss
            case Formatter.FORMAT_HOURS_MINUTES_SECONDS:
                formatter = Formatter._hh_mm_ss
            case Formatter.FORMAT_HOURS_MINUTES_SECONDS_START:
                formatter = Formatter._hh_mm_ss
            case _:
                raise curses.error(" format error row {self.current_format}")

        return f"{formatter(td):>{COLUMN_WIDTH + offset}s}"

    @property
    def buffer_key(self) -> str:
        """Make the key for the buffer"""
        month_day = "      " if self.month_day else ""
        match self.current_format:
            case Formatter.FORMAT_DECIMAL_SECONDS:
                buftime = f" {month_day}Time"
                unit = "s"
                space = "        "
            case Formatter.FORMAT_MINUTES_SECONDS:
                buftime = f" {month_day}Time"
                unit = "mm:ss"
                space = "    "
            case Formatter.FORMAT_HOURS_MINUTES_SECONDS:
                buftime = f" {month_day}Time"
                unit = "hh:mm:ss"
                space = " "
            case Formatter.FORMAT_HOURS_MINUTES_SECONDS_START:
                buftime = f"{month_day}Start      {month_day}End"
                unit = "hh:mm:ss"
                space = " "
            case _:
                raise curses.error("format error key {self.current_format}")
        return f"  #    {buftime} {space}lap({unit}){space}total({unit})"


class Display:
    """Class to handle the display of the stopwatch data"""

    def __init__(self, screen: curses.window) -> None:
        """Create a StopwatchDisplay object to write with"""
        self.screen = screen
        self.clear_buffer = False
        self.formatter = Formatter()
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
        self.num_rows, self.num_cols = self.screen.getmaxyx()
        self.num_header_rows = len(self.header_rows)
        self.num_buffer_rows = self.num_rows - self.num_header_rows

    def blank_line(self) -> str:
        """Make a blank line"""
        return " " * (self.num_cols - 1)

    def exit_msg(self, timestamps) -> str | None:
        """Generate an exit message"""
        if self.verbose:
            header = self.formatter.buffer_key
            rows = self.get_rows(timestamps)
            msg = header + "\n" + "\n".join(rows)
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
            self.formatter.buffer_key,
        ]

    def write_header(self) -> None:
        """Write the header (above the display buffer)"""
        for i, header_row in enumerate(self.header_rows):
            self.screen.addstr(i, 0, self.blank_line())  # clear line
            self.screen.addstr(i, 0, header_row)

    def get_rows(self, timestamps: list[datetime]) -> str | list[str]:
        """Get the rows to display and return them as strings"""

        def _row_text(current: datetime, previous: datetime, lap_num: int) -> str:
            td_total = current - timestamps[0]
            lap_duration = self.formatter.row_time(current - previous)
            total_duration = self.formatter.row_time(td_total, offset=2)

            fmt = "%d-%b %H:%M:%S" if self.formatter.month_day else "%H:%M:%S"
            time_str = current.strftime(fmt)
            if self.formatter.is_long_format:
                time_str = previous.strftime(fmt) + " " + time_str

            return f"{lap_num:3} {time_str} {lap_duration} {total_duration}"

        # Make a COPY of timstamps appended with "now" to generate the lap rows.
        timestamps = timestamps + [datetime.now()]
        self.formatter.month_day = timestamps[-1].date() != timestamps[0].date()
        rows = [
            _row_text(timestamp, previous, i + 1)
            for i, (previous, timestamp) in enumerate(pairwise(timestamps))
        ]

        return rows

    def write_buffer(self, timestamps: list[datetime]) -> None:
        """Write the lap info for each lap into the display buffer"""

        rows = self.get_rows(timestamps)

        if self.clear_buffer:
            curses.resizeterm(*self.screen.getmaxyx())
            self.screen.clear()
            self.screen.refresh()
            self.write_header()
            # TODO: replace the above redraw with this: (for all the rows)?
            #for all buffer rows:
            #    self._clear_row(row_num)

        # Write visible lines (the last num_buffer_rows timestamps) to buffer.
        # If the buffer has rotated, clear_buffer will be true, so erase each
        # line first, and erase the rest of the buffer if applicable.
        istop = len(timestamps)
        istart = max(istop - self.num_buffer_rows, 0)
        for i in range(istart, istop):
            row_num = i - istart
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
        self._write_buffer_row(lap_num, self.blank_line())

    def check_clear(self, num_rows: int = 9999):
        """
        Set the toggle to clear the buffer if there are too many rows to
        display, or if called without args.
        """
        self.clear_buffer = num_rows > self.num_buffer_rows
        # TODO: check if width of text in new format is too large (start-stop
        # to other format) so the text on the right isn't left hanging


class Stopwatch:
    """Class to emulate a stopwatch"""

    def __init__(self, screen: curses.window) -> None:
        """Create a Stopwatch object"""
        try:
            self.display = Display(screen)
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
            KEY_NO_INPUT: self._no_input,
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
        self.display.check_clear()


    def _toggle_verbose(self):
        self.display.verbose = not self.display.verbose
        self.display.write_header()

    def _change_format(self, direction: str = "next"):
        if direction == "next":
            self.display.formatter.next()
        else:
            self.display.formatter.prev()
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
                if curses.is_term_resized(self.display.num_rows, self.display.num_cols):
                    self._resize()
            except curses.error:
                self.display.write_buffer(self.timestamps)
                time.sleep(0.1)


def main(screen: curses.window) -> None:
    """Main stopwatch function"""

    stopwatch = Stopwatch(screen)
    stopwatch.run()


if __name__ == "__main__":
    curses.wrapper(main)
