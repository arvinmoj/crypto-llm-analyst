"""Initial database migration

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create cryptocurrency_symbols table
    op.create_table('cryptocurrency_symbols',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('symbol', sa.String(length=20), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('market_cap_rank', sa.Integer(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('symbol')
    )
    op.create_index(op.f('ix_cryptocurrency_symbols_id'), 'cryptocurrency_symbols', ['id'], unique=False)
    op.create_index(op.f('ix_cryptocurrency_symbols_symbol'), 'cryptocurrency_symbols', ['symbol'], unique=False)

    # Create ohlc_data table
    op.create_table('ohlc_data',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('symbol_id', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.Column('open_price', sa.Float(), nullable=False),
    sa.Column('high_price', sa.Float(), nullable=False),
    sa.Column('low_price', sa.Float(), nullable=False),
    sa.Column('close_price', sa.Float(), nullable=False),
    sa.Column('volume', sa.Float(), nullable=False),
    sa.Column('exchange', sa.String(length=50), nullable=True),
    sa.Column('timeframe', sa.String(length=10), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['symbol_id'], ['cryptocurrency_symbols.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('symbol_id', 'timestamp', 'timeframe', name='unique_ohlc_entry')
    )
    op.create_index(op.f('ix_ohlc_data_id'), 'ohlc_data', ['id'], unique=False)
    op.create_index(op.f('ix_ohlc_data_timestamp'), 'ohlc_data', ['timestamp'], unique=False)
    op.create_index('idx_ohlc_symbol_timestamp', 'ohlc_data', ['symbol_id', 'timestamp'], unique=False)

    # Create technical_indicators table
    op.create_table('technical_indicators',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('symbol_id', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.Column('indicator_name', sa.String(length=50), nullable=False),
    sa.Column('value', sa.Float(), nullable=False),
    sa.Column('parameters', sa.JSON(), nullable=True),
    sa.Column('timeframe', sa.String(length=10), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['symbol_id'], ['cryptocurrency_symbols.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('symbol_id', 'timestamp', 'indicator_name', 'timeframe', name='unique_indicator_entry')
    )
    op.create_index(op.f('ix_technical_indicators_id'), 'technical_indicators', ['id'], unique=False)
    op.create_index(op.f('ix_technical_indicators_timestamp'), 'technical_indicators', ['timestamp'], unique=False)
    op.create_index('idx_indicator_symbol_timestamp', 'technical_indicators', ['symbol_id', 'timestamp'], unique=False)

    # Create market_signals table
    op.create_table('market_signals',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('symbol_id', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.Column('signal_type', sa.String(length=10), nullable=False),
    sa.Column('strength', sa.Float(), nullable=False),
    sa.Column('confidence', sa.Float(), nullable=False),
    sa.Column('price', sa.Float(), nullable=False),
    sa.Column('reason', sa.Text(), nullable=True),
    sa.Column('indicators_used', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['symbol_id'], ['cryptocurrency_symbols.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_market_signals_id'), 'market_signals', ['id'], unique=False)
    op.create_index(op.f('ix_market_signals_timestamp'), 'market_signals', ['timestamp'], unique=False)
    op.create_index('idx_signal_symbol_timestamp', 'market_signals', ['symbol_id', 'timestamp'], unique=False)
    op.create_index('idx_signal_type_timestamp', 'market_signals', ['signal_type', 'timestamp'], unique=False)

    # Create analysis_results table
    op.create_table('analysis_results',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('symbol_id', sa.Integer(), nullable=False),
    sa.Column('analysis_type', sa.String(length=50), nullable=False),
    sa.Column('analysis_data', sa.JSON(), nullable=False),
    sa.Column('summary', sa.Text(), nullable=True),
    sa.Column('recommendations', sa.JSON(), nullable=True),
    sa.Column('confidence_score', sa.Float(), nullable=True),
    sa.Column('agent_version', sa.String(length=20), nullable=True),
    sa.Column('execution_time', sa.Float(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['symbol_id'], ['cryptocurrency_symbols.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_analysis_results_id'), 'analysis_results', ['id'], unique=False)
    op.create_index('idx_analysis_symbol_type', 'analysis_results', ['symbol_id', 'analysis_type'], unique=False)
    op.create_index('idx_analysis_timestamp', 'analysis_results', ['created_at'], unique=False)

    # Create market_sentiment table
    op.create_table('market_sentiment',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('symbol_id', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.Column('overall_sentiment', sa.Float(), nullable=False),
    sa.Column('sentiment_label', sa.String(length=20), nullable=False),
    sa.Column('sources', sa.JSON(), nullable=True),
    sa.Column('volume_indicators', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['symbol_id'], ['cryptocurrency_symbols.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_market_sentiment_id'), 'market_sentiment', ['id'], unique=False)
    op.create_index(op.f('ix_market_sentiment_timestamp'), 'market_sentiment', ['timestamp'], unique=False)
    op.create_index('idx_sentiment_symbol_timestamp', 'market_sentiment', ['symbol_id', 'timestamp'], unique=False)

    # Create knowledge_documents table
    op.create_table('knowledge_documents',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('doc_id', sa.String(length=50), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('category', sa.String(length=50), nullable=True),
    sa.Column('symbols', sa.JSON(), nullable=True),
    sa.Column('metadata', sa.JSON(), nullable=True),
    sa.Column('source', sa.String(length=100), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('doc_id')
    )
    op.create_index(op.f('ix_knowledge_documents_id'), 'knowledge_documents', ['id'], unique=False)
    op.create_index('idx_knowledge_category', 'knowledge_documents', ['category'], unique=False)
    op.create_index('idx_knowledge_active', 'knowledge_documents', ['is_active'], unique=False)

    # Create user_sessions table
    op.create_table('user_sessions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('session_id', sa.String(length=100), nullable=False),
    sa.Column('user_id', sa.String(length=100), nullable=True),
    sa.Column('started_at', sa.DateTime(), nullable=True),
    sa.Column('last_activity', sa.DateTime(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('session_data', sa.JSON(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('session_id')
    )
    op.create_index(op.f('ix_user_sessions_id'), 'user_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_user_sessions_session_id'), 'user_sessions', ['session_id'], unique=False)

    # Create user_interactions table
    op.create_table('user_interactions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('session_id', sa.String(length=100), nullable=False),
    sa.Column('interaction_type', sa.String(length=50), nullable=False),
    sa.Column('input_data', sa.JSON(), nullable=True),
    sa.Column('output_data', sa.JSON(), nullable=True),
    sa.Column('processing_time', sa.Float(), nullable=True),
    sa.Column('success', sa.Boolean(), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['session_id'], ['user_sessions.session_id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_interactions_id'), 'user_interactions', ['id'], unique=False)
    op.create_index('idx_interaction_session_time', 'user_interactions', ['session_id', 'timestamp'], unique=False)
    op.create_index('idx_interaction_type_time', 'user_interactions', ['interaction_type', 'timestamp'], unique=False)

    # Create system_metrics table
    op.create_table('system_metrics',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('metric_name', sa.String(length=100), nullable=False),
    sa.Column('metric_value', sa.Float(), nullable=False),
    sa.Column('metric_unit', sa.String(length=20), nullable=True),
    sa.Column('metadata', sa.JSON(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_system_metrics_id'), 'system_metrics', ['id'], unique=False)
    op.create_index(op.f('ix_system_metrics_metric_name'), 'system_metrics', ['metric_name'], unique=False)
    op.create_index('idx_metric_name_time', 'system_metrics', ['metric_name', 'timestamp'], unique=False)


def downgrade():
    # Drop tables in reverse order
    op.drop_table('system_metrics')
    op.drop_table('user_interactions')
    op.drop_table('user_sessions')
    op.drop_table('knowledge_documents')
    op.drop_table('market_sentiment')
    op.drop_table('analysis_results')
    op.drop_table('market_signals')
    op.drop_table('technical_indicators')
    op.drop_table('ohlc_data')
    op.drop_table('cryptocurrency_symbols')