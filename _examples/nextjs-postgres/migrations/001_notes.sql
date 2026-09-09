CREATE TABLE notes (
  id uuid PRIMARY KEY,
  body text NOT NULL CHECK (length(body) BETWEEN 1 AND 200),
  created_at timestamptz NOT NULL DEFAULT now()
);
