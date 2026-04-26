// BOSS Data Graph — schema constraints and indexes.
// Apply once per database. All statements are idempotent (IF NOT EXISTS).

// ---------------------------------------------------------------------------
// Uniqueness constraints
// ---------------------------------------------------------------------------

CREATE CONSTRAINT framework_key_unique IF NOT EXISTS
FOR (f:Framework) REQUIRE f.key IS UNIQUE;

CREATE CONSTRAINT regulation_key_unique IF NOT EXISTS
FOR (r:Regulation) REQUIRE r.key IS UNIQUE;

CREATE CONSTRAINT dimension_key_unique IF NOT EXISTS
FOR (d:Dimension) REQUIRE d.key IS UNIQUE;

CREATE CONSTRAINT tier_name_unique IF NOT EXISTS
FOR (t:Tier) REQUIRE t.name IS UNIQUE;

CREATE CONSTRAINT director_id_unique IF NOT EXISTS
FOR (dir:Director) REQUIRE dir.id IS UNIQUE;

CREATE CONSTRAINT intent_id_unique IF NOT EXISTS
FOR (i:Intent) REQUIRE i.intent_id IS UNIQUE;

CREATE CONSTRAINT result_id_unique IF NOT EXISTS
FOR (r:Result) REQUIRE r.result_id IS UNIQUE;

CREATE CONSTRAINT packet_id_unique IF NOT EXISTS
FOR (p:ExceptionPacket) REQUIRE p.packet_id IS UNIQUE;

CREATE CONSTRAINT receipt_id_unique IF NOT EXISTS
FOR (r:DecisionReceipt) REQUIRE r.receipt_id IS UNIQUE;

CREATE CONSTRAINT flight_event_unique IF NOT EXISTS
FOR (f:FlightRecorderEvent) REQUIRE f.event_id IS UNIQUE;

CREATE CONSTRAINT escalation_tier_unique IF NOT EXISTS
FOR (e:EscalationTier) REQUIRE e.name IS UNIQUE;

// ---------------------------------------------------------------------------
// Indexes for lookup hotspots
// ---------------------------------------------------------------------------

CREATE INDEX intent_tenant_idx IF NOT EXISTS FOR (i:Intent) ON (i.tenant);
CREATE INDEX result_tier_idx IF NOT EXISTS FOR (r:Result) ON (r.tier);
CREATE INDEX fr_type_idx IF NOT EXISTS FOR (f:FlightRecorderEvent) ON (f.event_type);
CREATE INDEX fr_ts_idx IF NOT EXISTS FOR (f:FlightRecorderEvent) ON (f.timestamp);
