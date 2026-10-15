import { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button } from '@/components/ui/Button';
import { TextField } from '@/components/ui/Field';
import { Alert, Card, CardBody, ErrorMessage } from '@/components/ui/Primitives';
import { loginSchema, type LoginValues } from '@/schemas/forms';
import { useAuth } from '@/hooks/authContext';
import { ApiError, toApiError } from '@/api/client';

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [submitError, setSubmitError] = useState<ApiError | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginValues>({ resolver: zodResolver(loginSchema) });

  async function onSubmit(values: LoginValues) {
    setSubmitError(null);
    try {
      await login(values.email, values.password);
      // Return them to wherever they were headed before being redirected.
      const next = searchParams.get('next');
      navigate(next && next.startsWith('/') ? next : '/dashboard', { replace: true });
    } catch (error) {
      setSubmitError(toApiError(error));
    }
  }

  return (
    <div className="mx-auto flex max-w-md flex-col justify-center px-4 py-16">
      <div className="mb-6 text-center">
        <h1 className="text-2xl">Sign in to ResumeIQ</h1>
        <p className="mt-2 text-sm text-ink-500">
          Your saved analyses are private to your account.
        </p>
      </div>

      <Card>
        <CardBody className="space-y-5">
          {searchParams.get('password') === 'changed' && (
            <Alert tone="success">
              Your password has been changed. All sessions have ended. Sign in with your new
              password.
            </Alert>
          )}
          {submitError && <ErrorMessage error={submitError} />}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
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
              autoComplete="current-password"
              required
              error={errors.password?.message}
              {...register('password')}
            />
            <Button
              type="submit"
              className="w-full"
              isLoading={isSubmitting}
              loadingLabel="Signing in…"
            >
              Sign in
            </Button>
          </form>
        </CardBody>
      </Card>

      <p className="mt-6 text-center text-sm text-ink-600">
        No account yet?{' '}
        <Link to="/register" className="font-medium text-brand-700 underline underline-offset-2">
          Create one
        </Link>
      </p>
    </div>
  );
}
