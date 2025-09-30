#!/usr/bin/env python
"""Test generator resolution."""

import json
from utils.enhanced_xml_generator import EnhancedXMLGenerator

config_path = 'resource/test_JSON_for_test_xsd/1_xsd_travel_booking_business_config.json'
xsd_path = 'resource/test_xsd/1_test.xsd'

with open(config_path) as f:
    config = json.load(f)

gen = EnhancedXMLGenerator(xsd_path, config)
result = gen.generate_xml()

print("Generated XML:")
print("=" * 70)
print(result.xml_content)
print("=" * 70)
print(f"\nXML length: {len(result.xml_content)} characters")