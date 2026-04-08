import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import ErrorBoundary from './ErrorBoundary';

// A component that throws on render
const ThrowingComponent = () => {
    throw new Error('test error');
};

// A component that conditionally throws
function ConditionalThrower({ shouldThrow }) {
    if (shouldThrow) throw new Error('conditional error');
    return <p>All good</p>;
}

describe('ErrorBoundary', () => {
    let consoleErrorSpy;

    beforeEach(() => {
        // Suppress React error boundary console noise
        consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    });

    it('renders children when no error occurs', () => {
        render(
            <ErrorBoundary>
                <p>Hello World</p>
            </ErrorBoundary>
        );

        expect(screen.getByText('Hello World')).toBeInTheDocument();
    });

    it('shows fallback UI when a child throws', () => {
        render(
            <ErrorBoundary>
                <ThrowingComponent />
            </ErrorBoundary>
        );

        expect(screen.getByText('Something went wrong')).toBeInTheDocument();
        expect(screen.getByText('test error')).toBeInTheDocument();
    });

    it('shows a Try Again button in the error state', () => {
        render(
            <ErrorBoundary>
                <ThrowingComponent />
            </ErrorBoundary>
        );

        expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
    });

    it('logs error via componentDidCatch', () => {
        render(
            <ErrorBoundary>
                <ThrowingComponent />
            </ErrorBoundary>
        );

        // console.error is called by React and by our componentDidCatch
        expect(consoleErrorSpy).toHaveBeenCalled();
        // Find the call from our componentDidCatch
        const catchCall = consoleErrorSpy.mock.calls.find(
            (call) => call[0] === 'ErrorBoundary caught:'
        );
        expect(catchCall).toBeDefined();
        expect(catchCall[1]).toBeInstanceOf(Error);
        expect(catchCall[1].message).toBe('test error');
    });

    it('shows fallback message for errors without a message', () => {
        const NoMessageThrower = () => {
            throw new Error();
        };

        render(
            <ErrorBoundary>
                <NoMessageThrower />
            </ErrorBoundary>
        );

        expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    });

    it('resets error state when Try Again is clicked', () => {
        // Use a ref-like flag so the component can stop throwing after reset
        let shouldThrow = true;

        function ToggleThrower() {
            if (shouldThrow) throw new Error('toggle error');
            return <p>Recovered</p>;
        }

        render(
            <ErrorBoundary>
                <ToggleThrower />
            </ErrorBoundary>
        );

        expect(screen.getByText('Something went wrong')).toBeInTheDocument();

        // Stop throwing before clicking Try Again
        shouldThrow = false;

        fireEvent.click(screen.getByRole('button', { name: /try again/i }));

        expect(screen.getByText('Recovered')).toBeInTheDocument();
        expect(screen.queryByText('Something went wrong')).not.toBeInTheDocument();
    });

    afterEach(() => {
        consoleErrorSpy.mockRestore();
    });
});
