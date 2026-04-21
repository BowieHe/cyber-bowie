"""Router node for plan-driven execution.

Reads the execution plan and execution history to decide the next step.
This is a lightweight LLM node — its decision space is constrained by the plan.
"""

import logging
from typing import Any

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from cyber_persona.engine.llm_factory import get_llm
from cyber_persona.models import AssistantState

logger = logging.getLogger(__name__)

ROUTER_PROMPT = """你是计划执行器。根据执行计划和执行历史，确认下一步节点。

## 执行计划
{plan_text}

## 当前进度
第 {current_step} 步 / 共 {total_steps} 步

## 执行历史（最近）
{execution_log}

## 可用节点说明
- chat_agent: 闲聊、简单问答
- research_orchestrator: 多源深度研究
- drafter: 撰写报告草稿
- debater_agent: 批判性辩论
- synthesizer: 输出最终答案

请只输出下一步节点名称（必须是上面可用节点之一）。"""


def router_node(llm: ChatOpenAI | None = None):
    """Factory for the router node."""
    llm_instance = get_llm(llm, temperature=0.3)

    async def _node(state: AssistantState) -> dict[str, Any]:
        plan = state.get("plan", [])
        plan_index = state.get("plan_index", 0)
        execution_log = state.get("execution_log", [])

        # Plan completed — route to END
        if plan_index >= len(plan):
            logger.info("Router: plan completed (%d/%d steps)", plan_index, len(plan))
            return {
                "next_agent": "__end__",
                "execution_log": ["router: 执行计划已完成"],
            }

        expected_step = plan[plan_index]
        logger.info(
            "Router: plan_index=%d/%d, expected_step=%s",
            plan_index,
            len(plan),
            expected_step,
        )

        # Build prompt for LLM
        plan_text = "\n".join(
            f"{i + 1}. {step}" for i, step in enumerate(plan)
        )
        log_text = "\n".join(execution_log[-8:]) if execution_log else "无"

        prompt = ROUTER_PROMPT.format(
            plan_text=plan_text,
            current_step=plan_index + 1,
            total_steps=len(plan),
            execution_log=log_text,
        )
        messages = [HumanMessage(content=prompt)]
        result = await llm_instance.ainvoke(messages)

        next_agent = result.content.strip().lower()
        # Normalize: extract known node name from response
        available = {
            "chat_agent",
            "research_orchestrator",
            "drafter",
            "debater_agent",
            "synthesizer",
        }
        matched = None
        for name in available:
            if name in next_agent:
                matched = name
                break

        if matched is None:
            # Fallback to expected step if LLM returned garbage
            logger.warning(
                "Router LLM returned unrecognized node '%s', falling back to %s",
                next_agent,
                expected_step,
            )
            matched = expected_step
        else:
            logger.info(
                "Router LLM chose %s (expected %s)",
                matched,
                expected_step,
            )

        return {
            "next_agent": matched,
            "execution_log": [
                f"router: 第 {plan_index + 1} 步，选择节点 {matched}（计划预期：{expected_step}）"
            ],
        }

    return _node
