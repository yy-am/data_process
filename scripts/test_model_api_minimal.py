from __future__ import annotations

import argparse
import json
import os
import sys

try:
    import httpx
    from openai import OpenAI
except ImportError as exc:  # pragma: no cover
    print(
        "Missing dependency. Please install with: .\\python.cmd -m pip install openai httpx",
        file=sys.stderr,
    )
    raise


def main() -> None:
    parser = argparse.ArgumentParser(description="Minimal SDK-based connectivity test for model APIs.")
    parser.add_argument("--base-url", default=os.getenv("EVAL_BASE_URL"), help="Model API base URL.")
    parser.add_argument("--model", default=os.getenv("EVAL_MODEL_NAME"), help="Model name.")
    parser.add_argument(
        "--authorization-header",
        default=os.getenv("EVAL_AUTHORIZATION_HEADER"),
        help="Full Authorization header value.",
    )
    parser.add_argument(
        "--prompt",
        default='你好，请只返回一个简短 JSON，例如 {"ok": true}。',
        help="User prompt to send.",
    )
    args = parser.parse_args()

    if not args.base_url:
        raise RuntimeError("Missing --base-url or EVAL_BASE_URL.")
    if not args.model:
        raise RuntimeError("Missing --model or EVAL_MODEL_NAME.")
    if not args.authorization_header:
        raise RuntimeError("Missing --authorization-header or EVAL_AUTHORIZATION_HEADER.")

    client = OpenAI(
        api_key="dummy",
        base_url=args.base_url,
        http_client=httpx.Client(verify=False, trust_env=False),
    )

    completion = client.chat.completions.create(
        model=args.model,
        messages=[{"role": "user", "content": args.prompt}],
        stream=False,
        extra_headers={"Authorization": args.authorization_header},
    )

    print("RAW COMPLETION:")
    print(completion)
    print()

    content = completion.choices[0].message.content
    print("MESSAGE CONTENT:")
    print(content)
    print()

    try:
        parsed = json.loads(content)
    except Exception as exc:  # noqa: BLE001
        print("CONTENT IS NOT VALID JSON:")
        print(repr(content))
        raise RuntimeError(f"message.content is not valid JSON: {exc}") from exc

    print("PARSED JSON:")
    print(json.dumps(parsed, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
