"""Sistema de permissões v2 — tabelas permission, role, user_permission, role_permission, user_role

Revision ID: 0004_permissions
Revises: 0003_caixa_turno
Create Date: 2026-07-14 18:00:00
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "0004_permissions"
down_revision = "0003_caixa_turno"
branch_labels = None
depends_on = None


def upgrade():
    # Tabela de permissões (scopes)
    op.create_table(
        "permission",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("scope", sa.String(60), nullable=False, unique=True),
        sa.Column("nome", sa.String(120), nullable=False),
        sa.Column("descricao", sa.Text, nullable=False, server_default=""),
        sa.Column("categoria", sa.String(40), nullable=False, server_default="geral"),
        sa.Column("ativo", sa.Boolean, nullable=False, server_default=sa.true()),
    )

    # Tabela de papéis (roles)
    op.create_table(
        "role",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("nome", sa.String(80), nullable=False, unique=True),
        sa.Column("descricao", sa.Text, nullable=False, server_default=""),
        sa.Column("ativo", sa.Boolean, nullable=False, server_default=sa.true()),
    )

    # Permissões por papel
    op.create_table(
        "role_permission",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("role_id", sa.BigInteger, sa.ForeignKey("role.id", ondelete="CASCADE"), nullable=False),
        sa.Column("permission_id", sa.BigInteger, sa.ForeignKey("permission.id", ondelete="CASCADE"), nullable=False),
        sa.UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )

    # Permissões por usuário (individual)
    op.create_table(
        "user_permission",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, sa.ForeignKey("auth_user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("permission_id", sa.BigInteger, sa.ForeignKey("permission.id", ondelete="CASCADE"), nullable=False),
        sa.UniqueConstraint("user_id", "permission_id", name="uq_user_permission"),
    )

    # Papéis por usuário
    op.create_table(
        "user_role",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, sa.ForeignKey("auth_user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role_id", sa.BigInteger, sa.ForeignKey("role.id", ondelete="CASCADE"), nullable=False),
        sa.UniqueConstraint("user_id", "role_id", name="uq_user_role"),
    )

    # Seed das permissões base
    op.execute("""
        INSERT INTO permission (scope, nome, descricao, categoria) VALUES
        ('core:read',  'Core - Ler',       'Visualizar eventos e dados básicos', 'core'),
        ('core:write', 'Core - Editar',    'Criar/editar eventos', 'core'),
        ('finance:read',  'Financeiro - Ler',    'Visualizar lançamentos e relatórios', 'finance'),
        ('finance:write', 'Financeiro - Editar', 'Criar/editar lançamentos financeiros', 'finance'),
        ('inventory:read',  'Estoque - Ler',    'Visualizar produtos e estoque', 'inventory'),
        ('inventory:write', 'Estoque - Editar', 'Criar/editar produtos, entradas, requisições', 'inventory'),
        ('lodging:read',  'Hospedagem - Ler',    'Visualizar chalés e reservas', 'lodging'),
        ('lodging:write', 'Hospedagem - Editar', 'Criar/editar chalés, reservas e ações', 'lodging'),
        ('pos:read',  'PDV - Ler',    'Visualizar vendas e dashboard PDV', 'pos'),
        ('pos:write', 'PDV - Editar', 'Realizar vendas, abrir caixa, editar estoque local', 'pos'),
        ('admin:read',  'Admin - Ler',    'Visualizar configurações administrativas', 'admin'),
        ('admin:write', 'Admin - Editar', 'Gerenciar usuários, permissões e configurações do sistema', 'admin'),
        ('reports:read',  'Relatórios - Ler',    'Visualizar relatórios', 'reports'),
        ('reports:write', 'Relatórios - Editar', 'Exportar e gerar relatórios', 'reports')
    """)

    # Seed dos papéis padrão
    op.execute("""
        INSERT INTO role (nome, descricao) VALUES
        ('Operador', 'Acesso básico de leitura e operações do dia-a-dia'),
        ('Gerente',  'Acesso completo a todos os módulos operacionais'),
        ('Administrador', 'Acesso total ao sistema incluindo configurações e usuários')
    """)

    # Seed das permissões por papel
    op.execute("""
        INSERT INTO role_permission (role_id, permission_id)
        SELECT r.id, p.id FROM role r, permission p
        WHERE r.nome = 'Operador' AND p.scope IN (
            'core:read', 'pos:read', 'pos:write', 'finance:read',
            'inventory:read', 'lodging:read', 'reports:read'
        )
    """)
    op.execute("""
        INSERT INTO role_permission (role_id, permission_id)
        SELECT r.id, p.id FROM role r, permission p
        WHERE r.nome = 'Gerente' AND p.scope IN (
            'core:read', 'core:write', 'finance:read', 'finance:write',
            'inventory:read', 'inventory:write', 'lodging:read', 'lodging:write',
            'pos:read', 'pos:write', 'reports:read', 'reports:write'
        )
    """)
    op.execute("""
        INSERT INTO role_permission (role_id, permission_id)
        SELECT r.id, p.id FROM role r, permission p
        WHERE r.nome = 'Administrador' AND p.ativo = true
    """)


def downgrade():
    op.drop_table("user_role")
    op.drop_table("user_permission")
    op.drop_table("role_permission")
    op.drop_table("role")
    op.drop_table("permission")
