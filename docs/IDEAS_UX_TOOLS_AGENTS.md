# Ideas: Tools & Agents to Improve UX

All items have been implemented. This doc is kept for reference.

---

## Done

1. **Schedule from chat** – Flo: `list_schedules`, `create_schedule`, `delete_schedule` (`tools/schedule_tools.py`).
2. **My work / activity summary** – `get_my_work_summary()` in `workflow_tools.py`.
3. **Re-run / clone run** – `rerun_workflow(run_id)` + **Run again** button on run detail page.
4. **Workflow run summary** – `get_workflow_run_summary(run_id)` in `workflow_tools.py`.
5. **Scheduler / schedule assistant** – `update_schedule`, `set_schedule_active` in `schedule_tools.py`.
6. **Search runs / tasks** – `search_workflow_runs(...)`, `search_tasks(...)` in `workflow_tools.py`.
7. **Bulk run workflow** – `bulk_run_workflow(workflow_id, list_of_inputs, max_runs=20)` in `workflow_tools.py`.
8. **Notification preferences** – `UserPreference.notification_preferences` (migration 0028); `get_notification_preferences`, `set_notification_preferences` in `tools/notification_preferences_tools.py`.
9. **Health / status tool** – `get_workflow_system_status()` in `workflow_tools.py`.
10. **Guided workflow start** – Flo instructions: ask for each required input one by one, then confirm and execute.
