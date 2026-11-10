from strictdoc.api import ProjectConfig, SavedQuery


def create_config() -> ProjectConfig:
    return ProjectConfig(
        queries=[
            SavedQuery(title="Broken", value="node.is_requirement and"),
        ],
    )
