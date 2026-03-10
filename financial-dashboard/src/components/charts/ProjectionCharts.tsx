import React from 'react';
import {
    AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
    LineChart, Line, Legend
} from 'recharts';
import { type YearProjection, type InflationData } from '../../utils/calculations';

interface WealthChartProps {
    data: YearProjection[];
}

interface InflationChartProps {
    data: InflationData[];
}

const formatLakhs = (value: number) => `₹${(value / 100000).toFixed(1)}L`;

export const WealthChart: React.FC<WealthChartProps> = ({ data }) => {
    return (
        <div className="p-6 bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-800 h-full">
            <h3 className="text-lg font-semibold text-slate-700 dark:text-slate-200 mb-6">Total Wealth Projector</h3>
            <div className="h-[300px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                        <defs>
                            <linearGradient id="colorSafe" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8} />
                                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.1} />
                            </linearGradient>
                            <linearGradient id="colorGrowth" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#10b981" stopOpacity={0.8} />
                                <stop offset="95%" stopColor="#10b981" stopOpacity={0.1} />
                            </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                        <XAxis dataKey="year" tickFormatter={(val) => `Year ${val}`} axisLine={false} tickLine={false} dy={10} />
                        <YAxis tickFormatter={formatLakhs} axisLine={false} tickLine={false} />
                        <RechartsTooltip
                            formatter={(value: number) => formatLakhs(value)}
                            contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' }}
                        />
                        <Area
                            type="monotone"
                            dataKey="safeCapital"
                            stackId="1"
                            stroke="#3b82f6"
                            fill="url(#colorSafe)"
                            name="Safe Corpus"
                        />
                        <Area
                            type="monotone"
                            dataKey="growthCapital"
                            stackId="1"
                            stroke="#10b981"
                            fill="url(#colorGrowth)"
                            name="Growth Corpus"
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </div>
            <div className="flex justify-center gap-6 mt-4">
                <div className="flex items-center gap-2 text-sm text-slate-600">
                    <div className="w-3 h-3 bg-blue-500 rounded-full"></div> Safe Capital (Fixed)
                </div>
                <div className="flex items-center gap-2 text-sm text-slate-600">
                    <div className="w-3 h-3 bg-emerald-500 rounded-full"></div> Growth Capital (MFs)
                </div>
            </div>
        </div>
    );
}

export const InflationChart: React.FC<InflationChartProps> = ({ data }) => {
    return (
        <div className="p-6 bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-800 h-full">
            <h3 className="text-lg font-semibold text-slate-700 dark:text-slate-200 mb-6">Inflation Impact</h3>
            <div className="h-[300px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={data} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                        <XAxis dataKey="year" tickFormatter={(val) => `Year ${val}`} axisLine={false} tickLine={false} dy={10} />
                        <YAxis tickFormatter={(val) => `₹${val / 1000}k`} axisLine={false} tickLine={false} domain={['dataMin - 1000', 'auto']} />
                        <RechartsTooltip
                            formatter={(value: number) => `₹${value.toLocaleString()}`}
                            contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' }}
                        />
                        <Line
                            type="monotone"
                            dataKey="nominalIncome"
                            stroke="#3b82f6"
                            strokeWidth={3}
                            name="Nominal Income"
                            dot={false}
                        />
                        <Line
                            type="monotone"
                            dataKey="realPurchasingPower"
                            stroke="#ef4444"
                            strokeWidth={3}
                            name="Real Purchasing Power"
                        />
                        <Legend verticalAlign="bottom" height={36} />
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}
