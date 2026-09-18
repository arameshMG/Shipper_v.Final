import pytest
from fedex_oauth import parse_address

def test_standard_multiline_with_name():
    result = parse_address("Jane Doe\n302 Grace Arbor Lane\nFountain Inn, SC 29644")
    assert result["street"] == "302 Grace Arbor Lane"
    assert result["city"] == "Fountain Inn"
    assert result["state"] == "SC"
    assert result["zip_code"] == "29644"


def test_no_name_just_street_and_city_state_zip():
    result = parse_address("123 Main St\nPhiladelphia, PA 19103")
    assert result["street"] == "123 Main St"
    assert result["city"] == "Philadelphia"
    assert result["state"] == "PA"
    assert result["zip_code"] == "19103"


def test_extra_blank_lines():
    result = parse_address("John Smith\n\n456 Oak Ave\n\nAtlanta, GA 30301")
    assert result["street"] == "456 Oak Ave"
    assert result["city"] == "Atlanta"
    assert result["state"] == "GA"


def test_zip_plus_4_format():
    result = parse_address("Jane Doe\n789 Elm St\nBoston, MA 02101-1234")
    assert result["zip_code"] == "02101-1234"


def test_hyphenated_city_name():
    result = parse_address("Bob Lee\n55 Park Rd\nWinston-Salem, NC 27101")
    assert result["city"] == "Winston-Salem"


# Formatting inconsistencies

def test_no_comma_before_state():
    result = parse_address("Jane Doe\n302 Grace Arbor Lane\nFountain Inn SC 29644")
    assert result["city"] == "Fountain Inn"
    assert result["state"] == "SC"


def test_lowercase_state_code():
    result = parse_address("Jane Doe\n302 Grace Arbor Lane\nFountain Inn, sc 29644")
    assert result["state"] == "SC"  # should be normalized to uppercase


def test_extra_surrounding_whitespace():
    result = parse_address("  Jane Doe  \n  302 Grace Arbor Lane  \n  Fountain Inn, SC 29644  ")
    assert result["street"] == "302 Grace Arbor Lane"
    assert result["city"] == "Fountain Inn"


def test_apartment_number_on_street_line():
    result = parse_address("Jane Doe\n302 Grace Arbor Lane Apt 4B\nFountain Inn, SC 29644")
    assert "Apt 4B" in result["street"]


def test_apartment_on_its_own_line():
    result = parse_address("Test UserMED\n30 Crystal Palm Boulevard\nApt. 402\nSt. John's, FL 32259")
    assert "30 Crystal Palm Boulevard" in result["street"]
    assert "Apt. 402" in result["street"]
    assert result["city"] == "St. John's"


def test_one_line_comma_separated():
    result = parse_address("Jane Doe, 302 Grace Arbor Lane, Fountain Inn, SC 29644")
    assert result["street"] == "302 Grace Arbor Lane"
    assert result["city"] == "Fountain Inn"


def test_one_line_no_name():
    result = parse_address("302 Grace Arbor Lane, Fountain Inn, SC 29644")
    assert result["street"] == "302 Grace Arbor Lane"


def test_trailing_comma():
    result = parse_address("Jane Doe\n302 Grace Arbor Lane\nFountain Inn, SC 29644,")
    assert result["zip_code"] == "29644"


def test_trailing_comma_and_space():
    result = parse_address("Jane Doe\n302 Grace Arbor Lane\nFountain Inn, SC 29644, ")
    assert result["zip_code"] == "29644"


def test_curly_apostrophe_in_city_name():
    # reverse -> convert straight quotes to curly ones
    result = parse_address("Test UserMED\n30 Crystal Palm Boulevard\nApt. 402\nSt. John\u2019s, FL 32259, ")
    assert result["city"] in ("St. John's", "St. John\u2019s")
    assert result["state"] == "FL"
    assert result["zip_code"] == "32259"


# Fully concatenated, no separators at all

def test_fully_concatenated_no_separators():
    result = parse_address("Test UserMED30 Crystal Palm BoulevardApt. 402St. John's, FL 32259")
    assert result["city"] == "St. John's"
    assert result["state"] == "FL"
    assert result["zip_code"] == "32259"


# Cases that should correctly raise an error, not silently guess

def test_missing_zip_raises_error():
    with pytest.raises(ValueError):
        parse_address("Jane Doe\n302 Grace Arbor Lane\nFountain Inn, SC")


def test_empty_string_raises_error():
    with pytest.raises(ValueError):
        parse_address("")


def test_none_input_raises_error():
    with pytest.raises(ValueError):
        parse_address(None)


def test_just_a_name_raises_error():
    with pytest.raises(ValueError):
        parse_address("Jane Doe")
