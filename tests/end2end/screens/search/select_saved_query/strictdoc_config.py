from strictdoc.api import ProjectConfig, SavedQuery


def create_config() -> ProjectConfig:
    config = ProjectConfig(
        project_features=["SEARCH"],
        queries=[
            SavedQuery(
                title="System requirements",
                value='(node.is_requirement and "System" in node["TITLE"])',
            ),
            SavedQuery(title="All requirements", value="node.is_requirement"),
        ],
    )
    return config
