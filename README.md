# Keypirinha Time

This is a package that extends the fast keystroke launcher keypirinha (<http://keypirinha.com/>)
with a command to convert and format datetime strings.

## Usage

Use the `Time:` item. (configurable)

If no other input is entered the displayed datetime is the current time.
Any input is interpreted as date string (or at least tried to)

Hitting tab after a time is displayed offers timezone to convert the time.

There is also the possibility to start off with a timezone with item`Timezone:`
(configurable) and do the above (current time or try parse).

Executing any of the suggestions copies the selected item to the clipboard.

![Usage](usage.gif)

## Configuration

It's possible to configure multiple formats and locales in which the time is displayed. See the
default configuration file for further information.

## Installation

### With [PackageControl](https://github.com/ueffel/Keypirinha-PackageControl)

Install Package "Keypirinha-Time"

### Manually

* Download the `Time.keypirinha-package` from the [releases](https://github.com/ueffel/Keypirinha-Time/releases/latest).
* Copy the file into `%APPDATA%\Keypirinha\InstalledPackages` (installed mode) or
  `<Keypirinha_Home>\portable\Profile\InstalledPackages` (portable mode)
