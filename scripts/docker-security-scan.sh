#!/bin/bash
# Container Security Scanning Script

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

IMAGE_NAME="${1:-ecommerce-data-platform:latest}"

echo -e "${BLUE}🔍 Container Security Scanning for: ${IMAGE_NAME}${NC}"
echo "========================================"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 1. Docker Scout (native Docker security scanning)
if command_exists docker; then
    echo -e "\n${YELLOW}1. Running Docker Scout CVE scan...${NC}"
    docker scout cves "$IMAGE_NAME" || echo -e "${YELLOW}Docker Scout not available. Install with: docker scout init${NC}"

    echo -e "\n${YELLOW}2. Running Docker Scout recommendations...${NC}"
    docker scout recommendations "$IMAGE_NAME" 2>/dev/null || true
fi

# 2. Grype vulnerability scanner
if command_exists grype; then
    echo -e "\n${YELLOW}3. Running Grype vulnerability scan...${NC}"
    grype "$IMAGE_NAME" --output table
else
    echo -e "${YELLOW}Grype not installed. Install with: brew install grype${NC}"
fi

# 3. Trivy comprehensive scanner
if command_exists trivy; then
    echo -e "\n${YELLOW}4. Running Trivy security scan...${NC}"
    trivy image --severity HIGH,CRITICAL "$IMAGE_NAME"
else
    echo -e "${YELLOW}Trivy not installed. Install with: brew install trivy${NC}"
fi

# 4. Basic Docker security checks
echo -e "\n${YELLOW}5. Running basic security checks...${NC}"

# Check if running as root
echo -n "Checking USER directive: "
if docker inspect "$IMAGE_NAME" --format '{{.Config.User}}' | grep -q "root\|^$"; then
    echo -e "${RED}❌ Container runs as root${NC}"
else
    echo -e "${GREEN}✅ Container runs as non-root${NC}"
fi

# Check for sensitive files
echo -n "Checking for secrets: "
docker run --rm --entrypoint sh "$IMAGE_NAME" -c 'find / -name "*.pem" -o -name "*.key" -o -name "*credentials*" -o -name "*secret*" 2>/dev/null | head -5' > /tmp/secrets_check.txt
if [ -s /tmp/secrets_check.txt ]; then
    echo -e "${RED}❌ Potential secrets found:${NC}"
    cat /tmp/secrets_check.txt
else
    echo -e "${GREEN}✅ No obvious secrets found${NC}"
fi
rm -f /tmp/secrets_check.txt

# Check image size
echo -n "Image size: "
SIZE=$(docker inspect "$IMAGE_NAME" --format='{{.Size}}' | awk '{print $1/1024/1024}')
echo -e "${BLUE}$(printf "%.2f" "$SIZE") MB${NC}"

# Check exposed ports
echo -n "Exposed ports: "
PORTS=$(docker inspect "$IMAGE_NAME" --format='{{range $p, $conf := .Config.ExposedPorts}}{{$p}} {{end}}')
if [ -n "$PORTS" ]; then
    echo -e "${BLUE}$PORTS${NC}"
else
    echo -e "${GREEN}None${NC}"
fi

# 6. SBOM (Software Bill of Materials)
if command_exists syft; then
    echo -e "\n${YELLOW}6. Generating SBOM...${NC}"
    syft "$IMAGE_NAME" -o table | head -20
else
    echo -e "${YELLOW}Syft not installed. Install with: brew install syft${NC}"
fi

echo -e "\n${GREEN}========================================"
echo -e "Security scan complete!${NC}"
echo -e "\n${YELLOW}Recommendations:${NC}"
echo "1. Fix any HIGH or CRITICAL vulnerabilities"
echo "2. Ensure container runs as non-root user"
echo "3. Minimize image size by using multi-stage builds"
echo "4. Regularly update base images"
echo "5. Never include secrets or credentials in images"
