import React from 'react';
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    ReferenceLine
} from 'recharts';
import { type MonthlyFlow } from '../../utils/calculations';

interface CashFlowChartProps {
    data: MonthlyFlow[];
}

const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
        return (
            <div className="bg-white dark:bg-slate-900 p-4 border border-slate-100 dark:border-slate-800 rounded-xl shadow-xl">
                <p className="font-semibold text-slate-700 dark:text-slate-200 mb-2">{label}</p>
                <div className="space-y-1 text-sm">
                    <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
                        <span className="text-muted-foreground">Income:</span>
                        <span className="font-mono font-medium text-emerald-600">₹{payload[0].value.toLocaleString()}</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-rose-500"></div>
                        <span className="text-muted-foreground">Outflow:</span>
                        <span className="font-mono font-medium text-rose-600">₹{payload[1].value.toLocaleString()}</span>
                    </div>
                    <div className="pt-2 mt-2 border-t border-dashed">
                        <span className="text-xs text-muted-foreground">Net: </span>
                        <span className={(payload[0].value - payload[1].value) > 0 ? "text-emerald-500" : "text-rose-500"}>
                            {((payload[0].value - payload[1].value) > 0 ? "+" : "")}₹{(payload[0].value - payload[1].value).toLocaleString()}
                        </span>
                    </div>
                </div>
            </div>
        );
    }
    return null;
};

export const CashFlowChart: React.FC<CashFlowChartProps> = ({ data }) => {
    return (
        <div className="p-6 bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-800 h-full">
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h3 className="text-lg font-semibold text-slate-700 dark:text-slate-200">Year 1 Cash Flow</h3>
                    <p className="text-xs text-muted-foreground">Monthly Inflows vs Outflows</p>
                </div>
                <div className="flex gap-4 text-xs font-medium">
                    <div className="flex items-center gap-1">
                        <div className="w-3 h-3 rounded bg-emerald-500"></div> Income
                    </div>
                    <div className="flex items-center gap-1">
                        <div className="w-3 h-3 rounded bg-rose-500"></div> Outflow
                    </div>
                </div>
            </div>

            <div className="h-[300px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                        data={data}
                        margin={{
                            top: 5,
                            right: 10,
                            left: 10,
                            bottom: 5,
                        }}
                        barGap={4}
                    >
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                        <XAxis
                            dataKey="month"
                            axisLine={false}
                            tickLine={false}
                            tick={{ fill: '#64748b', fontSize: 12 }}
                            dy={10}
                        />
                        <YAxis
                            axisLine={false}
                            tickLine={false}
                            tick={{ fill: '#64748b', fontSize: 12 }}
                            tickFormatter={(value) => `₹${value / 1000}k`}
                        />
                        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'transparent' }} />
                        <Bar
                            dataKey="income"
                            fill="#10b981"
                            radius={[4, 4, 0, 0]}
                            maxBarSize={40}
                        />
                        <Bar
                            dataKey="outflow"
                            fill="#f43f5e"
                            radius={[4, 4, 0, 0]}
                            maxBarSize={40}
                        />
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};
