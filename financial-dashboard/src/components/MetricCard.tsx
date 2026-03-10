import React from 'react';
import { cn } from '../../lib/utils';
import { type LucideIcon } from 'lucide-react';

interface MetricCardProps {
    title: string;
    value: string;
    subValue?: string;
    icon: LucideIcon;
    trend?: 'up' | 'down' | 'neutral';
    trendValue?: string;
    className?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
    title,
    value,
    subValue,
    icon: Icon,
    className
}) => {
    return (
        <div className={cn(
            "p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800 shadow-sm flex flex-col justify-between hover:shadow-md transition-shadow",
            className
        )}>
            <div className="flex items-start justify-between mb-4">
                <div className="p-2 bg-primary/10 rounded-lg text-primary">
                    <Icon className="w-5 h-5" />
                </div>
                {subValue && (
                    <span className="text-xs font-medium px-2 py-1 bg-slate-100 dark:bg-slate-800 rounded-full text-slate-500">
                        {subValue}
                    </span>
                )}
            </div>
            <div>
                <p className="text-sm font-medium text-slate-500 mb-1">{title}</p>
                <h3 className="text-2xl font-bold text-slate-800 dark:text-slate-100">{value}</h3>
            </div>
        </div>
    );
};
