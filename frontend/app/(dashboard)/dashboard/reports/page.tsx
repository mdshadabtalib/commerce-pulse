'use client';

import * as React from 'react';
import { FileText, Download, Calendar, TrendingUp } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

interface Report {
  id: string;
  name: string;
  description: string;
  type: string;
  lastGenerated: string;
  frequency: string;
}

const mockReports: Report[] = [
  {
    id: '1',
    name: 'Sales Report',
    description: 'Comprehensive sales analysis including revenue, orders, and trends',
    type: 'Sales',
    lastGenerated: '2 hours ago',
    frequency: 'Daily',
  },
  {
    id: '2',
    name: 'Customer Analytics',
    description: 'Customer behavior, segments, and lifetime value analysis',
    type: 'Customers',
    lastGenerated: '1 day ago',
    frequency: 'Weekly',
  },
  {
    id: '3',
    name: 'Product Performance',
    description: 'Top-selling products, inventory levels, and profit margins',
    type: 'Products',
    lastGenerated: '3 hours ago',
    frequency: 'Daily',
  },
  {
    id: '4',
    name: 'Financial Summary',
    description: 'Revenue, expenses, taxes, and profit/loss statement',
    type: 'Finance',
    lastGenerated: '1 week ago',
    frequency: 'Monthly',
  },
];

export default function ReportsPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Reports</h1>
          <p className="text-muted-foreground mt-1">
            Generate and download detailed analytics reports
          </p>
        </div>
        <Button>
          <FileText className="mr-2 h-4 w-4" />
          Create Custom Report
        </Button>
      </div>

      {/* Reports Grid */}
      <div className="grid gap-6 md:grid-cols-2">
        {mockReports.map((report) => (
          <Card key={report.id}>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <CardTitle className="text-lg">{report.name}</CardTitle>
                  <CardDescription>{report.description}</CardDescription>
                </div>
                <Badge variant="outline">{report.type}</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <Calendar className="h-4 w-4" />
                    <span>Last: {report.lastGenerated}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <TrendingUp className="h-4 w-4" />
                    <span>{report.frequency}</span>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" className="flex-1">
                    <Download className="mr-2 h-4 w-4" />
                    Download PDF
                  </Button>
                  <Button variant="outline" className="flex-1">
                    <Download className="mr-2 h-4 w-4" />
                    Download Excel
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Scheduled Reports */}
      <Card>
        <CardHeader>
          <CardTitle>Scheduled Reports</CardTitle>
          <CardDescription>
            Automatically generated reports delivered to your inbox
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between py-3 border-b">
              <div>
                <p className="text-sm font-medium">Weekly Sales Summary</p>
                <p className="text-sm text-muted-foreground">Every Monday at 9:00 AM</p>
              </div>
              <Badge>Active</Badge>
            </div>
            <div className="flex items-center justify-between py-3 border-b">
              <div>
                <p className="text-sm font-medium">Monthly Financial Report</p>
                <p className="text-sm text-muted-foreground">1st of every month</p>
              </div>
              <Badge>Active</Badge>
            </div>
            <div className="flex items-center justify-between py-3">
              <div>
                <p className="text-sm font-medium">Quarterly Performance Review</p>
                <p className="text-sm text-muted-foreground">End of each quarter</p>
              </div>
              <Badge variant="secondary">Paused</Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
