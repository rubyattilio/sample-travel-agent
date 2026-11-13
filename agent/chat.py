import uuid

from openinference.instrumentation import using_session

from agent.instrumentation import tracer_provider
from agent.loop import run_agent


def main():
    print("Travel Agent — ask me about flights, hotels, weather, or trip plans.")
    print("Type 'quit' to exit.\n")
    messages = []
    session_id = str(uuid.uuid4())
    while True:
        try:
            user_input = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_input:
            continue
        if user_input.lower() in {"quit", "exit"}:
            break
        messages.append({"role": "user", "content": user_input})
        with using_session(session_id):
            reply, messages = run_agent(messages)
        print(f"\nagent> {reply}\n")
    tracer_provider.force_flush()  # CLI exits right after; ship buffered spans first


if __name__ == "__main__":
    main()
