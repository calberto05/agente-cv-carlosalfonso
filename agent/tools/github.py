import base64
import os

import httpx

_GITHUB_API = "https://api.github.com"
_TIMEOUT = 10


def _headers() -> dict:
    token = os.environ.get("GITHUB_TOKEN")
    return {"Authorization": f"Bearer {token}"} if token else {}


def make_github_tools(username: str) -> list:
    """Devuelve las tools de GitHub vinculadas al username del CV."""

    def list_github_repos() -> dict:
        """
        Lista los repositorios públicos de GitHub del candidato.
        Úsala cuando el usuario pregunte sobre proyectos, portafolio o trabajo en GitHub.
        No incluye forks.
        """
        try:
            response = httpx.get(
                f"{_GITHUB_API}/users/{username}/repos",
                headers=_headers(),
                params={"sort": "updated", "per_page": 20, "type": "owner"},
                timeout=_TIMEOUT,
            )
            response.raise_for_status()
            repos = response.json()
            return {
                "repos": [
                    {
                        "name": r["name"],
                        "description": r["description"] or "",
                        "language": r["language"] or "",
                        "stars": r["stargazers_count"],
                        "url": r["html_url"],
                        "updated_at": r["updated_at"],
                    }
                    for r in repos
                    if not r["fork"]
                ]
            }
        except httpx.TimeoutException:
            return {"error": "Tiempo de espera agotado al consultar GitHub. Intenta de nuevo."}
        except httpx.HTTPStatusError as e:
            return {"error": f"Error al consultar GitHub: {e.response.status_code}"}
        except httpx.HTTPError as e:
            return {"error": f"Error de red: {str(e)}"}

    def get_repo_details(repo_name: str) -> dict:
        """
        Obtiene los detalles de un repositorio específico de GitHub del candidato.
        Úsala cuando el usuario pregunte por un proyecto en particular y necesites más contexto.

        Args:
            repo_name: Nombre exacto del repositorio.
        """
        try:
            response = httpx.get(
                f"{_GITHUB_API}/repos/{username}/{repo_name}",
                headers=_headers(),
                timeout=_TIMEOUT,
            )
            if response.status_code == 404:
                return {"error": f"El repositorio '{repo_name}' no existe o es privado."}
            response.raise_for_status()
            r = response.json()
            return {
                "name": r["name"],
                "description": r["description"] or "",
                "language": r["language"] or "",
                "stars": r["stargazers_count"],
                "forks": r["forks_count"],
                "topics": r.get("topics", []),
                "url": r["html_url"],
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
            }
        except httpx.TimeoutException:
            return {"error": "Tiempo de espera agotado al consultar GitHub. Intenta de nuevo."}
        except httpx.HTTPStatusError as e:
            return {"error": f"Error al consultar GitHub: {e.response.status_code}"}
        except httpx.HTTPError as e:
            return {"error": f"Error de red: {str(e)}"}

    def get_repo_readme(repo_name: str) -> str:
        """
        Lee el contenido del README de un repositorio específico.
        Úsala cuando el usuario quiera entender qué hace un proyecto en detalle.

        Args:
            repo_name: Nombre exacto del repositorio.
        """
        try:
            response = httpx.get(
                f"{_GITHUB_API}/repos/{username}/{repo_name}/readme",
                headers=_headers(),
                timeout=_TIMEOUT,
            )
            if response.status_code == 404:
                return "Este repositorio no tiene README."
            response.raise_for_status()
            content = base64.b64decode(response.json()["content"]).decode("utf-8")
            return content
        except httpx.TimeoutException:
            return "Tiempo de espera agotado al obtener el README. Intenta de nuevo."
        except httpx.HTTPStatusError as e:
            return f"Error al obtener el README: {e.response.status_code}"
        except httpx.HTTPError as e:
            return f"Error de red: {str(e)}"

    return [list_github_repos, get_repo_details, get_repo_readme]
