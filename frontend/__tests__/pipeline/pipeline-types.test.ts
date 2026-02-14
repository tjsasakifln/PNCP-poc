/**
 * Tests for pipeline types configuration (STORY-250)
 */

import { STAGES_ORDER, STAGE_CONFIG, PipelineStage } from '../../app/pipeline/types';

describe('Pipeline Types', () => {
  describe('STAGES_ORDER', () => {
    it('has exactly 5 stages', () => {
      expect(STAGES_ORDER).toHaveLength(5);
    });

    it('contains all valid stages', () => {
      const expectedStages = ['descoberta', 'analise', 'preparando', 'enviada', 'resultado'];
      expect(STAGES_ORDER).toEqual(expectedStages);
    });

    it('stages are in correct order', () => {
      expect(STAGES_ORDER[0]).toBe('descoberta');
      expect(STAGES_ORDER[1]).toBe('analise');
      expect(STAGES_ORDER[2]).toBe('preparando');
      expect(STAGES_ORDER[3]).toBe('enviada');
      expect(STAGES_ORDER[4]).toBe('resultado');
    });

    it('all stages are unique', () => {
      const uniqueStages = new Set(STAGES_ORDER);
      expect(uniqueStages.size).toBe(STAGES_ORDER.length);
    });
  });

  describe('STAGE_CONFIG', () => {
    it('has config for every stage in STAGES_ORDER', () => {
      STAGES_ORDER.forEach((stage) => {
        expect(STAGE_CONFIG[stage]).toBeDefined();
      });
    });

    it('each config entry has label property', () => {
      STAGES_ORDER.forEach((stage) => {
        expect(STAGE_CONFIG[stage].label).toBeDefined();
        expect(typeof STAGE_CONFIG[stage].label).toBe('string');
        expect(STAGE_CONFIG[stage].label.length).toBeGreaterThan(0);
      });
    });

    it('each config entry has color property', () => {
      STAGES_ORDER.forEach((stage) => {
        expect(STAGE_CONFIG[stage].color).toBeDefined();
        expect(typeof STAGE_CONFIG[stage].color).toBe('string');
        expect(STAGE_CONFIG[stage].color.length).toBeGreaterThan(0);
      });
    });

    it('each config entry has icon property', () => {
      STAGES_ORDER.forEach((stage) => {
        expect(STAGE_CONFIG[stage].icon).toBeDefined();
        expect(typeof STAGE_CONFIG[stage].icon).toBe('string');
        expect(STAGE_CONFIG[stage].icon.length).toBeGreaterThan(0);
      });
    });

    describe('descoberta stage', () => {
      it('has correct label', () => {
        expect(STAGE_CONFIG.descoberta.label).toBe('Descoberta');
      });

      it('has blue color scheme', () => {
        expect(STAGE_CONFIG.descoberta.color).toContain('blue');
      });

      it('has search icon', () => {
        expect(STAGE_CONFIG.descoberta.icon).toBe('🔍');
      });
    });

    describe('analise stage', () => {
      it('has correct label', () => {
        expect(STAGE_CONFIG.analise.label).toBe('Em Análise');
      });

      it('has yellow color scheme', () => {
        expect(STAGE_CONFIG.analise.color).toContain('yellow');
      });

      it('has clipboard icon', () => {
        expect(STAGE_CONFIG.analise.icon).toBe('📋');
      });
    });

    describe('preparando stage', () => {
      it('has correct label', () => {
        expect(STAGE_CONFIG.preparando.label).toBe('Preparando Proposta');
      });

      it('has purple color scheme', () => {
        expect(STAGE_CONFIG.preparando.color).toContain('purple');
      });

      it('has memo icon', () => {
        expect(STAGE_CONFIG.preparando.icon).toBe('📝');
      });
    });

    describe('enviada stage', () => {
      it('has correct label', () => {
        expect(STAGE_CONFIG.enviada.label).toBe('Enviada');
      });

      it('has green color scheme', () => {
        expect(STAGE_CONFIG.enviada.color).toContain('green');
      });

      it('has outbox icon', () => {
        expect(STAGE_CONFIG.enviada.icon).toBe('📤');
      });
    });

    describe('resultado stage', () => {
      it('has correct label', () => {
        expect(STAGE_CONFIG.resultado.label).toBe('Resultado');
      });

      it('has gray color scheme', () => {
        expect(STAGE_CONFIG.resultado.color).toContain('gray');
      });

      it('has checkered flag icon', () => {
        expect(STAGE_CONFIG.resultado.icon).toBe('🏁');
      });
    });
  });

  describe('Color class consistency', () => {
    it('all colors have light mode classes', () => {
      STAGES_ORDER.forEach((stage) => {
        const color = STAGE_CONFIG[stage].color;
        // Should have bg and text classes
        expect(color).toMatch(/bg-\w+-\d+/);
        expect(color).toMatch(/text-\w+-\d+/);
      });
    });

    it('all colors have dark mode classes', () => {
      STAGES_ORDER.forEach((stage) => {
        const color = STAGE_CONFIG[stage].color;
        // Should have dark: prefix for dark mode
        expect(color).toContain('dark:');
      });
    });

    it('all colors follow Tailwind CSS format', () => {
      STAGES_ORDER.forEach((stage) => {
        const color = STAGE_CONFIG[stage].color;
        // Should be valid Tailwind classes separated by spaces
        const classes = color.split(' ');
        expect(classes.length).toBeGreaterThan(0);
        classes.forEach((cls) => {
          expect(cls).toMatch(/^(bg-|text-|dark:)/);
        });
      });
    });
  });

  describe('Type safety', () => {
    it('STAGES_ORDER elements are assignable to PipelineStage', () => {
      STAGES_ORDER.forEach((stage) => {
        // This will cause a TypeScript error if types don't match
        const typedStage: PipelineStage = stage;
        expect(typedStage).toBe(stage);
      });
    });

    it('STAGE_CONFIG keys are PipelineStage types', () => {
      const stages: PipelineStage[] = ['descoberta', 'analise', 'preparando', 'enviada', 'resultado'];
      stages.forEach((stage) => {
        expect(STAGE_CONFIG[stage]).toBeDefined();
      });
    });
  });

  describe('Configuration completeness', () => {
    it('no extra stages in STAGE_CONFIG', () => {
      const configKeys = Object.keys(STAGE_CONFIG);
      configKeys.forEach((key) => {
        expect(STAGES_ORDER).toContain(key as PipelineStage);
      });
    });

    it('STAGE_CONFIG has exactly 5 entries', () => {
      expect(Object.keys(STAGE_CONFIG)).toHaveLength(5);
    });

    it('all stages have non-empty labels', () => {
      STAGES_ORDER.forEach((stage) => {
        expect(STAGE_CONFIG[stage].label.trim()).not.toBe('');
      });
    });

    it('all stages have non-empty colors', () => {
      STAGES_ORDER.forEach((stage) => {
        expect(STAGE_CONFIG[stage].color.trim()).not.toBe('');
      });
    });

    it('all stages have non-empty icons', () => {
      STAGES_ORDER.forEach((stage) => {
        expect(STAGE_CONFIG[stage].icon.trim()).not.toBe('');
      });
    });
  });

  describe('Icon uniqueness', () => {
    it('all icons are unique', () => {
      const icons = STAGES_ORDER.map((stage) => STAGE_CONFIG[stage].icon);
      const uniqueIcons = new Set(icons);
      expect(uniqueIcons.size).toBe(icons.length);
    });
  });

  describe('Label uniqueness', () => {
    it('all labels are unique', () => {
      const labels = STAGES_ORDER.map((stage) => STAGE_CONFIG[stage].label);
      const uniqueLabels = new Set(labels);
      expect(uniqueLabels.size).toBe(labels.length);
    });
  });
});
