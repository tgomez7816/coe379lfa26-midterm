"""Milestone 3: implement three selected validation responsibilities."""

from __future__ import annotations

from .agent_models import ToolCallDecision
from .models import AgentResponse, LabRequest, TraceEvent
from .policy_context import ReservationContext, build_reservation_context


def validate_request_binding(
    decision: ToolCallDecision,
    *,
    request: LabRequest,
) -> list[str]:
    """TODO 3.1: Prevent identity and resolved-field substitution."""
    #need to check fields that overlap between tool call and the trusted request
    #get values from decision.arguments and request.model_dump()
    #if any values are different, return an error message for each field
    
    del decision, request #these need to be removed after implementing!!
    return []


def validate_reservation_preconditions(context: ReservationContext) -> list[str]:
    """TODO 3.2: Return an error for every required context fact that is false."""
    #make a list of preconditon errors using boolean facts
    #esstentially: fact is false, add an error message to the list
    #follow a pattern of -> context.fact: error.append"some message"
    #look at policy_context for what to specifically check

    del context #remove afeter implementing!!
    return []


def validate_proposed_tool_call(
    decision: ToolCallDecision,
    *,
    request: LabRequest,
    trace: list[TraceEvent],
) -> list[str]:
    """Supplied wrapper. Do not modify this function."""
    errors = validate_request_binding(decision, request=request)
    if decision.tool == "reserve_resource":
        context = build_reservation_context(decision, trace)
        errors.extend(validate_reservation_preconditions(context))
    return errors


def retrieved_passage_ids(trace: list[TraceEvent]) -> set[str]:
    """Supplied helper. Do not modify this function."""
    identifiers: set[str] = set()
    for event in trace:
        if event.observation.tool != "search_lab_documents" or not event.observation.ok:
            continue
        identifiers.update(
            passage["passage_id"]
            for passage in event.observation.data.get("passages", [])
        )
    return identifiers


def validate_final_response(
    response: AgentResponse, trace: list[TraceEvent]
) -> list[str]:
    """TODO 3.3: Validate citations, claimed actions, and final status."""
    #don't want the model making things up so checks on the finaldecision before accepted
    #set things up, need: errors, retrieved, sucessful mutations...
    #from hint! - mutation = successful if BOTH event.mutating and event.observation.ok are TRUE

    #from hint 3a - citation grounding
    #for each in response.citations, not retrieved needs error message
    #needs to stop hallucinations, prior-knowledge, and passages from earlier runs

    #from hint 3b - complete actions must match real sucessful mutations
    #list of successful mutation tool names
    #each entry in response.completed.actions
    #if doesn't have a corresponding successful mutation send error message
    #claims about proposed, gate-denied, or ok=False need to fail here

    #fint hint 3c - status == completed requirements
    #can't claim completion with no successful mutatutions
    #a completed response should state what was done
    
    #from hint 3d - status != completed requirements 
    #any remaining non-completed requirements 
    #response.completed_actions is empty, or send error
    #a noncompleted response can't claim to be finished work
    #trace can't have unreported sucessful mutations
    #if successful_muations is not empty, send an error because work succeeded and response failed to report it
    #needs to return full errors list w/empty list == valid response
    #includes everything from all 4 checks 

    del response, trace  #delete this when impletmented!!
    return []
