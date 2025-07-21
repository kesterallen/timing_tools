"""Simple stopwatch tool"""

import curses
import datetime as dt
import sys

HEADER = [
    "Stopwatch: q to quit, space to mark a lap, u to undo a mark",
    "",
    "Time       lap (#)   total",
]
BLANK_LINE = " " * 42


class StopwatchDisplay:
    def __init__(self, screen):
        self.screen = screen
        self.col = 0
        self.header_rows = len(HEADER)
        self.buffer_rows = self.screen.getmaxyx()[0] - self.header_rows

        self.init_curses()
        self.draw_header()

    def init_curses(self):
        curses.noecho()
        curses.cbreak()
        self.screen.nodelay(True)

    def draw_header(self):
        for i, line in enumerate(HEADER):
            self.screen.addstr(i, self.col, line)

    def write_line(self, line, lap_num):
        row = self.header_rows + (lap_num % self.buffer_rows)
        self.screen.addstr(row, self.col, line)

    def clear_row(self, lap_num):
        self.write_line(BLANK_LINE, lap_num)


class Stopwatch:
    def __init__(self, screen):
        self.display = StopwatchDisplay(screen)
        self.start_time = dt.datetime.now()
        self.marks = [self.start_time]
        self.lap_num = 0

    def run(self):
        while True:
            try:
                key = self.display.screen.getkey()
                if key == "q":
                    sys.exit(0)
                elif key == " ":
                    self.add_mark()
                elif key == "u":
                    self.undo()
            except curses.error:
                self.update_display()

    def add_mark(self):
        self.lap_num += 1
        self.marks.append(dt.datetime.now())

    def undo(self):
        if len(self.marks) < 2:
            return

        # TODO if undo wraps over the top of the screen, redraw a screen's worth of marks
        # TODO or just always display the last N marks
        self.display.clear_row(self.lap_num)
        self.lap_num -= 1
        self.marks.pop()

    def update_display(self):
        now = dt.datetime.now()
        since_last = now - self.marks[-1]
        since_start = now - self.start_time

        line = (
            f"{now.strftime('%H:%M:%S')}   "
            f"{since_last.total_seconds():.1f} "
            f"(#{self.lap_num+1})   "
            f"{since_start.total_seconds():.1f}"
        )
        self.display.write_line(line, self.lap_num)


def main(screen):
    stopwatch = Stopwatch(screen)
    stopwatch.run()


if __name__ == "__main__":
    curses.wrapper(main)
