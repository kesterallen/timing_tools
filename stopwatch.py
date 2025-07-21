""" Simple curses-based stopwatch tool """

import curses
from curses import A_BOLD, A_NORMAL
import datetime as dt
import sys

COL = 0
HEADER = ["Stopwatch: q to quit, space to mark a lap, u to undo a mark", "", "Time       lap (#)   total"]
HEADER_ROWS = len(HEADER)

BLANK_LINE = "                                          "
BUFFER_ROWS = 0

is_bold = False


def tds(td: dt.timedelta):
    """The number of seconds in the time delta in %.1f precision"""
    return f"{td.total_seconds():.1f}"


def hms(dt: dt.datetime):
    """Hours:Minutes:Seconds string for a datetime"""
    return dt.strftime("%H:%M:%S")


def fmt(is_bold: bool):
    """Curses formatting attribute"""
    return A_BOLD if is_bold else A_NORMAL

def write_row(line: str, lap_num: int, is_bold: bool, screen: curses.window) -> None:
    """Write 'line' to the current row on the screen"""
    row = HEADER_ROWS + lap_num % BUFFER_ROWS
    screen.addstr(row, COL, line, fmt(is_bold))

def init(screen):
    global BUFFER_ROWS
    BUFFER_ROWS = screen.getmaxyx()[0] - HEADER_ROWS

    curses.noecho()  # Disable echoing of input
    curses.cbreak()  # React to keys instantly
    screen.nodelay(True)  # Set non-blocking mode

def main(screen):
    """Main stopwatch function"""

    init(screen)
    start = dt.datetime.now()
    marks = [start]
    lap_num = 0

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
                marks.append(dt.datetime.now())
            if key == "u":  # undo last mark
                if len(marks) < 2:
                    continue
                write_row(BLANK_LINE, lap_num, is_bold, screen)
                lap_num -= 1
                marks.pop(-1)
        except curses.error:
            # No key was pressed, print the time
            now = dt.datetime.now()
            since_mark = now - marks[-1]
            since_start = now - start

            # Toggle bold text when the display wraps to the top:
            if lap_num % BUFFER_ROWS == 0:
                is_bold = lap_num // BUFFER_ROWS % 2 != 0

            line = f"{hms(now)}   {tds(since_mark)} (#{lap_num+1})   {tds(since_start)}"
            write_row(line, lap_num, is_bold, screen)


if __name__ == "__main__":
    curses.wrapper(main)
