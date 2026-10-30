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
from atlas_agent.tools import ToolEnvironment

#make sure tests are repeatable using ScriptedLLM
#each test needs to wire ScriptedLLM into agent look
#make assertions on kind, content of final decision, trace, and termination properties

#Test 1, an unsafe action proposal that is denied before tool execution;
def test_unsafe_action_propsal_denial_before_tool_execution(environment, monkeypatch):
    #set up LLM to propose ToolCallDecision for reserve resource
    #doesn't have required preconditions
    #LabRequest -> lacks required fields
    request = LabRequest(
        authenticated_user_id="taylor",
        #vague information from request
        text="Reserve tensile-01 for polymer-study tomorrow.",
        project_id="polymer-study",
        resource_id="tensile-01",
        #missing start and end
    )

    #scripts a LLM's JSON output
    unsafe_proposal: dict = {"kind":"tool_call", "tool":"reserve_resource", "arguments":{"authenticated_user_id": "taylor", "project_id": "polymer-study",
                             "resource_id":"tensile-01", "start": "2026-10-15T10:00:00",  "end": "2026-10-15T11:00:00"},
                             "reasoning_summary":"User asked for reservation, reserving it."}

    #agent logic should intercept and deny tool execution from policy
    #sanity check
    #if this fails whole test doesn't make sense
    DecisionAdapter.validate_python(unsafe_proposal)

    #second scripted decision
    #what the agent should follow up with after seeing denial
    followup_clarification: dict = { "kind":"clarification", "question": ("What is the specific start and end time I should reserve?"), 
                                    "missing_fields": ["start", "end"]}
    llm = ScriptedLLM([unsafe_proposal, followup_clarification]) 

    #"spy" on simulator's reserve() method
    reserve_calls: list[dict] = []
    origin_reserve = environment.simulator.reserve

    def spy_reserve(**kwargs):
        reserve_calls.append(kwargs)
        return origin_reserve(**kwargs)

    monkeypatch.setattr(environment.simulator, "reserve", spy_reserve)

    #run the agent
    run = run_agent(request, llm=llm, environment=environment, max_steps=10)

    #gate should deny the call
    gated = [
        e for e in run.trace
             if e.observation.error_code == "action_gate_denied"]

    assert len(gated) == 1, (f"Expected 1 action_gate_denied event, recieved {len(gated)}. If 0 with failure, block came from argument validation or tool routing.")
    assert gated[0].decision["tool"] == "reserve_resource"
    #using MUTATING_TOOLS, not hard-coded
    assert gated[0].mutating is True

    #make sure no reserve resource observation succeeded
    executed = [
        e for e in run.trace
        if e.decision.get("tool") == "reserve_resource" and e.observation.ok
    ]
    assert executed == [], ("Unsafe reserve_resource must never execute successfully")

    #mutating was not invoked
    assert reserve_calls == [], (f"Fail: simulator.reserve was called {len(reserve_calls)} time(s) "f"with {reserve_calls!r}. The unsafe action executed.")

    #denial is given back to the model
    assert len(llm.calls) == 2, (f"Expected 2 LLM calls (proposal + post-denial turn), got {len(llm.calls)}")
    tool_msg = llm.calls[1][-1]
    assert tool_msg["role"] == "tool"
    assert "action_gate_denied" in tool_msg["content"]

    #agent responds wiyh safe decision type -> ask for clarification or finalized explanation of refusal
    assert run.termination_reason == "clarification_required"
    assert run.response.status == "clarification_required"
    #clarifying question is non-empty
    assert run.response.message  

#Test 2, a contradictory final response that is rejected because it disagrees with the trace; and
def test_contradictory_final_response_rejection_because_of_trace_mismatch(environment, monkeypatch):
    #set up LLM to creat FinalDecision claiming success, but trace doesn't have a successful reserve_resource tool call
    request = LabRequest(
            authenticated_user_id="taylor",
            #vague information from request
            text="Reserve tensile-01 for polymer-study tomorrow.",
            project_id="polymer-study",
            resource_id="tensile-01",
            #missing start and end
        )
    
    #LLM claims reservation succeeded
    liar_decision: dict = {"kind":"final", "response": {"status":"completed", "message":"Reservation confirmed", "citations":[],
                                                        "completed_actions":["reserve_resource"]}}

    #sanity check makes sure the test only fails on policy
    DecisionAdapter.validate_python(liar_decision)

    llm = ScriptedLLM([liar_decision])

    #"spy" on mutation
    reserve_calls: list[dict] = []
    origin_reserve = environment.simulator.reserve
    
    def spy_reserve(**kwargs):
        reserve_calls.append(kwargs)
        return origin_reserve(**kwargs)
    
    monkeypatch.setattr(environment.simulator, "reserve", spy_reserve)

    #run the agent
    run = run_agent(request, llm=llm, environment=environment, max_steps=10)

    #assert agent reject contradiction in final response
    assert run.termination_reason == "invalid_final_response", (f"Expected the contradictory final response to be rejected, got termination_reason={run.termination_reason!r}")
    assert run.response.status == "failed", (f"Expected failed status, got {run.response.status!r}")
    #assert result.termination_reason == "completed_action_not_in_successful_trace"
    assert "completed_action_not_in_successful_trace" in run.response.message, (f"Expected the error code in the failure message, got: {run.response.message!r}")
    assert "completed_without_successful_mutation" in run.response.message, (f"Expected the empty-mutation error code in the failure message, got: {run.response.message!r}")
    #there are no sucessful reservations
    successful_reservations = [
        e for e in run.trace
        if e.decision.get("tool") == "reserve_resource" and e.observation.ok
    ]
    assert successful_reservations == [], (
        "No successful reservation may exist in the trace — the claim "
        "had no basis in reality"
    )
    #simulator was not called
    assert reserve_calls == [], ("Fail: simulator.reserve was called {len(reserve_calls)} time(s) state changed despite the run being rejected")
    #agent rejects final
    assert len(llm.calls) == 1, (f"Expected exactly 1 LLM call, got {len(llm.calls)} and the agent should reject the contradictory final response without retrying"
    )

#Test 3, something I make up (one additional case of your choice.)
