import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button } from '@/components/ui/Button';
import { TextField } from '@/components/ui/Field';
import { Card, CardBody, ErrorMessage } from '@/components/ui/Primitives';
import { registerSchema, type RegisterValues } from '@/schemas/forms';
import { useAuth } from '@/hooks/authContext';
import { ApiError, toApiError } from '@/api/client';

export function RegisterPage() {
  const { register: createAccount } = useAuth();
  const navigate = useNavigate();
  const [submitError, setSubmitError] = useState<ApiError | null>(null);

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<RegisterValues>({ resolver: zodResolver(registerSchema) });

  async function onSubmit(values: RegisterValues) {
    setSubmitError(null);
    try {
      await createAccount(values.full_name, values.email, values.password);
      navigate('/dashboard', { replace: true });
    } catch (error) {
      const apiError = toApiError(error);
      // Map server field errors back onto the form where possible, so the
      // message lands next to the input that caused it.
      const fieldEntries = Object.entries(apiError.fields);
      if (fieldEntries.length > 0) {
        fieldEntries.forEach(([field, message]) => {
          if (field === 'email' || field === 'password' || field === 'full_name') {
            setError(field, { message });
          }
        });
      } else {
        setSubmitError(apiError);
      }
    }
  }

  return (
    <div className="mx-auto flex max-w-md flex-col justify-center px-4 py-16">
      <div className="mb-6 text-center">
        <h1 className="text-2xl">Create your account</h1>
        <p className="mt-2 text-sm text-ink-500">
          Free to try. Read the privacy information before uploading a resume.
        </p>
      </div>

      <Card>
        <CardBody className="space-y-5">
          {submitError && <ErrorMessage error={submitError} />}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
            <TextField
              label="Full name"
              autoComplete="name"
              required
              error={errors.full_name?.message}
              {...register('full_name')}
            />
            <TextField
              label="Email address"
              type="email"
              autoComplete="email"
              required
              error={errors.email?.message}
              {...register('email')}
            />
            <TextField
              label="Password"
              type="password"
              autoComplete="new-password"
              required
              hint="At least 10 characters, including a letter and a number."
              error={errors.password?.message}
              {...register('password')}
            />
            <TextField
              label="Confirm password"
              type="password"
              autoComplete="new-password"
              required
              error={errors.confirm_password?.message}
              {...register('confirm_password')}
            />
            <Button
              type="submit"
              className="w-full"
              isLoading={isSubmitting}
              loadingLabel="Creating account…"
            >
              Create account
            </Button>
          </form>

          <p className="text-xs leading-relaxed text-ink-500">
            By creating an account you agree that your analysis results will be stored so you can
            revisit them. You can delete any analysis, or your entire account, at any time. See the{' '}
            <Link to="/privacy" className="underline underline-offset-2">
              privacy page
            </Link>{' '}
            for exactly what is kept.
          </p>
        </CardBody>
      </Card>

      <p className="mt-6 text-center text-sm text-ink-600">
        Already registered?{' '}
        <Link to="/login" className="font-medium text-brand-700 underline underline-offset-2">
          Sign in
        </Link>
      </p>
    </div>
  );
}
