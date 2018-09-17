import keypirinha as kp
import keypirinha_util as kpu
import datetime
import locale
import contextlib
import sys
import os
import re

# insert lib directory to path to import modules normally
lib = os.path.join(os.path.dirname(__file__), "lib")
if lib not in sys.path:
    sys.path.append(lib)
import dateutil.parser


class Time(kp.Plugin):
    DEFAULT_FORMATS = [
        "%c",
        "%x",
    ]
    DEFAULT_LOCALES = [
        "",
        "C",
    ]
    DEFAULT_ITEM_LABEL = "Time:"
    COPY_TO_CB = "(press Enter to copy to clipboard)"

    def __init__(self):
        super().__init__()
        self._formats = self.DEFAULT_FORMATS
        self._locales = self.DEFAULT_LOCALES
        self._item_label = self.DEFAULT_ITEM_LABEL
        # self._debug = True

    def on_start(self):
        self._read_config()
        self.set_default_icon(self.load_icon("res://{}/clock.ico".format(self.package_full_name())))

    def on_events(self, flags):
        """Reloads the package config when its changed
        """
        if flags & kp.Events.PACKCONFIG:
            self._read_config()

    def _read_config(self):
        """Reads the config
        """
        self.dbg("Reading config")
        settings = self.load_settings()

        self._formats = settings.get_multiline("formats", "main", self.DEFAULT_FORMATS)
        self.dbg("Formats =", self._formats)

        self._locales = settings.get_multiline("locales", "main", self.DEFAULT_LOCALES, True)
        self.dbg("Locales =", self._locales)

        self._item_label = settings.get("item_label", "main", self.DEFAULT_ITEM_LABEL)
        self.dbg("item_label =", self._item_label)

    def on_catalog(self):
        """Adds the kill command to the catalog
        """
        catalog = [
            self.create_item(
                category=kp.ItemCategory.KEYWORD,
                label=self._item_label,
                short_desc="Date and time parsing and formatting",
                target="time",
                args_hint=kp.ItemArgsHint.REQUIRED,
                hit_hint=kp.ItemHitHint.KEEPALL
            )
        ]
        self.set_catalog(catalog)

    def _create_suggestions(self, timetoshow):
        """Creates various catalog items with different formats and locales for a given datetime object
        """
        suggestions = []

        try:
            suggestions.append(self.create_item(
                category=kp.ItemCategory.KEYWORD,
                label=str(int(timetoshow.timestamp())),
                short_desc="Time as unix timestamp (seconds since Jan 01 1970. (UTC)) {}".format(self.COPY_TO_CB),
                target="timestamp_int",
                args_hint=kp.ItemArgsHint.FORBIDDEN,
                hit_hint=kp.ItemHitHint.IGNORE
            ))
            suggestions.append(self.create_item(
                category=kp.ItemCategory.KEYWORD,
                label=str(int(timetoshow.timestamp() * 1000)),
                short_desc="Time as timestamp (milliseconds since Jan 01 1970. (UTC)) {}".format(self.COPY_TO_CB),
                target="timestamp_float",
                args_hint=kp.ItemArgsHint.FORBIDDEN,
                hit_hint=kp.ItemHitHint.IGNORE
            ))
        except OSError as ex:
            self.dbg("Timestamp failed:", ex)

        suggestions.append(self.create_item(
            category=kp.ItemCategory.KEYWORD,
            label=str(timetoshow.isoformat(timespec="seconds")),
            short_desc="Time in ISO 8601 format {}".format(self.COPY_TO_CB),
            target="isoformat_s",
            args_hint=kp.ItemArgsHint.FORBIDDEN,
            hit_hint=kp.ItemHitHint.IGNORE
        ))
        suggestions.append(self.create_item(
            category=kp.ItemCategory.KEYWORD,
            label=str(timetoshow.isoformat(timespec="microseconds")),
            short_desc="Time in ISO 8601 format {}".format(self.COPY_TO_CB),
            target="isoformat_ms",
            args_hint=kp.ItemArgsHint.FORBIDDEN,
            hit_hint=kp.ItemHitHint.IGNORE
        ))

        for idx, frmt in enumerate(self._formats):
            for loc in self._locales:
                try:
                    with self.__setlocale(loc):
                        item = self.create_item(
                            category=kp.ItemCategory.KEYWORD,
                            label=str(timetoshow.strftime(frmt)),
                            short_desc="Time in format '{}' in locale {} {}".format(frmt,
                                                                                    loc if loc else "system default",
                                                                                    self.COPY_TO_CB),
                            target="format_{}_{}".format(idx, loc),
                            args_hint=kp.ItemArgsHint.FORBIDDEN,
                            hit_hint=kp.ItemHitHint.IGNORE
                        )
                        if not self.__contains_item(suggestions, item):
                            suggestions.append(item)
                except locale.Error as ex:
                    self.warn("Error with format ", frmt, "on locale", loc, ":", ex)

        return suggestions

    def __contains_item(self, suggestions, search):
        """Checks if a catalog item with the same label is already in the collection
        """
        for item in suggestions:
            if item.label() == search.label():
                return True
        return False

    @contextlib.contextmanager
    def __setlocale(self, name):
        """Sets the locale for time formatting functions to be used in a with statement.

        :param name: See https://docs.microsoft.com/en-us/cpp/c-runtime-library/language-strings?view=vs-2017 for
            possible values
        """
        saved = locale.setlocale(locale.LC_TIME)
        try:
            yield locale.setlocale(locale.LC_TIME, name)
        finally:
            locale.setlocale(locale.LC_TIME, saved)

    def on_suggest(self, user_input, items_chain):
        if not items_chain:
            return

        if user_input:
            timetoshow = self._tryparse(user_input)
        else:
            timetoshow = datetime.datetime.now().astimezone()

        if timetoshow:
            suggestions = self._create_suggestions(timetoshow)
            self.set_suggestions(suggestions, kp.Match.ANY, kp.Sort.NONE)

    def _tryparse(self, in_str):
        """Tries to parse a string into a datetime object
        """
        # Maybe its a timestamp
        if re.match("^\d+$", in_str):
            try:
                return datetime.datetime.fromtimestamp(int(in_str)).astimezone()
            except:
                self.dbg("Parsing failed: ", sys.exc_info()[0])

            try:
                return datetime.datetime.fromtimestamp(int(in_str) / 1000).astimezone()
            except OSError as ex:
                self.dbg("Parsing failed: ", ex)

        if re.match("^\d+\.\d*$", in_str):
            try:
                return datetime.datetime.fromtimestamp(float(in_str)).astimezone()
            except OSError as ex:
                self.dbg("Parsing failed: ", ex)

            try:
                return datetime.datetime.fromtimestamp(float(in_str) / 1000).astimezone()
            except OSError as ex:
                self.dbg("Parsing failed: ", ex)

        # do your magic dateutil
        try:
            return dateutil.parser.parse(in_str)
        except (ValueError, OverflowError) as ex:
            self.dbg("Parsing failed: ", ex)

        return None

    def on_execute(self, item, action):
        """Copies the item label to the clipboard
        """
        kpu.set_clipboard(item.label())

