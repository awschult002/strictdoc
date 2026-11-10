from strictdoc.api import ProjectConfig, SavedQuery


def create_config() -> ProjectConfig:
    return ProjectConfig(
        project_features=["SEARCH"],
        # Saved queries are appended below by the test.
        queries=[
            SavedQuery(title="All requirements", value="node.is_requirement"),
        ],
    )
