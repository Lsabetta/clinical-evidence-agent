from dataclasses import dataclass
from time import perf_counter
from typing import Generic, TypeVar

from ollama import chat
from pydantic import BaseModel


MODEL = "qwen3:4b-instruct"
NUM_CTX = 8192

T = TypeVar("T", bound=BaseModel)


@dataclass
class LLMResult(Generic[T]):
    output: T
    model: str
    latency_s: float
    input_tokens: int | None
    output_tokens: int | None


def generate_structured_answer(
    prompt: str,
    schema: type[T],
) -> LLMResult[T]:
    start = perf_counter()

    response = chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        format=schema.model_json_schema(),
        options={
            "temperature": 0,
            "num_ctx": NUM_CTX,
        }, 
    )

    end = perf_counter()

    output = schema.model_validate_json(
        response.message.content
    )

    return LLMResult(
        output=output,
        model=MODEL,
        latency_s=end - start,
        input_tokens=response.prompt_eval_count,
        output_tokens=response.eval_count,
    )