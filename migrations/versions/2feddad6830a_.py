"""empty message

Revision ID: 2feddad6830a
Revises: c04390d373e2
Create Date: 2019-05-15 05:08:41.821839

"""

# revision identifiers, used by Alembic.
revision = '2feddad6830a'
down_revision = 'c04390d373e2'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('match', sa.Column('demoFile', mysql.VARCHAR(length=256), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('match', 'demoFile')
    ### end Alembic commands ###