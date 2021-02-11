# -*- coding: utf-8 -*-
import multiprocessing
import logging
import curses
import pytz
import datetime
import pyfiglet
import feedparser
import time
import calendar
from . import curses_constants

from . import fortune_cookie_loader

logger = logging.getLogger(__name__)


def is_config_section_valid_widget_worker(config_section):
    subclasses_dict = {subclass.__name__: subclass for subclass in WidgetWorker.get_all_subclasses()}
    subclass_names = subclasses_dict.keys()
    return any(config_section.name.startswith(subclass_name) for subclass_name in subclass_names)


def instantiate_widget_from_configsection(config_section, output_queue):
    logger.info("Initializing widget based on config section {}...".format(config_section.name))
    subclasses_dict = {subclass.__name__: subclass for subclass in WidgetWorker.get_all_subclasses()}
    subclass_names = subclasses_dict.keys()
    matching_subclass_name = next(
        (subclass_name for subclass_name in subclass_names if config_section.name.startswith(subclass_name)), None)
    matching_subclass = subclasses_dict[matching_subclass_name]
    logger.info("Found matching widget class {}...".format(matching_subclass))
    if matching_subclass:
        try:
            widget_instance = matching_subclass.InstanceFromConfigSection(config_section, output_queue)
        except Exception as e:
            logger.error("Instantation of config_section {} failed, error message:".format(config_section))
            logger.error(e)
            return None
        return widget_instance
    else:
        return None


class WidgetWorker(multiprocessing.Process):
    def __init__(self, output_queue, x, y, width, height):
        multiprocessing.Process.__init__(self)
        self.output_queue = output_queue
        self.width = width
        self.height = height
        self.x = x
        self.y = y

    def get_windows(self):
        border_win = curses.newwin(self.height, self.width, self.y, self.x)
        win = border_win.derwin(self.height - 2, self.width - 2, 1, 1)
        return border_win, win

    def send_output_to_queue(self, output):
        self.output_queue.put((self.name, self.label, output))

    def send_input(self, input):
        pass

    @classmethod
    def get_all_subclasses(cls):
        all_subclasses = []

        for subclass in cls.__subclasses__():
            all_subclasses.append(subclass)
            all_subclasses.extend(subclass.get_all_subclasses())

        return all_subclasses

    def get_label(self):
        return self.name

    def interior_space(self):
        return self.width - 2, self.height - 2


class FortuneWorker(WidgetWorker):

    def __init__(self, output_queue, x, y, width, height, fortune_file, label="Bern"):
        WidgetWorker.__init__(self, output_queue, x, y, width, height)
        self.output_queue = output_queue
        self.fortune_file = fortune_file
        self.label = label
        self.input_queue = multiprocessing.JoinableQueue()

    @classmethod
    def InstanceFromConfigSection(cls, configsection, output_queue):
        instance = cls(
            output_queue=output_queue,
            x=configsection.getint("x"),
            y=configsection.getint("y"),
            width=configsection.getint("width"),
            height=configsection.getint("height"),
            fortune_file=configsection.get("fortune_file"),
            label=configsection.get("label"),
        )
        return instance

    def run(self):
        max_width, max_height = self.interior_space()
        f = fortune_cookie_loader.fortune_cookie_loader(self.fortune_file, max_width=max_width, max_height=max_height)
        self.send_new_cookie(f)
        while True:
            event = self.input_queue.get()
            self.send_new_cookie(f)

    def send_input(self, input):
        self.input_queue.put(input)

    def send_new_cookie(self, f):
        cookie = f.return_fortune_cookie()
        logger.info(cookie)
        output = []
        regular_text = True
        for y, line in enumerate(cookie):
            output_line = ["addstr", y, 0, line]
            if line.startswith("--"):
                regular_text = False

            if not regular_text:
                output_line.append(curses_constants.A_DIM)

            output.append(output_line)
        logger.info(output)
        self.send_output_to_queue(output)

    def get_label(self):
        return self.label



class FeedReaderWorker(WidgetWorker):
    # http://rss.cnn.com/rss/cnn_topstories.rss

    def __init__(self, output_queue, x, y, width, height, feed_url, refresh_interval_mins = 10, label = "RSS Feed"):
        WidgetWorker.__init__(self, output_queue, x, y, width, height)
        self.feed_url = feed_url
        self.refresh_interval_mins = refresh_interval_mins
        self.label = label

    @classmethod
    def InstanceFromConfigSection(cls, configsection, output_queue):
        instance = cls(
            output_queue=output_queue,
            x=configsection.getint("x"),
            y=configsection.getint("y"),
            width=configsection.getint("width"),
            height=configsection.getint("height"),
            feed_url=configsection.get("feed_url"),
            refresh_interval_mins=configsection.getint("refresh_interval_mins"),
            label=configsection.get("label"),
        )
        return instance

    def _prep_entry_summary(self, entry):
        if hasattr(entry, "published_parsed"):
            utc_tuple = entry.published_parsed
            posix_timestamp = calendar.timegm(utc_tuple)
            from tzlocal import get_localzone
            local_timezone = get_localzone()
            local_time = datetime.datetime.fromtimestamp(posix_timestamp, local_timezone)
            local_time.strftime("%m/%d/%Y, %H:%M:%S")
            summary = "{}: {}".format(local_time.strftime("%Y-%m-%d %H:%M"), entry["title"])
        else:
            summary = "No Time: {}".format(entry["title"])
        return summary

    def run(self):
        while True:
            feed = feedparser.parse(self.feed_url)
            feed_entries_without_pubdate = [entry for entry in feed["entries"] if hasattr(entry,"published_parsed")]
            feed_entries_without_pubdate.sort(key=lambda x: x.published_parsed, reverse=True)

            entries = []
            for entry in feed_entries_without_pubdate[:self.y - 2]:
                if hasattr(entry, "published_parsed"):
                    entries.append(self._prep_entry_summary(entry))

            output = []

            for y, line in enumerate(entries):
                output_line = ["addstr", y, 0, line]
                if y%2:
                    #output_line.append(curses.color_pair(9))
                    output_line.append(curses_constants.A_REVERSE)
                else:
                    #output_line.append(curses.color_pair(8))
                    output_line.append(curses_constants.A_BOLD)
                output.append(output_line)

            self.send_output_to_queue(output)

            time.sleep(self.refresh_interval_mins * 60)

"""
class QuoteWorker(WidgetWorker):

    def __init__(self, output_queue, x, y, width, height):
        WidgetWorker.__init__(self, output_queue, x, y, width, height)
        self.output_queue = output_queue

    @classmethod
    def InstanceFromConfigSection(cls, configsection, output_queue):
        instance = cls(
            output_queue=output_queue,
            x=configsection.getint("x"),
            y=configsection.getint("y"),
            width=configsection.getint("width"),
            height=configsection.getint("height"),
        )
        return instance

    def load_fitting_fortune_cookies(self):
        available_width, available_height = self.interior_space()
        fitting_fortune_cookies = []

    def run(self):
        output_lines = []
        output_lines.extend(["Zack " * 15])
        self.send_output_to_queue(output_lines)
        return


class BoxWorker(WidgetWorker):

    def __init__(self, output_queue, x, y, width, height, tl, t, tr, r, br, b, bl, l):
        WidgetWorker.__init__(self, output_queue, x, y, width, height)
        self.tl = tl
        self.t = t
        self.tr = tr
        self.r = r
        self.br = br
        self.b = b
        self.bl = bl
        self.l = l

    @classmethod
    def InstanceFromConfigSection(cls, configsection, output_queue):
        instance = cls(
            output_queue=output_queue,
            x=configsection.getint("x"),
            y=configsection.getint("y"),
            width=configsection.getint("width"),
            height=configsection.getint("height"),
            tl=configsection.get("tl"),
            t=configsection.get("t"),
            tr=configsection.get("tr"),
            r=configsection.get("r"),
            br=configsection.get("br"),
            b=configsection.get("b"),
            bl=configsection.get("bl"),
            l=configsection.get("l"),
        )
        return instance

    def run(self):
        output = ["BOX!"]
        output.append("{}{}{}".format(self.tl, self.t * 5, self.tr))
        for n in range(3): output.append("{}{}{}".format(self.l, " " * 5, self.r))
        output.append("{}{}{}".format(self.bl, self.b * 5, self.br))
        self.send_output_to_queue(output)
        return


class CounterWorker(WidgetWorker):

    def __init__(self, output_queue, x, y, width, height):
        WidgetWorker.__init__(self, output_queue, x, y, width, height)
        self.counter = 0
        self.sleep_time = 0.1

    def run(self):
        while True:
            self.counter += 1
            output_lines = ["Counter", "{}".format(self.counter)]
            self.send_output_to_queue(output_lines)

            time.sleep(self.sleep_time)

"""

class WorldClockWorker(WidgetWorker):
    def __init__(self, output_queue, x, y, width, height, destination_timezone='Europe/Zurich', label="Bern",
                 sleep_time=1.0, time_format='%H:%M:%S', font='nancyj'):
        WidgetWorker.__init__(self, output_queue, x, y, width, height)
        self.label = label
        self.local_timezone = pytz.timezone('US/Central')
        self.destination_timezone = pytz.timezone(destination_timezone)
        self.sleep_time = sleep_time
        self.time_format = time_format
        self.font = font

    @classmethod
    def InstanceFromConfigSection(cls, configsection, output_queue):
        instance = cls(
            output_queue=output_queue,
            x=configsection.getint("x"),
            y=configsection.getint("y"),
            width=configsection.getint("width"),
            height=configsection.getint("height"),
            destination_timezone=configsection.get("destination_timezone"),
            label=configsection.get("label"),
            sleep_time=configsection.getint("sleep_time", 1),
            time_format=configsection.get("time_format", '%H:%M:%S', raw=True),
            font=configsection.get("font", "nancyj")
        )
        return instance

    def generate_figlet_output(self, string_to_output):
        output_lines = pyfiglet.figlet_format(string_to_output, font=self.font, width=self.width - 2).split('\n')
        return [output_line for output_line in output_lines if output_line.strip()]

    def get_label(self):
        return self.label

    def run(self):
        try:
            while True:
                now = datetime.datetime.now()
                local_time = self.local_timezone.localize(now)
                destination_time = local_time.astimezone(self.destination_timezone)
                formatted_destination_time = destination_time.strftime(self.time_format)
                figlet_lines = self.generate_figlet_output(formatted_destination_time)
                output_lines = []

                for y, line in enumerate(figlet_lines):
                    output_line = ["addstr", y, 0, line]
                    # if line.startswith("--"):
                    #     output_line.append(curses.color_pair(9))
                    # else:
                    #     output_line.append(curses.color_pair(8))
                    output_lines.append(output_line)

                self.send_output_to_queue(output_lines)
                time.sleep(self.sleep_time)
        except Exception as e:
            logger.error(e)

