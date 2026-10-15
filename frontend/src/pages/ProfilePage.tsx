import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button } from '@/components/ui/Button';
import { TextField } from '@/components/ui/Field';
import { Alert, Card, CardBody, CardHeader } from '@/components/ui/Primitives';
import { Modal } from '@/components/ui/Modal';
import { authApi } from '@/api/auth';
import { toApiError } from '@/api/client';
import { useAuth } from '@/hooks/authContext';
import {
  changePasswordSchema,
  profileSchema,
  type ChangePasswordValues,
  type ProfileValues,
} from '@/schemas/forms';
import { formatDate } from '@/utilities/format';

export function ProfilePage() {
  const { user, setUser, logout } = useAuth();
  const navigate = useNavigate();

  const [profileMessage, setProfileMessage] = useState<string | null>(null);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [passwordMessage, setPasswordMessage] = useState<string | null>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [deletePassword, setDeletePassword] = useState('');
  const [deleteConfirmation, setDeleteConfirmation] = useState('');
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const profileForm = useForm<ProfileValues>({
    resolver: zodResolver(profileSchema),
    values: { full_name: user?.full_name ?? '' },
  });

  const passwordForm = useForm<ChangePasswordValues>({
    resolver: zodResolver(changePasswordSchema),
  });

  async function onSaveProfile(values: ProfileValues) {
    setProfileMessage(null);
    setProfileError(null);
    try {
      const updated = await authApi.updateProfile(values.full_name);
      setUser(updated);
      setProfileMessage('Your name has been updated.');
    } catch (error) {
      setProfileError(toApiError(error).what);
    }
  }

  async function onChangePassword(values: ChangePasswordValues) {
    setPasswordMessage(null);
    setPasswordError(null);
    try {
      await authApi.changePassword(values.current_password, values.new_password);
      passwordForm.reset();
      setPasswordMessage(
        'Your password has been changed. All other sessions have been signed out.',
      );
    } catch (error) {
      setPasswordError(toApiError(error).what);
    }
  }

  async function onDeleteAccount() {
    if (deleteConfirmation.trim().toUpperCase() !== 'DELETE') {
      setDeleteError('Type DELETE to confirm.');
      return;
    }
    setIsDeleting(true);
    setDeleteError(null);
    try {
      await authApi.deleteAccount(deletePassword);
      await logout();
      navigate('/', { replace: true });
    } catch (error) {
      setDeleteError(toApiError(error).what);
    } finally {
      setIsDeleting(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1>Profile &amp; settings</h1>
        {user && (
          <p className="mt-1 text-ink-600">
            {user.email} · member since {formatDate(user.created_at)}
          </p>
        )}
      </div>

      <Card>
        <CardHeader title="Your details" />
        <CardBody>
          <form onSubmit={profileForm.handleSubmit(onSaveProfile)} className="space-y-4" noValidate>
            {profileMessage && <Alert tone="success">{profileMessage}</Alert>}
            {profileError && <Alert tone="danger">{profileError}</Alert>}

            <TextField
              label="Full name"
              required
              error={profileForm.formState.errors.full_name?.message}
              {...profileForm.register('full_name')}
            />
            <TextField
              label="Email address"
              value={user?.email ?? ''}
              disabled
              readOnly
              hint="Email addresses cannot be changed in this version."
            />
            <Button type="submit" isLoading={profileForm.formState.isSubmitting}>
              Save changes
            </Button>
          </form>
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="Change password" />
        <CardBody>
          <form
            onSubmit={passwordForm.handleSubmit(onChangePassword)}
            className="space-y-4"
            noValidate
          >
            {passwordMessage && <Alert tone="success">{passwordMessage}</Alert>}
            {passwordError && <Alert tone="danger">{passwordError}</Alert>}

            <TextField
              label="Current password"
              type="password"
              autoComplete="current-password"
              required
              error={passwordForm.formState.errors.current_password?.message}
              {...passwordForm.register('current_password')}
            />
            <TextField
              label="New password"
              type="password"
              autoComplete="new-password"
              required
              hint="At least 10 characters, including a letter and a number."
              error={passwordForm.formState.errors.new_password?.message}
              {...passwordForm.register('new_password')}
            />
            <TextField
              label="Confirm new password"
              type="password"
              autoComplete="new-password"
              required
              error={passwordForm.formState.errors.confirm_password?.message}
              {...passwordForm.register('confirm_password')}
            />
            <Button type="submit" isLoading={passwordForm.formState.isSubmitting}>
              Change password
            </Button>
          </form>
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="Your data" />
        <CardBody className="space-y-3 text-sm leading-relaxed text-ink-600">
          <p>
            <span className="font-medium text-ink-900">Your PDF is not saved permanently.</span> It
            may use temporary upload storage, which is removed after processing. Results retain
            evidence snippets.
          </p>
          <p>
            The extracted text is not stored either, unless you tick the opt-in box when running an
            analysis. What is kept is the analysis itself: scores, matched and missing skills,
            detected sections, the statements that were flagged, and the job description you pasted.
          </p>
          <p>
            Deleting an analysis removes all of it. Deleting your account removes every analysis you
            have ever run.
          </p>
        </CardBody>
      </Card>

      <Card className="border-danger-500/30">
        <CardHeader title="Delete account" description="This cannot be undone." />
        <CardBody className="space-y-4">
          <p className="text-sm leading-relaxed text-ink-600">
            Permanently delete your account and every analysis attached to it.
          </p>
          <Button variant="danger" onClick={() => setIsDeleteOpen(true)}>
            Delete my account
          </Button>
        </CardBody>
      </Card>

      <Modal
        isOpen={isDeleteOpen}
        onClose={() => setIsDeleteOpen(false)}
        title="Delete your account?"
        description="Every analysis you have run will be permanently removed. This cannot be undone."
        footer={
          <>
            <Button
              variant="secondary"
              onClick={() => setIsDeleteOpen(false)}
              disabled={isDeleting}
            >
              Cancel
            </Button>
            <Button variant="danger" onClick={onDeleteAccount} isLoading={isDeleting}>
              Delete permanently
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          {deleteError && <Alert tone="danger">{deleteError}</Alert>}
          <TextField
            label="Your password"
            type="password"
            autoComplete="current-password"
            required
            value={deletePassword}
            onChange={(event) => setDeletePassword(event.target.value)}
          />
          <TextField
            label="Type DELETE to confirm"
            required
            value={deleteConfirmation}
            onChange={(event) => setDeleteConfirmation(event.target.value)}
          />
        </div>
      </Modal>
    </div>
  );
}
