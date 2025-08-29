"""Define the configurable parameters for the agent."""

from __future__ import annotations

import os
from dataclasses import dataclass, field, fields
from typing import Annotated

from . import prompts


@dataclass(kw_only=True)
class Context:
    """The context for the agent."""

    system_prompt: str = field(
        default=prompts.SYSTEM_PROMPT,
        metadata={
            "description": "The system prompt to use for the agent's interactions. "
            "This prompt sets the context and behavior for the agent."
        },
    )

    supervisor_system_prompt: str = field(
        default=prompts.SUPERVISOR_SYSTEM_PROMPT,
        metadata={
            "description": "The system prompt to use for the agent's interactions. "
            "This prompt sets the context and behavior for the agent."
        },
    )

    rpa_agent_system_prompt: str = field(
        default=prompts.RPA_AGENT_SYSTEM_PROMPT,
        metadata={
            "description": "The system prompt to use for the agent's interactions. "
            "This prompt sets the context and behavior for the agent."
        },
    )

    extraction_agent_system_prompt: str = field(
        default=prompts.EXTRACTION_AGENT_SYSTEM_PROMPT,
        metadata={
            "description": "The system prompt to use for the agent's interactions. "
            "This prompt sets the context and behavior for the agent."
        },
    )

    model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default="azure_openai/gpt-4o/2025-01-01-preview",
        metadata={
            "description": "The name of the language model to use for the supervisor agent's main interactions. "
            "Should be in the form: provider/model-name/api-version."
        },
    )

    supervisor_model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default="azure_openai/gpt-4o/2025-01-01-preview",
        metadata={
            "description": "The name of the language model to use for the supervisor agent's main interactions. "
            "Should be in the form: provider/model-name/api-version."
        },
    )

    worker_agents_model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default="azure_openai/gpt-4o/2024-02-15-preview",
        metadata={
            "description": "The name of the language model to use for the worker agent's main interactions. "
            "Should be in the form: provider/model-name/api-version."
        },
    )


    def __post_init__(self) -> None:
        """Fetch env vars for attributes that were not passed as args."""
        for f in fields(self):
            if not f.init:
                continue

            if getattr(self, f.name) == f.default:
                setattr(self, f.name, os.environ.get(f.name.upper(), f.default))
