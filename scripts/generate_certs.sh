#!/bin/bash
# Generate self-signed TLS certificates for local development

set -e

CERT_DIR="${1:-./certs}"
DAYS="${2:-365}"

echo "Generating self-signed TLS certificates for development..."
echo "Certificate directory: $CERT_DIR"
echo "Valid for: $DAYS days"
echo ""

# Create certificate directory
mkdir -p "$CERT_DIR"

# Generate private key
openssl genrsa -out "$CERT_DIR/key.pem" 2048

# Generate certificate signing request
openssl req -new -key "$CERT_DIR/key.pem" -out "$CERT_DIR/csr.pem" \
    -subj "/C=US/ST=State/L=City/O=Development/OU=MCP/CN=localhost"

# Generate self-signed certificate
openssl x509 -req -days "$DAYS" -in "$CERT_DIR/csr.pem" \
    -signkey "$CERT_DIR/key.pem" -out "$CERT_DIR/cert.pem" \
    -extfile <(printf "subjectAltName=DNS:localhost,DNS:*.localhost,IP:127.0.0.1")

# Clean up CSR
rm "$CERT_DIR/csr.pem"

# Set permissions
chmod 600 "$CERT_DIR/key.pem"
chmod 644 "$CERT_DIR/cert.pem"

echo "✓ Certificates generated successfully!"
echo ""
echo "Files created:"
echo "  Certificate: $CERT_DIR/cert.pem"
echo "  Private key: $CERT_DIR/key.pem"
echo ""
echo "To use with Docker Compose:"
echo "  1. Update docker-compose.yml to mount the certs directory"
echo "  2. Set environment variables:"
echo "     MCP_SSL_CERTFILE=/app/certs/cert.pem"
echo "     MCP_SSL_KEYFILE=/app/certs/key.pem"
echo ""
echo "⚠  WARNING: These are self-signed certificates for DEVELOPMENT ONLY"
echo "   For production, use proper certificates from a trusted CA"
echo ""
echo "   Claude Desktop may require you to trust this certificate."
echo "   On macOS: sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain $CERT_DIR/cert.pem"
