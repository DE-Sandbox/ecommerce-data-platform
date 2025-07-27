"""Database functions and triggers managed by alembic_utils."""

from alembic_utils.pg_function import PGFunction
from alembic_utils.pg_trigger import PGTrigger

# UUID v7 generation function
uuid_generate_v7 = PGFunction(
    schema="public",
    signature="uuid_generate_v7()",
    definition="""
RETURNS uuid
LANGUAGE sql
VOLATILE
PARALLEL SAFE
AS $$
  -- Generate UUID v7 using current timestamp
  -- Structure: unix_ts_ms (48 bits) | ver (4 bits) | rand_a (12 bits) | var (2 bits) | rand_b (62 bits)
  SELECT encode(
    set_bit(
      set_bit(
        overlay(
          uuid_send(gen_random_uuid())
          placing substring(int8send(floor(extract(epoch from clock_timestamp()) * 1000)::bigint) from 3)
          from 1 for 6
        ),
        52, 1
      ),
      53, 1
    ),
    'hex'
  )::uuid
$$""",
)

# UUID v7 with sub-millisecond precision
uuid_generate_v7_precise = PGFunction(
    schema="public",
    signature="uuid_generate_v7_precise()",
    definition="""
RETURNS uuid
LANGUAGE sql
VOLATILE
PARALLEL SAFE
AS $$
  -- Extract timestamp with microsecond precision
  WITH ts AS (
    SELECT extract(epoch from clock_timestamp()) AS epoch_seconds
  )
  SELECT encode(
    set_bit(
      set_bit(
        overlay(
          overlay(
            uuid_send(gen_random_uuid())
            placing substring(int8send(floor(ts.epoch_seconds * 1000)::bigint) from 3)
            from 1 for 6
          )
          -- Add sub-millisecond precision in rand_a field (12 bits)
          placing substring(int8send(((ts.epoch_seconds * 1000000)::bigint % 1000) << 2) from 7)
          from 7 for 2
        ),
        52, 1
      ),
      53, 1
    ),
    'hex'
  )::uuid
  FROM ts
$$""",
)

# Audit trigger function
audit_trigger_function = PGFunction(
    schema="audit",
    signature="audit_trigger()",
    definition="""
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit.audit_log (table_name, record_id, action, new_values)
        VALUES (TG_TABLE_NAME, NEW.id, TG_OP, to_jsonb(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit.audit_log (table_name, record_id, action, old_values, new_values, changed_fields)
        VALUES (
            TG_TABLE_NAME,
            NEW.id,
            TG_OP,
            to_jsonb(OLD),
            to_jsonb(NEW),
            (
                SELECT array_agg(key)
                FROM jsonb_each(to_jsonb(NEW))
                WHERE to_jsonb(NEW) -> key IS DISTINCT FROM to_jsonb(OLD) -> key
            )
        );
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit.audit_log (table_name, record_id, action, old_values)
        VALUES (TG_TABLE_NAME, OLD.id, TG_OP, to_jsonb(OLD));
        RETURN OLD;
    END IF;
END;
$$""",
)

# List of all database functions
DATABASE_FUNCTIONS = [
    uuid_generate_v7,
    uuid_generate_v7_precise,
    audit_trigger_function,
]

# Function to create audit triggers for a table
def create_audit_trigger(table_name: str, schema: str = "ecommerce") -> PGTrigger:
    """Create an audit trigger for a table."""
    return PGTrigger(
        schema=schema,
        signature=f"audit_{table_name}",
        on_entity=f"{schema}.{table_name}",
        definition=f"""
AFTER INSERT OR UPDATE OR DELETE ON {schema}.{table_name}
FOR EACH ROW EXECUTE FUNCTION audit.audit_trigger()""",
    )
