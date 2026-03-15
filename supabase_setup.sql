-- Script SQL para criar a tabela de conversas no Supabase
-- Execute este script no SQL Editor do Supabase

CREATE TABLE IF NOT EXISTS conversations (
    id VARCHAR(16) PRIMARY KEY,
    name TEXT NOT NULL,
    messages JSONB NOT NULL DEFAULT '[]'::jsonb,
    expert_type TEXT DEFAULT 'Dev Sênior',
    opinionated BOOLEAN DEFAULT FALSE,
    include_media BOOLEAN DEFAULT FALSE,
    english_mode BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Criar índice para buscas por nome
CREATE INDEX IF NOT EXISTS idx_conversations_name ON conversations(name);

-- Criar índice para buscas por data de criação
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at DESC);

-- Políticas RLS (Row Level Security) - permitir tudo por enquanto
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

-- Política para permitir todas as operações (INSERT, SELECT, UPDATE, DELETE)
CREATE POLICY "Allow all operations on conversations" ON conversations
    FOR ALL USING (true);