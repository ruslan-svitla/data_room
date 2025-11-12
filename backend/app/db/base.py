# Import all the models, so that Base has them before being
# imported by Alembic
from app.db.base_class import Base  # noqa

# Import all models here for Alembic to detect
from app.models.user import User  # noqa
from app.models.document import Document  # noqa
from app.models.folder import Folder  # noqa
from app.models.integration import ExternalIntegration  # noqa
