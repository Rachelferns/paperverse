-- Supabase/Postgres production starting point. Runtime local development uses SQLite.
create extension if not exists pgcrypto;

create table if not exists papers (
  id uuid primary key default gen_random_uuid(), title text not null, arxiv_id text,
  markdown_content text not null default '', summary text not null default '', sections_json jsonb not null default '[]'::jsonb,
  created_at timestamptz default now(), status text not null default 'queued'
);
create table if not exists equations (
  id uuid primary key default gen_random_uuid(), paper_id uuid references papers(id) on delete cascade,
  official_latex text not null, section_name text, derivation_payload jsonb not null, created_at timestamptz default now()
);
create table if not exists generated_videos (
  id uuid primary key default gen_random_uuid(), equation_id uuid references equations(id) on delete cascade,
  composition_props jsonb not null, video_url text, status text default 'pending', created_at timestamptz default now()
);
create table if not exists symbol_glossary (
  id uuid primary key default gen_random_uuid(), paper_id uuid references papers(id) on delete cascade,
  symbol text not null, definition text not null, dimensions text
);
create table if not exists artifacts (
  id uuid primary key default gen_random_uuid(), paper_id uuid references papers(id) on delete cascade,
  mermaid_diagram text, executable_python text, flashcards_json jsonb, viva_quiz_json jsonb
);
