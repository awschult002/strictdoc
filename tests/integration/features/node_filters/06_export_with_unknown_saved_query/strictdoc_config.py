from strictdoc.api import ProjectConfig, SavedQuery


def create_config() -> ProjectConfig:
    return ProjectConfig(
        queries=[
            SavedQuery(
                title="Requirements 2 and 4",
                value='("2" in node["TITLE"] or "4" in node["TITLE"])',
            ),
        ],
    )
