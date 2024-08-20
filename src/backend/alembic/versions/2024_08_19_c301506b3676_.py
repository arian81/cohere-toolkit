"""empty message

Revision ID: c301506b3676
Revises: a76ebb869eb8
Create Date: 2024-08-19 12:36:34.118536

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c301506b3676'
down_revision: Union[str, None] = 'a76ebb869eb8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('groups',
    sa.Column('display_name', sa.String(), nullable=False),
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('display_name', name='unique_display_name')
    )
    op.create_table('user_group',
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('group_id', sa.String(), nullable=False),
    sa.Column('display', sa.String(), nullable=False),
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id', 'group_id', 'id')
    )
    op.add_column('users', sa.Column('user_name', sa.String(), nullable=True))
    op.add_column('users', sa.Column('external_id', sa.String(), nullable=True))
    op.add_column('users', sa.Column('active', sa.Boolean(), nullable=True))
    op.create_unique_constraint('unique_user_name', 'users', ['user_name'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('unique_user_name', 'users', type_='unique')
    op.drop_column('users', 'active')
    op.drop_column('users', 'external_id')
    op.drop_column('users', 'user_name')
    op.drop_table('user_group')
    op.drop_table('groups')
    # ### end Alembic commands ###
