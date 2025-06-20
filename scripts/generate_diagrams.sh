#!/bin/bash

# Script to generate PNG diagrams from Mermaid source files
# This script compiles all C4 diagrams to PNG format for documentation

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DIAGRAMS_DIR="$PROJECT_DIR/docs/diagrams"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if mermaid CLI is available
check_dependencies() {
    log "Checking dependencies..."
    
    if ! command -v npx &> /dev/null; then
        error "npx is required but not installed"
        exit 1
    fi
    
    success "Dependencies check passed"
}

# Generate PNG from Mermaid file
generate_png() {
    local mmd_file="$1"
    local png_file="${mmd_file%.mmd}.png"
    local diagram_name="$(basename "$mmd_file" .mmd)"
    
    log "Generating PNG for $diagram_name..."
    
    if npx -p @mermaid-js/mermaid-cli mmdc \
        -i "$mmd_file" \
        -o "$png_file" \
        -t dark \
        -b transparent \
        --width 1200 \
        --height 800 \
        2>/dev/null; then
        success "Generated $png_file"
        return 0
    else
        error "Failed to generate $png_file"
        return 1
    fi
}

# Main function
main() {
    echo "=================================================="
    echo "C4 Diagram Generator for Payment Service"
    echo "=================================================="
    
    check_dependencies
    
    # Create diagrams directory if it doesn't exist
    mkdir -p "$DIAGRAMS_DIR"
    
    cd "$DIAGRAMS_DIR"
    
    # List of diagrams to generate
    diagrams=(
        "c1-system-context"
        "c2-container"
        "c3-component"
        "deployment"
        "data-flow"
        "security-architecture"
    )
    
    generated=0
    failed=0
    
    for diagram in "${diagrams[@]}"; do
        mmd_file="${diagram}.mmd"
        
        if [ -f "$mmd_file" ]; then
            if generate_png "$mmd_file"; then
                ((generated++))
            else
                ((failed++))
            fi
        else
            warning "Mermaid file not found: $mmd_file"
            ((failed++))
        fi
    done
    
    echo ""
    echo "=================================================="
    echo "Generation Summary"
    echo "=================================================="
    echo "Generated: $generated diagrams"
    echo "Failed: $failed diagrams"
    echo "Output directory: $DIAGRAMS_DIR"
    
    if [ $failed -eq 0 ]; then
        success "All diagrams generated successfully!"
        
        echo ""
        log "Available diagram files:"
        ls -la *.png 2>/dev/null || echo "No PNG files found"
        
        echo ""
        log "To view diagrams:"
        echo "  open $DIAGRAMS_DIR"
        echo "  # or"
        echo "  ls $DIAGRAMS_DIR/*.png"
        
    else
        error "Some diagrams failed to generate"
        exit 1
    fi
}

# Script help
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "C4 Diagram Generator"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  --clean        Remove existing PNG files before generating"
    echo ""
    echo "This script generates PNG images from Mermaid diagram files"
    echo "located in docs/diagrams/ directory."
    echo ""
    echo "Requirements:"
    echo "  - Node.js and npx"
    echo "  - Mermaid CLI (installed automatically via npx)"
    echo ""
    exit 0
fi

# Clean option
if [ "$1" = "--clean" ]; then
    log "Cleaning existing PNG files..."
    cd "$DIAGRAMS_DIR"
    rm -f *.png
    success "Cleaned PNG files"
fi

# Run main function
main