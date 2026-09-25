from pathlib import Path

from .decorators import tool


def create_search_tools(project_root):
    root = Path(project_root).resolve()

    def resolve_path(path):
        target = (root / path).resolve()

        try:
            target.relative_to(root)
        except ValueError:
            raise ValueError(
                f"Path '{path}' is outside "
                "the project root."
            )

        return target

    @tool()
    def search_files(
        query: str,
        path: str = ".",
        search_type: str = "name",
        recursive: bool = True,
        max_results: int = 50,
    ):
        """Search files inside the project workspace."""

        valid_search_types = {
            "name",
            "suffix",
            "content",
        }

        if search_type not in valid_search_types:
            raise ValueError(
                "search_type must be one of: "
                "name, suffix, content."
            )

        if max_results <= 0:
            raise ValueError(
                "max_results must be greater than 0."
            )

        target = resolve_path(path)
        if not target.exists():
            raise FileNotFoundError(
                f"Path '{path}' does not exist."
            )
        if not target.is_dir():
            raise NotADirectoryError(
                f"Path '{path}' is not a directory."
            )
        if recursive:
            candidates = target.rglob("*")
        else:
            candidates = target.iterdir()

        results = []

        for item in candidates:
            if not item.is_file():
                continue

            relative_path = str(
                item.relative_to(root)
            )
            # ---------------------------------
            # Search by file name
            # ---------------------------------
            if search_type == "name":
                if (
                    query.lower()
                    not in item.name.lower()
                ):
                    continue

                results.append(
                    {
                        "path": relative_path,
                    }
                )
            # ---------------------------------
            # Search by suffix
            # ---------------------------------
            elif search_type == "suffix":
                expected_suffix = (
                    query.lower()
                )
                if not expected_suffix.startswith(
                    "."
                ):
                    expected_suffix = (
                        "." + expected_suffix
                    )
                if (
                    item.suffix.lower()
                    != expected_suffix
                ):
                    continue
                results.append(
                    {
                        "path": relative_path,
                    }
                )
            # ---------------------------------
            # Search by file content
            # ---------------------------------
            elif search_type == "content":
                try:
                    content = item.read_text(
                        encoding="utf-8"
                    )
                except (
                    UnicodeDecodeError,
                    OSError,
                ):
                    continue
                line_matches = []
                for line_number, line in enumerate(
                    content.splitlines(),
                    start=1,
                ):
                    if (
                        query.lower()
                        in line.lower()
                    ):
                        line_matches.append(
                            {
                                "line": line_number,
                                "text": line.strip(),
                            }
                        )

                if not line_matches:
                    continue
                results.append(
                    {
                        "path": relative_path,
                        "matches": line_matches,
                    }
                )
            if len(results) >= max_results:
                break
            
        return {
            "query": query,
            "search_type": search_type,
            "path": str(
                target.relative_to(root)
            ),
            "recursive": recursive,
            "count": len(results),
            "results": results,
        }

    return [
        search_files,
    ]