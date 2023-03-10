"""empty message

Revision ID: cc8e4c727779
Revises: d6dfcaddde6f
Create Date: 2023-02-06 16:59:51.094234

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cc8e4c727779'
down_revision = 'd6dfcaddde6f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('treatment_machine', schema=None) as batch_op:
        batch_op.add_column(sa.Column('patient_id', sa.Integer(), nullable=False))
        batch_op.create_foreign_key(None, 'patient', ['patient_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('treatment_machine', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('patient_id')

    # ### end Alembic commands ###
