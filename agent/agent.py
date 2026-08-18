import os

from google.adk.agents import Agent

from agent.cv_loader import extract_github_username, load_cv
from agent.prompts import build_system_prompt
from agent.tools.github import make_github_tools


def create_agent() -> Agent:
    cv_data = load_cv()
    github_username = extract_github_username(cv_data)
    system_prompt = build_system_prompt(cv_data)
    model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

    return Agent(
        model=model_name,
        name="cv_agent",
        description="Agente conversacional que representa el perfil profesional de un candidato",
        instruction=system_prompt,
        tools=make_github_tools(github_username),
    )
