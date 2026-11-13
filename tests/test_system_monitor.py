#!/usr/bin/env python3
"""
Unit tests for app.system_monitor and combined monitoring endpoints.
Verifies Approach 1 (Application-level pipeline heartbeat) and
Approach 2 (System-level host services watcher).
"""

import os
import json
import sqlite3
import unittest
from pathlib import Path

from app.system_monitor import (
    get_host_services_status,
    get_pipeline_tasks_status,
    get_combined_agent_status,
    check_tcp_port,
    check_pid_alive,
    SCHEDULED_TALENTS,
    DB_PATH
)

class TestSystemMonitor(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(f"file:{DB_PATH.resolve()}?mode=ro", uri=True)
        self.conn.row_factory = sqlite3.Row

    def tearDown(self):
        self.conn.close()

    def test_scheduled_talents_contains_four_core_characters(self):
        char_ids = [t["id"] for t in SCHEDULED_TALENTS]
        self.assertIn("dinda", char_ids)
        self.assertIn("isk", char_ids)
        self.assertIn("bang_ray", char_ids)
        self.assertIn("pak_vincent", char_ids)

    def test_pipeline_tasks_status_returns_all_characters(self):
        tasks = get_pipeline_tasks_status(self.conn, target_date="2026-11-13")
        self.assertEqual(len(tasks), 4)
        cids = [t["character_id"] for t in tasks]
        self.assertListEqual(cids, ["dinda", "isk", "bang_ray", "pak_vincent"])

        for t in tasks:
            # Verify 5 stages structure
            self.assertEqual(len(t["stages"]), 5)
            stage_nums = [s["num"] for s in t["stages"]]
            self.assertEqual(stage_nums, [1, 2, 3, 4, 5])
            
            # Verify progress bounds
            self.assertGreaterEqual(t["progress_percent"], 0)
            self.assertLessEqual(t["progress_percent"], 100)

            # Verify target duration is within 10s-18s policy
            self.assertGreaterEqual(t["target_duration"], 10)
            self.assertLessEqual(t["target_duration"], 18)

            # Verify presence of headline status
            self.assertTrue(bool(t["headline_status"]))

    def test_host_services_status_structure(self):
        res = get_host_services_status()
        self.assertIn("environment", res)
        self.assertIn("host_metrics", res)
        self.assertIn("services", res)

        metrics = res["host_metrics"]
        self.assertIn("chip", metrics)
        self.assertIn("ram_summary", metrics)
        self.assertIn("disk_free_gb", metrics)

        services = res["services"]
        service_ids = [s["id"] for s in services]
        self.assertIn("hermes_gateway", service_ids)
        self.assertIn("chrome_cdp", service_ids)
        self.assertIn("hermes_9router", service_ids)
        self.assertIn("telegram_watcher", service_ids)
        self.assertIn("dashboard_server", service_ids)

    def test_combined_agent_status_response(self):
        res = get_combined_agent_status(self.conn)
        self.assertEqual(res.get("status"), "success")
        self.assertIn("host_status", res)
        self.assertIn("pipeline_tasks", res)
        self.assertIn("server_time_wib", res)
        self.assertEqual(len(res["pipeline_tasks"]), 4)

    def test_check_pid_alive(self):
        # Current process should be alive
        self.assertTrue(check_pid_alive(os.getpid()))
        # Non-existent or invalid PID should return False
        self.assertFalse(check_pid_alive(99999999))
        self.assertFalse(check_pid_alive(None))

if __name__ == "__main__":
    unittest.main()
