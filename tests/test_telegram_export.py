from rent_parse.ingest.telegram_export import TextEntity, parse_text_entities


def test_parse_text_entities_with_placeholders() -> None:
    mock_entities: list[TextEntity] = [
        {"type": "plain", "text": "Video: "},
        {"type": "link", "text": "https://youtube.com/xyz"},
    ]

    parsed_entity = parse_text_entities(mock_entities)

    # Check the string output
    assert parsed_entity.text == "Video: [LINK_1]"

    # Check the extracted dictionary output
    assert parsed_entity.extracted_data == {"[LINK_1]": "https://youtube.com/xyz"}


def test_parse_text_entities_multiple_same_type() -> None:
    mock_entities: list[TextEntity] = [
        {"type": "plain", "text": "Call "},
        {"type": "phone", "text": "9999999999"},
        {"type": "plain", "text": " or "},
        {"type": "phone", "text": "8888888888"},
    ]

    parsed_entity = parse_text_entities(mock_entities)

    assert parsed_entity.text == "Call [PHONE_1] or [PHONE_2]"
    assert parsed_entity.extracted_data == {
        "[PHONE_1]": "9999999999",
        "[PHONE_2]": "8888888888",
    }


def test_parse_text_entities_empty_list() -> None:
    parsed_entity = parse_text_entities([])

    assert parsed_entity.text == ""
    assert parsed_entity.extracted_data == {}


def test_parse_text_entities_unknown_type() -> None:
    mock_entities: list[TextEntity] = [
        {"type": "plain", "text": "Area: "},
        {"type": "new_unsupported_type", "text": "HSR Layout"},
    ]

    parsed_entity = parse_text_entities(mock_entities)

    assert parsed_entity.text == "Area: HSR Layout"
    assert parsed_entity.extracted_data == {}


def test_parse_text_entities_text_link() -> None:
    mock_entities: list[TextEntity] = [
        {"type": "plain", "text": "Area: "},
        {
            "type": "text_link",
            "text": "HSR Layout",
            "href": "https://example.com/hsr-layout",
        },
    ]

    parsed_entity = parse_text_entities(mock_entities)

    assert parsed_entity.text == "Area: HSR Layout [TEXT_LINK_1]"
    assert parsed_entity.extracted_data == {
        "[TEXT_LINK_1]": "https://example.com/hsr-layout",
    }


def test_parse_text_entities_text_link_without_href() -> None:
    mock_entities: list[TextEntity] = [
        {"type": "plain", "text": "Area: "},
        {
            "type": "text_link",
            "text": "HSR Layout",
            "href": "",
        },
    ]

    parsed_entity = parse_text_entities(mock_entities)

    assert parsed_entity.text == "Area: HSR Layout"
    assert parsed_entity.extracted_data == {}


def test_parse_text_entities_real_masked_data() -> None:
    mock_entities: list[TextEntity] = [
        {
            "type": "plain",
            "text": "Male Flatmate needed in a 3 BHK Flat\n\nNO BROKERAGE!!"
            "\n\nCONTACT WHATSAPP ",
        },
        {"type": "phone", "text": "7000000000"},
        {
            "type": "plain",
            "text": "\n\nDESCRIPTION:\n\nHi everyone! We are looking for 1 male "
            "flatmate for a spacious 3BHK, 3-bathroom flat in a gated society at "
            "Seegehalli.\n\nThe flat is 1,850 sq. ft., and the total rent is "
            "₹51,000 (including maintenance).\n\nIf you're interested "
            "or know someone who is, please DM me for more details.\n\n",
        },
        {"type": "link", "text": "https://example.com/location"},
        {"type": "plain", "text": "\n\nCLICK on the LINK BELOW TO MESSAGE!!\n\n"},
        {"type": "link", "text": "https://wa.me/+917000000000"},
        {"type": "plain", "text": ""},
    ]

    parsed_entity = parse_text_entities(mock_entities)

    assert (
        parsed_entity.text == "Male Flatmate needed in a 3 BHK Flat\n\nNO BROKERAGE!!"
        "\n\nCONTACT WHATSAPP [PHONE_1]\n\nDESCRIPTION:"
        "\n\nHi everyone! We are looking for 1 male flatmate for a spacious 3BHK, "
        "3-bathroom flat in a gated society at Seegehalli."
        "\n\nThe flat is 1,850 sq. ft., and the total rent is ₹51,000 "
        "(including maintenance).\n\nIf you're interested or know someone who is, "
        "please DM me for more details.\n\n[LINK_1]\n\nCLICK on the LINK "
        "BELOW TO MESSAGE!!\n\n[LINK_2]"
    )
    assert parsed_entity.extracted_data == {
        "[PHONE_1]": "7000000000",
        "[LINK_1]": "https://example.com/location",
        "[LINK_2]": "https://wa.me/+917000000000",
    }
