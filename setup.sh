#!/bin/bash
# Unitree Workspace Setup Script
# Usage: ./setup.sh [options]

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SHALLOW=""
CLONE_OFFICIAL=true
CLONE_COMMUNITY=false
UPDATE_MODE=false

show_help() {
    echo "Unitree Workspace Setup"
    echo ""
    echo "Usage: ./setup.sh [options]"
    echo ""
    echo "Options:"
    echo "  --shallow          Shallow clone (faster, less history)"
    echo "  --official-only    Only clone official SDKs"
    echo "  --community        Include community projects"
    echo "  --update           Update existing repositories"
    echo "  --help             Show this help"
    echo ""
    echo "Examples:"
    echo "  ./setup.sh --shallow              # Quick setup with official SDKs"
    echo "  ./setup.sh --shallow --community  # Include community projects"
    echo "  ./setup.sh --update               # Update all cloned repos"
}

clone_repo() {
    local path=$1
    local url=$2
    local desc=$3
    
    if [ -d "$path/.git" ]; then
        if [ "$UPDATE_MODE" = true ]; then
            echo -e "  ${YELLOW}⟳${NC} Updating $path"
            git -C "$path" pull --ff-only 2>/dev/null || echo -e "  ${RED}✗${NC} Update failed for $path"
        else
            echo -e "  ${GREEN}✓${NC} $path (exists)"
        fi
    else
        echo -e "  ${YELLOW}↓${NC} Cloning $path"
        mkdir -p "$(dirname "$path")"
        git clone $SHALLOW "$url" "$path" 2>/dev/null || echo -e "  ${RED}✗${NC} Clone failed: $path"
    fi
}

parse_yaml() {
    local yaml_file=$1
    local section=$2
    awk -v section="$section" '
    $0 ~ "^"section":" { in_section=1; next }
    /^[a-z]/ && in_section { in_section=0 }
    in_section && /^  - path:/ { path=$3 }
    in_section && /url:/ { url=$2 }
    in_section && /description:/ { 
        desc=""; for(i=2;i<=NF;i++) desc=desc" "$i
        print path "|" url "|" substr(desc,2)
    }
    ' "$yaml_file"
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --shallow)
            SHALLOW="--depth 1"
            shift
            ;;
        --official-only)
            CLONE_COMMUNITY=false
            shift
            ;;
        --community)
            CLONE_COMMUNITY=true
            shift
            ;;
        --update)
            UPDATE_MODE=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

if [ ! -f "repos.yaml" ]; then
    echo -e "${RED}Error: repos.yaml not found${NC}"
    exit 1
fi

echo -e "${GREEN}🚀 Unitree Workspace Setup${NC}"
echo ""

if [ "$CLONE_OFFICIAL" = true ]; then
    echo -e "${GREEN}📦 Official SDKs${NC}"
    while IFS='|' read -r path url desc; do
        clone_repo "$path" "$url" "$desc"
    done < <(parse_yaml repos.yaml "official")
fi

if [ "$CLONE_COMMUNITY" = true ]; then
    echo ""
    echo -e "${GREEN}🌐 Community Projects${NC}"
    while IFS='|' read -r path url desc; do
        clone_repo "$path" "$url" "$desc"
    done < <(parse_yaml repos.yaml "community")
fi

echo ""
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Build C++ SDK:    cd git/official/unitree_sdk2 && cmake -Bbuild && cmake --build build"
echo "  2. Build Python SDK: cd git/official/unitree_sdk2_python && pip install -e ."
echo "  3. Build ROS2:       cd git/official/unitree_ros2 && colcon build"
