/**
 * Tests for PipelineAlerts component (STORY-250)
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { PipelineAlerts } from '../../app/components/PipelineAlerts';
import type { PipelineItem } from '../../app/pipeline/types';

// Mock usePipeline hook
const mockFetchAlerts = jest.fn();
let mockAlerts: PipelineItem[] = [];

jest.mock('../../hooks/usePipeline', () => ({
  usePipeline: () => ({
    alerts: mockAlerts,
    fetchAlerts: mockFetchAlerts,
    items: [],
    loading: false,
    error: null,
    total: 0,
    fetchItems: jest.fn(),
    addItem: jest.fn(),
    updateItem: jest.fn(),
    removeItem: jest.fn(),
  }),
}));

// Mock useAuth
let mockSession: any = null;

jest.mock('../../app/components/AuthProvider', () => ({
  useAuth: () => ({
    session: mockSession,
  }),
}));

// Mock Next.js Link
jest.mock('next/link', () => {
  return function Link({ children, href, ...props }: any) {
    return (
      <a href={href} {...props}>
        {children}
      </a>
    );
  };
});

describe('PipelineAlerts', () => {
  const mockAlert: PipelineItem = {
    id: "alert-1",
    user_id: "user-1",
    pncp_id: "12345",
    objeto: "Aquisição urgente",
    orgao: "Prefeitura",
    uf: "SP",
    valor_estimado: 100000,
    data_encerramento: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString(), // 2 days
    link_pncp: "https://pncp.gov.br/12345",
    stage: "descoberta",
    notes: null,
    created_at: "2026-02-14T10:00:00",
    updated_at: "2026-02-14T10:00:00",
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockAlerts = [];
    mockSession = null;
  });

  describe('Rendering', () => {
    it('returns null when alerts is empty', () => {
      mockAlerts = [];
      const { container } = render(<PipelineAlerts />);

      expect(container.firstChild).toBeNull();
    });

    it('renders alert count when alerts exist', () => {
      mockAlerts = [mockAlert];

      render(<PipelineAlerts />);

      expect(screen.getByText('1')).toBeInTheDocument();
    });

    it('renders correct count for multiple alerts', () => {
      mockAlerts = [
        mockAlert,
        { ...mockAlert, id: 'alert-2', pncp_id: '67890' },
        { ...mockAlert, id: 'alert-3', pncp_id: '11111' },
      ];

      render(<PipelineAlerts />);

      expect(screen.getByText('3')).toBeInTheDocument();
    });

    it('renders link to /pipeline', () => {
      mockAlerts = [mockAlert];

      render(<PipelineAlerts />);

      const link = screen.getByRole('link');
      expect(link).toHaveAttribute('href', '/pipeline');
    });

    it('shows ping animation dot', () => {
      mockAlerts = [mockAlert];

      const { container } = render(<PipelineAlerts />);

      const pingElement = container.querySelector('.animate-ping');
      expect(pingElement).toBeInTheDocument();
    });

    it('has correct title attribute', () => {
      mockAlerts = [mockAlert];

      render(<PipelineAlerts />);

      const link = screen.getByRole('link');
      expect(link).toHaveAttribute('title', '1 licitação(ões) com prazo próximo');
    });

    it('shows correct title for multiple alerts', () => {
      mockAlerts = [
        mockAlert,
        { ...mockAlert, id: 'alert-2', pncp_id: '67890' },
      ];

      render(<PipelineAlerts />);

      const link = screen.getByRole('link');
      expect(link).toHaveAttribute('title', '2 licitação(ões) com prazo próximo');
    });
  });

  describe('Authentication and data fetching', () => {
    it('calls fetchAlerts on mount when authenticated', () => {
      mockSession = { access_token: 'test-token' };
      mockAlerts = [];

      render(<PipelineAlerts />);

      expect(mockFetchAlerts).toHaveBeenCalledTimes(1);
    });

    it('does not call fetchAlerts when not authenticated', () => {
      mockSession = null;
      mockAlerts = [];

      render(<PipelineAlerts />);

      expect(mockFetchAlerts).not.toHaveBeenCalled();
    });

    it('calls fetchAlerts when session changes to authenticated', () => {
      mockSession = null;
      const { rerender } = render(<PipelineAlerts />);

      expect(mockFetchAlerts).not.toHaveBeenCalled();

      mockSession = { access_token: 'test-token' };
      rerender(<PipelineAlerts />);

      expect(mockFetchAlerts).toHaveBeenCalledTimes(1);
    });
  });

  describe('Styling', () => {
    it('applies correct text color classes', () => {
      mockAlerts = [mockAlert];

      const { container } = render(<PipelineAlerts />);

      const link = screen.getByRole('link');
      expect(link).toHaveClass('text-orange-600');
      expect(link).toHaveClass('dark:text-orange-400');
    });

    it('applies hover state classes', () => {
      mockAlerts = [mockAlert];

      const { container } = render(<PipelineAlerts />);

      const link = screen.getByRole('link');
      expect(link).toHaveClass('hover:text-orange-700');
      expect(link).toHaveClass('dark:hover:text-orange-300');
    });

    it('has correct size and font classes', () => {
      mockAlerts = [mockAlert];

      const { container } = render(<PipelineAlerts />);

      const link = screen.getByRole('link');
      expect(link).toHaveClass('text-xs');
      expect(link).toHaveClass('font-medium');
    });

    it('ping animation has correct color', () => {
      mockAlerts = [mockAlert];

      const { container } = render(<PipelineAlerts />);

      const pingElement = container.querySelector('.animate-ping');
      expect(pingElement).toHaveClass('bg-orange-400');
    });

    it('static dot has correct color', () => {
      mockAlerts = [mockAlert];

      const { container } = render(<PipelineAlerts />);

      const dotElement = container.querySelector('.bg-orange-500');
      expect(dotElement).toBeInTheDocument();
    });
  });

  describe('Edge cases', () => {
    it('handles null alerts', () => {
      mockAlerts = null as any;

      const { container } = render(<PipelineAlerts />);

      expect(container.firstChild).toBeNull();
    });

    it('handles undefined session.access_token', () => {
      mockSession = { access_token: undefined };
      mockAlerts = [];

      render(<PipelineAlerts />);

      expect(mockFetchAlerts).not.toHaveBeenCalled();
    });

    it('renders correctly with very large alert count', () => {
      const manyAlerts = Array.from({ length: 99 }, (_, i) => ({
        ...mockAlert,
        id: `alert-${i}`,
        pncp_id: `${i}`,
      }));
      mockAlerts = manyAlerts;

      render(<PipelineAlerts />);

      expect(screen.getByText('99')).toBeInTheDocument();
    });
  });
});
