import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Check, FilePlus2, FileText, Pencil, Trash2, X } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardBody, EmptyState, ErrorMessage, Skeleton } from '@/components/ui/Primitives';
import { ConfirmModal } from '@/components/ui/Modal';
import { analysesApi } from '@/api/analyses';
import { toApiError } from '@/api/client';
import { formatDate, formatRelative } from '@/utilities/format';
import { scoreBand } from '@/utilities/score';
import type { AnalysisSummary } from '@/types';

const PAGE_SIZE = 10;

export function HistoryPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [draftTitle, setDraftTitle] = useState('');
  const [pendingDelete, setPendingDelete] = useState<AnalysisSummary | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const renameInputRef = useRef<HTMLInputElement>(null);

  // Focus the rename field imperatively rather than with autoFocus. The prop
  // is banned because focus stolen on page load harms screen-reader users;
  // moving focus in response to the user pressing "Rename" is the expected
  // behaviour, and keying the effect on the id means it fires once per rename
  // rather than on every keystroke.
  useEffect(() => {
    if (renamingId) renameInputRef.current?.focus();
  }, [renamingId]);

  const listQuery = useQuery({
    queryKey: ['analyses', page, PAGE_SIZE],
    queryFn: () => analysesApi.list(page, PAGE_SIZE),
  });

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ['analyses'] });
    queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
  }

  const renameMutation = useMutation({
    mutationFn: ({ id, title }: { id: string; title: string }) => analysesApi.rename(id, title),
    onSuccess: () => {
      setRenamingId(null);
      setActionError(null);
      invalidate();
    },
    onError: (error) => setActionError(toApiError(error).what),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => analysesApi.remove(id),
    onSuccess: () => {
      setPendingDelete(null);
      setActionError(null);
      invalidate();
    },
    onError: (error) => setActionError(toApiError(error).what),
  });

  function startRename(item: AnalysisSummary) {
    setRenamingId(item.id);
    setDraftTitle(item.title);
    setActionError(null);
  }

  function submitRename(id: string) {
    const title = draftTitle.trim();
    if (!title) {
      setActionError('A name is required.');
      return;
    }
    renameMutation.mutate({ id, title });
  }

  const data = listQuery.data;

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1>Analysis history</h1>
          <p className="mt-1 text-ink-600">
            {data
              ? `${data.total} saved ${data.total === 1 ? 'analysis' : 'analyses'}`
              : 'Your saved analyses'}
          </p>
        </div>
        <Link to="/analyses/new">
          <Button>
            <FilePlus2 className="h-4 w-4" aria-hidden="true" />
            New analysis
          </Button>
        </Link>
      </div>

      {actionError && (
        <p
          role="alert"
          className="rounded border border-danger-500/30 bg-danger-50 px-4 py-2 text-sm text-danger-700"
        >
          {actionError}
        </p>
      )}

      <Card>
        <CardBody className="p-0">
          {listQuery.isLoading ? (
            <div className="space-y-3 p-5" role="status" aria-live="polite">
              <span className="sr-only">Loading your analyses</span>
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
            </div>
          ) : listQuery.error ? (
            <div className="p-5">
              <ErrorMessage
                error={toApiError(listQuery.error)}
                onRetry={() => void listQuery.refetch()}
              />
            </div>
          ) : !data || data.items.length === 0 ? (
            <EmptyState
              icon={FileText}
              title="No analyses saved yet"
              description="Once you compare a resume against a job description, the result will appear here so you can revisit it and track your progress."
              action={
                <Link to="/analyses/new">
                  <Button>Run your first analysis</Button>
                </Link>
              }
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[38rem] text-sm">
                <caption className="sr-only">Your saved analyses, most recent first</caption>
                <thead className="border-b border-ink-200 bg-ink-50 text-left">
                  <tr>
                    <th scope="col" className="px-5 py-3 font-medium text-ink-600">
                      Name
                    </th>
                    <th scope="col" className="px-5 py-3 font-medium text-ink-600">
                      Role
                    </th>
                    <th scope="col" className="px-5 py-3 font-medium text-ink-600">
                      Date
                    </th>
                    <th scope="col" className="px-5 py-3 text-right font-medium text-ink-600">
                      Score
                    </th>
                    <th scope="col" className="px-5 py-3 text-right font-medium text-ink-600">
                      <span className="sr-only">Actions</span>
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-ink-200">
                  {data.items.map((item) => {
                    const band = scoreBand(item.overall_score);
                    const isRenaming = renamingId === item.id;

                    return (
                      <tr key={item.id} className="hover:bg-ink-50">
                        <td className="px-5 py-3">
                          {isRenaming ? (
                            <div className="flex items-center gap-1.5">
                              <label htmlFor={`rename-${item.id}`} className="sr-only">
                                New name for {item.title}
                              </label>
                              <input
                                id={`rename-${item.id}`}
                                ref={renameInputRef}
                                value={draftTitle}
                                onChange={(event) => setDraftTitle(event.target.value)}
                                onKeyDown={(event) => {
                                  if (event.key === 'Enter') submitRename(item.id);
                                  if (event.key === 'Escape') setRenamingId(null);
                                }}
                                maxLength={120}
                                className="h-9 w-full rounded border border-ink-300 px-2 text-sm"
                              />
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => submitRename(item.id)}
                                aria-label="Save name"
                              >
                                <Check className="h-4 w-4 text-success-600" aria-hidden="true" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setRenamingId(null)}
                                aria-label="Cancel rename"
                              >
                                <X className="h-4 w-4" aria-hidden="true" />
                              </Button>
                            </div>
                          ) : (
                            <Link
                              to={`/analyses/${item.id}`}
                              className="font-medium text-ink-900 hover:text-brand-700"
                            >
                              {item.title}
                            </Link>
                          )}
                        </td>
                        <td className="px-5 py-3 text-ink-600">{item.job_title ?? '—'}</td>
                        <td className="px-5 py-3 text-ink-600">
                          <time dateTime={item.created_at} title={formatDate(item.created_at)}>
                            {formatRelative(item.created_at)}
                          </time>
                        </td>
                        <td
                          className={`px-5 py-3 text-right font-semibold tabular-nums ${band.text}`}
                        >
                          {item.overall_score}
                        </td>
                        <td className="px-5 py-3">
                          <div className="flex justify-end gap-1">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => startRename(item)}
                              aria-label={`Rename ${item.title}`}
                            >
                              <Pencil className="h-4 w-4" aria-hidden="true" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => setPendingDelete(item)}
                              aria-label={`Delete ${item.title}`}
                            >
                              <Trash2 className="h-4 w-4 text-danger-600" aria-hidden="true" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardBody>
      </Card>

      {data && data.total > PAGE_SIZE && (
        <nav aria-label="Pagination" className="flex items-center justify-between">
          <Button
            variant="secondary"
            size="sm"
            disabled={page === 1}
            onClick={() => setPage((p) => p - 1)}
          >
            Previous
          </Button>
          <p className="text-sm text-ink-600" aria-live="polite">
            Page {page} of {Math.max(1, Math.ceil(data.total / PAGE_SIZE))}
          </p>
          <Button
            variant="secondary"
            size="sm"
            disabled={!data.has_next}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
          </Button>
        </nav>
      )}

      <ConfirmModal
        isOpen={pendingDelete !== null}
        onClose={() => setPendingDelete(null)}
        onConfirm={() => pendingDelete && deleteMutation.mutate(pendingDelete.id)}
        title="Delete this analysis?"
        description={
          pendingDelete
            ? `"${pendingDelete.title}" and all of its results will be permanently removed. This cannot be undone.`
            : ''
        }
        confirmLabel="Delete permanently"
        isLoading={deleteMutation.isPending}
      />
    </div>
  );
}
