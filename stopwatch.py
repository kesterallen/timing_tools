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
BLANK_ROW = " " * 42


class StopwatchDisplay:
    """Class to handle the display of the stopwatch data"""

    def __init__(self, screen):
        """Create a StopwatchDisplay object to write with"""
        self.screen = screen
        self.num_header_rows = len(HEADER)
        self.num_buffer_rows = self.screen.getmaxyx()[0] - self.num_header_rows

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

    def write_buffer(self, timestamps, start_time):
        """Write the lap info for each lap into the display buffer"""

        def _row_text(time, prev_time, lap_num):
            return (
                f"{time.strftime('%H:%M:%S')}   "
                f"{(time - prev_time).total_seconds():.1f}    "
                f"({lap_num})   "
                f"{(time - start_time).total_seconds():.1f}"
            )

        rows = []

        # Recorded timestamps -> static updates. Skip first timestamp because
        # that's the zero point.
        for i, time in enumerate(timestamps[1:]):
            prev_time = timestamps[i]
            rows.append(_row_text(time, prev_time, i + 1))

        # The bottom row is updated-live (so "time" is now and prev_time is the
        # last timestamp).
        time = dt.datetime.now()
        prev_time = timestamps[-1]
        rows.append(_row_text(time, prev_time, len(timestamps)))

        for i in range(self.num_buffer_rows):
            self.clear_row(i)

        istop = len(timestamps)
        istart = max(istop - self.num_buffer_rows, 0)
        for i in range(istart, istop):
            text_fmt = A_BOLD if i == istop - 1 else A_NORMAL
            self.write_buffer_row(rows[i], i - istart, text_fmt)

    def write_buffer_row(self, buffer_row_text, lap_num, text_fmt=A_NORMAL):
        """Write formatted text to a line in the display buffer"""
        row = self.num_header_rows + (lap_num % self.num_buffer_rows)
        self.screen.addstr(row, 0, buffer_row_text, text_fmt)

    def clear_row(self, lap_num):
        """Erase one row"""
        self.write_buffer_row(BLANK_ROW, lap_num)


class Stopwatch:
    """Class to emulate a stopwatch"""

    def __init__(self, screen):
        """Create a Stopwatch object"""
        self.display = StopwatchDisplay(screen)
        self.start_time = dt.datetime.now()
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
                self.display.write_buffer(self.timestamps, self.start_time)

    def add_timestamp(self):
        """Add a new timestamp/lap"""
        self.timestamps.append(dt.datetime.now())

    def remove_timestamp(self):
        """Remove the most recent timestamp; undo last mark"""
        if len(self.timestamps) < 2:
            return
        self.timestamps.pop()


def main(screen):
    """Main stopwatch function"""
    stopwatch = Stopwatch(screen)
    stopwatch.run()


if __name__ == "__main__":
    curses.wrapper(main)
