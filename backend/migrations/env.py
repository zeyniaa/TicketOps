from alembic import context
from sqlalchemy import create_engine
from ticketops.config import settings
from ticketops.db import Base
from ticketops import models

if context.is_offline_mode():
    context.configure(url=settings.database_url,target_metadata=Base.metadata,literal_binds=True)
    with context.begin_transaction(): context.run_migrations()
else:
    engine=create_engine(settings.database_url)
    with engine.connect() as conn:
        context.configure(connection=conn,target_metadata=Base.metadata)
        with context.begin_transaction():context.run_migrations()
