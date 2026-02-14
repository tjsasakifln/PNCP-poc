/**
 * Tests for PipelineCard component (STORY-250)
 */

import React from 'react';
import { render, screen, fireEvent, within } from '@testing-library/react';
import { PipelineCard } from '../../app/pipeline/PipelineCard';
import type { PipelineItem } from '../../app/pipeline/types';

// Mock @dnd-kit/sortable
jest.mock('@dnd-kit/sortable', () => ({
  useSortable: () => ({
    attributes: {},
    listeners: {},
    setNodeRef: jest.fn(),
    transform: null,
    transition: null,
    isDragging: false,
  }),
}));

// Mock @dnd-kit/utilities
jest.mock('@dnd-kit/utilities', () => ({
  CSS: { Transform: { toString: () => null } },
}));

describe('PipelineCard', () => {
  const mockItem: PipelineItem = {
    id: "item-1",
    user_id: "user-1",
    pncp_id: "12345",
    objeto: "Aquisição de uniformes para guardas municipais",
    orgao: "Prefeitura de São Paulo",
    uf: "SP",
    valor_estimado: 150000,
    data_encerramento: "2026-03-01T23:59:59",
    link_pncp: "https://pncp.gov.br/app/editais/12345",
    stage: "descoberta",
    notes: "Nota de teste",
    created_at: "2026-02-14T10:00:00",
    updated_at: "2026-02-14T10:00:00",
  };

  const mockOnRemove = jest.fn();
  const mockOnUpdateNotes = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Basic rendering', () => {
    it('renders objeto text', () => {
      render(<PipelineCard item={mockItem} />);

      expect(screen.getByText(mockItem.objeto)).toBeInTheDocument();
    });

    it('truncates objeto to 80 chars when longer', () => {
      const longObjeto = 'A'.repeat(100);
      const longItem = { ...mockItem, objeto: longObjeto };

      render(<PipelineCard item={longItem} />);

      expect(screen.getByText(longObjeto.slice(0, 80) + "...")).toBeInTheDocument();
    });

    it('renders UF badge', () => {
      render(<PipelineCard item={mockItem} />);

      expect(screen.getByText('SP')).toBeInTheDocument();
    });

    it('renders orgao name', () => {
      render(<PipelineCard item={mockItem} />);

      expect(screen.getByText('Prefeitura de São Paulo')).toBeInTheDocument();
    });

    it('renders formatted currency value', () => {
      render(<PipelineCard item={mockItem} />);

      // Brazilian currency format
      expect(screen.getByText(/R\$\s*150\.000,00/)).toBeInTheDocument();
    });

    it('does not render UF badge when UF is null', () => {
      const itemWithoutUF = { ...mockItem, uf: null };
      render(<PipelineCard item={itemWithoutUF} />);

      expect(screen.queryByText('SP')).not.toBeInTheDocument();
    });

    it('does not render orgao when null', () => {
      const itemWithoutOrgao = { ...mockItem, orgao: null };
      render(<PipelineCard item={itemWithoutOrgao} />);

      expect(screen.queryByText('Prefeitura de São Paulo')).not.toBeInTheDocument();
    });
  });

  describe('Urgency indicators', () => {
    it('shows "Encerrado" when daysRemaining <= 0', () => {
      // Set date to past
      const pastItem = {
        ...mockItem,
        data_encerramento: "2025-01-01T23:59:59",
      };

      render(<PipelineCard item={pastItem} />);

      expect(screen.getByText('Encerrado')).toBeInTheDocument();
    });

    it('shows "Xd restantes" when days remaining', () => {
      // Set date to future (e.g., 10 days from now)
      const futureDate = new Date();
      futureDate.setDate(futureDate.getDate() + 10);
      const futureItem = {
        ...mockItem,
        data_encerramento: futureDate.toISOString(),
      };

      render(<PipelineCard item={futureItem} />);

      expect(screen.getByText(/\d+d restantes/)).toBeInTheDocument();
    });

    it('does not show urgency when data_encerramento is null', () => {
      const itemWithoutDate = { ...mockItem, data_encerramento: null };

      render(<PipelineCard item={itemWithoutDate} />);

      expect(screen.queryByText(/Encerrado|restantes/)).not.toBeInTheDocument();
    });
  });

  describe('Link to edital', () => {
    it('shows "Ver edital" link with correct href', () => {
      render(<PipelineCard item={mockItem} />);

      const link = screen.getByText('Ver edital');
      expect(link).toHaveAttribute('href', 'https://pncp.gov.br/app/editais/12345');
      expect(link).toHaveAttribute('target', '_blank');
      expect(link).toHaveAttribute('rel', 'noopener noreferrer');
    });

    it('does not show link when link_pncp is null', () => {
      const itemWithoutLink = { ...mockItem, link_pncp: null };

      render(<PipelineCard item={itemWithoutLink} />);

      expect(screen.queryByText('Ver edital')).not.toBeInTheDocument();
    });
  });

  describe('Notes functionality', () => {
    it('shows notes text when notes exist', () => {
      render(<PipelineCard item={mockItem} />);

      expect(screen.getByText('Nota de teste')).toBeInTheDocument();
    });

    it('truncates notes to 60 chars when longer', () => {
      const longNotes = 'A'.repeat(80);
      const itemWithLongNotes = { ...mockItem, notes: longNotes };

      render(<PipelineCard item={itemWithLongNotes} />);

      expect(screen.getByText(longNotes.slice(0, 60) + "...")).toBeInTheDocument();
    });

    it('shows "Anotar" button when no notes', () => {
      const itemWithoutNotes = { ...mockItem, notes: null };

      render(<PipelineCard item={itemWithoutNotes} />);

      expect(screen.getByText('Anotar')).toBeInTheDocument();
    });

    it('shows "Editar nota" button when notes exist', () => {
      render(<PipelineCard item={mockItem} />);

      expect(screen.getByText('Editar nota')).toBeInTheDocument();
    });

    it('clicking "Anotar" opens textarea for editing', () => {
      const itemWithoutNotes = { ...mockItem, notes: null };

      render(<PipelineCard item={itemWithoutNotes} />);

      const anotarButton = screen.getByText('Anotar');
      fireEvent.click(anotarButton);

      const textarea = screen.getByPlaceholderText('Suas anotações...');
      expect(textarea).toBeInTheDocument();
    });

    it('clicking notes text opens editor', () => {
      render(<PipelineCard item={mockItem} />);

      const notesText = screen.getByText('Nota de teste');
      fireEvent.click(notesText);

      const textarea = screen.getByDisplayValue('Nota de teste');
      expect(textarea).toBeInTheDocument();
    });

    it('clicking "Salvar" in notes calls onUpdateNotes', () => {
      render(<PipelineCard item={mockItem} onUpdateNotes={mockOnUpdateNotes} />);

      // Open editor
      const editButton = screen.getByText('Editar nota');
      fireEvent.click(editButton);

      // Change note
      const textarea = screen.getByDisplayValue('Nota de teste');
      fireEvent.change(textarea, { target: { value: 'Nova nota' } });

      // Save
      const saveButton = screen.getByText('Salvar');
      fireEvent.click(saveButton);

      expect(mockOnUpdateNotes).toHaveBeenCalledWith('Nova nota');
    });

    it('clicking "Cancelar" in notes closes editor', () => {
      render(<PipelineCard item={mockItem} />);

      // Open editor
      const editButton = screen.getByText('Editar nota');
      fireEvent.click(editButton);

      // Change note
      const textarea = screen.getByDisplayValue('Nota de teste');
      fireEvent.change(textarea, { target: { value: 'Nova nota' } });

      // Cancel
      const cancelButton = screen.getByText('Cancelar');
      fireEvent.click(cancelButton);

      // Editor should be closed
      expect(screen.queryByPlaceholderText('Suas anotações...')).not.toBeInTheDocument();
      // Original note should be visible again
      expect(screen.getByText('Nota de teste')).toBeInTheDocument();
    });

    it('canceling notes editor reverts changes', () => {
      render(<PipelineCard item={mockItem} />);

      // Open editor
      const editButton = screen.getByText('Editar nota');
      fireEvent.click(editButton);

      // Change note
      const textarea = screen.getByDisplayValue('Nota de teste');
      fireEvent.change(textarea, { target: { value: 'Nova nota temporária' } });

      // Cancel
      const cancelButton = screen.getByText('Cancelar');
      fireEvent.click(cancelButton);

      // Open editor again
      const editButton2 = screen.getByText('Editar nota');
      fireEvent.click(editButton2);

      // Should show original note, not the temporary change
      const newTextarea = screen.getByDisplayValue('Nota de teste');
      expect(newTextarea).toBeInTheDocument();
    });
  });

  describe('Remove functionality', () => {
    it('clicking "Remover" calls onRemove', () => {
      render(<PipelineCard item={mockItem} onRemove={mockOnRemove} />);

      const removeButton = screen.getByText('Remover');
      fireEvent.click(removeButton);

      expect(mockOnRemove).toHaveBeenCalledTimes(1);
    });

    it('does not show "Remover" button when onRemove is undefined', () => {
      render(<PipelineCard item={mockItem} />);

      expect(screen.queryByText('Remover')).not.toBeInTheDocument();
    });
  });

  describe('Drag and drop styling', () => {
    it('applies opacity and ring when isDragging prop is true', () => {
      const { container } = render(<PipelineCard item={mockItem} isDragging={true} />);

      const card = container.firstChild;
      expect(card).toHaveClass('opacity-50');
      expect(card).toHaveClass('shadow-lg');
      expect(card).toHaveClass('ring-2');
      expect(card).toHaveClass('ring-brand-blue');
    });

    it('does not apply dragging styles when isDragging is false', () => {
      const { container } = render(<PipelineCard item={mockItem} isDragging={false} />);

      const card = container.firstChild;
      expect(card).not.toHaveClass('opacity-50');
      expect(card).not.toHaveClass('ring-2');
    });
  });

  describe('Event propagation', () => {
    it('stops propagation when clicking "Ver edital"', () => {
      const parentClick = jest.fn();

      render(
        <div onClick={parentClick}>
          <PipelineCard item={mockItem} />
        </div>
      );

      const link = screen.getByText('Ver edital');
      fireEvent.click(link);

      expect(parentClick).not.toHaveBeenCalled();
    });

    it('stops propagation when clicking "Editar nota"', () => {
      const parentClick = jest.fn();

      render(
        <div onClick={parentClick}>
          <PipelineCard item={mockItem} />
        </div>
      );

      const editButton = screen.getByText('Editar nota');
      fireEvent.click(editButton);

      expect(parentClick).not.toHaveBeenCalled();
    });

    it('stops propagation when clicking "Remover"', () => {
      const parentClick = jest.fn();

      render(
        <div onClick={parentClick}>
          <PipelineCard item={mockItem} onRemove={mockOnRemove} />
        </div>
      );

      const removeButton = screen.getByText('Remover');
      fireEvent.click(removeButton);

      expect(parentClick).not.toHaveBeenCalled();
    });
  });

  describe('Urgency border color', () => {
    it('applies red border when days remaining <= 0', () => {
      const pastItem = {
        ...mockItem,
        data_encerramento: "2025-01-01T23:59:59",
      };

      const { container } = render(<PipelineCard item={pastItem} />);
      const card = container.firstChild;

      expect(card).toHaveClass('border-l-red-500');
    });

    it('applies orange border when days remaining <= 3', () => {
      const soonItem = {
        ...mockItem,
        data_encerramento: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString(), // 2 days
      };

      const { container } = render(<PipelineCard item={soonItem} />);
      const card = container.firstChild;

      expect(card).toHaveClass('border-l-orange-500');
    });

    it('applies yellow border when days remaining <= 7', () => {
      const weekItem = {
        ...mockItem,
        data_encerramento: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString(), // 5 days
      };

      const { container } = render(<PipelineCard item={weekItem} />);
      const card = container.firstChild;

      expect(card).toHaveClass('border-l-yellow-500');
    });

    it('applies transparent border when no urgency', () => {
      const futureItem = {
        ...mockItem,
        data_encerramento: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(), // 30 days
      };

      const { container } = render(<PipelineCard item={futureItem} />);
      const card = container.firstChild;

      expect(card).toHaveClass('border-l-transparent');
    });
  });
});
