from fastapi import APIRouter

from ..services import run_tool_wrapper

router = APIRouter(prefix="/api", tags=["tools"])


@router.post("/tools/{tool_name}")
def tools(tool_name: str, args: list[str] | None = None):
    return run_tool_wrapper(tool_name, args or [])
