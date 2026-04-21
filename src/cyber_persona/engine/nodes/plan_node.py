"""Plan node for generating execution plans.

Analyzes the user request and generates a linear execution plan
that the Router will follow step by step.
"""

import logging
from typing import Any

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from cyber_persona.engine.llm_factory import get_llm
from cyber_persona.models import AssistantState

logger = logging.getLogger(__name__)

PLAN_PROMPT = """你是任务规划器。根据用户请求，判断需要哪些步骤来完成任务。

可用步骤（按使用顺序排列）：
- chat_agent: 闲聊、问候、简单问答（不需要深度研究时）
- research_orchestrator: 多源深度研究（需要检索最新信息时）
- drafter: 撰写报告草稿（研究完成后）
- debater_agent: 批判性辩论（需要对草稿进行审查时）
- synthesizer: 输出最终答案（整合所有信息后）

重要规则：
1. 计划必须是线性的，一步一步执行
2. 如果用户请求需要检索信息，必须先执行 research_orchestrator
3. 如果用户只是闲聊，只需要 chat_agent
4. 不要包含不必要的步骤

用户请求：{user_query}

请直接输出步骤列表，每行一个步骤名称（只输出可用步骤中的名称）。
"""


def _parse_plan(text: str) -> list[str]:
    """Extract plan steps from LLM output.

    Expected format: one step name per line.
    """
    available = {
        "chat_agent",
        "research_orchestrator",
        "drafter",
        "debater_agent",
        "synthesizer",
    }
    steps: list[str] = []
    for line in text.strip().split("\n"):
        step = line.strip().strip("-• ").strip()
        if step in available and step not in steps:
            steps.append(step)
    return steps


def plan_node(llm: ChatOpenAI | None = None):
    """Factory for the plan node."""
    llm_instance = get_llm(llm)

    async def _node(state: AssistantState) -> dict[str, Any]:
        user_query = state.get("user_query", "")
        logger.info("PlanNode generating plan for query=%r", user_query)

        prompt = PLAN_PROMPT.format(user_query=user_query)
        messages = [HumanMessage(content=prompt)]
        result = await llm_instance.ainvoke(messages)

        plan = _parse_plan(result.content)
        if not plan:
            # Fallback: if no valid plan extracted, default to chat
            logger.warning("PlanNode failed to parse plan, defaulting to chat_agent")
            plan = ["chat_agent"]

        logger.info("PlanNode generated plan=%s", plan)
        return {
            "plan": plan,
            "plan_index": 0,
            "execution_log": [f"plan_node: 生成执行计划 {' → '.join(plan)}"],
        }

    return _node
