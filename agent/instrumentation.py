"""Arize AX tracing. Import before any Anthropic client is created."""

import os

import agent.config  # noqa: F401  loads .env so register() can read ARIZE_SPACE_ID / ARIZE_API_KEY
from arize.otel import register
from openinference.instrumentation import OITracer, TraceConfig
from openinference.instrumentation.anthropic import AnthropicInstrumentor

# anthropic>=1.14 emits its own OTel spans; turn them off so each LLM call is traced once.
os.environ.setdefault("ANTHROPIC_OPEN_TELEMETRY", "false")

tracer_provider = register(
    project_name=os.getenv("ARIZE_PROJECT_NAME", "travel-agent"), verbose=False
)
AnthropicInstrumentor().instrument(tracer_provider=tracer_provider)
tracer = OITracer(tracer_provider.get_tracer(__name__), config=TraceConfig())
