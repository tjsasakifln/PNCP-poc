# Changelog

All notable changes to the BidIQ Uniformes POC will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-01-28 - PRODUCTION RELEASE 🚀

### Deployed
- **Frontend:** https://bidiq-uniformes.vercel.app ✅ LIVE
- **Backend:** https://bidiq-backend-production.up.railway.app ✅ LIVE
- **API Docs:** https://bidiq-backend-production.up.railway.app/docs ✅ LIVE

### Added
- Production deployment on Vercel (Frontend) and Railway (Backend)
- Comprehensive E2E test suite with Playwright (25 tests, 100% passing)
- Automated CI/CD pipeline with GitHub Actions
- Production environment variable configuration
- CORS configuration for production domains
- Health check endpoints for monitoring
- Railway.toml configuration for backend deployment
- Vercel.json configuration for frontend deployment
- Complete deployment documentation (docs/DEPLOYMENT.md)
- Production troubleshooting guide in README.md

### Changed
- Updated README.md with production URLs
- Updated INTEGRATION.md with production endpoints
- Updated PRD.md to mark as deployed
- Updated ROADMAP.md with live production URLs
- Environment variables now documented for both local and production
- Troubleshooting section now includes production-specific issues

### Fixed
- Railway healthcheck timeout issues (Issue #73)
- Frontend BACKEND_URL alignment for production (Issue #75)
- PNCP URL format in Excel exports
- Favicon updated to DescompLicita logo
- Broken Excel hyperlinks to PNCP portal

### Testing
- Backend coverage: 99.2% (226 tests passing)
- Frontend coverage: 91.5% (94 tests passing)
- E2E tests: 25/25 passing
- CI/CD: All automated tests passing

## [0.1.0] - 2026-01-25 - MVP COMPLETE

### Added
- Backend FastAPI implementation
  - PNCP client with retry logic and rate limiting
  - Smart filtering engine with 50+ keywords
  - Excel generation with openpyxl
  - GPT-4.1-nano integration for executive summaries
  - Fallback mode for offline operation
- Frontend Next.js implementation
  - Interactive UF selection (27 Brazilian states)
  - Date range picker with validation
  - Real-time form validation
  - Results display with executive summary
  - Excel download functionality
- Docker Compose setup for local development
- Comprehensive test suites
  - Backend: 226 tests (99.2% coverage)
  - Frontend: 94 tests (91.5% coverage)
- Complete documentation
  - PRD.md (1900+ lines)
  - INTEGRATION.md (680 lines)
  - ROADMAP.md
  - Tech stack documentation

### Implementation Details
- **PNCP Integration:**
  - Exponential backoff retry (max 5 retries)
  - Circuit breaker pattern
  - Pagination support (500 items/page)
  - Rate limiting (100ms between requests)
  - Handles 429 rate limits with Retry-After

- **Filtering Engine:**
  - Fail-fast sequential filters
  - UF validation
  - Value range: R$ 50k - R$ 5M
  - 50+ uniform-related keywords
  - Exclusion keywords for false positives
  - Unicode normalization

- **Excel Generation:**
  - 11 columns with formatted headers
  - Hyperlinks to PNCP portal
  - Currency formatting (Brazilian locale)
  - Frozen header row
  - Metadata sheet with statistics
  - Auto-width columns

- **LLM Integration:**
  - GPT-4.1-nano for summaries
  - Structured output via Pydantic
  - Token optimization (<500 tokens)
  - Automatic fallback without API key

## [0.0.1] - 2026-01-24 - Initial Setup

### Added
- Project structure
- Development environment setup
- AIOS framework integration
- Git repository initialization
- Basic documentation structure

---

## Versioning Strategy

- **MAJOR.MINOR.PATCH** format
- MAJOR: Breaking changes or major feature releases
- MINOR: New features, backward compatible
- PATCH: Bug fixes, documentation updates

## Links

- [GitHub Repository](https://github.com/tjsasakifln/PNCP-poc)
- [Production Frontend](https://bidiq-uniformes.vercel.app)
- [Production Backend](https://bidiq-backend-production.up.railway.app)
- [API Documentation](https://bidiq-backend-production.up.railway.app/docs)
