from app.services.normalizer.extractors.standard import StandardTaskExtractor


class ProjectsTaskExtractor(StandardTaskExtractor):
    protocol_type = "projects"
