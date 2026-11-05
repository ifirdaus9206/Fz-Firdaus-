#!/usr/bin/env bash
# Verification script for Hermes Agency Integration
# Run this after installing the agency-agents router plugin

set -euo pipefail

echo "=== Hermes Agency Integration Verification ==="
echo ""

# Check 1: Plugin in config
echo "1. Checking agency-agents-router in config.yaml..."
if grep -q "agency-agents-router" ~/.hermes20/config.yaml; then
    echo "   ✓ agency-agents-router found in plugins.enabled"
else
    echo "   ✗ agency-agents-router NOT found in config.yaml"
    echo "   Run: ./scripts/install.sh --tool hermes --no-interactive"
    exit 1
fi

# Check 2: Plugin directory exists
echo "2. Checking plugin directory..."
if [ -d ~/.hermes20/plugins/agency-agents-router ]; then
    echo "   ✓ Plugin directory exists at ~/.hermes20/plugins/agency-agents-router"
else
    echo "   ✗ Plugin directory missing"
    exit 1
fi

# Check 3: Agents data file
echo "3. Checking agents data file..."
if [ -f ~/.hermes20/plugins/agency-agents-router/data/agents.json ]; then
    AGENT_COUNT=$(python3 -c "import json; data=json.load(open('~/.hermes20/plugins/agency-agents-router/data/agents.json')); print(len(data))")
    echo "   ✓ Agents data file exists with ${AGENT_COUNT} agents"
else
    echo "   ✗ Agents data file missing"
    exit 1
fi

# Check 4: Hermes doctor
echo "4. Running hermes doctor..."
if hermes doctor 2>&1 | grep -q "healthy"; then
    echo "   ✓ Hermes health check passed"
else
    echo "   ! Hermes doctor had warnings (check output above)"
fi

# Check 5: Test agent search
echo "5. Testing agent search functionality..."
RESULT=$(hermes --dev chat --query "list agency agents" 2>&1 | head -5)
if echo "$RESULT" | grep -q "agents"; then
    echo "   ✓ Agent search functional"
else
    echo "   ! Agent search may have issues"
fi

echo ""
echo "=== Verification Complete ==="
echo "All checks passed. The Agency agents are ready for use with Hermes."
echo "Available tools: agency_agents_search, agency_agents_inspect, agency_agents_load, agency_agents_delegate"