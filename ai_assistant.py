"""
AI 辅助模块
使用 Mimo API 将自然语言解析为任务或计划表，通过 PomodoroTimer 的 User API 创建。

工作流程：
    1. preview(user_input) → 调用 AI 解析，返回预览结果（不创建任何东西）
    2. 前端展示预览，用户确认
    3. confirm(preview_result) → 调用 user.create_task / create_focus_plan 创建

API Key：默认从 ~/.deepseek_key 文件读取（纯文本，只存 key 本身）
模型：固定使用 mimo-v2.5-pro
零外部依赖：只使用 Python 标准库 (urllib.request + json)
"""

import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta

# 固定模型，不允许修改
_MODEL = "mimo-v2.5-pro"


def load_api_key(key_path: Optional[Path] = None) -> str:
    """从文件读取 Mimo API Key；默认读取 ~/.deepseek_key"""
    path = key_path or Path.home() / ".deepseek_key"
    if not path.exists():
        raise FileNotFoundError(
            f"API Key 文件不存在: {path}\n"
            "请创建该文件并将 Mimo API Key 写入（纯文本，只写 key 本身）"
        )
    return path.read_text(encoding="utf-8").strip()


# ============================================================
# System Prompt — 指导 Mimo 输出结构化 JSON
# ============================================================

def _build_system_prompt() -> str:
    """构建 system prompt，注入当前日期时间和解析规则"""
    now = datetime.now()
    weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    today_str = now.strftime("%Y-%m-%d")
    today_weekday = weekday_names[now.weekday()]
    next_monday = (now + timedelta(days=(7 - now.weekday()))).strftime("%Y-%m-%d")

    return f"""你是时间管理助手，以对话框形式与用户交流。当前日期：{today_str}（{today_weekday}），当前时间：{now.strftime("%H:%M")}。下周一开始于 {next_monday}。

根据用户输入，判断意图并输出 JSON。所有输出必须包含一个友好的对话回复（reply 字段），让用户感觉在和一个助手聊天。

## 输出格式
统一使用以下 JSON 格式，type 区分意图：

### type="tasks" — 创建任务
{{
  "reply": "友好的对话回复，说明你帮用户创建了什么任务，包含关键信息（标题、时间、优先级等）",
  "type": "tasks",
  "summary": "简短摘要",
  "data": {{
    "tasks": [
      {{
        "title": "任务标题",
        "description": "可选描述",
        "due_date": "ISO格式日期时间或null",
        "importance": "LOW|MEDIUM|HIGH|CRITICAL",
        "planned_minutes": 数字,
        "mode": "POMODORO|COUNTDOWN|COUNTUP"
      }}
    ]
  }}
}}

### type="focus_plan" — 创建计划表
{{
  "reply": "友好的对话回复，说明你帮用户创建了什么计划（标题、日期范围、每天时长等）",
  "type": "focus_plan",
  "summary": "简短摘要",
  "data": {{
    "title": "计划标题",
    "start_date": "YYYY-MM-DD",
    "end_date": "YYYY-MM-DD",
    "daily_focus_minutes": 数字,
    "selected_dates": ["YYYY-MM-DD", ...]
  }}
}}

### type="chat" — 纯对话（用户只是聊天、问候、咨询，不需要创建任务/计划）
{{
  "reply": "友好的聊天回复",
  "type": "chat",
  "summary": "",
  "data": {{}}
}}

### type="error" — 输入太模糊
{{
  "reply": "友好的提示，引导用户补充更多信息（如标题、时间、时长等）",
  "type": "error",
  "summary": "错误原因",
  "data": {{}}
}}

## 对话风格
- 热情、简洁、有亲和力（2-4句话即可）
- 确认任务时列出关键信息：标题、截止时间、优先级、预计时长
- 创建计划时说明起止日期和每天目标
- 纯聊天时简短友好地回应，并提示用户可以做什么
- 模糊输入时不要拒绝用户，而是引导补充信息

## 解析规则
- 相对日期：今天={today_str}，明天={today_str}+1天，后天={today_str}+2天，下周一={next_monday}
- 本周=周一到周日，下周=下周一到下周日
- 上午默认9:00，下午默认14:00，晚上默认19:00
- importance 默认 MEDIUM；提到"紧急/赶紧"→CRITICAL，"重要/很重要"→HIGH，"顺便/有空/不急"→LOW
- mode 默认 POMODORO；提到"倒计时/计时XX分钟"→COUNTDOWN，"正计时/正向/不限时"→COUNTUP
- planned_minutes：提取数字；未提及时默认25（单任务）或从描述推断
- due_date：明确提到截止时间才设置，否则为 null
- "每隔几天/每天/每周几+持续一段时间"→优先使用 focus_plan
- 问候、感谢、问功能→type="chat"

## 严格要求
- 只输出 JSON，不要 markdown 代码块，不要 ``` 包裹
- reply 字段必须有实质内容，不能为空
- 字段名必须完全匹配上述格式"""


# ============================================================
# AIParser — 底层 Mimo API 调用
# ============================================================

class AIParser:
    """调用 Mimo API 解析自然语言（模型固定为 mimo-v2.5-pro）"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.xiaomimimo.com/v1",
        timeout: int = 30,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def parse(self, user_input: str) -> dict:
        """
        解析用户自然语言输入
        Returns:
            {"type": "tasks"|"focus_plan"|"error", "summary": "...", "data": {...}}
            或网络错误时: {"type": "error", "summary": "网络错误: ...", "data": {}}
        """
        if not user_input or not user_input.strip():
            return {"type": "error", "summary": "输入为空", "data": {}}

        system_prompt = _build_system_prompt()
        request_body = json.dumps({
            "model": _MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input.strip()},
            ],
            "temperature": 0.1,
            "max_tokens": 1024,
        }, ensure_ascii=False).encode("utf-8")

        try:
            req = urllib.request.Request(
                url=f"{self.base_url}/chat/completions",
                data=request_body,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                body = json.loads(response.read().decode("utf-8"))

            content = body["choices"][0]["message"]["content"].strip()

            # 清理可能出现的 markdown 代码块包裹
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

            result = json.loads(content)
            return result

        except urllib.error.URLError as e:
            return {"type": "error", "summary": f"网络错误: {e.reason}", "data": {}}
        except urllib.error.HTTPError as e:
            return {"type": "error", "summary": f"API 错误 ({e.code})", "data": {}}
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            return {"type": "error", "summary": f"解析响应失败: {e}", "data": {}}


# ============================================================
# AIAssistant — 高层编排
# ============================================================

class AIAssistant:
    """
    AI 辅助助手
    工作流程：preview → 前端展示 → confirm

    api_key 默认从 ~/.deepseek_key（Mimo API Key）自动读取；也可显式传入
    """

    def __init__(self, user: "User", api_key: Optional[str] = None):  # noqa: F821
        if api_key is None:
            api_key = load_api_key()
        self.parser = AIParser(api_key=api_key)
        self.user = user

    def chat(self, user_input: str) -> dict:
        """
        对话框式交互：AI 解析输入并返回对话回复 + 结构化数据
        如果是 tasks/focus_plan 类型，自动调用 confirm 创建
        Returns:
            {"reply": "...", "type": "tasks"|"focus_plan"|"chat"|"error", "data": {...}, "created": ...}
        """
        result = self.parser.parse(user_input)
        result_type = result.get("type")

        if result_type in ("tasks", "focus_plan"):
            confirmed = self.confirm(result)
            result["created"] = confirmed.get("created")
            if confirmed.get("type") == "error":
                result["type"] = "error"
                result["reply"] = f"解析成功但创建失败：{confirmed.get('summary', '')}"
        return result

    def preview(self, user_input: str) -> dict:
        """
        仅预览：AI 解析用户输入，返回对话回复 + 结构化数据，不创建任何对象
        Returns:
            {"reply": "...", "type": "tasks"|"focus_plan"|"chat"|"error", "data": {...}}
        """
        return self.parser.parse(user_input)

    def confirm(self, preview_result: dict) -> dict:
        """
        根据预览结果创建 Task 或 FocusPlan
        Args:
            preview_result: preview() 返回的字典
        Returns:
            创建成功时返回 {"type": ..., "created": ...}
            失败时返回 {"type": "error", "summary": "..."}
        """
        result_type = preview_result.get("type")
        data = preview_result.get("data", {})

        if result_type == "tasks":
            tasks_data = data.get("tasks", [])
            if not tasks_data:
                return {"type": "error", "summary": "预览数据中没有任务"}

            # 将 AI 返回的字段映射到 create_tasks_from_arrangements 参数
            arrangements = []
            for t in tasks_data:
                item = {
                    "title": t.get("title", "未命名任务"),
                    "description": t.get("description", ""),
                    "planned_minutes": float(t.get("planned_minutes", 25.0)),
                }
                # 解析 mode
                mode_str = t.get("mode", "POMODORO").upper()
                item["mode"] = mode_str
                # 解析 importance
                importance_str = t.get("importance", "MEDIUM").upper()
                item["importance"] = importance_str
                # 解析 due_date
                due_str = t.get("due_date")
                if due_str and due_str != "null":
                    item["due_date"] = due_str
                else:
                    item["due_date"] = None
                arrangements.append(item)

            from PomodoroTimer import User
            created_tasks = self.user.create_tasks_from_arrangements(arrangements)
            return {
                "type": "tasks",
                "summary": preview_result.get("summary", ""),
                "created": [t.to_dict() for t in created_tasks],
            }

        elif result_type == "focus_plan":
            try:
                from PomodoroTimer import User
                plan = self.user.create_focus_plan(
                    title=data.get("title", "未命名计划"),
                    start_date=data["start_date"],
                    end_date=data["end_date"],
                    daily_focus_minutes=float(data.get("daily_focus_minutes", 60)),
                    selected_dates=data.get("selected_dates"),
                )
                return {
                    "type": "focus_plan",
                    "summary": preview_result.get("summary", ""),
                    "created": plan.to_dict(),
                }
            except (KeyError, ValueError) as e:
                return {"type": "error", "summary": f"创建计划失败: {e}"}

        else:
            return preview_result  # 透传 error


# ============================================================
# 测试入口
# ============================================================

if __name__ == "__main__":
    from PomodoroTimer import UserManager

    try:
        api_key = load_api_key()
    except FileNotFoundError as e:
        print(e)
        exit(1)

    manager = UserManager()
    user = manager.create_user("AI测试用户")
    assistant = AIAssistant(user=user, api_key=api_key)

    print("=" * 60)
    print("AI 对话框模式测试")
    print("=" * 60)

    # 模拟对话
    test_inputs = [
        "你好！你能帮我做什么？",
        "明天下午3点前完成实验报告，很重要，预计90分钟",
        "下周一三五每天复习2小时",
        "谢谢你！",
    ]

    for user_input in test_inputs:
        print(f"\n{'─' * 50}")
        print(f"用户: {user_input}")
        result = assistant.chat(user_input)
        print(f"助手: {result.get('reply', '(无回复)')}")
        if result.get("created"):
            print(f"  [已创建: {result['type']}]")
            created = result["created"]
            if isinstance(created, list):
                for item in created:
                    print(f"    - [{item.get('task_id')}] {item.get('title')}")
            elif isinstance(created, dict):
                print(f"    - 计划: {created.get('title')}")
        print()

    # 验证持久化
    print(f"{'─' * 50}")
    print("重新加载用户，验证数据持久化...")
    user2 = manager.create_user("AI测试用户")
    print(f"  任务: {len(user2.calendar.tasks)} 个, 计划: {len(user2.focus_plans)} 个")
    for t in user2.calendar.tasks:
        print(f"    [{t.task_id}] {t.title}")
    for p in user2.focus_plans:
        print(f"    [计划{p.plan_id}] {p.title}")

    print(f"\n{'=' * 60}")
    print("测试完成")
    print("=" * 60)
