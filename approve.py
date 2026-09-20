#!/usr/bin/env python3
"""Decide Antigravity PreToolUse requests from stdin."""

import json
import os
import re
import shlex
import sys
from datetime import datetime

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(CURRENT_DIR, 'config.json')
MANAGE_PATH = '~/.gemini/config/plugins/auto-approver/manage.py'


def load_config():
    try:
        with open(CONFIG_FILE, encoding='utf-8') as f:
            config = json.load(f)
        if (not isinstance(config, dict) or config.get('mode') not in ('safe', 'all', 'off')
                or config.get('highRiskAction') not in ('ask', 'deny')
                or not isinstance(config.get('alwaysAllowTools'), list)
                or not all(isinstance(t, str) for t in config['alwaysAllowTools'])
                or not isinstance(config.get('dangerousPatterns'), list)
                or not all(isinstance(p, str) for p in config['dangerousPatterns'])
                or not isinstance(config.get('enableAuditLog'), bool)
                or not isinstance(config.get('logFile'), str)
                or not config['logFile']):
            return None
        for pattern in config['dangerousPatterns']:
            re.compile(pattern)
        return config
    except (OSError, ValueError, TypeError, re.error):
        return None


def log_path(config):
    path = config['logFile'] if config else 'auto-approver.log'
    return path if os.path.isabs(path) else os.path.join(CURRENT_DIR, path)


def write_audit_log(config, tool_name, decision, reason):
    if config is not None and not config['enableAuditLog']:
        return
    try:
        path = log_path(config)
        # Avoid echoing untrusted tool names, commands, paths or payloads into the log.
        tool = 'run_command' if tool_name == 'run_command' else 'listed_tool' if config and tool_name in config['alwaysAllowTools'] else 'unknown'
        line = '[{}] [{}] tool={} reason={}\n'.format(
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'), decision.upper(), tool, reason)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, 'O_NOFOLLOW', 0), 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(line)
    except OSError:
        pass


def is_management_command(cmd):
    try:
        parts = shlex.split(cmd)
    except ValueError:
        return False
    if len(parts) not in (3, 4) or parts[0] != 'python3':
        return False
    # shlex splits words but accepts shell operators as ordinary tokens.
    if re.search(r'[;&|`$<>\\\n\r]', cmd) or any(c in cmd for c in ('*', '?', '[', ']', '{', '}', '(', ')')):
        return False
    if parts[1] not in (MANAGE_PATH, os.path.join(CURRENT_DIR, 'manage.py')):
        return False
    if parts[2] == 'mode':
        return len(parts) == 4 and parts[3] in ('safe', 'all', 'off')
    if parts[2] == 'status':
        return len(parts) == 3
    if parts[2] == 'log':
        return (len(parts) == 3 or len(parts) == 4 and parts[3].isdigit())
    return False


def decide(config, payload):
    if config is None:
        return 'ask', 'Invalid configuration', ''
    if not isinstance(payload, dict) or not isinstance(payload.get('toolCall'), dict):
        return 'ask', 'Invalid tool call', ''
    call = payload['toolCall']
    tool = call.get('name')
    args = call.get('args')
    if not isinstance(tool, str) or not tool or not isinstance(args, dict):
        return 'ask', 'Invalid tool call', ''
    if tool == 'run_command':
        cmd = args.get('CommandLine')
        if not isinstance(cmd, str) or not cmd.strip():
            return 'ask', 'Missing command', tool
        if is_management_command(cmd):
            return 'allow', 'Management command', tool
    if config['mode'] == 'off':
        return 'ask', 'Auto-approval disabled', tool
    if config['mode'] == 'all':
        return 'allow', 'All mode', tool
    if tool == 'run_command':
        if any(re.search(p, cmd, re.IGNORECASE) for p in config['dangerousPatterns']):
            return config['highRiskAction'], 'High-risk command', tool
        if re.search(r'[;&|`$<>\\\n\r]', cmd) or any(c in cmd for c in ('*', '?', '[', ']', '{', '}', '(', ')')):
            return 'ask', 'Complex command', tool
        # ponytail: simple text checks cannot parse aliases or other shell expansions;
        # use a real parser or executable allowlist if those become a requirement.
        return 'allow', 'Command passed heuristic check', tool
    if tool in config['alwaysAllowTools']:
        return 'allow', 'Listed tool', tool
    return 'ask', 'Unlisted tool', tool


def main():
    config = load_config()
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else None
    except ValueError:
        payload = None
    decision, reason, tool = decide(config, payload)
    write_audit_log(config, tool, decision, reason)
    print(json.dumps({'decision': decision, 'reason': reason}))


if __name__ == '__main__':
    main()
