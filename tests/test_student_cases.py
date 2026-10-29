"""
From IMPLEMENTATION_STEPS.md

Create tests/test_student_cases.py and add your tests. Do not add your tests to or modify the instructor-provided test files.

Use ScriptedLLM so that all three tests are deterministic. Give each test a descriptive name and assert the relevant response, trace, or termination property. 
It is not enough to just check that the code executed without an exception.

The tests must run as part of:

uv run pytest
"""
import pytest

#imports from other test files
import json

from atlas_agent.agent import run_agent

from atlas_agent.llm import ScriptedLLM
from atlas_agent.llm import OpenAICompatibleLLM

from atlas_agent.models import LabRequest
from atlas_agent.models import AgentResponse, LabRequest
from atlas_agent.models import ToolObservation, TraceEvent
from atlas_agent.agent_models import (
    ClarificationDecision,
    DecisionAdapter,
    FinalDecision,
    ToolCallDecision,
)

from atlas_agent.policy_context import ReservationContext
from atlas_agent.policy_context import build_reservation_context

from atlas_agent.prompts import SYSTEM_PROMPT, initialize_messages

from atlas_agent.validation import (
    validate_final_response,
    validate_request_binding,
    validate_reservation_preconditions,
)

#make sure tests are repeatable using ScriptedLLM
#each test needs to wire ScriptedLLM into agent look
#make assertions on kind, content of final decision, trace, and termination properties

#Test 1, an unsafe action proposal that is denied before tool execution;
def test_unsafe_action_propsal_denial_before_tool_execution():
    #set up LLM to propose ToolCallDecision for reserve resource
    #doesn't have required preconditions (maybe missing authorization/status)
    #agent should block this action

    #LabRequest -> lacks required fields
    request = LabRequest(
        authenticated_user_id="Taylor",
        #vague information from request
        text="Reserve tensile-01 for polymer-study tomorrow.",
        project_id="polymer-study",
        resource_id="tensile-01",
        #missing start and end
    )

    #scripts a LLM's JSON output
    unsafe_proposal: dict = {"kind":"tool_call", "tool":"reserve_resource", "arguments":{"resource": "centrifuge-2", "slot": "tomorrow-pm"}, 
                             "reasoning_summary":"User asked for reservation, reserving it."}
    

    #agent logic should intercept and deny tool execution
    #sanity check
    #if this fails whole test doesn't make sense
    DecisionAdapter.validate_python(unsafe_proposal)
    llm = ScriptedLLM([unsafe_proposal]) 
    agent = run_agent(request=request, llm=llm, ) #NOT FILLED CORRECTLY

    result, trace = run_agent...(request, return_trace=True) #NOT FILLED CORRECTLY

    #agent responds wiyh safe decision type -> ask for clarification or finalized explanation of refusal
    assert result.kind in ("clarification", "final"), (f"Expected clarification or final decision. Threw {result.kind!r}")

    if result.kind == "clarification":
        #needs to name what is missing
        assert result.question, "Clarification must include a question"
        assert result.missing_fields, ("Clarification needs to list the missing fields")
    else:
        #if final instead, the response needs to have refusal/error
        #not a success, there was no reserved resource
        assert not result.response.reported_success ("FinalDecision can not claim that the reservation succeeded")

    #termination reason accurately describes the blocked action
    assert result.termination_reason in (...), (f"Unexpected termination reason: {result.termination_reason!r}")
    assert ...

#Test 2, a contradictory final response that is rejected because it disagrees with the trace; and
def test_contradictory_final_response_rejection_because_of_trace_mismatch():
    #set up LLM to creat FinalDecision claiming success, but trace doesn't have a successful reserve_resource tool call

    #LLM claims reservation succeeded
    #...

    #assert agent reject contradiction in final response
    #assert result.kind == "final"
    #assert result.termination_reason == "completed_action_not_in_successful_trace"
    assert ...

#Test 3, something I make up (one additional case of your choice.)
