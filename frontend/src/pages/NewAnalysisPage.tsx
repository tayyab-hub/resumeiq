import { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { CheckboxField, TextAreaField, TextField } from '@/components/ui/Field';
import { Alert, Card, CardBody, CardHeader, ErrorMessage } from '@/components/ui/Primitives';
import { FileUpload } from '@/features/analysis/FileUpload';
import { analysesApi } from '@/api/analyses';
import { toApiError, type ApiError } from '@/api/client';
import {
  MAX_JOB_DESCRIPTION,
  MIN_JOB_DESCRIPTION,
  newAnalysisSchema,
  validateResumeFile,
  type NewAnalysisValues,
} from '@/schemas/forms';

export function NewAnalysisPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string | undefined>();
  const [submitError, setSubmitError] = useState<ApiError | null>(null);
  const submission = useRef<{ file: File; signature: string; key: string }>();

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<NewAnalysisValues>({
    resolver: zodResolver(newAnalysisSchema),
    defaultValues: { store_resume_text: false },
  });

  const jobDescription = watch('job_description') ?? '';

  const mutation = useMutation({
    mutationFn: analysesApi.create,
    onSuccess: (analysis) => {
      queryClient.invalidateQueries({ queryKey: ['analyses'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
      queryClient.setQueryData(['analysis', analysis.id], analysis);
      navigate(`/analyses/${analysis.id}`);
    },
    onError: (error) => setSubmitError(toApiError(error)),
  });

  function onSubmit(values: NewAnalysisValues) {
    if (mutation.isPending) return;
    const problem = validateResumeFile(file);
    if (problem || !file) {
      setFileError(problem ?? 'Select your resume as a PDF file');
      return;
    }

    setFileError(undefined);
    setSubmitError(null);
    const signature = JSON.stringify(values);
    if (submission.current?.file !== file || submission.current.signature !== signature) {
      submission.current = { file, signature, key: crypto.randomUUID() };
    }
    mutation.mutate({
      requestKey: submission.current.key,
      resume: file,
      jobDescription: values.job_description,
      jobTitle: values.job_title,
      companyName: values.company_name,
      title: values.title,
      storeResumeText: values.store_resume_text,
    });
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1>New analysis</h1>
        <p className="mt-2 max-w-prose text-ink-600">
          Upload your resume and paste the job description. The comparison runs against a published
          rubric, and every point in the result is traceable back to your document.
        </p>
      </div>

      {submitError && <ErrorMessage error={submitError} />}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6" noValidate>
        <Card>
          <CardHeader title="1. Your resume" />
          <CardBody>
            <FileUpload file={file} onChange={setFile} error={fileError} />
          </CardBody>
        </Card>

        <Card>
          <CardHeader
            title="2. The job description"
            description="Paste the full posting, including the requirements section."
          />
          <CardBody className="space-y-4">
            <TextAreaField
              label="Job description"
              rows={12}
              required
              placeholder="Paste the complete job description here…"
              error={errors.job_description?.message}
              hint={`Between ${MIN_JOB_DESCRIPTION} and ${MAX_JOB_DESCRIPTION} characters.`}
              {...register('job_description')}
            />
            <p className="text-right text-xs tabular-nums text-ink-500" aria-live="polite">
              {jobDescription.length} / {MAX_JOB_DESCRIPTION} characters
            </p>

            <div className="grid gap-4 sm:grid-cols-2">
              <TextField
                label="Job title"
                placeholder="Junior Backend Developer"
                hint="Optional. Detected automatically if omitted."
                error={errors.job_title?.message}
                {...register('job_title')}
              />
              <TextField
                label="Company"
                placeholder="Acme"
                hint="Optional."
                error={errors.company_name?.message}
                {...register('company_name')}
              />
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="3. Saving options" />
          <CardBody className="space-y-4">
            <TextField
              label="Name this analysis"
              placeholder="Left blank, we will use the job title"
              error={errors.title?.message}
              {...register('title')}
            />

            <CheckboxField
              label="Store the extracted resume text with this analysis"
              hint="Off by default. Turning it on lets you regenerate AI suggestions later without re-uploading, but means the text of your resume is kept in the database until you delete the analysis."
              {...register('store_resume_text')}
            />

            <Alert tone="info" title="What happens to your file">
              Your PDF may be buffered in temporary storage during upload and is removed after
              processing. Results retain evidence snippets and flagged statements. Full extracted
              text is saved only if you opt in.
            </Alert>
          </CardBody>
        </Card>

        <div className="flex flex-wrap items-center gap-3">
          <Button type="submit" size="lg" isLoading={mutation.isPending} loadingLabel="Analysing…">
            Run analysis
          </Button>
          <Button variant="secondary" size="lg" onClick={() => navigate(-1)}>
            Cancel
          </Button>
        </div>

        {mutation.isPending && (
          <div
            role="status"
            aria-live="polite"
            className="flex items-center gap-3 rounded-lg border border-ink-200 bg-white px-4 py-3 text-sm text-ink-600"
          >
            <Loader2 className="h-4 w-4 animate-spin text-brand-600" aria-hidden="true" />
            Extracting text, comparing against the job description, and scoring. This usually takes
            a few seconds — longer if the server is waking from idle.
          </div>
        )}
      </form>
    </div>
  );
}
