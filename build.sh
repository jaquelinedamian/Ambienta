#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Current directory: $(pwd)"
echo "Listing directory contents:"
ls -la

echo "Moving to backend directory..."
cd backend || exit 1
echo "New current directory: $(pwd)"
echo "Listing backend directory contents:"
ls -la

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Running collectstatic..."
python manage.py collectstatic --no-input

echo "Running migrations..."
python manage.py migrate

echo "Build script completed."