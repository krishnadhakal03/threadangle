"""
Add video_thumbnail column to Generation model
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('generations', sa.Column('video_thumbnail', sa.String(), nullable=True))

def downgrade():
    op.drop_column('generations', 'video_thumbnail')
