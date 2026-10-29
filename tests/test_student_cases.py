"""Create tests/test_student_cases.py and add your tests. Do not add your tests to or modify the instructor-provided test files.

The file must contain at least three tests:

an unsafe action proposal that is denied before tool execution;
a contradictory final response that is rejected because it disagrees with the trace; and
one additional case of your choice.
Use ScriptedLLM so that all three tests are deterministic. Give each test a descriptive name and assert the relevant response, trace, or termination property. It is not enough to just check that the code executed without an exception.

The tests must run as part of:

uv run pytest"""