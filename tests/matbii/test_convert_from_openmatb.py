from xml.etree.ElementTree import Element, SubElement, fromstring, tostring

from matbexp.matbii.convert_from_openmatb import (
    _remove_events,
    convert_communications_to_xml,
    convert_sysmon_lights_to_xml,
    convert_sysmon_scales_to_xml,
    matbii_generate_random_xml_with_text_file,
)

_TEXT_FILE_CONTENTS = """
# Name: incapacitation
# Date: 10/05/2024 09:41:46


# Block n° 1. Technical load = 5.0 %
0:00:00;track;start
0:00:00;track;targetproportion;0.95
0:00:00;sysmon;start
0:00:00;communications;start
0:00:00;resman;start
0:00:00;resman;tank-a-lossperminute;60
0:00:00;resman;tank-b-lossperminute;60

# Block n° 2. Technical load = 15.6 %
0:01:00;track;targetproportion;0.8444444444444444
0:01:00;resman;tank-a-lossperminute;186
0:01:00;resman;tank-b-lossperminute;186

# Block n° 3. Technical load = 26.1 %
0:02:00;track;targetproportion;0.7388888888888889
0:02:39;sysmon;lights-1-failure;True
0:02:41;sysmon;scales-1-failure;True
0:02:02;communications;radioprompt;other
0:02:00;resman;tank-a-lossperminute;313
0:02:00;resman;tank-b-lossperminute;313

# Block n° 4. Technical load = 36.7 %
0:03:00;track;targetproportion;0.6333333333333333
0:03:26;sysmon;lights-1-failure;True
0:03:46;sysmon;lights-2-failure;True
0:03:22;sysmon;scales-1-failure;True
0:03:45;sysmon;scales-2-failure;True
0:03:45;communications;radioprompt;own
0:03:00;resman;tank-a-lossperminute;439
0:03:00;resman;tank-b-lossperminute;439

# Block n° 5. Technical load = 47.2 %
0:04:00;track;targetproportion;0.5277777777777778
0:04:21;sysmon;lights-1-failure;True
0:04:35;sysmon;lights-2-failure;True
0:04:19;sysmon;scales-1-failure;True
0:04:47;sysmon;scales-2-failure;True
0:04:13;communications;radioprompt;own
0:04:32;communications;radioprompt;other
0:04:00;resman;tank-a-lossperminute;566
0:04:00;resman;tank-b-lossperminute;566

# Block n° 6. Technical load = 57.8 %
0:05:00;track;targetproportion;0.42222222222222217
0:05:08;sysmon;lights-1-failure;True
0:05:20;sysmon;lights-1-failure;True
0:05:35;sysmon;lights-2-failure;True
0:05:02;sysmon;scales-1-failure;True
0:05:30;sysmon;scales-4-failure;True
0:05:43;sysmon;scales-3-failure;True
0:05:09;communications;radioprompt;own
0:05:24;communications;radioprompt;other
0:05:00;resman;tank-a-lossperminute;693
0:05:00;resman;tank-b-lossperminute;693

# Block n° 7. Technical load = 68.3 %
0:06:00;track;targetproportion;0.31666666666666665
0:06:10;sysmon;lights-2-failure;True
0:06:35;sysmon;lights-1-failure;True
0:06:49;sysmon;lights-1-failure;True
0:06:16;sysmon;scales-2-failure;True
0:06:31;sysmon;scales-4-failure;True
0:06:45;sysmon;scales-1-failure;True
0:06:16;communications;radioprompt;own
0:06:31;communications;radioprompt;other
0:06:00;resman;tank-a-lossperminute;820
0:06:00;resman;tank-b-lossperminute;820

# Block n° 8. Technical load = 78.9 %
0:07:00;track;targetproportion;0.21111111111111103
0:07:04;sysmon;lights-2-failure;True
0:07:17;sysmon;lights-1-failure;True
0:07:32;sysmon;lights-1-failure;True
0:07:45;sysmon;lights-2-failure;True
0:07:04;sysmon;scales-4-failure;True
0:07:18;sysmon;scales-3-failure;True
0:07:37;sysmon;scales-1-failure;True
0:07:49;sysmon;scales-2-failure;True
0:07:10;communications;radioprompt;other
0:07:25;communications;radioprompt;own
0:07:41;communications;radioprompt;own
0:07:00;resman;tank-a-lossperminute;946
0:07:00;resman;tank-b-lossperminute;946

# Block n° 9. Technical load = 89.4 %
0:08:00;track;targetproportion;0.10555555555555551
0:08:09;sysmon;lights-2-failure;True
0:08:23;sysmon;lights-1-failure;True
0:08:36;sysmon;lights-2-failure;True
0:08:48;sysmon;lights-1-failure;True
0:08:02;sysmon;scales-1-failure;True
0:08:18;sysmon;scales-3-failure;True
0:08:30;sysmon;scales-4-failure;True
0:08:46;sysmon;scales-2-failure;True
0:08:07;communications;radioprompt;other
0:08:28;communications;radioprompt;other
0:08:45;communications;radioprompt;own
0:08:00;resman;tank-a-lossperminute;1073
0:08:00;resman;tank-b-lossperminute;1073

# Block n° 10. Technical load = 100.0 %
0:09:00;track;targetproportion;0.0
0:09:00;sysmon;lights-1-failure;True
0:09:12;sysmon;lights-1-failure;True
0:09:25;sysmon;lights-2-failure;True
0:09:37;sysmon;lights-2-failure;True
0:09:48;sysmon;lights-1-failure;True
0:09:01;sysmon;scales-1-failure;True
0:09:12;sysmon;scales-1-failure;True
0:09:25;sysmon;scales-3-failure;True
0:09:38;sysmon;scales-2-failure;True
0:09:49;sysmon;scales-4-failure;True
0:09:00;communications;radioprompt;other
0:09:15;communications;radioprompt;own
0:09:30;communications;radioprompt;own
0:09:45;communications;radioprompt;other
0:09:00;resman;tank-a-lossperminute;1200
0:09:00;resman;tank-b-lossperminute;1200
0:10:00;resman;stop
0:10:00;track;stop
0:10:00;sysmon;stop
0:10:00;communications;stop
"""


def test_matbii_generate_random_xml_with_text_file(tmp_path):
    # Write the provided text to a temporary file
    tmp_file = tmp_path / "text.txt"
    with open(tmp_file, "w") as f:
        f.write(_TEXT_FILE_CONTENTS)

    # Generate the XML
    xml_string, n_task_types, n_event_times = matbii_generate_random_xml_with_text_file(
        tmp_file
    )

    # Parse the XML string
    root = fromstring(xml_string)

    # Check that the root element is 'MATB-EVENTS'
    assert root.tag == "MATB-EVENTS"

    # Check that each child element has the correct tag and attributes
    task_times = []
    for child in root:
        assert child.tag == "event"
        assert "startTime" in child.attrib
        task_time = str(child.attrib["startTime"])
        task_times.append(task_time)

    assert "00:09:45" in task_times


def test_remove_sysmon_events():
    # Create a simple XML structure with some 'sysmon' events
    root = Element("MATB-EVENTS")
    event1 = SubElement(root, "event", startTime="00:01:00")
    SubElement(event1, "sysmon")
    event2 = SubElement(root, "event", startTime="00:02:00")
    SubElement(event2, "communications")
    event3 = SubElement(root, "event", startTime="00:03:00")
    SubElement(event3, "sysmon")

    # Call the function
    root = _remove_events(root, "sysmon")

    # Check that all 'sysmon' events have been removed
    for event in root:
        assert "sysmon" not in (child.tag for child in event)

    # Also check that the 'communications' event is still there
    assert any("communications" in (child.tag for child in event) for event in root)


def test_convert_communications_to_xml():
    xml = convert_communications_to_xml("00:02:02", "own")
    xml_str = tostring(xml, encoding="unicode")
    expected_start = '<event startTime="00:02:02">'
    expected_comm = "<comm>"
    expected_ship = "<ship>OWN</ship>"
    assert expected_start in xml_str
    assert expected_comm in xml_str
    assert expected_ship in xml_str


def test_convert_sysmon_scales_to_xml():
    xml = convert_sysmon_scales_to_xml("00:02:41", "scales-1-failure")
    xml_str = tostring(xml, encoding="unicode")

    expected_start = '<event startTime="00:02:41">'
    expected_sysmon = "<sysmon>"
    expected_scale_number = "<monitoringScaleNumber>ONE</monitoringScaleNumber>"
    assert expected_start in xml_str
    assert expected_sysmon in xml_str
    assert expected_scale_number in xml_str


def test_convert_sysmon_lights_to_xml():
    xml = convert_sysmon_lights_to_xml("00:02:39", "lights-1-failure")
    xml_str = tostring(xml, encoding="unicode")
    expected_start = '<event startTime="00:02:39">'
    expected_sysmon = '<sysmon activity="START">'
    expected_light_type = "<monitoringLightType>GREEN</monitoringLightType>"
    assert expected_start in xml_str
    assert expected_sysmon in xml_str
    assert expected_light_type in xml_str
