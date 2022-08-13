"""empty message

Revision ID: 310e351dbf75
Revises: 76dd713ef94a
Create Date: 2022-08-12 21:00:28.472370

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '310e351dbf75'
down_revision = '76dd713ef94a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Venue', sa.Column('genres', sa.String(length=120), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Venue', 'genres')
    # ### end Alembic commands ###
