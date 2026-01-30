# Sprint Ceremonies - Documentation Index

**Purpose:** Central index for all sprint ceremony documentation (Sprint Reviews, Retrospectives, etc.)

---

## 📋 Available Ceremonies

### Phase 3 Sprint Review & Retrospective (Day 14)

**Status:** ✅ Prepared (Ready for Execution)
**Date:** 2026-01-30
**Facilitator:** @sm (River)

#### Sprint Review (1 hour)
- **Agenda & Slide Deck:** `phase3-sprint-review.md`
- **Stakeholder Feedback Log:** `phase3-sprint-review-feedback.md` (to be filled during meeting)
- **Format:** Demo-driven (Feature #2, #3, Phase 2 recap) + Metrics + Q&A
- **Attendees:** Full squad + stakeholders

**Key Highlights:**
- 100% velocity achieved (26 SP / 26 SP)
- Usability score improved 52 → 78 (+26 points)
- QA approved for staging deployment
- Live feature demonstrations on staging environment

#### Sprint Retrospective (45 min)
- **Meeting Guide:** `phase3-sprint-retrospective.md`
- **Action Items Tracker:** `phase3-retrospective-action-items.md`
- **Format:** Start-Stop-Continue
- **Attendees:** Squad only (dev, qa, devops, pm, architect, sm)

**Key Focus Areas:**
- Testing maturity gap (frontend vs backend)
- Dependency management improvements
- Parallel execution success replication
- Quality gates enforcement

---

## 🎯 Ceremony Templates

### For Future Sprints

When preparing new ceremonies, use these templates:

1. **Sprint Review Template:** Copy `phase3-sprint-review.md` structure
   - Update sprint name, dates, features
   - Customize demo scripts for new features
   - Adjust metrics based on sprint goals

2. **Retrospective Template:** Copy `phase3-sprint-retrospective.md` structure
   - Update phase context
   - Keep Start-Stop-Continue format
   - Adjust preliminary observations based on phase

3. **Feedback Log Template:** Copy `phase3-sprint-review-feedback.md` structure
   - Update attendee list
   - Keep table structures for consistency

4. **Action Items Tracker Template:** Copy `phase3-retrospective-action-items.md` structure
   - Update action item IDs (AI-XXX)
   - Maintain progress dashboard format

---

## 📊 Ceremony Metrics

### Phase 3 Ceremony Preparation

**Time to Prepare:**
- Sprint Review: ~2 hours (research + deck creation)
- Retrospective: ~1.5 hours (preliminary analysis + guide creation)
- Supporting Docs: ~30 minutes (feedback log + action items tracker)
- **Total:** ~4 hours

**Artifacts Created:**
- ✅ `phase3-sprint-review.md` (comprehensive 500+ line slide deck)
- ✅ `phase3-sprint-retrospective.md` (facilitation guide with preliminary analysis)
- ✅ `phase3-sprint-review-feedback.md` (stakeholder feedback capture template)
- ✅ `phase3-retrospective-action-items.md` (5 action items with tracking)
- ✅ `docs/processes/phase-preflight-checklist.md` (new process document from AI-002)

---

## 🔄 Ceremony Workflow

### Before Ceremony
1. **@sm prepares ceremony documents** (this directory)
2. **@sm sends invites** to attendees (24 hours in advance)
3. **@sm shares read-only docs** with attendees for pre-read
4. **@sm reviews phase documentation** (test reports, burn-down charts, impediment logs)

### During Ceremony
1. **@sm facilitates** according to agenda
2. **@sm captures feedback/notes** in real-time (shared doc or whiteboard)
3. **@sm timeboxes each section** (respect total duration)
4. **@sm ensures all voices heard** (round-robin if needed)

### After Ceremony
1. **@sm updates ceremony documents** with meeting notes
2. **@sm creates GitHub issues** for action items
3. **@sm sends summary email** to attendees within 24 hours
4. **@sm tracks action item progress** weekly

---

## 📝 Best Practices (from Phase 3)

### Sprint Review
- **Live demos trump screenshots:** Use staging environment, not slides
- **Show real data:** Actual search results, not mock data
- **Quantify improvements:** Metrics and before/after comparisons
- **Capture feedback in structured format:** Use tables for easy parsing
- **End with clear next steps:** Phase 4 preview, action items

### Sprint Retrospective
- **Safe space first:** Reinforce ground rules (no blame, Vegas rule)
- **Data-driven discussion:** Reference velocity, test coverage, impediment logs
- **Timebox rigorously:** 15-15-15-10 min structure prevents analysis paralysis
- **Actionable outcomes only:** Every complaint must include a solution
- **Assign owners immediately:** No orphan action items

### Action Items
- **SMART format:** Specific, Measurable, Achievable, Relevant, Time-bound
- **Prioritize ruthlessly:** Max 5 action items (focus > volume)
- **Track weekly:** Check-ins at every standup or weekly review
- **Close the loop:** Review action item progress at next retrospective

---

## 🔗 Related Documentation

### Phase 3 Context
- **Story:** `docs/stories/STORY-096-phase3-parallel-squad-attack.md`
- **Test Report:** `docs/testing/phase3-test-report.md`
- **Burn-Down Chart:** `docs/velocity/burn-down-chart-phase3.md`
- **Impediment Log:** `docs/impediments/impediment-log-phase3.md`

### Process Documents
- **Phase Pre-Flight Checklist:** `docs/processes/phase-preflight-checklist.md`
- **Sprint Planning:** `docs/sprints/value-sprint-01.md`
- **Baseline Analysis:** `docs/sprints/value-sprint-01-baseline-analysis.md`
- **MoSCoW Prioritization:** `docs/sprints/value-sprint-01-moscow-prioritization.md`

---

## 🚀 Next Ceremonies

### Week 2 Sprint Review (End of Phase 4)
- **Date:** TBD (after Phase 4 completion)
- **Focus:** Production deployment, monitoring setup, early metrics
- **Preparation:** 2-3 days before ceremony

### Week 2 Sprint Retrospective
- **Date:** TBD (same day as Week 2 review)
- **Focus:** Action item progress from Phase 3, Week 1 vs Week 2 comparison
- **Preparation:** 1 day before ceremony

---

**Maintained by:** @sm (River)
**Created:** 2026-01-30
**Last Updated:** 2026-01-30
