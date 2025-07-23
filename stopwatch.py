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
]


class StopwatchDisplay:
    """Class to handle the display of the stopwatch data"""

    def __init__(self, screen: curses.window):
        """Create a StopwatchDisplay object to write with"""
        self.screen = screen
        self.num_header_rows = len(HEADER)
        screenrows, screencols = self.screen.getmaxyx()
        self.num_buffer_rows = screenrows - self.num_header_rows
        self.num_cols = screencols

        self.init_curses()
        self.write_header()

    def init_curses(self):
        """Set curses settings"""
        curses.noecho()
        curses.cbreak()
        self.screen.nodelay(True)

    def write_header(self):
        """Write the header (above the display buffer)"""
        for i, header_row in enumerate(HEADER):
            self.screen.addstr(i, 0, header_row)

    def write_buffer(self, timestamps: list[dt.datetime]):
        """Write the lap info for each lap into the display buffer"""

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

        # TODO: update code so the whole screen isn't rewritten on every update
        # TODO: implement screen-resize capability

        for i in range(self.num_buffer_rows):
            self.clear_row(i)

        istop = len(timestamps)
        istart = max(istop - self.num_buffer_rows, 0)
        for i in range(istart, istop):
            text_fmt = A_BOLD if i == istop - 1 else A_NORMAL
            self.write_buffer_row(rows[i], i - istart, text_fmt)

    def write_buffer_row(self, text: str, lap_num: int, text_fmt: int = A_NORMAL):
        """Write formatted text to a line in the display buffer"""
        row = self.num_header_rows + (lap_num % self.num_buffer_rows)
        self.screen.addstr(row, 0, text, text_fmt)

    def clear_row(self, lap_num: int):
        """Erase one row"""
        self.write_buffer_row(" " * (self.num_cols // 2), lap_num)


class Stopwatch:
    """Class to emulate a stopwatch"""

    def __init__(self, screen: curses.window):
        """Create a Stopwatch object"""
        self.display = StopwatchDisplay(screen)
        self.timestamps = [dt.datetime.now()]

    def run(self):
        """Run the stopwatch"""
        while True:
            try:
                key = self.display.screen.getkey()
                if key == "q":
                    sys.exit(0)
                elif key in MARK_KEYS:
                    self.add_timestamp()
                elif key in DROP_KEYS:
                    self.remove_timestamp()
            except curses.error:
                self.display.write_buffer(self.timestamps)

    def add_timestamp(self):
        """Add a new timestamp/lap"""
        self.timestamps.append(dt.datetime.now())

    def remove_timestamp(self):
        """Remove the most recent timestamp; undo last mark"""
        if len(self.timestamps) < 2:
            return
        self.timestamps.pop()


def main(screen: curses.window):
    """Main stopwatch function"""
    stopwatch = Stopwatch(screen)
    stopwatch.run()


if __name__ == "__main__":
    curses.wrapper(main)
