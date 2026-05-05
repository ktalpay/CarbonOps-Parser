"""Smoke tests for source acquisition CLI entrypoint wiring."""

from carbonfactor_parser.source_acquisition.cli import main


def test_source_acquisition_cli_main_is_callable() -> None:
    assert callable(main)
