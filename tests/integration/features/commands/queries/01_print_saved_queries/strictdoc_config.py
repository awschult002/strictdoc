from strictdoc.api import ProjectConfig, SavedQuery


def create_config() -> ProjectConfig:
    return ProjectConfig(
        queries=[
            SavedQuery(
                title="System requirements",
                value='(node.is_requirement and "System" in node["TITLE"])',
            ),
            SavedQuery(title="All sections", value="node.is_section"),
        ],
    )
