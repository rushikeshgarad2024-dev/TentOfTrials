#!/usr/bin/env python3
import os
import sys
import unittest
from pathlib import Path

# Add tools to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from log_aggregator import (
    JSONLogParser,
    TextLogParser,
    NginxLogParser,
    LogAggregator,
)

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

class TestLogParserFixtures(unittest.TestCase):
    def setUp(self):
        self.json_parser = JSONLogParser()
        self.text_parser = TextLogParser()
        self.nginx_parser = NginxLogParser()
        self.aggregator = LogAggregator()

    def test_json_fixtures_parsing(self):
        filepath = FIXTURES_DIR / "json_logs.jsonl"
        self.assertTrue(filepath.exists(), "JSON fixture file must exist")
        with open(filepath, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        
        parsed = [self.json_parser.parse(line) for line in lines]
        self.assertEqual(len(parsed), 4)
        self.assertTrue(all(p is not None for p in parsed))
        self.assertEqual(parsed[0]["service"], "auth-service")
        self.assertEqual(parsed[0]["level"], "info")
        self.assertEqual(parsed[1]["level"], "error")
        self.assertEqual(parsed[1]["service"], "payment-api")
        self.assertEqual(parsed[2]["level"], "warn")
        self.assertEqual(parsed[3]["level"], "critical")

    def test_nginx_fixtures_parsing(self):
        filepath = FIXTURES_DIR / "nginx_logs.log"
        self.assertTrue(filepath.exists(), "Nginx fixture file must exist")
        with open(filepath, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]

        parsed = [self.nginx_parser.parse(line) for line in lines]
        self.assertEqual(len(parsed), 3)
        self.assertTrue(all(p is not None for p in parsed))
        self.assertEqual(parsed[0]["fields"]["status"], 200)
        self.assertEqual(parsed[0]["level"], "info")
        self.assertEqual(parsed[1]["fields"]["status"], 400)
        self.assertEqual(parsed[1]["level"], "warn")
        self.assertEqual(parsed[2]["fields"]["status"], 500)
        self.assertEqual(parsed[2]["level"], "error")

    def test_plaintext_fixtures_parsing(self):
        filepath = FIXTURES_DIR / "plaintext_logs.log"
        self.assertTrue(filepath.exists(), "Plaintext fixture file must exist")
        with open(filepath, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]

        parsed = [self.text_parser.parse(line) for line in lines]
        self.assertEqual(len(parsed), 4)
        self.assertTrue(all(p is not None for p in parsed))
        self.assertEqual(parsed[0]["service"], "billing")
        self.assertEqual(parsed[0]["level"], "info")
        self.assertEqual(parsed[1]["service"], "AUTH")
        self.assertEqual(parsed[1]["level"], "error")
        self.assertEqual(parsed[2]["level"], "warn")
        self.assertEqual(parsed[3]["level"], "error")

    def test_malformed_lines_graceful_handling(self):
        filepath = FIXTURES_DIR / "malformed_logs.log"
        self.assertTrue(filepath.exists(), "Malformed fixture file must exist")
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                # None of the parsers should throw an unhandled exception
                json_res = self.json_parser.parse(line)
                nginx_res = self.nginx_parser.parse(line)
                self.assertIsNone(json_res)
                self.assertIsNone(nginx_res)

    def test_aggregator_precedence_and_metrics(self):
        agg = LogAggregator()
        for fixture_file in ["json_logs.jsonl", "nginx_logs.log", "plaintext_logs.log"]:
            count = agg.process_file(str(FIXTURES_DIR / fixture_file))
            self.assertGreater(count, 0)
        
        # Verify Nginx format is preserved over generic text
        formats = [e["format"] for e in agg.entries]
        self.assertIn("nginx", formats)
        self.assertIn("json", formats)
        self.assertIn("text", formats)

if __name__ == "__main__":
    unittest.main(verbosity=2)
