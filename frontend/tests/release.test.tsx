import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import axios from 'axios';
import { ResultsPage } from '@/pages/ResultsPage';
import { analysesApi } from '@/api/analyses';
import { restoreSession } from '@/api/client';
import { registerSchema } from '@/schemas/forms';
import sample from '@/data/sample-analysis.json';

describe('Release safety', () => {
  it('renders the complete sample without private API reads or AI mutations', () => {
    const get = vi.spyOn(analysesApi, 'get');
    render(
      <QueryClientProvider client={new QueryClient()}>
        <MemoryRouter><ResultsPage sample /></MemoryRouter>
      </QueryClientProvider>,
    );
    expect(screen.getByText('Explore Sample Analysis')).toBeInTheDocument();
    expect(sample.score_breakdown).toHaveLength(8);
    expect(get).not.toHaveBeenCalled();
    expect(screen.queryByRole('button', { name: /regenerate|try ai/i })).not.toBeInTheDocument();
    get.mockRestore();
  });

  it('rejects passwords exceeding the bcrypt byte limit even when character count fits', () => {
    const password = 'A1' + '界'.repeat(24);
    expect(registerSchema.safeParse({full_name: 'Fictional', email: 'fake@example.com', password, confirm_password: password}).success).toBe(false);
  });

  it('shares one cookie rotation between simultaneous session restorations', async () => {
    const post = vi.spyOn(axios, 'post').mockResolvedValue({data: {access_token: 'test-only', token_type: 'bearer'}});
    await Promise.all([restoreSession(), restoreSession(), restoreSession()]);
    expect(post).toHaveBeenCalledOnce();
    post.mockRestore();
  });
});
