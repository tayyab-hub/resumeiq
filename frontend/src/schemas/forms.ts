import { z } from 'zod';

/**
 * Client-side validation.
 *
 * These rules mirror the Pydantic models on the server, and exist for user
 * experience: instant feedback without a round trip. The server re-validates
 * everything, because client validation can be bypassed trivially and is
 * therefore never a security control.
 */

const password = z
  .string()
  .min(10, 'Password must be at least 10 characters long')
  .max(128, 'Password must be 128 characters or fewer')
  .regex(/[A-Za-z]/, 'Password must contain at least one letter')
  .regex(/\d/, 'Password must contain at least one number');

export const loginSchema = z.object({
  email: z.string().min(1, 'Email is required').email('Enter a valid email address'),
  password: z.string().min(1, 'Password is required'),
});
export type LoginValues = z.infer<typeof loginSchema>;

export const registerSchema = z
  .object({
    full_name: z
      .string()
      .trim()
      .min(1, 'Your name is required')
      .max(120, 'Name must be 120 characters or fewer'),
    email: z.string().min(1, 'Email is required').email('Enter a valid email address'),
    password,
    confirm_password: z.string().min(1, 'Please confirm your password'),
  })
  .refine((values) => values.password === values.confirm_password, {
    message: 'Passwords do not match',
    path: ['confirm_password'],
  });
export type RegisterValues = z.infer<typeof registerSchema>;

export const MIN_JOB_DESCRIPTION = 200;
export const MAX_JOB_DESCRIPTION = 8000;

export const newAnalysisSchema = z.object({
  job_description: z
    .string()
    .trim()
    .min(
      MIN_JOB_DESCRIPTION,
      `Paste at least ${MIN_JOB_DESCRIPTION} characters so the requirements can be identified reliably`,
    )
    .max(MAX_JOB_DESCRIPTION, `Job descriptions are limited to ${MAX_JOB_DESCRIPTION} characters`),
  job_title: z.string().trim().max(160, 'Job title must be 160 characters or fewer').optional(),
  company_name: z.string().trim().max(160, 'Company must be 160 characters or fewer').optional(),
  title: z.string().trim().max(120, 'Title must be 120 characters or fewer').optional(),
  store_resume_text: z.boolean().default(false),
});
export type NewAnalysisValues = z.infer<typeof newAnalysisSchema>;

export const profileSchema = z.object({
  full_name: z.string().trim().min(1, 'Your name is required').max(120),
});
export type ProfileValues = z.infer<typeof profileSchema>;

export const changePasswordSchema = z
  .object({
    current_password: z.string().min(1, 'Enter your current password'),
    new_password: password,
    confirm_password: z.string().min(1, 'Please confirm your new password'),
  })
  .refine((values) => values.new_password === values.confirm_password, {
    message: 'Passwords do not match',
    path: ['confirm_password'],
  });
export type ChangePasswordValues = z.infer<typeof changePasswordSchema>;

export const RESUME_MAX_BYTES = 5 * 1024 * 1024;

export function validateResumeFile(file: File | null): string | null {
  if (!file) return 'Select your resume as a PDF file';
  if (!file.name.toLowerCase().endsWith('.pdf')) {
    return 'Only PDF files can be analysed. Export your resume as a PDF and try again.';
  }
  if (file.size === 0) return 'That file is empty. Check the file and try again.';
  if (file.size > RESUME_MAX_BYTES) {
    return 'That file is larger than 5 MB. Re-export the PDF with compressed images.';
  }
  return null;
}
