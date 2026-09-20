# agy-auto-approver

Antigravity CLI (`agy`) 的 `PreToolUse` 审批插件。只使用 Python 3.8+ 标准库。

## 安装

```bash
./install.sh
```

脚本执行 `agy plugin install` 并检查插件列表，**不会修改** `~/.gemini/antigravity-cli/settings.json`。直接使用 `agy plugin install <插件目录>` 也可以。`hooks.json` 和下面的管理命令采用 `~/.gemini/config/plugins/auto-approver/` 路径；如 `agy` 安装到了其他目录，需按实际路径调整钩子和管理命令。具体信任目录及命令权限由 `agy` 决定，如需配置，先由用户检查并确认；插件不会自行授予权限。请用本机 `agy plugin validate` 验证安装兼容性；此仓库不保证所有 `agy` 版本的插件格式。

## 模式

| 模式 | 行为 |
| --- | --- |
| `safe`（默认） | 配置中的工具自动放行；命令通过正则检查后放行，命中高危规则时 `ask`（或配置为 `deny`）；未知工具、缺失命令和复杂 shell 语句需人工确认。 |
| `all` | 合法工具调用全部放行，包括危险命令。仅用于明确可信的环境。 |
| `off` | 普通工具调用全部人工确认；独立的合法管理命令可切换模式。 |

空输入、损坏的 JSON、无效配置和不完整的工具调用均返回 `ask`。正则规则只是启发式提示，**不能作为 shell 命令的安全边界**：别名、间接执行、特殊 shell 语法和未列出的危险命令仍可能漏检。使用 `safe` 时也应保留 `agy` 自身的权限和隔离措施。

## 管理

```bash
python3 ~/.gemini/config/plugins/auto-approver/manage.py status
python3 ~/.gemini/config/plugins/auto-approver/manage.py mode safe
python3 ~/.gemini/config/plugins/auto-approver/manage.py mode all
python3 ~/.gemini/config/plugins/auto-approver/manage.py mode off
python3 ~/.gemini/config/plugins/auto-approver/manage.py log 10
```

`/approver` 技能可指导 Agent 调用同一管理脚本，但须遵循 `agy` 的权限确认。修改模式后，下一次工具调用会重新加载 `config.json`。`mode` 只接受 `safe/all/off`；`highRiskAction` 只接受 `ask/deny`。`alwaysAllowTools` 仅控制非命令工具的自动放行；未知工具需确认。`dangerousPatterns` 使用 Python 正则。配置文件缺失、损坏或规则无效时不会自动放行。

## 审计与隐私

默认开启审计，`config.json` 的 `enableAuditLog` 可关闭；相对 `logFile` 路径以插件目录为基准，管理脚本也读取此路径。新建日志以当前用户可读写权限 `0600` 创建；已有文件权限不会自动改变。记录时间、审批决定、工具类别和固定理由，不保存命令文本、参数或文件路径，例如：

```text
[2026-09-20 12:35:10] [ALLOW] tool=run_command reason=Command passed heuristic check
[2026-09-20 12:35:15] [ASK] tool=unknown reason=Unlisted tool
```

旧版本日志可能包含完整命令、路径、密钥等敏感信息；升级不会自动删除或清理既有日志，请自行检查并安全处理。默认 `*.log` 被 `.gitignore` 忽略；若把 `logFile` 改成其他扩展名或仓库外路径，请自行确保不会提交或共享该文件。管理命令的输出只包含决定和理由，不附带动态 `permissionOverrides`。

## 文件

`approve.py` 审批钩子；`config.json` 可编辑策略；`manage.py` 模式与日志管理；`hooks.json` 钩子声明；`install.sh` 安装入口。运行本地回归检查：

```bash
python3 -m unittest test_approver
bash -n install.sh
```

MIT License，详见 [LICENSE](LICENSE)。
