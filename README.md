# safari-bookmarks-cli
A cli to manage bookmarks in the Safari web browser.

This utility interacts with Safari's `Bookmarks.plist` file. When it detects changes it is reloaded without intervention.

**Note** macOS 10.14+ requires Full Disk Access for the application being used. ie. Terminal, iTerm, etc.

## Installation

You can install safari-bookmarks-cli via pip:

```shell
pip3 install safari-bookmarks-cli

# verify installation
safari-bookmarks --version
```

## Usage

The following assumes the default location for Safari's bookmarks, which is `~/Library/Safari/Bookmarks.plist`. If this is not the case you can specify an alternate location by passing the arguments `-f <elsewhere>`.

For a full list of commands and options just run:

```shell
safari-bookmarks --help
```

### To list all bookmarks run

```shell
safari-bookmarks list
```

### Add a new bookmark to the menubar

```shell
safari-bookmarks add --title "New bookmark" --url "http://example.com" --to BookmarksMenu
```

### Add a new bookmark to the menu

```shell
safari-bookmarks add --title "New folder" --list --to BookmarksBar
```

### Move a bookmark to a different folder

```shell
safari-bookmarks move --title "New bookmark" --to "New folder"
```

### Remove a bookmark or folder

**Note** removing a folder will also remove all bookmarks and folders within it.

```shell
safari-bookmarks remove "New folder"
```

## Testing

Clone the repository:

```shell
git clone https://github.com/evilmarty/safari-bookmarks-cli.git
```

Install pytest and flake8

```shell
pip3 install pytest flake8
```

Run them

```shell
pytest && flake8
```
