"""Milestone 3: implement three selected validation responsibilities."""

from __future__ import annotations

from .agent_models import ToolCallDecision
from .models import AgentResponse, LabRequest, TraceEvent
from .policy_context import ReservationContext, build_reservation_context
#Failed 3 Tests, Passed 7
def validate_request_binding(
    decision: ToolCallDecision,
    *,
    request: LabRequest,
) -> list[str]:
    """TODO 3.1: Prevent identity and resolved-field substitution."""
    #collect all mismatches
    errors: list[str] = []
    #need to check fields that overlap between tool call and the trusted request
    #get values from decision.arguments and request.model_dump()
    arguments = decision.arguments
    #if any values are different, return an error message for each field
    if "user_id" in arguments and arguments["user_id"] != request.authenticated_user_id:
        errors.append("user_id_must_match_authenticated_user")

    if "project_id" in arguments:
        if request.project_id is None:
            errors.append("project_id_is_unresolved_in_request")
        elif arguments["project_id"] != request.project_id:
            errors.append("project_id_does_not_match_request")

    if "resource_id" in arguments:
        if request.resource_id is None:
            errors.append("resource_id_unresolved_in_request")
        elif arguments["resource_id"] != request.resource_id:
            errors.append("resource_id_does_not_match_request")
    #empty list == valid
    return errors


def validate_reservation_preconditions(context: ReservationContext) -> list[str]:
    """TODO 3.2: Return an error for every required context fact that is false."""
    #make a list of preconditon errors using boolean facts
    #esstentially: fact is false, add an error message to the list
    #follow a pattern of -> context.fact: error.append"some message"
    #look at policy_context for what to specifically check
    #one error per failing fact -> does not exit early
    errors: list[str] = []

    if not context.arguments_complete:
        errors.append("arguments_incomplete")

    if not context.policy_retrieved:
        errors.append("policy_not_retrieved")

    if not context.authorizations_checked:
        errors.append("authorizations_not_checked")

    if not context.resource_status_checked: 
        errors.append("resource_status_not_checked")

    if not context.project_authorized:
        errors.append("project_not_authorized")

    if not context.qualification_current:
        errors.append("required_qualification_missing")

    if not context.resource_available:
        errors.append("resource_not_availible")

    if not context.calibration_current:
        errors.append("calibration_not_current")

    if not context.maintenance_clear:
        errors.append("maintenance_scheduled")

    if not context.after_hours_approval_satisfied:
        errors.append("after_hours_approval_missing")

    return errors


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
    errors: list[str] = []
    retrieved = retrieved_passage_ids(trace)

    #from hint! - mutation = successful if BOTH event.mutating and event.observation.ok are TRUE
    successful_mutations = [event for event in trace if event.mutating and event.observation.ok]
    #list of successful mutation tool names
    mutation_tools = [event.observation.tool for event in successful_mutations]

    #from hint 3a - citation grounding
    #needs to stop hallucinations, prior-knowledge, and passages from earlier runs
    for citation in response.citations:
        if citation not in retrieved:
            #for each in response.citations, not retrieved needs error message
            errors.append(f"citations_not_retrieved:{citation}")

    #from hint 3b - complete actions must match real sucessful mutations
    #each entry in response.completed.actions
    #claims about proposed, gate-denied, or ok=False need to fail here
    for action in response.completed_actions:
        if action not in mutation_tools:
            #if doesn't have a corresponding successful mutation send error message
            errors.append(f"completed_action_with_no_successful_mutation:{action}")
        
    #fint hint 3c - status == completed requirements
    if response.status == "completed":
        #can't claim completion with no successful mutatutions
        if not successful_mutations:
            errors.append("completed_status_with_no_successful_mutation")
        #a completed response should state what was done
        if not response.completed_actions:
            errors.append("completed_status_with_no_action")
    #from hint 3d - status != completed requirements
    #any remaining non-completed requirements
    else:
        #response.completed_actions is empty, or send error
        #a noncompleted response can't claim to be finished work
        if response.completed_actions:
            errors.append("completed_action_not_in_successful_trace")
        #trace can't have unreported sucessful mutations
        # #if successful_muations is not empty, send an error because work succeeded and response failed to report it
        if successful_mutations:
            errors.append("completed_action_not_in_successful_trace")
    #needs to return full errors list w/empty list == valid response
    #includes everything from all 4 checks 
    return errors
