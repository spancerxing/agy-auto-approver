#!/usr/bin/env python3
"""Query or switch auto-approver modes and view its audit log."""

import json
import os
import sys

from approve import CONFIG_FILE, load_config, log_path


def read_config():
    config = load_config()
    if config is None:
        print('Invalid or missing config.json')
    return config


def cmd_status():
    config = read_config()
    if config is None:
        return
    print('Current Mode    : {}'.format(config['mode'].upper()))
    print('High-Risk Action: {}'.format(config['highRiskAction']))
    print('Audit Log       : {}'.format('Enabled' if config['enableAuditLog'] else 'Disabled'))
    print('Config Path     : {}'.format(CONFIG_FILE))


def cmd_mode(mode):
    if mode not in ('safe', 'all', 'off'):
        print('Supported modes: safe, all, off')
        return
    config = read_config()
    if config is None:
        return
    old_mode = config['mode']
    config['mode'] = mode
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print('Switched mode: {} -> {}'.format(old_mode, mode))
    except OSError as error:
        print('Error writing config: {}'.format(error))


def cmd_log(n=10):
    config = read_config()
    if config is None:
        return
    path = log_path(config)
    if not os.path.exists(path):
        print('No audit log found yet.')
        return
    with open(path, encoding='utf-8') as f:
        lines = f.readlines()
    print('--- Last {} audit entries ---'.format(min(n, len(lines))))
    for line in (lines[-n:] if n else []):
        print(line, end='')


def main():
    if len(sys.argv) < 2 or sys.argv[1] == 'status':
        cmd_status()
    elif sys.argv[1] == 'mode' and len(sys.argv) == 3:
        cmd_mode(sys.argv[2])
    elif sys.argv[1] == 'log' and (len(sys.argv) == 2 or len(sys.argv) == 3 and sys.argv[2].isdigit()):
        cmd_log(int(sys.argv[2]) if len(sys.argv) == 3 else 10)
    else:
        print('Usage: python3 manage.py <status|mode safe|all|off|log [n]>')


if __name__ == '__main__':
    main()
