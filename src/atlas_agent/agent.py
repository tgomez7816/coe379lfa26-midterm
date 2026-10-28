"""Milestone 2: complete the bounded decision–action–observation loop."""

# Ruff suppressions cover names intentionally reserved for the TODOs. Remove
# this line after completing Milestone 2.
# ruff: noqa: F401, F821, F841

from __future__ import annotations

import json

from pydantic import ValidationError

from .agent_models import (
    ClarificationDecision,
    DecisionAdapter,
    FinalDecision,
    ToolCallDecision,
)
from .llm import StructuredLLM
from .models import AgentResponse, AgentRun, LabRequest, ToolObservation, TraceEvent
from .prompts import initialize_messages
from .tools import MUTATING_TOOLS, ToolEnvironment
from .validation import validate_final_response, validate_proposed_tool_call


def _failed(message: str, trace: list[TraceEvent], reason: str) -> AgentRun:
    return AgentRun(
        response=AgentResponse(status="failed", message=message),
        trace=trace,
        termination_reason=reason,
    )


def run_agent(
    request: LabRequest,
    *,
    llm: StructuredLLM,
    environment: ToolEnvironment,
    max_steps: int = 10,
) -> AgentRun:
    messages = initialize_messages(request)
    trace: list[TraceEvent] = []

    for step in range(1, max_steps + 1):
        try:
            # TODO 2.1: Ask llm for one decision validated by DecisionAdapter.
            #Call LLM with messages
            #go through and validate the decision with DecisionAdapter
            #give results to decision variable
            #make sure except block will handle failed validation
            raise NotImplementedError
        except (ValidationError, ValueError, TypeError, RuntimeError) as exc:
            return _failed(
                f"The model did not produce a valid decision: {exc}",
                trace,
                "invalid_model_decision",
            )

        if isinstance(decision, ClarificationDecision):
            # TODO 2.2: Return clarification_required without calling a tool.
            #AgentRun with status clarification required
            #current trace + clarification decision details need to be here
            #does not call a tool or continue loop
            #act as early exit for clarification requests
            raise NotImplementedError

        if isinstance(decision, FinalDecision):
            # TODO 2.3: Validate the final response. Return a failed run if it is
            # inconsistent; otherwise return the model's final response.
            #check decision's response (validate_final_response)
            #if failed, return a failed AgentRun with "invalid_final_response" reason
            #if valid, return an AgentRun with final response, trace and "final_response" reason
            raise NotImplementedError

        if not isinstance(decision, ToolCallDecision):
            return _failed(
                "Unsupported decision type.", trace, "invalid_model_decision"
            )

        # TODO 2.4: Call validate_proposed_tool_call. If it returns errors,
        # create an action_gate_denied observation. Otherwise dispatch the tool.
        #validate_proposed_tool_call checks if call is allowed
        #if errors, create an action_gate_denied observation and don't call the tool
        #if valid, dispatch the tool (environment.dispatch_tool) with tool name and arguments from decision and get the ToolObservation
        raise NotImplementedError

        # TODO 2.5: Create and append a TraceEvent. Set mutating by consulting
        # MUTATING_TOOLS rather than hard-coding one tool name.
        #make TraceEvent
        #needs ToolCallDecision, ToolObservation, current step number and MUTATING_TOOLS
        #add TraceEvent to trace list
        raise NotImplementedError

        # TODO 2.6: Append the serialized decision as an assistant message and
        # the serialized observation as a tool message.
        #serialize ToolCallDecision as assistant message
        #serialize ToolObservation as tool message
        #add both to messages list -> let's next LLM call to see result
        #json.dumps to serialize?
        raise NotImplementedError

    # TODO 2.7: Return an explicit maximum_steps_exceeded failure.
    #completed loop without returning a final response or clarification request
    #make AgentRun with status failed
    #message should say max steps exceeded
    #should have full trace
    #reason "maximum_steps_exceeded"
    raise NotImplementedError
