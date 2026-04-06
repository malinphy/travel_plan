"""
Agent Model & Temperature Configuration
========================================
Central place to define which LLM model and temperature each agent uses.
To change a model or tune a temperature, edit ONLY this file.

Usage:
    from model_configs.agent_configs import FLIGHT_AGENT, HOTEL_AGENT, ...
    agent = Agent(name="FlightAgent", model=FLIGHT_AGENT.model, ...)

Temperature guidelines:
  0.0  → fully deterministic, best for tool-calling / structured outputs
  0.3  → slight variability, good for summarisation tasks
  0.7+ → creative / conversational responses
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentConfig:
    """Immutable config for a single agent."""
    model: str
    temperature: float
    notes: str = ""


# ─── Sub-agents ──────────────────────────────────────────────────────────────

FLIGHT_AGENT = AgentConfig(
    model="gpt-4.1",
    temperature=0.0,
    notes="Handles flight searches and DB queries. Low temp for deterministic tool calls.",
)

HOTEL_AGENT = AgentConfig(
    model="gpt-4o-mini",
    temperature=0.0,
    notes="Handles hotel searches and DB queries.",
)

YELP_AGENT = AgentConfig(
    model="gpt-4.1",
    temperature=0.0,
    notes="Handles Yelp / restaurant searches.",
)

BOOKING_AGENT = AgentConfig(
    model="gpt-4o-mini",
    temperature=0.0,
    notes="Manages the user's basket (add / remove / modify items).",
)

# ─── Orchestrator ─────────────────────────────────────────────────────────────

SUPERVISOR_AGENT = AgentConfig(
    model="gpt-4.1",
    temperature=0.0,
    notes="Top-level coordinator. Delegates to sub-agents. Needs reliable routing.",
)

# ─── BaseAgent reflection / reasoning helpers ────────────────────────────────

BASE_AGENT_DEFAULT = AgentConfig(
    model="gpt-4o-mini",
    temperature=0.0,
    notes="Default for BaseAgent when no explicit config is provided.",
)

REFLECTION_AGENT = AgentConfig(
    model="gpt-4o-mini",
    temperature=0.3,
    notes="Critic agent used inside BaseAgent self-reflection loop.",
)

REVISION_AGENT = AgentConfig(
    model="gpt-4o-mini",
    temperature=0.3,
    notes="Reviser agent used inside BaseAgent self-reflection loop.",
)

DEEPTHINK_AGENT = AgentConfig(
    model="gpt-4o-mini",
    temperature=0.7,
    notes="Chain-of-thought / deep thinking agent inside BaseAgent.",
)
