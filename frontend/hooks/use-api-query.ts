'use client';

import {
  useQuery,
  UseQueryOptions,
  UseQueryResult,
} from '@tanstack/react-query';
import { useEffect } from 'react';
import { toast } from 'sonner';
import type { ApiError } from '@/types';
import { get, AxiosRequestConfig } from '@/lib/api';

interface UseApiQueryOptions<TQueryFnData, TError, TData>
  extends Omit<
    UseQueryOptions<TQueryFnData, TError, TData>,
    'queryKey' | 'queryFn'
  > {
  showErrorToast?: boolean;
  errorMessage?: string | ((error: ApiError) => string);
  axiosConfig?: AxiosRequestConfig;
}

export function useApiQuery<
  TQueryFnData = unknown,
  TError extends ApiError = ApiError,
  TData = TQueryFnData
>(
  queryKey: readonly unknown[],
  url: string | (() => Promise<TQueryFnData>),
  options: UseApiQueryOptions<TQueryFnData, TError, TData> = {}
): UseQueryResult<TData, TError> {
  const {
    showErrorToast = false,
    errorMessage,
    axiosConfig,
    ...queryOptions
  } = options;

  const queryFn = async (): Promise<TQueryFnData> => {
    if (typeof url === 'function') {
      return url();
    }
    return get<TQueryFnData>(url, axiosConfig);
  };

  const result = useQuery<TQueryFnData, TError, TData>({
    queryKey,
    queryFn,
    ...queryOptions,
  });

  useEffect(() => {
    if (!result.isError || !showErrorToast) return;
    const error = result.error as unknown as ApiError;
    const message =
      errorMessage !== undefined
        ? typeof errorMessage === 'function'
          ? errorMessage(error)
          : errorMessage
        : error.message || 'Failed to load data. Please try again.';
    toast.error(message);
  }, [errorMessage, result.error, result.isError, showErrorToast]);

  return result;
}

export function useListQuery<
  TItem = unknown,
  TQueryFnData extends { items: TItem[] } = { items: TItem[] }
>(
  queryKey: readonly unknown[],
  url: string | (() => Promise<TQueryFnData>),
  options: UseApiQueryOptions<TQueryFnData, ApiError, TQueryFnData> = {}
) {
  return useApiQuery(queryKey, url, {
    refetchOnWindowFocus: false,
    refetchOnMount: true,
    placeholderData: (previousData) => previousData,
    ...options,
  });
}

export interface UsePaginatedQueryResult<T>
  extends Omit<UseQueryResult<T, ApiError>, 'isLoading' | 'isFetching' | 'isRefetching' | 'isPending' | 'fetchStatus'> {
  isLoadingInitial: boolean;
  isLoadingMore: boolean;
  isRefreshing: boolean;
}

export function usePaginatedQuery<
  TItem = unknown
>(
  queryKey: readonly unknown[],
  url: string | (() => Promise<{ items: TItem[]; total: number; page: number; per_page: number; total_pages: number }>),
  options: UseApiQueryOptions<
    { items: TItem[]; total: number; page: number; per_page: number; total_pages: number },
    ApiError,
    { items: TItem[]; total: number; page: number; per_page: number; total_pages: number }
  > & {
    page?: number;
  } = {}
): UsePaginatedQueryResult<{
  items: TItem[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}> {
  const { page = 1, ...restOptions } = options;

  const result = useApiQuery(
    [...queryKey, page],
    url,
    {
      refetchOnWindowFocus: false,
      placeholderData: (previousData) => previousData,
      ...restOptions,
    }
  );

  const { isRefetching, fetchStatus } = result;

  const isLoadingInitial = !result.data && fetchStatus === 'fetching';
  const isLoadingMore = !!result.data && fetchStatus === 'fetching' && !isRefetching;
  const isRefreshing = !!result.data && fetchStatus === 'fetching' && isRefetching;

  return {
    ...result,
    isLoadingInitial,
    isLoadingMore,
    isRefreshing,
  };
}

export function useDetailQuery<T = unknown>(
  queryKey: readonly unknown[],
  url: string | (() => Promise<T>),
  options: UseApiQueryOptions<T, ApiError, T> = {}
) {
  return useApiQuery(queryKey, url, {
    refetchOnWindowFocus: false,
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
    ...options,
  });
}

export type QueryState<T> =
  | { status: 'idle' | 'loading'; data: undefined; error: undefined }
  | { status: 'success'; data: T; error: undefined }
  | { status: 'error'; data: T | undefined; error: ApiError };

export function getQueryState<T>(
  result: UseQueryResult<T, ApiError>
): QueryState<T> {
  const { data, error, status } = result;

  if (status === 'pending') {
    return { status: 'loading', data: undefined, error: undefined };
  }

  if (status === 'error') {
    return {
      status: 'error',
      data,
      error: error ?? { message: 'An error occurred', statusCode: 0 },
    };
  }

  return {
    status: 'success',
    data: data as T,
    error: undefined,
  };
}

export function isQueryLoading<T>(
  result: UseQueryResult<T, ApiError>,
  { includeRefetching = false }: { includeRefetching?: boolean } = {}
): boolean {
  if (includeRefetching) {
    return result.status === 'pending' || result.isFetching;
  }
  return result.status === 'pending';
}
