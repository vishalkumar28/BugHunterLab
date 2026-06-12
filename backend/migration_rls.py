# This represents what an Alembic migration script would look like
# alembic/versions/xxxx_enable_rls.py

from alembic import op
import sqlalchemy as sa

def upgrade():
    # Add tenant_id to tables
    op.add_column('targets', sa.Column('tenant_id', sa.String(50), nullable=False, server_default='default_tenant'))
    op.add_column('assets', sa.Column('tenant_id', sa.String(50), nullable=False, server_default='default_tenant'))
    op.add_column('jobs', sa.Column('tenant_id', sa.String(50), nullable=False, server_default='default_tenant'))
    op.add_column('findings', sa.Column('tenant_id', sa.String(50), nullable=False, server_default='default_tenant'))

    # Enable RLS
    op.execute("ALTER TABLE targets ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE assets ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE findings ENABLE ROW LEVEL SECURITY;")

    # Create policies
    op.execute("CREATE POLICY tenant_isolation_policy ON targets USING (tenant_id = current_setting('app.current_tenant', true));")
    op.execute("CREATE POLICY tenant_isolation_policy ON assets USING (tenant_id = current_setting('app.current_tenant', true));")
    op.execute("CREATE POLICY tenant_isolation_policy ON jobs USING (tenant_id = current_setting('app.current_tenant', true));")
    op.execute("CREATE POLICY tenant_isolation_policy ON findings USING (tenant_id = current_setting('app.current_tenant', true));")

def downgrade():
    op.drop_column('targets', 'tenant_id')
    op.drop_column('assets', 'tenant_id')
    op.drop_column('jobs', 'tenant_id')
    op.drop_column('findings', 'tenant_id')
