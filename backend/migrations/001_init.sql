-- Initial schema migration for Behavioral Risk OS MVP
CREATE TABLE IF NOT EXISTS firms (
  id SERIAL PRIMARY KEY,
  name VARCHAR(120) UNIQUE NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(20) DEFAULT 'trader',
  firm_id INTEGER REFERENCES firms(id),
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS policies (
  id SERIAL PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  enforcement_level VARCHAR(20) DEFAULT 'guard',
  max_risk_at_stop_pct FLOAT DEFAULT 1.0,
  max_leverage FLOAT DEFAULT 3.0,
  max_adds INTEGER DEFAULT 1,
  add_cooldown_seconds INTEGER DEFAULT 600,
  max_trades_per_day INTEGER DEFAULT 10,
  max_consecutive_losses INTEGER DEFAULT 3,
  strict_stop_widening_block BOOLEAN DEFAULT TRUE,
  allowlist_symbols JSONB DEFAULT '["PI_XBTUSD"]'::jsonb,
  config JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_policies (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  policy_id INTEGER NOT NULL REFERENCES policies(id),
  assigned_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS events (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  event_type VARCHAR(80) NOT NULL,
  action VARCHAR(80) NOT NULL,
  symbol VARCHAR(30),
  payload JSONB DEFAULT '{}'::jsonb,
  guard_result VARCHAR(20) DEFAULT 'allow',
  reason TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS stability_scores (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  score INTEGER NOT NULL,
  sub_scores JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_logs (
  id SERIAL PRIMARY KEY,
  actor_user_id INTEGER REFERENCES users(id),
  target_user_id INTEGER REFERENCES users(id),
  entity_type VARCHAR(40) NOT NULL,
  entity_id VARCHAR(80) NOT NULL,
  action VARCHAR(40) NOT NULL,
  details JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO policies (name) VALUES ('Default Guard Policy') ON CONFLICT DO NOTHING;
