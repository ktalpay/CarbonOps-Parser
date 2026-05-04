from carbonfactor_parser.normalization import (
    ArtificialNormalizationExecutor,
    NormalizationResult,
    NormalizedRecord,
    ParserNormalizationHandoff,
    ParserNormalizationHandoffEntry,
)


def _handoff() -> ParserNormalizationHandoff:
    return ParserNormalizationHandoff(
        parser_record_count=2,
        issue_count=1,
        source_reference="fixture:parser_source",
        entries=(
            ParserNormalizationHandoffEntry(
                record_id="record-001",
                parser_record=(
                    ("field_name", "alpha"),
                    ("value_label", "one"),
                ),
                source_reference="fixture:parser_source",
            ),
            ParserNormalizationHandoffEntry(
                record_id="record-002",
                parser_record=(
                    ("field_name", "beta"),
                    ("value_label", "two"),
                ),
                source_reference="fixture:parser_source",
            ),
        ),
    )


def test_executor_accepts_parser_normalization_handoff() -> None:
    result = ArtificialNormalizationExecutor().execute(_handoff())

    assert isinstance(result, NormalizationResult)


def test_executor_returns_normalized_record_instances() -> None:
    result = ArtificialNormalizationExecutor().execute(_handoff())

    assert result.summary.normalized_record_count == 2
    assert all(isinstance(record, NormalizedRecord) for record in result.records)


def test_executor_produces_deterministic_output() -> None:
    executor = ArtificialNormalizationExecutor()
    handoff = _handoff()

    first = executor.execute(handoff)
    second = executor.execute(handoff)

    assert first == second
    assert first.records == (
        NormalizedRecord(
            record_id="record-001",
            fields=(
                (
                    "parser_record",
                    (
                        ("field_name", "alpha"),
                        ("value_label", "one"),
                    ),
                ),
                ("parser_source_reference", "fixture:parser_source"),
                ("handoff_source_reference", "fixture:parser_source"),
                ("handoff_is_artificial", True),
            ),
            source_reference="fixture:parser_source",
        ),
        NormalizedRecord(
            record_id="record-002",
            fields=(
                (
                    "parser_record",
                    (
                        ("field_name", "beta"),
                        ("value_label", "two"),
                    ),
                ),
                ("parser_source_reference", "fixture:parser_source"),
                ("handoff_source_reference", "fixture:parser_source"),
                ("handoff_is_artificial", True),
            ),
            source_reference="fixture:parser_source",
        ),
    )


def test_executor_does_not_mutate_input_handoff() -> None:
    handoff = _handoff()
    before = handoff

    ArtificialNormalizationExecutor().execute(handoff)

    assert handoff == before


def test_executor_handles_empty_handoff_records() -> None:
    handoff = ParserNormalizationHandoff(
        parser_record_count=0,
        issue_count=0,
        entries=(),
        source_reference="fixture:empty_source",
    )

    result = ArtificialNormalizationExecutor().execute(handoff)

    assert result.records == ()
    assert result.issues == ()
    assert result.summary.normalized_record_count == 0
    assert result.summary.is_clean is True


def test_executor_does_not_read_files(monkeypatch, tmp_path) -> None:
    missing_path = tmp_path / "parser_source.txt"
    handoff = ParserNormalizationHandoff(
        parser_record_count=1,
        issue_count=0,
        source_reference=str(missing_path),
        entries=(
            ParserNormalizationHandoffEntry(
                record_id="record-001",
                parser_record=(("field_name", "alpha"),),
                source_reference=str(missing_path),
            ),
        ),
    )

    def fail_open(*args, **kwargs):
        raise AssertionError("executor should not open files")

    monkeypatch.setattr("builtins.open", fail_open)

    result = ArtificialNormalizationExecutor().execute(handoff)

    assert result.summary.normalized_record_count == 1
    assert not missing_path.exists()


def test_executor_does_not_apply_unit_conversion_or_correctness_logic() -> None:
    handoff = ParserNormalizationHandoff(
        parser_record_count=1,
        issue_count=0,
        entries=(
            ParserNormalizationHandoffEntry(
                record_id="record-001",
                parser_record=(
                    ("unit_label", "uninterpreted label"),
                    ("value_label", "sample text"),
                ),
            ),
        ),
    )

    result = ArtificialNormalizationExecutor().execute(handoff)
    result_text = str(result).lower()

    assert result.records[0].fields[0] == (
        "parser_record",
        (
            ("unit_label", "uninterpreted label"),
            ("value_label", "sample text"),
        ),
    )
    assert "converted" not in result_text
    assert "correct" not in result_text
