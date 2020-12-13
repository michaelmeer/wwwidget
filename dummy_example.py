#!/usr/bin/env python3
import curses 

def main(scr, *args):
    # -- Perform an action with Screen --
    scr.border(0)
    scr.addstr(5, 5, 'Hello World!', curses.A_BOLD)
    scr.addstr(6, 5, 'Press q to end', curses.A_NORMAL)

    while True:
        # stay in this loop till the user presses 'q'
        ch = scr.getch()
        if ch == ord('q'):
            break

curses.wrapper(main)
