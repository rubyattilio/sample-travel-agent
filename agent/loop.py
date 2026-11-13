import json

import anthropic
from openinference.instrumentation import using_metadata
from opentelemetry.trace import Status, StatusCode

from agent.config import MAX_TOKENS, MODEL
from agent.instrumentation import tracer
from agent.prompt import PROMPT_VERSION, SYSTEM_PROMPT
from agent.tools import TOOLS, execute_tool

client = anthropic.Anthropic()


def run_agent(messages: list) -> tuple[str, list]:
    """Run one user turn through the tool-calling loop.

    `messages` must end with the latest user message. Returns the assistant's
    reply text and the updated message history.
    """
    # Hand-rolled (not @tracer.agent) so the span input is this turn's message, not the whole history.
    with using_metadata({"prompt_version": PROMPT_VERSION, "model": MODEL}), tracer.start_as_current_span(
        "travel_agent", openinference_span_kind="agent"
    ) as span:
        span.set_input(messages[-1]["content"])

        while True:
            response = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )
            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason != "tool_use":
                break

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = execute_tool(block.name, block.input)
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result),
                        }
                    )
            messages.append({"role": "user", "content": tool_results})

        reply = "".join(block.text for block in response.content if block.type == "text")
        span.set_output(reply)
        span.set_status(Status(StatusCode.OK))
    return reply, messages
