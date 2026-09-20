---
name: approver
description: Manage and switch Antigravity CLI auto-approver modes (safe, all, off), check status, or view audit logs during a session. Use whenever the user asks to switch auto-approval mode, check approval status, or view approval logs.
---

# Auto-Approver In-Session Switcher

This skill allows you to switch the auto-approver mode or inspect its status in the middle of a session without restarting the CLI.

## Workflow

Use the installed management script to perform actions. Follow the CLI's permission prompts; installation does not silently grant permissions:

1. **Switch Mode**:
   Execute the management script after the user authorizes the mode change:
   ```bash
   python3 ~/.gemini/config/plugins/auto-approver/manage.py mode <safe|all|off>
   ```

2. **Check Status**:
   Execute:
   ```bash
   python3 ~/.gemini/config/plugins/auto-approver/manage.py status
   ```

3. **View Logs**:
   Execute:
   ```bash
   python3 ~/.gemini/config/plugins/auto-approver/manage.py log 10
   ```

4. **Feedback to User**:
   Briefly confirm to the user the mode that has been activated. Changes take effect on the very next tool call.
