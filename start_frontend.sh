#!/bin/bash
cd "$(dirname "$0")/frontend"

# Build if needed
npm run build

# Serve frontend
serve -s dist -l 5173
