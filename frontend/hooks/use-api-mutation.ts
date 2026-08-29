'use client';

import {
  useMutation,
  UseMutationOptions,
  UseMutationResult,
  useQueryClient,
} from '@tanstack/react-query';
import { toast } from 'sonner';
import type { ApiError } from '@/types';
import { post, put, patch, remove, AxiosRequestConfig } from '@/lib/api';

export type HttpMethod = 'post' | 'put' | 'patch' | 'delete';

interface UseApiMutationOptions<
  TData = unknown,
  TVariables = unknown,
  TContext = unknown
> extends Omit<
    UseMutationOptions<TData, ApiError, TVariables, TContext>,
    'mutationFn'
  > {
  successMessage?: string | ((data: TData, variables: TVariables) => string);
  errorMessage?: string | ((error: ApiError, variables: TVariables) => string);
  showSuccessToast?: boolean;
  showErrorToast?: boolean;
  invalidateQueries?: unknown[][];
  axiosConfig?: AxiosRequestConfig;
}

export function useApiMutation<
  TData = unknown,
  TVariables = unknown,
  TContext = unknown
>(
  config:
    | {
        method: HttpMethod;
        url: string;
      }
    | ((variables: TVariables) => Promise<TData>),
  options: UseApiMutationOptions<TData, TVariables, TContext> = {}
): UseMutationResult<TData, ApiError, TVariables, TContext> {
  const queryClient = useQueryClient();
  const {
    successMessage,
    errorMessage,
    showSuccessToast = true,
    showErrorToast = true,
    invalidateQueries,
    axiosConfig,
    onSuccess,
    onError,
    onMutate,
    onSettled,
    ...mutationOptions
  } = options;

  const mutationFn = async (variables: TVariables): Promise<TData> => {
    if (typeof config === 'function') {
      return config(variables);
    }

    const { method, url } = config;

    switch (method) {
      case 'post':
        return post<TData>(url, variables, axiosConfig);
      case 'put':
        return put<TData>(url, variables, axiosConfig);
      case 'patch':
        return patch<TData>(url, variables, axiosConfig);
      case 'delete':
        return remove<TData>(url, axiosConfig);
      default:
        throw new Error(`Unsupported HTTP method: ${method}`);
    }
  };

  return useMutation<TData, ApiError, TVariables, TContext>({
    ...mutationOptions,
    mutationFn,
    onMutate,
    onSuccess: async (data, variables, context) => {
      if (showSuccessToast && successMessage !== undefined) {
        const message =
          typeof successMessage === 'function'
            ? successMessage(data, variables)
            : successMessage;
        toast.success(message);
      }

      if (invalidateQueries && invalidateQueries.length > 0) {
        for (const queryKey of invalidateQueries) {
          await queryClient.invalidateQueries({ queryKey });
        }
      }

      onSuccess?.(data, variables, context);
    },
    onError: (error, variables, context) => {
      if (showErrorToast) {
        const message =
          errorMessage !== undefined
            ? typeof errorMessage === 'function'
              ? errorMessage(error, variables)
              : errorMessage
            : error.message || 'Something went wrong. Please try again.';
        toast.error(message);
      }
      onError?.(error, variables, context);
    },
    onSettled,
  });
}

export function useCreateMutation<
  TData = unknown,
  TVariables = unknown
>(
  config:
    | { method: HttpMethod; url: string }
    | ((variables: TVariables) => Promise<TData>),
  options: Omit<
    UseApiMutationOptions<TData, TVariables, unknown>,
    'successMessage' | 'errorMessage'
  > & {
    successMessage?: UseApiMutationOptions<TData, TVariables, unknown>['successMessage'];
    errorMessage?: UseApiMutationOptions<TData, TVariables, unknown>['errorMessage'];
  } = {}
) {
  return useApiMutation(config, {
    successMessage: options.successMessage ?? 'Created successfully',
    errorMessage: options.errorMessage,
    ...options,
  });
}

export function useUpdateMutation<
  TData = unknown,
  TVariables = unknown
>(
  config:
    | { method: HttpMethod; url: string }
    | ((variables: TVariables) => Promise<TData>),
  options: Omit<
    UseApiMutationOptions<TData, TVariables, unknown>,
    'successMessage' | 'errorMessage'
  > & {
    successMessage?: UseApiMutationOptions<TData, TVariables, unknown>['successMessage'];
    errorMessage?: UseApiMutationOptions<TData, TVariables, unknown>['errorMessage'];
  } = {}
) {
  return useApiMutation(config, {
    successMessage: options.successMessage ?? 'Updated successfully',
    errorMessage: options.errorMessage,
    ...options,
  });
}

export function useDeleteMutation<
  TData = unknown,
  TVariables = unknown
>(
  config:
    | { method: HttpMethod; url: string }
    | ((variables: TVariables) => Promise<TData>),
  options: Omit<
    UseApiMutationOptions<TData, TVariables, unknown>,
    'successMessage' | 'errorMessage'
  > & {
    successMessage?: UseApiMutationOptions<TData, TVariables, unknown>['successMessage'];
    errorMessage?: UseApiMutationOptions<TData, TVariables, unknown>['errorMessage'];
  } = {}
) {
  return useApiMutation(config, {
    successMessage: options.successMessage ?? 'Deleted successfully',
    errorMessage: options.errorMessage,
    ...options,
  });
}

export function useActionMutation<
  TData = unknown,
  TVariables = unknown
>(
  config:
    | { method: HttpMethod; url: string }
    | ((variables: TVariables) => Promise<TData>),
  actionName: string,
  options: Omit<
    UseApiMutationOptions<TData, TVariables, unknown>,
    'successMessage' | 'errorMessage'
  > = {}
) {
  return useApiMutation(config, {
    successMessage: `${actionName} completed`,
    errorMessage: (err) =>
      `Failed to ${actionName.toLowerCase()}: ${err.message}`,
    ...options,
  });
}
