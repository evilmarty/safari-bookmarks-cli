from argparse import ArgumentParser, BooleanOptionalAction, Namespace
from os.path import expanduser
from sys import stdout
from uuid import UUID

from .cli import CLI
from .version import VERSION


def parse_args() -> Namespace:
    parser = ArgumentParser(
        prog="Safari Bookmarks CLI",
        description="A utility to help manage Safari bookmarks.",
    )
    parser.set_defaults(command=None)
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s v{version}".format(version=VERSION),
    )
    parser.add_argument(
        "--file",
        "-f",
        type=expanduser,
        default="~/Library/Safari/Bookmarks.plist",
        help="The path to the Safari bookmarks.",
    )
    parser.add_argument(
        "--json",
        action=BooleanOptionalAction,
        default=False,
        help="Render output as JSON",
    )
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument(
        "--format",
        "-F",
        required=False,
        help="Customize the output format. Available placeholders: {title}, {url}, {id}, {type}, {prefix}, {suffix}.",
    )
    group.add_argument(
        "--simple",
        dest="simple_format",
        action=BooleanOptionalAction,
        default=False,
        help="Set the output to a simple format. Not to be used with --format.",
    )
    subparsers = parser.add_subparsers(
        title="commands",
        required=True,
    )
    parser_list = subparsers.add_parser(
        "list",
        aliases=["ls", "show"],
        description="List bookmarks and folders.",
    )
    parser_list.add_argument(
        "path",
        nargs="*",
        help="The UUID or bookmark or folder path to show. Default shows all.",
    )
    parser_list.set_defaults(command="list")
    parser_add = subparsers.add_parser(
        "add",
        aliases=["a", "create"],
        description="Add a bookmark or folder.",
    )
    parser_add.add_argument(
        "path",
        nargs="*",
        help="The UUID or folder path to add the new bookmark or folder to.",
    )
    parser_add.add_argument(
        "--uuid",
        type=UUID,
        required=False,
        help="The UUID to use. Default is to generate a new UUID.",
    )
    parser_add.add_argument(
        "--title",
        required=True,
        help="The title of the bookmark or folder.",
    )
    group = parser_add.add_mutually_exclusive_group(required=True)
    group.add_argument("--url", help="The URL for the bookmark.")
    group.add_argument(
        "--folder",
        dest="list",
        action=BooleanOptionalAction,
        default=False,
        help="Add a folder instead of a bookmark.",
    )
    parser_add.set_defaults(command="add")
    parser_remove = subparsers.add_parser(
        "remove",
        aliases=["rm", "delete", "del"],
        description="Remove a bookmark or folder.",
    )
    parser_remove.add_argument(
        "path",
        nargs="+",
        help="The UUID or path to the bookmark or folder to remove.",
    )
    parser_remove.set_defaults(command="remove")
    parser_move = subparsers.add_parser(
        "move",
        aliases=["mv"],
        description="Move a bookmark or folder.",
    )
    parser_move.add_argument(
        "target", nargs="+", help="The UUID or path of the bookmark or folder to move."
    )
    parser_move.add_argument(
        "--to",
        nargs="*",
        help="The UUID or path to the destination folder.",
    )
    parser_move.set_defaults(command="move")
    parser_edit = subparsers.add_parser(
        "edit",
        aliases=["e", "update", "change"],
        description="Edit a bookmark or folder.",
    )
    parser_edit.add_argument(
        "path",
        nargs="+",
        help="The UUID or path of the bookmark or folder to change.",
    )
    parser_edit.add_argument(
        "--title",
        help="The new title to change.",
    )
    parser_edit.add_argument(
        "--url",
        help="The new URL to change. Only used for bookmarks.",
    )
    parser_edit.set_defaults(command="edit")
    parser_empty = subparsers.add_parser(
        "empty",
        aliases=["clear"],
        description="Empty the items in a folder.",
    )
    parser_empty.add_argument(
        "path",
        nargs="+",
        help="The UUID or path of the bookmark or folder to empty.",
    )
    parser_empty.set_defaults(command="empty")
    return parser.parse_args()


def main():
    args = parse_args().__dict__
    file = args.pop("file")
    CLI(file, stdout).run(**args)
