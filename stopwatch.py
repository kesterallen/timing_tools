""" Simple curses-based stopwatch tool """

import curses
from curses import A_BOLD, A_NORMAL
from datetime import datetime
import sys

COL = 0
HEADER = ["Stopwatch: q to quit, space to mark a lap", "", "Time       lap (#)   total"]
HEADER_ROWS = len(HEADER)


def tds(td):
    """The number of seconds in the time delta in %.1f precision"""
    return f"{td.total_seconds():.1f}"


def hms(dt):
    """Hours:Minutes:Seconds string for a datetime"""
    return dt.strftime("%H:%M:%S")


def fmt(is_bold):
    """Curses formatting attribute"""
    return A_BOLD if is_bold else A_NORMAL


def main(screen):
    """Main stopwatch function"""

    buffer_rows = screen.getmaxyx()[0] - HEADER_ROWS
    curses.noecho()  # Disable echoing of input
    curses.cbreak()  # React to keys instantly
    screen.nodelay(True)  # Set non-blocking mode

    start = datetime.now()
    #TODO: array of marks instead of mark to support undo
    mark = start

    lap_num = 0

    is_bold = False

    # Header
    for irow, line in enumerate(HEADER):
        screen.addstr(irow, COL, line)

    # Timer loop
    while True:
        try:
            key = screen.getkey()  # Non-blocking getkey()
            if key == "q":
                sys.exit(0)
            if key == " ":  # mark a lap and move to the next row
                lap_num += 1
                mark = datetime.now()
        except curses.error:
            # No key was pressed, print the time
            now = datetime.now()
            since_mark = now - mark
            since_start = now - start

            # Toggle bold text when the display wraps to the top:
            if lap_num % buffer_rows == 0:
                is_bold = lap_num // buffer_rows % 2 != 0

            line = f"{hms(now)}   {tds(since_mark)} (#{lap_num+1})   {tds(since_start)}"
            row = HEADER_ROWS + lap_num % buffer_rows
            screen.addstr(row, COL, line, fmt(is_bold))


if __name__ == "__main__":
    curses.wrapper(main)
