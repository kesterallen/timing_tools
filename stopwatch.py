"""Simple stopwatch tool"""

import curses
from curses import A_BOLD, A_NORMAL
import datetime as dt
import sys

MARK_KEYS = [" ", "j", "n", "m"]
DROP_KEYS = ["u", "k", "p"]

HEADER = [
    "Stopwatch: q to quit, space/j/n/m to mark a lap, u/k/p to undo a mark",
    "",
    "Time       lap(s) (#)   total(s)",
    # "HH:MM:SS   #.#    (#)   #.#"
]


class StopwatchDisplay:
    """Class to handle the display of the stopwatch data"""

    def __init__(self, screen: curses.window):
        """Create a StopwatchDisplay object to write with"""
        self.screen = screen
        self.num_header_rows = len(HEADER)
        self.set_screen_size()

        self.init_curses()
        self.write_header()

        self.blank_line = " " * (self.num_cols // 2)

    def init_curses(self):
        """Set curses settings"""
        curses.noecho()
        curses.cbreak()
        self.screen.nodelay(True)

    def set_screen_size(self):
        screenrows, screencols = self.screen.getmaxyx()
        self.num_rows = screenrows
        self.num_buffer_rows = self.num_rows - self.num_header_rows
        self.num_cols = screencols

    def write_header(self):
        """Write the header (above the display buffer)"""
        for i, header_row in enumerate(HEADER):
            self.screen.addstr(i, 0, header_row)

    def get_rows(self, timestamps: list[dt.datetime]) -> list[str]:
        def _row_text(time: dt.datetime, previous: dt.datetime, lap_num: int):
            start_time = timestamps[0]
            return (
                f"{time.strftime('%H:%M:%S')}   "
                f"{(time - previous).total_seconds():.1f}    "
                f"({lap_num})   "
                f"{(time - start_time).total_seconds():.1f}"
            )

        rows = []

        # Recorded timestamps -> static updates. Skip first timestamp because
        # that's the zero point. Enumerated 'i' is zero-based, so timestamps[i]
        # is the previous timestamp to 'timestamp'.
        for i, timestamp in enumerate(timestamps[1:]):
            previous = timestamps[i]
            rows.append(_row_text(timestamp, previous, i + 1))

        # The bottom row is updated-live (so "time" is now and previous is the
        # last timestamp).
        time = dt.datetime.now()
        previous = timestamps[-1]
        rows.append(_row_text(time, previous, len(timestamps)))

        return rows

    def write_buffer(self, timestamps: list[dt.datetime], clear_buffer: bool = False):
        """Write the lap info for each lap into the display buffer"""

        rows = self.get_rows(timestamps)

        # Write visible lines (the last num_buffer_rows timestamps) to buffer.
        # If the buffer has rotated, clear_buffer will be true, so erase each
        # line first, and erase the rest of the buffer if applicable.
        istop = len(timestamps)
        istart = max(istop - self.num_buffer_rows, 0)
        for i in range(istart, istop):
            text_fmt = A_BOLD if i == istop - 1 else A_NORMAL
            if clear_buffer:
                self.clear_row(i - istart)
            self.write_buffer_row(i - istart, rows[i], text_fmt)

        for i in range(istop, self.num_buffer_rows):
            if clear_buffer:
                self.clear_row(i - istart)

    def write_buffer_row(self, lap_num: int, text: str, text_fmt: int = A_NORMAL):
        """Write formatted text to a line in the display buffer"""
        row = self.num_header_rows + (lap_num % self.num_buffer_rows)
        self.screen.addstr(row, 0, text, text_fmt)

    def clear_row(self, lap_num: int):
        """Erase one row"""
        self.write_buffer_row(lap_num, self.blank_line)


class Stopwatch:
    """Class to emulate a stopwatch"""

    def __init__(self, screen: curses.window):
        """Create a Stopwatch object"""
        self.display = StopwatchDisplay(screen)
        self.timestamps = [dt.datetime.now()]
        self.clear_buffer = False

    def run(self):
        """Run the stopwatch"""
        while True:
            try:
                key = self.display.screen.getkey()
                if key == "q":
                    sys.exit(0)
                elif key == curses.KEY_RESIZE:
                    self.display.set_screen_size()
                elif key in MARK_KEYS:
                    self.add_timestamp()
                elif key in DROP_KEYS:
                    self.remove_timestamp()
                    self.clear_buffer = True
            except curses.error:
                self.display.write_buffer(self.timestamps, self.clear_buffer)
                if self.clear_buffer:
                    self.clear_buffer = False

    def add_timestamp(self):
        """Add a new timestamp/lap"""
        self.timestamps.append(dt.datetime.now())
        self.clear_buffer = len(self.timestamps) > self.display.num_buffer_rows

    def remove_timestamp(self):
        """Remove the most recent timestamp; undo last mark"""
        if len(self.timestamps) > 1:
            self.timestamps.pop()


def main(screen: curses.window):
    """Main stopwatch function"""
    stopwatch = Stopwatch(screen)
    stopwatch.run()


if __name__ == "__main__":
    curses.wrapper(main)
