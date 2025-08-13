"""Simple stopwatch tool"""

import curses
from curses import A_BOLD, A_NORMAL
from datetime import datetime, timedelta
import sys


class StopwatchDisplay:
    """Class to handle the display of the stopwatch data"""

    def __init__(self, screen: curses.window) -> None:
        """Create a StopwatchDisplay object to write with"""
        self.screen = screen
        self.clear_buffer = False
        self.format_seconds = True
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
        self.blank_line = " " * (self.num_cols - 1)

    def exit_msg(self, timestamps):
        """Generate an exit message"""
        if self.verbose:
            header = self.buffer_key
            buffer = self.get_rows(timestamps, as_string=True)
            msg = f"{header}\n{buffer}"
        else:
            msg = None
        return msg

    @property
    def buffer_key(self) -> str:
        """Make the key for the buffer"""
        return "Time       #" + (
            "    lap(s)     total(s)"
            if self.format_seconds
            else "  lap(mm:ss) total(mm:ss)"
        )

    @property
    def header_rows(self) -> list[str]:
        """Generate header text rows"""
        return [
            "Stopwatch:" + (" (verbose mode)" if self.verbose else ""),
            "q to quit, space/j/n/m to mark a lap, u/k/p to undo a mark, ",
            "slash/y to toggle time format (seconds or minutes:seconds)",
            "v to toggle verbosity (screen dump vs silent quit)",
            "",
            self.buffer_key,
        ]

    def write_header(self) -> None:
        """Write the header (above the display buffer)"""
        for i, header_row in enumerate(self.header_rows):
            self.screen.addstr(i, 0, self.blank_line)  # clear line
            self.screen.addstr(i, 0, header_row)

    def get_rows(
        self, timestamps: list[datetime], as_string: bool = False
    ) -> list[str]:
        """Get the rows to print"""

        def _td_to_mm_ss(td: timedelta) -> str:
            """Convert timedelta to "mm:ss" """
            mm = int(td.total_seconds()) // 60
            ss = int(td.total_seconds()) % 60
            return f"{mm:02}:{ss:02}"

        def _row_text(time: datetime, previous: datetime, lap_num: int) -> str:
            time_str = f"{time.strftime('%H:%M:%S')}"
            start_time = timestamps[0]
            prev_td = time - previous
            start_td = time - start_time
            if self.format_seconds:
                prev_str = f"{prev_td.total_seconds():8.1f}"
                start_str = f"{start_td.total_seconds():8.1f}"
            else:
                prev_str = f"    {_td_to_mm_ss(prev_td)}   "
                start_str = f"{_td_to_mm_ss(start_td)}"

            return f"{time_str} {lap_num:3}  {prev_str}     {start_str}"

        rows = []

        # Recorded timestamps -> static updates. Skip first timestamp because
        # that's the zero point. Enumerated 'i' is zero-based, so timestamps[i]
        # is the previous timestamp to 'timestamp'.
        for i, timestamp in enumerate(timestamps[1:]):
            previous = timestamps[i]
            rows.append(_row_text(timestamp, previous, i + 1))

        # The bottom row is updated-live (so "time" is now and previous is the
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
        self.screen.addstr(row, 0, text, fmt)

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
        self.display = StopwatchDisplay(screen)
        self.timestamps = [datetime.now()]

        self.keystroke_actions = {
            **dict.fromkeys(" jnm", self.add_timestamp),  # add a lap
            **dict.fromkeys("ukp", self.remove_timestamp),  # remove a lap
            **dict.fromkeys("/y", self._toggle_format),  # toggle display format
            "v": self._toggle_verbose,  # toggle verbosity
            "q": self._quit,  # quit
            "key_resize": self._resize,  # handle a resize event
        }
        print(self.keystroke_actions)

    def _quit(self):
        msg = self.display.exit_msg(self.timestamps)
        sys.exit(msg)

    def _resize(self):
        self.display.set_screen_size()

    def _toggle_verbose(self):
        self.display.verbose = not self.display.verbose
        self.display.write_header()

    def _toggle_format(self):
        self.display.format_seconds = not self.display.format_seconds
        self.display.check_clear()
        self.display.write_header()

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
                key = self.display.screen.getkey().lower()
                if action := self.keystroke_actions.get(key):
                    action()
            except curses.error:
                self.display.write_buffer(self.timestamps)


def main(screen: curses.window) -> None:
    """Main stopwatch function"""
    stopwatch = Stopwatch(screen)
    stopwatch.run()


if __name__ == "__main__":
    curses.wrapper(main)
