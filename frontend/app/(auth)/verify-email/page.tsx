'use client';

import * as React from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { AlertCircle, CheckCircle, Loader2, Mail } from 'lucide-react';

import { post } from '@/lib/api';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

type VerificationStatus = 'verifying' | 'success' | 'error' | 'resend';

export default function VerifyEmailPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get('token');

  const [status, setStatus] = React.useState<VerificationStatus>('verifying');
  const [error, setError] = React.useState<string | null>(null);
  const [isResending, setIsResending] = React.useState(false);
  const [resendSuccess, setResendSuccess] = React.useState(false);

  React.useEffect(() => {
    if (!token) {
      setStatus('resend');
      return;
    }

    const verifyEmail = async () => {
      try {
        await post('/auth/verify-email', { token });
        setStatus('success');
        
        // Redirect to dashboard after 3 seconds
        setTimeout(() => {
          router.push('/dashboard');
        }, 3000);
      } catch (err: any) {
        setStatus('error');
        setError(err?.message || 'Failed to verify email. The link may be invalid or expired.');
      }
    };

    verifyEmail();
  }, [token, router]);

  const handleResend = async () => {
    setIsResending(true);
    setResendSuccess(false);
    setError(null);

    try {
      await post('/auth/resend-verification');
      setResendSuccess(true);
    } catch (err: any) {
      setError(err?.message || 'Failed to resend verification email.');
    } finally {
      setIsResending(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1 text-center">
          <CardTitle className="text-2xl font-bold">Email Verification</CardTitle>
          <CardDescription>
            {status === 'verifying' && 'Verifying your email address...'}
            {status === 'success' && 'Your email has been verified!'}
            {status === 'error' && 'Verification failed'}
            {status === 'resend' && 'Verify your email address'}
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-4">
          {status === 'verifying' && (
            <div className="flex flex-col items-center justify-center py-8">
              <Loader2 className="h-12 w-12 animate-spin text-primary mb-4" />
              <p className="text-sm text-muted-foreground">
                Please wait while we verify your email...
              </p>
            </div>
          )}

          {status === 'success' && (
            <Alert variant="success">
              <CheckCircle className="h-4 w-4" />
              <AlertTitle>Success!</AlertTitle>
              <AlertDescription>
                Your email has been verified successfully. Redirecting you to the dashboard...
              </AlertDescription>
            </Alert>
          )}

          {status === 'error' && (
            <>
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>Verification Failed</AlertTitle>
                <AlertDescription>{error}</AlertDescription>
              </Alert>

              <div className="flex flex-col space-y-2">
                <Button
                  onClick={handleResend}
                  loading={isResending}
                  loadingText="Sending..."
                  className="w-full"
                >
                  <Mail className="mr-2 h-4 w-4" />
                  Resend verification email
                </Button>

                <Link href="/login" className="block">
                  <Button variant="outline" className="w-full">
                    Back to sign in
                  </Button>
                </Link>
              </div>
            </>
          )}

          {status === 'resend' && (
            <>
              {resendSuccess ? (
                <Alert variant="success">
                  <CheckCircle className="h-4 w-4" />
                  <AlertTitle>Email sent!</AlertTitle>
                  <AlertDescription>
                    Check your inbox for the verification link. If you don&apos;t see it, check your spam folder.
                  </AlertDescription>
                </Alert>
              ) : (
                <>
                  <div className="flex flex-col items-center justify-center py-4">
                    <Mail className="h-12 w-12 text-muted-foreground mb-4" />
                    <p className="text-sm text-muted-foreground text-center">
                      Click the button below to receive a new verification email
                    </p>
                  </div>

                  {error && (
                    <Alert variant="destructive">
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>{error}</AlertDescription>
                    </Alert>
                  )}

                  <Button
                    onClick={handleResend}
                    loading={isResending}
                    loadingText="Sending..."
                    className="w-full"
                  >
                    <Mail className="mr-2 h-4 w-4" />
                    Send verification email
                  </Button>
                </>
              )}

              <Link href="/login" className="block">
                <Button variant="outline" className="w-full">
                  Back to sign in
                </Button>
              </Link>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
