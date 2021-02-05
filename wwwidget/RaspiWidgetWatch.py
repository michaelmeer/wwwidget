#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Dimensions for 720x720 Hyperpixel Display with Terminus Font
12 Px height: 45 row x 90 columns 
10 Px height: 51 rows x 90 columns

Needs the package GPM installed on Linux to have mouse support
"""

import argparse
import configparser
import curses
import logging.config
import multiprocessing
import signal
import sys

import multiprocessing_logging
from widgetworkers import WidgetWorker

# create logger
logger = logging.getLogger(__name__)


def signal_handler(sig, frame):
    curses.endwin()
    print('You pressed Ctrl+C!')
    sys.exit(0)


class RaspiWidgetWatchController(object):
    def __init__(self, config, screen):
        self.config = config
        jobs = []
        self.widget_workers = {}
        output_queue = multiprocessing.JoinableQueue()

        screen.nodelay(True)
        curses.mousemask(curses.ALL_MOUSE_EVENTS)
        curses.curs_set(0)  # Turn off the cursor
        curses.start_color()
        curses.use_default_colors()

        for i in range(0, curses.COLORS):
            curses.init_pair(i, i, -1)

        curses.init_pair(8, curses.COLOR_BLUE, curses.COLOR_RED)
        curses.init_pair(9, curses.COLOR_RED, curses.COLOR_BLUE)

        rows, cols = screen.getmaxyx()
        logger.info("Rows: {}, Cols: {}".format(rows, cols))
        logger.info("Can change color? {}".format(curses.can_change_color()))
        logger.info("COLORS {}, COLOR_PAIRS {}".format(curses.COLORS, curses.COLOR_PAIRS))

        for section in self.config.sections():
            if WidgetWorker.is_config_section_valid_widget_worker(self.config[section]):
                widget_worker = WidgetWorker.instantiate_widget_from_configsection(self.config[section], output_queue)
                self.widget_workers[widget_worker.name] = widget_worker.get_windows()
                if widget_worker:
                    jobs.append(widget_worker)
                    widget_worker.start()

        logger.info("Starting the loop now...")

        while True:
            event = screen.getch()
            if event == ord("q"):
                logger.info("q pressed!")
                break
            if event == curses.KEY_MOUSE:
                id, x, y, z, bstate = curses.getmouse()
                logger.info("mouse event: id {}, x {}, y {}, z {}, bstate {}".format(id, x, y, z, bstate))

                for widget_name, windows in self.widget_workers.items():
                    logger.info("{}: {}".format(widget_name, windows[0].enclose(y, x)))


            if not output_queue.empty():
                widget_name, widget_label, widget_output = output_queue.get_nowait()

                border_win, win = self.widget_workers[widget_name]
                win.clear()

                border_win.border()
                border_win.addstr(0, 2, widget_label)
                border_win.refresh()

                logger.debug("Received output from {}, {} lines".format(widget_name, len(widget_output)))
                logger.debug(widget_output)

                # for y, line in enumerate(widget_output):
                for y, output in enumerate(widget_output):
                    try:
                        action = output[0]
                        parameters = output[1:]
                        if action == 'addstr':
                            #widget.win.addstr(*parameters)
                            win.addstr(*parameters)
                        elif action == 'bkgd':
                            #widget.win.bkgd(*parameters)
                            win.bkgd(*parameters)
                        # widget.win.addstr(y,0,str(output)[:75])
                        # win.addstr(y,2,line,curses.color_pair(9))
                    except Exception as e:
                        # logger.warning("Error from widget {} printing line (length {}): {}".format(widget_name, len(line), line))
                        logger.warning(e)

                # widget.win.refresh()
                win.refresh()



        logger.info("Ende der Fahnenstange!")
        curses.endwin()



def main(screen):
    signal.signal(signal.SIGINT, signal_handler)

    parser = argparse.ArgumentParser(description='Run a collection of informational and silly widgets in the terminal')
    parser.add_argument('configfile', help='Mandatory Configfile')
    args = parser.parse_args()

    #logging.config.fileConfig(args.configfile)

    logging.basicConfig(filename='example.log',
                        filemode='w',
                        level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p')

    multiprocessing_logging.install_mp_handler()

    logger = logging.getLogger(__name__)
    logger.info("Starting now...")

    config = configparser.ConfigParser()
    config.read(args.configfile)
    logger.info("Color Pair 0: " + str(curses.color_pair(0)))
    logger.info("Color Pair 1: " + str(curses.color_pair(1)))
    logger.info("Color Pair 2: " + str(curses.color_pair(2)))
    controller = RaspiWidgetWatchController(config, screen)


if __name__ == '__main__':
    try:
        curses.wrapper(main)
    except Exception:
        logger.error("Fatal error in main loop", exc_info=True)
