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
    def __init__(self, screen):
        self.screen = screen
        self.num_header_rows = len(HEADER)
        self.num_buffer_rows = self.screen.getmaxyx()[0] - self.num_header_rows

        self.init_curses()
        self.draw_header()

    def init_curses(self):
        curses.noecho()
        curses.cbreak()
        self.screen.nodelay(True)

    def draw_header(self):
        for i, header_row in enumerate(HEADER):
            self.screen.addstr(i, 0, header_row)

    def write_buffer_row(self, buffer_row_text, lap_num, text_fmt=A_NORMAL):
        row = self.num_header_rows + (lap_num % self.num_buffer_rows)
        self.screen.addstr(row, 0, buffer_row_text, text_fmt)

    def clear_row(self, lap_num):
        self.write_buffer_row(BLANK_ROW, lap_num)


class Stopwatch:
    def __init__(self, screen):
        self.display = StopwatchDisplay(screen)
        self.start_time = dt.datetime.now()
        self.timestamps = [dt.datetime.now()]

    def run(self):
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
                self.write_buffer()

    def add_timestamp(self):
        self.timestamps.append(dt.datetime.now())

    def remove_timestamp(self):
        if len(self.timestamps) < 2:
            return
        self.timestamps.pop()

    def write_buffer(self):
        def _row_text(time, prev_time, lap_num):
            return (
                f"{time.strftime('%H:%M:%S')}   "
                f"{(time - prev_time).total_seconds():.1f}    "
                f"({lap_num})   "
                f"{(time - self.start_time).total_seconds():.1f}"
            )

        rows = []

        # Recorded timestamps -> static updates. Skip first timestamp because
        # that's the zero point.
        for i, time in enumerate(self.timestamps[1:]):
            prev_time = self.timestamps[i]
            rows.append(_row_text(time, prev_time, i+1))

        # The bottom row is updated-live (so "time" is now and prev_time is the
        # last timestamp).
        time = dt.datetime.now()
        prev_time = self.timestamps[-1]
        rows.append(_row_text(time, prev_time, len(self.timestamps)))

        # TODO remove?
        for i in range(self.display.num_buffer_rows):
            self.display.clear_row(i)

        istop = len(self.timestamps)
        istart = istop - self.display.num_buffer_rows
        if istart < 0:
            istart = 0
        for i in range(istart, istop):
            text_fmt = A_BOLD if i == istop - 1 else A_NORMAL
            self.display.write_buffer_row(rows[i], i - istart, text_fmt)


def main(screen):
    stopwatch = Stopwatch(screen)
    stopwatch.run()


if __name__ == "__main__":
    curses.wrapper(main)
