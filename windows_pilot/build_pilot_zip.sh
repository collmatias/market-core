#!/bin/bash
# Build the Windows pilot ZIP package
# Run from the project root: ./windows_pilot/build_pilot_zip.sh

set -e

DIST_DIR="dist"
ZIP_NAME="vetcoresoft-pilot.zip"
TEMP_DIR="$DIST_DIR/vetcoresoft-pilot"

echo "=== Building VetCoreSoft Pilot Package ==="

# Clean previous build
rm -rf "$DIST_DIR"
mkdir -p "$TEMP_DIR/backend"

# Copy backend code (exclude __pycache__, .sqlite3, media uploads)
rsync -a --exclude='__pycache__' \
         --exclude='*.pyc' \
         --exclude='db.sqlite3' \
         --exclude='media/historias_clinicas' \
         --exclude='staticfiles' \
         backend/ "$TEMP_DIR/backend/"

# Copy pilot files
cp windows_pilot/start_vetcoresoft.bat "$TEMP_DIR/"
cp windows_pilot/vetcoresoft.ini "$TEMP_DIR/"
cp windows_pilot/README.md "$TEMP_DIR/"

# Remove Docker-specific files from the package
rm -f "$TEMP_DIR/backend/Dockerfile"

echo "Creating ZIP..."
cd "$DIST_DIR"
zip -r "$ZIP_NAME" vetcoresoft-pilot/ -x "*/\__pycache__/*"
cd ..

# Optionally copy to static downloads folder for the SaaS landing page
STATIC_DL="backend/staticfiles/downloads"
mkdir -p "$STATIC_DL"
cp "$DIST_DIR/$ZIP_NAME" "$STATIC_DL/"

echo "=== Done! ==="
echo "Package: $DIST_DIR/$ZIP_NAME"
echo "Static:  $STATIC_DL/$ZIP_NAME"
