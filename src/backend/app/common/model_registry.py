def register_orm_models() -> None:
    from app.audit import models as audit_models
    from app.modules import models as module_models
    from app.prompt_configs import models as prompt_config_models
    from app.requirements import models as requirement_models
    from app.testcases import job_models
    from app.testcases import models as testcase_models
    from app.testcases import version_models as testcase_version_models
    from app.users import models as user_models

    _ = (
        audit_models,
        module_models,
        prompt_config_models,
        requirement_models,
        job_models,
        testcase_models,
        testcase_version_models,
        user_models,
    )
