export type ID = string | number;

export type Timestamp = string;

export type JsonValue =
  | string
  | number
  | boolean
  | null
  | JsonValue[]
  | { [key: string]: JsonValue };

export type JsonObject = Record<string, JsonValue>;

export type SortDirection = 'asc' | 'desc';

export interface ApiError {
  message: string;
  statusCode: number;
  code?: string;
  details?: unknown;
  originalError?: unknown;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface ListQueryParams {
  page?: number;
  page_size?: number;
  per_page?: number;
  search?: string;
  sort_by?: string;
  sort_dir?: SortDirection;
  [key: string]: unknown;
}

export type UserStatus = 'active' | 'invited' | 'disabled' | 'pending';

export interface User {
  id: ID;
  email: string;
  full_name: string | null;
  avatar_url: string | null;
  status: UserStatus;
  roles: string[];
  permissions: string[];
  organization_id?: ID;
  created_at: Timestamp;
  last_login_at?: Timestamp | null;
  email_verified?: boolean;
  timezone?: string;
  locale?: string;
  first_name?: string | null;
  last_name?: string | null;
  updated_at?: Timestamp;
}

export type OrganizationStatus =
  | 'active'
  | 'trial'
  | 'past_due'
  | 'suspended'
  | 'canceled';

export interface Organization {
  id: ID;
  name: string;
  slug: string;
  logo_url?: string | null;
  status: OrganizationStatus;
  timezone: string;
  default_currency: string;
  settings?: JsonObject;
  created_at: Timestamp;
  billing_plan?: string;
  industry?: string | null;
  website?: string | null;
  updated_at?: Timestamp;
  trial_ends_at?: Timestamp | null;
  stripe_customer_id?: string | null;
}

export interface Member {
  id: ID;
  user_id: ID;
  email: string;
  name: string;
  role_slug: string;
  role_tier: number;
  status: UserStatus;
  joined_at?: Timestamp | null;
  avatar?: string | null;
}

export interface Role {
  id: ID;
  slug: string;
  name: string;
  tier: number;
  description: string | null;
  is_system: boolean;
  permissions: string[];
  created_at?: Timestamp;
  is_default?: boolean;
}

export type PermissionSlug =
  | 'dashboard.view'
  | 'dashboard.edit'
  | 'sales.view'
  | 'customers.view'
  | 'products.view'
  | 'products.edit'
  | 'inventory.view'
  | 'inventory.edit'
  | 'forecasting.view'
  | 'forecasting.edit'
  | 'anomalies.view'
  | 'reports.view'
  | 'reports.create'
  | 'reports.schedule'
  | 'datasets.view'
  | 'datasets.manage'
  | 'integrations.view'
  | 'integrations.manage'
  | 'members.view'
  | 'members.invite'
  | 'members.remove'
  | 'roles.manage'
  | 'settings.view'
  | 'settings.edit'
  | 'billing.view'
  | 'billing.edit';

export interface Permission {
  id: ID;
  slug: PermissionSlug;
  name: string;
  description: string | null;
  category: string;
}

export interface OrganizationMember {
  id: ID;
  user: User;
  organization_id: ID;
  role: Role;
  is_owner: boolean;
  joined_at: Timestamp;
  invited_by: ID | null;
  last_active_at: Timestamp | null;
}

export type DataSourceType =
  | 'shopify'
  | 'woocommerce'
  | 'amazon'
  | 'stripe'
  | 'shopee'
  | 'lazada'
  | 'bigcommerce'
  | 'magento'
  | 'csv'
  | 'custom_api';

export type DatasetStatus =
  | 'pending'
  | 'importing'
  | 'ready'
  | 'failed'
  | 'disabled'
  | 'archived';

export interface Dataset {
  id: ID;
  name: string;
  source_type: DataSourceType;
  status: DatasetStatus;
  row_count?: number;
  column_count?: number;
  file_size_bytes?: number;
  last_imported_at?: Timestamp | null;
  created_at: Timestamp;
  organization_id?: ID;
  slug?: string;
  description?: string | null;
  is_active?: boolean;
  sync_status?: string;
  last_synced_at?: Timestamp | null;
  next_sync_at?: Timestamp | null;
  records_count?: number;
  sync_frequency_minutes?: number | null;
  config?: JsonObject;
  updated_at?: Timestamp;
  connected_by_id?: ID;
}

export type ColumnDataType =
  | 'string'
  | 'integer'
  | 'float'
  | 'boolean'
  | 'date'
  | 'datetime'
  | 'json'
  | 'money'
  | 'enum'
  | 'unknown';

export interface DatasetColumn {
  id: ID;
  name: string;
  data_type: ColumnDataType;
  mapped_to?: string | null;
  is_nullable: boolean;
  sample_values?: JsonValue[];
}

export type ImportJobStatus =
  | 'pending'
  | 'queued'
  | 'processing'
  | 'validating'
  | 'completed'
  | 'failed'
  | 'cancelled'
  | 'partial';

export type ImportJobType =
  | 'initial_import'
  | 'full_sync'
  | 'incremental_sync'
  | 'csv_upload'
  | 'backfill';

export interface ImportJob {
  id: ID;
  status: ImportJobStatus;
  job_type: ImportJobType;
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  error_count: number;
  started_at?: Timestamp | null;
  completed_at?: Timestamp | null;
  summary?: JsonObject;
}

export type OrderStatus =
  | 'pending'
  | 'paid'
  | 'processing'
  | 'shipped'
  | 'delivered'
  | 'completed'
  | 'refunded'
  | 'cancelled';

export type PaymentStatus =
  | 'unpaid'
  | 'pending'
  | 'paid'
  | 'partially_refunded'
  | 'refunded'
  | 'void';

export interface Address {
  name: string | null;
  first_name: string | null;
  last_name: string | null;
  company: string | null;
  address1: string | null;
  address2: string | null;
  city: string | null;
  province: string | null;
  province_code: string | null;
  zip: string | null;
  country: string | null;
  country_code: string | null;
  phone: string | null;
}

export interface Order {
  id: ID;
  organization_id: ID;
  dataset_id: ID | null;
  external_order_id: string;
  order_number: string;
  status: OrderStatus;
  payment_status: PaymentStatus;
  currency: string;
  subtotal_amount: number;
  discount_amount: number;
  tax_amount: number;
  shipping_amount: number;
  total_amount: number;
  refunded_amount: number;
  net_amount: number;
  total_quantity: number;
  customer_id: ID | null;
  external_customer_id: string | null;
  customer_email: string | null;
  billing_address: Address | null;
  shipping_address: Address | null;
  ordered_at: Timestamp;
  paid_at: Timestamp | null;
  shipped_at: Timestamp | null;
  delivered_at: Timestamp | null;
  cancelled_at: Timestamp | null;
  source: DataSourceType;
  tags: string[];
  line_items_count: number;
  created_at: Timestamp;
  updated_at: Timestamp;
}

export interface OrderLineItem {
  id: ID;
  order_id: ID;
  product_id: ID | null;
  external_product_id: string | null;
  external_variant_id: string | null;
  sku: string | null;
  product_title: string;
  variant_title: string | null;
  quantity: number;
  unit_price: number;
  subtotal: number;
  discount_amount: number;
  tax_amount: number;
  total_amount: number;
  currency: string;
  image_url: string | null;
}

export type ProductStatus = 'active' | 'archived' | 'draft' | 'inactive';

export interface Product {
  id: ID;
  organization_id: ID;
  dataset_id: ID | null;
  external_product_id: string;
  title: string;
  slug: string;
  description: string | null;
  status: ProductStatus;
  product_type: string | null;
  vendor: string | null;
  tags: string[];
  image_url: string | null;
  images: string[];
  published_at: Timestamp | null;
  source: DataSourceType;
  created_at: Timestamp;
  updated_at: Timestamp;
  variants_count: number;
}

export interface ProductVariant {
  id: ID;
  product_id: ID;
  external_variant_id: string;
  title: string;
  sku: string;
  upc: string | null;
  isbn: string | null;
  price: number;
  compare_at_price: number | null;
  cost: number | null;
  currency: string;
  weight_unit: string | null;
  weight_value: number | null;
  inventory_quantity: number;
  inventory_policy: string;
  position: number;
  image_url: string | null;
  option_values: Record<string, string>;
  created_at: Timestamp;
  updated_at: Timestamp;
}

export type CustomerSegment =
  | 'vip'
  | 'repeat'
  | 'at_risk'
  | 'one_time'
  | 'new';

export interface Customer {
  id: ID;
  organization_id: ID;
  dataset_id: ID | null;
  external_customer_id: string;
  email: string | null;
  phone: string | null;
  first_name: string | null;
  last_name: string | null;
  full_name: string | null;
  avatar_url: string | null;
  accepts_marketing: boolean;
  currency: string;
  language: string | null;
  address: Address | null;
  segment: CustomerSegment | null;
  orders_count: number;
  total_spent: number;
  average_order_value: number;
  lifetime_value: number;
  last_order_id: ID | null;
  last_order_at: Timestamp | null;
  first_order_at: Timestamp | null;
  tags: string[];
  source: DataSourceType;
  created_at: Timestamp;
  updated_at: Timestamp;
}

export interface InventoryItem {
  id: ID;
  organization_id: ID;
  product_id: ID;
  variant_id: ID;
  location_id: ID | null;
  sku: string;
  quantity_available: number;
  quantity_reserved: number;
  quantity_incoming: number;
  quantity_sold_last_30d: number;
  reorder_point: number | null;
  reorder_quantity: number | null;
  lead_time_days: number | null;
  unit_cost: number | null;
  currency: string;
  last_restocked_at: Timestamp | null;
  updated_at: Timestamp;
}

export interface SalesKPIs {
  total_revenue: number;
  total_orders: number;
  average_order_value: number;
  total_items_sold: number;
  net_revenue: number;
  gross_margin: number | null;
  discounts_total: number;
  taxes_total: number;
  shipping_total: number;
  refunds_total: number;
  new_customers: number;
  returning_customers: number;
  conversion_rate: number | null;
}

export interface TimeSeriesPoint {
  timestamp: Timestamp;
  date: string;
  value: number;
  label: string | null;
  comparison_value?: number | null;
}

export interface BreakdownItem {
  key: string;
  label: string;
  value: number;
  percentage: number;
  color: string | null;
}

export interface ForecastPoint {
  date: Timestamp;
  predicted_value: number;
  lower_bound: number | null;
  upper_bound: number | null;
  actual_value: number | null;
}

export interface ForecastResult {
  id: ID;
  organization_id: ID;
  name: string;
  description: string | null;
  forecast_horizon_days: number;
  frequency: 'daily' | 'weekly' | 'monthly';
  model_type: string;
  model_version: string;
  status: 'processing' | 'completed' | 'failed';
  entity_type: 'product' | 'variant' | 'category' | 'organization' | 'customer';
  entity_id: ID | null;
  dataset_ids: ID[];
  total_predicted_value: number;
  total_actual_value: number | null;
  mape: number | null;
  mae: number | null;
  rmse: number | null;
  confidence_level: number;
  lower_bound_ratio: number;
  upper_bound_ratio: number;
  generated_at: Timestamp;
  generated_by_id: ID;
  points: ForecastPoint[];
}

export type AnomalySeverity = 'low' | 'medium' | 'high' | 'critical';

export type AnomalyStatus = 'open' | 'investigating' | 'acknowledged' | 'resolved';

export type AnomalyDirection = 'spike' | 'drop' | 'deviation';

export interface Anomaly {
  id: ID;
  organization_id: ID;
  anomaly_key: string;
  title: string;
  description: string | null;
  severity: AnomalySeverity;
  status: AnomalyStatus;
  direction: AnomalyDirection;
  metric: string;
  metric_value: number;
  expected_value: number | null;
  deviation_percentage: number | null;
  category: string;
  entity_type: 'order' | 'product' | 'variant' | 'customer' | 'revenue' | 'inventory' | string;
  entity_id: ID | null;
  dataset_id: ID | null;
  detected_at: Timestamp;
  window_start: Timestamp;
  window_end: Timestamp;
  investigation_notes: string | null;
  resolution_notes: string | null;
  resolved_at: Timestamp | null;
  resolved_by_id: ID | null;
  assignee_id: ID | null;
  related_anomaly_ids: ID[];
  created_at: Timestamp;
  updated_at: Timestamp;
}

export interface AnomalyResponse {
  id: ID;
  anomaly_key: string;
  title: string;
  description?: string | null;
  severity: AnomalySeverity;
  status: AnomalyStatus;
  direction: AnomalyDirection;
  metric: string;
  metric_value: number;
  expected_value: number | null;
  deviation_percentage: number | null;
  category: string;
  detected_at: Timestamp;
  window_start: Timestamp;
  window_end: Timestamp;
  entity_type?: string;
  entity_id?: ID | null;
  dataset_id?: ID | null;
  investigation_notes?: string | null;
  resolution_notes?: string | null;
  resolved_at?: Timestamp | null;
  assignee_id?: ID | null;
}

export type InsightType =
  | 'trend'
  | 'anomaly'
  | 'opportunity'
  | 'segment'
  | 'forecast'
  | 'comparison';

export type InsightSeverity = 'info' | 'warning' | 'success' | 'danger';

export interface Insight {
  id: ID;
  type: InsightType;
  title: string;
  description: string;
  severity: InsightSeverity;
  metric?: string;
  value?: number;
  comparison_value?: number | null;
  percentage_change?: number | null;
  confidence?: number;
  actionable?: boolean;
  action_label?: string | null;
  action_url?: string | null;
  generated_at: Timestamp;
  expires_at?: Timestamp | null;
}

export type ReportFormat = 'pdf' | 'csv' | 'excel' | 'html';

export type ReportFrequency = 'once' | 'daily' | 'weekly' | 'monthly' | 'quarterly';

export interface SavedReport {
  id: ID;
  organization_id: ID;
  name: string;
  description: string | null;
  slug: string;
  report_type: string;
  template_id: ID | null;
  dataset_ids: ID[];
  widget_ids: ID[];
  filters: JsonObject;
  time_range: JsonObject;
  config: JsonObject;
  default_format: ReportFormat;
  is_scheduled: boolean;
  schedule_frequency: ReportFrequency | null;
  schedule_time: string | null;
  schedule_weekday: number | null;
  schedule_monthday: number | null;
  recipient_emails: string[];
  is_public: boolean;
  created_by_id: ID;
  created_at: Timestamp;
  updated_at: Timestamp;
  last_run_at: Timestamp | null;
}

export interface ReportResponse {
  id: ID;
  name: string;
  description?: string | null;
  report_type: string;
  status: 'draft' | 'generating' | 'ready' | 'failed' | 'expired';
  format: ReportFormat;
  file_url?: string | null;
  file_size_bytes?: number | null;
  generated_at?: Timestamp | null;
  generated_by_id?: ID | null;
  period_start?: Timestamp | null;
  period_end?: Timestamp | null;
  filters?: JsonObject;
  created_at: Timestamp;
}

export interface ProductResponse {
  id: ID;
  title: string;
  sku?: string | null;
  status: ProductStatus;
  product_type?: string | null;
  vendor?: string | null;
  image_url?: string | null;
  tags?: string[];
  source: DataSourceType;
  total_revenue: number;
  total_orders: number;
  total_quantity_sold: number;
  units_in_stock?: number | null;
  average_order_value?: number | null;
  growth_rate?: number | null;
  last_sold_at?: Timestamp | null;
  created_at?: Timestamp;
}

export interface CustomerResponse {
  id: ID;
  email: string | null;
  full_name: string | null;
  avatar_url?: string | null;
  segment: CustomerSegment | null;
  orders_count: number;
  total_spent: number;
  average_order_value: number;
  lifetime_value: number;
  last_order_at?: Timestamp | null;
  first_order_at?: Timestamp | null;
  days_since_last_order?: number | null;
  predicted_next_order_at?: Timestamp | null;
  churn_risk_score?: number | null;
  tags?: string[];
  created_at?: Timestamp;
}

export interface KPIData {
  key: string;
  label: string;
  value: number;
  previous_value: number | null;
  growth_rate: number | null;
  formatted_value: string | null;
  currency: string | null;
  unit: string | null;
  trend: 'up' | 'down' | 'flat' | null;
  sparkline_data: number[] | null;
}

export type WidgetType =
  | 'kpi_card'
  | 'line_chart'
  | 'bar_chart'
  | 'pie_chart'
  | 'area_chart'
  | 'table'
  | 'metric_list'
  | 'funnel_chart'
  | 'heatmap';

export interface DashboardWidget {
  id: ID;
  organization_id: ID;
  dashboard_id: ID;
  title: string;
  description: string | null;
  widget_type: WidgetType;
  width: number;
  height: number;
  position_x: number;
  position_y: number;
  dataset_id: ID | null;
  metric: string | null;
  dimensions: string[];
  filters: JsonObject;
  time_range: string | null;
  config: JsonObject;
  is_visible: boolean;
  created_by_id: ID;
  created_at: Timestamp;
  updated_at: Timestamp;
}

export type NotificationType =
  | 'anomaly_detected'
  | 'forecast_complete'
  | 'report_complete'
  | 'sync_complete'
  | 'sync_failed'
  | 'invitation'
  | 'billing'
  | 'system';

export type NotificationChannel = 'email' | 'in_app' | 'slack' | 'sms';

export interface Notification {
  id: ID;
  user_id: ID;
  organization_id: ID | null;
  type: NotificationType;
  title: string;
  body: string;
  read_at: Timestamp | null;
  is_read: boolean;
  action_url: string | null;
  action_label: string | null;
  channel: NotificationChannel;
  related_resource_type: string | null;
  related_resource_id: ID | null;
  metadata: JsonObject;
  created_at: Timestamp;
}

export type DateRangePreset =
  | 'today'
  | 'yesterday'
  | '7d'
  | '14d'
  | '30d'
  | '90d'
  | 'this_week'
  | 'last_week'
  | 'this_month'
  | 'last_month'
  | 'this_quarter'
  | 'last_quarter'
  | 'this_year'
  | 'last_year'
  | 'custom';

export interface DateRange {
  from: Date | string | null;
  to: Date | string | null;
  preset: DateRangePreset;
  compare_from?: Date | string | null;
  compare_to?: Date | string | null;
}

export type ThemeMode = 'light' | 'dark' | 'system';

export type BillingPlan = 'starter' | 'growth' | 'enterprise' | 'custom';

export type SyncStatus = 'idle' | 'syncing' | 'success' | 'failed' | 'disabled';
