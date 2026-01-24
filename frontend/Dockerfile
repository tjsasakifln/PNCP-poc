# =============================================================================
# BidIQ Uniformes - Frontend Dockerfile (Placeholder)
# =============================================================================
# This is a placeholder until issue #21 (Setup Next.js) is implemented
# Serves a simple "Coming Soon" page via nginx

FROM nginx:alpine

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Create simple placeholder HTML
RUN echo '<!DOCTYPE html>' > /usr/share/nginx/html/index.html && \
    echo '<html lang="pt-BR">' >> /usr/share/nginx/html/index.html && \
    echo '<head>' >> /usr/share/nginx/html/index.html && \
    echo '    <meta charset="UTF-8">' >> /usr/share/nginx/html/index.html && \
    echo '    <meta name="viewport" content="width=device-width, initial-scale=1.0">' >> /usr/share/nginx/html/index.html && \
    echo '    <title>BidIQ Uniformes - Coming Soon</title>' >> /usr/share/nginx/html/index.html && \
    echo '    <style>' >> /usr/share/nginx/html/index.html && \
    echo '        body { font-family: system-ui, -apple-system, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }' >> /usr/share/nginx/html/index.html && \
    echo '        .container { text-align: center; padding: 2rem; }' >> /usr/share/nginx/html/index.html && \
    echo '        h1 { font-size: 3rem; margin-bottom: 1rem; }' >> /usr/share/nginx/html/index.html && \
    echo '        p { font-size: 1.2rem; opacity: 0.9; }' >> /usr/share/nginx/html/index.html && \
    echo '        .status { background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 8px; margin-top: 2rem; }' >> /usr/share/nginx/html/index.html && \
    echo '        a { color: #ffd700; text-decoration: none; }' >> /usr/share/nginx/html/index.html && \
    echo '    </style>' >> /usr/share/nginx/html/index.html && \
    echo '</head>' >> /usr/share/nginx/html/index.html && \
    echo '<body>' >> /usr/share/nginx/html/index.html && \
    echo '    <div class="container">' >> /usr/share/nginx/html/index.html && \
    echo '        <h1>🎯 BidIQ Uniformes</h1>' >> /usr/share/nginx/html/index.html && \
    echo '        <p>POC - Automação de Descoberta de Licitações PNCP</p>' >> /usr/share/nginx/html/index.html && \
    echo '        <div class="status">' >> /usr/share/nginx/html/index.html && \
    echo '            <p><strong>Frontend: Coming Soon</strong></p>' >> /usr/share/nginx/html/index.html && \
    echo '            <p>Next.js interface will be implemented in <a href="https://github.com/tjsasakifln/PNCP-poc/issues/21" target="_blank">Issue #21</a></p>' >> /usr/share/nginx/html/index.html && \
    echo '            <p style="margin-top: 1rem;">Backend API available at: <a href="http://localhost:8000/docs">http://localhost:8000/docs</a></p>' >> /usr/share/nginx/html/index.html && \
    echo '        </div>' >> /usr/share/nginx/html/index.html && \
    echo '    </div>' >> /usr/share/nginx/html/index.html && \
    echo '</body>' >> /usr/share/nginx/html/index.html && \
    echo '</html>' >> /usr/share/nginx/html/index.html

# Expose port 3000 (non-standard for nginx, but matches frontend convention)
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:3000/ || exit 1
