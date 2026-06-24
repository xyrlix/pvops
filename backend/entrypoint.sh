#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
while ! nc -z postgres 5432; do
  sleep 1
done
echo "PostgreSQL is ready"

echo "Waiting for TDengine..."
while ! nc -z tdengine 6030; do
  sleep 1
done
echo "TDengine is ready"

echo "Waiting for Redis..."
while ! nc -z redis 6379; do
  sleep 1
done
echo "Redis is ready"

echo "Starting application..."
exec "$@"
