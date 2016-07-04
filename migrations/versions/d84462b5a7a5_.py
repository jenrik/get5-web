"""empty message

Revision ID: d84462b5a7a5
Revises: 5b607892c512
Create Date: 2016-07-04 14:23:54.246240

"""

# revision identifiers, used by Alembic.
revision = 'd84462b5a7a5'
down_revision = '5b607892c512'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('match', sa.Column('plugin_version', sa.String(length=32), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('match', 'plugin_version')
    ### end Alembic commands ###