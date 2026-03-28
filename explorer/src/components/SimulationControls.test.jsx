import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SimulationControls from './SimulationControls';

describe('SimulationControls', () => {
    const defaultProps = {
        isPlaying: false,
        onToggle: vi.fn(),
        onReset: vi.fn(),
        stepCount: 0,
        speed: 2500,
        onSpeedChange: vi.fn(),
        currentLabel: '',
    };

    it('renders help button', () => {
        render(<SimulationControls {...defaultProps} />);
        expect(screen.getByLabelText('Show guide')).toBeInTheDocument();
    });

    it('shows guide popover when help button is clicked', async () => {
        const user = userEvent.setup();
        render(<SimulationControls {...defaultProps} />);

        await user.click(screen.getByLabelText('Show guide'));

        expect(screen.getByText('Ghost Runner')).toBeInTheDocument();
        expect(screen.getByText('Code Analyzer')).toBeInTheDocument();
    });

    it('guide contains key explanations', async () => {
        const user = userEvent.setup();
        render(<SimulationControls {...defaultProps} />);

        await user.click(screen.getByLabelText('Show guide'));

        // Ghost Runner section
        expect(screen.getByText(/walks through your call graph/)).toBeInTheDocument();
        expect(screen.getByText(/Trail/)).toBeInTheDocument();
        expect(screen.getByText(/Strategies/)).toBeInTheDocument();
        expect(screen.getByText(/Progress/)).toBeInTheDocument();

        // Code Analyzer section
        expect(screen.getByText(/Abstract Syntax Tree/)).toBeInTheDocument();
        expect(screen.getByText(/File dependencies/)).toBeInTheDocument();
    });

    it('closes guide when close button is clicked', async () => {
        const user = userEvent.setup();
        render(<SimulationControls {...defaultProps} />);

        await user.click(screen.getByLabelText('Show guide'));
        expect(screen.getByText('Ghost Runner')).toBeInTheDocument();

        await user.click(screen.getByLabelText('Close guide'));
        expect(screen.queryByText('Ghost Runner')).not.toBeInTheDocument();
    });

    it('toggles guide on repeated clicks', async () => {
        const user = userEvent.setup();
        render(<SimulationControls {...defaultProps} />);

        const helpBtn = screen.getByLabelText('Show guide');

        await user.click(helpBtn);
        expect(screen.getByText('Ghost Runner')).toBeInTheDocument();

        await user.click(helpBtn);
        expect(screen.queryByText('Ghost Runner')).not.toBeInTheDocument();
    });

    it('shows play button when not playing', () => {
        render(<SimulationControls {...defaultProps} isPlaying={false} />);
        expect(screen.getByLabelText('Play simulation')).toBeInTheDocument();
    });

    it('shows pause button when playing', () => {
        render(<SimulationControls {...defaultProps} isPlaying={true} />);
        expect(screen.getByLabelText('Pause simulation')).toBeInTheDocument();
    });

    it('displays current ghost label when provided', () => {
        render(<SimulationControls {...defaultProps} currentLabel="main" />);
        expect(screen.getByText(/main/)).toBeInTheDocument();
    });
});
