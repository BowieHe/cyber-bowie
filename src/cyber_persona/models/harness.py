"""Harness evaluation schema for LLM-as-a-Judge nodes."""

from typing import Literal
from pydantic import BaseModel, Field


class HarnessEvaluation(BaseModel):
    """Structured output schema for Harness quality control gates.

    All Harness nodes must bind to this schema via
    `llm.with_structured_output(HarnessEvaluation)` to guarantee
    routable, machine-readable verdicts.
    """

    status: Literal["PASSED", "NEEDS_RETRY", "PARTIAL_ACCEPT"] = Field(
        description="评估结果枚举值，必须是以下三个之一：'PASSED', 'NEEDS_RETRY', 'PARTIAL_ACCEPT'"
    )
    reasoning: str = Field(
        description="一步步思考的逻辑过程，解释为什么给出该 status。"
    )
    correction_directive: str | None = Field(
        default=None,
        description="如果 status 为 NEEDS_RETRY，这里必须写明针对被评估节点的明确修改指令。如果通过则为空。"
    )
    missing_information: str | None = Field(
        default=None,
        description="如果 status 为 PARTIAL_ACCEPT，这里必须总结出当前全网无法搜到/系统缺失的核心信息盲区。供下游环节进行风险提示。"
    )
