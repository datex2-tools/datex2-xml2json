from pathlib import Path

import pytest

from datex2_xml2json.transformer import (
    InputFormat,
    OutputFormat,
    UnsupportedOptionsError,
    build_transformer,
    check_options,
    transform,
)

XML_FIXTURE = str(Path(__file__).parents[1] / 'integration' / 'data' / 'sitpub_pointCoordinate.xml')


@pytest.mark.parametrize(
    'output_format', [OutputFormat.GEOJSON, OutputFormat.RAW, OutputFormat.DATEX2_3_7_JSON_LITE, OutputFormat.GEOPARQUET]
)
def test_validation_of_unsupported_format_is_rejected_before_writing(tmp_path: Path, output_format: OutputFormat) -> None:
    with pytest.raises(UnsupportedOptionsError):
        transform(XML_FIXTURE, str(tmp_path), InputFormat.DATEX2_2_2_XML, output_format, True, None, None)

    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    'output_format',
    [None, OutputFormat.GEOJSON, OutputFormat.CIFS, OutputFormat.DATEX2_3_7_JSON_LITE, OutputFormat.GEOPARQUET],
)
def test_unsupported_output_formats_for_3_7_input_are_rejected(output_format: OutputFormat | None) -> None:
    with pytest.raises(UnsupportedOptionsError):
        check_options(InputFormat.DATEX2_3_7_XML, output_format, False, None, None)


@pytest.mark.parametrize('source,publication', [('source', None), (None, 'publication')])
def test_source_options_for_3_7_input_are_rejected(source: str | None, publication: str | None) -> None:
    with pytest.raises(UnsupportedOptionsError):
        check_options(InputFormat.DATEX2_3_7_XML, OutputFormat.DATEX2_3_7_JSON, False, source, publication)


@pytest.mark.parametrize('output_format', [OutputFormat.DATEX2_3_7_JSON, OutputFormat.RAW])
def test_supported_output_formats_for_3_7_input_are_accepted(output_format: OutputFormat) -> None:
    check_options(InputFormat.DATEX2_3_7_XML, output_format, False, None, None)


def test_build_transformer_rejects_unsupported_output_format_for_3_7_input() -> None:
    with pytest.raises(ValueError, match='Unsupported output format'):
        build_transformer(InputFormat.DATEX2_3_7_XML, OutputFormat.GEOJSON)


def test_raw_output_does_not_contain_source_options(tmp_path: Path) -> None:
    transform(XML_FIXTURE, str(tmp_path), InputFormat.DATEX2_2_2_XML, None, False, 'MY_SOURCE_ID', 'MY_PUBLICATION_ID')

    assert 'MY_SOURCE_ID' not in (tmp_path / 'sitpub_pointCoordinate.raw.json').read_text()
    assert 'MY_SOURCE_ID' in (tmp_path / 'sitpub_pointCoordinate.lite.json').read_text()
    assert 'MY_PUBLICATION_ID' in (tmp_path / 'sitpub_pointCoordinate.lite.json').read_text()
