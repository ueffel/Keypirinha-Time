import keypirinha as kp
import keypirinha_util as kpu
import contextlib
import datetime
import locale
import os
import re
import site
import traceback

# insert lib directory to path to import modules normally
site.addsitedir(os.path.join(os.path.dirname(__file__), "lib"))
import dateutil.parser
import dateutil.zoneinfo


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
    DEFAULT_ITEM_LABEL2 = "Timezone:"
    COPY_TO_CB = "(press Enter to copy to clipboard)"

    def __init__(self):
        super().__init__()
        self._formats = self.DEFAULT_FORMATS
        self._locales = self.DEFAULT_LOCALES
        self._item_label = self.DEFAULT_ITEM_LABEL
        self._item_label2 = self.DEFAULT_ITEM_LABEL2

    def on_start(self):
        self._read_config()
        self.set_default_icon(
            self.load_icon("res://{}/clock.ico".format(self.package_full_name()))
        )

    def on_events(self, flags):
        """Reloads the package config when its changed"""
        if flags & kp.Events.PACKCONFIG:
            self._read_config()
            self.on_catalog()

    def _read_config(self):
        """Reads the config"""
        self.dbg("Reading config")
        settings = self.load_settings()

        self._debug = settings.get_bool("debug", "main", False)

        self._formats = settings.get_multiline("formats", "main", self.DEFAULT_FORMATS)
        self.dbg("Formats =", self._formats)

        self._locales = settings.get_multiline(
            "locales", "main", self.DEFAULT_LOCALES, True
        )
        self.dbg("Locales =", self._locales)

        self._item_label = settings.get("item_label", "main", self.DEFAULT_ITEM_LABEL)
        self.dbg("item_label =", self._item_label)

        self._item_label2 = settings.get(
            "item_label2", "main", self.DEFAULT_ITEM_LABEL2
        )
        self.dbg("item_label2 =", self._item_label2)

    def on_catalog(self):
        """Adds the kill command to the catalog"""
        catalog = [
            self.create_item(
                category=kp.ItemCategory.KEYWORD,
                label=self._item_label,
                short_desc="Date and time parsing and formatting",
                target="time",
                args_hint=kp.ItemArgsHint.REQUIRED,
                hit_hint=kp.ItemHitHint.KEEPALL,
            ),
            self.create_item(
                category=kp.ItemCategory.KEYWORD,
                label=self._item_label2,
                short_desc="Current date in different timezones",
                target="timezone",
                args_hint=kp.ItemArgsHint.REQUIRED,
                hit_hint=kp.ItemHitHint.KEEPALL,
            ),
        ]
        self.set_catalog(catalog)

    def _create_suggestions(self, timetoshow):
        """Creates various catalog items with different formats and locales for a given datetime object"""
        suggestions = []

        try:
            suggestions.append(
                self.create_item(
                    category=kp.ItemCategory.KEYWORD,
                    label=str(int(timetoshow.timestamp())),
                    short_desc="Time as unix timestamp (seconds since Jan 01 1970. (UTC)) {}".format(
                        self.COPY_TO_CB
                    ),
                    target="timestamp_int",
                    args_hint=kp.ItemArgsHint.ACCEPTED,
                    hit_hint=kp.ItemHitHint.IGNORE,
                    loop_on_suggest=True,
                )
            )
            suggestions.append(
                self.create_item(
                    category=kp.ItemCategory.KEYWORD,
                    label=str(int(timetoshow.timestamp() * 1000)),
                    short_desc="Time as timestamp (milliseconds since Jan 01 1970. (UTC)) {}".format(
                        self.COPY_TO_CB
                    ),
                    target="timestamp_float",
                    args_hint=kp.ItemArgsHint.ACCEPTED,
                    hit_hint=kp.ItemHitHint.IGNORE,
                    loop_on_suggest=True,
                )
            )
        except OSError as ex:
            self.dbg("Timestamp failed:", ex)

        suggestions.append(
            self.create_item(
                category=kp.ItemCategory.KEYWORD,
                label=timetoshow.isoformat(timespec="seconds"),
                short_desc="Time in ISO 8601 format {}".format(self.COPY_TO_CB),
                target="isoformat_s",
                args_hint=kp.ItemArgsHint.ACCEPTED,
                hit_hint=kp.ItemHitHint.IGNORE,
                loop_on_suggest=True,
            )
        )
        suggestions.append(
            self.create_item(
                category=kp.ItemCategory.KEYWORD,
                label=timetoshow.isoformat(timespec="microseconds"),
                short_desc="Time in ISO 8601 format {}".format(self.COPY_TO_CB),
                target="isoformat_ms",
                args_hint=kp.ItemArgsHint.ACCEPTED,
                hit_hint=kp.ItemHitHint.IGNORE,
                loop_on_suggest=True,
            )
        )

        for idx, frmt in enumerate(self._formats):
            for loc in self._locales:
                try:
                    with self.__setlocale(loc):
                        item = self.create_item(
                            category=kp.ItemCategory.KEYWORD,
                            label=str(timetoshow.strftime(frmt)),
                            short_desc="Time in format '{}' in locale {} {}".format(
                                frmt, loc if loc else "system default", self.COPY_TO_CB
                            ),
                            target="format_{}_{}".format(idx, loc),
                            args_hint=kp.ItemArgsHint.ACCEPTED,
                            hit_hint=kp.ItemHitHint.IGNORE,
                            loop_on_suggest=True,
                        )
                        if not self.__contains_item(suggestions, item):
                            suggestions.append(item)
                except locale.Error as ex:
                    self.warn("Error with format ", frmt, "on locale", loc, ":", ex)

        return suggestions

    @staticmethod
    def __contains_item(suggestions, search):
        """Checks if a catalog item with the same label is already in the collection"""
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

        if (len(items_chain) % 2 == 1 and items_chain[0].target() == "time") or (
            len(items_chain) > 1
            and len(items_chain) % 2 == 0
            and items_chain[0].target() == "timezone"
        ):
            timezone = items_chain[-1].target() if len(items_chain) > 1 else None
            self.dbg("timezone", timezone)
            if user_input:
                try:
                    if int(user_input) < 86400:
                        self.dbg("Timestamps smaller than 86400 do not work.")
                        return
                except ValueError as ex:
                    self.dbg("Input error: ", ex, "\n", traceback.format_exc())

                parsed = self._tryparse(user_input)
                self.dbg("parsed time", parsed)
                if parsed is None:
                    return

                if timezone:
                    timetoshow = parsed.replace(tzinfo=dateutil.tz.gettz(timezone))
                else:
                    timetoshow = parsed.astimezone()
            else:
                if (
                    items_chain[0].target() == "time"
                    and len(items_chain) > 1
                    or items_chain[0].target() == "timezone"
                    and len(items_chain) > 2
                ):
                    time_wo_zone = self._tryparse(items_chain[-2].label())
                else:
                    time_wo_zone = datetime.datetime.now()

                if timezone:
                    timetoshow = time_wo_zone.astimezone(tz=dateutil.tz.gettz(timezone))
                else:
                    timetoshow = time_wo_zone.astimezone()
                self.dbg("timetoshow", timetoshow)

            if timetoshow:
                suggestions = self._create_suggestions(timetoshow)
                self.set_suggestions(suggestions, kp.Match.ANY, kp.Sort.NONE)
        elif (
            (len(items_chain) % 2 == 1) and items_chain[0].target() == "timezone"
        ) or (
            len(items_chain) > 1
            and len(items_chain) % 2 == 0
            and items_chain[0].target() == "time"
        ):
            suggestions = []
            for (
                name,
                timezone,
            ) in dateutil.zoneinfo.get_zonefile_instance().zones.items():
                suggestions.append(
                    self.create_item(
                        category=kp.ItemCategory.KEYWORD,
                        label="{} ({})".format(
                            name.replace("_", " "),
                            datetime.datetime.utcnow()
                            .astimezone(tz=timezone)
                            .strftime("%z"),
                        ),
                        short_desc="Time in timezone '{}'".format(name),
                        target=name,
                        args_hint=kp.ItemArgsHint.REQUIRED,
                        hit_hint=kp.ItemHitHint.IGNORE,
                        loop_on_suggest=True,
                    )
                )
            self.set_suggestions(suggestions)

    def _tryparse(self, in_str):
        """Tries to parse a string into a datetime object"""
        # Maybe its a timestamp
        if re.match(r"^\d+$", in_str):
            try:
                return datetime.datetime.fromtimestamp(int(in_str))
            except Exception as ex:
                self.dbg("Parsing failed: ", ex, "\n", traceback.format_exc())

            try:
                return datetime.datetime.fromtimestamp(int(in_str) / 1000)
            except Exception as ex:
                self.dbg("Parsing failed: ", ex, "\n", traceback.format_exc())

        if re.match(r"^\d+\.\d*$", in_str):
            try:
                return datetime.datetime.fromtimestamp(float(in_str))
            except OSError as ex:
                self.dbg("Parsing failed: ", ex, "\n", traceback.format_exc())

            try:
                return datetime.datetime.fromtimestamp(float(in_str) / 1000)
            except OSError as ex:
                self.dbg("Parsing failed: ", ex, "\n", traceback.format_exc())

        # do your magic dateutil
        try:
            return dateutil.parser.parse(in_str)
        except (ValueError, OverflowError) as ex:
            self.dbg("Parsing failed: ", ex, "\n", traceback.format_exc())

        return None

    def on_execute(self, item, action):
        """Copies the item label to the clipboard"""
        self.dbg("on_execute:", item.target())
        kpu.set_clipboard(item.label())
