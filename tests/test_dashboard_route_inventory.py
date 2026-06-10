from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "adapters" / "hermes" / "dashboard_route_inventory.py"
SPEC = importlib.util.spec_from_file_location("dashboard_route_inventory", MODULE_PATH)
assert SPEC is not None
dashboard_route_inventory = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["dashboard_route_inventory"] = dashboard_route_inventory
SPEC.loader.exec_module(dashboard_route_inventory)


class DashboardRouteInventoryTest(unittest.TestCase):
    def test_extracts_and_classifies_routes(self) -> None:
        source = '''
@router.get("/board")
def board():
    pass

@router.patch("/tasks/{task_id}")
def update_task():
    pass

@router.post("/dispatch")
def dispatch():
    pass

@router.post("/tasks")
def create_task():
    pass

@router.post("/tasks/{task_id}/attachments")
def upload_attachment():
    pass

@router.delete("/attachments/{attachment_id}")
def delete_attachment():
    pass

@router.delete("/tasks/{task_id}")
def delete_task():
    pass

@router.post("/tasks/bulk")
def bulk_update():
    pass

@router.post("/tasks/{task_id}/reassign")
def reassign_task():
    pass

@router.post("/tasks/{task_id}/reclaim")
def reclaim_task():
    pass

@router.post("/runs/{run_id}/terminate")
def terminate_run():
    pass

@router.post("/tasks/{task_id}/specify")
def specify_task():
    pass

@router.post("/tasks/{task_id}/decompose")
def decompose_task():
    pass

@router.post("/tasks/{task_id}/comments")
def add_comment():
    pass

@router.post("/tasks/{task_id}/home-subscribe/{platform}")
def subscribe_home():
    pass

@router.delete("/tasks/{task_id}/home-subscribe/{platform}")
def unsubscribe_home():
    pass

@router.post("/links")
def add_link():
    pass

@router.delete("/links")
def delete_link():
    pass

@router.patch("/profiles/{profile_name}")
def update_profile_description():
    pass

@router.post("/profiles/{profile_name}/describe-auto")
def auto_describe_profile():
    pass

@router.put("/orchestration")
def set_orchestration_settings():
    pass
'''
        routes = [dashboard_route_inventory.classify_route(route) for route in dashboard_route_inventory.extract_routes(source)]

        self.assertEqual(len(routes), 21)
        self.assertEqual(routes[0]["parity_status"], "not_required_read_only")
        self.assertEqual(routes[1]["parity_status"], "covered_for_ready_and_done_status")
        self.assertEqual(routes[2]["parity_status"], "covered_for_dispatch_route_mechanics")
        self.assertEqual(routes[3]["parity_status"], "covered_for_create_before_ready")
        self.assertEqual(routes[4]["parity_status"], "covered_for_attachment_route_safety")
        self.assertEqual(routes[5]["parity_status"], "covered_for_attachment_route_safety")
        self.assertEqual(routes[6]["parity_status"], "covered_for_delete_guard")
        self.assertEqual(routes[7]["parity_status"], "covered_for_ready_done_and_archive_guard")
        self.assertEqual(routes[8]["parity_status"], "covered_for_reassign_route_guard")
        self.assertEqual(routes[9]["parity_status"], "covered_for_reclaim_terminate_guard")
        self.assertEqual(routes[10]["parity_status"], "covered_for_reclaim_terminate_guard")
        self.assertEqual(routes[11]["parity_status"], "covered_for_specify_route_guard")
        self.assertEqual(routes[12]["parity_status"], "covered_for_decompose_route_guard")
        self.assertEqual(routes[13]["parity_status"], "covered_for_comments_append_only")
        self.assertEqual(routes[14]["parity_status"], "covered_for_home_subscribe_visibility_only")
        self.assertEqual(routes[15]["parity_status"], "covered_for_home_subscribe_visibility_only")
        self.assertEqual(routes[16]["parity_status"], "covered_for_dependency_link_guard")
        self.assertEqual(routes[17]["parity_status"], "covered_for_dependency_link_guard")
        self.assertEqual(routes[18]["parity_status"], "covered_for_profile_routes_operational_safety")
        self.assertEqual(routes[19]["parity_status"], "covered_for_profile_routes_operational_safety")
        self.assertEqual(routes[20]["parity_status"], "covered_for_orchestration_route_operational_safety")


if __name__ == "__main__":
    unittest.main()
