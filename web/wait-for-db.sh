#!/bin/sh
# wait-for-db.sh
set -e

host="$1"
shift
port="$1"
shift

until nc -z "$host" "$port"; do
  echo "⏳ Waiting for database at $host:$port..."
  sleep 2
done

echo "✅ Database is ready! Executing command: $@"
exec "$@"